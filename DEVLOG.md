# MindFlow — Dev Log & Learning Journal

> This file is updated at the end of every build phase, before committing.
> It contains two sections per phase: a technical dev log and a plain-language learning report.

---

## Phase 1 — Scaffold + Repo Setup

### Dev Log

**What we set out to do**
Stand up the project skeleton: Next.js frontend, Python FastAPI backend, Azure Functions for habits and mood, and a seed script to populate the Cosmos DB demo account.

**What got built**
- `frontend/` — Next.js 14 app with full clay design system in `globals.css`, root layout with Google Fonts, placeholder page
- `frontend/.env.local.example` — single variable: `NEXT_PUBLIC_API_URL`
- `backend/` — FastAPI app scaffold, `requirements.txt`, `main.py` with CORS and `/health` endpoint, `.env.example` with all Azure variable keys
- `azure-functions/habits/function_app.py` — Python v2 decorator model, all 3 habit routes in one file: `GET /api/habits`, `POST /api/habits`, `PATCH /api/habits/{habit_id}/log` with streak recalculation in UTC
- `azure-functions/mood/function_app.py` — `POST /api/mood` mood log
- `seed/seed.py` — self-contained Python seed script with 14 journal entries (deliberate emotional arc), 5 habits with real log arrays and streaks, 14 mood logs, and 1 user memory document with 5 pre-populated facts
- `.gitignore` — extended to cover Python venv, `__pycache__`, `local.settings.json`
- `README.md` — submission-ready skeleton

**What broke and how it was fixed**

| Problem | What happened | Fix |
|---------|--------------|-----|
| `create-next-app` refused to run | The tool checks for an empty directory — the blueprint HTML was already in the folder | Skipped the scaffold tool entirely and created all files manually. Faster and gave full control. |
| `@microsoft/semantic-kernel` returns 404 | The npm package does not exist. Every variant tried: 404. GitHub install attempts also failed (monorepo has no installable root, gitpkg.vercel.app requires paid plan for large repos). | Switched the entire backend to **Python FastAPI**. The Python `semantic-kernel` package on PyPI is the stable, officially published Microsoft SDK. |
| Hand-rolled TypeScript SK implementation was committed | Before the Python decision, a fake `lib/semantic-kernel/` was created and committed | Deleted `lib/semantic-kernel/`, `seed/seed.ts`, `tsconfig.seed.json` in the next commit. |
| Blueprint HTML in repo misaligned with Python plan | The original blueprint referenced TypeScript implementation details | `git rm mindflow-blueprint.html` — committed and pushed. Blueprint still in git history but gone from working tree. |
| Stray `javascript/` folder | Created by a failed `npm install github:...` attempt | `Remove-Item -Recurse -Force javascript` before commit. |

**Commits**
- `chore: scaffold Next.js app and seed script`
- `chore: scaffold Python backend, reorganize repo, seed script`
- `chore: remove original blueprint HTML — superseded by Python architecture plan`

---

### Learning Report (Plain Language)

**What is a monorepo and why did we use one?**

A monorepo is one Git repository that holds multiple projects — in our case `frontend/` (the Next.js UI) and `backend/` (the Python API). The alternative would be two separate repos.

We chose one repo because:
- One `git push` publishes everything together
- The hackathon submission is one GitHub link — judges see the whole project at once
- Easier to keep environment variable names consistent across frontend and backend during a fast build

**What is a seed script and why does the content matter so much?**

The database starts empty. The seed script fills it with realistic demo data so the app has something meaningful to show immediately — without a real user journaling for two weeks.

The data quality is critical. If the journal entries are generic ("Today was a good day"), the Insights Agent will return something equally generic. The entries were written with a specific emotional arc: work stress peaking in the first week, a clear breakthrough moment at Day 4 (phone-free mornings), and measurable improvement through Day 0. This gives the AI something real to pattern-match against during the demo.

**Why is the design system in one CSS file?**

All colors, shadows, and component styles are defined as CSS variables in `globals.css`. Every component uses these variables rather than hardcoded values. If the sage green color needs to change, one line updates everything. The clay/neumorphic shadow effect only works correctly against the cream background (`#F5F2EC`) — the shadows are calculated relative to that specific tone.

**Why did we split the environment variables?**

- `backend/.env` — all Azure secrets. Only the Python backend reads these.
- `frontend/.env.local` — one variable: `NEXT_PUBLIC_API_URL`. Points to the FastAPI server.

In Next.js, any variable prefixed with `NEXT_PUBLIC_` gets embedded into the browser bundle — visible to anyone who opens the page source. By keeping all secrets in the backend, the frontend never touches them.

**Why does the frontend call FastAPI, and FastAPI calls Azure Functions?**

The frontend knows about one URL. Azure Functions are an internal detail. FastAPI receives habit and mood requests from the frontend, forwards them to Azure Functions internally, and returns the result. This means:
- CORS (cross-origin browser security) is configured in one place only — FastAPI
- The frontend code is simpler — one base URL, consistent interface
- Azure Functions appear in the Azure portal (satisfying the hackathon requirement) without the frontend needing to know they exist

**What is the Python Azure Functions v2 programming model?**

Azure Functions let you run small pieces of server code without managing a server. The v2 Python model uses the `@` decorator syntax — you attach a route definition directly to a function. All 3 habit routes live in one `function_app.py` file and appear in the Azure portal as separate functions but share the same deployed code.

**What does UTC mean for streak calculation?**

UTC (Coordinated Universal Time) is the same number everywhere on Earth at any moment. By calculating streaks in UTC, we avoid a bug where someone completing a habit at 11pm local time (which might already be the next day in UTC) breaks their streak incorrectly. The streak algorithm walks backward through sorted log dates, counting consecutive days.

---

---

## Phase 2 — Semantic Kernel + Schemas + Memory Agent

### Dev Log

**What we set out to do**
- Confirm the latest stable semantic-kernel version and pin it
- Create the Python package directory structure for the backend
- Build all Pydantic data models
- Create the Cosmos DB repository with the 3 methods needed by the Memory Agent
- Create the IFileStore stub (v2 voice journaling hook)
- Create the shared Semantic Kernel factory
- Build the Memory Agent — full READ pass and full WRITE pass

**What got built**
- `backend/requirements.txt` — `semantic-kernel==1.41.3` pinned (confirmed from `pip index versions semantic-kernel`)
- `backend/agents/`, `backend/api/`, `backend/models/`, `backend/prompts/`, `backend/providers/` — all created with `__init__.py` files
- `backend/models/schemas.py` — all 5 Cosmos collection models (`User`, `UserMemory`, `MemoryFact`, `JournalEntry`, `HabitLog`, `MoodLog`) and API types (`ChatRequest`, `OrchestratorResult`, `HabitCreate`, `MoodLogRequest`)
- `backend/providers/file_store.py` — `IFileStore` abstract class stub with `upload()`, `get_url()`, `delete()` methods. Header comment contains the exact demo voice journaling closing line.
- `backend/providers/cosmos_repository.py` — `get_user()`, `get_user_memory()`, `upsert_user_memory()` (Hour 2). `save_journal_entry()`, `get_recent_journal_entries()` stubbed for Hour 3. `get_mood_logs()` stubbed for Hour 7.
- `backend/kernel.py` — `build_kernel()` creates a Semantic Kernel instance with `AzureChatCompletion` and `AzureTextEmbedding` services. `get_embedding()` is an async wrapper for generating 1536-dimension float vectors.
- `backend/prompts/memory.py` — `MEMORY_CONTEXT_TEMPLATE` (the `{memoryContext}` block injected into every specialist agent's system prompt) and `MEMORY_WRITE_PROMPT` (instructs GPT to extract and score new facts in JSON format).
- `backend/agents/memory_agent.py` — full READ pass and full WRITE pass with fact scoring, deduplication, decay, and Cosmos upsert.

**What broke and how it was fixed**

Nothing broke in Phase 2. All files created cleanly. No live Azure connections were tested yet — those are verified when the seed script runs against a real Cosmos DB account.

One decision reconfirmed: `asyncio.ensure_future()` is used (not `asyncio.create_task()`) for non-blocking Memory WRITE calls inside the streaming generator. The Memory Agent's `write()` is a plain `async def` — callers wrap it with `ensure_future()`. This keeps the agent clean and independently testable.

**Commit**
- `feat: add Pydantic schemas, Cosmos provider, Memory Agent read/write`

---

### Learning Report (Plain Language)

**What is Semantic Kernel and what does it do here?**

Semantic Kernel is a Microsoft framework for building AI-powered applications. In Python, it gives you a `Kernel` object that holds your connection to an AI model (Azure OpenAI in our case), and `ChatCompletionAgent` objects that represent individual AI agents — each with their own personality defined by a system prompt.

Without Semantic Kernel, you'd write raw OpenAI API calls every time. With SK, you define each agent once and call `agent.invoke_stream(history)` — the framework handles the API call, streaming, and message formatting. Every specialist in MindFlow (Sage, River, Grove, Lumen) is a `ChatCompletionAgent`.

**Why are the Pydantic models important?**

Pydantic is Python's data validation library. When you define a `BaseModel`, you're specifying the exact shape and types of your data. FastAPI uses these models for two things:

1. **Request validation** — if the frontend sends a request missing a required field, FastAPI rejects it automatically with a clear error before your code even runs
2. **Response serialization** — FastAPI converts Python objects to JSON automatically using these models

This replaces the TypeScript interfaces from the original plan. The concept is the same (defining the shape of your data) but Pydantic checks data at runtime, while TypeScript interfaces only check at compile time.

**What is the Memory Agent actually doing?**

The Memory Agent is the reason MindFlow feels like it knows you.

**READ pass (before every response):** Think of it like a friend who keeps notes about you. Before responding, they look at their notes: "Alex gets anxious on Mondays. They've been working on breathing exercises. They had a breakthrough about phone-free mornings." The agent assembles this into a context paragraph and inserts it into every specialist agent's instructions — so Sage and River respond as if they already know your history.

**WRITE pass (after every response):** After your conversation ends, the agent re-reads the exchange and asks GPT: "Did we learn anything new about this person worth noting?" Facts scored above 0.6 get stored. Generic statements below 0.6 get discarded. Stale facts (not referenced in 14 days) have their importance score reduced slightly over time. The total is capped at 12 facts per user.

**Why does build_kernel() create a new kernel per request instead of once at startup?**

When multiple users send messages at the same time, they arrive concurrently. If there's one shared kernel object and two requests are both streaming through it simultaneously, they could interfere with each other's state. Creating a fresh kernel per request guarantees isolation. The cost is negligible — it's just a Python object construction with no network calls.

**What is "silent degradation"?**

Both the `read()` and `write()` functions in the Memory Agent catch all exceptions quietly:
- `read()` returns an empty string if it fails — the specialist agent gets no memory context, but the conversation continues
- `write()` logs the error and returns without storing anything

This is intentional. Memory is an enhancement — the app should never be broken by a Cosmos DB timeout. During a live demo, if Azure has a moment of latency, the chat still works.

**What is the 60-character deduplication check?**

Before storing a new fact, the Memory Agent checks if a similar fact already exists by comparing the first 60 characters of each fact's text. This catches obvious duplicates without adding the complexity of semantic similarity checks (which would require an embedding comparison). For a hackathon demo with one user and 12 stored facts, this is the correct level of sophistication.

**What does `asyncio.ensure_future()` do?**

`asyncio.ensure_future()` schedules an async function to run in the background without waiting for it to finish. When the streaming response ends, calling `asyncio.ensure_future(memory_agent.write(...))` tells Python: "start this task, but don't wait for it — let the response return to the user immediately." This is why the Memory write pass doesn't add latency to the user experience.

We use `ensure_future()` instead of `create_task()` because `ensure_future()` is more reliable inside async generator functions (which is what the streaming pipeline uses). `create_task()` can behave unpredictably in that context on Python 3.11.

---

*Next: Phase 3–4 — Orchestrator + Sage + River + Streaming Pipeline*
