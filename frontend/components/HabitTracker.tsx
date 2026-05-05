'use client';

import { useState, useEffect } from 'react';
import HabitCoach from './HabitCoach';

interface Habit {
  id: string;
  name: string;
  why?: string;
  currentStreak: number;
  longestStreak?: number;
  logs: string[];
  active?: boolean;
}

interface HabitTrackerProps {
  userId: string;
  isActive?: boolean;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

function todayUTC(): string {
  return new Date().toISOString().split('T')[0];
}

export default function HabitTracker({ userId, isActive }: HabitTrackerProps) {
  const [habits, setHabits] = useState<Habit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [logging, setLogging] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<{ name: string; why: string }>({ name: '', why: '' });
  const [showAddForm, setShowAddForm] = useState(false);
  const [newHabit, setNewHabit] = useState({ name: '', why: '' });
  const [addingHabit, setAddingHabit] = useState(false);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const today = todayUTC();

  // Initial fetch
  useEffect(() => {
    fetchHabits();
  }, []);

  // Re-fetch whenever the Habits tab becomes active (catches habits created via chat)
  useEffect(() => {
    if (isActive) fetchHabits();
  }, [isActive]);

  async function fetchHabits() {
    setLoading(true);
    setError(false);
    try {
      const res = await fetch(`${API_URL}/habits?userId=${userId}`);
      if (res.ok) setHabits(await res.json());
      else setError(true);
    } catch (e) {
      console.error('Failed to load habits:', e);
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  async function logHabit(habitId: string) {
    if (logging) return;
    setLogging(habitId);
    try {
      const res = await fetch(`${API_URL}/habits/${habitId}/log?userId=${userId}`, { method: 'PATCH' });
      if (res.ok) {
        const updated = await res.json();
        setHabits((prev) => prev.map((h) => (h.id === habitId ? { ...h, ...updated } : h)));
      }
    } catch (e) {
      console.error('Failed to log habit:', e);
    } finally {
      setLogging(null);
    }
  }

  async function unlogHabit(habitId: string) {
    if (logging) return;
    setLogging(habitId);
    try {
      const res = await fetch(`${API_URL}/habits/${habitId}/unlog?userId=${userId}`, { method: 'PATCH' });
      if (res.ok) {
        const updated = await res.json();
        setHabits((prev) => prev.map((h) => (h.id === habitId ? { ...h, ...updated } : h)));
      }
    } catch (e) {
      console.error('Failed to unlog habit:', e);
    } finally {
      setLogging(null);
    }
  }

  async function deleteHabit(habitId: string) {
    try {
      const res = await fetch(`${API_URL}/habits/${habitId}?userId=${userId}`, { method: 'DELETE' });
      if (res.ok) {
        setHabits((prev) => prev.filter((h) => h.id !== habitId));
      } else {
        console.error('Delete failed:', res.status, await res.text());
      }
    } catch (e) {
      console.error('Failed to delete habit:', e);
    } finally {
      setConfirmingId(null);
    }
  }

  function startEdit(habit: Habit) {
    setEditingId(habit.id);
    setEditValues({ name: habit.name, why: habit.why ?? '' });
  }

  async function saveEdit(habitId: string) {
    try {
      const res = await fetch(`${API_URL}/habits/${habitId}?userId=${userId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editValues),
      });
      if (res.ok) {
        const updated = await res.json();
        setHabits((prev) => prev.map((h) => (h.id === habitId ? { ...h, ...updated } : h)));
      }
    } catch (e) {
      console.error('Failed to update habit:', e);
    } finally {
      setEditingId(null);
    }
  }

  async function addHabit() {
    if (!newHabit.name.trim() || !newHabit.why.trim()) return;
    setAddingHabit(true);
    try {
      const res = await fetch(`${API_URL}/habits`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...newHabit, userId }),
      });
      if (res.ok) {
        const created = await res.json();
        setHabits((prev) => [...prev, created]);
        setNewHabit({ name: '', why: '' });
        setShowAddForm(false);
      }
    } catch (e) {
      console.error('Failed to add habit:', e);
    } finally {
      setAddingHabit(false);
    }
  }

  function isDoneToday(habit: Habit): boolean {
    return habit.logs?.includes(today) ?? false;
  }

  if (loading) {
    return (
      <div className="habit-list">
        {[1, 2, 3].map((i) => (
          <div key={i} className="habit-card skeleton" style={{ height: '72px' }} />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="placeholder-tab">
        <span className="placeholder-emoji">⚠️</span>
        <p className="placeholder-title">Couldn't load habits</p>
        <p className="placeholder-sub">Check your connection and try again.</p>
        <button className="suggestion-chip" onClick={fetchHabits} style={{ marginTop: '0.75rem' }}>Retry</button>
      </div>
    );
  }

  const doneCount = habits.filter((h) => isDoneToday(h)).length;
  const total = habits.length;
  const pct = total > 0 ? Math.round((doneCount / total) * 100) : 0;

  return (
    <>
    <div className="habit-list">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <p className="habit-list-date">
          Today · {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
        </p>
        <button
          className="habit-add-btn"
          onClick={() => setShowAddForm((v) => !v)}
          aria-label="Add habit"
          id="add-habit-btn"
        >
          {showAddForm ? '✕' : '＋ Add'}
        </button>
      </div>

      {/* Add habit inline form */}
      {showAddForm && (
        <div className="habit-add-form">
          <input
            className="habit-add-input"
            placeholder="Habit name (e.g. Drink 8 glasses of water)"
            value={newHabit.name}
            onChange={(e) => setNewHabit((v) => ({ ...v, name: e.target.value }))}
            id="new-habit-name"
          />
          <input
            className="habit-add-input"
            placeholder="Why does this matter to you?"
            value={newHabit.why}
            onChange={(e) => setNewHabit((v) => ({ ...v, why: e.target.value }))}
            id="new-habit-why"
          />
          <button
            className="habit-save-btn"
            onClick={addHabit}
            disabled={addingHabit || !newHabit.name.trim() || !newHabit.why.trim()}
          >
            {addingHabit ? 'Adding…' : 'Add Habit'}
          </button>
        </div>
      )}

      {/* Daily progress bar */}
      {total > 0 && (
        <div className="habit-progress-wrap">
          <div className="habit-progress-labels">
            <span className="habit-progress-text">{doneCount} of {total} done today</span>
            <span className="habit-progress-pct">{pct}%</span>
          </div>
          <div className="habit-progress-track">
            <div className="habit-progress-fill" style={{ width: `${pct}%` }} />
          </div>
        </div>
      )}

      {/* Empty state */}
      {habits.length === 0 && !showAddForm && (
        <div className="placeholder-tab">
          <span className="placeholder-emoji">🌱</span>
          <p className="placeholder-title">No habits yet</p>
          <p className="placeholder-sub">
            Tap <strong>+ Add</strong> above to create your first habit, or ask Grove in chat.
          </p>
        </div>
      )}

      {/* Habit cards */}
      {habits.map((habit) => {
        const done = isDoneToday(habit);
        const isLogging = logging === habit.id;
        const isEditing = editingId === habit.id;

        return (
          <div key={habit.id} className={`habit-card ${done ? 'done' : ''}`}>
            {isEditing ? (
              /* Inline edit form */
              <div className="habit-edit-form">
                <input
                  className="habit-add-input"
                  value={editValues.name}
                  onChange={(e) => setEditValues((v) => ({ ...v, name: e.target.value }))}
                  placeholder="Habit name"
                />
                <input
                  className="habit-add-input"
                  value={editValues.why}
                  onChange={(e) => setEditValues((v) => ({ ...v, why: e.target.value }))}
                  placeholder="Why does this matter?"
                />
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button className="habit-save-btn" onClick={() => saveEdit(habit.id)}>Save</button>
                  <button className="habit-cancel-btn" onClick={() => setEditingId(null)}>Cancel</button>
                </div>
              </div>
            ) : (
              <>
                {/* Checkbox */}
                <button
                  className={`habit-check ${done ? 'done' : 'todo'}`}
                  onClick={() => done ? unlogHabit(habit.id) : logHabit(habit.id)}
                  disabled={isLogging}
                  aria-label={done ? `Uncheck ${habit.name}` : `Mark ${habit.name} done`}
                  id={`habit-check-${habit.id}`}
                  title={done ? 'Click to uncheck' : 'Click to mark done'}
                >
                  {isLogging ? '…' : done ? '✓' : ''}
                </button>

                {/* Habit info */}
                <div className="habit-info">
                  <span className="habit-name">{habit.name}</span>
                  {habit.why && <span className="habit-reason">{habit.why}</span>}
                </div>

                {/* Streak + actions */}
                <div className="habit-right">
                  <div className="habit-streak">
                    {habit.currentStreak >= 2 && <span className="streak-fire">🔥</span>}
                    <span className="streak-number">{habit.currentStreak}</span>
                    <span className="streak-label">day{habit.currentStreak !== 1 ? 's' : ''}</span>
                  </div>
                  <div className="habit-actions">
                    {confirmingId === habit.id ? (
                      /* Inline confirm: replaces action buttons */
                      <>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Remove?</span>
                        <button
                          className="habit-action-btn"
                          onClick={() => deleteHabit(habit.id)}
                          title="Confirm delete"
                          aria-label="Confirm delete"
                          id={`habit-delete-confirm-${habit.id}`}
                        >✓</button>
                        <button
                          className="habit-action-btn"
                          onClick={() => setConfirmingId(null)}
                          title="Cancel"
                          aria-label="Cancel delete"
                        >✕</button>
                      </>
                    ) : (
                      <>
                        <button
                          className="habit-action-btn"
                          onClick={() => startEdit(habit)}
                          aria-label={`Edit ${habit.name}`}
                          title="Edit"
                        >✏️</button>
                        <button
                          className="habit-action-btn habit-action-delete"
                          onClick={() => setConfirmingId(habit.id)}
                          aria-label={`Delete ${habit.name}`}
                          title="Delete"
                          id={`habit-delete-${habit.id}`}
                        >🗑️</button>
                      </>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        );
      })}
    </div>

    {/* Grove Habit Coach — embedded below habit list */}
    <HabitCoach habits={habits} userId={userId} />
    </>
  );
}
