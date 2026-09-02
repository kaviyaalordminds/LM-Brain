'use client';

import React from 'react';
import { ShieldCheck, Server, Key, Radio } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export function Header({ title, subtitle }: HeaderProps) {
  return (
    <header className="h-16 border-b border-slate-800 bg-[#090d16] flex items-center justify-between px-6 shrink-0 select-none">
      <div className="flex flex-col min-w-0">
        <h1 className="text-lg font-bold text-slate-100 uppercase tracking-wider truncate">
          {title}
        </h1>
        {subtitle && (
          <p className="text-xs text-slate-400 font-mono tracking-tight truncate">
            {subtitle}
          </p>
        )}
      </div>

      {/* Right controls - Quick Info Pills */}
      <div className="flex items-center gap-3">
        {/* Shield status */}
        <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-xs font-mono">
          <ShieldCheck className="h-4 w-4 text-indigo-400" />
          <span className="text-slate-400 hidden sm:inline">Guardrails:</span>
          <span className="text-indigo-400 font-semibold uppercase">ACTIVE</span>
        </div>

        {/* Server type */}
        <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-xs font-mono">
          <Server className="h-4 w-4 text-emerald-400" />
          <span className="text-slate-400 hidden sm:inline">Host:</span>
          <span className="text-emerald-400 font-semibold uppercase">LOCAL-FIRST</span>
        </div>

        {/* Sync */}
        <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-xs font-mono">
          <Radio className="h-4 w-4 text-amber-500 animate-pulse" />
          <span className="text-slate-400 hidden sm:inline">Obsidian Sync:</span>
          <span className="text-amber-500 font-semibold uppercase">PENDING</span>
        </div>
      </div>
    </header>
  );
}
