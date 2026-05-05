'use client';

import { useState, useRef, useEffect } from 'react';
import AgentBadge from './AgentBadge';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  agent?: string;
}

interface ChatWindowProps {
  userId: string;
  presetMessage?: string | null;
  onPresetConsumed?: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const AGENT_PREFIX_RE = /^\[AGENT:(\w+)\]\n?/;

const SUGGESTIONS = [
  "I've been feeling anxious about a big presentation tomorrow",
  'I want to journal about my day',
  'Help me with a breathing exercise',
  'What patterns do you see in my journal entries?',
];

export default function ChatWindow({ userId, presetMessage, onPresetConsumed }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [isClassifying, setIsClassifying] = useState(false);
  const [currentAgent, setCurrentAgent] = useState('journal');
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-send preset message (from Lumen button or low-mood Sage prompt)
  useEffect(() => {
    if (!presetMessage) return;
    const msg = presetMessage; // capture before any re-render
    const t = setTimeout(() => {
      onPresetConsumed?.(); // consume AFTER firing — prevents React cleanup from cancelling the timeout
      sendMessage(msg);
    }, 150);
    return () => clearTimeout(t);
  }, [presetMessage]);

  const conversationHistory = messages.map((m) => ({
    role: m.role,
    content: m.content,
  }));

  async function sendMessage(text: string) {
    if (!text.trim() || streaming) return;
    const userMessage = text.trim();
    setInput('');
    // Reset textarea height
    if (inputRef.current) inputRef.current.style.height = '24px';

    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setMessages((prev) => [...prev, { role: 'assistant', content: '', agent: 'journal' }]);
    setStreaming(true);
    setIsClassifying(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          userId,
          conversationHistory,
        }),
      });

      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = '';
      let detectedAgent = 'journal';
      let firstChunk = true;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        let chunk = decoder.decode(value, { stream: true });

        // Parse [AGENT:xxx] prefix from first chunk — settle the routing flash
        if (firstChunk) {
          firstChunk = false;
          const match = AGENT_PREFIX_RE.exec(chunk);
          if (match) {
            detectedAgent = match[1];
            setCurrentAgent(detectedAgent);
            chunk = chunk.replace(AGENT_PREFIX_RE, '');
          }
          setIsClassifying(false);
        }

        accumulated += chunk;

        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: 'assistant',
            content: accumulated,
            agent: detectedAgent,
          };
          return updated;
        });
      }
    } catch (err) {
      console.error('[ChatWindow] stream error:', err);
      setIsClassifying(false);
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: 'assistant',
          content: 'Something went wrong. Please try again.',
          agent: 'journal',
        };
        return updated;
      });
    } finally {
      setStreaming(false);
      setIsClassifying(false);
      inputRef.current?.focus();
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  return (
    <div className="chat-window">
      {/* Empty state */}
      {messages.length === 0 && (
        <div className="chat-empty">
          <p className="chat-empty-title">What&apos;s on your mind?</p>
          <p className="chat-empty-sub">
            Your thoughts are safe here. Start typing or choose a prompt below.
          </p>
          <div className="suggestions">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                className="suggestion-chip"
                onClick={() => sendMessage(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message-row ${msg.role}`}>
            {msg.role === 'assistant' && (
              isClassifying && i === messages.length - 1 ? (
                <span className="agent-badge routing-flash">
                  <span className="routing-dot" /> routing…
                </span>
              ) : (
                <AgentBadge
                  agent={msg.agent ?? 'journal'}
                  streaming={streaming && i === messages.length - 1}
                />
              )
            )}
            <div className={`bubble ${msg.role}`}>
              {msg.content || (streaming && i === messages.length - 1 ? (
                <span className="typing-indicator">
                  <span /><span /><span />
                </span>
              ) : null)}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="chat-input-row">
        <textarea
          ref={inputRef}
          className="chat-input"
          placeholder="Share what's on your mind…"
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            // Auto-resize
            const el = e.target;
            el.style.height = 'auto';
            el.style.height = Math.min(el.scrollHeight, 120) + 'px';
          }}
          onKeyDown={handleKeyDown}
          rows={1}
          style={{ height: '24px' }}
          disabled={streaming}
          id="chat-input"
        />
        <button
          className="send-btn"
          onClick={() => sendMessage(input)}
          disabled={!input.trim() || streaming}
          aria-label="Send message"
          id="send-btn"
        >
          {streaming ? (
            <span className="typing-indicator small">
              <span /><span /><span />
            </span>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}
