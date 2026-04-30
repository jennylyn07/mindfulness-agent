"""
MindFlow Seed Script (Python)
──────────────────────────────────────────────────────────────────────────────
SELF-CONTAINED — uses only azure-cosmos and uuid. No backend imports.
Run: python seed/seed.py

Creates for DEMO_USER_ID=demo-user-001:
  - 1 user document
  - 14 journal entries (deliberate emotional arc — Minute 4 demo depends on this)
  - 5 habits with 7–14 days of real logs
  - 14 mood logs matching the journal arc
  - 1 user_memory document with 5 pre-populated facts

NOTE: Embeddings are NOT generated here — bulk index into AI Search happens
in Hour 7 using the running FastAPI backend's embed endpoint.
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
# Emotional arc: work stress peaks Days 13–11, Wednesday recovery pattern,
# breakthrough at Day 4 (phone-free mornings), sustained improvement Days 3–0.
# Lumen's RAG must return something specific — generic text kills Minute 4.

JOURNAL_ENTRIES = [
    {
        "id": det_id("journal", "day-13"), "userId": USER_ID,
        "content": "Today was brutal. My manager keeps moving the goalposts on the project scope and I feel like nothing I do is ever enough. I stayed late again and I'm exhausted. I don't know how much longer I can keep this pace up.",
        "moodAtEntry": "anxious", "sentiment": "negative",
        "themes": ["work stress", "manager conflict", "exhaustion"],
        "summary": "User felt overwhelmed by unclear expectations and an exhausting work pace.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(13),
    },
    {
        "id": det_id("journal", "day-12"), "userId": USER_ID,
        "content": "Another hard Monday. Woke up dreading the week already. The anxiety about the presentation my manager wants by Friday kept me up last night. I tried the box breathing thing this morning and it helped a little — maybe I'll try it again tonight.",
        "moodAtEntry": "anxious", "sentiment": "negative",
        "themes": ["work stress", "sleep issues", "breathing exercise"],
        "summary": "User struggled with anticipatory anxiety but noted breathing exercises helped slightly.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(12),
    },
    {
        "id": det_id("journal", "day-11"), "userId": USER_ID,
        "content": "I did the presentation. My manager barely acknowledged it and then immediately pointed out what was missing. I felt invisible. On the walk home I noticed I've been holding tension in my shoulders for weeks.",
        "moodAtEntry": "sad", "sentiment": "negative",
        "themes": ["manager conflict", "feeling invisible", "body awareness"],
        "summary": "User felt unseen after a presentation and became aware of physical tension from chronic stress.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(11),
    },
    {
        "id": det_id("journal", "day-10"), "userId": USER_ID,
        "content": "Wednesday is always better for some reason. Had a good conversation with a colleague about the manager situation — apparently others feel the same way. Did my morning meditation today, first time in a week.",
        "moodAtEntry": "okay", "sentiment": "neutral",
        "themes": ["work stress", "connection", "morning meditation"],
        "summary": "User found relief through peer connection and returned to morning meditation practice.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(10),
    },
    {
        "id": det_id("journal", "day-9"), "userId": USER_ID,
        "content": "Thursday felt lighter. I've noticed I'm almost always more anxious on Mondays and Tuesdays — by Wednesday something shifts. The meditation this morning was really grounding. Maybe there's something to this consistency thing.",
        "moodAtEntry": "good", "sentiment": "positive",
        "themes": ["mood patterns", "morning meditation", "consistency"],
        "summary": "User noticed a recurring mood pattern — higher anxiety early week, recovery mid-week — linked to meditation consistency.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(9),
    },
    {
        "id": det_id("journal", "day-8"), "userId": USER_ID,
        "content": "Long week but I made it. Manager situation is the same but I feel less reactive to it today. The ones where I don't look at my phone first thing are noticeably calmer. Need to test this properly.",
        "moodAtEntry": "good", "sentiment": "positive",
        "themes": ["manager conflict", "morning routine", "phone habits"],
        "summary": "User identified that phone-free mornings may correlate with a calmer emotional baseline.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(8),
    },
    {
        "id": det_id("journal", "day-7"), "userId": USER_ID,
        "content": "Weekend was restorative. Went for a walk without headphones and just let my mind wander. It felt strange at first but I noticed I wasn't thinking about work at all after about ten minutes.",
        "moodAtEntry": "good", "sentiment": "positive",
        "themes": ["rest", "nature", "mental space"],
        "summary": "User experienced mental relief through undistracted walking.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(7),
    },
    {
        "id": det_id("journal", "day-6"), "userId": USER_ID,
        "content": "Monday again. Smaller anxiety spike than usual — noticed it and did the box breathing before the stand-up meeting. It helped me stay calm when my manager criticized the timeline in front of the team.",
        "moodAtEntry": "anxious", "sentiment": "neutral",
        "themes": ["work stress", "breathing exercise", "manager conflict"],
        "summary": "User proactively used breathing technique before a stressful meeting with measurable effect.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(6),
    },
    {
        "id": det_id("journal", "day-5"), "userId": USER_ID,
        "content": "Something clicked today. I realized I've been trying to get my manager to validate my work — and that's not something I can control. The only thing I can control is how I show up. That feels like a real shift.",
        "moodAtEntry": "okay", "sentiment": "positive",
        "themes": ["work stress", "control", "self-awareness", "boundary"],
        "summary": "User had a significant mindset shift: recognizing external validation cannot be controlled.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(5),
    },
    {
        "id": det_id("journal", "day-4"), "userId": USER_ID,
        "content": "BREAKTHROUGH DAY. I've been keeping my phone off until 9am this week and the mornings feel completely different. Less reactive, more present. This is the thing. I'm going to make this a proper habit.",
        "moodAtEntry": "great", "sentiment": "positive",
        "themes": ["phone habits", "morning routine", "breakthrough", "habit formation"],
        "summary": "User experienced a clear breakthrough: phone-free mornings until 9am produce a noticeably calmer and more present emotional state.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(4),
    },
    {
        "id": det_id("journal", "day-3"), "userId": USER_ID,
        "content": "Five days of morning meditation in a row. I can see the streak and it actually motivates me — but not in a guilty way, more like genuine pride. The journal entries this week have all been calmer in tone.",
        "moodAtEntry": "great", "sentiment": "positive",
        "themes": ["morning meditation", "streak", "self-compassion", "mood improvement"],
        "summary": "User maintained a 5-day meditation streak with intrinsic motivation, noticing a shift in emotional tone.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(3),
    },
    {
        "id": det_id("journal", "day-2"), "userId": USER_ID,
        "content": "Had a difficult conversation with my manager today. But unlike two weeks ago, I stayed regulated. I said what I needed to say clearly. I was actually surprised at myself. The breathing practice is doing something.",
        "moodAtEntry": "okay", "sentiment": "positive",
        "themes": ["manager conflict", "self-regulation", "breathing exercise", "progress"],
        "summary": "User demonstrated concrete progress in emotional regulation during a previously triggering situation.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(2),
    },
    {
        "id": det_id("journal", "day-1"), "userId": USER_ID,
        "content": "Sunday evenings used to make me dread the week ahead. Tonight I noticed the old anxiety trying to creep in but it didn't take hold. I think I'm building something real here.",
        "moodAtEntry": "good", "sentiment": "positive",
        "themes": ["sunday anxiety", "mood patterns", "resilience", "growth"],
        "summary": "User noticed reduced Sunday evening anxiety — a previously consistent trigger — and attributed it to sustained practice.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(1),
    },
    {
        "id": det_id("journal", "day-0"), "userId": USER_ID,
        "content": "Starting this week with meditation already done. Feels different to begin the day having already done something for myself. The phone-off-until-9 rule is holding. I feel ready.",
        "moodAtEntry": "great", "sentiment": "positive",
        "themes": ["morning routine", "self-care", "readiness", "consistency"],
        "summary": "User began the week with established morning routine, reporting a sense of readiness and calm.",
        "agentUsed": "journal", "embedding": [], "timestamp": days_ago(0),
    },
]

MOOD_LOGS = [
    {"id": det_id("mood", "day-13"), "userId": USER_ID, "mood": "anxious", "score": 2, "context": "evening_checkin",  "note": "Rough day at work",                   "timestamp": days_ago(13)},
    {"id": det_id("mood", "day-12"), "userId": USER_ID, "mood": "anxious", "score": 3, "context": "morning_checkin", "note": "Dreading the week",                   "timestamp": days_ago(12)},
    {"id": det_id("mood", "day-11"), "userId": USER_ID, "mood": "sad",     "score": 3, "context": "evening_checkin",  "note": "Presentation went badly",             "timestamp": days_ago(11)},
    {"id": det_id("mood", "day-10"), "userId": USER_ID, "mood": "okay",    "score": 5, "context": "morning_checkin", "note": "Wednesday — usually better",           "timestamp": days_ago(10)},
    {"id": det_id("mood", "day-9"),  "userId": USER_ID, "mood": "good",    "score": 7, "context": "morning_checkin", "note": "Meditation helped",                    "timestamp": days_ago(9)},
    {"id": det_id("mood", "day-8"),  "userId": USER_ID, "mood": "good",    "score": 6, "context": "evening_checkin",  "note": "Less reactive today",                 "timestamp": days_ago(8)},
    {"id": det_id("mood", "day-7"),  "userId": USER_ID, "mood": "good",    "score": 7, "context": "morning_checkin", "note": "Weekend restoration",                  "timestamp": days_ago(7)},
    {"id": det_id("mood", "day-6"),  "userId": USER_ID, "mood": "anxious", "score": 4, "context": "morning_checkin", "note": "Monday but managed it",                "timestamp": days_ago(6)},
    {"id": det_id("mood", "day-5"),  "userId": USER_ID, "mood": "okay",    "score": 6, "context": "evening_checkin",  "note": "Big mindset shift today",             "timestamp": days_ago(5)},
    {"id": det_id("mood", "day-4"),  "userId": USER_ID, "mood": "great",   "score": 8, "context": "morning_checkin", "note": "Phone off until 9 — different feeling","timestamp": days_ago(4)},
    {"id": det_id("mood", "day-3"),  "userId": USER_ID, "mood": "great",   "score": 9, "context": "morning_checkin", "note": "5 day streak — proud",                 "timestamp": days_ago(3)},
    {"id": det_id("mood", "day-2"),  "userId": USER_ID, "mood": "okay",    "score": 7, "context": "evening_checkin",  "note": "Stayed regulated in hard convo",      "timestamp": days_ago(2)},
    {"id": det_id("mood", "day-1"),  "userId": USER_ID, "mood": "good",    "score": 8, "context": "evening_checkin",  "note": "Sunday anxiety smaller than usual",   "timestamp": days_ago(1)},
    {"id": det_id("mood", "day-0"),  "userId": USER_ID, "mood": "great",   "score": 9, "context": "morning_checkin", "note": "Ready for the week",                   "timestamp": days_ago(0)},
]

HABITS = [
    {
        "id": det_id("habit", "morning-meditation"), "userId": USER_ID,
        "name": "Morning meditation",
        "why": "To feel grounded and less reactive before the workday starts",
        "frequency": "daily", "targetTime": "07:30", "durationMins": 10,
        "logs": [date_str_days_ago(d) for d in [0,1,2,3,4,6,7,8,9,10]],
        "currentStreak": 5, "longestStreak": 10, "active": True,
    },
    {
        "id": det_id("habit", "evening-journal"), "userId": USER_ID,
        "name": "Evening journal",
        "why": "To process my day and stop carrying unresolved thoughts to bed",
        "frequency": "daily", "targetTime": "21:00", "durationMins": 15,
        "logs": [date_str_days_ago(d) for d in [0,1,2,3,4,5,6,7]],
        "currentStreak": 8, "longestStreak": 8, "active": True,
    },
    {
        "id": det_id("habit", "phone-off-9am"), "userId": USER_ID,
        "name": "Phone off until 9am",
        "why": "Mornings without my phone feel completely different — calmer and more present",
        "frequency": "daily", "targetTime": "09:00", "durationMins": 0,
        "logs": [date_str_days_ago(d) for d in [0,1,2,3,4]],
        "currentStreak": 5, "longestStreak": 5, "active": True,
    },
    {
        "id": det_id("habit", "30-min-walk"), "userId": USER_ID,
        "name": "30 minute walk",
        "why": "To get out of my head and into my body",
        "frequency": "daily", "targetTime": "17:00", "durationMins": 30,
        "logs": [date_str_days_ago(d) for d in [0,2,4,6,8,10,12]],
        "currentStreak": 1, "longestStreak": 3, "active": True,
    },
    {
        "id": det_id("habit", "no-screens-9pm"), "userId": USER_ID,
        "name": "No screens after 9pm",
        "why": "Better sleep means better everything the next day",
        "frequency": "daily", "targetTime": "21:00", "durationMins": 0,
        "logs": [date_str_days_ago(d) for d in [1,3,5,7]],
        "currentStreak": 0, "longestStreak": 4, "active": True,
    },
]

USER_MEMORY = {
    "id": USER_ID, "userId": USER_ID,
    "facts": [
        {
            "content": "User experiences significant work stress connected to a difficult relationship with their manager, specifically around unclear expectations and lack of recognition.",
            "source": "journal_entry", "importance": 0.95,
            "createdAt": days_ago(13), "lastReferencedAt": days_ago(2),
        },
        {
            "content": "User discovered that mornings without phone use until 9am produce a noticeably calmer and more present emotional baseline — identified as a personal breakthrough.",
            "source": "journal_entry", "importance": 0.92,
            "createdAt": days_ago(4), "lastReferencedAt": days_ago(0),
        },
        {
            "content": "User consistently experiences higher anxiety on Mondays and Tuesdays, with natural emotional recovery occurring by Wednesday — a recurring weekly mood pattern.",
            "source": "mood_log", "importance": 0.88,
            "createdAt": days_ago(9), "lastReferencedAt": days_ago(6),
        },
        {
            "content": "User responds well to breathing exercises, particularly box breathing, when used proactively before stressful situations rather than reactively after.",
            "source": "journal_entry", "importance": 0.85,
            "createdAt": days_ago(6), "lastReferencedAt": days_ago(2),
        },
        {
            "content": "User has shown measurable progress in emotional regulation — able to have difficult conversations with their manager without escalating, attributed to breathing practice.",
            "source": "journal_entry", "importance": 0.80,
            "createdAt": days_ago(2), "lastReferencedAt": days_ago(0),
        },
    ],
    "weekSummary": (
        "This week the user maintained a 5-day meditation streak and established a phone-free morning routine. "
        "Mood scores trended from 4 (Monday) up to 9 (Friday), with the user noting they felt emotionally regulated "
        "during a difficult manager conversation on Wednesday — something that would have been harder two weeks ago."
    ),
    "weekSummaryUpdatedAt": days_ago(0),
    "learnedPreferences": {
        "preferredTone": "warm",
        "bestJournalingTime": "evening",
        "respondsWellTo": ["breathing exercises", "open questions", "streak acknowledgment"],
        "avoids": ["direct advice", "long bullet lists", "guilt framing"],
    },
    "recurringThemes": ["work stress", "manager conflict", "morning routine", "breathing exercises", "mood patterns"],
    "breakthroughs": [
        "Mornings without phone use until 9am produce a noticeably calmer emotional baseline",
        "Monday and Tuesday consistently bring higher anxiety — awareness of this pattern reduces its impact",
        "External validation from manager cannot be controlled — only personal effort can",
        "Sunday evening anxiety is decreasing as weekly resilience builds",
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
    print("\n⚠️  NEXT: Bulk-index journal entries into Azure AI Search in Hour 7.")
    print("   Embeddings are generated by the FastAPI backend at that point.")


if __name__ == "__main__":
    seed()
