"""
MindFlow — Cosmos Cleanup Script
Deletes ALL documents from habits, journal_entries, and mood_logs
for DEMO_USER_ID so seed.py can re-run cleanly with deterministic IDs.

Run BEFORE seed.py when you need a clean slate.
"""
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", ".env")))

from azure.cosmos import CosmosClient

ENDPOINT = os.getenv("COSMOS_ENDPOINT")
KEY = os.getenv("COSMOS_KEY")
DB_NAME = os.getenv("COSMOS_DB_NAME", "mindflow")
USER_ID = os.getenv("DEMO_USER_ID", "demo-user-001")

if not ENDPOINT or not KEY:
    print("[ERROR] COSMOS credentials missing")
    sys.exit(1)

client = CosmosClient(ENDPOINT, KEY)
db = client.get_database_client(DB_NAME)


def purge(container_name: str):
    container = db.get_container_client(container_name)
    items = list(container.query_items(
        query="SELECT c.id, c.userId FROM c WHERE c.userId = @uid",
        parameters=[{"name": "@uid", "value": USER_ID}],
        enable_cross_partition_query=False,
    ))
    for item in items:
        container.delete_item(item=item["id"], partition_key=USER_ID)
    print(f"  ✓ Deleted {len(items)} docs from {container_name}")


print(f"🗑️  Cleaning Cosmos — user: {USER_ID}")
purge("habits")
purge("journal_entries")
purge("mood_logs")
print("✅ Cleanup complete. Run seed/seed.py now.")
