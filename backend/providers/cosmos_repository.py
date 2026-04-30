"""
MindFlow — Cosmos DB Repository
Wraps all Cosmos DB operations. Hour 2 implements only the 3 methods
needed by the Memory Agent. Additional methods added per phase:
  Hour 3: save_journal_entry(), get_recent_journal_entries()
  Hours 5–6: get_habits(), log_habit() [these go to Azure Functions]
  Hour 7: get_mood_logs()
"""
import os
from typing import Optional
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from dotenv import load_dotenv

_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(dotenv_path=_ENV_PATH, override=True)

_ENDPOINT = os.getenv("COSMOS_ENDPOINT", "")
_KEY = os.getenv("COSMOS_KEY", "")
_DB_NAME = os.getenv("COSMOS_DB_NAME", "mindflow")

_client = CosmosClient(_ENDPOINT, _KEY)
_db = _client.get_database_client(_DB_NAME)


def _container(name: str):
    return _db.get_container_client(name)


# ── Hour 2: Memory Agent methods ───────────────────────────

async def get_user(user_id: str) -> Optional[dict]:
    """Fetch the user document from the users collection."""
    try:
        return _container("users").read_item(item=user_id, partition_key=user_id)
    except CosmosResourceNotFoundError:
        return None


async def get_user_memory(user_id: str) -> Optional[dict]:
    """
    Fetch the user_memory document for this user.
    Returns None if no memory doc exists yet (new user).
    The id of user_memory equals the userId — one doc per user.
    """
    try:
        return _container("user_memory").read_item(item=user_id, partition_key=user_id)
    except CosmosResourceNotFoundError:
        return None


async def upsert_user_memory(memory: dict) -> dict:
    """
    Upsert the user_memory document.
    Uses Cosmos upsert — creates if missing, replaces if exists.
    The document id must equal userId.
    NOTE: Last-write-wins if two requests race — acceptable for hackathon demo.
    Log all errors — do not silently swallow failures.
    """
    return _container("user_memory").upsert_item(memory)


# ── Hour 3: Journal methods (added when River agent is built) ──

async def save_journal_entry(entry: dict) -> dict:
    """Save a journal entry to Cosmos + async index into AI Search (Hour 7)."""
    return _container("journal_entries").upsert_item(entry)


async def get_recent_journal_entries(user_id: str, limit: int = 10) -> list[dict]:
    """Fetch the most recent N journal entries for a user."""
    items = list(_container("journal_entries").query_items(
        query=(
            "SELECT TOP @limit * FROM c WHERE c.userId = @uid "
            "ORDER BY c.timestamp DESC"
        ),
        parameters=[
            {"name": "@uid", "value": user_id},
            {"name": "@limit", "value": limit},
        ],
        enable_cross_partition_query=False,
    ))
    return items


# ── Hour 7: Mood logs (added when Lumen agent is built) ───

async def get_mood_logs(user_id: str, days: int = 7) -> list[dict]:
    """Fetch recent mood logs for trend analysis."""
    items = list(_container("mood_logs").query_items(
        query=(
            "SELECT TOP @limit * FROM c WHERE c.userId = @uid "
            "ORDER BY c.timestamp DESC"
        ),
        parameters=[
            {"name": "@uid", "value": user_id},
            {"name": "@limit", "value": days},
        ],
        enable_cross_partition_query=False,
    ))
    return items


# ── Hour 8: Habit reads for Grove agent context ────────────

async def get_habits(user_id: str) -> list[dict]:
    """Fetch active habits for a user — used by Grove to inject live data."""
    items = list(_container("habits").query_items(
        query=(
            "SELECT * FROM c WHERE c.userId = @uid AND c.active = true "
            "ORDER BY c.name"
        ),
        parameters=[{"name": "@uid", "value": user_id}],
        enable_cross_partition_query=False,
    ))
    return items
