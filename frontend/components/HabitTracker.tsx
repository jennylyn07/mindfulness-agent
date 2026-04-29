'use client';

import { useState, useEffect } from 'react';

interface Habit {
  id: string;
  name: string;
  icon: string;
  reason: string;
  streak: number;
  logs: string[];
}

interface HabitTrackerProps {
  userId: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

function todayUTC(): string {
  return new Date().toISOString().split('T')[0];
}

export default function HabitTracker({ userId }: HabitTrackerProps) {
  const [habits, setHabits] = useState<Habit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [logging, setLogging] = useState<string | null>(null);
  const today = todayUTC();

  useEffect(() => {
    fetchHabits();
  }, []);

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
      const res = await fetch(`${API_URL}/habits/${habitId}/log?userId=${userId}`, {
        method: 'PATCH',
      });
      if (res.ok) {
        const updated = await res.json();
        setHabits((prev) =>
          prev.map((h) => (h.id === habitId ? { ...h, ...updated } : h))
        );
      }
    } catch (e) {
      console.error('Failed to log habit:', e);
    } finally {
      setLogging(null);
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

  if (habits.length === 0) {
    return (
      <div className="placeholder-tab">
        <span className="placeholder-emoji">🌱</span>
        <p className="placeholder-title">No habits yet</p>
        <p className="placeholder-sub">
          Tell Grove about a habit you want to build — it will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="habit-list">
      <p className="habit-list-date">Today · {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}</p>
      {habits.map((habit) => {
        const done = isDoneToday(habit);
        const isLogging = logging === habit.id;
        return (
          <div key={habit.id} className={`habit-card ${done ? 'done' : ''}`}>
            <button
              className={`habit-check ${done ? 'done' : 'todo'}`}
              onClick={() => !done && logHabit(habit.id)}
              disabled={done || isLogging}
              aria-label={done ? `${habit.name} completed` : `Mark ${habit.name} done`}
              id={`habit-check-${habit.id}`}
            >
              {done ? '✓' : isLogging ? '…' : ''}
            </button>
            <div className="habit-info">
              <span className="habit-name">
                {habit.icon ?? '🌿'} {habit.name}
              </span>
              {habit.reason && (
                <span className="habit-reason">{habit.reason}</span>
              )}
            </div>
            <div className="habit-streak">
              <span className="streak-number">{habit.streak}</span>
              <span className="streak-label">day{habit.streak !== 1 ? 's' : ''}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
