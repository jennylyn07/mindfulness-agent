"""
MindFlow — GET /journal
Returns the user's most recent journal entries.
Entries are created by River via the SAVE_ENTRY buffer parser in chat.py.
"""
import os
from fastapi import APIRouter
from backend.providers import cosmos_repository as db

router = APIRouter()

_DEMO_USER_ID = os.getenv("DEMO_USER_ID", "demo-user-001")


@router.get("/journal")
async def get_journal(userId: str = _DEMO_USER_ID, limit: int = 10):
    """Return the N most recent journal entries for a user."""
    entries = await db.get_recent_journal_entries(userId, limit=limit)
    return entries
