# MindFlow

> AI-powered mindfulness, journaling, and habit-tracking assistant.  
> Built for the Microsoft Azure Hackathon · AI-Powered Mindfulness Track.

---

## Overview

MindFlow is a multi-agent AI system that helps users build healthier habits, reflect more deeply, and practice mindfulness — adapting to their emotional state, goals, and progress over time. Four specialized agents work together, coordinated by an Orchestrator and personalized by a silent Memory Agent that builds a picture of the user over time.

**6 Agents:**
- 🎯 **Orchestrator** — classifies every message, routes to the right specialist (JSON mode, <300ms)
- 🧠 **Memory Agent** — runs silently on every request, builds and injects personalized context
- 🧘 **Sage** — Mindfulness Coach (grounding exercises, urgency-aware tone)
- 📓 **River** — Journal & Reflection Agent (contextual prompts, structured SAVE_ENTRY parsing)
- ✅ **Grove** — Habit Coach (WHY-first, no-guilt, proactive DM nudge)
- 📊 **Lumen** — Insights & Analytics Agent (RAG over journal history via Azure AI Search)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Vanilla CSS |
| Backend | Python FastAPI (uvicorn), running on port 8000 |
| Agent Framework | Microsoft Semantic Kernel (Python) `semantic-kernel==1.41.3` |
| LLM | Azure AI Foundry → GPT-4o |
| Embeddings | Azure OpenAI `text-embedding-3-small-1` |
| Database | Azure Cosmos DB (Core SQL API) |
| Vector Search | Azure AI Search (index: `journal-index`) |
| Serverless | Azure Functions v2 Python (`mindflow-functions.azurewebsites.net`) |
| Frontend Hosting | Azure App Service (Node.js 20 LTS) or local `npm run dev` |

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 20 LTS
- Azure account with the following services provisioned:
  - Azure AI Foundry (GPT-4o + text-embedding-3-small-1 deployed)
  - Azure Cosmos DB (Serverless, database: `mindflow`)
  - Azure AI Search (index: `journal-index`)
  - Azure Functions app (`mindflow-functions`)

### Backend Setup

```powershell
# From the repo root
python -m venv .venv
.venv\Scripts\activate

pip install -r backend/requirements.txt

# Copy and fill in backend credentials
copy backend\.env.example backend\.env
# Edit backend/.env with your Azure keys
```

### Frontend Setup

```powershell
cd frontend
npm install

# Copy and set the backend URL
copy .env.local.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000  (default — no change needed for local dev)
```

### Seed Demo Data

```powershell
# From repo root (with .venv active)
python seed/seed.py         # Populates Cosmos DB with 14 days of demo data
python seed/bulk_index.py   # Embeds and indexes journal entries into Azure AI Search
```

Populates Cosmos DB with 14 days of demo journal entries, mood logs, 5 habits, and user memory facts for `DEMO_USER_ID=demo-user-001` (Jen).

### Run Locally

```powershell
# Terminal 1 — Backend (run from REPO ROOT, not backend/ subfolder)
python -m uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
# → http://localhost:3000
```

> ⚠️ **Always run uvicorn from the repo root.** The backend uses `backend.xxx` package paths — running from inside `backend/` causes `ModuleNotFoundError`.

---

## API Routes

### FastAPI Backend (port 8000)
| Method | Route | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/user?userId=...` | Returns display name and preferences from Cosmos |
| GET | `/habits?userId=...` | List habits (proxied to Azure Functions) |
| POST | `/habits` | Create a habit (proxied to Azure Functions) |
| PATCH | `/habits/{id}/log` | Mark habit done today (proxied to Azure Functions) |
| DELETE | `/habits/{id}` | Soft-delete a habit (proxied to Azure Functions) |
| POST | `/mood` | Log mood check-in (proxied to Azure Functions) |
| GET | `/journal?userId=...&limit=50` | List journal entries, newest first |
| PATCH | `/journal/{entry_id}` | Edit journal summary + background memory re-sync |
| GET | `/insights?userId=...&days=14` | Returns mood logs + AI-generated weekly reflection |
| GET | `/grove/nudge?userId=...` | AI-generated proactive habit nudge (non-streaming) |
| POST | `/chat` | Main agent pipeline (Orchestrator → Memory → Specialist, streaming) |

### Azure Functions (`mindflow-functions.azurewebsites.net`)
| Method | Route | Description |
|---|---|---|
| GET | `/api/habits` | List habits |
| POST | `/api/habits` | Create habit |
| PATCH | `/api/habits/{habit_id}/log` | Log habit done, recalculate streak |
| DELETE | `/api/habits/{habit_id}` | Soft-delete habit |
| POST | `/api/mood` | Save mood log to Cosmos |
| TIMER | Weekly (Sunday 08:00 UTC) | Pre-warms weekly reflection for all users |

---

## Agent Design

### Request Flow
```
User message
  → POST /chat
  → Orchestrator.classify()          [JSON mode, temp=0, ~200ms]
  → memory_agent.read()              [injects personalized context]
  → Specialist agent (Sage/River/Grove/Lumen)
  → StreamingResponse                [first chunk: [AGENT:xxx]\n]
  → memory_agent.write()             [background, non-blocking]
```

### Key Behaviours
- **Memory injection**: Every specialist receives `{memoryContext}` — top-5 facts, recurring themes, breakthroughs, weekly summary, preferred tone — assembled from Cosmos before each response.
- **SAVE_ENTRY parsing**: River appends a structured `[SAVE_ENTRY]...[/SAVE_ENTRY]` block to every response. The stream parser intercepts and saves this to Cosmos and AI Search without the user seeing it.
- **agentOverride**: The Grove chat head bypasses the Orchestrator LLM call (saves ~300ms) by setting `agentOverride: "habit"` on the request.
- **Weekly reflection**: `GET /insights` triggers `rebuild_week_summary()` which generates a 2–3 sentence AI narrative from the past week's journal entries (TTL-gated, rebuilds every 7 days).

---

## Frontend Tabs

| Tab | Component | Description |
|---|---|---|
| Chat | `ChatWindow` + `MorningBanner` | Streaming chat, mood check-in, agent badges |
| Journal | `JournalView` | Journal entry cards, expandable River responses, inline edit |
| Habits | `HabitTracker` + `HabitCoach` | Habit cards, streaks, Grove floating chat head |
| Insights | `InsightsDashboard` + `MoodSparkline` | Weekly reflection card, sparkline, mood stats |

---

## Architecture Notes

- **Endpoint normalization**: Azure AI Foundry endpoints include `/openai/v1` in the URL. All SDK clients strip this via `urlparse` before passing to OpenAI SDK (which appends the path internally).
- **Proxy pattern**: Frontend talks to FastAPI only. Azure Functions are an internal detail — FastAPI proxies `/habits` and `/mood` via `httpx`.
- **Streaming**: `StreamingResponse` with async generator. First chunk is `[AGENT:xxx]\n` for frontend badge routing. OpenTelemetry `ValueError` on generator cleanup is caught and suppressed (known SK + FastAPI interaction).

---

## Demo

See [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) for the 5-minute hackathon walkthrough with fallback lines for common failure scenarios.

---

## Scalability Roadmap

- 🎙️ **Voice journaling** — `IFileStore` interface already in adapter layer; one new class needed
- 📱 **Native mobile** — React Native against the same API layer, zero backend changes
- 🔒 **Privacy mode** — Ollama local LLM via `ILLMProvider` swap
- 📅 **Calendar integration** — Microsoft Graph API for busy-week habit adjustments
- 📈 **Advanced analytics** — Mood heatmap, habit completion matrix, wellness reports
- 🔐 **Auth** — Azure AD B2C; currently uses `DEMO_USER_ID` env var

---

*Microsoft Azure Hackathon · AI Mindfulness Track · $100 1st Prize*
