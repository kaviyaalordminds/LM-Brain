import React from 'react';
import { SimulationProvider } from '@/lib/context/SimulationContext';
import { AppShell } from '@/components/layout/AppShell';
import '@/app/globals.css';

export const metadata = {
  title: 'Autonomous AI Workforce',
  description: 'Premium enterprise operating system for autonomous agents workforce.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full">
      <body className="h-full bg-[#090d16] text-slate-100 overflow-hidden">
        <SimulationProvider>
          <AppShell>{children}</AppShell>
        </SimulationProvider>
      </body>
    </html>
  );
}
