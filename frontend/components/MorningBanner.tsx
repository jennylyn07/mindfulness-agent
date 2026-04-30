'use client';

import { useState } from 'react';

interface MorningBannerProps {
  name: string;
  onMoodSelect: (mood: string, score: number) => void;
}

const MOODS = [
  { emoji: '😔', label: 'rough',   value: 'rough',   score: 2 },
  { emoji: '😟', label: 'anxious', value: 'anxious', score: 3 },
  { emoji: '😐', label: 'okay',    value: 'okay',    score: 5 },
  { emoji: '🙂', label: 'good',    value: 'good',    score: 7 },
  { emoji: '😊', label: 'great',   value: 'great',   score: 9 },
];

export default function MorningBanner({ name, onMoodSelect }: MorningBannerProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);

  const hour = new Date().getHours();
  const greeting =
    hour >= 5 && hour < 12  ? 'Good morning' :
    hour >= 12 && hour < 17 ? 'Good afternoon' :
    hour >= 17 && hour < 22 ? 'Good evening' :
    hour >= 22               ? 'Hey, it\'s getting late' :
                               'Still going?'; // 0–4 AM

  function handleMoodSelect(mood: { value: string; score: number; label: string }) {
    setSelected(mood.value);
    setTimeout(() => {
      setConfirmed(true);
      setTimeout(() => onMoodSelect(mood.value, mood.score), 800);
    }, 200);
  }

  return (
    <div className={`morning-banner ${confirmed ? 'banner-confirmed' : ''}`}>
      {confirmed ? (
        <div className="banner-toast">
          <span className="banner-toast-icon">✓</span>
          <span>Mood logged — good to hear from you, {name} 🌿</span>
        </div>
      ) : (
        <>
          <p className="morning-greeting">
            {greeting}, <strong>{name}</strong> 🌿
          </p>
          <p className="morning-question">How are you feeling right now?</p>
          <div className="mood-row">
            {MOODS.map((m) => (
              <button
                key={m.value}
                className={`mood-btn ${selected === m.value ? 'selected' : ''}`}
                onClick={() => handleMoodSelect(m)}
                aria-label={m.label}
                disabled={!!selected}
              >
                <span className="mood-emoji">{m.emoji}</span>
                <span className="mood-label">{m.label}</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
