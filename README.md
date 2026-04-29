# MindFlow

> AI-powered mindfulness, journaling, and habit-tracking assistant.  
> Built for the Microsoft Azure Hackathon · AI-Powered Mindfulness Track.

---

## Overview

MindFlow is a multi-agent AI system that helps users build healthier habits, reflect more deeply, and practice mindfulness — adapting to their emotional state, goals, and progress over time.

**6 Agents:**
- 🎯 **Orchestrator** — classifies every message, routes to the right specialist
- 🧠 **Memory Agent** — runs silently on every request, builds a picture of the user over time
- 🧘 **Sage** — Mindfulness Coach
- 📓 **River** — Journal & Reflection Agent
- ✅ **Grove** — Habit Coach
- 📊 **Lumen** — Insights & Analytics Agent

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Hosting | Azure App Service (Node.js 20 LTS) |
| LLM | Azure AI Foundry → GPT-4o |
| Embeddings | text-embedding-3-small |
| Database | Azure Cosmos DB (Core SQL API) |
| Vector Search | Azure AI Search |
| Agent Framework | Microsoft Semantic Kernel |
| Serverless API | Azure Functions (v4) |

---

## Setup

### Prerequisites
- Node.js 20 LTS
- Azure account with the following services provisioned:
  - Azure AI Foundry (GPT-4o + text-embedding-3-small deployed)
  - Azure Cosmos DB (Serverless, database: `mindflow`)
  - Azure AI Search (index: `journal-index`)
  - Azure App Service (Node.js 20 LTS)
  - Azure Functions app

### Environment Variables

Copy `.env.local.example` to `.env.local` and fill in your Azure credentials:

```bash
cp .env.local.example .env.local
```

### Install & Run

```bash
npm install
npm run dev
```

### Seed Demo Data

```bash
npm run seed
```

Populates the Cosmos DB with 14 days of demo journal entries, mood logs, habits, and memory facts for `DEMO_USER_ID=demo-user-001`.

---

## API Routes

### Next.js API Routes
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/chat` | Main agent pipeline (Orchestrator → Memory → Specialist, streaming) |
| GET | `/api/journal` | List recent journal entries |
| GET | `/api/insights` | Insights Agent with RAG context |

### Azure Functions
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/habits` | List habits for demo user |
| POST | `/api/habits` | Create a new habit |
| PATCH | `/api/habits/{id}/log` | Mark habit done for today |
| POST | `/api/mood` | Log a mood check-in |

---

## Agent Design

See [`docs/agents.md`](docs/agents.md) for full system prompt descriptions and trigger keywords.

---

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full 6-layer architecture diagram and adapter pattern documentation.

---

## Demo

[Demo video link — added after recording]

---

## Scalability Roadmap

- 🎙️ **Voice journaling** — `IFileStore` interface already in adapter layer; one new class needed
- 📱 **Native mobile** — React Native against the same API layer, zero backend changes
- 🔒 **Privacy mode** — Ollama local LLM via `ILLMProvider` swap
- 📅 **Calendar integration** — Microsoft Graph API for busy-week habit adjustments
- 📈 **Advanced analytics** — Mood heatmap, habit completion matrix, wellness reports

---

*Microsoft Azure Hackathon · AI Mindfulness Track · $100 1st Prize*
