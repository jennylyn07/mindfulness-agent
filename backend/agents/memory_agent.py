"""
MindFlow — Memory Agent
Runs silently on every request. Never produces a user-facing response.
Two passes per request:
  READ  — before specialist: assembles memoryContext string ≤800 tokens
  WRITE — after specialist: extracts + scores new facts, upserts to Cosmos

Architecture note: ensure_future() used (not create_task()) — more reliable
inside async generators on Python 3.11 (Decision 3 correction, 2026-04-28).
"""
import json
import asyncio
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from backend.providers import cosmos_repository as db
from backend.prompts.memory import MEMORY_CONTEXT_TEMPLATE, MEMORY_WRITE_PROMPT


_FACT_THRESHOLD = 0.6        # facts below this importance are not stored
_MAX_FACTS = 12              # cap total stored facts per user (oldest dropped)
_DECAY_DAYS = 14             # facts not referenced for 14 days decay by 0.05
_WEEK_SUMMARY_TTL_DAYS = 7  # rebuild weekly summary after 7 days

WEEK_SUMMARY_PROMPT = """
You are summarizing a user's week from their mindfulness journal entries.
Write 2–3 warm, human sentences in the third person (e.g. "This week, they...").
Focus on emotional tone, recurring themes, and any notable shifts or breakthroughs.
Do NOT bullet-point. Do NOT use clinical language. Be specific if the entries allow it.
If there are no entries, respond with exactly: "No journal entries this week."

Journal entries (most recent first):
{entries_block}

Summary:"""


# ── READ pass ──────────────────────────────────────────────

async def read(
    user_id: str,
    mood: str = "unknown",
    urgency: str = "low",
) -> str:
    """
    Fetch user_memory from Cosmos and assemble the memoryContext string.
    Injected into each specialist agent's system prompt as {memoryContext}.
    Returns empty string if no memory doc found (graceful degradation).
    Context is capped at ~800 tokens — never let memory crowd out the conversation.
    """
    try:
        memory = await db.get_user_memory(user_id)
        user = await db.get_user(user_id)

        if not memory:
            return ""

        display_name = user.get("displayName", "friend") if user else "friend"
        hour = datetime.now(timezone.utc).hour
        time_of_day = (
            "morning" if 5 <= hour < 12
            else "afternoon" if 12 <= hour < 17
            else "evening"
        )

        # Sort facts by importance DESC, take top 5 for context budget
        facts = sorted(
            memory.get("facts", []),
            key=lambda f: f.get("importance", 0),
            reverse=True,
        )[:5]

        facts_block = "\n".join(
            f"- {f['content']} (importance: {f.get('importance', 0):.2f})"
            for f in facts
        ) or "No facts stored yet."

        prefs = memory.get("learnedPreferences", {})
        responds_well = ", ".join(prefs.get("respondsWellTo", [])) or "not yet known"
        avoids = ", ".join(prefs.get("avoids", [])) or "not yet known"
        themes = ", ".join(memory.get("recurringThemes", [])) or "none identified yet"
        breakthroughs = "; ".join(memory.get("breakthroughs", [])) or "none yet"

        context = MEMORY_CONTEXT_TEMPLATE.format(
            display_name=display_name,
            current_mood=mood,
            urgency=urgency,
            time_of_day=time_of_day,
            facts_block=facts_block,
            week_summary=memory.get("weekSummary", "No summary yet."),
            preferred_tone=prefs.get("preferredTone", "warm"),
            best_journaling_time=prefs.get("bestJournalingTime", "evening"),
            responds_well_to=responds_well,
            avoids=avoids,
            recurring_themes=themes,
            breakthroughs=breakthroughs,
        )

        return context

    except Exception as e:
        # Memory failure must never break the chat pipeline — log and return empty
        print(f"[MemoryAgent] READ failed for {user_id}: {e}")
        return ""


# ── WRITE pass ─────────────────────────────────────────────

async def write(
    user_id: str,
    user_message: str,
    ai_response: str,
) -> None:
    """
    After the specialist agent streams its response, extract new facts,
    score them, and upsert the user_memory document.

    Uses JSON mode via direct OpenAI call (not ChatCompletionAgent) —
    the Orchestrator and Memory write pass are the only two places in the
    codebase that use JSON mode.

    Fact scoring rules (from blueprint):
      ≥ 0.6  → stored
      < 0.6  → discarded
      > 0.8  → pushed to front of facts list
      Stale facts (not referenced in 14 days) → decayed by 0.05
      Total facts capped at 12 → oldest/lowest-importance dropped
    """
    try:
        from openai import AsyncAzureOpenAI
        from urllib.parse import urlparse as _up
        import os

        _raw = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        _p = _up(_raw)
        _base_ep = f"{_p.scheme}://{_p.netloc}/"

        client = AsyncAzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY", ""),
            azure_endpoint=_base_ep,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        )

        prompt = MEMORY_WRITE_PROMPT.format(
            user_message=user_message,
            ai_response=ai_response,
        )

        response = await client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=512,
        )

        raw = response.choices[0].message.content or '{"facts": []}'
        # Strip markdown code fences if the model wrapped its JSON response
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]          # drop opening ```json line
            raw = raw.rsplit("```", 1)[0].strip()  # drop closing ``` line
        # Try to parse — LLM occasionally omits outer braces
        extracted: dict = {}
        for _attempt in (raw, f"{{{raw}}}"):
            try:
                _parsed = json.loads(_attempt)
                if isinstance(_parsed, dict):
                    extracted = _parsed
                    break
            except json.JSONDecodeError:
                continue
        new_facts = extracted.get("facts", [])

        if not new_facts:
            return

        # Fetch current memory (create shell if not found)
        memory = await db.get_user_memory(user_id)
        if not memory:
            memory = _empty_memory(user_id)

        now_iso = datetime.now(timezone.utc).isoformat()

        # Decay stale facts
        existing_facts: list[dict] = _decay_facts(memory.get("facts", []), now_iso)

        # Merge new facts (skip duplicates by content similarity — simple prefix check)
        existing_contents = {f["content"][:60].lower() for f in existing_facts}
        for fact in new_facts:
            importance = float(fact.get("importance", 0))
            if importance < _FACT_THRESHOLD:
                continue
            content_key = fact["content"][:60].lower()
            if content_key in existing_contents:
                continue
            existing_facts.append({
                "content": fact["content"],
                "source": fact.get("source", "conversation"),
                "importance": importance,
                "createdAt": now_iso,
                "lastReferencedAt": now_iso,
            })

        # Sort by importance DESC, cap at max
        existing_facts.sort(key=lambda f: f.get("importance", 0), reverse=True)
        existing_facts = existing_facts[:_MAX_FACTS]

        memory["facts"] = existing_facts
        memory["updatedAt"] = now_iso

        await db.upsert_user_memory(memory)
        print(f"[MemoryAgent] WRITE: stored {len(new_facts)} new facts for {user_id}")

    except Exception as e:
        # Write failure must never surface to the user — log only
        print(f"[MemoryAgent] WRITE failed for {user_id}: {e}")


# ── Weekly Summary ────────────────────────────────────────

async def rebuild_week_summary(user_id: str) -> str:
    """
    Generate (or regenerate) the weekSummary field in user_memory.
    Checks _WEEK_SUMMARY_TTL_DAYS before rebuilding — skips if still fresh.
    Returns the new summary string, or the existing one if still valid.
    Safe to call from a timer trigger or on-demand.
    """
    try:
        memory = await db.get_user_memory(user_id)
        if not memory:
            memory = _empty_memory(user_id)

        now = datetime.now(timezone.utc)
        updated_at_str = memory.get("weekSummaryUpdatedAt", "")

        # Check TTL — skip rebuild if summary is still fresh
        if updated_at_str:
            try:
                updated_at = datetime.fromisoformat(updated_at_str)
                # Make aware if naive
                if updated_at.tzinfo is None:
                    updated_at = updated_at.replace(tzinfo=timezone.utc)
                age_days = (now - updated_at).days
                if age_days < _WEEK_SUMMARY_TTL_DAYS:
                    return memory.get("weekSummary", "")
            except ValueError:
                pass  # bad date string — proceed to rebuild

        # Fetch recent journal entries
        entries = await db.get_recent_journal_entries(user_id, limit=10)

        if not entries:
            summary = "No journal entries this week."
        else:
            entries_block = "\n\n".join(
                f"[{e.get('timestamp', '')[:10]}] {e.get('content', '')[:300]}"
                for e in entries
            )

            from openai import AsyncAzureOpenAI
            from urllib.parse import urlparse as _up

            _raw = os.getenv("AZURE_OPENAI_ENDPOINT", "")
            _p = _up(_raw)
            _base_ep = f"{_p.scheme}://{_p.netloc}/"

            client = AsyncAzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_KEY", ""),
                azure_endpoint=_base_ep,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            )

            response = await client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
                messages=[{
                    "role": "user",
                    "content": WEEK_SUMMARY_PROMPT.format(entries_block=entries_block),
                }],
                temperature=0.4,
                max_tokens=200,
            )
            summary = (response.choices[0].message.content or "").strip()

        memory["weekSummary"] = summary
        memory["weekSummaryUpdatedAt"] = now.isoformat()
        memory["updatedAt"] = now.isoformat()
        await db.upsert_user_memory(memory)
        print(f"[MemoryAgent] weekSummary rebuilt for {user_id}: {summary[:80]}...")
        return summary

    except Exception as e:
        print(f"[MemoryAgent] rebuild_week_summary failed for {user_id}: {e}")
        return ""


# ── Helpers ────────────────────────────────────────────────

def _empty_memory(user_id: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": user_id,
        "userId": user_id,
        "facts": [],
        "weekSummary": "",
        "weekSummaryUpdatedAt": now,
        "learnedPreferences": {
            "preferredTone": "warm",
            "bestJournalingTime": "evening",
            "respondsWellTo": [],
            "avoids": [],
        },
        "recurringThemes": [],
        "breakthroughs": [],
        "updatedAt": now,
    }


def _decay_facts(facts: list[dict], now_iso: str) -> list[dict]:
    """Reduce importance of facts not referenced in the last 14 days."""
    now = datetime.fromisoformat(now_iso)
    decayed = []
    for fact in facts:
        last_ref = fact.get("lastReferencedAt", now_iso)
        try:
            days_since = (now - datetime.fromisoformat(last_ref)).days
        except ValueError:
            days_since = 0
        if days_since >= _DECAY_DAYS:
            fact = {**fact, "importance": max(0.0, fact.get("importance", 0) - 0.05)}
        decayed.append(fact)
    return decayed
