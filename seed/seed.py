"""
MindFlow Seed Script (Python)
──────────────────────────────────────────────────────────────────────────────
SELF-CONTAINED — uses only azure-cosmos and uuid. No backend imports.
Run: python seed/seed.py

Creates for DEMO_USER_ID=demo-user-001:
  - 1 user document
  - 14 journal entries (hackathon build arc — 2 weeks of Jen building MindFlow)
  - 5 habits with 7–14 days of real logs
  - 14 mood logs matching the hackathon arc
  - 1 user_memory document with 5 pre-populated facts

NOTE: Embeddings are NOT generated here — bulk index into AI Search happens
using bulk_index.py after the backend is running.
"""

import os
import sys

# Windows terminals default to cp1252 — force UTF-8 so emoji prints correctly
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
import uuid
from datetime import datetime, timedelta, timezone
from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

_env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
load_dotenv(dotenv_path=_env_path)

ENDPOINT = os.getenv("COSMOS_ENDPOINT")
KEY = os.getenv("COSMOS_KEY")
DB_NAME = os.getenv("COSMOS_DB_NAME", "mindflow")
USER_ID = os.getenv("DEMO_USER_ID", "demo-user-001")

if not ENDPOINT or not KEY:
    print("[ERROR] COSMOS_ENDPOINT and COSMOS_KEY must be set in backend/.env")
    print(f"[DEBUG] Looking for .env at: {_env_path}")
    sys.exit(1)


# ── Helpers ───────────────────────────────────────────────

def days_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()

def date_str_days_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=n)).strftime("%Y-%m-%d")

def det_id(collection: str, key: str) -> str:
    """Deterministic UUID — same inputs always produce the same ID.
    Prevents duplicate documents when seed.py is re-run.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{USER_ID}:{collection}:{key}"))


# ── Seed Data ──────────────────────────────────────────────
# Emotional arc: hackathon build stress peaks Days 13–11 (project kickoff + scope panic),
# momentum builds Days 10–7 as the system comes together, breakthrough Day 4 when
# the full streaming pipeline works end-to-end, final QA grind Days 3–1,
# confident and demo-ready Day 0.
# Lumen's RAG must return something specific — generic text kills Minute 4.

JOURNAL_ENTRIES = [
    {
        "id": det_id("journal", "day-13"), "userId": USER_ID,
        "content": "It makes sense that your mind is spinning — a big goal with a short timeline can feel like too much all at once. I hear both the excitement and the fear in what you’re holding. When you wrote that simple plan and felt steadier for a moment, what part of the plan helped you breathe again?",
        "moodAtEntry": "anxious", "sentiment": "negative",
        "themes": ["hackathon kickoff", "scope anxiety", "planning", "overwhelm"],
        "summary": "I felt both excited and terrified reading the hackathon requirements — the scope felt huge and I wasn't sure where to start.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(13),
    },
    {
        "id": det_id("journal", "day-12"), "userId": USER_ID,
        "content": "That early wall sounds discouraging — especially when you can feel panic starting to build. What stands out is that you didn’t force it; you adapted, and momentum returned. What did that “tiny win” give you emotionally — relief, confidence, or something else?",
        "moodAtEntry": "anxious", "sentiment": "neutral",
        "themes": ["setbacks", "adaptability", "problem solving", "first win"],
        "summary": "I hit an early setback, but changing my plan instead of forcing it helped me move forward — and the first clean commit felt like a real win.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(12),
    },
    {
        "id": det_id("journal", "day-11"), "userId": USER_ID,
        "content": "You built something that makes the whole experience feel personal — that’s not a small thing. I hear the pride and the clarity it brought you, even with the deadline humming in the background. If the deadline had a voice right now, what would it be saying — and what would you want to say back?",
        "moodAtEntry": "okay", "sentiment": "neutral",
        "themes": ["personalization", "momentum", "time pressure", "building"],
        "summary": "I built the part that makes the assistant feel personal, which gave me momentum — but the deadline still feels loud.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(11),
    },
    {
        "id": det_id("journal", "day-10"), "userId": USER_ID,
        "content": "It sounds like today was a turning point — like the project shifted from “idea” to “something alive.” I hear how meaningful it was to feel supported in a moment of anxiety, and then guided into reflection instead of being left alone with it. What do you want to protect about this feeling as the pressure ramps up again?",
        "moodAtEntry": "good", "sentiment": "positive",
        "themes": ["momentum", "mindfulness", "reflection", "product feel"],
        "summary": "The app felt real for the first time today — it helped me calm down and reflect in a way that felt genuinely useful.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(10),
    },
    {
        "id": det_id("journal", "day-9"), "userId": USER_ID,
        "content": "That “almost rage-quit” moment sounds real — like you were right at the edge of your patience. And then that deep-exhale relief when it finally clicked… that’s your nervous system coming back online. When you think about what helped you push through, was it stubbornness, hope, or something else?",
        "moodAtEntry": "good", "sentiment": "positive",
        "themes": ["habits", "frustration", "debugging", "relief"],
        "summary": "Habits are working — a frustrating progress bug almost broke me, but fixing it brought real relief and restored my confidence.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(9),
    },
    {
        "id": det_id("journal", "day-8"), "userId": USER_ID,
        "content": "I hear how draining those “small failures” can be — especially when they stack up and start to make you question the whole effort. And I also hear the moment it turned: when something you’d written before was held gently and connected to the present. What did that moment make you feel — seen, understood, relieved?",
        "moodAtEntry": "okay", "sentiment": "positive",
        "themes": ["insights", "patterns", "persistence", "breakthrough moment"],
        "summary": "After a long day of small failures, the assistant finally connected a current feeling to something I'd written before — and it felt like a companion, not just a tool.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(8),
    },
    {
        "id": det_id("journal", "day-7"), "userId": USER_ID,
        "content": "This sounds like one of those quiet-but-important days — the kind that doesn’t look impressive from the outside, but changes how safe the experience feels. I hear your care for future-you and for the person who will rely on what you built. As you notice that steadier feeling, where do you feel it — in your chest, your shoulders, your breath?",
        "moodAtEntry": "okay", "sentiment": "neutral",
        "themes": ["reliability", "maintenance", "patience", "steady progress"],
        "summary": "I did the unglamorous reliability work today — nothing flashy, but it made everything feel steadier.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(7),
    },
    {
        "id": det_id("journal", "day-6"), "userId": USER_ID,
        "content": "There’s a grounded kind of confidence that comes from moving slowly and checking the basics — not rushing past them. I hear how your calm grew as the surprises disappeared, and how that turned into trust. What does it feel like to trust what you built, even just a little more than yesterday?",
        "moodAtEntry": "good", "sentiment": "positive",
        "themes": ["quality", "trust", "stability", "small fixes"],
        "summary": "I spent the day testing like a real user would, and it made me trust the app more.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(6),
    },
    {
        "id": det_id("journal", "day-5"), "userId": USER_ID,
        "content": "It sounds like you’re creating a space that feels inviting — not clinical, not performative, just human. I hear how much “gentle” matters to you: the journal as a story, and saving an entry as something that flows naturally. When you imagine coming back to this space on a hard day, what would you hope it gives you?",
        "moodAtEntry": "good", "sentiment": "positive",
        "themes": ["journaling", "clarity", "gentle UX", "progress"],
        "summary": "The journal now feels like a place I'd return to, and saving an entry feels gentler and more natural.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(5),
    },
    {
        "id": det_id("journal", "day-4"), "userId": USER_ID,
        "content": "I can feel your delight here — that moment where it stops being “a feature” and starts feeling like support. What stands out is the care: a nudge that matches your real day, not a generic push. As you sit with that pride, what do you think you proved to yourself by getting this working?",
        "moodAtEntry": "great", "sentiment": "positive",
        "themes": ["habit coaching", "support", "delight", "breakthrough"],
        "summary": "The habit coach now feels present and supportive — it nudges me in a way that matches my real day, and I'm proud of how it feels.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(4),
    },
    {
        "id": det_id("journal", "day-3"), "userId": USER_ID,
        "content": "You’re naming something really important: being recorded isn’t the same as being understood. I hear how much it mattered to read a reflection that felt like “I see you,” especially after a hard stretch. When you picture someone reading that weekly reflection, what do you hope it changes for them in that moment?",
        "moodAtEntry": "great", "sentiment": "positive",
        "themes": ["reflection", "meaning", "weekly summary", "care"],
        "summary": "I added a weekly reflection that turns the past week into a gentle story — it made the app feel more human.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(3),
    },
    {
        "id": det_id("journal", "day-2"), "userId": USER_ID,
        "content": "This sounds like care work — the kind that’s easy to overlook, but changes how it feels to step into the experience. I hear the relief of “closing open tabs,” of making things clearer and kinder for whoever comes next (including you). What feels most finished inside you right now — and what still feels slightly undone?",
        "moodAtEntry": "good", "sentiment": "positive",
        "themes": ["closing loops", "clarity", "prep", "care"],
        "summary": "I spent the day closing loops and making the experience clearer — it felt like mental decluttering.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(2),
    },
    {
        "id": det_id("journal", "day-1"), "userId": USER_ID,
        "content": "I hear a mix of nerves and steadiness — like you’re rehearsing, but you’re also appreciating what you made. What stands out is your intention: meeting anxiety with calm instead of hype, and reflecting patterns with care. As you go into tomorrow, what would “enough” look like for you, regardless of the outcome?",
        "moodAtEntry": "good", "sentiment": "positive",
        "themes": ["demo prep", "readiness", "pride", "nerves"],
        "summary": "Demo prep complete — walked through the script twice and felt genuinely proud of what was built, regardless of the result.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(1),
    },
    {
        "id": det_id("journal", "day-0"), "userId": USER_ID,
        "content": "It sounds like you’re standing right at the edge of something you worked hard for — nervous, and also ready. I hear the values you want the experience to carry: supportive, not judgmental; gentle, not pressuring. Before you step into the demo, what would help you feel one notch more grounded right now?",
        "moodAtEntry": "great", "sentiment": "positive",
        "themes": ["demo day", "launch", "pride", "hackathon completion"],
        "summary": "Demo day — the system is live, the script is ready, and I'm proud of every line of code.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(0),
    },
]

MOOD_LOGS = [
    {"id": det_id("mood", "day-13"), "userId": USER_ID, "mood": "anxious", "score": 3, "context": "evening_checkin",  "note": "The scope felt huge and my mind kept racing",              "timestamp": days_ago(13)},
    {"id": det_id("mood", "day-12"), "userId": USER_ID, "mood": "anxious", "score": 4, "context": "morning_checkin", "note": "Early setback, but I chose to adapt",                       "timestamp": days_ago(12)},
    {"id": det_id("mood", "day-11"), "userId": USER_ID, "mood": "okay",    "score": 5, "context": "evening_checkin",  "note": "Momentum is back, but the deadline is loud",              "timestamp": days_ago(11)},
    {"id": det_id("mood", "day-10"), "userId": USER_ID, "mood": "good",    "score": 7, "context": "morning_checkin", "note": "The app helped me breathe and reflect — it felt real",     "timestamp": days_ago(10)},
    {"id": det_id("mood", "day-9"),  "userId": USER_ID, "mood": "good",    "score": 7, "context": "evening_checkin",  "note": "Fixed a frustrating habits issue — big relief",           "timestamp": days_ago(9)},
    {"id": det_id("mood", "day-8"),  "userId": USER_ID, "mood": "okay",    "score": 6, "context": "morning_checkin", "note": "A long day, but a meaningful breakthrough",               "timestamp": days_ago(8)},
    {"id": det_id("mood", "day-7"),  "userId": USER_ID, "mood": "okay",    "score": 5, "context": "evening_checkin",  "note": "Unsexy reliability work — tired but steadier",             "timestamp": days_ago(7)},
    {"id": det_id("mood", "day-6"),  "userId": USER_ID, "mood": "good",    "score": 8, "context": "morning_checkin", "note": "Testing made me trust what I built",                        "timestamp": days_ago(6)},
    {"id": det_id("mood", "day-5"),  "userId": USER_ID, "mood": "good",    "score": 7, "context": "evening_checkin",  "note": "The journal space feels calmer and clearer",               "timestamp": days_ago(5)},
    {"id": det_id("mood", "day-4"),  "userId": USER_ID, "mood": "great",   "score": 9, "context": "morning_checkin", "note": "A delightful coaching moment finally landed",              "timestamp": days_ago(4)},
    {"id": det_id("mood", "day-3"),  "userId": USER_ID, "mood": "great",   "score": 9, "context": "morning_checkin", "note": "Weekly reflection made the app feel human",                "timestamp": days_ago(3)},
    {"id": det_id("mood", "day-2"),  "userId": USER_ID, "mood": "good",    "score": 8, "context": "evening_checkin",  "note": "Closing loops and making the experience clearer",          "timestamp": days_ago(2)},
    {"id": det_id("mood", "day-1"),  "userId": USER_ID, "mood": "good",    "score": 8, "context": "evening_checkin",  "note": "Nervous, but proud — rehearsal helped",                    "timestamp": days_ago(1)},
    {"id": det_id("mood", "day-0"),  "userId": USER_ID, "mood": "great",   "score": 9, "context": "morning_checkin", "note": "Demo day — nervous and ready",                              "timestamp": days_ago(0)},
]

HABITS = [
    {
        "id": det_id("habit", "daily-build-session"), "userId": USER_ID,
        "name": "Daily build session",
        "why": "Consistent daily progress compounds — even 2 hours beats one 14-hour sprint",
        "frequency": "daily", "targetTime": "09:00", "durationMins": 120,
        "logs": [date_str_days_ago(d) for d in [0,1,2,3,4,5,6,7,8,9,10,11,12,13]],
        "currentStreak": 14, "longestStreak": 14, "active": True,
    },
    {
        "id": det_id("habit", "evening-journal"), "userId": USER_ID,
        "name": "Evening journal",
        "why": "Journaling what I built (and what blocked me) clears my head and helps me problem-solve overnight",
        "frequency": "daily", "targetTime": "21:00", "durationMins": 15,
        "logs": [date_str_days_ago(d) for d in [0,1,2,3,4,5,6,7,8,9]],
        "currentStreak": 10, "longestStreak": 10, "active": True,
    },
    {
        "id": det_id("habit", "morning-meditation"), "userId": USER_ID,
        "name": "Morning meditation",
        "why": "Starting with 10 minutes of quiet means I make better technical decisions all day",
        "frequency": "daily", "targetTime": "07:30", "durationMins": 10,
        "logs": [date_str_days_ago(d) for d in [0,1,2,3,4,6,7,8]],
        "currentStreak": 5, "longestStreak": 8, "active": True,
    },
    {
        "id": det_id("habit", "no-doom-scroll-before-code"), "userId": USER_ID,
        "name": "No phone before first commit",
        "why": "Opening social media before coding fragments my focus before I even start",
        "frequency": "daily", "targetTime": "09:00", "durationMins": 0,
        "logs": [date_str_days_ago(d) for d in [0,1,2,3,4,5]],
        "currentStreak": 6, "longestStreak": 6, "active": True,
    },
    {
        "id": det_id("habit", "afternoon-walk"), "userId": USER_ID,
        "name": "Afternoon walk (no headphones)",
        "why": "When I'm stuck on a bug, a 20-minute walk without input almost always surfaces the answer",
        "frequency": "daily", "targetTime": "15:00", "durationMins": 20,
        "logs": [date_str_days_ago(d) for d in [0,2,4,6,8,10]],
        "currentStreak": 1, "longestStreak": 3, "active": True,
    },
]

USER_MEMORY = {
    "id": USER_ID, "userId": USER_ID,
    "facts": [
        {
            "content": "Jen is building MindFlow for a hackathon — one place to check in, journal, practice mindfulness, and keep gentle track of habits.",
            "source": "journal_entry", "importance": 0.98,
            "createdAt": days_ago(13), "lastReferencedAt": days_ago(0),
        },
        {
            "content": "Jen's biggest boost comes when the app feels genuinely supportive — especially when it offers a small, timely nudge that matches her real day.",
            "source": "journal_entry", "importance": 0.92,
            "createdAt": days_ago(10), "lastReferencedAt": days_ago(4),
        },
        {
            "content": "Jen responds well to reframing setbacks as progress — naming small wins helps her keep going when pressure is high.",
            "source": "journal_entry", "importance": 0.88,
            "createdAt": days_ago(7), "lastReferencedAt": days_ago(3),
        },
        {
            "content": "User experiences a consistent mood dip when blocked on an invisible bug, but recovers quickly once the root cause is understood — the pattern is frustration → investigation → clarity → relief.",
            "source": "mood_log", "importance": 0.85,
            "createdAt": days_ago(8), "lastReferencedAt": days_ago(5),
        },
        {
            "content": "Afternoon walks without headphones reliably reset Jen's nervous system and help her find clarity when she's stuck.",
            "source": "journal_entry", "importance": 0.82,
            "createdAt": days_ago(7), "lastReferencedAt": days_ago(1),
        },
    ],
    "weekSummary": (
        "This week Jen moved from overwhelm into steadier momentum. "
        "She kept showing up for her habits, built a calmer place to reflect, and added a weekly reflection that made the experience feel more human. "
        "Even with nerves in the final stretch, she ends the week proud — and ready for demo day."
    ),
    "weekSummaryUpdatedAt": days_ago(0),
    "learnedPreferences": {
        "preferredTone": "warm",
        "bestJournalingTime": "evening",
        "respondsWellTo": ["reframing setbacks as growth", "acknowledging streaks", "gentle, specific reflections"],
        "avoids": ["generic encouragement", "long bullet lists", "pressure or guilt"],
    },
    "recurringThemes": ["building under pressure", "mindfulness", "reflection", "habits", "momentum and flow"],
    "breakthroughs": [
        "The first time the app helped her calm down in a high-pressure moment",
        "Seeing a reflection connect a present feeling to something she'd written earlier",
        "A small, timely habit-coach nudge that felt personal instead of generic",
        "Learning that a walk without headphones beats forcing focus when stuck",
    ],
    "updatedAt": days_ago(0),
}

USER = {
    "id": USER_ID, "userId": USER_ID,
    "email": "demo@mindflow.app",
    "displayName": "Jen",
    "timezone": "Asia/Manila",
    "preferences": {"morningCheckIn": True, "tone": "warm"},
    "createdAt": days_ago(14),
}


# ── Main ──────────────────────────────────────────────────

def seed():
    print("🌱 MindFlow Seed Script")
    print(f"   Endpoint: {ENDPOINT}")
    print(f"   Database: {DB_NAME}")
    print(f"   User ID:  {USER_ID}\n")

    client = CosmosClient(ENDPOINT, KEY)
    db = client.create_database_if_not_exists(DB_NAME)

    collections = ["users", "journal_entries", "habits", "mood_logs", "user_memory"]
    for name in collections:
        db.create_container_if_not_exists(
            id=name,
            partition_key=PartitionKey(path="/userId"),
        )
        print(f"  ✓ Container ready: {name}")

    db.get_container_client("users").upsert_item(USER)
    print(f"\n  ✓ User upserted: {USER['displayName']} ({USER_ID})")

    for entry in JOURNAL_ENTRIES:
        db.get_container_client("journal_entries").upsert_item(entry)
    print(f"  ✓ Journal entries upserted: {len(JOURNAL_ENTRIES)}")

    for habit in HABITS:
        db.get_container_client("habits").upsert_item(habit)
    print(f"  ✓ Habits upserted: {len(HABITS)}")

    for log in MOOD_LOGS:
        db.get_container_client("mood_logs").upsert_item(log)
    print(f"  ✓ Mood logs upserted: {len(MOOD_LOGS)}")

    db.get_container_client("user_memory").upsert_item(USER_MEMORY)
    print(f"  ✓ User memory upserted ({len(USER_MEMORY['facts'])} facts)")

    print("\n✅ Seed complete. Demo account is ready.")
    print("\n⚠️  NEXT: Run python seed/bulk_index.py to embed and index journal entries into Azure AI Search.")


if __name__ == "__main__":
    seed()
