"""
MindFlow — POST /chat
Full streaming pipeline:
  1. Orchestrator classifies the message (JSON mode, <300ms)
  2. Memory Agent READ — assembles memoryContext from Cosmos
  3. Route to specialist ChatCompletionAgent
  4. Stream response chunks to frontend via StreamingResponse
  5. Buffer-strip the [SAVE_ENTRY] block (Decision 1 — prompt directive at end)
  6. Parse and save journal entry asynchronously
  7. Memory Agent WRITE — extract + score new facts (ensure_future, non-blocking)

Decision 3 (locked): frontend uses fetch + getReader() on text/plain stream.
Decision (correction): asyncio.ensure_future() used inside async generators — 
  more reliable than create_task() on Python 3.11.
"""
import asyncio
import json
import uuid
import os
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from semantic_kernel.contents import ChatHistory

from backend.models.schemas import ChatRequest, OrchestratorResult
from backend.agents import orchestrator, memory_agent
from backend.agents import mindfulness_agent, journal_agent, habit_agent, insights_agent
from backend.providers import cosmos_repository as db

router = APIRouter()

_SAVE_START = "[SAVE_ENTRY]"
_SAVE_END   = "[/SAVE_ENTRY]"
_HABIT_START = "[CREATE_HABIT]"
_HABIT_END   = "[/CREATE_HABIT]"

_FUNCTIONS_HABIT_URL = os.getenv("FUNCTIONS_HABIT_URL", "http://localhost:7071")
_DEMO_USER_ID        = os.getenv("DEMO_USER_ID", "demo-user-001")


def _chunk_text(chunk) -> str:
    """
    Safely extract plain text from any SK 1.x invoke_stream chunk.
    SK 1.41.3 ChatCompletionAgent yields StreamingChatMessageContent directly.
    Never use truthiness on content objects — use `is not None` + str() instead.
    """
    if isinstance(chunk, list):
        parts = []
        for item in chunk:
            c = getattr(item, "content", None)
            if c is not None:
                parts.append(str(c))
        return "".join(parts)
    c = getattr(chunk, "content", None)
    if c is None:
        return ""
    return c if isinstance(c, str) else str(c)


# ── Agent router ───────────────────────────────────────────

async def _get_specialist(agent_name: str, memory_context: str, user_id: str = "", user_message: str = ""):
    """Return the correct ChatCompletionAgent for the classified intent."""
    if agent_name == "mindfulness":
        return mindfulness_agent.get_agent(memory_context)

    if agent_name == "habit":
        # Fetch live habit data from Cosmos so Grove knows your actual streaks
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        try:
            habits = await db.get_habits(user_id)
        except Exception:
            habits = []
        if habits:
            habit_list = "\n".join(
                f"- {h['name']} (why: {h.get('why', '—')})" for h in habits
            )
            today_logs = "\n".join(
                f"- {h['name']} ✓" for h in habits if today in h.get("logs", [])
            ) or "None completed yet today."
            streaks = "\n".join(
                f"- {h['name']}: {h.get('currentStreak', 0)} day streak"
                for h in habits
            )
        else:
            habit_list = "No active habits yet."
            today_logs = "None completed yet today."
            streaks = "No streaks yet."
        return habit_agent.get_agent(memory_context, habit_list, today_logs, streaks)

    if agent_name == "insights":
        return await insights_agent.get_agent(user_id, user_message, memory_context)

    return journal_agent.get_agent(memory_context)  # default + journal


# ── SAVE_ENTRY parser ──────────────────────────────────────

async def _parse_and_save_entry(buffer: str, user_id: str) -> None:
    """
    Extract the [SAVE_ENTRY] block from River's response buffer,
    parse the structured fields, and save a JournalEntry to Cosmos.
    Runs as a background task via ensure_future — never blocks the stream.
    """
    try:
        start_idx = buffer.find(_SAVE_START)
        end_idx = buffer.find(_SAVE_END)
        if start_idx == -1 or end_idx == -1:
            return

        block = buffer[start_idx + len(_SAVE_START): end_idx].strip()
        fields: dict = {}
        for line in block.splitlines():
            if ":" in line:
                key, _, val = line.partition(":")
                fields[key.strip()] = val.strip()

        mood = fields.get("mood", "okay")
        sentiment = fields.get("sentiment", "neutral")
        themes_raw = fields.get("themes", "")
        themes = [t.strip() for t in themes_raw.split(",") if t.strip()]
        summary = fields.get("summary", "")

        # Extract the user-facing text (before [SAVE_ENTRY])
        user_text = buffer[:start_idx].strip()

        entry = {
            "id": str(uuid.uuid4()),
            "userId": user_id,
            "content": user_text,
            "moodAtEntry": mood,
            "sentiment": sentiment,
            "themes": themes,
            "summary": summary,
            "agentUsed": "journal",
            "embedding": [],   # populated in Hour 7 bulk index
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await db.save_journal_entry(entry)
        print(f"[River] Saved journal entry for {user_id}: {summary[:60]}...")

    except Exception as e:
        print(f"[River] _parse_and_save_entry failed: {e}")


# ── CREATE_HABIT parser ─────────────────────────────────────

async def _parse_and_create_habit(buffer: str, user_id: str) -> None:
    """
    Extract the [CREATE_HABIT] block from Grove's response buffer,
    parse name/why/targetTime, and POST to the habits proxy (Azure Functions).
    Runs as a background task via ensure_future — never blocks the stream.
    """
    try:
        start_idx = buffer.find(_HABIT_START)
        end_idx   = buffer.find(_HABIT_END)
        if start_idx == -1 or end_idx == -1:
            return

        block = buffer[start_idx + len(_HABIT_START): end_idx].strip()
        fields: dict = {}
        for line in block.splitlines():
            if ":" in line:
                key, _, val = line.partition(":")
                fields[key.strip()] = val.strip()

        name = fields.get("name", "").strip()
        why  = fields.get("why",  "").strip()
        target_time = fields.get("targetTime", "").strip()

        if not name or not why:
            print("[Grove] CREATE_HABIT block missing name or why — skipping")
            return

        payload = {
            "userId": user_id,
            "name": name,
            "why": why,
            "frequency": "daily",
            "targetTime": target_time or "",
            "durationMins": 0,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{_FUNCTIONS_HABIT_URL}/api/habits",
                json=payload,
            )
            if r.status_code in (200, 201):
                print(f"[Grove] Created habit '{name}' for {user_id}")
            else:
                print(f"[Grove] Habit create returned {r.status_code}: {r.text[:120]}")

    except Exception as e:
        print(f"[Grove] _parse_and_create_habit failed: {e}")


# ── /chat route ────────────────────────────────────────────

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    POST /chat — streams specialist agent response to the frontend.
    Frontend reads via response.body.getReader() (Decision 3).
    """
    async def generate():
        try:
            # 1. Orchestrator: classify intent (skipped when agentOverride is set)
            if request.agentOverride:
                classification = OrchestratorResult(
                    agent=request.agentOverride,
                    confidence=1.0,
                    mood="unknown",
                    urgency="low",
                )
                print(f"[Orchestrator] agentOverride={request.agentOverride} — skipping classify")
            else:
                classification = await orchestrator.classify(request.message)
                print(
                f"[Orchestrator] agent={classification.agent} "
                f"mood={classification.mood} urgency={classification.urgency}"
            )

            # 2. Memory READ: assemble context
            memory_context = await memory_agent.read(
                request.userId,
                mood=classification.mood,
                urgency=classification.urgency,
            )

            # 3. Build specialist agent + conversation history
            agent = await _get_specialist(
                classification.agent,
                memory_context,
                user_id=request.userId,
                user_message=request.message,
            )
            history = ChatHistory()

            for msg in request.conversationHistory:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    history.add_user_message(content)
                elif role == "assistant":
                    history.add_assistant_message(content)

            history.add_user_message(request.message)

            # 4. Stream response — buffer-strip [SAVE_ENTRY] and [CREATE_HABIT] blocks
            full_response = ""
            buffer = ""
            in_save_block  = False
            in_habit_block = False
            _HOLD = len(_SAVE_START)  # hold back 13 chars to catch partial tags

            # Yield agent name as first token so frontend can show agent badge
            yield f"[AGENT:{classification.agent}]\n"

            try:
                async for chunk in agent.invoke_stream(history):
                    content = _chunk_text(chunk)

                    if not content:
                        continue

                    buffer += content

                    # ── SAVE_ENTRY interception (River) ────────────
                    if not in_save_block and not in_habit_block and _SAVE_START in buffer:
                        in_save_block = True
                        pre = buffer[: buffer.index(_SAVE_START)]
                        unsent = pre[len(full_response):]
                        if unsent:
                            yield unsent
                            full_response += unsent

                    # ── CREATE_HABIT interception (Grove) ──────────
                    elif not in_save_block and not in_habit_block and _HABIT_START in buffer:
                        in_habit_block = True
                        pre = buffer[: buffer.index(_HABIT_START)]
                        unsent = pre[len(full_response):]
                        if unsent:
                            yield unsent
                            full_response += unsent

                    elif not in_save_block and not in_habit_block:
                        # Only yield what's safely before any potential marker prefix
                        safe_end = max(len(full_response), len(buffer) - _HOLD)
                        safe_content = buffer[len(full_response): safe_end]
                        if safe_content:
                            yield safe_content
                            full_response += safe_content

                    if in_save_block and _SAVE_END in buffer:
                        asyncio.ensure_future(
                            _parse_and_save_entry(buffer, request.userId)
                        )
                        break

                    if in_habit_block and _HABIT_END in buffer:
                        asyncio.ensure_future(
                            _parse_and_create_habit(buffer, request.userId)
                        )
                        break

                # Flush remaining held-back content if no marker was encountered
                if not in_save_block and not in_habit_block:
                    remaining = buffer[len(full_response):]
                    if remaining:
                        yield remaining
                        full_response += remaining

            except ValueError as e:
                # OpenTelemetry context cleanup error — harmless.
                # Occurs when SK's generator is torn down inside FastAPI StreamingResponse
                # because the OTEL ContextVar token was created in a different async context.
                # Content has already been yielded — safe to ignore.
                if "created in a different Context" not in str(e):
                    raise

            # 5. Memory WRITE — non-blocking
            asyncio.ensure_future(
                memory_agent.write(request.userId, request.message, full_response)
            )

        except Exception as e:
            print(f"[Chat] generate() error: {type(e).__name__}: {e}")
            yield "[ERROR] Something went wrong. Please try again."

    return StreamingResponse(generate(), media_type="text/plain")
