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

A vector is a list of numbers — in our case, 1536 numbers. The embedding model (text-embedding-ada-002) converts any piece of text into this list. Similar texts produce similar vectors. The similarity between two vectors can be measured mathematically (cosine similarity).

So if you ask "Why do I feel anxious at work?" and an old journal entry says "I felt overwhelmed during the project deadline," the vectors for both texts will be close to each other — even though no exact words match. This is why AI Search finds relevant entries that keyword search would miss.

**Why is `_get_specialist()` async only for Lumen?**

The other three specialists (Sage, River, Grove) are simple — `get_agent()` is a synchronous function that just constructs a Python object. There's no network call. Lumen is different: before it can construct the agent, it needs to call Azure AI Search (a network call) to retrieve relevant journal entries. Network calls in async Python must be awaited. So Lumen's factory is `async def`, and the router function must be `async def` too.

**What does the week-over-week trend tell us?**

The trend delta compares your average mood score from the past 7 days against the 7 days before that. A positive number (↑) means your average mood is higher this week than last week. A negative number (↓) means it's lower.

This is deliberately simple — not a statistical test, just a directional signal. The goal isn't clinical accuracy; it's giving the user a meaningful reflection point: "My mood has been trending up" or "This week has been harder than last week." Lumen uses this alongside the journal context to surface a narrative rather than just numbers.

---

*Next: Phase 9 — Polish, demo script, error states, loading states*
