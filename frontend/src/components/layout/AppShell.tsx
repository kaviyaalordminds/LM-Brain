'use client';

import React, { useState } from 'react';
import { useSimulation } from '@/lib/context/SimulationContext';
import { Sidebar } from '@/components/layout/Sidebar';
import { StatusBar } from '@/components/layout/StatusBar';
import { RightPanel } from '@/components/layout/RightPanel';

export function AppShell({ children }: { children: React.ReactNode }) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const { isPlaying, progress, activeProject, agents } = useSimulation();

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-[#090d16] text-slate-100">
      {/* Upper part containing sidebar, main, and right panel */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar isCollapsed={isSidebarCollapsed} setIsCollapsed={setIsSidebarCollapsed} />
        
        {/* Main Content Area */}
        <main className="flex-1 flex flex-col overflow-hidden bg-[#090d16] relative">
          <div className="flex-1 overflow-y-auto">
            {children}
          </div>
        </main>

        {/* Right context panel */}
        <RightPanel />
      </div>

      {/* Global Status Bar */}
      <StatusBar
        activeTaskText={activeProject ? activeProject.name : "Idle"}
        activeAgentsCount={agents.filter(a => a.status === 'running' || a.status === 'spawn' || a.status === 'retry' || a.status === 'reflect').length}
        progress={progress}
        isPlaying={isPlaying}
      />
    </div>
  );
}
