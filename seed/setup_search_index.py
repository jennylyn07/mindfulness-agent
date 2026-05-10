"""
MindFlow — AI Search Index Setup Script
─────────────────────────────────────────────────────────────────────────────
Creates (or recreates) the 'journal-index' in Azure AI Search with the exact
schema and vector search configuration required by search_provider.py.

Run this ONCE before running bulk_index.py.
If the index already exists it will be updated in-place (create_or_update).

Run: python seed/setup_search_index.py
"""
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

_env_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "backend", ".env")
)
load_dotenv(dotenv_path=_env_path)

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchProfile,
)

ENDPOINT   = os.getenv("SEARCH_ENDPOINT", "")
KEY        = os.getenv("SEARCH_KEY", "")
INDEX_NAME = os.getenv("SEARCH_INDEX_NAME", "journal-index")

if not ENDPOINT or not KEY:
    print("[ERROR] SEARCH_ENDPOINT and SEARCH_KEY must be set in backend/.env")
    sys.exit(1)


def build_index() -> SearchIndex:
    fields = [
        # Key field
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
        ),
        # User filter
        SimpleField(
            name="userId",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        # Full-text search field (Standard analyser)
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
        ),
        # Mood + sentiment — retrievable and filterable
        SimpleField(
            name="mood",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="sentiment",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        # Themes collection — retrievable, filterable, facetable
        SearchField(
            name="themes",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
            facetable=True,
        ),
        # Timestamp — DateTimeOffset for correct sort/filter behaviour
        SimpleField(
            name="timestamp",
            type=SearchFieldDataType.DateTimeOffset,
            filterable=True,
            sortable=True,
        ),
        # Vector field — 1536-dim embeddings (text-embedding-3-small-1)
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="hnsw-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="hnsw-config"),
        ],
        profiles=[
            VectorSearchProfile(
                name="hnsw-profile",
                algorithm_configuration_name="hnsw-config",
            ),
        ],
    )

    return SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
    )


def main():
    print(f"🔍 MindFlow Search Index Setup")
    print(f"   Endpoint:   {ENDPOINT}")
    print(f"   Index name: {INDEX_NAME}\n")

    client = SearchIndexClient(
        endpoint=ENDPOINT,
        credential=AzureKeyCredential(KEY),
    )

    index = build_index()

    try:
        result = client.create_or_update_index(index)
        print(f"✅ Index '{result.name}' created/updated successfully.")
        print(f"   Fields: {[f.name for f in result.fields]}")
        print(f"\n⚠️  NEXT: Run python seed/bulk_index.py to embed and index journal entries.")
    except Exception as e:
        print(f"[ERROR] Failed to create index: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
