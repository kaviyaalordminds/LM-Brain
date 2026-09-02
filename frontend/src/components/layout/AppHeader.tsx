'use client';

import React from 'react';
import { useSystemHealth } from '../../hooks/useSystemHealth';
import { NavigationDock } from './NavigationDock';
import { Terminal, Search, ShieldCheck, Database, HardDrive, Cpu, Brain } from 'lucide-react';

interface AppHeaderProps {
  onOpenCommandPalette?: () => void;
  activeExecutionId?: string | null;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  onOpenCommandPalette,
  activeExecutionId,
}) => {
  const health = useSystemHealth(6000);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-space-800 bg-space-950/95 backdrop-blur-md">
      {/* Top Status & Brand Strip */}
      <div className="flex flex-wrap items-center justify-between px-4 py-2 gap-3 border-b border-space-850/80">
        {/* Left: Brand Identity */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded bg-space-850 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-mono font-bold text-sm">
              Ω
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono-tech text-xs font-bold text-slate-100 tracking-wider">
                  MASTER ORCHESTRATOR
                </span>
                <span className="text-[9px] font-mono-tech px-1.5 py-0.5 rounded bg-space-800 text-slate-400 border border-space-700">
                  CONTROL PLANE v1.0
                </span>
              </div>
              <div className="text-[10px] text-slate-500 font-mono-tech">
                AUTONOMOUS MULTI-AGENT WORKFORCE
              </div>
            </div>
          </div>
        </div>

        {/* Center: Live Operational Status Strip (NO FAKE DATA) */}
        <div className="flex items-center gap-2 overflow-x-auto text-[11px] font-mono-tech py-0.5">
          {/* Master */}
          <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-space-900 border border-space-800">
            <span
              className={`w-2 h-2 rounded-full ${
                health.master === 'UP' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
              }`}
            />
            <span className="text-slate-400">MASTER:</span>
            <span className={health.master === 'UP' ? 'text-emerald-400' : 'text-rose-400'}>
              {health.master === 'UP' ? 'ONLINE' : 'OFFLINE'}
            </span>
          </div>

          {/* Planner */}
          <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-space-900 border border-space-800">
            <Cpu className="w-3 h-3 text-slate-400" />
            <span className="text-slate-400">PLANNER:</span>
            <span className={health.planner === 'UP' ? 'text-emerald-400' : 'text-slate-500'}>
              {health.planner}
            </span>
          </div>

          {/* Memory */}
          <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-space-900 border border-space-800">
            <Brain className="w-3 h-3 text-slate-400" />
            <span className="text-slate-400">MEMORY:</span>
            <span className={health.memory === 'UP' ? 'text-emerald-400' : 'text-slate-500'}>
              {health.memory}
            </span>
          </div>

          {/* Persistence */}
          <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-space-900 border border-space-800">
            <Database className="w-3 h-3 text-slate-400" />
            <span className="text-slate-400">PERSISTENCE:</span>
            <span className="text-slate-300">SQLite</span>
          </div>
        </div>

        {/* Right: Quick Command Bar Trigger */}
        <div className="flex items-center gap-2">
          {activeExecutionId && (
            <div className="hidden sm:flex items-center gap-1.5 px-2 py-1 rounded bg-space-900 border border-space-800 text-[11px] font-mono-tech text-slate-300">
              <span className="text-slate-500">EXEC:</span>
              <span className="text-emerald-400">{activeExecutionId.slice(0, 8)}...</span>
            </div>
          )}

          <button
            onClick={onOpenCommandPalette}
            className="flex items-center gap-2 px-2.5 py-1 text-xs font-mono-tech bg-space-900 hover:bg-space-800 text-slate-300 hover:text-slate-100 border border-space-800 rounded transition-colors"
            title="Open Command Palette"
          >
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <span className="hidden md:inline text-[11px]">Command</span>
            <kbd className="px-1.5 py-0.2 text-[9px] bg-space-800 border border-space-700 rounded text-slate-400 font-mono">
              Ctrl K
            </kbd>
          </button>
        </div>
      </div>

      {/* Main Navigation Bar */}
      <div className="flex items-center justify-between px-4 py-1.5 bg-space-950/80">
        <NavigationDock />
      </div>
    </header>
  );
};
