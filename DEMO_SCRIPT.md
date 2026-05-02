# MindFlow Demo Script
## Hackathon Presentation — 5-Minute Walkthrough

> **Setup checklist before presenting:**
> - [ ] `backend/.env` all values set
> - [ ] `seed/seed.py` ran successfully (14 journal entries, 5 habits, 14 mood logs)
> - [ ] FastAPI running: `python -m backend.main` (port 8000)
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

> *"That mood score just traveled from this button → FastAPI → Azure Functions → Cosmos DB. And it's already shaping how the AI will talk to me today."*

**Action:** Switch to the Insights tab — point to the Weekly Reflection card at the top, then the sparkline.

> *"At the top — a weekly reflection. The Memory Agent read my last 10 journal entries and wrote this 2–3 sentence narrative. It's not generic — it references the specific breakthrough I had about phone-free mornings. Below that: 14 days of emotional data, visualized. Average score, dominant mood, and a week-over-week trend — am I improving?"*

---

## Minute 2 — Mindfulness Session with Sage (75 seconds)

**Action:** Switch to Chat tab. Type:
```
I've been feeling really anxious about a big presentation tomorrow
```

**What to narrate while streaming:**
> *"Watch the badge — that's the Orchestrator. In under 300ms it classified this as a mindfulness request and handed it to Sage, our mindfulness coach. And notice — I didn't tell it to do that. The system routed it automatically."*

> *"Sage knows I've been anxious before. That's the Memory Agent — it reads my conversation history and injects it into Sage's instructions before the response starts. So Sage isn't starting from zero."*

**Wait for response, then:**
> *"This is a real grounding exercise, calibrated to high urgency. Not a generic tip — a specific intervention for anxiety before a high-stakes event."*

---

## Minute 3 — Journal Entry with River (75 seconds)

**Action:** In Chat tab, type:
```
I want to journal about how I'm feeling. I've been stressed about work lately and I notice I'm snapping at people I care about.
```

**What to narrate while streaming:**
> *"The Orchestrator now classifies this as journaling — badge switches to River. River is a reflective companion, not an advice-giver."*

**Wait for response, then:**
> *"River just did something invisible. At the end of its response, it appended a structured data block — mood, sentiment, themes, summary. The streaming parser intercepted that block, stripped it from what you see, and saved a structured journal entry to Cosmos DB. In the background. Without any lag."*

**Action:** Switch to Insights tab.
> *"That entry will show up the next time Lumen searches our journal history."*

---

## Minute 4 — Lumen Surfaces Patterns (45 seconds)

**Action:** Switch to Chat tab. Type:
```
What patterns do you see across my journal entries?
```

**What to narrate while streaming:**
> *"Lumen is different from the other agents. Before it even starts responding, it runs a hybrid semantic search over all my journal entries in Azure AI Search — finding the most relevant ones for this question. That's RAG — Retrieval-Augmented Generation. Lumen literally re-reads my history before speaking."*

**Wait for response, then:**
> *"This is what makes it feel like the system actually knows me. It does — because it just looked it up."*

---

## Minute 5 — Habit Tracking with Grove (30 seconds)

**Action:** Switch to Habits tab.
> *"Five habits, each with a reason behind it — the WHY. Grove coached me to define that when I created each one. That WHY is stored in memory."*

**Action:** Tap a habit check button to log it.
> *"Streak updated, logged to Cosmos via Azure Functions. And if I'd missed yesterday? Grove wouldn't guilt me — it would ask: 'What would a 5-minute version look like?'"*

---

## Closing (15 seconds)

> *"Four agents. One conversation. Your history remembered across every session. MindFlow — supportive, not judgmental. Personalized, not generic. Built on Azure AI Foundry, Semantic Kernel, Cosmos DB, AI Search, and Azure Functions."*

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
