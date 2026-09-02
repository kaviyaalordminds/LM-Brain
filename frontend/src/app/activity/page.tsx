'use client';

import React, { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { useSimulation } from '@/lib/context/SimulationContext';
import { mockActivity } from '@/lib/mock';
import { ActivityEvent } from '@/lib/types';
import { Terminal, Search, SlidersHorizontal, Trash2, ArrowUpRight } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

export default function Page() {
  const { simulatedEvents } = useSimulation();
  const [filter, setFilter] = useState<ActivityEvent['component'] | 'all'>('all');

  // Fallback to static mock logs if simulation hasn't run yet, so the screen isn't blank
  const activeLogs = simulatedEvents.length > 0 ? simulatedEvents : mockActivity;

  const filteredLogs = activeLogs.filter(log => {
    return filter === 'all' || log.component === filter;
  });

  const getLogTypeStyle = (type: ActivityEvent['type']) => {
    switch (type) {
      case 'error': return 'text-rose-400 border-rose-500/20 bg-rose-500/5';
      case 'warning': return 'text-amber-500 border-amber-500/20 bg-amber-500/5';
      case 'success': return 'text-emerald-400 border-emerald-500/20 bg-emerald-500/5';
      case 'info': return 'text-indigo-400 border-indigo-500/20 bg-indigo-500/5';
      default: return 'text-slate-400 border-slate-800 bg-slate-900/50';
    }
  };

  return (
    <div className="flex flex-col min-h-full pb-10">
      <Header
        title="Activity Log Feed"
        subtitle="Real-time websocket telemetry stream from workforce orchestrators."
      />

      <div className="flex-1 px-6 py-6 space-y-6 max-w-6xl mx-auto w-full select-none">
        
        {/* Component Filters */}
        <div className="flex flex-col sm:flex-row gap-3 justify-between items-stretch sm:items-center">
          <span className="text-xs font-mono text-indigo-400 font-bold uppercase tracking-wider">
            {simulatedEvents.length > 0 ? "🔴 Live Simulation Feed Active" : "📊 Historical Telemetry Log"}
          </span>

          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none bg-[#0c1322] border border-slate-800 p-1 rounded-lg">
            {(['all', 'perception', 'orchestrator', 'planner', 'security', 'agent', 'verification', 'memory'] as const).map(c => (
              <button
                key={c}
                onClick={() => setFilter(c)}
                className={cn(
                  "px-3 py-1.5 rounded text-[10px] uppercase font-bold tracking-wider transition-colors shrink-0",
                  filter === c ? "bg-slate-800 text-slate-100" : "text-slate-500 hover:text-slate-300"
                )}
              >
                {c}
              </button>
            ))}
          </div>
        </div>

        {/* Logs Feed wrapper */}
        <div className="bg-[#0c1322] border border-slate-800 rounded-xl overflow-hidden flex flex-col">
          <div className="h-10 bg-[#090d16] border-b border-slate-800 px-4 flex items-center justify-between text-xs font-mono text-slate-400">
            <div className="flex items-center gap-2">
              <Terminal className="h-4 w-4 text-indigo-400" />
              <span>telemetry_stream.log</span>
            </div>
            <span>WebSocket Status: Connected</span>
          </div>

          <div className="p-4 bg-slate-950/80 font-mono text-xs leading-relaxed space-y-2.5 max-h-[500px] overflow-y-auto min-h-[300px]">
            {filteredLogs.map(log => (
              <div key={log.id} className="flex gap-3 items-start border-b border-slate-900/60 pb-2 last:border-none">
                <span className="text-slate-600 shrink-0 select-none">
                  [{new Date(log.timestamp).toLocaleTimeString()}]
                </span>
                
                <span className={cn(
                  "text-[9px] font-bold uppercase border px-1.5 rounded shrink-0",
                  getLogTypeStyle(log.type)
                )}>
                  {log.component}
                </span>

                <span className={cn(
                  log.type === 'error' && "text-rose-300 font-semibold",
                  log.type === 'warning' && "text-amber-300",
                  log.type === 'success' && "text-emerald-300",
                  log.type === 'info' && "text-slate-300"
                )}>
                  {log.message}
                </span>
              </div>
            ))}
            
            {filteredLogs.length === 0 && (
              <div className="h-full flex items-center justify-center text-slate-600 py-10">
                No logs filtered for this component.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
