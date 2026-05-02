"""
MindFlow — GET /insights
Returns mood logs for the sparkline + weekSummary from user_memory.
The actual Lumen narrative is streamed through POST /chat — this endpoint
provides the raw data for the InsightsDashboard chart and weekly reflection card.
"""
import os
from fastapi import APIRouter
from backend.providers import cosmos_repository as db
from backend.agents import memory_agent

router = APIRouter()

_DEMO_USER_ID = os.getenv("DEMO_USER_ID", "demo-user-001")


@router.get("/insights")
async def get_insights(userId: str = _DEMO_USER_ID, days: int = 14):
    """
    Returns mood logs for the InsightsDashboard sparkline/stats,
    plus the weekSummary from user_memory (triggering a rebuild if stale).
    """
    mood_logs = await db.get_mood_logs(userId, days=days)

    # Rebuild weekSummary if stale (TTL-gated — cheap if already fresh)
    week_summary = await memory_agent.rebuild_week_summary(userId)

    return {
        "moodLogs": mood_logs,
        "days": days,
        "weekSummary": week_summary,
    }
