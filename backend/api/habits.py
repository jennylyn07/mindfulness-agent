"""
MindFlow — Habit proxy routes
Frontend calls these FastAPI routes. FastAPI proxies to Azure Functions internally.
Azure Functions handle the actual Cosmos reads/writes (Decision 2 — D2).
Frontend never calls Azure Functions directly.
"""
import os
import httpx
from fastapi import APIRouter, HTTPException
from backend.models.schemas import HabitCreate

router = APIRouter()

_FUNCTIONS_HABIT_URL = os.getenv("FUNCTIONS_HABIT_URL", "http://localhost:7071")
_DEMO_USER_ID = os.getenv("DEMO_USER_ID", "demo-user-001")


@router.get("/habits")
async def get_habits(userId: str = _DEMO_USER_ID):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(
                f"{_FUNCTIONS_HABIT_URL}/api/habits",
                params={"userId": userId},
            )
            r.raise_for_status()
            return r.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Habits function unreachable: {e}")


@router.post("/habits", status_code=201)
async def create_habit(body: HabitCreate):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.post(
                f"{_FUNCTIONS_HABIT_URL}/api/habits",
                json=body.model_dump(),
            )
            r.raise_for_status()
            return r.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Habits function unreachable: {e}")


@router.patch("/habits/{habit_id}/log")
async def log_habit(habit_id: str, userId: str = _DEMO_USER_ID):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.patch(
                f"{_FUNCTIONS_HABIT_URL}/api/habits/{habit_id}/log",
                params={"userId": userId},
            )
            r.raise_for_status()
            return r.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Habits function unreachable: {e}")
