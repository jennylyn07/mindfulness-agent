'use client';

import { useState, useEffect } from 'react';

interface JournalEntry {
  id: string;
  userId: string;
  content: string;       // River's full response text
  moodAtEntry: string;   // "anxious", "calm", "okay", etc.
  sentiment: string;     // "negative" | "neutral" | "positive"
  themes: string[];
  summary: string;
  agentUsed: string;
  timestamp: string;     // ISO 8601
}

interface JournalViewProps {
  userId: string;
  isActive?: boolean;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

const MOOD_COLORS: Record<string, string> = {
  positive: 'journal-mood-positive',
  neutral:  'journal-mood-neutral',
  negative: 'journal-mood-negative',
};

const MOOD_EMOJI: Record<string, string> = {
  // seed mood values
  great: '😊', good: '🙂', okay: '😐', rough: '😟',
  // conversational mood values from River
  anxious: '😟', overwhelmed: '😰', stressed: '😤', sad: '😢',
  calm: '😌', happy: '😊', grateful: '🙏', hopeful: '🌱',
  neutral: '😐', tired: '😴', frustrated: '😣',
  // fallback handled below
};

function formatDate(iso: string): { day: string; time: string; full: string } {
  const d = new Date(iso);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000);

  const time = d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  const full = d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
  if (diffDays === 0) return { day: 'Today', time, full };
  if (diffDays === 1) return { day: 'Yesterday', time, full };
  if (diffDays < 7)   return { day: `${diffDays} days ago`, time, full };
  return { day: full, time, full };
}

export default function JournalView({ userId, isActive }: JournalViewProps) {
  const [entries, setEntries]     = useState<JournalEntry[]>([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(false);
  const [expanded, setExpanded]   = useState<Set<string>>(new Set());
  const [retryCount, setRetryCount] = useState(0);
  const [editingEntryId, setEditingEntryId] = useState<string | null>(null);
  const [editSummary, setEditSummary]       = useState('');

  // Initial fetch + manual retry
  useEffect(() => {
    fetchEntries();
  }, [retryCount]);

  // Re-fetch whenever Journal tab becomes active (catches River entries created via chat)
  useEffect(() => {
    if (isActive) fetchEntries();
  }, [isActive]);

  async function fetchEntries() {
    setLoading(true);
    setError(false);
    try {
      const res = await fetch(`${API_URL}/journal?userId=${userId}&limit=50`);
      if (res.ok) {
        const data: JournalEntry[] = await res.json();
        // Newest first
        data.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
        setEntries(data);
      } else {
        setError(true);
      }
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  function toggleExpand(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function startEdit(entry: JournalEntry) {
    setEditingEntryId(entry.id);
    setEditSummary(entry.summary);
  }

  async function saveEdit(entryId: string) {
    try {
      const res = await fetch(
        `${API_URL}/journal/${entryId}?userId=${userId}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ summary: editSummary }),
        }
      );
      if (res.ok) {
        const updated = await res.json();
        setEntries((prev) =>
          prev.map((e) => (e.id === entryId ? { ...e, summary: updated.summary } : e))
        );
      }
    } catch (e) {
      console.error('Failed to update journal entry:', e);
    } finally {
      setEditingEntryId(null);
    }
  }

  // ── Loading state ───────────────────────────────────────
  if (loading) {
    return (
      <div className="journal-list">
        {[1, 2, 3].map((i) => (
          <div key={i} className="journal-card skeleton" style={{ height: '110px' }} />
        ))}
      </div>
    );
  }

  // ── Error state ─────────────────────────────────────────
  if (error) {
    return (
      <div className="placeholder-tab">
        <span className="placeholder-emoji">⚠️</span>
        <p className="placeholder-title">Couldn't load journal</p>
        <p className="placeholder-sub">Check your connection and try again.</p>
        <button
          className="suggestion-chip"
          onClick={() => setRetryCount((n) => n + 1)}
          style={{ marginTop: '0.75rem' }}
        >
          Retry
        </button>
      </div>
    );
  }

  // ── Empty state ──────────────────────────────────────────
  if (entries.length === 0) {
    return (
      <div className="placeholder-tab">
        <span className="placeholder-emoji">📓</span>
        <p className="placeholder-title">No entries yet</p>
        <p className="placeholder-sub">
          Chat with <strong>River</strong> in the Chat tab to start journaling.
          Your entries will appear here automatically.
        </p>
      </div>
    );
  }

  // ── Entries ──────────────────────────────────────────────
  return (
    <div className="journal-list">
      <p className="journal-header-label">
        {entries.length} {entries.length === 1 ? 'entry' : 'entries'} · newest first
      </p>

      {entries.map((entry) => {
        const { day, time } = formatDate(entry.timestamp);
        const isExpanded = expanded.has(entry.id);
        const moodKey = MOOD_COLORS[entry.sentiment] ?? 'journal-mood-neutral';
        const moodEmoji = MOOD_EMOJI[entry.moodAtEntry.toLowerCase()] ?? '💭';

        return (
          <div key={entry.id} className="journal-card" role="article">
            {/* Card header — date + mood */}
            <div className="journal-card-header">
              <div className="journal-date-block">
                <span className="journal-day">{day}</span>
                <span className="journal-time">{time}</span>
              </div>
              <span className={`journal-mood ${moodKey}`}>
                {moodEmoji} {entry.moodAtEntry}
              </span>
            </div>

            {/* Summary */}
            {editingEntryId === entry.id ? (
              <div className="journal-edit-wrap">
                <textarea
                  className="journal-edit-input"
                  value={editSummary}
                  onChange={(e) => setEditSummary(e.target.value)}
                  rows={3}
                  autoFocus
                />
                <div className="journal-edit-actions">
                  <button className="journal-edit-save" onClick={() => saveEdit(entry.id)}>Save</button>
                  <button className="journal-edit-cancel" onClick={() => setEditingEntryId(null)}>Cancel</button>
                </div>
              </div>
            ) : (
              entry.summary && (
                <div className="journal-summary-row">
                  <p className="journal-summary">{entry.summary}</p>
                  <button
                    className="journal-edit-btn"
                    onClick={() => startEdit(entry)}
                    title="Edit summary"
                    aria-label="Edit journal summary"
                  >✏️</button>
                </div>
              )
            )}

            {/* Themes */}
            {entry.themes.length > 0 && (
              <div className="journal-themes">
                {entry.themes.map((t) => (
                  <span key={t} className="journal-theme-chip">{t}</span>
                ))}
              </div>
            )}

            {/* Expandable: River's full response */}
            {entry.content && (
              <>
                <button
                  className="journal-expand-btn"
                  onClick={() => toggleExpand(entry.id)}
                  aria-expanded={isExpanded}
                >
                  {isExpanded ? "▲ Hide saved reflection" : "▼ Read saved reflection"}
                </button>
                {isExpanded && (
                  <div className="journal-content">
                    {entry.content}
                  </div>
                )}
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}
