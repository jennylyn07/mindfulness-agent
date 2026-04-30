"""
MindFlow — Lumen (Insights Agent)
Returns a ChatCompletionAgent with journal RAG context, mood trend,
habit stats, and memory context — all injected into the system prompt.

Flow:
  1. Fetch last 7 mood logs from Cosmos (trend)
  2. Fetch active habits from Cosmos (completion stats)
  3. Run hybrid search over journal entries in AI Search (RAG)
  4. Build Lumen's instructions with all context injected
  5. Return agent — caller streams response
"""
from datetime import datetime, timezone
from semantic_kernel.agents import ChatCompletionAgent
from backend.kernel import build_kernel
from backend.prompts.insights import INSIGHTS_PROMPT
from backend.providers import search_provider, cosmos_repository as db


async def get_agent(user_id: str, user_query: str, memory_context: str = "") -> ChatCompletionAgent:
    """Build Lumen with full context: RAG + mood trend + habit stats + memory."""

    # 1. Journal RAG context
    journal_context = await search_provider.search(
        query=user_query,
        user_id=user_id,
        top_k=5,
    )

    # 2. Mood trend (last 7 days)
    try:
        mood_logs = await db.get_mood_logs(user_id, days=7)
    except Exception:
        mood_logs = []

    if mood_logs:
        avg_score = sum(m.get("score", 5) for m in mood_logs) / len(mood_logs)
        moods_listed = ", ".join(
            f"{m.get('mood', '?')} ({m.get('timestamp', '')[:10]})"
            for m in reversed(mood_logs)
        )
        mood_trend = f"Average score: {avg_score:.1f}/10 over last {len(mood_logs)} logs. Entries: {moods_listed}"
    else:
        mood_trend = "No mood data yet."

    # 3. Habit completion stats (last 7 days)
    try:
        habits = await db.get_habits(user_id)
    except Exception:
        habits = []

    if habits:
        today = datetime.now(timezone.utc)
        last_7 = [(today.date() - __import__('datetime').timedelta(days=i)).isoformat() for i in range(7)]
        stats_lines = []
        for h in habits:
            logs = h.get("logs", [])
            done_this_week = sum(1 for d in last_7 if d in logs)
            stats_lines.append(
                f"- {h['name']}: {done_this_week}/7 days this week, "
                f"streak {h.get('currentStreak', 0)} days"
            )
        habit_stats = "\n".join(stats_lines)
    else:
        habit_stats = "No habit data yet."

    instructions = (
        INSIGHTS_PROMPT
        .replace("{journalContext}", journal_context or "No journal entries indexed yet.")
        .replace("{memoryContext}", memory_context)
        .replace("{moodTrend}", mood_trend)
        .replace("{habitStats}", habit_stats)
    )

    kernel = build_kernel()
    return ChatCompletionAgent(
        kernel=kernel,
        name="Lumen",
        instructions=instructions,
    )
