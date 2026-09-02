'use client';

import React, { useState, useEffect } from 'react';
import { useExecutionPolling } from '@/hooks/useExecutionPolling';
import { orchestratorApi } from '@/lib/api/orchestrator';
import { ExecutionCanvas } from '@/components/execution/ExecutionCanvas';
import { ExecutionInspector } from '@/components/execution/ExecutionInspector';
import { LiveEventStream } from '@/components/events/LiveEventStream';
import { Badge } from '@/components/ui/Badge';
import { formatTimestamp, truncateId } from '@/lib/utils/formatters';
import { Layers, RefreshCw, AlertCircle, Clock, ChevronRight } from 'lucide-react';

export default function ExecutionWorkspacePage() {
  const [executions, setExecutions] = useState<any[]>([]);
  const [selectedExecId, setSelectedExecId] = useState<string | null>(null);
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);

  const {
    execution,
    status,
    events,
    attempts,
    artifacts,
    isLoading,
    refetch,
  } = useExecutionPolling(selectedExecId);

  const loadExecutions = async () => {
    const list = await orchestratorApi.listExecutions();
    setExecutions(list);
    if (list.length > 0 && !selectedExecId) {
      setSelectedExecId(list[0].execution_id);
    }
  };

  useEffect(() => {
    loadExecutions();
  }, []);

  return (
    <div className="space-y-4">
      {/* Workspace Header */}
      <div className="flex items-center justify-between p-3 bg-space-900 border border-space-800 rounded-lg font-mono-tech">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-emerald-400" />
          <h1 className="text-xs font-bold text-slate-100 uppercase tracking-wider">
            Execution Workspace & DAG Studio
          </h1>
          <span className="text-[10px] text-slate-500">
            ({executions.length} historical runs in SQLite)
          </span>
        </div>
        <button
          onClick={loadExecutions}
          className="flex items-center gap-1.5 px-2.5 py-1 text-xs text-slate-300 bg-space-850 hover:bg-space-800 border border-space-750 rounded transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Runs</span>
        </button>
      </div>

      {/* 3-Pane Engineering Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        {/* Left Pane: Execution Selector (cols 3) */}
        <div className="lg:col-span-3 bg-space-900 border border-space-800 rounded-lg p-3 space-y-2 max-h-[720px] overflow-y-auto">
          <div className="text-[11px] font-mono-tech text-slate-400 uppercase tracking-wider pb-2 border-b border-space-800">
            Executions
          </div>

          {executions.length === 0 ? (
            <div className="text-center py-12 text-xs font-mono-tech text-slate-500">
              No executions found
            </div>
          ) : (
            executions.map((ex) => {
              const isSelected = selectedExecId === ex.execution_id;
              return (
                <div
                  key={ex.execution_id}
                  onClick={() => {
                    setSelectedExecId(ex.execution_id);
                    setSelectedStepId(null);
                  }}
                  className={`p-2.5 rounded border transition-all cursor-pointer font-mono-tech text-left ${
                    isSelected
                      ? 'bg-space-800 border-sky-500 shadow-sm ring-1 ring-sky-500/40'
                      : 'bg-space-950 hover:bg-space-850 border-space-800'
                  }`}
                >
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span className="text-xs font-bold text-slate-200">
                      {truncateId(ex.execution_id, 8)}
                    </span>
                    <Badge status={ex.status} size="sm" />
                  </div>
                  <p className="text-[11px] text-slate-400 font-sans line-clamp-2 leading-relaxed mb-1.5">
                    {ex.user_request}
                  </p>
                  <div className="flex items-center justify-between text-[10px] text-slate-500">
                    <span>{formatTimestamp(ex.created_at)}</span>
                    <span>Steps: {ex.completed_steps?.length || 0}/{ex.pending_steps?.length || 0}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Center & Right Panes (cols 9) */}
        <div className="lg:col-span-9 space-y-4">
          {/* DAG Canvas */}
          <ExecutionCanvas
            execution={execution}
            status={status}
            events={events}
            attempts={attempts}
            selectedStepId={selectedStepId}
            onSelectStep={setSelectedStepId}
          />

          {/* Bottom Split: Step Inspector & Event Stream */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ExecutionInspector
              execution={execution}
              status={status}
              events={events}
              attempts={attempts}
              artifacts={artifacts}
              selectedStepId={selectedStepId}
              onClose={() => setSelectedStepId(null)}
            />

            <LiveEventStream
              events={events}
              maxHeight="max-h-[420px]"
              title="Execution Event Logs"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
