"""
MindFlow Azure Functions — Root Entry Point
Python v2 programming model (decorator-based, single app instance).

Routes:
  GET  /api/habits              — list habits for a user
  POST /api/habits              — create a new habit
  PATCH /api/habits/{id}/log   — mark habit done today (recalculates streak)
  POST /api/mood               — log a mood check-in

Called by FastAPI backend (backend/api/habits.py, backend/api/mood.py),
not by the frontend directly.
"""
import json
import os
import uuid
from datetime import datetime, timezone

import azure.functions as func
from azure.cosmos import CosmosClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


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

        # Recalculate streak (UTC calendar days)
        streak = 0
        check = datetime.now(timezone.utc).date()
        for date_str in reversed(logs):
            log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            diff = (check - log_date).days
            if diff == streak:
                streak += 1
                check = log_date
            else:
                break

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

        # Recalculate streak from scratch
        streak = 0
        check = datetime.now(timezone.utc).date()
        for date_str in reversed(sorted(logs)):
            log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            diff = (check - log_date).days
            if diff == streak:
                streak += 1
                check = log_date
            else:
                break

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
