'use client';

import { useState } from 'react';
import ChatWindow from '../components/ChatWindow';
import MorningBanner from '../components/MorningBanner';
import HabitTracker from '../components/HabitTracker';
import InsightsDashboard from '../components/InsightsDashboard';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const USER_ID = 'demo-user-001';
const USER_NAME = 'Alex';

type Tab = 'chat' | 'habits' | 'insights';

export default function Home() {
  const [tab, setTab] = useState<Tab>('chat');
  const [bannerDismissed, setBannerDismissed] = useState(false);

  async function handleMoodSelect(mood: string, score: number) {
    setBannerDismissed(true);
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
          {(['chat', 'habits', 'insights'] as Tab[]).map((t) => (
            <button
              key={t}
              role="tab"
              aria-selected={tab === t}
              className={`tab-btn ${tab === t ? 'active' : ''}`}
              onClick={() => setTab(t)}
              id={`tab-${t}`}
            >
              {t === 'chat' && '💬 Chat'}
              {t === 'habits' && '🌱 Habits'}
              {t === 'insights' && '✨ Insights'}
            </button>
          ))}
        </nav>
      </header>

      {/* Body */}
      <div className="app-body">
        {tab === 'chat' && (
          <>
            {!bannerDismissed && (
              <MorningBanner
                name={USER_NAME}
                onMoodSelect={handleMoodSelect}
              />
            )}
            <ChatWindow userId={USER_ID} />
          </>
        )}

        {tab === 'habits' && (
          <HabitTracker userId={USER_ID} />
        )}

        {tab === 'insights' && (
          <InsightsDashboard userId={USER_ID} />
        )}
      </div>
    </main>
  );
}
