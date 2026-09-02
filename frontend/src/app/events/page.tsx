'use client';

import React, { useState, useEffect } from 'react';
import { orchestratorApi } from '@/lib/api/orchestrator';
import { ExecutionEvent } from '@/lib/types';
import { LiveEventStream } from '@/components/events/LiveEventStream';
import { ListTree, RefreshCw, Filter, Search } from 'lucide-react';

export default function SystemEventsPage() {
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [executions, setExecutions] = useState<any[]>([]);
  const [selectedExecId, setSelectedExecId] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState(false);

  const loadAllEvents = async () => {
    setIsLoading(true);
    try {
      const execList = await orchestratorApi.listExecutions();
      setExecutions(execList);

      const allEvts: ExecutionEvent[] = [];
      const targets = selectedExecId === 'ALL' ? execList.slice(0, 8) : execList.filter((e) => e.execution_id === selectedExecId);

      for (const ex of targets) {
        try {
          const evts = await orchestratorApi.getExecutionEvents(ex.execution_id);
          allEvts.push(...evts);
        } catch {
          // ignore
        }
      }

      // Sort newest first
      allEvts.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
      setEvents(allEvts);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAllEvents();
  }, [selectedExecId]);

  return (
    <div className="space-y-6 font-mono-tech">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-space-900 border border-space-800 rounded-lg shadow-md">
        <div className="flex items-center gap-3">
          <ListTree className="w-5 h-5 text-emerald-400" />
          <div>
            <h1 className="text-xs font-bold text-slate-100 uppercase tracking-wider">
              System Observability & Audit Trail
            </h1>
            <div className="text-[11px] text-slate-400">
              Complete chronological audit trail of all lifecycle events across execution DAGs
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Execution filter */}
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-slate-500">Run:</span>
            <select
              value={selectedExecId}
              onChange={(e) => setSelectedExecId(e.target.value)}
              className="bg-space-950 border border-space-750 text-slate-200 rounded px-2.5 py-1 text-xs focus:outline-none"
            >
              <option value="ALL">All Executions ({executions.length})</option>
              {executions.map((ex) => (
                <option key={ex.execution_id} value={ex.execution_id}>
                  {ex.execution_id.slice(0, 8)}... ({ex.status})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={loadAllEvents}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1 bg-space-850 hover:bg-space-800 border border-space-750 text-slate-300 text-xs rounded transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {/* Main Stream Component */}
      <LiveEventStream
        events={events}
        maxHeight="max-h-[720px]"
        title={`Audit Events Stream (${events.length} records)`}
      />
    </div>
  );
}
