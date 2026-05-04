'use client';

import { useEffect, useMemo, useState } from 'react';

interface CalendarDay {
  hasJournal: boolean;
  journalId: string;
  journalMood: string;
  journalThemes: string[];
  mood: number | null;
  moodLabel: string | null;
  habitsCompleted: number;
  habitsTotal: number;
}

type CalendarResponse = Record<string, CalendarDay>;

interface CalendarViewProps {
  userId: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

function pad2(n: number): string {
  return String(n).padStart(2, '0');
}

function ymd(d: Date): string {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

function startOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

function endOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth() + 1, 0);
}

function isSameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

export default function CalendarView({ userId }: CalendarViewProps) {
  const [month, setMonth] = useState<Date>(() => startOfMonth(new Date()));
  const [data, setData] = useState<CalendarResponse>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [selected, setSelected] = useState<string>('');

  const monthStart = useMemo(() => startOfMonth(month), [month]);
  const monthEnd = useMemo(() => endOfMonth(month), [month]);

  useEffect(() => {
    setLoading(true);
    setError(false);

    const start = ymd(monthStart);
    const end = ymd(monthEnd);

    fetch(`${API_URL}/calendar?userId=${encodeURIComponent(userId)}&start=${start}&end=${end}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((json: CalendarResponse) => {
        setData(json ?? {});
        const todayKey = ymd(new Date());
        if (json?.[todayKey]) setSelected(todayKey);
        else setSelected(start);
      })
      .catch((e) => {
        console.error('Failed to load calendar:', e);
        setError(true);
      })
      .finally(() => setLoading(false));
  }, [userId, monthStart.getFullYear(), monthStart.getMonth()]);

  const gridDays = useMemo(() => {
    const first = monthStart;
    const last = monthEnd;

    // Sunday-start grid
    const start = new Date(first);
    start.setDate(first.getDate() - first.getDay());

    const end = new Date(last);
    end.setDate(last.getDate() + (6 - last.getDay()));

    const days: Date[] = [];
    const cur = new Date(start);
    while (cur <= end) {
      days.push(new Date(cur));
      cur.setDate(cur.getDate() + 1);
    }

    // Always show 6 rows for stability
    while (days.length < 42) {
      const next = new Date(days[days.length - 1]);
      next.setDate(next.getDate() + 1);
      days.push(next);
    }

    return days;
  }, [monthStart.getTime(), monthEnd.getTime()]);

  const selectedDay = selected ? data[selected] : null;
  const today = new Date();

  function prevMonth() {
    setMonth((m) => startOfMonth(new Date(m.getFullYear(), m.getMonth() - 1, 1)));
  }

  function nextMonth() {
    setMonth((m) => startOfMonth(new Date(m.getFullYear(), m.getMonth() + 1, 1)));
  }

  const headerLabel = monthStart.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

  if (loading) {
    return (
      <div className="calendar-wrap">
        <div className="skeleton" style={{ height: '280px', borderRadius: '16px' }} />
        <div className="skeleton" style={{ height: '92px', borderRadius: '16px', marginTop: '0.75rem' }} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="calendar-wrap">
        <div className="placeholder-tab">
          <span className="placeholder-emoji">⚠️</span>
          <p className="placeholder-title">Couldn't load calendar</p>
          <p className="placeholder-sub">Check your connection and try again.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="calendar-wrap">
      <div className="calendar-card">
        <div className="calendar-header">
          <button className="calendar-nav-btn" onClick={prevMonth} aria-label="Previous month">‹</button>
          <p className="calendar-month">{headerLabel}</p>
          <button className="calendar-nav-btn" onClick={nextMonth} aria-label="Next month">›</button>
        </div>

        <div className="calendar-weekdays">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((w) => (
            <span key={w} className="calendar-weekday">{w}</span>
          ))}
        </div>

        <div className="calendar-grid" role="grid" aria-label="Monthly activity calendar">
          {gridDays.map((d) => {
            const key = ymd(d);
            const inMonth = d.getMonth() === monthStart.getMonth();
            const dayData = data[key];
            const isToday = isSameDay(d, today);
            const isSelected = selected === key;

            const hasJournal = !!dayData?.hasJournal;
            const hasMood = dayData?.mood !== null && dayData?.mood !== undefined;
            const showHabits = (dayData?.habitsTotal ?? 0) > 0 && (dayData?.habitsCompleted ?? 0) > 0;

            return (
              <button
                key={key}
                className={
                  `calendar-cell ${inMonth ? '' : 'calendar-cell-out'} ` +
                  `${isToday ? 'calendar-cell-today' : ''} ` +
                  `${isSelected ? 'calendar-cell-selected' : ''}`
                }
                onClick={() => setSelected(key)}
                role="gridcell"
                aria-label={key}
              >
                <span className="calendar-date-num">{d.getDate()}</span>

                <div className="calendar-meta">
                  <div className="calendar-dots" aria-label="Activity indicators">
                    {hasJournal && <span className="calendar-dot calendar-dot-journal" aria-label="Journal entry" />}
                    {hasMood && <span className="calendar-dot calendar-dot-mood" aria-label="Mood logged" />}
                  </div>
                  {showHabits && (
                    <span className="calendar-habits-pill" aria-label="Habits completed">
                      {dayData.habitsCompleted}/{dayData.habitsTotal}
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="calendar-detail insights-card">
        <p className="insights-section-label" style={{ marginBottom: '0.4rem' }}>
          {selected || 'Day details'}
        </p>

        {!selectedDay ? (
          <p className="calendar-detail-empty">No activity recorded.</p>
        ) : (
          <div className="calendar-detail-rows">
            <div className="calendar-detail-row">
              <span className="calendar-detail-key">Journal</span>
              <span className="calendar-detail-val">
                {selectedDay.hasJournal
                  ? `${selectedDay.journalMood || '—'}${selectedDay.journalThemes?.length ? ` · ${selectedDay.journalThemes.join(', ')}` : ''}`
                  : '—'}
              </span>
            </div>

            <div className="calendar-detail-row">
              <span className="calendar-detail-key">Mood</span>
              <span className="calendar-detail-val">
                {selectedDay.mood !== null && selectedDay.mood !== undefined
                  ? `${selectedDay.moodLabel ?? 'mood'} · ${selectedDay.mood}/10`
                  : '—'}
              </span>
            </div>

            <div className="calendar-detail-row">
              <span className="calendar-detail-key">Habits</span>
              <span className="calendar-detail-val">
                {(selectedDay.habitsTotal ?? 0) > 0
                  ? `${selectedDay.habitsCompleted}/${selectedDay.habitsTotal}`
                  : '—'}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
