# 🌿 MindFlow
### AI-Powered Multi-Agent Mindfulness, Journaling & Habit-Tracking Assistant
**Code Without Barriers Hackathon 2026 — ASEAN Edition**
Problem Statement — AI Mindfulness Track
Participant: Jennylyn Magno | Solo | Philippines

---

## The Problem

People who want to build healthier habits and reflect more deeply face three compounding problems. Fragmentation — the average person uses 3.4 separate apps for journaling, habit tracking, and meditation, none of which share context. Lack of personalization — tools that respond identically regardless of your mood, history, or the reason you started. And inconsistency — no system that understands *why* you missed a habit, or connects your emotional patterns to your progress over time.

The result: 80% of new habits fail within two weeks. Not from lack of effort — from lack of the right support at the right moment.

A traditional wellness app records what you do. It reacts after things go wrong. A multi-agent system personalizes every interaction — each specialist focused on one job, all sharing the same memory of who you are.

---

## The Solution

MindFlow is a fully personalized multi-agent AI system where six specialized agents collaborate in real time to support a user's complete personal growth journey — through a single, natural chat interface.

> *"Jen types 'I feel anxious today.' The Orchestrator classifies the intent in 200ms. The Memory Agent reads her stored context — she's been stressed about a project deadline all week and responds well to structured breathing. Sage, the Mindfulness Coach, delivers a box breathing exercise tailored to high urgency — not a generic response, one that references her specific pattern. After the conversation, the Memory Agent silently writes a new fact: 'box breathing effective for work-related anxiety spikes.' River saves a journal entry. The next time Jen is anxious, every agent already knows what works."*

---

## Architecture

```
User Message (chat)
        │
        ▼
┌───────────────────────────────────────────────────────┐
│                  Next.js 14 Frontend                  │
│     fetch + ReadableStream   ·   NEXT_PUBLIC_API_URL  │
└──────────────────────────┬────────────────────────────┘
                           │  POST /chat
                           ▼
┌───────────────────────────────────────────────────────┐
│               FastAPI Backend (Python 3.11)           │
│     StreamingResponse · CORS · Pydantic · 8 routers   │
└──┬────────────────────────┬──────────────────────────┘
   │                        │
   ▼                        ▼
┌──────────────┐    ┌────────────────────────────────┐
│ Orchestrator │    │         Memory Agent            │
│ JSON mode    │    │  READ before · WRITE after      │
│ temp=0       │    │  weekSummary · TTL-gated · decay│
│ ~200ms       │    └──────────────┬─────────────────┘
└──────────────┘                   │
   classify                  memory context
      │                            │
      ▼                            ▼
┌──────────┬──────────┬──────────┬──────────┐
│  Sage    │  River   │  Grove   │  Lumen   │
│Mindful-  │Journal & │ Habit    │Insights  │
│ness Coach│Reflection│ Coach    │& RAG     │
└────┬─────┴────┬─────┴────┬─────┴────┬────┘
     │          │          │          │
     ▼          ▼          ▼          ▼
┌───────────────────────────────────────────┐
│   Semantic Kernel ChatCompletionAgent     │
│         invoke_stream(ChatHistory)        │
└──────────────────┬────────────────────────┘
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────────┐
│Azure     │ │Azure     │ │Azure         │
│OpenAI    │ │Cosmos DB │ │AI Search     │
│GPT-4o    │ │5 collec- │ │journal-index │
│          │ │tions     │ │hybrid search │
└──────────┘ └──────────┘ └──────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  Azure Functions v2  │
        │  habits · mood       │
        │  weekly timer        │
        └──────────────────────┘
```

---

## The Six Agents

### 🎯 Agent 1 — The Orchestrator
**Role:** Intent classification and routing

Receives every user message and classifies intent into one of four categories — mindfulness, journal, habit, or insights — in under 300ms. Returns a structured JSON result `{agent, mood, urgency, confidence}`. Falls back silently to "journal" on any failure — the user never sees a routing error. Using `agentOverride`, downstream components like the Grove chat head can bypass the Orchestrator entirely when intent is predetermined, saving ~300ms per message.

**Technology:** GPT-4o (temp=0.0) · JSON mode · Pydantic `OrchestratorResult` · `agentOverride` bypass · Silent fallback to "journal"

---

### 🧠 Agent 2 — The Memory Agent
**Role:** Persistent user context — reads before every response, writes after

The invisible agent that makes every other agent feel like it knows you. Before every specialist response, it fetches stored facts, themes, breakthroughs, preferences, and a weekly narrative from Cosmos DB — assembled into an 800-token context block injected into the specialist's system prompt. After every response, a second GPT-4o call extracts new facts from the exchange. Facts scored ≥0.6 are stored; facts <0.6 are discarded. Stale facts (>14 days unreferenced) decay by 0.05. Total capped at 12 facts per user to prevent context bloat. Generates a `weekSummary` narrative TTL-gated to 7 days — surfaced in the Insights tab Weekly Reflection card.

**Technology:** GPT-4o · Azure Cosmos DB · Fact scoring + decay + dedup (60-char prefix check) · `asyncio.ensure_future()` non-blocking writes · JSON fence-strip guard

---

### 🌿 Agent 3 — Sage (Mindfulness Coach)
**Role:** Grounding exercises, breathing, and moment-to-moment calm

Receives the user's classified urgency level and tailors its response — high urgency triggers structured box breathing immediately; medium urgency invites reflection; low urgency opens with inquiry. Five grounding exercises are defined in the system prompt. Memory context is injected so Sage knows what has worked for this specific user before. Response streams word by word so the experience feels like a real conversation, not a form response.

**Technology:** GPT-4o · SK `ChatCompletionAgent.invoke_stream()` · Urgency-tiered response logic · Memory context injection · FastAPI `StreamingResponse`

---

### 📖 Agent 4 — River (Journal & Reflection)
**Role:** Journaling companion with automatic structured entry extraction

Responds as an empathetic journaling partner — asks one specific, contextual question based on the user's mood and history. After every response, River appends a `[SAVE_ENTRY]...[/SAVE_ENTRY]` block containing mood, sentiment, themes, and a first-person summary. The streaming pipeline intercepts this block in real time — it never appears in the user's chat bubble — parses it, and saves it as a Cosmos journal entry. Entries appear in the Journal tab with River's full response expandable and can be edited inline (edits trigger a background Memory re-extraction).

**Technology:** GPT-4o · SAVE_ENTRY buffer parser in async generator · Azure Cosmos DB · `asyncio.ensure_future()` non-blocking save · `PATCH /journal/{id}` with memory sync

---

### 🌱 Agent 5 — Grove (Habit Coach)
**Role:** WHY-first habit coaching with no-guilt streak recovery

Grove's philosophy: every habit has a reason, and the reason is what makes it stick. When a user creates a habit, Grove asks for the WHY — stored in memory and referenced on every subsequent interaction. Streak recovery is guilt-free by design: "Missing one day doesn't break a habit. Starting again does." Grove powers a Messenger-style floating chat head in the Habits tab — AI-generated daily nudges use live habit data and memory context. Streak logic uses a single authoritative `_calc_streak(logs, as_of)` helper called from GET, log, and unlog — ensuring GET, PATCH, and DELETE always agree on the streak value.

**Technology:** GPT-4o · `agentOverride` bypass · sessionStorage cache (60-min TTL + date key) · Azure Functions v2 · Single-source streak helper · WHY stored in Memory Agent

---

### ✨ Agent 6 — Lumen (Insights & Analytics)
**Role:** RAG-powered pattern surfacing from past journal entries

The only async specialist — before constructing its agent, it runs a hybrid vector + keyword search against Azure AI Search to retrieve the 5 most semantically relevant past journal entries. These are injected as `{journalContext}` alongside `{memoryContext}` into Lumen's system prompt, enabling responses grounded in actual past writing. Lumen populates the Insights tab — mood sparkline (pure SVG, no library), 14-day activity calendar grid, week-over-week trend delta, and the Weekly Reflection card.

**Technology:** GPT-4o · Azure AI Search hybrid search · `text-embedding-3-small-1` (1536-dim vectors) · Async factory pattern · Dual context injection (RAG + Memory)

---

## Agent Communication Protocol

Every agent-to-agent handoff in MindFlow follows a structured pipeline. The Orchestrator result, memory context, and streaming tokens all use defined formats — not free-form strings.

**Orchestrator output (JSON mode):**
```json
{
  "agent": "mindfulness",
  "confidence": 0.94,
  "mood": "anxious",
  "urgency": "high"
}
```

**Memory context block (injected into every specialist prompt):**
```
[MEMORY CONTEXT]
Known facts:
- responds well to box breathing when work anxiety spikes (importance: 0.85)
- phone-free mornings since April 22 — reports feeling calmer (importance: 0.90)

Recurring themes: work stress, deadline pressure, morning routine

This week: Mood trending upward (4→9). Meditation streak: 5 days.
[/MEMORY CONTEXT]
```

**River SAVE_ENTRY block (intercepted mid-stream, never shown to user):**
```
[SAVE_ENTRY]
mood: anxious
sentiment: negative
themes: work stress, deadline pressure
summary: I felt overwhelmed and noticed physical tension in my shoulders.
[/SAVE_ENTRY]
```

**Streaming agent token (first chunk — frontend extracts and strips):**
```
[AGENT:mindfulness]\n
```

Every Memory WRITE call and SAVE_ENTRY parse runs via `asyncio.ensure_future()` — non-blocking, the user receives the stream completion signal immediately.

---

## Architecture Principle

> **Memory is the product. Everything else is the interface.**

- **Context lives in Cosmos, always.** Specialists never carry state between requests — the Memory Agent fetches it fresh every time.
- **Hard routing belongs to the Orchestrator at temp=0.** Soft judgment belongs to GPT. Math (streaks, trend delta, mood averages) belongs to Python code.
- **Every GPT call degrades gracefully.** Memory read failure → empty string, chat continues. Orchestrator failure → falls back to "journal". Lumen RAG failure → responds from memory context alone.
- **Azure Functions own habit and mood data.** FastAPI proxies internally. The frontend knows one URL. CORS is configured in one place.
- **Streaming is end-to-end.** SK `invoke_stream()` → FastAPI `StreamingResponse` → `fetch + getReader()` in Next.js. No buffering, no polling.

---

## Azure Services

| Service | Resource | Role |
|---|---|---|
| Azure OpenAI GPT-4o | foundry-jmagno-2026 | All 6 agent reasoning and streaming calls |
| Azure OpenAI Embeddings | foundry-jmagno-2026 | `text-embedding-3-small-1` — 1536-dim journal vectors |
| Azure AI Search | search-jmagno-2026 | RAG knowledge base — 14 embedded journal entries, hybrid search |
| Azure Cosmos DB | cosmos-jmagno-2026 | 5 collections: users, user_memory, journal_entries, mood_logs, habits |
| Azure Functions v2 | mindflow-functions | Habit CRUD + mood logging + weekly pre-warm timer trigger |
| Azure App Service | mindflow-app | Next.js 14 frontend (Node 20 LTS) |

---

## Microsoft Agent Framework

**Present:** All six agents are implemented as `ChatCompletionAgent` objects from the Microsoft Semantic Kernel Python SDK (`semantic-kernel==1.41.3`). The Orchestrator uses direct `AzureChatCompletion` in JSON mode. All specialists stream via `agent.invoke_stream(ChatHistory)`. The kernel is instantiated fresh per request for async isolation across concurrent users. Azure Functions are registered using the Python v2 decorator model — all routes in a single `function_app.py`.

**Production roadmap:** SK Planner for adaptive agent routing based on conversation history; SK Memory Plugins to replace the hand-rolled Cosmos memory layer; multi-user session management with per-user kernel pools; Azure Container Apps for horizontal scaling of the streaming backend.

---

## Bonus Features

| Feature | Implementation |
|---|---|
| Activity Calendar | Month grid in Insights tab — journal, mood, and habit indicators per day. True UTC calendar-window query (`timestamp >= cutoff`) — not TOP-N rows. |
| Grove Chat Head | Messenger-style floating FAB in Habits tab. AI-generated daily nudge (GPT-4o, temp=0.85). sessionStorage cache with 60-min TTL + date key for instant tab switches. |
| Weekly Reflection Card | GPT-4o narrative of the user's week from 10 recent journal entries. TTL-gated to 7 days. Pre-warmed by Azure Functions timer trigger (Sunday 08:00 UTC). |
| Journal Inline Edit | ✏️ per-card edit mode. `PATCH /journal/{id}` triggers background Memory re-extraction via `ensure_future` — edits are reflected in the next agent response. |
| agentOverride | `ChatRequest.agentOverride` field bypasses Orchestrator LLM call — used by Grove chat head and any predetermined-intent surface to save ~300ms. |
| Idempotent Seed | UUID5-based `seed.py` — deterministic IDs, safe to re-run. `cleanup.py` purges demo user data. `bulk_index.py` purges stale AI Search documents before re-indexing. |
| Voice Journaling Stub | `IFileStore` abstract class in `backend/providers/file_store.py`. Adding voice = one new `AzureBlobFileStore` class. Zero agent changes required. |

---

## Verification

End-to-end QA pass confirmed all 13 routes returning 200 OK:

| Route | Result | Notes |
|---|---|---|
| `GET /health` | ✅ | |
| `GET /user` | ✅ | displayName: Jen |
| `GET /habits` | ✅ | 5 active habits |
| `POST /habits` | ✅ | |
| `PATCH /habits/{id}/log` | ✅ | streak incremented correctly |
| `DELETE /habits/{id}` | ✅ | soft-delete, active=False |
| `POST /mood` | ✅ | |
| `GET /journal` | ✅ | 14 entries, newest-first |
| `PATCH /journal/{id}` | ✅ | edit + background memory re-extract |
| `GET /insights` | ✅ | moodLogs (true 14-day window) + weekSummary |
| `GET /calendar` | ✅ | 14-day activity grid, UTC cutoff confirmed |
| `GET /grove/nudge` | ✅ | AI nudge generated |
| `POST /chat` | ✅ | Orchestrator → Sage → streaming confirmed |

Calendar window verified: all returned mood logs fall within `now_utc - timedelta(days=14)`. No stale documents in AI Search after `purge_index()` + re-index.

---

## Known Limitations

1. **Backend runs locally** — App Service deployment blocked by free subscription quota. Full Azure integration is live (Cosmos, AI Search, Azure Functions, OpenAI all connected and verified). Local compute only for the backend runtime. *Production fix: Azure App Service B1 (B1 minimum — F1 kills streaming connections).*

2. **BACKEND_URL placeholder** — Azure Functions weekly timer pre-warm requires the real App Service URL in portal App Settings. On-demand `weekSummary` generation via `GET /insights` works correctly without it. *Production fix: set `BACKEND_URL` in Azure Functions App Settings after App Service deploy.*

3. **Single demo user** — System is fully multi-user (all queries are `userId`-scoped) but seeded for one demo account (`demo-user-001`). *Production fix: authentication layer (Azure AD B2C or similar) + per-user onboarding flow.*

4. **Voice journaling stubbed** — `IFileStore` abstract class exists; `AzureBlobFileStore` implementation is the v2 roadmap item. *Production fix: implement `AzureBlobFileStore`, wire to `/journal/voice` endpoint — zero agent changes required.*

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- Azure resources provisioned (see `backend/.env.example`)

### Backend
```bash
# From repo root — always run uvicorn from repo root, not from backend/
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux

pip install -r backend/requirements.txt

cp backend/.env.example backend/.env
# Fill in Azure credentials — see backend/.env.example for all required keys

python -m uvicorn backend.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
# → http://localhost:3000
```

### Seed demo data
```bash
# From repo root, .venv active
python seed/seed.py          # Populates Cosmos DB (idempotent — UUID5, safe to re-run)
python seed/bulk_index.py    # Embeds + indexes journal entries to AI Search

# To reset completely:
python seed/cleanup.py       # Purges demo user data + stale AI Search documents
python seed/seed.py
python seed/bulk_index.py
```

### Azure Functions (local testing)
```bash
cd azure-functions
# Edit local.settings.json — fill in COSMOS_ENDPOINT, COSMOS_KEY, COSMOS_DB_NAME, DEMO_USER_ID
func start
```

---

## Project Structure

```
mindfulness-agent/
├── backend/
│   ├── agents/
│   │   ├── orchestrator.py         ← Agent 1: Intent classification
│   │   ├── memory_agent.py         ← Agent 2: READ + WRITE + weekSummary
│   │   ├── mindfulness_agent.py    ← Agent 3: Sage
│   │   ├── journal_agent.py        ← Agent 4: River
│   │   ├── habit_agent.py          ← Agent 5: Grove
│   │   └── insights_agent.py       ← Agent 6: Lumen (async RAG)
│   ├── api/
│   │   ├── chat.py                 ← POST /chat — full streaming pipeline
│   │   ├── calendar.py             ← GET /calendar — activity grid
│   │   ├── habits.py               ← Proxy → Azure Functions
│   │   ├── mood.py                 ← Proxy → Azure Functions
│   │   ├── journal.py              ← GET + PATCH /journal
│   │   ├── insights.py             ← GET /insights
│   │   ├── user.py                 ← GET /user
│   │   └── grove.py                ← GET /grove/nudge
│   ├── models/schemas.py           ← Pydantic models for all request/response types
│   ├── prompts/                    ← System prompt strings for all 6 agents
│   ├── providers/
│   │   ├── cosmos_repository.py    ← All Cosmos DB helpers
│   │   ├── search_provider.py      ← AI Search bulk_index + hybrid search
│   │   └── file_store.py           ← IFileStore stub (v2 voice journaling hook)
│   ├── kernel.py                   ← Semantic Kernel factory (fresh per request)
│   └── main.py                     ← FastAPI app, CORS, 8 routers registered
├── azure-functions/
│   ├── function_app.py             ← 6 HTTP routes + weekly timer trigger
│   ├── host.json
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx                ← 4-tab shell: Chat · Journal · Habits · Insights
│   │   ├── layout.tsx
│   │   └── globals.css             ← Clay neumorphic design system
│   └── components/
│       ├── ChatWindow.tsx          ← Streaming chat + agent badges + suggestion chips
│       ├── AgentBadge.tsx          ← Sage / River / Grove / Lumen badges
│       ├── MorningBanner.tsx       ← Time-aware greeting + one-tap mood check-in
│       ├── HabitTracker.tsx        ← Habit cards + streak + inline delete confirm
│       ├── HabitCoach.tsx          ← Grove Messenger-style floating chat head
│       ├── JournalView.tsx         ← Journal cards + River response + inline edit
│       ├── InsightsDashboard.tsx   ← Sparkline + calendar + weekly reflection
│       ├── CalendarView.tsx        ← Month activity grid (journal · mood · habits)
│       └── MoodSparkline.tsx       ← Pure SVG sparkline, no chart library
├── seed/
│   ├── seed.py                     ← Idempotent seed — UUID5, 14 entries, 5 habits
│   ├── bulk_index.py               ← Embed + upload journal entries to AI Search
│   └── cleanup.py                  ← Purge demo user data from Cosmos + AI Search
├── docs/
│   ├── agents.md                   ← Agent design and prompt philosophy
│   └── architecture.md             ← Full architecture with sequence diagrams
├── DEVLOG.md                       ← 17-phase dev log and learning reports
└── DEMO_SCRIPT.md                  ← 5-minute demo walkthrough with fallback lines
```

---

## AI Tools Disclosure

This project was built with assistance from the following AI tools, as required by Hackathon Rules Section 5 — Generative AI Tools:

- **Claude (Anthropic)** — architecture planning, code generation, debugging, documentation, and prompt engineering
- **Windsurf (Codeium)** — code execution, file editing, and live repo verification against actual codebase
- **GPT-4o via Azure AI Foundry** — all runtime agent responses (Sage, River, Grove, Lumen, Orchestrator, Memory Agent)

All code was reviewed, tested, and integrated by the participant. All development occurred during the official hackathon period (April 2 – May 3, 2026). No AI-generated assets contain sensitive, confidential, or proprietary information.

---

*Built for Code Without Barriers Hackathon 2026 — ASEAN Edition*
*Participant: Jennylyn Magno · Philippines · Solo submission*
