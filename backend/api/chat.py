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
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from semantic_kernel.contents import ChatHistory

from backend.models.schemas import ChatRequest
from backend.agents import orchestrator, memory_agent
from backend.agents import mindfulness_agent, journal_agent, habit_agent
from backend.providers import cosmos_repository as db

router = APIRouter()

_SAVE_START = "[SAVE_ENTRY]"
_SAVE_END = "[/SAVE_ENTRY]"


# ── Agent router ───────────────────────────────────────────

def _get_specialist(agent_name: str, memory_context: str):
    """Return the correct ChatCompletionAgent for the classified intent."""
    if agent_name == "mindfulness":
        return mindfulness_agent.get_agent(memory_context)
    if agent_name == "habit":
        return habit_agent.get_agent(memory_context)
    # insights_agent added in Phase 7
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


# ── /chat route ────────────────────────────────────────────

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    POST /chat — streams specialist agent response to the frontend.
    Frontend reads via response.body.getReader() (Decision 3).
    """
    async def generate():
        try:
            # 1. Orchestrator: classify intent
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
            agent = _get_specialist(classification.agent, memory_context)
            history = ChatHistory()

            for msg in request.conversationHistory:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    history.add_user_message(content)
                elif role == "assistant":
                    history.add_assistant_message(content)

            history.add_user_message(request.message)

            # 4. Stream response — buffer-strip [SAVE_ENTRY] block
            full_response = ""
            buffer = ""
            in_save_block = False

            # Yield agent name as first token so frontend can show agent badge
            yield f"[AGENT:{classification.agent}]\n"

            async for chunk in agent.invoke_stream(history):
                # SK 1.x invoke_stream — handle list or direct content
                if isinstance(chunk, list):
                    content = "".join(
                        item.content
                        for item in chunk
                        if hasattr(item, "content") and item.content
                    )
                elif hasattr(chunk, "content") and chunk.content:
                    content = chunk.content
                else:
                    content = ""

                if not content:
                    continue

                buffer += content

                if not in_save_block and _SAVE_START in buffer:
                    in_save_block = True
                    pre = buffer[: buffer.index(_SAVE_START)]
                    if pre:
                        yield pre
                        full_response += pre
                elif not in_save_block:
                    yield content
                    full_response += content

                if in_save_block and _SAVE_END in buffer:
                    asyncio.ensure_future(
                        _parse_and_save_entry(buffer, request.userId)
                    )
                    break

            # 5. Memory WRITE — non-blocking
            asyncio.ensure_future(
                memory_agent.write(request.userId, request.message, full_response)
            )

        except Exception as e:
            print(f"[Chat] generate() error: {e}")
            yield f"[ERROR] Something went wrong. Please try again."

    return StreamingResponse(generate(), media_type="text/plain")
