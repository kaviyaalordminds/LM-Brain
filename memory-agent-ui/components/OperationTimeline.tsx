'use client';

import React from 'react';
import { Terminal, CheckCircle2, XCircle, AlertTriangle, ArrowRight } from 'lucide-react';

export interface OperationEvent {
  id: string;
  timestamp: string;
  operation: string;
  endpoint: string;
  status: 'success' | 'error' | 'warning';
  statusCode: number;
  durationMs: number;
  detail: string;
}

interface OperationTimelineProps {
  events: OperationEvent[];
}

export const OperationTimeline: React.FC<OperationTimelineProps> = ({ events }) => {
  return (
    <div className="rounded-2xl bg-[#090D15] border border-slate-800 p-4 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
        <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-300">
          <Terminal className="w-4 h-4 text-sky-400" />
          <span>HTTP API Operations Stream</span>
        </div>
        <span className="text-[10px] font-mono text-slate-500 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
          {events.length} Records
        </span>
      </div>

      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
        {events.length === 0 ? (
          <div className="p-4 text-center text-xs text-slate-500 font-mono">
            No API operations recorded in this session.
          </div>
        ) : (
          events.map((ev) => {
            const isSuccess = ev.status === 'success';

            return (
              <div
                key={ev.id}
                className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800/80 flex items-start justify-between gap-3 text-xs font-mono"
              >
                <div className="space-y-0.5 truncate">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-500">{ev.timestamp}</span>
                    <span className="font-bold text-sky-300">{ev.operation}</span>
                    <span className="text-slate-500 text-[10px]">{ev.endpoint}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 truncate">{ev.detail}</p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-[10px] text-slate-500">{ev.durationMs}ms</span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                      isSuccess
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}
                  >
                    HTTP {ev.statusCode}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
