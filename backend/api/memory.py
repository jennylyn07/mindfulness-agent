"""MindFlow — Memory management routes.

Allows the frontend to view and manage the user's stored memory facts.
Backed by the user_memory document in Cosmos (one doc per user).
"""

import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.providers import cosmos_repository as db

router = APIRouter()

_DEMO_USER_ID = os.getenv("DEMO_USER_ID", "demo-user-001")


class MemoryToggleRequest(BaseModel):
    enabled: bool


class MemoryFactUpdateRequest(BaseModel):
    content: str


class MemoryFactCreateRequest(BaseModel):
    content: str
    source: str = "manual"
    importance: float = 0.7


def _ensure_fact_ids(memory: dict) -> bool:
    facts = memory.get("facts", []) or []
    changed = False
    for f in facts:
        if not isinstance(f, dict):
            continue
        if not f.get("id"):
            f["id"] = str(uuid.uuid4())
            changed = True
    if changed:
        memory["facts"] = facts
    return changed


@router.get("/memory")
async def get_memory(userId: str = _DEMO_USER_ID):
    """Return the user's user_memory document (creating a shell doc if missing)."""
    memory = await db.get_user_memory(userId)
    if not memory:
        from backend.agents.memory_agent import _empty_memory

        memory = _empty_memory(userId)
        memory = await db.upsert_user_memory(memory)

    changed = _ensure_fact_ids(memory)
    if "memoryEnabled" not in memory:
        memory["memoryEnabled"] = True
        changed = True

    if changed:
        memory = await db.upsert_user_memory(memory)

    return memory


@router.patch("/memory/toggle")
async def toggle_memory(body: MemoryToggleRequest, userId: str = _DEMO_USER_ID):
    memory = await db.get_user_memory(userId)
    if not memory:
        from backend.agents.memory_agent import _empty_memory

        memory = _empty_memory(userId)

    _ensure_fact_ids(memory)
    memory["memoryEnabled"] = bool(body.enabled)

    try:
        return await db.upsert_user_memory(memory)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/facts")
async def create_fact(body: MemoryFactCreateRequest, userId: str = _DEMO_USER_ID):
    memory = await db.get_user_memory(userId)
    if not memory:
        from backend.agents.memory_agent import _empty_memory

        memory = _empty_memory(userId)

    _ensure_fact_ids(memory)
    now_iso = datetime.now(timezone.utc).isoformat()

    facts = memory.get("facts", []) or []
    facts.append({
        "id": str(uuid.uuid4()),
        "content": body.content,
        "source": body.source,
        "importance": float(body.importance),
        "createdAt": now_iso,
        "lastReferencedAt": now_iso,
    })

    memory["facts"] = facts
    memory["updatedAt"] = now_iso

    try:
        return await db.upsert_user_memory(memory)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/memory/facts/{fact_id}")
async def update_fact(fact_id: str, body: MemoryFactUpdateRequest, userId: str = _DEMO_USER_ID):
    memory = await db.get_user_memory(userId)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    changed = _ensure_fact_ids(memory)
    facts = memory.get("facts", []) or []

    found = False
    for f in facts:
        if isinstance(f, dict) and f.get("id") == fact_id:
            f["content"] = body.content
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="Fact not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    memory["facts"] = facts
    memory["updatedAt"] = now_iso

    try:
        return await db.upsert_user_memory(memory)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/facts/{fact_id}")
async def delete_fact(fact_id: str, userId: str = _DEMO_USER_ID):
    memory = await db.get_user_memory(userId)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    _ensure_fact_ids(memory)
    facts = memory.get("facts", []) or []
    new_facts = [f for f in facts if not (isinstance(f, dict) and f.get("id") == fact_id)]

    if len(new_facts) == len(facts):
        raise HTTPException(status_code=404, detail="Fact not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    memory["facts"] = new_facts
    memory["updatedAt"] = now_iso

    try:
        return await db.upsert_user_memory(memory)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
