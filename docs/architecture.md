# MindFlow — System Architecture

> This document covers the 6-layer architecture, adapter pattern, proxy design, streaming pipeline, and Azure service topology.

---

## Architecture Overview

MindFlow is a **6-layer system** with clean separation between presentation, API gateway, agent orchestration, AI/LLM, data, and infrastructure.

```
┌─────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                          │
│  Next.js 16 (App Router) · TypeScript · TailwindCSS 3.4     │
│  Tabs: Chat · Journal · Habits · Insights                    │
│  Hosted: Azure App Service (Node.js 20 LTS) or local        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS · fetch + getReader() (streaming)
                         │ NEXT_PUBLIC_API_URL (one env var)
┌────────────────────────▼────────────────────────────────────┐
│  API GATEWAY LAYER                                           │
│  FastAPI (Python 3.11) · uvicorn · port 8000                │
│  ┌──────────────────┐   ┌───────────────────────────────┐   │
│  │  Direct routes   │   │  Azure Functions proxy routes │   │
│  │  /chat           │   │  /habits → httpx →            │   │
│  │  /journal        │   │    mindflow-functions.net      │   │
│  │  /insights       │   │  /mood → httpx →              │   │
│  │  /user           │   │    mindflow-functions.net      │   │
│  │  /grove/nudge    │   └───────────────────────────────┘   │
│  │  /calendar       │                                        │
│  │  /memory         │                                        │
│  └──────────────────┘                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  AGENT ORCHESTRATION LAYER (Microsoft Semantic Kernel)       │
│                                                              │
│  🎯 Orchestrator ──────────────────────────────────────────┐ │
│     classify(message) → {agent, mood, urgency}             │ │
│                                                            ▼ │
│  🧠 Memory Agent READ ─────────────────────────────────────┐ │
│     fetch user_memory → assemble {memoryContext} ≤800 tok  │ │
│                                                            ▼ │
│  ┌──────────┬──────────┬──────────┬──────────┐            │ │
│  │🧘 Sage   │📓 River  │✅ Grove  │📊 Lumen  │            │ │
│  │Mindful   │Journal   │Habit     │Insights  │            │ │
│  │Coach     │Reflection│Coach     │+RAG      │            │ │
│  └──────────┴──────────┴──────────┴──────────┘            │ │
│                          invoke_stream() →                 │ │
│                          StreamingResponse chunks          │ │
│                                                            ▼ │
│  🧠 Memory Agent WRITE ────────────────────────────────────┘ │
│     extract facts → score → decay → upsert user_memory      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  AI / LLM LAYER                                              │
│  Azure AI Foundry → GPT-4o (chat + JSON mode)               │
│  Azure OpenAI → text-embedding-3-small-1 (1536 dims)        │
│                                                              │
│  Endpoint quirk: AI Foundry URL includes /openai/v1 suffix  │
│  → urlparse strips to base domain before passing to SDK     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  DATA LAYER                                                  │
│  ┌─────────────────────┐  ┌──────────────────────────────┐  │
│  │ Azure Cosmos DB      │  │ Azure AI Search               │  │
│  │ cosmos-jmagno-2026  │  │ search-jmagno-2026           │  │
│  │ database: mindflow  │  │ index: journal-index         │  │
│  │                     │  │                              │  │
│  │ Collections:        │  │ Fields:                      │  │
│  │ · users             │  │ · id (key)                   │  │
│  │ · journal_entries   │  │ · userId (filterable)        │  │
│  │ · habits            │  │ · content (searchable)       │  │
│  │ · mood_logs         │  │ · embedding (1536-dim vector)│  │
│  │ · user_memory       │  │ · mood, sentiment, themes    │  │
│  │                     │  │ · timestamp                  │  │
│  │ Partition key: /userId │                              │  │
│  └─────────────────────┘  └──────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  SERVERLESS / SCHEDULED LAYER                                │
│  Azure Functions v2 Python (mindflow-functions.azurewebsites)│
│                                                              │
│  HTTP routes (7 total):                                      │
│  · GET  /api/habits                                         │
│  · POST /api/habits                                         │
│  · PATCH /api/habits/{id}/log    (add today, recalc streak) │
│  · PATCH /api/habits/{id}/unlog  (remove today, recalc)     │
│  · PATCH /api/habits/{id}        (edit name/why/targetTime) │
│  · DELETE /api/habits/{id}       (soft-delete active=false) │
│  · POST /api/mood                                           │
│                                                             │
│  Timer trigger (Sunday 08:00 UTC):                         │
│  · Fetches user IDs from Cosmos (user_memory container)    │
│  · Calls GET /insights?userId=...&days=14 concurrently     │
│  · Pre-warms weekSummary before users open the app         │
└─────────────────────────────────────────────────────────────┘
```

---

## Adapter Pattern (Provider Classes)

All external dependencies are accessed through Python provider classes in `backend/providers/`. Each class has one Azure implementation. Post-hackathon, swap any service by writing a new class — zero changes to agent logic or API routes.

| Provider class | Interface | Current implementation | Swap to |
|---|---|---|---|
| `CosmosRepository` | `IUserRepository` | Azure Cosmos DB Core SQL API | Postgres, MongoDB |
| `SearchProvider` | `IVectorStore` | Azure AI Search (hybrid) | Pinecone, Qdrant, Weaviate |
| `build_kernel()` | `ILLMProvider` | Azure AI Foundry → GPT-4o | OpenAI API, Ollama (local) |
| `IFileStore` (stub) | `IFileStore` | Not implemented | Azure Blob Storage (voice v2) |

---

## Proxy Architecture

**The frontend has one API URL.** Azure Functions are an internal implementation detail — the frontend never calls them directly.

```
Frontend (Next.js)
  ↓ NEXT_PUBLIC_API_URL = http://localhost:8000
FastAPI Backend
  ├── /chat           → Semantic Kernel agent pipeline (internal)
  ├── /journal        → Cosmos DB direct (internal)
  ├── /insights       → Cosmos DB + Memory Agent (internal)
  ├── /user           → Cosmos DB direct (internal)
  ├── /grove/nudge    → GPT-4o direct (internal)
  ├── /calendar       → Cosmos DB direct (internal)
  ├── /memory         → Cosmos DB direct (internal)
  ├── /habits/*       → httpx → Azure Functions /api/habits/*
  └── /mood           → httpx → Azure Functions /api/mood
```

CORS is configured on FastAPI only (`allow_origins=[localhost:3000, FRONTEND_URL]`). Azure Functions use Anonymous auth level — authentication boundary is FastAPI, not the Functions.

---

## Streaming Pipeline (POST /chat)

```
1. Parse ChatRequest {message, userId, chatHistory, agentOverride?}

2. Orchestrator.classify(message, conversationHistory)
   → {agent, mood, urgency, confidence}
   → agent routing keys: "mindfulness" | "journal" | "habit" | "insights"
     (persona names Sage/River/Grove/Lumen are resolved in _get_specialist)
   → CONTINUITY RULE: if last assistant message contains a habit-creation question → force `habit`
   → SKIP if agentOverride is set (saves ~300ms)

3. memory_agent.read(userId, mood, urgency)
   → Cosmos fetch → format memoryContext string
   → Returns "" on failure (graceful degradation)

4. _get_specialist(agent, memory_context)
   → Sage, River, Grove: synchronous factory (habit_agent.get_agent is def, not async)
     · Grove path: _get_specialist first awaits db.get_habits() (Cosmos direct,
       not Functions proxy), then calls the sync factory with live habit list,
       today's completions, and streaks injected into the system prompt
   → Lumen: async factory — insights_agent.get_agent is async def
             awaits AI Search hybrid search + mood logs + habit stats
             before the ChatCompletionAgent is constructed

5. yield "[AGENT:{agent}]\n"    ← first chunk — frontend extracts + strips
                                   used to set agent badge before content arrives

6. async for chunk in agent.invoke_stream(history):
   → _chunk_text(chunk)         ← extracts text safely from StreamingChatMessageContent
   → buffer hold: _HOLD = 14 chars (max marker length) — prevents partial marker leak
   → River: buffer check for [SAVE_ENTRY]...[/SAVE_ENTRY]
      · content before [SAVE_ENTRY] → yield to user
      · block content → capture, do not yield
      · on [/SAVE_ENTRY] → asyncio.ensure_future(_parse_and_save_entry(...))
      · then yield: "✓ Entry saved to your Journal."
   → Grove: buffer check for [CREATE_HABIT]...[/CREATE_HABIT]
      · block content → capture, do not yield
      · on [/CREATE_HABIT] → asyncio.ensure_future(_parse_and_create_habit(...))
      · _parse_and_create_habit writes directly to Cosmos via db.create_habit()
      · then yield: "✓ \"Habit Name\" has been added to your Habits tab."
   → All other content: yield chunk directly

7. try/except ValueError:
   → Catches SK + FastAPI OpenTelemetry ContextVar cleanup error
   → Ignored — all content already yielded before cleanup fires

8. asyncio.ensure_future(memory_agent.write(userId, message, full_response))
   → Runs after stream completes, non-blocking
```

---

## Azure AI Search — RAG Pipeline

Used exclusively by Lumen (Insights Agent) before constructing its `ChatCompletionAgent`.

### Index schema (`journal-index`)
```
id          → String (key)
userId      → String (filterable, not searchable)
content     → String (searchable — raw journal entry text)
embedding   → Collection(Edm.Single) — 1536 dimensions, cosine similarity
mood        → String (filterable)
sentiment   → String (filterable)
themes      → Collection(Edm.String) (filterable, facetable)
timestamp   → DateTimeOffset (filterable, sortable)
```

### Hybrid search query
```python
results = search_client.search(
    search_text=query,                    # keyword component
    vector_queries=[VectorizedQuery(      # vector component
        vector=query_embedding,
        k_nearest_neighbors=5,
        fields="embedding"
    )],
    filter=f"userId eq '{user_id}'",      # partition by user
    select=["content", "mood", "themes", "timestamp"],
    top=5
)
```

Hybrid search finds semantically relevant entries even when no exact keywords match. "Why do I feel anxious at work?" will surface "I felt overwhelmed during the project deadline" — zero keyword overlap, high vector similarity.

### Indexing
`bulk_index.py` runs once to embed all journal entries. New entries saved by River via `_parse_and_save_entry()` go to Cosmos only — they are **not** automatically re-indexed into AI Search. Re-indexing requires re-running `seed/bulk_index.py` manually. Before re-seeding, `purge_index(userId)` is called to remove stale orphaned documents.

> **Production fix:** Add `asyncio.ensure_future(search_provider.bulk_index([entry]))` in `_parse_and_save_entry()` after the Cosmos write. Same fire-and-forget pattern already used for memory writes — zero stream impact if it fails.

---

## Environment Variables

### `backend/.env` (gitignored — never committed)
```
# Azure AI Foundry
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/openai/v1
AZURE_OPENAI_KEY=<key>
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBED_DEPLOYMENT=text-embedding-3-small-1   # NOTE: -1 suffix required
AZURE_OPENAI_API_VERSION=2024-10-21

# Cosmos DB
COSMOS_ENDPOINT=https://<account>.documents.azure.com:443/
COSMOS_KEY=<key>
COSMOS_DB_NAME=mindflow

# AI Search
SEARCH_ENDPOINT=https://<service>.search.windows.net
SEARCH_KEY=<key>
SEARCH_INDEX_NAME=journal-index

# Azure Functions (internal proxy target)
FUNCTIONS_HABIT_URL=https://mindflow-functions.azurewebsites.net
FUNCTIONS_MOOD_URL=https://mindflow-functions.azurewebsites.net

# App
DEMO_USER_ID=demo-user-001
FRONTEND_URL=http://localhost:3000
```

### `frontend/.env.local` (gitignored — never committed)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Azure Functions App Settings (set in Azure Portal)
```
COSMOS_ENDPOINT=<same as backend>
COSMOS_KEY=<same as backend>
COSMOS_DB_NAME=mindflow
DEMO_USER_ID=demo-user-001
BACKEND_URL=<real backend URL — needed for timer trigger>
AzureWebJobsStorage=UseDevelopmentStorage=true
FUNCTIONS_WORKER_RUNTIME=python
```

---

## Known Quirks & Gotchas

| Issue | Root cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'backend'` | Running `uvicorn` from `backend/` instead of repo root. Imports use `backend.xxx` paths. | Always run `python -m uvicorn backend.main:app` from repo root. |
| Azure AI Foundry endpoint 404 | AI Foundry URL includes `/openai/v1` suffix. SDK appends its own path, causing double-append. | `urlparse` strips to base domain in `kernel.py`, `orchestrator.py`, `memory_agent.py`. |
| SK streaming `ValueError` | Semantic Kernel's OpenTelemetry cleanup calls `ContextVar.reset()` across async contexts on generator teardown. Known SK + FastAPI interaction. | `try/except ValueError` around SK streaming loop — suppressed, all content already yielded. |
| SK `invoke_stream` `TypeError` | SK 1.41.3 yields `StreamingChatMessageContent` directly (not a list). `bool()` triggers `__len__()` → `TypeError`. | `_chunk_text()` helper uses `c is not None` instead of truthiness, `str()` for non-string types. |
| Memory WRITE JSON fences | Model occasionally wraps `json_object` response in ` ```json...``` ` fences despite the mode setting. | Fence-strip pass before `json.loads()` in `memory_agent.write()`. |
| Azure Functions v2 route conflict | Two `@app.route` decorators sharing the same route string silently fail — both handlers return 500. | Single handler with `methods=["PATCH", "DELETE"]`, dispatches on `req.method` internally. |
| Azure Functions v2 route params | Python v1 injected route params as function args. v2 requires `req.route_params.get("param_name")`. | All habit handlers use `req.route_params.get(...)`. |

---

## Scalability Roadmap

| Feature | What's needed |
|---|---|
| 🎙️ Voice journaling | Implement `IFileStore` with Azure Blob Storage upload. Add `/journal/voice` route that transcribes with Azure Speech API and feeds to River. |
| 📱 Native mobile | React Native app pointing at the same FastAPI backend — zero backend changes needed. |
| 🔒 Privacy mode (on-device) | New `ILLMProvider` implementation using Ollama local LLM. Swap in one config line. |
| 📅 Calendar integration | Microsoft Graph API. Grove reads busy-week data to adjust habit coaching strategy. |
| 🔐 Auth | Azure AD B2C. Currently using `DEMO_USER_ID` env var. Cosmos partition key is already `/userId` — multi-user is a config change, not an architectural one. |
| 📈 Advanced analytics | Mood heatmap, habit completion matrix, per-theme emotional arc visualization. |
| 🔍 Auto-index on save | Add `asyncio.ensure_future(search_provider.bulk_index([entry]))` to `_parse_and_save_entry()` — new journal entries appear in Lumen's RAG immediately, not just after manual re-index. One line of code. |
