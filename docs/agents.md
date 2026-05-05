# MindFlow — Agent System Reference

> This document describes the 6-agent architecture: trigger keywords, system prompt philosophy, memory injection pattern, and inter-agent communication.

---

## Overview

Every user message flows through the same pipeline:

```
User message
  → Orchestrator (classify intent)
  → Memory Agent READ (assemble personalized context)
  → Specialist Agent (stream response)
  → Memory Agent WRITE (extract + store new facts)
```

All specialist agents receive `{memoryContext}` injected into their system prompt before responding. This is what makes every agent feel like it knows the user — it does, because it just looked it up.

---

## Agent 1 — Orchestrator

**File:** `backend/agents/orchestrator.py`  
**Prompt:** `backend/prompts/orchestrator.py`

### Role
Intent router. Never produces a user-facing response. Makes one fast LLM call in JSON mode to classify every incoming message.

### Output schema
```json
{
  "agent": "mindfulness | journal | habit | insights",
  "confidence": 0.0–1.0,
  "mood": "anxious | sad | okay | good | great | unknown",
  "urgency": "high | medium | low"
}
```

### Routing logic
| Trigger keywords / signals | Routes to |
|---|---|
| stressed, anxious, overwhelmed, breathe, meditate, calm, panic, can't focus, nervous | `mindfulness` |
| journal, write, reflect, how was my day, I'm thinking, I feel, I want to talk about | `journal` |
| habit, goal, routine, did I, check in, log, track, streak, missed, skipped | `habit` |
| patterns, insights, trend, what do you see, how have I been, last week | `insights` |
| unclear / ambiguous | `journal` (fallback) |

### Key design decisions
- **Temperature 0** — deterministic classification, no variation
- **JSON mode** — structured output only, no prose
- **Silent fallback** — on any exception (network timeout, malformed JSON), returns `OrchestratorResult(agent="journal")` and continues
- **Target latency:** <300ms — uses direct Azure OpenAI call, not Semantic Kernel
- **CONTINUITY RULE** — if the last 6 turns of `conversationHistory` contain an unanswered habit question (e.g. Grove asked for the user's WHY), the current message routes to `habit` regardless of emotional keywords. Prevents WHY answers being misclassified as Sage.
- **History-aware** — `classify(message, conversationHistory)` injects the last 6 turns into the classification prompt. Chat history is passed from `request.conversationHistory` in `chat.py`.

### agentOverride bypass
When `agentOverride` is set on the `ChatRequest`, the Orchestrator LLM call is skipped entirely. Used by the Grove chat head in the Habits tab where intent is always `"habit"` — saves ~300ms per message.

---

## Agent 2 — Memory Agent

**File:** `backend/agents/memory_agent.py`  
**Prompt:** `backend/prompts/memory.py`

### Role
Silent context builder. Runs on every request, never produces a user-facing response. Two passes per request.

### READ pass (before specialist)
Fetches `user_memory` document from Cosmos DB and assembles `{memoryContext}` — a structured context block injected into every specialist's system prompt.

Context block includes:
- User's display name + current mood + urgency + time of day
- Top 5 facts sorted by importance (capped at ~800 tokens total)
- Recurring themes + breakthroughs
- `weekSummary` (AI-generated narrative from last 10 journal entries)
- Learned preferences: preferred tone, best journaling time, responds well to, avoids

Returns `""` on any exception — memory failure never breaks the chat pipeline.

### WRITE pass (after specialist)
After the streaming response completes, a JSON-mode GPT call evaluates the exchange and extracts new facts.

Fact scoring rules:
| Score | Action |
|---|---|
| ≥ 0.6 | Stored |
| < 0.6 | Discarded |
| > 0.8 | Pushed to front of facts list |
| Not referenced in 14 days | Decayed by 0.05 (importance) |

Additional rules:
- **Deduplication:** First 60 characters compared (case-insensitive). Near-duplicate facts are skipped.
- **Cap:** Maximum 12 facts per user. Lowest-importance facts dropped when cap is exceeded.
- **Fence-strip guard:** If the model wraps its JSON in markdown code fences (` ```json ... ``` `), they are stripped before `json.loads()`.
- **Three-attempt JSON parse fallback:** Tries `json.loads(raw)` → `json.loads(f"{{{raw}}}")` → falls back to `{}`. Prevents WRITE failures when the LLM omits outer braces on the JSON object.

READ is **awaited synchronously** (must complete before the specialist runs). WRITE runs via `asyncio.ensure_future()` — non-blocking, after the stream completes.

### Weekly summary (`rebuild_week_summary`)
Called from `GET /insights` on every load (TTL-gated):
- Checks `weekSummaryUpdatedAt` — skips rebuild if less than 7 days old
- Fetches 10 most recent journal entries
- GPT-4o call (temp=0.4, max 200 tokens) generates a 2–3 sentence warm narrative
- Upserts `weekSummary` + `weekSummaryUpdatedAt` back to `user_memory`

---

## Agent 3 — Sage (Mindfulness Coach)

**File:** `backend/agents/mindfulness_agent.py`  
**Prompt:** `backend/prompts/mindfulness.py`

### Role
Core Capability 1 from problem statement. Guides grounding exercises and mindful moments. Urgency-aware tone.

### Trigger keywords
`stressed`, `anxious`, `overwhelmed`, `breathe`, `meditate`, `calm down`, `panic`, `can't focus`, `nervous`, `grounding`

### Behaviour
| Urgency | Response style |
|---|---|
| `high` | Slow, step-by-step. Box breathing or 5-4-3-2-1 immediately. Short sentences. |
| `medium` | Gentle check-in first. One grounding technique offered. |
| `low` | Brief mindful moment. Inquiry-based. |

### Built-in exercises
1. Box breathing (4-4-4-4)
2. Extended exhale (4-6)
3. 5-4-3-2-1 grounding
4. Body scan
5. STOP technique (Stop, Take a breath, Observe, Proceed)

### Design principles
- Never clinical language
- Short, calm sentences — calming even when streamed word-by-word
- References `{memoryContext}` — knows user's history, preferences, past breakthroughs
- Never says "you should"

---

## Agent 4 — River (Journal & Reflection Agent)

**File:** `backend/agents/journal_agent.py`  
**Prompt:** `backend/prompts/journal.py`

### Role
Core Capability 2 from problem statement. Reflective journaling companion. Default fallback agent.

### Trigger keywords
`journal`, `write`, `reflect`, `how was my day`, `I'm thinking`, `I feel`, `I want to talk about`, or any ambiguous input

### Behaviour
- Opens with **one** contextual question based on mood and memory themes — never generic
- Reflects back key phrases without interpreting them
- Asks one follow-up question at a time
- Writes full 2–3 sentence response **before** the `[SAVE_ENTRY]` block

### SAVE_ENTRY block (invisible to user)
River appends a structured block to every response:
```
[SAVE_ENTRY]
content: <River's full response text>
summary: <one-line first-person summary>
moodAtEntry: <detected mood word>
sentiment: positive | neutral | negative
themes: <comma-separated list>
[/SAVE_ENTRY]
```

The stream parser in `chat.py` intercepts this block mid-stream:
- Everything **before** `[SAVE_ENTRY]` is yielded to the user normally
- The block itself is captured but **not** yielded
- On `[/SAVE_ENTRY]`, the block is parsed and saved to Cosmos DB as a journal entry
- After save, a deterministic confirmation is yielded: `✓ Entry saved to your Journal.`

**Summary is first-person** ("I realised...", "I felt...") — not third-person case note style.

### Journal editing
`PATCH /journal/{entry_id}` lets users edit summary, moodAtEntry, and themes inline in the Journal tab. On edit, a background `memory_agent.write()` call re-extracts context from the corrected summary. AI Search is **not** re-indexed on edit (Lumen's RAG embeds `content`, not `summary`).

---

## Agent 5 — Grove (Habit Coach)

**File:** `backend/agents/habit_agent.py`  
**Prompt:** `backend/prompts/habit.py`  
**Nudge endpoint:** `backend/api/grove.py`

### Role
Core Capability 3 from problem statement. WHY-first habit coaching philosophy. No-guilt.

### Trigger keywords
`habit`, `goal`, `routine`, `did I`, `check in`, `log`, `track`, `streak`, `missed`, `skipped`

### Habit creation via chat — CREATE_HABIT block
Grove uses a two-state machine to collect both a habit name and a WHY before saving:

**SCAN HISTORY FIRST:** Before responding, Grove scans the full conversation history:
- If no `NAME_FOUND` → ask "What habit would you like to build?"
- If `NAME_FOUND` but no `WHY_FOUND` → ask "What's the reason behind this one?"
- If both `NAME_FOUND` AND `WHY_FOUND` → emit warm closing + `[CREATE_HABIT]` block

```
[CREATE_HABIT]
name: <habit name>
why: <user's WHY>
targetTime: <optional>
[/CREATE_HABIT]
```

The stream parser in `chat.py` intercepts this block identically to `[SAVE_ENTRY]`:
- Block content is captured but not yielded to the user
- On `[/CREATE_HABIT]`, `_parse_and_create_habit()` runs via `asyncio.ensure_future()`
- Writes **directly to Cosmos DB** via `db.create_habit()` — no HTTP hop to Azure Functions
- After save, a confirmation is yielded: `✓ "Habit Name" has been added to your Habits tab.`

This flow works identically in the main Chat tab and the HabitCoach FAB panel.

### General coaching behaviour
| Scenario | Response |
|---|---|
| New habit | Asks WHY before WHAT. Values-connected habits stick longer. Makes initial version tiny enough to guarantee early success. |
| Completion | Brief genuine celebration + "how did it feel?" (builds intrinsic motivation) |
| Miss | Normalizes immediately. One gentle question to find the blocker. One specific tweak. Never guilt. |
| Struggling | "What would a 5-minute version look like?" reframe |

### Design principles
- No willpower language
- No "you should"
- "Missing one day doesn't break a habit. Starting again does."

### HabitCoach chat head (frontend)
Grove powers a Messenger-style floating chat head in the Habits tab:
- **FAB:** Circular 🌿 button, bottom-left of habits content area
- **DM bubble:** Slides in 1s after habits load with an AI-generated nudge from `GET /grove/nudge`
- **Cache:** `sessionStorage` with key `grove_nudge_{userId}_{date}` — 60-minute TTL + date key
- **Chat panel:** Glassmorphism (rgba 0.72 + blur 18px). Opening message = DM bubble content (always in sync)
- **Routing:** Uses `agentOverride: "habit"` — bypasses Orchestrator
- **Conversation history:** Sends real `conversationHistory` built from `messages` state on every turn — Grove maintains full context across the multi-turn creation flow

### GET /grove/nudge
Non-streaming GPT-4o call (temp=0.85 for variation). Fetches user's habits + memory context, generates a warm proactive message. Returns `{ nudge, date }`.

---

## Agent 6 — Lumen (Insights & Analytics Agent)

**File:** `backend/agents/insights_agent.py`  
**Prompt:** `backend/prompts/insights.py`

### Role
Insights or Analytics Agent from problem statement. Pattern surfacing via RAG over journal history.

### Trigger keywords
`patterns`, `insights`, `trend`, `what do you see`, `how have I been`, `last week`, `looking back`, `analysis`

### RAG pipeline (runs before constructing agent)
1. User question is converted to a 1536-dimension embedding (`text-embedding-3-small-1`)
2. Azure AI Search runs hybrid vector + keyword search over `journal-index`, filtered by `userId`
3. Top 5 semantically relevant journal entries are retrieved
4. Their content is formatted and injected as `{journalContext}` into Lumen's system prompt
5. `{memoryContext}` from the Memory Agent is also injected

This is why `insights_agent.get_agent()` is `async def` — it must `await` the AI Search call before the agent can be constructed. All other specialist factory functions are synchronous.

### Behaviour
- Non-clinical pattern surfacing
- Emotional arc narration ("Your mood shifted noticeably around April 22...")
- References specific entries via the RAG context
- Never prescriptive — "I noticed..." not "You should..."

---

## Memory Context Template

The `{memoryContext}` block injected into every specialist system prompt:

```
== User Context ==
Name: {display_name}
Current mood: {current_mood} | Urgency: {urgency} | Time: {time_of_day}

Key facts about this user:
{facts_block}

Week summary: {week_summary}

Preferences:
- Preferred tone: {preferred_tone}
- Best journaling time: {best_journaling_time}
- Responds well to: {responds_well_to}
- Avoids: {avoids}

Recurring themes: {recurring_themes}
Breakthroughs: {breakthroughs}
== End User Context ==
```

Context is capped at ~800 tokens — never let memory crowd out the conversation.

---

## Cosmos DB Schema — `user_memory`

```json
{
  "id": "demo-user-001",
  "userId": "demo-user-001",
  "facts": [
    {
      "content": "Experiences anxiety before high-stakes presentations",
      "source": "conversation",
      "importance": 0.85,
      "createdAt": "2026-04-28T10:00:00Z",
      "lastReferencedAt": "2026-05-01T09:00:00Z"
    }
  ],
  "weekSummary": "This week, they maintained a 5-day meditation streak...",
  "weekSummaryUpdatedAt": "2026-05-01T08:00:00Z",
  "learnedPreferences": {
    "preferredTone": "warm",
    "bestJournalingTime": "evening",
    "respondsWellTo": ["grounding exercises", "open-ended questions"],
    "avoids": ["direct advice", "clinical framing"]
  },
  "recurringThemes": ["work stress", "manager conflict", "phone-free mornings"],
  "breakthroughs": ["Phone-free morning routine started April 22"],
  "updatedAt": "2026-05-02T06:00:00Z"
}
```
