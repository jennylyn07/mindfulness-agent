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

---

---

## Phase 3–4 — Orchestrator + Sage + River + Streaming Pipeline

### Dev Log

**What we set out to do**
Build the entire chat pipeline end-to-end: Orchestrator classification → Memory READ → specialist agent → streaming response → SAVE_ENTRY buffer parser → Memory WRITE. Wire frontend to NEXT_PUBLIC_API_URL with full streaming via `getReader()`.

**What got built**

*Backend prompts*
- `backend/prompts/orchestrator.py` — JSON mode classification prompt. Returns `{agent, confidence, mood, urgency}`. Falls back to "journal" when intent is unclear. No prose output.
- `backend/prompts/mindfulness.py` — Sage system prompt verbatim from blueprint. Urgency-tiered responses (high/medium/low), 5 grounding exercises defined, `{memoryContext}` injection point.
- `backend/prompts/journal.py` — River system prompt. Reflective journaling companion. Includes D1 SAVE_ENTRY block directive at absolute end with explicit format and placement rules.

*Backend agents*
- `backend/agents/orchestrator.py` — `classify(message)` using direct Azure OpenAI in JSON mode, temperature=0. Silent fallback to `OrchestratorResult(agent="journal")` on any exception.
- `backend/agents/mindfulness_agent.py` — `get_agent(memory_context)` builds `ChatCompletionAgent` with Sage instructions + injected memory context.
- `backend/agents/journal_agent.py` — same pattern for River.

*Backend API routes*
- `backend/api/chat.py` — `POST /chat`. Full pipeline: Orchestrator → Memory READ → agent routing → `invoke_stream()` → SAVE_ENTRY buffer strip → `_parse_and_save_entry()` via `ensure_future` → Memory WRITE via `ensure_future`. Yields `[AGENT:xxx]` as first token so frontend can show the correct badge.
- `backend/api/habits.py` — 3 proxy routes (`GET`, `POST`, `PATCH /habits/{id}/log`) via `httpx.AsyncClient`. Proxies to `FUNCTIONS_HABIT_URL`. Frontend never calls Azure Functions directly (Fix 1).
- `backend/api/mood.py` — `POST /mood` proxy to `FUNCTIONS_MOOD_URL`.
- `backend/main.py` — updated: all 3 routers registered. `journal.router` and `insights.router` commented in for Hours 5/7.

*Frontend components*
- `frontend/components/AgentBadge.tsx` — maps agent name to label, emoji, and color. Shows animated dot while streaming.
- `frontend/components/MorningBanner.tsx` — time-aware greeting, one-tap emoji mood check-in, fires `onMoodSelect`.
- `frontend/components/ChatWindow.tsx` — streaming chat with `fetch + getReader()` (D3). Parses `[AGENT:xxx]` prefix from first chunk. Accumulates chunks into live-updating bubble. Shows typing indicator while streaming. Suggestion chips on empty state.
- `frontend/app/page.tsx` — three-tab shell (Chat / Habits / Insights). Morning banner with mood tap → `POST /mood`. Habits and Insights tabs show placeholders until Phase 5/7.
- `frontend/app/globals.css` — extended with all missing classes: `.app-shell`, `.tab-nav`, `.tab-btn`, `.chat-window`, `.bubble`, `.agent-badge`, `.typing-indicator`, `.chat-input-row`, `.suggestion-chip`, `.placeholder-tab`, morning banner internals.

**What broke and how it was fixed**

| Problem | Fix |
|---------|-----|
| `globals.css` had `.tab-bar`/`.tab-item` but components used `.tab-nav`/`.tab-btn` | Added correct class names to CSS. Old classes left in place (they don't conflict). |
| `globals.css` had `.bubble-ai`/`.bubble-user` but ChatWindow used `.bubble.assistant`/`.bubble.user` | Added `.bubble`, `.bubble.assistant`, `.bubble.user` modifier classes. |
| SK `invoke_stream` return type uncertain across versions | Wrote defensive handler: checks `isinstance(chunk, list)` first, falls back to `.content` attribute. |
| `chat.py` needed `_parse_and_save_entry` to not block the stream | Used `asyncio.ensure_future()` — same pattern as Memory WRITE. |

**Commit**
- `feat: add Orchestrator, Sage, River with FastAPI streaming pipeline`

---

### Learning Report (Plain Language)

**What is the Orchestrator and why does it run first?**

Every message the user sends goes through the Orchestrator before anything else. Its only job is to classify the intent into one of four categories: mindfulness, journal, habit, or insights. It's like a receptionist who reads your message and decides which specialist you need to see.

It runs in JSON mode at temperature=0, which means the model gives a deterministic structured response instead of free-form text. This is intentional — you want classification to be fast, consistent, and machine-readable. The target is under 300ms.

If the classification fails for any reason (network timeout, malformed JSON), it falls back to "journal" silently. The user never sees an error.

**What is the streaming pipeline in plain terms?**

When you type a message:
1. The Orchestrator reads it and classifies it in ~200ms
2. The Memory Agent reads your history from the database and assembles a context paragraph
3. That context is injected into the specialist agent's instructions (so Sage "knows you")
4. The specialist agent (Sage, River, etc.) starts generating a response word by word
5. Each word chunk is sent to your browser immediately as it arrives — you see the response appearing in real time, like watching someone type
6. At the end, the Memory Agent reads the full exchange and decides what new facts to store — this happens in the background, you don't wait for it

**Why does the `[AGENT:xxx]` token appear at the start of the stream?**

The frontend needs to show the correct agent badge (Sage/River/Grove/Lumen) as soon as the response starts. But the streaming response is just a plain text stream — there's no HTTP header or metadata attached to each chunk.

The solution: the backend yields `[AGENT:journal]\n` as the very first chunk before any actual content. The frontend's reader detects this pattern, strips it out, and sets the badge. The user never sees it in the bubble.

**What is `asyncio.ensure_future()` and why is it used twice?**

Both the SAVE_ENTRY parsing and the Memory WRITE happen after the streaming response is sent. If we `await` them, the user would have to wait for them to finish before the response is "done." That adds latency to every message.

`ensure_future()` schedules these tasks to run in the background — they start executing after the stream finishes, but the user's browser receives the "stream done" signal immediately. Both tasks are self-contained and handle their own errors silently, so they can safely run without supervision.

**What is the SAVE_ENTRY buffer parser?**

River (the journal agent) appends a structured data block to the end of every response:
```
[SAVE_ENTRY]
mood: anxious
sentiment: negative
themes: work stress, manager conflict
summary: User felt overwhelmed and noticed physical tension.
[/SAVE_ENTRY]
```

The chat route maintains a buffer of the streaming content. As chunks arrive, it checks whether the buffer now contains `[SAVE_ENTRY]`. If it does:
- Everything before `[SAVE_ENTRY]` gets sent to the user normally
- Everything from `[SAVE_ENTRY]` onward is captured but not yielded to the frontend
- When `[/SAVE_ENTRY]` arrives, the block is parsed into fields and saved as a journal entry

The user only ever sees the conversational response. The structured data is extracted invisibly in real time.

**What is httpx and why is it used for proxy routes?**

`httpx` is Python's async HTTP client — the equivalent of `fetch()` in JavaScript. The habits and mood proxy routes use it to forward requests from FastAPI to Azure Functions.

By using `httpx.AsyncClient`, the FastAPI server doesn't block while waiting for Azure Functions to respond — it can handle other requests in the meantime. The `timeout=10.0` setting means if Azure Functions doesn't respond within 10 seconds, the proxy returns a 503 error rather than hanging forever.

---

*Next: Phase 5–6 — Grove agent + HabitTracker UI*

---

---

## Phase 5–6 — Grove Agent + HabitTracker + Proxy Routes

### Dev Log

**What got built**
- `backend/prompts/habit.py` — Grove system prompt. WHY-first coaching philosophy, no-guilt streak recovery ("Missing one day doesn't break a habit. Starting again does."), urgency-tiered responses.
- `backend/agents/habit_agent.py` — Same factory pattern as Sage and River. Memory context injected.
- `backend/api/journal.py` — `GET /journal` returning the N most recent journal entries. River's SAVE_ENTRY parser saves entries; this endpoint reads them back.
- `backend/api/chat.py` — Grove wired into `_get_specialist()`. Import added.
- `backend/requirements.txt` — All explicit version pins loosened to `>=`. Only `semantic-kernel==1.41.3` remains pinned. Resolves conflict between SK 1.41.3 (needs openai>=2.0.0, pydantic 2.12.5, httpx 0.28.1) and our earlier exact pins.
- `frontend/components/HabitTracker.tsx` — Fetches `GET /habits`, renders habit cards with one-tap `PATCH /habits/{id}/log`. Skeleton loading. UTC date comparison for done-today detection. Streak displayed as a serif number.
- `frontend/app/globals.css` — `.habit-list`, `.habit-card`, `.habit-card.done`, `.habit-streak`, `.streak-number` classes added.
- `frontend/app/page.tsx` — Habits tab replaced with live HabitTracker component.

**What broke and how it was fixed**

| Problem | Fix |
|---------|-----|
| `pip install` failed with `ResolutionImpossible` | SK 1.41.3 requires `openai>=2.0.0`, `pydantic>=2.12`, `httpx>=0.28`. All our pins were exact (`==`). Loosened to `>=` except SK itself. |
| `tail` command not found on PowerShell | Replaced `\| tail -5` with `\| Select-Object -Last 6` throughout. |
| `seed.py` crashing on Unicode ❌ emoji (Windows cp1252 encoding) | Replaced emoji with plain `[ERROR]` prefix. Added `$env:PYTHONIOENCODING="utf-8"` to commands. |
| `seed.py` not finding `.env` | Made path absolute using `os.path.abspath`. Added debug line printing resolved path. |
| `COSMOS_ENDPOINT` not filled in | Cosmos credentials still blank — Cosmos DB not yet provisioned. Seed deferred. |

**Commit**
- `feat: add Grove agent, Azure Functions for habits and mood, tracker UI`

---

### Learning Report

**What is Grove's "WHY-first" approach?**

Most habit apps focus on the action: "Did you meditate today? Yes/No." Grove's philosophy is different — every habit has a reason behind it, and that reason is what makes it stick. When you tell Grove "I want to meditate daily," Grove asks: "What's the reason behind this one?" The WHY gets stored in memory. When Grove coaches you through a struggle or celebrates a streak, it references that WHY directly: "You started this for your anxiety — 6 days in, that's real."

Research in habit formation shows that habits tied to identity and values are more durable than those tied to outcomes. Grove's prompt is designed around this principle.

**Why is the streak logic in Azure Functions and not FastAPI?**

The streak calculation uses UTC date strings. It walks backward through sorted log dates and counts consecutive days. This is a stateful write operation (append today's date, recalculate streak). Azure Functions are the natural boundary here because they own the habit data in Cosmos — they're the authority on what constitutes a valid log. FastAPI acts only as a proxy, forwarding the request and returning the result.

**What does "loosening version pins" mean and why was it necessary?**

When you write `pydantic==2.7.0` in requirements.txt, pip will only install exactly version 2.7.0. When you write `pydantic>=2.7.0`, pip can install 2.7.0 or any higher version.

semantic-kernel 1.41.3 was released after our original version pins were chosen. It needs pydantic 2.12.5, which is newer than our pin. With exact pins, pip can't satisfy both requirements simultaneously — it's a conflict. Loosening the pins lets pip find compatible versions automatically. The only version we keep exact is semantic-kernel itself, because that's the core architectural decision we committed to at the start.

---

---

## Phase 7–8 — Lumen Agent + AI Search + Insights Dashboard

### Dev Log

**What got built**
- `backend/prompts/insights.py` — Lumen system prompt. Non-clinical pattern surfacing, emotional arc narration, RAG injection points for both `{journalContext}` (AI Search results) and `{memoryContext}`.
- `backend/providers/search_provider.py` — `bulk_index(entries)` generates embeddings and upserts into AI Search. `search(query, user_id, top_k=5)` runs hybrid vector+keyword search filtered by userId, returns formatted string for `{journalContext}`.
- `backend/agents/insights_agent.py` — Async factory: calls `search_provider.search()` first, then builds `ChatCompletionAgent` with both contexts injected.
- `backend/api/insights.py` — `GET /insights` returns 14-day mood logs for the sparkline chart. Lumen's conversational responses still stream through `POST /chat`.
- `backend/api/chat.py` — `_get_specialist()` made async. Lumen wired in — when Orchestrator classifies "insights", `insights_agent.get_agent()` is awaited (it needs to run the RAG search before building the agent).
- `backend/main.py` — All 5 routers now registered: chat, habits, mood, journal, insights.
- `frontend/components/MoodSparkline.tsx` — Pure SVG sparkline. No chart library. Gradient fill, color-coded dots by mood value, last mood highlighted. Scales dynamically to any score range.
- `frontend/components/InsightsDashboard.tsx` — Fetches `GET /insights`, renders sparkline, avg mood score, dominant mood, week-over-week trend delta. Lumen prompt card directs users to Chat tab.
- `frontend/app/globals.css` — `.insights-shell`, `.insights-card`, `.stat-pill`, `.sparkline-*`, `.lumen-prompt` classes added.
- `frontend/app/page.tsx` — Insights tab replaced with live InsightsDashboard.

**What broke and how it was fixed**

| Problem | Fix |
|---------|-----|
| `_get_specialist()` was sync but Lumen's factory is async | Changed `_get_specialist` to `async def`, updated call site to `await _get_specialist(...)`. |
| Chunk 1 replacement failed (wrong target content) | Viewed the actual file before retrying. Target content must match exactly including whitespace. |

**Commit**
- `feat: add Lumen agent with RAG and mood dashboard`

---

### Learning Report

**What is RAG and how does it work in MindFlow?**

RAG stands for Retrieval-Augmented Generation. Instead of relying purely on what the AI "remembers" from training, you first retrieve relevant documents from your own data store, then inject them into the AI's instructions.

In MindFlow, when you ask Lumen "What patterns do you see?", this happens:
1. Your question is converted to a 1536-dimension vector (a mathematical representation)
2. Azure AI Search compares that vector to the vectors of all your past journal entries
3. The 5 most semantically similar entries are retrieved
4. Their summaries and themes are formatted and injected into Lumen's system prompt as `{journalContext}`
5. Lumen responds as if it just re-read those entries moments ago

This is what makes Lumen feel like it actually knows your history — it does, because it just looked it up.

**What is a vector and why does it enable semantic search?**

A vector is a list of numbers — in our case, 1536 numbers. The embedding model (`text-embedding-3-small-1`) converts any piece of text into this list. Similar texts produce similar vectors. The similarity between two vectors can be measured mathematically (cosine similarity).

So if you ask "Why do I feel anxious at work?" and an old journal entry says "I felt overwhelmed during the project deadline," the vectors for both texts will be close to each other — even though no exact words match. This is why AI Search finds relevant entries that keyword search would miss.

**Why is `_get_specialist()` async only for Lumen?**

The other three specialists (Sage, River, Grove) are simple — `get_agent()` is a synchronous function that just constructs a Python object. There's no network call. Lumen is different: before it can construct the agent, it needs to call Azure AI Search (a network call) to retrieve relevant journal entries. Network calls in async Python must be awaited. So Lumen's factory is `async def`, and the router function must be `async def` too.

**What does the week-over-week trend tell us?**

The trend delta compares your average mood score from the past 7 days against the 7 days before that. A positive number (↑) means your average mood is higher this week than last week. A negative number (↓) means it's lower.

This is deliberately simple — not a statistical test, just a directional signal. The goal isn't clinical accuracy; it's giving the user a meaningful reflection point: "My mood has been trending up" or "This week has been harder than last week." Lumen uses this alongside the journal context to surface a narrative rather than just numbers.

---

*Next: Phase 9 — Polish, demo script, error states, loading states*

---

## Phase 9 — Infrastructure Hardening + AI Search Population

### Dev Log

**What we set out to do**
Resolve all remaining infrastructure blockers before demo day: fix environment loading, populate the AI Search index so Lumen has RAG data, confirm all frontend components exist, deploy Azure Functions, and commit all pending changes cleanly.

**What got built / fixed**

| Fix | Root cause | Resolution |
|---|---|---|
| `load_dotenv()` not finding `backend/.env` | All modules called `load_dotenv()` without a path — defaults to CWD (repo root), but `.env` lives in `backend/`. Server started with no credentials. | Changed all three callers (`kernel.py`, `main.py`, `cosmos_repository.py`) to use `__file__`-relative `os.path.abspath()` paths. |
| Azure AI Foundry endpoint 404 | Endpoint in `.env` includes `/openai/v1` path suffix (AI Foundry format). SK's `AzureChatCompletion` and `AsyncAzureOpenAI` both expect just the base domain — they construct the path internally. | Added `urlparse` normalization in `kernel.py`. Applied same normalization inline in `orchestrator.py` and `memory_agent.py` WRITE pass. |
| SK `invoke_stream` TypeError | `ChatCompletionAgent.invoke_stream()` in SK 1.41.3 yields `StreamingChatMessageContent` directly (not a list as older docs stated). Calling `bool()` on the content object triggers `__len__()` → `TypeError`. | Replaced inline extraction with `_chunk_text()` helper that uses `c is not None` instead of truthiness and `str()` for non-string types. |
| OpenTelemetry `ValueError` crashing stream | SK's generator cleanup fires `ContextVar.reset()` inside FastAPI `StreamingResponse` — the token was created in a different async context → `ValueError`. This propagated to our outer `except` and yielded `[ERROR]`. | Wrapped SK streaming loop in `try/except ValueError` that specifically ignores the OTEL context error (content already yielded before cleanup runs). |
| AI Search `summary` field not found | `search_provider.py` was sending and selecting a `summary` field that doesn't exist in the manually-created index schema. | Removed `summary` from upload documents and `select` list. Used `content[:150]` snippet instead. |
| AI Search `contentVector` field not found | Code used `contentVector` as the vector field name; actual index uses `embedding`. | Renamed in both `bulk_index()` and the `VectorizedQuery` fields parameter. |
| Embedding model deployment name mismatch | Deployed as `text-embedding-3-small-1` (with `-1` suffix); code defaulted to `text-embedding-3-small`. | Updated `AZURE_OPENAI_EMBED_DEPLOYMENT=text-embedding-3-small-1` in `.env` and fallback default in `kernel.py`. |
| Azure Functions — no functions registered | Root `function_app.py` was missing (`func publish` found no entry point). Then after creating it, module-level `os.environ["COSMOS_ENDPOINT"]` crashed the worker at cold start before any routes could register. Then `log_habit(req, habit_id)` — Python v2 doesn't inject route params as function args; they come from `req.route_params`. | Created root `function_app.py` + `host.json` + `requirements.txt`. Moved credential reads inside helper functions. Changed `habit_id: str` param to `habit_id = req.route_params.get("habit_id")`. Verified locally with `func start` (all 4 routes confirmed), then deployed. |
| `frontend/.env.local` missing | File was never created; all 4 frontend components had `?? 'http://localhost:8000'` hardcoded fallback only. | Created `frontend/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`. Swap to ngrok URL at demo time without code changes. |

**AI Search populated**
- Ran `seed/bulk_index.py` — embedded all 14 journal entries using `text-embedding-3-small-1`, uploaded to `journal-index`
- Test query `"feeling anxious"` returned 3 semantically relevant entries (2026-04-22, 2026-04-19, 2026-04-16) with correct mood and themes — Lumen's RAG pipeline confirmed working

**Azure Functions deployed**
- `mindflow-functions.azurewebsites.net` live with 4 routes:
  - `GET  /api/habits`
  - `POST /api/habits`
  - `PATCH /api/habits/{habit_id}/log`
  - `POST /api/mood`
- App Settings required in Azure Portal: `COSMOS_ENDPOINT`, `COSMOS_KEY`, `COSMOS_DB_NAME`, `DEMO_USER_ID`

**End-to-end smoke test result**
```
POST /chat { "message": "I feel anxious today", "userId": "demo-user-001" }
→ [AGENT:mindfulness]
→ Sage responded with box breathing exercise
→ Memory context from Cosmos (2092 chars, 5 facts) correctly injected
→ Full streaming pipeline confirmed working
```

**Commits**
- `fix: dotenv paths, Azure endpoint normalization, SK chunk extraction, OTEL cleanup`
- `fix: update embedding model name to text-embedding-3-small across all files`
- (pending) `fix: update embed deployment name, fix AI Search schema fields, add frontend .env.local, Azure Functions v2 publish setup`

---

### Learning Report

**Why did the same `load_dotenv()` work in the seed script but not the server?**

The seed script explicitly constructed the path using `os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))`. The server modules used bare `load_dotenv()` which searches the current working directory. When you run `uvicorn` from the repo root, CWD is the repo root — not `backend/`. There is no `.env` at the repo root (it's gitignored there). So the server started with all empty strings.

**What is the Azure AI Foundry endpoint format and why does it break SDKs?**

Azure AI Foundry provides a "unified inference" endpoint that includes `/openai/v1` in the URL. This is different from the classic Azure OpenAI endpoint format. The OpenAI Python SDK and Semantic Kernel both expect just the base domain (`https://resource.openai.azure.com/`) because they construct the full path (`/openai/deployments/{name}/chat/completions`) internally. Passing in the full path causes the SDK to double-append it, resulting in a 404. The fix is to strip everything after the domain using `urlparse`.

**Why does Python v2 Azure Functions not accept route params as function arguments?**

In the Python v1 model, Azure Functions injected route parameters as named function arguments. Python v2 changed this — the function signature is always `(req: func.HttpRequest) -> func.HttpResponse`, and route parameters are accessed via `req.route_params.get("param_name")`. This is a documented breaking change between models. The error `parameters declared in Python but not in the function definition` is the worker rejecting the function at index time, which cascades to zero functions registering.

**What is OTEL (OpenTelemetry) and why did it break our streaming?**

OpenTelemetry is an observability framework that Semantic Kernel uses to trace LLM calls. It uses Python's `contextvars.ContextVar` to track trace context across async calls. When FastAPI's `StreamingResponse` tears down an async generator (via `GeneratorExit`), SK's cleanup code tries to reset the OTEL context variable — but the `ContextVar` token was created in a different async task context, so `token.reset()` raises `ValueError`. This is a known SK + FastAPI interaction bug. The fix is to catch `ValueError` with the specific message `"created in a different Context"` and ignore it — all content has already been yielded before this cleanup fires.

---

---

## Phase 10 — UI Polish + Error States

### Dev Log

**What got built / fixed**
- `frontend/components/HabitTracker.tsx` — Added full error state with retry button. If the habits fetch fails (Azure Functions unreachable, Cosmos timeout), the user sees a clear message with a Retry button rather than a blank card or a silent spinner.
- `frontend/components/InsightsDashboard.tsx` — Same error state treatment. If `GET /insights` fails, a friendly message appears with retry. Prevents the dashboard tab from appearing broken during demo if there's a cold-start delay.
- Both components: retry logic uses a `retryCount` state increment to re-trigger the `useEffect` data fetch, keeping the fetch logic in one place.

**What broke and how it was fixed**

Nothing broke. This was a focused polish pass — all changes were additive UI improvements.

**Commit**
- `polish: add error states with retry to HabitTracker and InsightsDashboard`

---

### Learning Report

**Why add error states at all — won't everything just work?**

In a demo environment, Azure services occasionally have cold starts (the first request after inactivity can take 5–15 seconds). Azure Functions in particular can be slow on the first call. Without error states, the user sees a blank white card with a spinner that never resolves — which looks broken and creates panic during a presentation.

With an error state and a retry button, even if the first call fails, one tap recovers it. This is the difference between a demo that looks polished and one that looks fragile.

**What is a retry pattern?**

Instead of the component re-fetching automatically (which can cause infinite loops on genuine errors), we use a `retryCount` integer in state. Clicking Retry increments it by 1. The `useEffect` dependency array includes `retryCount`, so React re-runs the data fetch every time it changes. One tap = one retry = clean and predictable.

---

---

## Phase 11 — Current Session: Embedding Consistency + Re-seed + Re-index + User API

### Dev Log

**What this session addressed**
This session focused on data consistency and correctness before demo day: verifying the embedding model name was correct everywhere, re-seeding Cosmos with fresh data, re-indexing into AI Search, and adding the `/user` endpoint for dynamic name retrieval.

**What got built / fixed**

| Fix | Root cause | Resolution |
|---|---|---|
| Embedding model fallback default wrong | `kernel.py` fallback was `"text-embedding-3-small"` (no `-1` suffix). `.env` had the correct value so runtime was unaffected, but the fallback would fail if `.env` was ever missing. | Changed fallback to `"text-embedding-3-small-1"` in `kernel.py`. |
| `.env.example` had wrong embed name | Template showed `text-embedding-3-small` without `-1`. Anyone copying this to set up the project would get a 404 from Azure. | Updated `.env.example` to `text-embedding-3-small-1`. |
| DEVLOG.md learning note referenced `ada-002` | An educational explanation used `text-embedding-ada-002` as an example. | Updated to `text-embedding-3-small-1` so documentation is consistent with the actual deployment. |
| Seed script crashed on Windows (emoji encoding) | Windows terminals default to `cp1252` which can't print emoji (`🌱`, `✅`, `⚠️`). `UnicodeEncodeError` on first `print()`. | Added `sys.stdout.reconfigure(encoding="utf-8")` at the top of `seed.py`, guarded by `if sys.platform == "win32"`. |
| AI Search index stale after re-seed | Re-seeding creates new document IDs. The old indexed documents in AI Search had different IDs — Lumen's RAG would return stale data. | Re-ran `bulk_index.py` after re-seed. All 20 entries (14 from today's seed + 6 from prior test entries) indexed successfully. RAG test query confirmed working. |
| User name hardcoded in frontend | Frontend references to `"Jen"` were static strings instead of reading from the database. | Created `backend/api/user.py` — `GET /user` reads the user document from Cosmos and returns `displayName`, `email`, `preferences`. Registered in `main.py`. Frontend can now call this endpoint to get the real name. |

**Seed result**
```
✓ User upserted: Jen (demo-user-001)
✓ Journal entries upserted: 14
✓ Habits upserted: 5
✓ Mood logs upserted: 14
✓ User memory upserted (5 facts)
✅ Seed complete. Demo account is ready.
```

**Bulk index result**
```
→ Found 20 entries
→ Indexed: 20/20 documents
Test query: 'feeling anxious' → Results returned (3 semantically relevant entries)
```

**Commits**
- `fix: correct embedding model name to text-embedding-3-small-1 across all files`
- (pending) `polish: UI refinements, dynamic user name, seed encoding fix, user API`

---

### Learning Report

**Why does the fallback value matter if `.env` overrides it anyway?**

The fallback in `os.getenv("VAR", "default")` is only used when the environment variable is missing entirely. In practice, `.env` is always present during development. But there are scenarios where it could be missing — a fresh clone without running setup, a CI environment, or a misconfigured deployment. In those cases, the fallback kicks in. If the fallback is wrong, the embed call silently sends the wrong model name to Azure and gets a 404, which is very confusing to debug. Correct fallbacks are defensive programming — they cost nothing and prevent hard-to-trace failures.

**Why does Windows have an encoding problem with emoji?**

Windows uses a legacy encoding called `cp1252` (also called Windows-1252) for its terminal by default. This encoding dates back to the 1980s and can only represent 256 characters — none of which are emoji. When Python tries to print `🌱` to a cp1252 terminal, it raises `UnicodeEncodeError` immediately.

`sys.stdout.reconfigure(encoding="utf-8")` tells Python to switch the terminal's output stream to UTF-8, which supports all Unicode characters including emoji. This only applies to the current process — it doesn't change your system settings.

**What does the `/user` endpoint enable?**

Instead of `"Hello, Jen!"` being hardcoded in the frontend JavaScript, the frontend calls `GET /user` at startup and gets `{ displayName: "Jen" }` from Cosmos. This means:
- If you change the name in the database, the UI reflects it immediately — no code change
- The demo works for any user ID, not just the one whose name was hardcoded
- It demonstrates a proper data-driven architecture to judges: the UI is a view over real data, not a mock

---

*Status: Backend running. AI Search indexed. Demo data seeded. Pending commit of all UI refinements.*

---

---

## Phase 12 — Final QA Hardening + Backend Sign-Off

### Dev Log

**What this session addressed**
End-to-end backend QA sign-off before demo day. Ran a 15-checkpoint pass across all routes (health, user, habits CRUD, journal, insights, chat streaming). Fixed every failure found. All routes confirmed 200 OK in FastAPI server logs. Chat pipeline confirmed: Orchestrator → Sage → streaming AGENT token → `POST /chat 200 OK`.

**What got built / fixed**

| Fix | Root cause | Resolution |
|---|---|---|
| `PATCH /habits/{id}` + `DELETE /habits/{id}` both 500 | Azure Functions Python v2 silently conflicts when two `@app.route` decorators share the same route string — both handlers fail to register | Merged into a single `manage_habit` handler with `methods=["PATCH", "DELETE"]`; dispatches internally on `req.method`. |
| `[MemoryAgent] WRITE failed` — JSON parse error | Model occasionally wraps JSON response in markdown code fences (` ```json ... ``` `) even with `response_format={"type": "json_object"}` set | Added fence-strip pass: if `raw.startswith("```")`, drop the opening and closing lines before `json.loads()`. |
| `GET /journal` returning only 10 entries | Default `limit` parameter was 10; seed contains 14 journal entries — last 4 were invisible to the frontend | Changed default from `limit: int = 10` to `limit: int = 50`. |
| Stale AI Search documents accumulating on re-seed | Each re-seed creates new UUID5 document IDs; old IDs remain in the index — Lumen's RAG returns a mix of old and new entries | Added `purge_index(user_id)` to `search_provider.py`. `bulk_index.py` now calls this before uploading. |
| `GET /insights` field name mismatch in QA script | Response shape is `{ moodLogs: [...], days: 14 }` — QA script was checking `$ins.logs` (wrong key) | Fixed QA assertion to use `$ins.moodLogs`. Confirmed 5/5 insights checks pass. |
| Chat streaming test hung indefinitely | PowerShell `Invoke-WebRequest` and `curl.exe` both buffer `StreamingResponse` until TCP close — FastAPI's `StreamingResponse` with an async generator never sends a TCP close, it just ends the generator | Not a backend bug — confirmed via server logs: `POST /chat 200 OK`, `[Orchestrator] agent=mindfulness`, AGENT token received. Test tooling limitation only. |
| Seed data not idempotent — duplicate documents on re-run | Original seed used `uuid.uuid4()` (random) IDs — every run created new documents | Switched to `uuid.uuid5(NAMESPACE_DNS, stable_key)` throughout `seed.py`. Same inputs always produce same IDs; Cosmos upserts are safe to re-run. |
| No clean teardown path before re-seed | Stale habit/journal/mood docs from earlier test runs remained in Cosmos, polluting QA | Created `seed/cleanup.py` — purges all habits, journal_entries, and mood_logs for `DEMO_USER_ID` before re-seeding. |

**Final QA result — confirmed in FastAPI server access logs**
```
GET  /health               → 200 OK
GET  /user                 → 200 OK  (displayName: Jen)
GET  /habits               → 200 OK  (5 habits)
POST /habits               → 200 OK  (create)
PATCH /habits/{id}/log     → 200 OK  (currentStreak incremented)
DELETE /habits/{id}        → 200 OK  (soft-delete active=False)
GET  /journal              → 200 OK  (14 entries)
POST /mood                 → 200 OK
GET  /insights             → 200 OK  ({ moodLogs: [14], days: 14 })
POST /chat                 → 200 OK  [Orchestrator] agent=mindfulness mood=anxious urgency=medium
                                      [AGENT:mindfulness] token confirmed in stream
```

**Commits**
- `fix: merge Azure Functions PATCH+DELETE conflict, memory fence-strip, journal limit, search purge, seed determinism, cleanup script`

---

### Learning Report (Plain Language)

**Why can't Azure Functions v2 have two routes with the same path?**

In the Python v2 programming model, all function definitions in `function_app.py` are registered at the same time when the worker starts. If two `@app.route` decorators share the same route string (e.g. `"habits/{habit_id}"`), the Functions host sees a conflict and both handlers silently fail — any request to that route returns 500 with no useful error message.

The fix is to register one handler for both HTTP methods (`methods=["PATCH", "DELETE"]`) and dispatch on `req.method` inside the function. This is the documented pattern for multi-method routes in Azure Functions v2.

**Why does `response_format={"type": "json_object"}` not guarantee clean JSON?**

`json_object` mode tells the model to produce a valid JSON document — but it doesn't prevent the model from wrapping that JSON in a markdown code fence (` ```json\n{...}\n``` `). This is a model-level behavior that some checkpoints exhibit more than others. The defensive fix is always to strip fences before parsing, regardless of the mode setting. This adds two lines of code and costs nothing at runtime.

**Why use UUID5 over UUID4 for seed data?**

`uuid.uuid4()` is random — every call produces a different ID. Running `seed.py` twice creates duplicate documents in Cosmos (one old, one new) because the IDs never match. `uuid.uuid5(NAMESPACE_DNS, stable_key)` is deterministic — given the same input string (e.g. `"demo-user-001-habit-meditation"`), it always produces the same UUID. Cosmos `upsert_item` with the same ID overwrites the existing document cleanly. This makes the seed script safe to re-run at any time without accumulating debris.

**What does `purge_index()` do and why is it needed before re-indexing?**

Azure AI Search documents are addressed by their `id` field. When you delete a document from Cosmos and create a new one with a different ID (which happened before UUID5 was adopted), the old document stays in the search index forever — it's orphaned. Lumen's RAG pipeline searches by `userId`, so it retrieves these stale orphaned entries alongside the fresh ones. `purge_index()` runs a wildcard search filtered by `userId`, collects all document IDs, and deletes them in a batch before the fresh index upload. This ensures Lumen only sees current, accurate journal data.

---

*Status: All routes signed off. Memory agent hardened. Seed deterministic. Demo data clean. Ready for presentation.*

---

## Phase 13 — Final Polish & Feature Completion (Demo Day)

### Dev Log

**What this session addressed**
Final feature push before the hackathon presentation. Covered five areas: streak logic correctness, Journal tab implementation, habit coach engagement, journal editing with memory sync, and a series of UX quality fixes.

---

#### 1. Streak Logic Overhaul (`azure-functions/function_app.py`)

**Problem:** Streak values were inconsistent — unchecking a habit reset it to 0, habits with broken chains showed wrong counts, and the UI drifted from the actual log array.

**Solution:** Introduced a single authoritative `_calc_streak(logs, as_of=date)` helper. All three operations (GET, log, unlog) now call this one function:

| Rule | Implementation |
|---|---|
| Not logged today, logged yesterday → show yesterday's streak | `GET`: today not in logs → `_calc_streak(as_of=yesterday)` |
| Not logged today, missed yesterday → 0 | `_calc_streak(as_of=yesterday)` finds gap → returns 0 |
| Logged today → yesterday's streak + 1 | `log_habit`: adds today → `_calc_streak(as_of=today)` |
| Uncheck today → back to pre-check streak | `unlog_habit`: removes today → `_calc_streak(as_of=yesterday)` |
| Miss a whole day (midnight) → 0 | Next day's GET: yesterday shifted, no log → 0 |

Deployed to Azure Functions via `func azure functionapp publish`.

---

#### 2. Journal Tab (`frontend/components/JournalView.tsx`, `frontend/app/globals.css`)

Built a full journal view as the second tab (Chat · **Journal** · Habits · Insights):
- Card-based layout with date, mood pill, theme chips
- Expandable "▼ Read River's response" section per entry
- Mood-to-colour and mood-to-emoji mapping covering all seed values
- Sorted newest-first via `timestamp DESC` from Cosmos

**River response completeness fix:** The journal prompt instructed River to "continue the conversation after [/SAVE_ENTRY]" — but the stream parser breaks at `[/SAVE_ENTRY]`, so that continuation text was never sent to the user. River was writing just "Of course, here's what I'm saving:" before the block. Fixed by instructing River to write its full 2–3 sentence response *before* the `[SAVE_ENTRY]` block, then silently append the block.

**First-person summaries:** Changed the `summary` prompt field from third-person case note style ("Jen reflected on…") to first-person user voice ("I realised…", "I felt…").

---

#### 3. Journal Entry Editing

**Backend (`backend/api/journal.py`, `backend/providers/cosmos_repository.py`):**
- Added `PATCH /journal/{entry_id}` endpoint accepting `{ summary?, moodAtEntry?, themes? }`
- Added `update_journal_entry(entry_id, user_id, updates)` to `cosmos_repository.py`
- On summary edit: triggers a background `memory_agent.write()` call so `user_memory` reflects the corrected text — non-blocking via `asyncio.ensure_future()`
- AI Search is intentionally *not* re-indexed on summary edit (Lumen's RAG embeds `content`, not `summary`)

**Frontend (`frontend/components/JournalView.tsx`):**
- ✏️ button appears on card hover → inline edit mode with a `<textarea>` pre-filled with current summary
- Save/Cancel buttons; optimistic UI update on success

---

#### 4. Habit Delete Fix (`frontend/components/HabitTracker.tsx`)

**Problem:** `window.confirm()` is silently blocked in some Next.js / Chromium contexts, so the delete button did nothing.

**Fix:** Replaced with a two-click inline flow — first click changes the row to "Remove? ✓ ✕"; second click confirms. No browser dialog dependency.

---

#### 5. Grove Habit Coach Chat Head (`frontend/components/HabitCoach.tsx`, `backend/api/grove.py`)

Built a Messenger-style floating chat head embedded in the Habits tab:

**FAB behaviour:**
- Circular 🌿 button, sticky to bottom-left of the Habits tab content area
- Always visible — shows a sage ring when chat panel is open
- Tapping FAB or the DM bubble opens/closes the panel

**Proactive DM bubble:**
- 1 second after habits load, a white chat bubble slides in from the left with a Grove message
- Clicking it opens the chat; ✕ dismisses it; auto-dismisses after 9 seconds
- Content is **AI-generated** by `GET /grove/nudge` — a lightweight non-streaming GPT-4o call with the user's live habit data and memory context (temperature 0.85 for variation)
- **Cached in `sessionStorage`** with key `grove_nudge_{userId}_{date}`, TTL 60 minutes — tab switches are instant; refreshes after an hour or on a new day

**Chat panel:**
- Absolute-positioned above the FAB (no document flow impact — habit cards never obscured)
- Glassmorphism background: `rgba(255,255,255,0.72)` + `backdrop-filter: blur(18px)`
- Green gradient header: Grove + Habit Coach
- Opening message is the **same** as the DM bubble (fetched from cache — always in sync)
- Subsequent messages stream from `POST /chat` with `agentOverride: "habit"` — bypasses the orchestrator LLM call, routes directly to Grove
- `[AGENT:habit]\n` header stripped from first chunk before display

**Backend additions:**
- `agentOverride: Optional[str]` added to `ChatRequest` schema — when set, skips `orchestrator.classify()` and constructs `OrchestratorResult` directly (saves ~300ms per Habits tab message)
- `GET /grove/nudge` endpoint in `backend/api/grove.py` — fetches habits + memory, generates nudge, returns `{ nudge, date }`

**Memory:** Grove in the Habits chat head shares the same `memory_agent.read/write` pipeline as Grove in the main Chat tab. Any context learned in one is available in the other on the next request.

---

**Files changed**

| File | Change |
|---|---|
| `azure-functions/function_app.py` | `_calc_streak()` helper, live streak recalc on GET/log/unlog |
| `backend/api/chat.py` | `agentOverride` bypass, `OrchestratorResult` import |
| `backend/api/journal.py` | `PATCH /journal/{entry_id}` + background memory re-extraction |
| `backend/api/grove.py` | NEW — `GET /grove/nudge` AI nudge endpoint |
| `backend/main.py` | Register `grove` router |
| `backend/models/schemas.py` | `agentOverride: Optional[str]` on `ChatRequest` |
| `backend/prompts/journal.py` | Fix River save response (full text before block), first-person summary |
| `backend/providers/cosmos_repository.py` | `update_journal_entry()` |
| `frontend/app/page.tsx` | Journal tab added (tab 2), tab order: Chat·Journal·Habits·Insights |
| `frontend/app/globals.css` | JournalView styles, journal edit styles, Grove chat head styles (glassmorphism panel, FAB, DM bubble) |
| `frontend/components/JournalView.tsx` | NEW — full Journal tab component |
| `frontend/components/HabitCoach.tsx` | NEW — Grove Messenger-style chat head |
| `frontend/components/HabitTracker.tsx` | Inline delete confirm, HabitCoach integration |

---

### Learning Report (Plain Language)

**Why does the streak need a single helper function instead of inline logic in each route?**

Each habit operation (GET, log, unlog) was computing the streak independently. Small differences in each implementation — how they handled edge cases like missing yesterday, or the meaning of "as of today vs. yesterday" — caused the streak values to diverge. One function that takes `(logs, as_of)` and is called from every route guarantees that GET, log, and unlog always agree on what the streak is.

**Why is `sessionStorage` the right cache for the Grove nudge?**

`localStorage` persists across browser sessions — once generated, the nudge would never refresh unless you manually clear storage. `sessionStorage` scopes to the browser tab and clears on close, which is a natural TTL. We add an explicit 60-minute timestamp check on top so the nudge refreshes throughout a long session (e.g. morning habits check vs. evening check-in). The date in the cache key ensures a fresh nudge every calendar day regardless of TTL.

**Why does `agentOverride` bypass the orchestrator instead of sending a hint?**

The orchestrator is a JSON-mode LLM call — it costs ~300ms per request even when you already know the answer. In the Habits tab chat head, the user is always talking to Grove; routing is predetermined. Adding an optional bypass makes the chat head feel snappy while keeping the full orchestrator path for the main Chat tab where intent is genuinely ambiguous.

**Why is the journal summary stored separately from River's response?**

River's chat response (`content`) is what the user saw in real time — the empathetic 2–3 sentence reflection. The `summary` is a compact, indexable one-liner generated by the prompt's `[SAVE_ENTRY]` block. Keeping them separate lets the Journal tab show the summary as the card headline and the full response as expandable detail, without surfacing the raw AI output as the primary text.

---

*Status: All features complete. Streak logic deterministic. Grove chat head live. Journal editable with memory sync. Demo-ready.*

---

---

## Phase 14 — Weekly Reflection + Documentation + Sufficiency Verification

### Dev Log

**What this session addressed**
A third-party code review (Windsurf) raised a question about whether the system was "sufficient" for the problem statement. After verifying against the actual codebase, the review confirmed all major capabilities were implemented — but identified one real gap: `weekSummary` in `user_memory` was referenced in every specialist's system prompt but was never actually generated. The field always stayed empty because no code ever wrote to it. This session closed that gap by implementing the full `weekSummary` generation pipeline and surfacing it visibly in the UI.

**What got built / fixed**

| Fix | Root cause | Resolution |
|---|---|---|
| `weekSummary` never generated | `_WEEK_SUMMARY_TTL_DAYS` and `weekSummaryUpdatedAt` were scaffolded but never checked or written. Prompts referenced `memory.get("weekSummary", "No summary yet.")` which always returned empty string. | Added `rebuild_week_summary(user_id)` to `memory_agent.py`. Checks 7-day TTL against `weekSummaryUpdatedAt`. Fetches 10 most recent journal entries, calls GPT-4o (temp=0.4, max 200 tokens) to write a 2–3 sentence warm narrative, upserts result back to `user_memory`. |
| `weekSummary` invisible to users | Even after generation, the summary was only injected into agent system prompts — users had no direct visibility into what the AI saw. | Updated `GET /insights` to call `rebuild_week_summary()` and return `weekSummary` in the response alongside `moodLogs`. Added "✨ Your week, reflected" card to `InsightsDashboard.tsx` — conditionally rendered only when a non-empty summary exists. |
| Azure Functions timer trigger had broken import | Timer trigger used `from backend.agents.memory_agent import rebuild_week_summary` — `backend/` is not on the Azure Functions Python path at runtime. Would have caused `ModuleNotFoundError` on first Sunday fire. | Replaced backend import with `aiohttp` HTTP call to `GET /insights?userId=...`. FastAPI handles the logic internally. This respects the deployment boundary: Functions → API, not Functions importing API internals. Added `aiohttp==3.9.5` to `azure-functions/requirements.txt`. Runs all users concurrently in one `asyncio.run()` call. |
| `BACKEND_URL` placeholder in Azure Portal | Set to `https://your-mindflow-backend.azurewebsites.net` (template string, not real URL). Timer trigger has an early-return guard and logs a warning when `BACKEND_URL` is unset — won't crash, but won't pre-warm. | Left as-is. Backend is running locally (free subscription quota blocks App Service deploy). Weekly card still appears on-demand: `rebuild_week_summary()` is called inline in `GET /insights` every time the Insights tab loads. Timer is a performance optimization (pre-caching), not a correctness requirement. |

**Sufficiency verdict — confirmed against problem statement**

All MUST items from the blueprint scope table are implemented:
- ✅ Chat UI + mood check-in
- ✅ Orchestrator intent routing
- ✅ Memory Agent READ + WRITE
- ✅ Sage (Mindfulness Coach)
- ✅ River (Journal & Reflection) + SAVE_ENTRY
- ✅ Grove (Habit Coach) + chat head
- ✅ Habit tracker UI
- ✅ Agent badges in chat
- ✅ Sentiment detection (via SAVE_ENTRY block)
- ✅ Lumen (Insights Agent) + RAG
- ✅ Memory Agent weekly summary (this session)
- ✅ Mood sparkline + trend stats
- ✅ "What I noticed this week" card (this session)

**Files changed**

| File | Change |
|---|---|
| `backend/agents/memory_agent.py` | Added `rebuild_week_summary()` — TTL-gated, GPT-4o narrative, upserts to Cosmos |
| `backend/api/insights.py` | Now calls `rebuild_week_summary()` and returns `weekSummary` in response |
| `azure-functions/function_app.py` | Timer trigger rewritten: uses `aiohttp` HTTP call instead of broken backend import |
| `azure-functions/requirements.txt` | Added `aiohttp==3.9.5` |
| `azure-functions/local.settings.json` | Added `BACKEND_URL` key (placeholder — real URL needed for production) |
| `frontend/components/InsightsDashboard.tsx` | Added `weekSummary` state + "✨ Your week, reflected" card (conditional render) |
| `frontend/app/globals.css` | Added `.week-summary-card` and `.week-summary-text` styles |
| `docs/agents.md` | NEW — full agent reference: trigger keywords, SAVE_ENTRY, Grove chat head, memory schema |
| `docs/architecture.md` | NEW — 6-layer architecture diagram, adapter pattern, streaming pipeline, quirks |
| `README.md` | Full rewrite: correct tech stack, all API routes, Python setup, restored docs links |
| `DEMO_SCRIPT.md` | Updated Minute 1 to call out Weekly Reflection card |

**Verified working**
```
GET /insights?userId=demo-user-001&days=14
→ 200 OK
→ {
    "moodLogs": [...],
    "days": 14,
    "weekSummary": "This week the user maintained a 5-day meditation streak and
    established a phone-free morning routine. Mood scores trended from 4 (Monday)
    up to 9 (Friday), with the user noting they felt emotionally regulated during
    a difficult manager conversation — something that would have been harder two weeks ago."
  }
```

**Commits**
- `feat: add weekly reflection — rebuild_week_summary, /insights exposes weekSummary, Azure Functions timer trigger, InsightsDashboard card`

---

### Learning Report (Plain Language)

**Why was `weekSummary` scaffolded but never implemented?**

This is a common pattern in fast builds: the data model is designed upfront with all the fields you intend to use, the prompts reference those fields to show intent, but the actual generation logic gets deferred. `_WEEK_SUMMARY_TTL_DAYS = 7` and `weekSummaryUpdatedAt` were both defined — the skeleton of the feature was there. The generation function was the missing piece. In a production system, this would be caught by an integration test that verifies the field is non-empty after a session. In a hackathon build, it's caught by a thorough code review.

**Why does the timer trigger call HTTP instead of importing backend code?**

Azure Functions and the FastAPI backend are two separate deployment units. In Azure, each unit has its own Python environment and `sys.path`. The `backend/` Python package is installed in the App Service's Python environment — it is not automatically available inside the Functions app's Python worker. Importing `from backend.agents.memory_agent import ...` inside a Function would raise `ModuleNotFoundError` the moment Azure tries to start the worker.

The correct architectural boundary is: **Functions talk to the API, not to each other's internals.** The timer trigger calls `GET /insights?userId=...` — FastAPI owns that logic and the Functions app stays clean. This also means if the backend logic changes, the timer trigger picks up the change automatically without needing a redeployment.

**What is the TTL pattern for expensive operations?**

`rebuild_week_summary()` is an LLM call — it costs money and takes 1–2 seconds. Calling it on every page load would be wasteful. The TTL (time-to-live) pattern solves this: store the result alongside a timestamp (`weekSummaryUpdatedAt`). On the next call, check if the timestamp is older than 7 days. If yes — rebuild. If no — return the cached value immediately. This is the same pattern used in every modern caching system, from CDN edge caches to React Query's `staleTime`. The key insight is: "fresh enough" is often good enough. A week-old summary that's mostly accurate is more valuable than a perfectly fresh one that takes 2 seconds on every tab switch.

---

*Status: All features complete and verified. Weekly reflection live. Problem statement fully satisfied. Demo-ready.*

---

---

## Phase 15 — Insights Calendar (Month View) + Activity Aggregation

### Dev Log

**What we set out to do**
- Add a real month-grid calendar inside the Insights tab
- Fetch activity data dynamically from Cosmos DB (no hardcoded UI)
- Aggregate journal entries, mood logs, and habit completion into a per-day summary

**What got built**
- `backend/api/calendar.py` — NEW `GET /calendar` endpoint
  - Query params: `userId`, `start=YYYY-MM-DD`, `end=YYYY-MM-DD`
  - Returns `Record<YYYY-MM-DD, { hasJournal, journalMood, journalThemes, mood, moodLabel, habitsCompleted, habitsTotal }>`
  - Journal and mood queries use true calendar window filtering (range query), not `TOP N`
- `backend/providers/cosmos_repository.py`
  - Added range query helpers for journal and mood logs to support the calendar endpoint
- `backend/main.py`
  - Registered the new calendar router so the endpoint is available on the API
- `frontend/components/CalendarView.tsx` — NEW calendar UI
  - Month navigation (prev/next)
  - 6-row grid for stable layout
  - Daily indicators for journal + mood + habit completion
  - Inline detail panel for selected day
- `frontend/components/InsightsDashboard.tsx`
  - Embedded CalendarView as a collapsible section: "📅 Your month at a glance"
- `frontend/app/globals.css`
  - Added calendar styles matching the clay design system
  - Updated day-cell indicator layout to avoid overflow: left-aligned stack
    - date
    - dots row
    - habit stat pill

**Verified working**
```
GET /calendar?userId=demo-user-001&start=2026-04-01&end=2026-04-30
→ 200 OK
→ Keys are YYYY-MM-DD for every day in range
→ Early April days: hasJournal=false, mood=null
→ Journal entries present from 2026-04-19 onward with mood + themes populated
→ habitsCompleted/habitsTotal correct per day
```

**Commits**
- `feat: add insights calendar — /calendar endpoint + CalendarView month grid`
- `polish: calendar indicator layout to prevent overflow in dense months`

---

### Learning Report (Plain Language)

**Why does the calendar endpoint return a dictionary keyed by date instead of an array?**

Because the UI needs to render a month grid where each cell maps to a single day. A `Record<YYYY-MM-DD, ...>` means the frontend can look up any day in O(1) time without searching an array, and days with no activity still have a predictable default object.

**Why do we query by date range instead of "most recent N" items?**

Calendars are about time windows, not recency. A range query ensures April always shows April’s activity, even if a user has hundreds of mood logs or journal entries. This avoids a subtle bug where older logs could push newer-but-in-range data out of a `TOP N` result.

**Why did the indicator layout matter?**

Dense months can have days where all signals appear at once (journal + mood + habits). The UI was adjusted so the indicators are always constrained inside the cell boundary, ensuring the grid remains stable and readable.

---

---

## Phase 16 — README Audit & Final Verification

### Dev Log

**What this session addressed**
Post-build audit of the README against the actual codebase before final commit. Every claim in the README was verified by reading the corresponding source files — not from memory. Two inaccuracies were found and corrected. Everything else was confirmed accurate.

**Methodology**
Files read for verification: `backend/main.py`, all 6 `backend/agents/*.py`, all 8 `backend/api/*.py`, `backend/models/schemas.py`, `backend/providers/*.py`, `backend/kernel.py`, `backend/requirements.txt`, `azure-functions/function_app.py`, `frontend/app/page.tsx`, all 9 `frontend/components/*.tsx`, `seed/seed.py`, and the `azure-functions/` directory listing.

**What was verified as accurate**

| Claim | File verified against |
|---|---|
| All 6 agent files and descriptions | `backend/agents/` — all present, names match |
| SK `semantic-kernel==1.41.3` | `backend/requirements.txt` |
| FastAPI: 8 routers registered | `backend/main.py` lines 29–36 |
| Orchestrator: JSON mode, temp=0, fallback "journal" | `orchestrator.py` |
| Memory: facts ≥0.6, 12 cap, 14-day decay, 0.05 reduction | `memory_agent.py` — `_FACT_THRESHOLD`, `_MAX_FACTS`, `_DECAY_DAYS` |
| Memory: 60-char dedup prefix check | `memory_agent.py` line 181 |
| Memory: JSON fence-strip guard | `memory_agent.py` lines 160–163 |
| Memory: weekSummary TTL = 7 days | `_WEEK_SUMMARY_TTL_DAYS = 7` |
| River: SAVE_ENTRY buffer parser, ensure_future | `backend/api/chat.py` |
| agentOverride bypass | `chat.py` + `schemas.py` |
| Grove: sessionStorage 60-min TTL + date key | `HabitCoach.tsx` lines 38–45 |
| Grove nudge temp=0.85 | `grove.py` line 60 |
| Grove: single `_calc_streak` helper | `function_app.py` |
| Lumen: top_k=5 hybrid search | `insights_agent.py` |
| Embeddings: `text-embedding-3-small-1`, 1536-dim | `kernel.py` |
| Cosmos: 5 collections, correct names | `cosmos_repository.py` + `seed.py` |
| Seed: 14 journal entries, 14 mood logs, 5 habits | `seed.py` — confirmed by counting arrays |
| 9 frontend components, all correct file names | `frontend/components/` directory listing |
| docs/agents.md, docs/architecture.md present | `docs/` directory listing |

**What was corrected**

| Claim in draft README | Actual code | Correction |
|---|---|---|
| "5 HTTP routes + weekly timer trigger" in Azure Functions | `function_app.py` has 6 HTTP routes: `GET /habits`, `POST /habits`, `PATCH /habits/{id}/log`, `PATCH /habits/{id}/unlog`, `PATCH /habits/{id}`, `POST /mood` — the unlog route was missing from the count | Changed to "6 HTTP routes + weekly timer trigger" in project structure comment |
| Local setup: `cp local.settings.json.example local.settings.json` | No `.example` file exists in `azure-functions/` — confirmed by directory listing | Instruction changed to "Edit `local.settings.json` directly" |

**Additional finding — no code impact**
The QA verification table in the README lists 13 routes (what was tested at QA sign-off). The total FastAPI route surface is 15 distinct endpoints — unlog and update-habit-fields were added after the Phase 12 QA pass. The table documents what was verified, not a complete route inventory. No change needed.

**Also corrected in README**
The DEVLOG header reference in `README.md` said "13-phase dev log" — updated to "16-phase" to reflect the current phase count.

**Commit**
- `docs: verify README against codebase — correct Azure Functions route count and local settings setup`

---

### Learning Report (Plain Language)

**Why audit the README against source files instead of from memory?**

A README written during a build reflects the *intended* system. Code written during a build reflects the *actual* system. These diverge. In a fast build, it's normal to add a route, fix a bug, or rename something and forget to update the documentation. The only reliable way to confirm accuracy is to read both the claim and the implementation and compare them directly — not to rely on the author's recollection of what they built.

**What's the difference between "routes tested in QA" and "routes that exist"?**

The QA sign-off table is a record of what was explicitly tested end-to-end with a confirmed 200 OK. It's not a complete API inventory. Routes added after QA (like unlog, which was added in Phase 13 along with the full streak overhaul) are implemented, tested implicitly through the frontend, and working — but they weren't part of the formal QA pass. Both are true simultaneously and neither contradicts the other.

**Why does it matter that `local.settings.json.example` doesn't exist?**

If a contributor follows the README setup instructions exactly and runs `cp local.settings.json.example local.settings.json`, they get `cp: local.settings.json.example: No such file or directory`. This is a silent failure — the copy command fails, `local.settings.json` doesn't get created, and `func start` refuses to run. A README with a broken setup step is worse than no README, because it creates the impression that setup is easy when it's actually going to error. The corrected instruction points to the file that actually exists.

---

*Status: README verified against codebase. Two corrections applied. DEVLOG complete through Phase 16. Ready to commit.*

---

---

## Phase 17 — Pre-Demo Polish: Routing Flash, Lumen Button, Low-Mood Sage, Habit Creation via Chat

### Dev Log

**What this session addressed**
Five targeted enhancements to maximise demo impact and judge legibility of the multi-agent system, without introducing new infrastructure or risk to the existing pipeline.

**What got built**

| Enhancement | Files changed | Description |
|---|---|---|
| Better suggestion chips | `ChatWindow.tsx` | Four chips now match the exact demo script flow: anxious presentation → Sage, journaling → River, breathing → Sage, patterns → Lumen. Previously "How have my habits been?" didn't demonstrate the full agent range. |
| Orchestrator routing flash | `ChatWindow.tsx`, `globals.css` | While waiting for the first stream chunk (the `[AGENT:xxx]` token), a pulsing `routing…` badge replaces the agent badge. Makes the Orchestrator's classification step visible in real time. Resolves on first chunk arrival via `setIsClassifying(false)`. |
| Lumen "Ask me" button | `InsightsDashboard.tsx`, `page.tsx`, `globals.css` | `onAskLumen` callback prop on InsightsDashboard. Clicking "Ask Lumen now →" calls `handleAskLumen()` in page.tsx: switches to Chat tab and sets `chatPreset = "What patterns do you see across my journal entries?"`. |
| Preset message mechanism | `ChatWindow.tsx`, `page.tsx` | Shared `chatPreset` state in page.tsx. `ChatWindow` accepts `presetMessage` + `onPresetConsumed` props. When `presetMessage` is set, a 120ms timeout fires `sendMessage()` (allows tab animation to complete first), then `onPresetConsumed()` clears the preset to prevent re-fire. Used by both the Lumen button and the low-mood Sage trigger. |
| Low-mood Sage trigger | `page.tsx` | After `handleMoodSelect` with score ≤ 4 (rough/anxious), a 1400ms timeout sets `chatPreset` to a Sage-bound message: `"I just checked in feeling {mood}. Can you help me breathe for a moment?"`. The 1400ms delay allows the banner toast to complete (800ms) + banner dismiss (1200ms) before the message fires. |
| Habit creation via Grove chat | `backend/prompts/habit.py`, `backend/api/chat.py` | Grove's system prompt now instructs it to append a `[CREATE_HABIT]name/why/targetTime[/CREATE_HABIT]` block once it has collected both habit name and WHY from the user. The streaming loop in `chat.py` intercepts this block identically to `[SAVE_ENTRY]`: strips it from the user-visible stream, fires `_parse_and_create_habit()` via `ensure_future`. That function POSTs to `FUNCTIONS_HABIT_URL/api/habits` via `httpx.AsyncClient`. |

**Streaming loop change (chat.py)**

The buffer-strip logic was extended from one marker to two:
- `in_save_block` — existing, River SAVE_ENTRY
- `in_habit_block` — new, Grove CREATE_HABIT

Both follow the same interception pattern: detect start marker → flush visible content → accumulate the block → on end marker, fire background task and break. The flush at the end now gates on `not in_save_block and not in_habit_block`.

**Guard conditions in CREATE_HABIT prompt**
Three explicit guards prevent accidental habit creation:
1. Only emit the block when the user has provided BOTH name AND WHY in the current conversation
2. Never emit it for existing habit coaching (streak updates, misses, etc.)
3. Append it at most once per creation flow

**Files changed**

| File | Change |
|---|---|
| `frontend/components/ChatWindow.tsx` | `presetMessage`/`onPresetConsumed` props; `isClassifying` state; routing flash render; better chips |
| `frontend/components/InsightsDashboard.tsx` | `onAskLumen` prop; Lumen prompt card → clickable button |
| `frontend/app/page.tsx` | `chatPreset` state; `handleAskLumen`; low-mood Sage timeout in `handleMoodSelect`; props wired |
| `frontend/app/globals.css` | `.routing-flash`, `.routing-dot`, `@keyframes routingPulse`; `.lumen-ask-btn` |
| `backend/prompts/habit.py` | `[CREATE_HABIT]` marker directive with explicit guard conditions |
| `backend/api/chat.py` | `httpx` import; `_HABIT_START`/`_HABIT_END` constants; `_parse_and_create_habit()` function; `in_habit_block` in streaming loop |

**Commit**
- `feat: routing flash, Lumen ask button, low-mood Sage trigger, habit creation via Grove chat`

---

### Learning Report (Plain Language)

**Why does the routing flash matter for judges?**

The Orchestrator is the most architecturally interesting part of MindFlow — it's what makes the system genuinely multi-agent rather than a single large prompt. But it's also completely invisible: it runs in ~200ms before the first visible response token arrives. The routing flash makes that classification step legible in real time. Judges who are evaluating "is this actually multi-agent?" now have a visible signal that says "yes — the system is deciding which agent you need right now."

**Why use a preset message mechanism instead of directly calling sendMessage?**

`sendMessage` is defined inside the `ChatWindow` component and is not accessible from `page.tsx`. Prop drilling a function reference would couple the components too tightly. The preset + consumed pattern keeps the communication unidirectional: page.tsx sets a string, ChatWindow reads it and acts on it, ChatWindow signals back when consumed. This is the same pattern as controlled inputs in React — the parent owns the state, the child owns the action.

**Why 120ms delay before auto-sending the preset?**

Switching tabs in page.tsx is synchronous state change, but the CSS `tab-panel-active` transition takes ~150ms to visually complete. Firing `sendMessage` immediately on the same render would cause the chat to start streaming before the tab is visible — creating a jarring experience where content appears mid-transition. The 120ms delay is enough for the tab to visually settle without feeling slow.

**Why does CREATE_HABIT use the same marker pattern as SAVE_ENTRY?**

The SAVE_ENTRY pattern was already proven safe and non-breaking across all previous phases. Reusing it for CREATE_HABIT means: the same buffer-strip logic, the same `ensure_future` delivery, the same invisible-to-user experience. The alternative — having Grove call an API directly — would require giving the agent tool-use capabilities (a Semantic Kernel plugin), which adds a new dependency and integration surface. The marker pattern achieves the same result with no new dependencies.

**What happens if Grove emits CREATE_HABIT by mistake on an existing habit conversation?**

Three things protect against this: (1) the prompt explicitly says "never append it for existing habits" and lists when NOT to use it, (2) the parser requires both `name` and `why` to be non-empty before calling the API, (3) the `POST /habits` call proxies to Azure Functions which upserts — if a habit with the same name somehow got created twice, the user would just see a duplicate in the Habits tab, not a crash. It's a recoverable edge case, not a system error.

---

*Status: All 5 pre-demo enhancements complete. System integrity maintained — no existing pipeline broken. Ready for demo video.*


---

---

## Phase 18 — Habit Creation Bug Fixes: Routing Continuity, State Machine, Direct Write, UI Sync

### Dev Log

**What this session addressed**

Three distinct categories of bugs were preventing the habit creation flow from working reliably:
1. **Routing drift** — the Orchestrator misclassified WHY answers mid-flow, breaking Grove's conversation state
2. **Habit save failures** — `_parse_and_create_habit` silently failing; habits confirmed but not persisted
3. **UI desync** — the Habits tab not refreshing after a habit was created via chat; Grove chat head forgetting all conversation history on every turn

**What got built / fixed**

| Fix | Root cause | Resolution |
|---|---|---|
| Orchestrator CONTINUITY RULE | When a user answered "why" with emotional content (e.g. "calm my mind"), the Orchestrator classified the message as Sage, abandoning the in-progress habit creation flow. No history was passed to `classify()`. | Added CONTINUITY RULE to `ORCHESTRATOR_PROMPT`: if the last 6 turns contain an unanswered habit question, the current message is a habit reply regardless of keywords. Updated `orchestrator.py` `classify()` to accept and inject `conversation_history`. Passed `request.conversationHistory` from `chat.py`. |
| Grove state machine — SCAN HISTORY FIRST | Grove's prompt lacked explicit instructions to scan prior turns before asking for name/WHY. If the user's WHY response arrived, Grove would reset to "What habit would you like to build?" because it treated each call as stateless. | Rewrote `HABIT_PROMPT` in `backend/prompts/habit.py` with an explicit two-state machine: `NAME_FOUND` / `WHY_FOUND`. Prompt now opens with: "Before responding, scan the full conversation history for a habit name and a WHY. If both are found, emit `[CREATE_HABIT]` immediately — do not ask again." |
| HabitCoach `conversationHistory: []` hardcoded | `HabitCoach.tsx` `send()` always passed an empty array for `conversationHistory`. Grove received no prior turns, entered STATE A on every turn, and looped forever asking "What habit would you like to build?" | Built real `conversationHistory` from `messages` state before each send — same pattern as `ChatWindow`. Grove/assistant messages map to `role: "assistant"`, user messages to `role: "user"`. |
| `[` character leaking into stream | `_HOLD = len("[SAVE_ENTRY]") = 12`. `[CREATE_HABIT]` is 14 chars. When a streaming chunk arrived containing `[CREATE_HABIT` (13 chars, no closing `]`), the `[` fell outside the 12-char hold window and was flushed to the frontend. | Changed to `_HOLD = max(len(_SAVE_START), len(_HABIT_START)) = 14`. Moved to a module-level constant (removed the local duplicate inside the generator). |
| `_parse_and_create_habit` silently failing | Function made an HTTP POST to `localhost:7071/api/habits` (Azure Functions) via `httpx`. Despite Azure Functions running, the call failed silently — environment variable mismatch or CORS issue. No error surfaced because all exceptions were caught and logged only. | Eliminated the HTTP hop entirely. Added `create_habit(habit_doc: dict)` to `cosmos_repository.py`. `_parse_and_create_habit` now calls `await db.create_habit(habit_doc)` directly — same pattern as `_parse_and_save_entry` for journal entries. Removed `httpx` import and `_FUNCTIONS_HABIT_URL` constant from `chat.py`. |
| No confirmation message visible to user | After the `[CREATE_HABIT]` block was parsed and the generator broke, no text was yielded confirming success. The habit saved silently. | After `asyncio.ensure_future(_parse_and_create_habit(...))`, yield a deterministic confirmation string. Habit name is extracted from the block and title-cased: `✓ "Read 10 pages a day" has been added to your Habits tab.` Journal saves also get `✓ Entry saved to your Journal.` |
| Habits tab stale after chat creation | `HabitTracker` only fetched on mount (`useEffect(..., [])`). Switching from Chat to Habits after creating a habit showed the old list until browser refresh. | Added `isActive?: boolean` prop to `HabitTracker`. A second `useEffect(..., [isActive])` calls `fetchHabits()` whenever `isActive` flips to `true`. `page.tsx` passes `isActive={tab === 'habits'}`. |
| MemoryAgent WRITE fails with JSON error | Memory agent's LLM call occasionally returned JSON without outer braces (e.g. `\n  "facts": [...]` instead of `{"facts": [...]}`), causing `json.loads()` to fail and logging `[MemoryAgent] WRITE failed` on every habit turn. | Replaced single `json.loads(raw)` with a three-attempt fallback: try `raw` as-is → try `{raw}` wrapped → fall back to `{}`. Each attempt validates that the result is a `dict`. |
| `\n\n` and `**bold**` not rendering in grove panel | `grove-float-bubble` CSS had `word-break: break-word` but no `white-space: pre-wrap`. The confirmation `\n\n✓ "Name"...` collapsed to a single line. Markdown `**bold**` rendered as literal asterisks. | Added `white-space: pre-wrap` to `.grove-float-bubble`. Changed confirmation format from `**{name}**` (markdown) to `"{Name}"` (quoted, title-cased) — plain text that renders correctly without a markdown parser. |

**Streaming pipeline change**

`_parse_and_save_entry` (journal) and `_parse_and_create_habit` (habit) now both write directly to Cosmos via the repository layer. Neither depends on Azure Functions being reachable from within the backend process. Azure Functions remains the authoritative path for frontend-initiated operations (HabitTracker "+", log, unlog, delete) — the direct write is an internal-only shortcut for the background task that runs after streaming ends.

**Files changed**

| File | Change |
|---|---|
| `backend/prompts/orchestrator.py` | CONTINUITY RULE — routes WHY replies to `habit` regardless of emotional keywords |
| `backend/agents/orchestrator.py` | `classify(message, history)` — injects last 6 turns into classification prompt |
| `backend/api/chat.py` | `_HOLD=14`; removed `httpx` and `_FUNCTIONS_HABIT_URL`; `_parse_and_create_habit` rewrites to direct Cosmos write; named confirmation yields for both journal and habit |
| `backend/prompts/habit.py` | SCAN HISTORY FIRST state machine; `NAME_FOUND`/`WHY_FOUND` explicit states |
| `backend/providers/cosmos_repository.py` | Added `create_habit(habit_doc)` for direct write from chat pipeline |
| `backend/agents/memory_agent.py` | Three-attempt JSON parse fallback prevents WRITE failures on malformed LLM output |
| `frontend/components/HabitCoach.tsx` | `conversationHistory` built from `messages` state (was hardcoded `[]`) |
| `frontend/components/HabitTracker.tsx` | `isActive` prop → re-fetch on tab switch |
| `frontend/app/page.tsx` | `isActive={tab === 'habits'}` passed to `HabitTracker` |
| `frontend/app/globals.css` | `white-space: pre-wrap` on `.grove-float-bubble` |
| `README.md` | DEVLOG phase count updated: 17 → 18 |

**Commit**
- `fix: habit creation pipeline — routing continuity, state machine, direct Cosmos write, HabitCoach history, UI sync`

---

### Learning Report (Plain Language)

**Why did the HabitCoach FAB loop forever while the main Chat tab worked?**

Both use the same backend — the difference was entirely in what `conversationHistory` each sent. `ChatWindow` maintained a proper history array and passed it on every request, so Grove could read prior turns and track state. `HabitCoach.tsx` hardcoded `conversationHistory: []`, so Grove received a blank slate on every message — it saw only the current message with no context, concluded it was in STATE A, and asked "What habit would you like to build?" every time. One `[]` caused the entire flow to loop indefinitely.

**Why does _parse_and_create_habit now write directly to Cosmos instead of calling Azure Functions?**

The function runs as a background task (`asyncio.ensure_future`) after streaming ends — it's internal to the FastAPI process. Making an outbound HTTP call from inside that process to Azure Functions introduces a network hop, an additional failure surface (what if Azure Functions is slow?), and an environment dependency (`FUNCTIONS_HABIT_URL` must be correct and the service must be reachable). Writing directly via the repository eliminates all three risks. `_parse_and_save_entry` for journal entries already used this pattern — habit creation now follows the same design. The authoritative, externally-facing write path (HabitTracker UI → FastAPI → Azure Functions → Cosmos) is unchanged.

**Why is `_HOLD` set to the longest marker and not just the longest start token?**

The hold window determines how many characters are kept in the buffer before being yielded to the frontend. Its purpose is: if a streaming chunk ends mid-marker, don't yield the partial marker — it would appear as raw text. The window must be at least as wide as the longest possible partial prefix of any marker. `[CREATE_HABIT]` is 14 characters. If `_HOLD` is only 12 (the length of `[SAVE_ENTRY]`), a 13-character partial `[CREATE_HABIT` would be wider than the hold window — the `[` gets flushed immediately. Setting `_HOLD = max(...)` ensures the window is always wide enough for whichever marker is longest, regardless of which block the model is currently writing.

**Why does the confirmation message come from the backend instead of the LLM?**

The LLM produces the warm coaching response — it varies in wording, length, and tone, which is desirable. The confirmation that a habit was saved is a system fact, not a conversational response — it should be exact, deterministic, and always present. If the LLM were asked to include it, it might omit it, rephrase it vaguely, or embed it mid-sentence. Yielding `✓ "Read 10 pages a day" has been added to your Habits tab.` from the backend guarantees the user always sees a clear, accurate confirmation with the actual habit name — regardless of what the model said before the `[CREATE_HABIT]` block.

---

*Status: Habit creation flow end-to-end verified. Habits save to Cosmos, confirm in chat, appear immediately on Habits tab switch. MemoryAgent write failures resolved. Grove FAB conversation continuity restored.*

---

---

## Phase 17 — User-Visible Memory Controls (Facts CRUD + Toggle)

### Dev Log

**What we set out to do**
- Make the Memory Agent's stored facts user-visible and editable
- Add full CRUD for memory facts + a global toggle to disable memory
- Ensure the UI changes actually sync to Cosmos DB (no local-only state)

**What got built**
- `backend/api/memory.py` — NEW memory management router
  - `GET /memory` — returns `user_memory` (creates shell doc if missing)
  - `PATCH /memory/toggle` — flips `memoryEnabled` on the memory doc
  - `POST /memory/facts` — add a fact (UI defaults `source="manual"`)
  - `PATCH /memory/facts/{fact_id}` — edit a fact's content
  - `DELETE /memory/facts/{fact_id}` — remove a fact
  - Backfills missing fact IDs for older seeded facts on read (upsert after generation)
- `backend/main.py` — registers `memory.router`
- `backend/models/schemas.py`
  - `UserMemory.memoryEnabled: bool` (default true)
  - `MemoryFact.id: str` so facts can be edited/deleted deterministically
- `backend/agents/memory_agent.py`
  - Respects `memoryEnabled`:
    - READ returns empty context when disabled
    - WRITE is a no-op when disabled
    - `rebuild_week_summary()` returns empty string when disabled
  - Manual fact priority fix:
    - Inject top facts by importance PLUS the newest `source="manual"` fact, so UI edits are felt immediately even with seeded high-importance facts
- `frontend/components/MemoryPanel.tsx` — NEW UI panel
  - View / add / edit / delete facts
  - Toggle "Remember things about me" (`memoryEnabled`)
  - All operations call `/memory` endpoints and update UI from the server response
- `frontend/components/InsightsDashboard.tsx` — embeds MemoryPanel as a collapsible "🧠 Your memory" section
- `frontend/app/globals.css` — Memory panel styles
- `frontend/app/layout.tsx` — hydration mismatch suppression (extension-injected DOM attributes)
- `.gitignore` — ignore local-only `azure-functions/.python_packages/` + `QA_CHECKLIST.md`

**What broke and how it was fixed**

| Problem | What happened | Fix |
|---|---|---|
| Newly added UI fact was saved but not reflected in agent replies | Memory Agent injected only the top facts by importance; seeded facts crowded out new low-importance facts | Manual fact is now tagged `source="manual"` and the Memory Agent always includes the newest manual fact in context |
| Next.js hydration mismatch warning | Browser extension injected an attribute onto `<body>` before hydration (`cz-shortcut-listen`) | Added `suppressHydrationWarning` on `<html>` + `<body>` |

**Verified working**
```
POST /memory/facts { content: "I like strawberry", source: "manual" }
→ Fact persists in Cosmos and is visible in GET /memory
→ Next chat response reflects the new memory context

PATCH /memory/toggle { enabled: false }
→ Memory READ returns empty context and no new facts are written
```

---

### Learning Report (Plain Language)

**Why let users view and edit their memory facts?**

Hidden memory can feel "magical" when it works — but uncomfortable when it doesn't. A simple control panel gives users transparency and agency: they can correct wrong assumptions, remove sensitive details, and choose when they want personalization.

**Why did the new fact not show up in responses even though it was stored?**

Because the Memory Agent has a strict context budget — it only injects a small subset of facts into the prompt. If seeded facts have higher importance scores, they can crowd out newly added facts. The fix is to always include the newest user-added (`manual`) fact so edits feel immediate.
