'use client';
/**
 * HabitCoach — Grove Messenger-style chat head.
 * FAB always visible. Panel floats above it. Opening message = same as nudge bubble.
 */
import React, { useState, useRef, useEffect } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Habit {
  id: string;
  name: string;
  currentStreak: number;
  logs: string[];
}

interface Message {
  role: 'grove' | 'user';
  text: string;
}

function todayUTC() {
  return new Date().toISOString().slice(0, 10);
}

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

const FALLBACK_NUDGES = [
  "How are your habits sitting with you today?",
  "Grove is here if you want to talk through your practice.",
  "Any habit feeling harder than usual lately?",
];

async function fetchNudge(userId: string): Promise<string> {
  const today = todayUTC();
  const cacheKey = `grove_nudge_${userId}_${today}`;

  try {
    const cached = sessionStorage.getItem(cacheKey);
    if (cached) {
      const { nudge, ts } = JSON.parse(cached);
      if ((Date.now() - ts) / 60000 < 60) return nudge;
    }
  } catch { /* unavailable */ }

  try {
    const res = await fetch(`${API_URL}/grove/nudge?userId=${userId}`);
    if (res.ok) {
      const data = await res.json();
      const nudge = data.nudge || pick(FALLBACK_NUDGES);
      try { sessionStorage.setItem(cacheKey, JSON.stringify({ nudge, ts: Date.now() })); } catch { /* quota */ }
      return nudge;
    }
  } catch { /* network */ }

  return pick(FALLBACK_NUDGES);
}

export default function HabitCoach({ habits, userId }: { habits: Habit[]; userId: string }) {
  const [isOpen,       setIsOpen]       = useState(false);
  const [nudgeMsg,     setNudgeMsg]     = useState<string | null>(null);
  const [showNudge,    setShowNudge]    = useState(false);
  const [messages,     setMessages]     = useState<Message[]>([]);
  const [input,        setInput]        = useState('');
  const [streaming,    setStreaming]    = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLInputElement>(null);

  // Fetch nudge once, show bubble 1s later, auto-dismiss after 9s
  useEffect(() => {
    if (!habits.length) return;
    let cancelled = false;

    fetchNudge(userId).then((msg) => {
      if (cancelled) return;
      setNudgeMsg(msg);
      const showT = setTimeout(() => { if (!cancelled) setShowNudge(true); }, 1000);
      const hideT = setTimeout(() => { if (!cancelled) setShowNudge(false); }, 10000);
      return () => { clearTimeout(showT); clearTimeout(hideT); };
    });

    return () => { cancelled = true; };
  }, [habits.length]);

  // When panel opens, seed the chat with the SAME nudge message (or a fallback)
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      const opener = nudgeMsg || pick(FALLBACK_NUDGES);
      setMessages([{ role: 'grove', text: opener }]);
      setTimeout(() => inputRef.current?.focus(), 80);
    }
  }, [isOpen]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function openChat() {
    setIsOpen(true);
    setShowNudge(false);
  }

  function closeChat() {
    setIsOpen(false);
  }

  async function send() {
    const text = input.trim();
    if (!text || streaming) return;
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', text }]);
    setStreaming(true);
    setMessages((prev) => [...prev, { role: 'grove', text: '' }]);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, userId, agentOverride: 'habit', conversationHistory: [] }),
      });
      if (!res.body) throw new Error('No body');
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let first = true;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        let chunk = decoder.decode(value, { stream: true });
        if (first) { chunk = chunk.replace(/^\[AGENT:[^\]]+\]\n?/, ''); first = false; if (!chunk) continue; }
        setMessages((prev) => {
          const c = [...prev];
          c[c.length - 1] = { ...c[c.length - 1], text: c[c.length - 1].text + chunk };
          return c;
        });
      }
    } catch {
      setMessages((prev) => {
        const c = [...prev];
        c[c.length - 1] = { ...c[c.length - 1], text: "Couldn't connect right now. Try again in a moment." };
        return c;
      });
    } finally {
      setStreaming(false);
      inputRef.current?.focus();
    }
  }

  return (
    <div className="grove-float-root">
      {/* ── Inner anchor for absolute positioning ─── */}
      <div className="grove-float-inner">

        {/* Chat panel — floats above FAB */}
        {isOpen && (
          <div className="grove-float-panel" role="dialog" aria-label="Grove habit coach">
            <div className="grove-float-header">
              <span className="grove-float-avatar-sm" aria-hidden>🌿</span>
              <div className="grove-float-title-block">
                <span className="grove-float-name">Grove</span>
                <span className="grove-float-sub">Habit Coach</span>
              </div>
              <button className="grove-float-close" onClick={closeChat} aria-label="Close Grove">✕</button>
            </div>

            <div className="grove-float-messages" aria-live="polite">
              {messages.map((msg, i) => (
                <div key={i} className={`grove-float-bubble grove-float-bubble--${msg.role}`}>
                  {msg.text}
                  {msg.role === 'grove' && streaming && i === messages.length - 1 && (
                    <span className="grove-float-cursor" aria-hidden>▌</span>
                  )}
                </div>
              ))}
              <div ref={bottomRef} />
            </div>

            <div className="grove-float-input-row">
              <input
                ref={inputRef}
                className="grove-float-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send()}
                placeholder="Reply to Grove…"
                disabled={streaming}
                aria-label="Message Grove"
                id="grove-chat-input"
              />
              <button className="grove-float-send" onClick={send} disabled={streaming || !input.trim()} aria-label="Send">
                {streaming ? '…' : '↑'}
              </button>
            </div>
          </div>
        )}

        {/* DM nudge bubble — to the right of the FAB */}
        {!isOpen && showNudge && nudgeMsg && (
          <div className="grove-dm-wrap">
            <div className="grove-dm-bubble" onClick={openChat} role="button" tabIndex={0}
                 onKeyDown={(e) => e.key === 'Enter' && openChat()}>
              <span className="grove-dm-text">{nudgeMsg}</span>
            </div>
            <button
              className="grove-dm-dismiss"
              onClick={(e) => { e.stopPropagation(); setShowNudge(false); }}
              aria-label="Dismiss"
            >✕</button>
          </div>
        )}

        {/* FAB — always visible, Messenger-style circular avatar */}
        <button
          className={`grove-fab ${isOpen ? 'grove-fab--active' : ''}`}
          onClick={() => isOpen ? closeChat() : openChat()}
          aria-label={isOpen ? 'Close Grove' : 'Open Grove habit coach'}
          id="grove-fab-btn"
        >
          🌿
        </button>
      </div>
    </div>
  );
}
