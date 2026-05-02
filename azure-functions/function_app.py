"""
MindFlow Azure Functions — Root Entry Point
Python v2 programming model (decorator-based, single app instance).

Routes:
  GET  /api/habits              — list habits for a user
  POST /api/habits              — create a new habit
  PATCH /api/habits/{id}/log   — mark habit done today (recalculates streak)
  POST /api/mood               — log a mood check-in

Timer Triggers:
  weekly_digest                 — every Sunday 08:00 UTC, rebuilds weekSummary
                                  for all users who have journaled in the last 14 days

Called by FastAPI backend (backend/api/habits.py, backend/api/mood.py),
not by the frontend directly.
"""
import json
import os
import uuid
import asyncio
from datetime import datetime, timezone, timedelta

import azure.functions as func
from azure.cosmos import CosmosClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


# ── Weekly digest timer trigger ────────────────────────────
@app.timer_trigger(
    schedule="0 0 8 * * 0",   # every Sunday at 08:00 UTC (NCRONTAB)
    arg_name="timer",
    run_on_startup=False,
)
def weekly_digest(timer: func.TimerRequest) -> None:
    """
    Rebuild weekSummary in user_memory for all recently-active users.
    Fires every Sunday at 08:00 UTC.

    Architecture: calls the FastAPI backend's GET /insights?userId=... endpoint
    rather than importing backend code directly. This avoids Python-path issues
    when azure-functions and backend are deployed as separate units.
    The /insights endpoint already calls rebuild_week_summary() internally (TTL-gated).

    BACKEND_URL env var must be set to the FastAPI base URL in Application Settings,
    e.g. https://mindflow-backend.azurewebsites.net
    """
    if timer.past_due:
        print("[WeeklyDigest] Timer is past due — running anyway")

    backend_url = os.environ.get("BACKEND_URL", "").rstrip("/")
    if not backend_url:
        print("[WeeklyDigest] BACKEND_URL not set — skipping (set it in Application Settings)")
        return

    try:
        import urllib.request
        import urllib.error

        # Fetch all user IDs that have a memory doc from Cosmos directly
        # (safe — azure-cosmos IS part of this deployment unit)
        endpoint = os.environ["COSMOS_ENDPOINT"]
        key = os.environ["COSMOS_KEY"]
        db_name = os.environ.get("COSMOS_DB_NAME", "mindflow")
        client = CosmosClient(endpoint, key)
        container = client.get_database_client(db_name).get_container_client("user_memory")

        users = list(container.query_items(
            query="SELECT c.userId FROM c",
            enable_cross_partition_query=True,
        ))
        user_ids = [u["userId"] for u in users if u.get("userId")]

        print(f"[WeeklyDigest] Triggering weekSummary rebuild for {len(user_ids)} users via API")

        async def _rebuild_all(ids: list) -> None:
            """Hit GET /insights for each user concurrently (TTL-gated in the API)."""
            import aiohttp
            async with aiohttp.ClientSession() as session:
                tasks = [
                    session.get(f"{backend_url}/insights?userId={uid}&days=14")
                    for uid in ids
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for uid, result in zip(ids, results):
                    if isinstance(result, Exception):
                        print(f"[WeeklyDigest] ✗ {uid}: {result}")
                    else:
                        async with result:
                            status = result.status
                            print(f"[WeeklyDigest] {'✓' if status == 200 else '✗'} {uid} → HTTP {status}")

        asyncio.run(_rebuild_all(user_ids))
        print("[WeeklyDigest] Done")

    except Exception as e:
        print(f"[WeeklyDigest] Fatal error: {e}")
        raise


def _get_habits_container():
    endpoint = os.environ["COSMOS_ENDPOINT"]
    key = os.environ["COSMOS_KEY"]
    db_name = os.environ.get("COSMOS_DB_NAME", "mindflow")
    client = CosmosClient(endpoint, key)
    return client.get_database_client(db_name).get_container_client("habits")


def _get_mood_container():
    endpoint = os.environ["COSMOS_ENDPOINT"]
    key = os.environ["COSMOS_KEY"]
    db_name = os.environ.get("COSMOS_DB_NAME", "mindflow")
    client = CosmosClient(endpoint, key)
    return client.get_database_client(db_name).get_container_client("mood_logs")


DEMO_USER_ID = os.environ.get("DEMO_USER_ID", "demo-user-001")


def _calc_streak(logs: list, as_of=None) -> int:
    """
    Calculate the consecutive-day streak ending on `as_of` (defaults to today UTC).

    Algorithm: walk backwards through sorted logs. For each date, check if it
    equals the next expected date (starting from as_of). If yes, count it and
    move the expected date back by one day. If the log date is earlier than
    expected (a gap), stop.

    This is the single authoritative implementation used by GET, log, and unlog.
    """
    if not logs:
        return 0
    if as_of is None:
        as_of = datetime.now(timezone.utc).date()
    streak = 0
    check = as_of
    for date_str in reversed(sorted(logs)):
        try:
            log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        if log_date == check:
            streak += 1
            check = check - timedelta(days=1)
        elif log_date < check:
            # Gap in the chain — stop counting
            break
    return streak


# ── GET /api/habits ────────────────────────────────────────
@app.route(route="habits", methods=["GET"])
def get_habits(req: func.HttpRequest) -> func.HttpResponse:
    user_id = req.params.get("userId", DEMO_USER_ID)
    try:
        container = _get_habits_container()
        items = list(container.query_items(
            query="SELECT * FROM c WHERE c.userId = @uid AND c.active = true ORDER BY c.name",
            parameters=[{"name": "@uid", "value": user_id}],
            enable_cross_partition_query=False,
        ))
        # Recalculate streak with the correct as_of date:
        #   - Today NOT logged → show yesterday's streak (still alive until midnight)
        #   - Today IS logged  → show today's full streak (yesterday + 1)
        # Midnight auto-reset: if tomorrow arrives and today wasn't logged,
        # as_of=yesterday will be tomorrow's "yesterday" (today), which has
        # no log → chain breaks → streak = 0 automatically.
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        yesterday_date = datetime.now(timezone.utc).date() - timedelta(days=1)
        for item in items:
            logs = item.get("logs", [])
            if today_str in logs:
                live_streak = _calc_streak(logs)           # includes today
            else:
                live_streak = _calc_streak(logs, as_of=yesterday_date)  # alive until midnight
            item["currentStreak"] = live_streak
            item["longestStreak"] = max(item.get("longestStreak", 0), live_streak)
        return func.HttpResponse(
            json.dumps(items),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)


# ── POST /api/habits ───────────────────────────────────────
@app.route(route="habits", methods=["POST"])
def create_habit(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        if not body.get("name") or not body.get("why"):
            return func.HttpResponse(
                json.dumps({"error": "name and why are required"}),
                status_code=400,
            )
        habit = {
            "id": str(uuid.uuid4()),
            "userId": body.get("userId", DEMO_USER_ID),
            "name": body["name"],
            "why": body["why"],
            "frequency": body.get("frequency", "daily"),
            "targetTime": body.get("targetTime", ""),
            "durationMins": body.get("durationMins", 0),
            "logs": [],
            "currentStreak": 0,
            "longestStreak": 0,
            "active": True,
        }
        _get_habits_container().upsert_item(habit)
        return func.HttpResponse(json.dumps(habit), mimetype="application/json", status_code=201)
    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)


# ── PATCH /api/habits/{habit_id}/log ──────────────────────
@app.route(route="habits/{habit_id}/log", methods=["PATCH"])
def log_habit(req: func.HttpRequest) -> func.HttpResponse:
    """Mark habit done for today (UTC). Recalculates streak."""
    habit_id = req.route_params.get("habit_id", "")
    user_id = req.params.get("userId", DEMO_USER_ID)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        container = _get_habits_container()
        habit = container.read_item(item=habit_id, partition_key=user_id)

        logs: list = habit.get("logs", [])
        if today not in logs:
            logs.append(today)
            logs.sort()

        # Recalculate streak from today (today is now in logs)
        streak = _calc_streak(logs)

        habit["logs"] = logs
        habit["currentStreak"] = streak
        habit["longestStreak"] = max(streak, habit.get("longestStreak", 0))

        container.upsert_item(habit)
        return func.HttpResponse(json.dumps(habit), mimetype="application/json", status_code=200)
    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)



# ── PATCH /api/habits/{habit_id}/unlog ────────────────────
@app.route(route="habits/{habit_id}/unlog", methods=["PATCH"])
def unlog_habit(req: func.HttpRequest) -> func.HttpResponse:
    """Remove today's log entry (uncheck). Recalculates streak."""
    habit_id = req.route_params.get("habit_id", "")
    user_id = req.params.get("userId", DEMO_USER_ID)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        container = _get_habits_container()
        habit = container.read_item(item=habit_id, partition_key=user_id)

        logs: list = habit.get("logs", [])
        if today in logs:
            logs.remove(today)

        # Uncheck = "undo today" → show streak as of YESTERDAY.
        # The chain is preserved: re-checking today immediately restores full streak.
        # Midnight auto-reset: handled by GET /habits live recalculation —
        # if tomorrow arrives and today was never logged, the chain breaks → 0.
        yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
        streak = _calc_streak(logs, as_of=yesterday)

        habit["logs"] = logs
        habit["currentStreak"] = streak
        # longestStreak stays unchanged — don't reduce it on unlog
        container.upsert_item(habit)
        return func.HttpResponse(json.dumps(habit), mimetype="application/json", status_code=200)
    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)


# ── PATCH + DELETE /api/habits/{habit_id} ─────────────────
# Azure Functions Python v2: two @app.route decorators with the same route
# string conflict at registration time — both return 500.
# Fix: one handler, one route, dispatch on req.method internally.
@app.route(route="habits/{habit_id}", methods=["PATCH", "DELETE"])
def manage_habit(req: func.HttpRequest) -> func.HttpResponse:
    """PATCH: update fields. DELETE: soft-delete (active=False)."""
    habit_id = req.route_params.get("habit_id", "")
    user_id = req.params.get("userId", DEMO_USER_ID)
    try:
        container = _get_habits_container()
        habit = container.read_item(item=habit_id, partition_key=user_id)

        if req.method == "DELETE":
            habit["active"] = False
            container.upsert_item(habit)
            return func.HttpResponse(
                json.dumps({"deleted": True, "id": habit_id}),
                mimetype="application/json",
                status_code=200,
            )

        # PATCH — update editable fields
        body = req.get_json()
        for field in ("name", "why", "targetTime", "durationMins", "frequency"):
            if field in body:
                habit[field] = body[field]
        container.upsert_item(habit)
        return func.HttpResponse(json.dumps(habit), mimetype="application/json", status_code=200)

    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)


# ── POST /api/mood ─────────────────────────────────────────
@app.route(route="mood", methods=["POST"])
def log_mood(req: func.HttpRequest) -> func.HttpResponse:
    """Log a mood check-in. Body: { mood, score, context?, note?, userId? }"""
    try:
        body = req.get_json()
        if not body.get("mood") or body.get("score") is None:
            return func.HttpResponse(
                json.dumps({"error": "mood and score are required"}),
                status_code=400,
            )

        log = {
            "id": str(uuid.uuid4()),
            "userId": body.get("userId", DEMO_USER_ID),
            "mood": body["mood"],
            "score": int(body["score"]),
            "context": body.get("context", "general"),
            "note": body.get("note", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        _get_mood_container().upsert_item(log)

        return func.HttpResponse(
            json.dumps(log),
            mimetype="application/json",
            status_code=201,
        )
    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)
