"""
MindFlow — Search Provider
Azure AI Search integration for journal entry RAG (Lumen agent).

Responsibilities:
  - bulk_index(entries): upsert journal entries into the search index with embeddings
  - search(query, user_id, top_k): semantic + keyword hybrid search over journal entries
  - Returns a formatted string for injection into Lumen's {journalContext} slot

The search index schema mirrors the JournalEntry Pydantic model.
Index must be created in the portal or via az CLI before bulk_index is called.
"""
import os
import json
from typing import List, Optional
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from backend.kernel import get_embedding


_SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT", "")
_SEARCH_KEY = os.getenv("SEARCH_KEY", "")
_INDEX_NAME = os.getenv("SEARCH_INDEX_NAME", "journal-index")


def _get_client() -> SearchClient:
    return SearchClient(
        endpoint=_SEARCH_ENDPOINT,
        index_name=_INDEX_NAME,
        credential=AzureKeyCredential(_SEARCH_KEY),
    )


async def bulk_index(entries: List[dict]) -> int:
    """
    Upsert journal entries into the AI Search index.
    Generates embeddings for each entry's content field.
    Returns number of entries successfully indexed.
    """
    if not _SEARCH_ENDPOINT or not _SEARCH_KEY:
        print("[SearchProvider] SEARCH_ENDPOINT or SEARCH_KEY not set — skipping index")
        return 0

    try:
        client = _get_client()
        documents = []

        for entry in entries:
            try:
                embedding = await get_embedding(entry.get("content", ""))
                documents.append({
                    "id": entry["id"],
                    "userId": entry.get("userId", ""),
                    "content": entry.get("content", ""),
                    "mood": entry.get("moodAtEntry", "okay"),
                    "sentiment": entry.get("sentiment", "neutral"),
                    "themes": entry.get("themes", []),
                    "timestamp": entry.get("timestamp", ""),
                    "embedding": embedding,          # matches index field name
                })
            except Exception as e:
                print(f"[SearchProvider] Failed to embed entry {entry.get('id')}: {e}")

        if not documents:
            return 0

        try:
            result = client.upload_documents(documents=documents)
            succeeded = sum(1 for r in result if r.succeeded)
            print(f"[SearchProvider] Indexed {succeeded}/{len(documents)} entries")
            return succeeded
        except Exception as e:
            print(f"[SearchProvider] bulk_index failed: {e}")
            return 0

    except Exception as e:
        print(f"[SearchProvider] bulk_index outer error: {e}")
        return 0


async def search(
    query: str,
    user_id: str,
    top_k: int = 5,
) -> str:
    """
    Hybrid search (vector + keyword) over the journal index filtered by userId.
    Returns a formatted string for injection into Lumen's {journalContext} prompt slot.
    Returns empty string on any error (graceful degradation).
    """
    if not _SEARCH_ENDPOINT or not _SEARCH_KEY:
        return ""

    try:
        client = _get_client()
        query_vector = await get_embedding(query)

        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top_k,
            fields="embedding",
        )

        results = client.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=f"userId eq '{user_id}'",
            select=["content", "themes", "mood", "timestamp"],
            top=top_k,
        )

        entries = []
        for r in results:
            date = r.get("timestamp", "")[:10]
            mood = r.get("mood", "")
            snippet = r.get("content", "")[:150]
            themes = ", ".join(r.get("themes", []))
            entries.append(f"[{date}] Mood: {mood} | Themes: {themes}\n{snippet}")

        if not entries:
            return ""

        return "Recent journal entries (most relevant):\n\n" + "\n\n".join(entries)

    except Exception as e:
        print(f"[SearchProvider] search() failed: {e}")
        return ""
