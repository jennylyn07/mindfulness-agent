"""
MindFlow — GET /insights
Returns mood logs for the sparkline + triggers Lumen via POST /chat.
The actual Lumen response is streamed through POST /chat — this endpoint
provides the raw mood data for the InsightsDashboard chart.
"""
import os
from fastapi import APIRouter
from backend.providers import cosmos_repository as db

router = APIRouter()

_DEMO_USER_ID = os.getenv("DEMO_USER_ID", "demo-user-001")


@router.get("/insights")
async def get_insights(userId: str = _DEMO_USER_ID, days: int = 14):
    """
    Returns mood logs for the past N days for the sparkline chart.
    Journal theme aggregation added here in a future iteration.
    """
    mood_logs = await db.get_mood_logs(userId, days=days)
    return {"moodLogs": mood_logs, "days": days}
