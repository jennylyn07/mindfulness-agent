# MindFlow Demo Script
## Hackathon Presentation — 5-Minute Walkthrough

## Apply the demo data (new seed)

Use this when you want to refresh the demo account and make sure the Insights tab has a weekly reflection.

⚠️ To apply: Run python seed/cleanup.py first to purge old data, then python seed/seed.py, then python seed/bulk_index.py.

1. **(Optional) Clear old demo data**
   Run:
   - `python seed/cleanup.py`

2. **Seed the new story + habits + moods**
   Run:
   - `python seed/seed.py`

3. **Start the backend**
   Run (from repo root):
   - `python -m uvicorn backend.main:app --reload --port 8000`

4. **Index journal entries for Insights (Lumen)**
   Run (in a new terminal, after the backend is running):
   - `python seed/bulk_index.py`

5. **Start the frontend**
   Run (in `frontend/`):
   - `npm run dev`

6. **Refresh the app**
   - Open `http://localhost:3000`
   - Go to the **Insights** tab and refresh once

> **Setup checklist before presenting:**
> - [ ] `backend/.env` all values set
> - [ ] `seed/seed.py` ran successfully (14 journal entries, 5 habits, 14 mood logs)
> - [ ] `seed/bulk_index.py` ran successfully (AI Search indexed)
> - [ ] FastAPI running: `python -m uvicorn backend.main:app --reload --port 8000` (from repo root)
> - [ ] Next.js running: `npm run dev` in `frontend/` (port 3000)
> - [ ] Browser open to `http://localhost:3000`
> - [ ] Browser DevTools closed
> - [ ] Font loaded (refresh once before presenting)

---

## Minute 0 — Opening Hook (30 seconds)

> *"Most wellness apps are fragmented — one for meditation, one for journaling, one for habits. None of them talk to each other, and none of them remember who you are. MindFlow is different. It's a single AI system with four specialized agents that coordinate in real time — each one knowing your history, your patterns, and your emotional state."*

**Action:** Show the app home screen. Point to the three tabs.

---

## Minute 1 — Morning Check-In (45 seconds)

**Script:**
> *"When you open MindFlow in the morning, the first thing you see is your mood check-in. One tap — no forms, no menus."*

**Action:** Tap the **😐 okay** emoji in the morning banner.

> *"That one tap sets the tone for the rest of the experience. MindFlow doesn't treat this like a form — it treats it like a moment of honesty."*

**Action:** Switch to the Insights tab — point to the Weekly Reflection card at the top, then the sparkline.

> *"At the top — a weekly reflection. It turns the past few days into a short, gentle story — not charts for the sake of charts. Below that is a simple mood timeline, so you can see the arc of your week at a glance."*

---

## Minute 2 — Mindfulness Session with Sage (75 seconds)

**Action:** Switch to Chat tab. Type:
```
I've been feeling really anxious about a big presentation tomorrow
```

**What to narrate while streaming:**
> *"Notice the badge — MindFlow automatically routes this to Sage, our mindfulness coach."*

> *"Sage doesn't jump into advice. It meets the emotion first, then guides a short practice you can actually do in under a minute."*

**Wait for response, then:**
> *"This is a real grounding exercise — not a motivational quote. The goal is to help you come back to your body and feel a little steadier."*

---

## Minute 3 — Journal Entry with River (75 seconds)

**Action:** In Chat tab, type:
```
I want to journal about how I'm feeling right now. I've been heads-down building for two weeks and I'm starting to feel the final-stretch pressure.
```

**What to narrate while streaming:**
> *"The Orchestrator now classifies this as journaling — badge switches to River. River is a reflective companion, not an advice-giver."*

**Wait for response, then:**
> *"River helps you slow down and find the words. And when you choose to save an entry, MindFlow quietly captures the mood and themes so you can reflect on patterns later — without making you fill out extra fields."*

**Action:** Switch to Insights tab.
> *"That entry will show up the next time Lumen searches our journal history."*

---

## Minute 4 — Lumen Surfaces Patterns (45 seconds)

**Action:** Switch to Chat tab. Type:
```
What patterns do you see across my journal entries?
```

**What to narrate while streaming:**
> *"Lumen is the insights companion. Before answering, it looks back at what you've actually written recently — so it can respond with context instead of guesses."*

**Wait for response, then:**
> *"Notice what Lumen does here — it stays specific. It reflects back themes that show up across multiple entries, and it asks a gentle question that helps you decide what you need next."*

---

## Minute 5 — Habit Tracking with Grove (30 seconds)

**Action:** Switch to Habits tab. Point to the 14-day daily build streak.
> *"Five habits, each with a WHY. The daily build session has a 14-day streak — that's consistency. And the afternoon walk has the lowest streak — that's also real life. Grove doesn't guilt you — it helps you reset gently."*

**Action:** Tap a habit check button to log it.
> *"When you miss a day, Grove doesn't punish you. It helps you make it smaller: 'What would a 5-minute version look like?'"*

---

## Closing (15 seconds)

> *"Four agents. One experience. MindFlow helps you check in, calm down, reflect, and keep showing up — in a way that feels supportive, not judgmental."*

---

## Fallback Lines (if something goes wrong)

| Scenario | Line |
|---|---|
| Stream takes >5s | *"The model is generating — this is real inference, not a mock."* |
| Habit tab is empty | *"Habits are seeded — if this is empty, we'll check the Functions connection."* |
| Badge doesn't appear | *"The agent badge appears as the first token — the Orchestrator has already classified and routed."* |
| Cosmos error | *"We can demo with the seed data already in Cosmos — let me pull up the journal tab."* |

---

## Key Tech Talking Points

| What judges might ask | Answer |
|---|---|
| "Why FastAPI instead of Next.js API routes?" | Streaming, background tasks, and Python's async ecosystem. Next.js API routes can't hold a streaming connection while running asyncio background tasks reliably. |
| "Why Semantic Kernel?" | It's Microsoft's official agent framework — same SDK used in Azure AI Agent Service. The `ChatCompletionAgent` abstraction works identically with Azure OpenAI. |
| "How is this different from just calling GPT?" | Four specialized agents, each with different system prompts, memory injection, and capabilities. The Orchestrator routes invisibly. The Memory Agent maintains facts across sessions. RAG gives Lumen real history. |
| "What's the Memory Agent?" | It reads the conversation, extracts factual statements about the user (name, goals, patterns), scores them for confidence, and saves them to Cosmos. Every agent reads this before responding. |
| "How does the mood affect the AI?" | Orchestrator classifies mood and urgency. These are passed to the Memory Agent's READ, which assembles context with emotional framing. Sage's prompt has explicit urgency-tiered responses (high/medium/low). |
