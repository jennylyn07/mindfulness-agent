# MindFlow Demo Script
## Hackathon Presentation — 5-Minute Walkthrough

---

## Pre-Demo Setup

> ⚠️ Run these in order before presenting. Both servers must be running.

**1. (Optional) Reset demo data**
```bash
python seed/cleanup.py
python seed/seed.py
python seed/bulk_index.py
```

**2. Start backend** (from repo root, `.venv` active)
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

**3. Start Azure Functions** (from `azure-functions/`, separate terminal)
```bash
func start
```

**4. Start frontend** (from `frontend/`)
```bash
npm run dev
```

**5. Open browser to** `http://localhost:3000` — refresh once to load fonts.

> **Pre-flight checklist:**
> - [ ] `backend/.env` — all Azure credentials set
> - [ ] `seed/seed.py` ran successfully (14 journal entries, 5 habits, 14 mood logs)
> - [ ] `seed/bulk_index.py` ran successfully (AI Search indexed)
> - [ ] FastAPI running on port 8000
> - [ ] Azure Functions running on port 7071
> - [ ] Next.js running on port 3000
> - [ ] Browser DevTools **closed**
> - [ ] Font loaded (refresh once before presenting)
> - [ ] Insights tab visited once (triggers weekSummary generation)

---

## Minute 0 — Opening Hook (30 seconds)

> *"Most wellness apps are fragmented — one for meditation, one for journaling, one for habits. None of them talk to each other, and none of them remember who you are. MindFlow is different. It's a single AI system with four specialized agents that coordinate in real time — each one knowing your history, your patterns, and your emotional state."*

**Action:** Show the app home screen. Point to the four tabs.

---

## Minute 1 — Morning Check-In + Low-Mood Trigger (45 seconds)

> *"When you open MindFlow in the morning, the first thing you see is a mood check-in. One tap — no forms, no menus."*

**Action:** Tap **😟 rough** (or **😰 anxious**) in the morning banner.

> *"Watch what happens — MindFlow doesn't just log that. It recognises you need support right now and automatically opens a conversation with Sage."*

**Observe:** The app switches to Chat tab and sends a Sage-bound message automatically. A `routing…` badge pulses while the Orchestrator classifies.

> *"The routing badge you see is the Orchestrator — a dedicated classification agent that runs in under 200ms and decides which specialist you need, before a single word of the response appears."*

**Action:** After Sage responds, switch to the **Insights** tab — point to the Weekly Reflection card, then the sparkline.

> *"The weekly reflection at the top turns journal entries into a short, warm narrative — not charts for their own sake. The sparkline below shows the emotional arc of your week at a glance."*

---

## Minute 2 — Journaling with River (60 seconds)

**Action:** Switch to **Chat** tab. Type:
```
I want to journal about how I'm feeling right now. I've been heads-down building for two weeks and I'm starting to feel the final-stretch pressure.
```

**Narrate while streaming:**
> *"Badge switches to River — the reflective journaling companion. River doesn't give advice. It helps you slow down and find the words."*

**Wait for response, then:**
> *"River quietly captures mood, themes, and a summary behind the scenes — no extra fields to fill in."*

**Action:** Switch to the **Journal** tab immediately.

> *"The entry appears straight away — no browser refresh needed. The tab re-fetches as soon as you land on it."*

**Action:** Point to the mood pill and theme chips on the card. Expand "Read saved reflection."

> *"The themes are AI-extracted. The expandable section shows River's full response. You can also tap ✏️ to edit the summary — any edit syncs back to the Memory Agent so future responses stay accurate."*

---

## Minute 3 — Lumen Surfaces Patterns via RAG (45 seconds)

**Action:** Switch to **Insights** tab. Click **"Ask Lumen now →"** button on the Lumen card.

> *"This button switches back to Chat and sends the question automatically — no typing needed."*

**Observe:** Tab switches to Chat, message fires, Lumen badge appears.

**Narrate while streaming:**
> *"Lumen runs a hybrid search across all journal entries before it responds — semantic vector search plus keyword matching. It's not guessing from training data; it's reading what you actually wrote."*

**Wait for response:**
> *"Lumen stays specific. It reflects back themes from your real entries, not generic wellness advice."*

---

## Minute 4 — Habit Creation with Grove (60 seconds)

**Action:** In Chat tab, type:
```
I want to add a new habit
```

**Narrate:**
> *"Badge switches to Grove — the habit coach. Grove doesn't just log a to-do. It asks for the WHY — because habits tied to meaning are the ones that stick."*

**Wait for Grove to ask:** *"What habit would you like to build?"*

**Type:**
```
I want to read 10 pages a day
```

**Wait for Grove to ask:** *"What's the reason behind this one?"*

**Type:**
```
I want to keep my mind sharp and carve out quiet time for myself
```

**Wait for confirmation:**
> *"Grove collects the name and the WHY, then silently writes the habit to the database. No form. No save button. The confirmation appears inline."*

**Action:** Switch to the **Habits** tab.

> *"The new habit is already there — the tab refreshes automatically. Five habits are seeded. Grove's coaching isn't just creation — tap the 🌿 button at the bottom left."*

**Action:** Open the **Grove FAB** (🌿 floating button). Point to the DM bubble.

> *"When the Habits tab loads, Grove generates a personalised nudge using your live habit data and memory context. Tap it to open the coaching panel."*

---

## Minute 5 — Closing + Habit Logging (30 seconds)

**Action:** Back on the Habits tab, tap the circle next to a habit to log it.

> *"Streak updates instantly. If you've already logged today, the card turns green. Miss a day — the chain breaks at midnight, automatically, by design."*

**Action:** Point to the streak numbers on each card.

> *"Each streak is recalculated live on every request — there's no caching that can drift. And the WHY is right there under the habit name, so you always remember why you started."*

**Closing:**
> *"Four agents. One experience. MindFlow helps you check in, calm down, reflect, and keep showing up — in a way that feels supportive, not clinical."*

---

## Fallback Lines

| Scenario | Line |
|---|---|
| Stream takes > 5s | *"The model is generating — this is real inference, not a pre-recorded mock."* |
| Routing flash doesn't appear | *"The Orchestrator has already classified — the badge you see is the result. It runs in under 200ms."* |
| Habits tab empty | *"Habits are seeded — if empty, the Azure Functions connection may need a moment. Let me show the journal instead."* |
| New habit doesn't appear | *"The habit is saved to Cosmos — the tab fetches on switch. One moment."* |
| Badge doesn't appear | *"The agent badge arrives as the first streaming token — the classification already happened before the first word."* |
| Grove FAB not visible | *"The Grove chat head appears on the Habits tab — let me switch over."* |
| Cosmos error | *"We can demo with the pre-seeded data — let me pull up the Insights tab."* |

---

## Key Tech Talking Points

| What judges might ask | Answer |
|---|---|
| "Why FastAPI instead of Next.js API routes?" | Streaming, background tasks (`asyncio.ensure_future`), and Python's async ecosystem. Next.js API routes can't hold a streaming connection while running async background saves reliably. |
| "Why Semantic Kernel?" | It's Microsoft's official agent framework — same SDK used in Azure AI Agent Service. `ChatCompletionAgent` works identically with Azure OpenAI. Swapping models requires one config change. |
| "How is this different from just calling GPT?" | Four specialised agents with different prompts, memory injection, and capabilities. The Orchestrator routes invisibly. The Memory Agent extracts and scores facts across sessions. RAG gives Lumen real history. |
| "What's the Memory Agent?" | Runs on every request — READ pass before the specialist (assembles context ≤800 tokens), WRITE pass after (extracts facts, scores importance ≥0.6, caps at 12, decays stale facts). |
| "How does mood affect the AI?" | Mood and urgency are classified by the Orchestrator and passed to the Memory READ. Sage has explicit urgency-tiered responses. Low mood (score ≤4) triggers an automatic Sage preset. |
| "Why does habit creation use a marker pattern instead of tool calls?" | The `[CREATE_HABIT]` block is intercepted in the streaming loop — same proven pattern as `[SAVE_ENTRY]`. No tool-use dependency, no extra LLM call, same async background write. |
| "How does the routing flash work?" | The first token of every streaming response is `[AGENT:name]`. The frontend shows a pulsing 'routing…' badge until that token arrives, then switches to the named agent badge. |
