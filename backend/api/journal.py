"""
MindFlow — GET /journal, PATCH /journal/{entry_id}
Returns the user's most recent journal entries and allows editing them.
Entries are created by River via the SAVE_ENTRY buffer parser in chat.py.
"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.providers import cosmos_repository as db

router = APIRouter()

_DEMO_USER_ID = os.getenv("DEMO_USER_ID", "demo-user-001")


class JournalUpdate(BaseModel):
    summary: Optional[str] = None
    moodAtEntry: Optional[str] = None
    themes: Optional[list[str]] = None


@router.get("/journal")
async def get_journal(userId: str = _DEMO_USER_ID, limit: int = 50):
    """Return the N most recent journal entries for a user (default 50)."""
    entries = await db.get_recent_journal_entries(userId, limit=limit)
    return entries


@router.patch("/journal/{entry_id}")
async def update_journal(entry_id: str, body: JournalUpdate, userId: str = _DEMO_USER_ID):
    """
    Edit the summary, mood or themes of a saved journal entry.
    After saving, re-runs the Memory Agent WRITE pass so that user_memory
    reflects the updated summary. AI Search is not re-indexed because
    it embeds the content field (River's response text), not the summary.
    """
    import asyncio
    from backend.agents import memory_agent

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        updated = await db.update_journal_entry(entry_id, userId, updates)

        # Re-extract facts into user_memory from the edited summary.
        # Runs non-blocking — response returns immediately while memory syncs.
        if "summary" in updates and updates["summary"].strip():
            edited_summary = updates["summary"]
            asyncio.ensure_future(
                memory_agent.write(
                    userId,
                    f"I want to update my journal reflection: {edited_summary}",
                    "",   # no agent response — user initiated the edit
                )
            )
            print(f"[Journal] Triggered memory re-extraction for edit on entry {entry_id}")

        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
