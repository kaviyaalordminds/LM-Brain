'use client';

import React from 'react';
import { Cpu, HardDrive, Database, Users, Activity, Play } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

interface StatusBarProps {
  activeTaskText?: string;
  activeAgentsCount?: number;
  progress?: number;
  isPlaying?: boolean;
}

export function StatusBar({
  activeTaskText = "Idle",
  activeAgentsCount = 0,
  progress = 0,
  isPlaying = false
}: StatusBarProps) {
  return (
    <footer className="h-10 bg-[#070b13] border-t border-slate-800 flex items-center justify-between px-4 text-xs font-mono text-slate-400 select-none z-10 shrink-0">
      {/* Left side: System status lights */}
      <div className="flex items-center gap-6 overflow-x-auto scrollbar-none whitespace-nowrap">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-[10px] text-slate-300">LOCAL AI:</span>
          <span className="text-[10px] text-emerald-400 font-semibold uppercase">Online (9 Loaded)</span>
        </div>

        <div className="flex items-center gap-2">
          <Cpu className="h-3.5 w-3.5 text-indigo-400" />
          <span className="text-[10px] text-slate-300">GPU:</span>
          <span className="text-[10px] text-indigo-400 font-semibold uppercase">RTX 4090 (Available)</span>
        </div>

        <div className="flex items-center gap-2">
          <Activity className="h-3.5 w-3.5 text-blue-400 animate-pulse-slow" />
          <span className="text-[10px] text-slate-300">ORCHESTRATOR:</span>
          <span className={cn(
            "text-[10px] font-semibold uppercase",
            isPlaying ? "text-indigo-400" : "text-slate-400"
          )}>
            {isPlaying ? "Executing Workflow" : "Ready"}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Database className="h-3.5 w-3.5 text-indigo-400" />
          <span className="text-[10px] text-slate-300">OBSIDIAN:</span>
          <span className="text-[10px] text-amber-400 font-semibold uppercase">Sync Pending (Local Vault)</span>
        </div>
      </div>

      {/* Middle/Right: Running task progress if active */}
      <div className="flex items-center gap-6 shrink-0 ml-4">
        {isPlaying && (
          <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 px-3 py-1 rounded">
            <div className="flex items-center gap-1.5 text-indigo-400">
              <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-ping"></span>
              <span className="text-[10px] uppercase font-bold">Task Running:</span>
            </div>
            <span className="text-[10px] text-slate-200 max-w-[200px] truncate">{activeTaskText}</span>
            <div className="w-16 bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-indigo-500 h-full transition-all duration-300" style={{ width: `${progress}%` }}></div>
            </div>
            <span className="text-[10px] font-bold text-slate-200">{progress}%</span>
          </div>
        )}

        <div className="flex items-center gap-2 text-slate-400">
          <Users className="h-3.5 w-3.5 text-indigo-400" />
          <span>Active Agents:</span>
          <span className="font-semibold text-slate-200">{activeAgentsCount}</span>
        </div>
      </div>
    </footer>
  );
}
