"""MindFlow — GET /calendar
Returns a per-day activity summary for a user over a date range.
"""

import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

from backend.providers import cosmos_repository as db

router = APIRouter()

_DEMO_USER_ID = os.getenv("DEMO_USER_ID", "demo-user-001")


def _parse_ymd(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date: {s}. Use YYYY-MM-DD") from e


@router.get("/calendar")
async def get_calendar(
    userId: str = _DEMO_USER_ID,
    start: str = "",
    end: str = "",
):
    if not start or not end:
        raise HTTPException(status_code=400, detail="Query params 'start' and 'end' are required (YYYY-MM-DD)")

    start_dt = _parse_ymd(start)
    end_dt = _parse_ymd(end)
    if end_dt < start_dt:
        raise HTTPException(status_code=400, detail="'end' must be >= 'start'")

    end_exclusive = end_dt + timedelta(days=1)

    dates: list[str] = []
    cur = start_dt
    while cur <= end_dt:
        dates.append(cur.strftime("%Y-%m-%d"))
        cur += timedelta(days=1)

    result: dict[str, dict] = {
        d: {
            "hasJournal": False,
            "journalId": "",
            "journalMood": "",
            "journalThemes": [],
            "mood": None,
            "moodLabel": None,
            "habitsCompleted": 0,
            "habitsTotal": 0,
        }
        for d in dates
    }

    journals = await db.get_journal_entries_in_range(userId, start_dt, end_exclusive)
    for j in journals:
        ts = j.get("timestamp", "")
        day = ts[:10]
        if day not in result:
            continue
        if not result[day]["hasJournal"]:
            result[day]["hasJournal"] = True
            result[day]["journalId"] = j.get("id", "")
            result[day]["journalMood"] = j.get("moodAtEntry", "")
            result[day]["journalThemes"] = j.get("themes", []) or []

    moods = await db.get_mood_logs_in_range(userId, start_dt, end_exclusive)
    for m in moods:
        ts = m.get("timestamp", "")
        day = ts[:10]
        if day not in result:
            continue
        if result[day]["mood"] is None:
            result[day]["mood"] = m.get("score")
            result[day]["moodLabel"] = m.get("mood")

    habits = await db.get_habits(userId)
    active_habits = [h for h in habits if h.get("active", True)]
    for day in dates:
        result[day]["habitsTotal"] = len(active_habits)
        completed = 0
        for h in active_habits:
            logs = h.get("logs", []) or []
            if day in logs:
                completed += 1
        result[day]["habitsCompleted"] = completed

    return result
