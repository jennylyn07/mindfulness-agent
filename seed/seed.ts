/**
 * MindFlow Seed Script
 * ────────────────────────────────────────────────────────────────────────────
 * SELF-CONTAINED — zero imports from lib/. Uses raw CosmosClient only.
 * Run: npm run seed
 *
 * Creates for DEMO_USER_ID=demo-user-001:
 *   - 1 user document
 *   - 14 journal entries (deliberate emotional arc — required for Minute 4 demo)
 *   - 5 habits with 7–14 days of logs (real streaks)
 *   - 14 mood logs (narrative arc matches journal entries)
 *   - 1 user_memory document (3+ pre-populated facts)
 */

import { CosmosClient } from '@azure/cosmos';
import { v4 as uuidv4 } from 'uuid';

// ── Config ────────────────────────────────────────────────
const ENDPOINT = process.env.COSMOS_ENDPOINT!;
const KEY = process.env.COSMOS_KEY!;
const DB_NAME = process.env.COSMOS_DB_NAME || 'mindflow';
const USER_ID = process.env.DEMO_USER_ID || 'demo-user-001';

if (!ENDPOINT || !KEY) {
  console.error('❌ COSMOS_ENDPOINT and COSMOS_KEY must be set in .env.local');
  process.exit(1);
}

const client = new CosmosClient({ endpoint: ENDPOINT, key: KEY });

// ── Helpers ───────────────────────────────────────────────
function daysAgo(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString();
}

function dateStringDaysAgo(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().split('T')[0];
}

// ── Seed Data ─────────────────────────────────────────────
// Emotional arc: work stress peaks Days 1–3, recovery mid-week,
// breakthrough at Day 10, sustained improvement Days 11–14.
// Lumen's RAG must find specific patterns — generic text ruins the Minute 4 demo.

const journalEntries = [
  {
    id: uuidv4(), userId: USER_ID,
    content: "Today was brutal. My manager keeps moving the goalposts on the project scope and I feel like nothing I do is ever enough. I stayed late again and I'm exhausted. I don't know how much longer I can keep this pace up.",
    moodAtEntry: 'anxious', sentiment: 'negative', themes: ['work stress', 'manager conflict', 'exhaustion'],
    summary: 'User felt overwhelmed by unclear expectations and an exhausting work pace.',
    agentUsed: 'journal', embedding: [], timestamp: daysAgo(13),
  },
  {
    id: uuidv4(), userId: USER_ID,
    content: "Another hard Monday. Woke up dreading the week already. The anxiety about the presentation my manager wants by Friday kept me up last night. I tried the box breathing thing this morning and it helped a little — maybe I'll try it again tonight.",
    moodAtEntry: 'anxious', sentiment: 'negative', themes: ['work stress', 'sleep issues', 'breathing exercise'],
    summary: 'User struggled with anticipatory anxiety but noted breathing exercises helped slightly.',
    agentUsed: 'journal', embedding: [], timestamp: daysAgo(12),
  },
  {
    id: uuidv4(), userId: USER_ID,
    content: "I did the presentation. My manager barely acknowledged it and then immediately pointed out what was missing. I felt invisible. On the walk home I noticed I've been holding tension in my shoulders for weeks.",
    moodAtEntry: 'sad', sentiment: 'negative', themes: ['manager conflict', 'feeling invisible', 'body awareness'],
    summary: 'User felt unseen after a presentation and became aware of physical tension from chronic stress.',
    agentUsed: 'journal', embedding: [], timestamp: daysAgo(11),
  },
  {
    id: uuidv4(), userId: USER_ID,
    content: "Wednesday is always better for some reason. Had a good conversation with a colleague about the manager situation — apparently others feel the same way. That helped. Did my morning meditation today, first time in a week.",
    moodAtEntry: 'okay', sentiment: 'neutral', themes: ['work stress', 'connection', 'morning meditation'],
    summary: 'User found relief through peer connection and returned to morning meditation practice.',
    agentUsed: 'journal', embedding: [], timestamp: daysAgo(10),
  },
  {
    id: uuidv4(), userId: USER_ID,
    content: "Thursday felt lighter. I've noticed I'm almost always more anxious on Mondays and Tuesdays — by Wednesday something shifts. The meditation this morning was really grounding. Maybe there's something to this consistency thing.",
    moodAtEntry: 'good', sentiment: 'positive', themes: ['mood patterns', 'morning meditation', 'consistency'],
    summary: 'User noticed a recurring mood pattern — higher anxiety early week, recovery mid-week — linked to meditation consistency.',
    agentUsed: 'journal', embedding: [], timestamp: daysAgo(9),
  },
  {
    id: uuidv4(), userId: USER_ID,
    content: "Long week but I made it. Manager situation is the same but I feel less reactive to it today. I've been thinking about why certain mornings feel so different — the ones where I don't look at my phone first thing are noticeably calmer.",
    moodAtEntry: 'good', sentiment: 'positive', themes: ['manager conflict', 'morning routine', 'phone habits'],
    summary: 'User identified that phone-free mornings correlate with a calmer emotional baseline.',
    agentUsed: 'journal', embedding: [], timestamp: daysAgo(8),
  },
  {
    id: uuidv4(), userId: USER_ID,
    content: "Weekend was restorative. Went for a walk without headphones and just let my mind wander. It felt strange at first but I noticed I wasn't thinking about work at all after about ten minutes.",
    moodAtEntry: 'good', sentiment: 'positive', themes: ['rest', 'nature', 'mental space'],
    summary: 'User experienced mental relief through undistracted walking.',
    agentUsed: 'journal', embedding: [], timestamp: daysAgo(7),
  },
  {
    id: uuidv4(), userId: USER_ID,
    content: "Monday again. Smaller anxiety spike than usual — noticed it and did the box breathing before the stand-up meeting. It actually helped me stay calm when my manager criticized the timeline in front of the team.",
    moodAtEntry: 'anxious', sentiment: 'neutral', themes: ['work stress', 'breathing exercise', 'manager conflict'],
    summary: 'User proactively used breathing technique before a stressful meeting with measurable effect.',
    agentUsed: 'journal', embedding: [], timestamp: daysAgo(6),
  },
  {
    id: uuidv4(), userId: USER_ID,
    content: "Something clicked today. I realized I've been trying to get my manager to validate my work — and that's not something I can control. The only thing I can control is how I show up. That feels like a shift.",
    moodAtEntry: 'okay', sentiment: 'positive', themes: ['work stress', 'control', 'self-awareness', 'boundary'],
    summary: 'User had a significant mindset shift: recognizing external validation cannot be controlled, only personal effort can.',
    agentUsed: 'journal', embedding: [], timestamp: daysAgo(5),
  },
  {
    id: uuidv4(), userId: USER_ID,
    content: "BREAKTHROUGH DAY. I've been keeping my phone off until 9am this week and the mornings feel completely different. Less reactive, more present. This is the thing. I'm going to make this a proper habit.",
    moodAtEntry: 'great', sentiment: 'positive', themes: ['phone habits', 'morning routine', 'breakthrough', 'habit formation'],
    summary: 'User experienced a clear breakthrough: phone-free mornings until 9am produce a noticeably calmer and more present emotional state.',
    agentUsed: 'journal', embedding: [], timestamp: daysAgo(4),
  },
  {
    id: uuidv4(), userId: USER_ID,
    content: "Five days of morning meditation in a row. I can see the streak and it actually motivates me — but not in a guilty way, more like genuine pride. The journal entries this week have all been calmer in tone, I noticed that.",
    moodAtEntry: 'great', sentiment: 'positive', themes: ['morning meditation', 'streak', 'self-compassion', 'mood improvement'],
    summary: 'User maintained a 5-day meditation streak with intrinsic rather than guilt-based motivation, noticing a shift in emotional tone.',
    agentUsed: 'journal', embedding: [], timestamp: daysAgo(3),
  },
  {
    id: uuidv4(), userId: USER_ID,
    content: "Had a difficult conversation with my manager today. But unlike two weeks ago, I stayed regulated. I said what I needed to say clearly. I was actually surprised at myself. The breathing practice is doing something.",
    moodAtEntry: 'okay', sentiment: 'positive', themes: ['manager conflict', 'self-regulation', 'breathing exercise', 'progress'],
    summary: 'User demonstrated concrete progress in emotional regulation during a previously triggering situation with their manager.',
    agentUsed: 'journal', embedding: [], timestamp: daysAgo(2),
  },
  {
    id: uuidv4(), userId: USER_ID,
    content: "Sunday evenings used to make me dread the week ahead. Tonight I noticed the old anxiety trying to creep in but it didn't take hold. I think I'm building something real here.",
    moodAtEntry: 'good', sentiment: 'positive', themes: ['sunday anxiety', 'mood patterns', 'resilience', 'growth'],
    summary: 'User noticed reduced Sunday evening anxiety — a previously consistent trigger — and attributed it to sustained practice.',
    agentUsed: 'journal', embedding: [], timestamp: daysAgo(1),
  },
  {
    id: uuidv4(), userId: USER_ID,
    content: "Starting this week with meditation already done. Feels different to begin the day having already done something for myself. The phone-off-until-9 rule is holding. I feel ready.",
    moodAtEntry: 'great', sentiment: 'positive', themes: ['morning routine', 'self-care', 'readiness', 'consistency'],
    summary: 'User began the week with established morning routine, reporting a sense of readiness and calm.',
    agentUsed: 'journal', embedding: [], timestamp: daysAgo(0),
  },
];

// Mood logs match the journal emotional arc
const moodLogs = [
  { id: uuidv4(), userId: USER_ID, mood: 'anxious',  score: 2, context: 'evening_checkin',  note: 'Rough day at work', timestamp: daysAgo(13) },
  { id: uuidv4(), userId: USER_ID, mood: 'anxious',  score: 3, context: 'morning_checkin', note: 'Dreading the week', timestamp: daysAgo(12) },
  { id: uuidv4(), userId: USER_ID, mood: 'sad',      score: 3, context: 'evening_checkin',  note: 'Presentation went badly', timestamp: daysAgo(11) },
  { id: uuidv4(), userId: USER_ID, mood: 'okay',     score: 5, context: 'morning_checkin', note: 'Wednesday — usually better', timestamp: daysAgo(10) },
  { id: uuidv4(), userId: USER_ID, mood: 'good',     score: 7, context: 'morning_checkin', note: 'Meditation helped', timestamp: daysAgo(9) },
  { id: uuidv4(), userId: USER_ID, mood: 'good',     score: 6, context: 'evening_checkin',  note: 'Less reactive today', timestamp: daysAgo(8) },
  { id: uuidv4(), userId: USER_ID, mood: 'good',     score: 7, context: 'morning_checkin', note: 'Weekend restoration', timestamp: daysAgo(7) },
  { id: uuidv4(), userId: USER_ID, mood: 'anxious',  score: 4, context: 'morning_checkin', note: 'Monday but managed it', timestamp: daysAgo(6) },
  { id: uuidv4(), userId: USER_ID, mood: 'okay',     score: 6, context: 'evening_checkin',  note: 'Big mindset shift today', timestamp: daysAgo(5) },
  { id: uuidv4(), userId: USER_ID, mood: 'great',    score: 8, context: 'morning_checkin', note: 'Phone off until 9 — different feeling', timestamp: daysAgo(4) },
  { id: uuidv4(), userId: USER_ID, mood: 'great',    score: 9, context: 'morning_checkin', note: '5 day streak — proud', timestamp: daysAgo(3) },
  { id: uuidv4(), userId: USER_ID, mood: 'okay',     score: 7, context: 'evening_checkin',  note: 'Stayed regulated in hard convo', timestamp: daysAgo(2) },
  { id: uuidv4(), userId: USER_ID, mood: 'good',     score: 8, context: 'evening_checkin',  note: 'Sunday anxiety smaller than usual', timestamp: daysAgo(1) },
  { id: uuidv4(), userId: USER_ID, mood: 'great',    score: 9, context: 'morning_checkin', note: 'Ready for the week', timestamp: daysAgo(0) },
];

// 5 habits with realistic logs (gives real streaks for demo)
const habits = [
  {
    id: uuidv4(), userId: USER_ID,
    name: 'Morning meditation',
    why: 'To feel grounded and less reactive before the workday starts',
    frequency: 'daily', targetTime: '07:30', durationMins: 10,
    logs: [0,1,2,3,4,6,7,8,9,10].map(d => dateStringDaysAgo(d)),
    currentStreak: 5, longestStreak: 10, active: true,
  },
  {
    id: uuidv4(), userId: USER_ID,
    name: 'Evening journal',
    why: 'To process my day and stop carrying unresolved thoughts to bed',
    frequency: 'daily', targetTime: '21:00', durationMins: 15,
    logs: [0,1,2,3,4,5,6,7].map(d => dateStringDaysAgo(d)),
    currentStreak: 8, longestStreak: 8, active: true,
  },
  {
    id: uuidv4(), userId: USER_ID,
    name: 'Phone off until 9am',
    why: 'Mornings without my phone feel completely different — calmer and more present',
    frequency: 'daily', targetTime: '09:00', durationMins: 0,
    logs: [0,1,2,3,4].map(d => dateStringDaysAgo(d)),
    currentStreak: 5, longestStreak: 5, active: true,
  },
  {
    id: uuidv4(), userId: USER_ID,
    name: '30 minute walk',
    why: 'To get out of my head and into my body',
    frequency: 'daily', targetTime: '17:00', durationMins: 30,
    logs: [0,2,4,6,8,10,12].map(d => dateStringDaysAgo(d)),
    currentStreak: 1, longestStreak: 3, active: true,
  },
  {
    id: uuidv4(), userId: USER_ID,
    name: 'No screens after 9pm',
    why: 'Better sleep means better everything the next day',
    frequency: 'daily', targetTime: '21:00', durationMins: 0,
    logs: [1,3,5,7].map(d => dateStringDaysAgo(d)),
    currentStreak: 0, longestStreak: 4, active: true,
  },
];

// User memory — pre-populated with 4 facts so Lumen's demo moment lands
const userMemory = {
  id: USER_ID,
  userId: USER_ID,
  facts: [
    {
      content: 'User experiences significant work stress connected to a difficult relationship with their manager, specifically around unclear expectations and lack of recognition.',
      source: 'journal_entry',
      importance: 0.95,
      createdAt: daysAgo(13),
      lastReferencedAt: daysAgo(2),
    },
    {
      content: 'User has discovered that mornings without phone use until 9am produce a noticeably calmer and more present emotional baseline — identified as a personal breakthrough.',
      source: 'journal_entry',
      importance: 0.92,
      createdAt: daysAgo(4),
      lastReferencedAt: daysAgo(0),
    },
    {
      content: 'User consistently experiences higher anxiety on Mondays and Tuesdays, with natural emotional recovery occurring by Wednesday — a recurring weekly mood pattern.',
      source: 'mood_log',
      importance: 0.88,
      createdAt: daysAgo(9),
      lastReferencedAt: daysAgo(6),
    },
    {
      content: 'User responds well to breathing exercises, particularly box breathing, when used proactively before stressful situations rather than reactively after.',
      source: 'journal_entry',
      importance: 0.85,
      createdAt: daysAgo(6),
      lastReferencedAt: daysAgo(2),
    },
    {
      content: 'User has shown measurable progress in emotional regulation — able to have difficult conversations with their manager without escalating, attributed to breathing practice.',
      source: 'journal_entry',
      importance: 0.80,
      createdAt: daysAgo(2),
      lastReferencedAt: daysAgo(0),
    },
  ],
  weekSummary:
    'This week the user maintained a 5-day meditation streak and established a phone-free morning routine. Mood scores trended from 4 (Monday) up to 9 (Friday), with the user noting they felt emotionally regulated during a difficult manager conversation on Wednesday — something that would have been harder two weeks ago.',
  weekSummaryUpdatedAt: daysAgo(0),
  learnedPreferences: {
    preferredTone: 'warm',
    bestJournalingTime: 'evening',
    respondsWellTo: ['breathing exercises', 'open questions', 'streak acknowledgment'],
    avoids: ['direct advice', 'long bullet lists', 'guilt framing'],
  },
  recurringThemes: ['work stress', 'manager conflict', 'morning routine', 'breathing exercises', 'mood patterns'],
  breakthroughs: [
    'Mornings without phone use until 9am produce a noticeably calmer emotional baseline',
    'Monday and Tuesday consistently bring higher anxiety — awareness of this pattern reduces its impact',
    'External validation from manager cannot be controlled — only personal effort can',
    'Sunday evening anxiety is decreasing as weekly resilience builds',
  ],
  updatedAt: daysAgo(0),
};

const user = {
  id: USER_ID,
  userId: USER_ID,
  email: 'demo@mindflow.app',
  displayName: 'Alex',
  timezone: 'Asia/Manila',
  preferences: { morningCheckIn: true, tone: 'warm' },
  createdAt: daysAgo(14),
};

// ── Main ──────────────────────────────────────────────────
async function seed() {
  console.log('🌱 MindFlow Seed Script');
  console.log(`   Endpoint: ${ENDPOINT}`);
  console.log(`   Database: ${DB_NAME}`);
  console.log(`   User ID:  ${USER_ID}\n`);

  const db = client.database(DB_NAME);

  // Ensure all collections exist
  const collections = ['users', 'journal_entries', 'habits', 'mood_logs', 'user_memory'];
  for (const name of collections) {
    await db.containers.createIfNotExists({ id: name, partitionKey: { paths: ['/userId'] } });
    console.log(`  ✓ Collection ready: ${name}`);
  }

  // Upsert user
  await db.container('users').items.upsert(user);
  console.log(`\n  ✓ User upserted: ${user.displayName} (${USER_ID})`);

  // Upsert journal entries
  let journalCount = 0;
  for (const entry of journalEntries) {
    await db.container('journal_entries').items.upsert(entry);
    journalCount++;
  }
  console.log(`  ✓ Journal entries upserted: ${journalCount}`);

  // Upsert habits
  for (const habit of habits) {
    await db.container('habits').items.upsert(habit);
  }
  console.log(`  ✓ Habits upserted: ${habits.length}`);

  // Upsert mood logs
  for (const log of moodLogs) {
    await db.container('mood_logs').items.upsert(log);
  }
  console.log(`  ✓ Mood logs upserted: ${moodLogs.length}`);

  // Upsert user memory
  await db.container('user_memory').items.upsert(userMemory);
  console.log(`  ✓ User memory upserted (${userMemory.facts.length} facts)`);

  console.log('\n✅ Seed complete. Demo account is ready.');
  console.log('\n⚠️  NEXT: Bulk-index journal entries into Azure AI Search in Hour 7.');
  console.log('   The seed script does NOT embed — embeddings require the AI Foundry endpoint.');
}

seed().catch((err) => {
  console.error('❌ Seed failed:', err);
  process.exit(1);
});
