import React from 'react';
import { Database, ShieldAlert, Sparkles, Terminal } from 'lucide-react';

export const DemoBanner: React.FC = () => {
  return (
    <div className="bg-gradient-to-r from-amber-950/40 via-indigo-950/30 to-slate-900 border-b border-amber-900/40 px-4 py-2 text-xs flex flex-wrap items-center justify-between gap-3 text-slate-300 select-none">
      <div className="flex items-center gap-2.5">
        <span className="flex h-2 w-2 relative">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
        </span>
        <span className="font-semibold text-amber-400 tracking-wide font-mono uppercase">
          ● DEMO MODE
        </span>
        <span className="text-slate-500">|</span>
        <span className="text-slate-400">
          Backend connection: <span className="text-slate-300 font-mono">Not configured (Offline Deterministic Mode)</span>
        </span>
      </div>

      <div className="flex items-center gap-4 text-xs font-mono">
        <span className="flex items-center gap-1.5 text-emerald-400/90">
          <Database className="w-3.5 h-3.5" />
          Authoritative Knowledge: <strong className="font-semibold">Company Obsidian</strong>
        </span>
        <span className="hidden md:flex items-center gap-1.5 text-indigo-300/80">
          <Terminal className="w-3.5 h-3.5" />
          SecurityGuard: <strong className="font-semibold">Active</strong>
        </span>
      </div>
    </div>
  );
};
