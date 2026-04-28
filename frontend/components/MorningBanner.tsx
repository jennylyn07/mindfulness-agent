'use client';

interface MorningBannerProps {
  name: string;
  onMoodSelect: (mood: string, score: number) => void;
}

const MOODS = [
  { label: '😰', value: 'anxious', score: 2 },
  { label: '😔', value: 'sad',     score: 3 },
  { label: '😐', value: 'okay',    score: 5 },
  { label: '🙂', value: 'good',    score: 7 },
  { label: '😊', value: 'great',   score: 9 },
];

export default function MorningBanner({ name, onMoodSelect }: MorningBannerProps) {
  const hour = new Date().getHours();
  const greeting =
    hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  return (
    <div className="morning-banner">
      <p className="morning-greeting">
        {greeting}, <strong>{name}</strong> 🌿
      </p>
      <p className="morning-question">How are you feeling right now?</p>
      <div className="mood-row">
        {MOODS.map((m) => (
          <button
            key={m.value}
            className="mood-btn"
            onClick={() => onMoodSelect(m.value, m.score)}
            aria-label={m.value}
            title={m.value}
          >
            {m.label}
          </button>
        ))}
      </div>
    </div>
  );
}
