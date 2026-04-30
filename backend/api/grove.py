"""
MindFlow — GET /grove/nudge
Returns a single personalised one-sentence nudge from Grove
based on the user's live habit data and memory context.
Non-streaming — designed for the chat head proactive message.
"""
import os
import json
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone

from backend.providers import cosmos_repository as db
from backend.agents import memory_agent

router = APIRouter()

_DEMO_USER_ID = os.getenv("DEMO_USER_ID", "demo-user-001")

_NUDGE_PROMPT = """You are Grove, a warm habit coach. Based on the user's habits and memory, \
write ONE short message (1–2 sentences, max 25 words) to send them as a proactive check-in notification.

Rules:
- Sound like a friend texting, not a coach lecturing
- Be specific to their actual habit data (use names, streaks)
- Vary the angle: sometimes encouragement, sometimes a gentle reminder, sometimes reframing a miss
- No emojis in the middle of sentences, one at the end is fine
- Never start with "I" — start with the habit name, a feeling word, or a question

User's habits:
{habit_summary}

Memory context:
{memory_context}
"""


async def _call_grove_nudge(habit_summary: str, memory_context: str) -> str:
    """Single non-streaming LLM call to generate a nudge message."""
    from openai import AsyncAzureOpenAI
    from urllib.parse import urlparse

    raw = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    p = urlparse(raw)
    base_ep = f"{p.scheme}://{p.netloc}/"

    client = AsyncAzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY", ""),
        azure_endpoint=base_ep,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
    )

    prompt = _NUDGE_PROMPT.format(
        habit_summary=habit_summary,
        memory_context=memory_context or "No memory context yet.",
    )

    response = await client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        messages=[{"role": "system", "content": prompt}],
        temperature=0.85,   # some variation so it's never identical
        max_tokens=60,
    )
    return (response.choices[0].message.content or "").strip()


@router.get("/grove/nudge")
async def get_grove_nudge(userId: str = _DEMO_USER_ID):
    """
    Returns a personalized Grove nudge for the chat head.
    Called once per session (frontend caches with 1-hour TTL + date key).
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    try:
        # 1. Fetch habits
        habits = await db.get_habits(userId)

        if not habits:
            return {"nudge": "Ready to build your first habit? Grove is here.", "date": today}

        # 2. Build habit summary for the prompt
        lines = []
        for h in habits:
            streak = h.get("currentStreak", 0)
            logged_today = today in h.get("logs", [])
            status = "✓ logged today" if logged_today else "not logged today"
            lines.append(
                f"- {h['name']}: {streak}-day streak, {status}"
            )
        habit_summary = "\n".join(lines)

        # 3. Read memory context
        memory_ctx = await memory_agent.read(userId, mood="unknown", urgency="low")

        # 4. Generate nudge
        nudge = await _call_grove_nudge(habit_summary, memory_ctx)
        if not nudge:
            nudge = "How are your habits sitting with you today?"

        return {"nudge": nudge, "date": today}

    except Exception as e:
        print(f"[Grove/nudge] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
