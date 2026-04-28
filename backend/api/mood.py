"""
MindFlow — Mood proxy route
Frontend calls POST /mood → FastAPI proxies to Azure Functions (mood log).
Azure Functions write to Cosmos mood_logs container.
"""
import os
import httpx
from fastapi import APIRouter, HTTPException
from backend.models.schemas import MoodLogRequest

router = APIRouter()

_FUNCTIONS_MOOD_URL = os.getenv("FUNCTIONS_MOOD_URL", "http://localhost:7071")


@router.post("/mood", status_code=201)
async def log_mood(body: MoodLogRequest):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.post(
                f"{_FUNCTIONS_MOOD_URL}/api/mood",
                json=body.model_dump(),
            )
            r.raise_for_status()
            return r.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Mood function unreachable: {e}")
