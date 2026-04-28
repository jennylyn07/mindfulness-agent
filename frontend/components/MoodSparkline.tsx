'use client';

interface MoodLog {
  score: number;
  mood: string;
  timestamp: string;
}

interface MoodSparklineProps {
  logs: MoodLog[];
}

const MOOD_COLORS: Record<string, string> = {
  anxious: '#E8854A',
  sad:     '#9B8EC4',
  okay:    '#8A9E94',
  good:    '#7BA08A',
  great:   '#4E7A62',
};

export default function MoodSparkline({ logs }: MoodSparklineProps) {
  if (!logs || logs.length === 0) {
    return (
      <div className="sparkline-empty">
        <p>No mood data yet — tap an emoji in the morning banner to start.</p>
      </div>
    );
  }

  const sorted = [...logs].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  const W = 300;
  const H = 60;
  const PAD = 8;
  const innerW = W - PAD * 2;
  const innerH = H - PAD * 2;

  const scores = sorted.map((l) => l.score ?? 5);
  const minS = Math.min(...scores, 1);
  const maxS = Math.max(...scores, 10);
  const range = maxS - minS || 1;

  const points = sorted.map((log, i) => {
    const x = PAD + (i / Math.max(sorted.length - 1, 1)) * innerW;
    const y = PAD + innerH - ((( log.score ?? 5) - minS) / range) * innerH;
    return { x, y, log };
  });

  const pathD = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(' ');

  const lastLog = sorted[sorted.length - 1];
  const lastColor = MOOD_COLORS[lastLog?.mood] ?? 'var(--sage)';

  return (
    <div className="sparkline-wrap">
      <div className="sparkline-header">
        <span className="sparkline-title">Mood · 14 days</span>
        <span className="sparkline-current" style={{ color: lastColor }}>
          {lastLog?.mood ?? '—'}
        </span>
      </div>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="sparkline-svg"
        aria-label="Mood trend over 14 days"
      >
        {/* Area fill */}
        <defs>
          <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--sage)" stopOpacity="0.25" />
            <stop offset="100%" stopColor="var(--sage)" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path
          d={`${pathD} L ${points[points.length - 1].x} ${H} L ${points[0].x} ${H} Z`}
          fill="url(#sparkGrad)"
        />
        {/* Line */}
        <path
          d={pathD}
          fill="none"
          stroke="var(--sage)"
          strokeWidth="2"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {/* Dots */}
        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={i === points.length - 1 ? 4 : 2.5}
            fill={MOOD_COLORS[p.log.mood] ?? 'var(--sage)'}
          />
        ))}
      </svg>
    </div>
  );
}
