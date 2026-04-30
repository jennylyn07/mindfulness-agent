'use client';

interface AgentBadgeProps {
  agent: string;
  streaming?: boolean;
}

const AGENTS: Record<string, { persona: string; role: string; emoji: string; color: string }> = {
  mindfulness: { persona: 'Sage',  role: 'Mindfulness Coach', emoji: '🌿', color: 'var(--sage)' },
  journal:     { persona: 'River', role: 'Journal Agent',     emoji: '📓', color: 'var(--lavender)' },
  habit:       { persona: 'Grove', role: 'Habit Coach',       emoji: '✅', color: 'var(--accent)' },
  insights:    { persona: 'Lumen', role: 'Insights',          emoji: '📊', color: 'var(--sky)' },
};

export default function AgentBadge({ agent, streaming = false }: AgentBadgeProps) {
  const info = AGENTS[agent] ?? AGENTS.journal;

  return (
    <span
      className="agent-badge"
      style={{ '--agent-color': info.color } as React.CSSProperties}
    >
      <span className="agent-badge-primary">
        {info.emoji} {info.persona}
        {streaming && <span className="agent-badge-dot" />}
      </span>
      <span className="agent-badge-role">{info.role}</span>
    </span>
  );
}
