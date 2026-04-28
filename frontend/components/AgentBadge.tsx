'use client';

interface AgentBadgeProps {
  agent: string;
  streaming?: boolean;
}

const AGENTS: Record<string, { label: string; emoji: string; color: string }> = {
  mindfulness: { label: 'Sage', emoji: '🌿', color: 'var(--sage)' },
  journal:     { label: 'River', emoji: '📖', color: 'var(--lavender)' },
  habit:       { label: 'Grove', emoji: '🌱', color: 'var(--sky)' },
  insights:    { label: 'Lumen', emoji: '✨', color: 'var(--accent)' },
};

export default function AgentBadge({ agent, streaming = false }: AgentBadgeProps) {
  const info = AGENTS[agent] ?? AGENTS.journal;

  return (
    <span
      className="agent-badge"
      style={{ '--agent-color': info.color } as React.CSSProperties}
    >
      {info.emoji} {info.label}
      {streaming && <span className="agent-badge-dot" />}
    </span>
  );
}
