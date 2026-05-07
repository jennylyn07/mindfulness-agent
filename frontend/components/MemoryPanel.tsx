'use client';

import { useEffect, useState } from 'react';

interface MemoryFact {
  id: string;
  content: string;
  source: string;
  importance: number;
  createdAt: string;
  lastReferencedAt: string;
}

interface UserMemory {
  userId: string;
  memoryEnabled: boolean;
  facts: MemoryFact[];
}

interface MemoryPanelProps {
  userId: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export default function MemoryPanel({ userId }: MemoryPanelProps) {
  const [memory, setMemory] = useState<UserMemory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [saving, setSaving] = useState(false);

  const [editingId, setEditingId] = useState<string>('');
  const [draft, setDraft] = useState<string>('');
  const [newFact, setNewFact] = useState<string>('');

  function loadMemory() {
    setLoading(true);
    setError(false);
    fetch(`${API_URL}/memory?userId=${encodeURIComponent(userId)}`)
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then((data) => setMemory(data))
      .catch((e) => { console.error('Failed to load memory:', e); setError(true); })
      .finally(() => setLoading(false));
  }

  async function addFact() {
    if (!newFact.trim()) return;
    setSaving(true);
    try {
      const r = await fetch(`${API_URL}/memory/facts?userId=${encodeURIComponent(userId)}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: newFact.trim(), source: 'manual' }),
        });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const json = await r.json();
      setMemory(json);
      setNewFact('');
    } catch (e) {
      console.error('Failed to add fact:', e);
      setError(true);
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => { loadMemory(); }, [userId]);

  function beginEdit(f: MemoryFact) {
    setEditingId(f.id);
    setDraft(f.content);
  }

  function cancelEdit() {
    setEditingId('');
    setDraft('');
  }

  async function saveEdit(factId: string) {
    setSaving(true);
    try {
      const r = await fetch(`${API_URL}/memory/facts/${encodeURIComponent(factId)}?userId=${encodeURIComponent(userId)}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: draft }),
        });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const json = await r.json();
      setMemory(json);
      cancelEdit();
    } catch (e) {
      console.error('Failed to save fact:', e);
      setError(true);
    } finally {
      setSaving(false);
    }
  }

  async function deleteFact(factId: string) {
    setSaving(true);
    try {
      const r = await fetch(`${API_URL}/memory/facts/${encodeURIComponent(factId)}?userId=${encodeURIComponent(userId)}`,
        { method: 'DELETE' });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const json = await r.json();
      setMemory(json);
      if (editingId === factId) cancelEdit();
    } catch (e) {
      console.error('Failed to delete fact:', e);
      setError(true);
    } finally {
      setSaving(false);
    }
  }

  async function toggle(enabled: boolean) {
    setSaving(true);
    try {
      const r = await fetch(`${API_URL}/memory/toggle?userId=${encodeURIComponent(userId)}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled }),
        });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const json = await r.json();
      setMemory(json);
    } catch (e) {
      console.error('Failed to toggle memory:', e);
      setError(true);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div className="skeleton" style={{ height: '160px', borderRadius: '16px' }} />;
  }

  if (error) {
    return (
      <div className="placeholder-tab">
        <span className="placeholder-emoji">⚠️</span>
        <p className="placeholder-title">Couldn't load memory</p>
        <p className="placeholder-sub">Check your connection and try again.</p>
        <button className="suggestion-chip" onClick={loadMemory} style={{ marginTop: '0.75rem' }}>Retry</button>
      </div>
    );
  }

  if (!memory) {
    return <p className="placeholder-sub">No memory loaded.</p>;
  }

  return (
    <div className="memory-wrap">
      <div className="memory-toggle-row">
        <label className="memory-toggle">
          <input
            type="checkbox"
            checked={!!memory.memoryEnabled}
            onChange={(e) => toggle(e.target.checked)}
            disabled={saving}
          />
          <span className="memory-toggle-label">Remember things about me</span>
        </label>
        {saving && <span className="memory-saving">Saving…</span>}
      </div>

      {!memory.memoryEnabled && (
        <p className="memory-disabled-note">
          Memory is off. Your chats won’t use stored facts, and no new facts will be saved.
        </p>
      )}

      <div className="memory-facts">
        {(memory.facts ?? []).length === 0 ? (
          <p className="memory-empty">No saved facts yet.</p>
        ) : (
          (memory.facts ?? []).map((f) => (
            <div key={f.id} className="memory-fact-row">
              {editingId === f.id ? (
                <textarea
                  className="memory-fact-input"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  rows={2}
                  disabled={saving}
                />
              ) : (
                <p className="memory-fact-text">{f.content}</p>
              )}

              <div className="memory-fact-actions">
                {editingId === f.id ? (
                  <>
                    <button
                      className="memory-btn"
                      onClick={() => saveEdit(f.id)}
                      disabled={saving || !draft.trim()}
                    >
                      Save
                    </button>
                    <button className="memory-btn memory-btn-ghost" onClick={cancelEdit} disabled={saving}>
                      Cancel
                    </button>
                  </>
                ) : (
                  <>
                    <button className="memory-btn" onClick={() => beginEdit(f)} disabled={saving}>
                      Edit
                    </button>
                    <button className="memory-btn memory-btn-danger" onClick={() => deleteFact(f.id)} disabled={saving}>
                      Delete
                    </button>
                  </>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {memory.memoryEnabled && (
        <div className="memory-add">
          <textarea
            className="memory-fact-input"
            value={newFact}
            onChange={(e) => setNewFact(e.target.value)}
            rows={2}
            placeholder="Add something you'd like MindFlow to remember…"
            disabled={saving}
          />
          <button
            className="memory-btn"
            onClick={addFact}
            disabled={saving || !newFact.trim()}
          >
            Add fact
          </button>
        </div>
      )}
    </div>
  );
}
