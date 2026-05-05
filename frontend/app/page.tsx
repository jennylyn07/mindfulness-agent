'use client';

import { useState, useRef, useEffect } from 'react';
import ChatWindow from '../components/ChatWindow';
import MorningBanner from '../components/MorningBanner';
import HabitTracker from '../components/HabitTracker';
import InsightsDashboard from '../components/InsightsDashboard';
import JournalView from '../components/JournalView';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const USER_ID = 'demo-user-001'; // demo constant — would come from auth in production

type Tab = 'chat' | 'habits' | 'insights' | 'journal';

export default function Home() {
  const [tab, setTab] = useState<Tab>('chat');
  const [bannerDismissed, setBannerDismissed] = useState(false);
  const [userName, setUserName] = useState('');
  const [chatPreset, setChatPreset] = useState<string | null>(null);
  // Track which tabs have been visited so secondary tabs stay mounted
  const visitedTabs = useRef<Set<Tab>>(new Set<Tab>(['chat']));

  // Fetch display name from API on load — not hardcoded
  useEffect(() => {
    fetch(`${API_URL}/user?userId=${USER_ID}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.displayName) setUserName(data.displayName);
      })
      .catch(() => {
        // Non-fatal — banner still shows without a name
      });
  }, []);

  function switchTab(t: Tab) {
    visitedTabs.current.add(t);
    setTab(t);
  }

  // Lumen button: switch to chat and auto-send the patterns question
  function handleAskLumen() {
    switchTab('chat');
    setChatPreset('What patterns do you see across my journal entries?');
  }

  async function handleMoodSelect(mood: string, score: number) {
    // Dismiss after toast animation completes (MorningBanner shows toast for 800ms)
    setTimeout(() => setBannerDismissed(true), 1200);
    // Low mood (rough/anxious ≤ 4) → gently surface Sage after banner dismisses
    if (score <= 4) {
      setTimeout(() => setChatPreset(
        `I just checked in feeling ${mood}. Can you help me breathe for a moment?`
      ), 1400);
    }
    try {
      await fetch(`${API_URL}/mood`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mood,
          score,
          context: 'morning_checkin',
          userId: USER_ID,
        }),
      });
    } catch (e) {
      console.error('Mood log failed:', e);
    }
  }

  return (
    <main className="app-shell">
      {/* Header */}
      <header className="app-header">
        <span className="app-logo">
          Mind<span>Flow</span>
        </span>
        <nav className="tab-nav" role="tablist">
          {(['chat', 'journal', 'habits', 'insights'] as Tab[]).map((t) => (
            <button
              key={t}
              role="tab"
              aria-selected={tab === t}
              className={`tab-btn ${tab === t ? 'active' : ''}`}
              onClick={() => switchTab(t)}
              id={`tab-${t}`}
            >
              {t === 'chat'     && '💬 Chat'}
              {t === 'habits'   && '🌱 Habits'}
              {t === 'journal'  && '📓 Journal'}
              {t === 'insights' && '✨ Insights'}
            </button>
          ))}
        </nav>
      </header>

      {/* Body */}
      <div className="app-body">

        {/* Chat — always mounted, hidden via CSS to preserve conversation state */}
        <div className={`tab-panel ${tab === 'chat' ? 'tab-panel-active' : ''}`}>
          {!bannerDismissed && (
            <MorningBanner
              name={userName}
              onMoodSelect={handleMoodSelect}
            />
          )}
          <ChatWindow
            userId={USER_ID}
            presetMessage={chatPreset}
            onPresetConsumed={() => setChatPreset(null)}
          />
        </div>

        {/* Habits — lazy mount on first visit, stays mounted after */}
        {visitedTabs.current.has('habits') && (
          <div className={`tab-panel ${tab === 'habits' ? 'tab-panel-active' : ''}`}>
            <HabitTracker userId={USER_ID} isActive={tab === 'habits'} />
          </div>
        )}

        {/* Journal — lazy mount on first visit, stays mounted after */}
        {visitedTabs.current.has('journal') && (
          <div className={`tab-panel ${tab === 'journal' ? 'tab-panel-active' : ''}`}>
            <JournalView userId={USER_ID} />
          </div>
        )}

        {/* Insights — lazy mount on first visit, stays mounted after */}
        {visitedTabs.current.has('insights') && (
          <div className={`tab-panel ${tab === 'insights' ? 'tab-panel-active' : ''}`}>
            <InsightsDashboard userId={USER_ID} onAskLumen={handleAskLumen} />
          </div>
        )}

      </div>
    </main>
  );
}
