'use client';

import React, { useState } from 'react';
import { AppHeader } from './AppHeader';
import { CommandPalette } from '../command/CommandPalette';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';

interface ShellProps {
  children: React.ReactNode;
}

export const Shell: React.FC<ShellProps> = ({ children }) => {
  const [isCommandOpen, setIsCommandOpen] = useState(false);
  const [activeExecId, setActiveExecId] = useState<string | null>(null);

  useKeyboardShortcuts({
    onOpenCommandPalette: () => setIsCommandOpen(true),
    onEscape: () => setIsCommandOpen(false),
  });

  return (
    <div className="min-h-screen bg-space-950 text-slate-100 flex flex-col antialiased">
      <AppHeader
        onOpenCommandPalette={() => setIsCommandOpen(true)}
        activeExecutionId={activeExecId}
      />
      <main className="flex-1 w-full max-w-7xl mx-auto p-4 sm:p-6 flex flex-col">
        {children}
      </main>
      <CommandPalette
        isOpen={isCommandOpen}
        onClose={() => setIsCommandOpen(false)}
        activeExecutionId={activeExecId}
      />
    </div>
  );
};
