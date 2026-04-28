"""
MindFlow Azure Functions — Habits
Python v2 programming model (decorator-based).
All 3 habit routes in one function app — appears as one app in the Azure portal.

Called by FastAPI (backend/api/habits.py) — NOT by the frontend directly.
"""
import json
import os
import uuid
from datetime import datetime, timezone
import azure.functions as func
from azure.cosmos import CosmosClient, PartitionKey

app = func.FunctionApp()

COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]
COSMOS_KEY = os.environ["COSMOS_KEY"]
DB_NAME = os.environ.get("COSMOS_DB_NAME", "mindflow")
DEMO_USER_ID = os.environ.get("DEMO_USER_ID", "demo-user-001")


def get_container():
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    db = client.get_database_client(DB_NAME)
    return db.get_container_client("habits")


# ── GET /api/habits ────────────────────────────────────────
@app.route(route="habits", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_habits(req: func.HttpRequest) -> func.HttpResponse:
    user_id = req.params.get("userId", DEMO_USER_ID)
    try:
        container = get_container()
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
@app.route(route="habits", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
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
        container = get_container()
        container.upsert_item(habit)
        return func.HttpResponse(json.dumps(habit), mimetype="application/json", status_code=201)
    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)


# ── PATCH /api/habits/{habit_id}/log ──────────────────────
@app.route(route="habits/{habit_id}/log", methods=["PATCH"], auth_level=func.AuthLevel.ANONYMOUS)
def log_habit(req: func.HttpRequest, habit_id: str) -> func.HttpResponse:
    """Mark habit done for today (UTC). Recalculates streak."""
    user_id = req.params.get("userId", DEMO_USER_ID)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        container = get_container()
        habit = container.read_item(item=habit_id, partition_key=user_id)

        logs: list = habit.get("logs", [])
        if today not in logs:
            logs.append(today)
            logs.sort()

        # Recalculate streak (UTC calendar days — D4)
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
