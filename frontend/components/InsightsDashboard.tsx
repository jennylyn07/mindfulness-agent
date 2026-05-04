'use client';

import { useState, useEffect } from 'react';
import MoodSparkline from './MoodSparkline';
import CalendarView from './CalendarView';

interface MoodLog {
  score: number;
  mood: string;
  timestamp: string;
}

interface InsightsDashboardProps {
  userId: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

const MOOD_EMOJI: Record<string, string> = {
  anxious: '😰', sad: '😔', okay: '😐', good: '🙂', great: '😊',
};

export default function InsightsDashboard({ userId }: InsightsDashboardProps) {
  const [moodLogs, setMoodLogs] = useState<MoodLog[]>([]);
  const [weekSummary, setWeekSummary] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [calendarOpen, setCalendarOpen] = useState(true);

  function loadInsights() {
    setLoading(true);
    setError(false);
    fetch(`${API_URL}/insights?userId=${userId}&days=14`)
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then((data) => {
        setMoodLogs(data.moodLogs ?? []);
        setWeekSummary(data.weekSummary ?? '');
      })
      .catch((e) => { console.error('Failed to load insights:', e); setError(true); })
      .finally(() => setLoading(false));
  }

  useEffect(() => { loadInsights(); }, [userId]);

  // Compute mood frequency for the past 14 days
  const moodCounts = moodLogs.reduce<Record<string, number>>((acc, log) => {
    acc[log.mood] = (acc[log.mood] ?? 0) + 1;
    return acc;
  }, {});

  const dominantMood = Object.entries(moodCounts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? null;
  const avgScore = moodLogs.length
    ? (moodLogs.reduce((s, l) => s + (l.score ?? 5), 0) / moodLogs.length).toFixed(1)
    : null;

  // 7-day vs prior 7-day trend
  const now = Date.now();
  const week1 = moodLogs.filter((l) => now - new Date(l.timestamp).getTime() < 7 * 864e5);
  const week2 = moodLogs.filter((l) => {
    const age = now - new Date(l.timestamp).getTime();
    return age >= 7 * 864e5 && age < 14 * 864e5;
  });
  const avg1 = week1.length ? week1.reduce((s, l) => s + l.score, 0) / week1.length : null;
  const avg2 = week2.length ? week2.reduce((s, l) => s + l.score, 0) / week2.length : null;
  const trend = avg1 !== null && avg2 !== null ? avg1 - avg2 : null;

  if (error) {
    return (
      <div className="insights-shell">
        <div className="placeholder-tab">
          <span className="placeholder-emoji">⚠️</span>
          <p className="placeholder-title">Couldn't load insights</p>
          <p className="placeholder-sub">Check your connection and try again.</p>
          <button className="suggestion-chip" onClick={loadInsights} style={{ marginTop: '0.75rem' }}>Retry</button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="insights-shell">
        <div className="skeleton" style={{ height: '80px', borderRadius: '16px' }} />
        <div className="skeleton" style={{ height: '120px', borderRadius: '16px', marginTop: '0.75rem' }} />
        <div className="skeleton" style={{ height: '96px', borderRadius: '16px', marginTop: '0.75rem' }} />
      </div>
    );
  }

  return (
    <div className="insights-shell">

      {/* Weekly Reflection card — only shown when a summary exists */}
      {weekSummary && weekSummary !== 'No journal entries this week.' && (
        <div className="insights-card week-summary-card">
          <p className="insights-section-label" style={{ marginBottom: '0.5rem' }}>
            ✨ Your week, reflected
          </p>
          <p className="week-summary-text">{weekSummary}</p>
        </div>
      )}

      {/* Sparkline card */}
      <div className="insights-card">
        <MoodSparkline logs={moodLogs} />
      </div>

      {/* Stats row */}
      {moodLogs.length > 0 && (
        <div className="insights-stats">
          <div className="stat-pill">
            <span className="stat-value">{avgScore}</span>
            <span className="stat-label">Avg mood</span>
          </div>
          <div className="stat-pill">
            <span className="stat-value">{MOOD_EMOJI[dominantMood!] ?? '—'}</span>
            <span className="stat-label">Most common</span>
          </div>
          {trend !== null && (
            <div className="stat-pill">
              <span className="stat-value" style={{ color: trend >= 0 ? 'var(--sage-deep)' : 'var(--accent)' }}>
                {trend >= 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(1)}
              </span>
              <span className="stat-label">vs last week</span>
            </div>
          )}
        </div>
      )}

      {/* Calendar (collapsible) */}
      <div className="insights-card">
        <button
          className="journal-expand-btn"
          onClick={() => setCalendarOpen((v) => !v)}
          aria-expanded={calendarOpen}
          style={{ width: '100%' }}
        >
          {calendarOpen ? '▲' : '▼'} 📅 Your month at a glance
        </button>
        {calendarOpen && (
          <div style={{ marginTop: '0.75rem' }}>
            <CalendarView userId={userId} />
          </div>
        )}
      </div>

      {/* Mood frequency pills */}
      {Object.keys(moodCounts).length > 0 && (
        <div className="insights-card">
          <p className="insights-section-label">Mood breakdown</p>
          <div className="mood-freq-row">
            {Object.entries(moodCounts)
              .sort((a, b) => b[1] - a[1])
              .map(([mood, count]) => (
                <span key={mood} className={`mood-freq-pill mood-freq-${mood}`}>
                  {MOOD_EMOJI[mood] ?? '😐'} {mood} ×{count}
                </span>
              ))}
          </div>
        </div>
      )}

      {/* Lumen prompt card */}
      <div className="insights-card lumen-prompt">
        <p className="lumen-prompt-text">
          ✨ Ask Lumen about your patterns
        </p>
        <p className="lumen-prompt-sub">
          Switch to Chat and ask: <em>&quot;What patterns do you see in my journal?&quot;</em>
        </p>
      </div>

      {/* Empty state */}
      {moodLogs.length === 0 && (
        <div className="placeholder-tab">
          <span className="placeholder-emoji">📊</span>
          <p className="placeholder-title">No data yet</p>
          <p className="placeholder-sub">
            Log your mood each morning and journal for a few days — your patterns will appear here.
          </p>
        </div>
      )}
    </div>
  );
}
