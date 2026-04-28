"""
MindFlow Azure Functions — Mood
POST /api/mood — logs a mood check-in to Cosmos DB.
Called by FastAPI (backend/api/mood.py) — NOT by the frontend directly.
"""
import json
import os
import uuid
from datetime import datetime, timezone
import azure.functions as func
from azure.cosmos import CosmosClient

app = func.FunctionApp()

COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]
COSMOS_KEY = os.environ["COSMOS_KEY"]
DB_NAME = os.environ.get("COSMOS_DB_NAME", "mindflow")
DEMO_USER_ID = os.environ.get("DEMO_USER_ID", "demo-user-001")


@app.route(route="mood", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def log_mood(req: func.HttpRequest) -> func.HttpResponse:
    """Log a mood check-in. Body: { mood, score, context, note, userId? }"""
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

        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        db = client.get_database_client(DB_NAME)
        db.get_container_client("mood_logs").upsert_item(log)

        return func.HttpResponse(
            json.dumps(log),
            mimetype="application/json",
            status_code=201,
        )
    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)
