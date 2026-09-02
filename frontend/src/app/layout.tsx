import React from 'react';
import '@/app/globals.css';
import { Shell } from '@/components/layout/Shell';

export const metadata = {
  title: 'Master Orchestrator — Autonomous AI Workforce Control Plane',
  description: 'Enterprise developer control plane and execution observability platform for autonomous multi-agent systems.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="h-full bg-space-950 text-slate-100 font-sans selection:bg-emerald-500/30 selection:text-emerald-200">
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}

