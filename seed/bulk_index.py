"""One-time script: bulk-index Cosmos journal entries into Azure AI Search."""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", ".env"), override=True)


async def run():
    from backend.providers import cosmos_repository as db
    from backend.providers import search_provider

    # 1. Fetch seeded entries
    print("Fetching journal entries from Cosmos...")
    entries = await db.get_recent_journal_entries("demo-user-001", limit=20)
    print(f"  -> Found {len(entries)} entries")
    for e in entries:
        ts = e.get("timestamp", "")[:10]
        summary = e.get("summary", "")[:60]
        print(f"     [{ts}] {summary}")

    if not entries:
        print("[ERROR] No entries found — check COSMOS credentials and seed data")
        return

    # 2. Purge stale index docs, then re-index fresh
    print()
    print("Purging stale AI Search entries...")
    purged = await search_provider.purge_index("demo-user-001")
    print(f"  -> Purged: {purged} old documents")

    import asyncio as _a2
    await _a2.sleep(2)  # let deletions settle

    print()
    print("Bulk-indexing into Azure AI Search...")
    indexed = await search_provider.bulk_index(entries)
    print(f"  -> Indexed: {indexed}/{len(entries)} documents")

    # 3. Test query — give index a moment to catch up
    import asyncio as _a
    print()
    print("Waiting 3s for index to settle...")
    await _a.sleep(3)

    print("Test query: 'feeling anxious'...")
    result = await search_provider.search("feeling anxious", "demo-user-001", top_k=3)
    if result:
        print("  -> Results returned:")
        for line in result.splitlines()[:10]:
            print(f"     {line}")
    else:
        print("  -> No results yet (index may need another moment — try again in 30s)")


asyncio.run(run())
