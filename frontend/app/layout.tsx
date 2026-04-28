import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'MindFlow — Your calm AI companion',
  description:
    'AI-powered mindfulness, journaling, and habit-tracking assistant. Built with Microsoft Azure AI Foundry, Cosmos DB, and Semantic Kernel.',
  keywords: ['mindfulness', 'journaling', 'habit tracking', 'AI', 'mental wellness'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
