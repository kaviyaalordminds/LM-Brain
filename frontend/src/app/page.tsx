'use client';

import React, { useState, useEffect } from 'react';
import { useExecutionPolling } from '@/hooks/useExecutionPolling';
import { orchestratorApi } from '@/lib/api/orchestrator';
import { TaskComposer } from '@/components/execution/TaskComposer';
import { ExecutionCanvas } from '@/components/execution/ExecutionCanvas';
import { ExecutionInspector } from '@/components/execution/ExecutionInspector';
import { LiveEventStream } from '@/components/events/LiveEventStream';
import { ALL_10_SPECIALISTS } from '@/components/specialists/WorkforceMap';
import { Badge } from '@/components/ui/Badge';
import {
  Play,
  Pause,
  RotateCcw,
  XCircle,
  RefreshCw,
  Layers,
  Bot,
  AlertTriangle,
  CheckCircle2,
  Clock,
} from 'lucide-react';

export default function WorkforceControlCenterPage() {
  const [activeExecId, setActiveExecId] = useState<string | null>(null);
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
  const [recentExecutions, setRecentExecutions] = useState<any[]>([]);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  // Poll active execution
  const {
    execution,
    status,
    events,
    attempts,
    artifacts,
    isLoading,
    isPolling,
    refetch,
  } = useExecutionPolling(activeExecId);

  // Fetch recent executions on mount
  useEffect(() => {
    orchestratorApi.listExecutions().then((list) => {
      setRecentExecutions(list);
      if (list.length > 0 && !activeExecId) {
        setActiveExecId(list[0].execution_id);
      }
    });
  }, []);

  const handleExecutionCreated = (newId: string) => {
    setActiveExecId(newId);
    setSelectedStepId(null);
    orchestratorApi.listExecutions().then(setRecentExecutions);
  };

  const handlePause = async () => {
    if (!activeExecId) return;
    try {
      await orchestratorApi.pauseExecution(activeExecId);
      setActionNotice('Paused execution');
      refetch();
    } catch (err: any) {
      setActionNotice(`Error: ${err.message}`);
    }
  };

  const handleResume = async () => {
    if (!activeExecId) return;
    try {
      await orchestratorApi.resumeExecution(activeExecId);
      setActionNotice('Resumed execution');
      refetch();
    } catch (err: any) {
      setActionNotice(`Error: ${err.message}`);
    }
  };

  const handleCancel = async () => {
    if (!activeExecId) return;
    try {
      await orchestratorApi.cancelExecution(activeExecId);
      setActionNotice('Cancelled execution');
      refetch();
    } catch (err: any) {
      setActionNotice(`Error: ${err.message}`);
    }
  };

  // Metrics
  const runningCount = execution?.running_steps?.length ?? status?.running_steps?.length ?? 0;
  const completedCount = execution?.completed_steps?.length ?? status?.completed_steps?.length ?? 0;
  const failedCount = execution?.failed_steps?.length ?? status?.failed_steps?.length ?? 0;
  const blockedCount = execution?.blocked_steps?.length ?? status?.blocked_steps?.length ?? 0;

  return (
    <div className="space-y-6">
      {/* Top Telemetry & Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-space-900 border border-space-800 rounded-lg shadow-md font-mono-tech">
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">Active Execution Context</div>
            <div className="flex items-center gap-2 mt-0.5">
              {recentExecutions.length > 0 ? (
                <select
                  value={activeExecId || ''}
                  onChange={(e) => {
                    setActiveExecId(e.target.value);
                    setSelectedStepId(null);
                  }}
                  className="bg-space-950 border border-space-750 text-xs text-slate-200 rounded px-2.5 py-1 focus:outline-none"
                >
                  {recentExecutions.map((ex) => (
                    <option key={ex.execution_id} value={ex.execution_id}>
                      {ex.execution_id.slice(0, 8)}... ({ex.status}) - {ex.user_request.slice(0, 30)}...
                    </option>
                  ))}
                </select>
              ) : (
                <span className="text-xs text-slate-400">No executions created yet</span>
              )}
              <Badge status={execution?.status || status?.status || 'IDLE'} size="sm" />
            </div>
          </div>

          {/* Real step counters */}
          <div className="hidden lg:flex items-center gap-2 pl-4 border-l border-space-800 text-xs">
            <span className="text-emerald-400">Run: {runningCount}</span>
            <span className="text-slate-600">|</span>
            <span className="text-cyan-400">Done: {completedCount}</span>
            <span className="text-slate-600">|</span>
            <span className="text-rose-400">Failed: {failedCount}</span>
            <span className="text-slate-600">|</span>
            <span className="text-orange-400">Blocked: {blockedCount}</span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          {actionNotice && (
            <span className="text-[11px] text-amber-400 animate-pulse mr-2">{actionNotice}</span>
          )}

          {activeExecId && (
            <>
              {execution?.status === 'PAUSED' ? (
                <button
                  onClick={handleResume}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-space-800 hover:bg-space-750 text-slate-200 text-xs rounded border border-space-700 transition-colors"
                  title="Resume Execution"
                >
                  <RotateCcw className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Resume</span>
                </button>
              ) : (
                <button
                  onClick={handlePause}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-space-800 hover:bg-space-750 text-slate-200 text-xs rounded border border-space-700 transition-colors"
                  title="Pause Execution"
                >
                  <Pause className="w-3.5 h-3.5 text-amber-400" />
                  <span>Pause</span>
                </button>
              )}

              <button
                onClick={handleCancel}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-space-800 hover:bg-space-750 text-slate-200 text-xs rounded border border-space-700 transition-colors"
                title="Cancel Execution"
              >
                <XCircle className="w-3.5 h-3.5 text-rose-400" />
                <span>Cancel</span>
              </button>
            </>
          )}

          <button
            onClick={() => refetch()}
            className="flex items-center gap-1.5 px-2.5 py-1.5 bg-space-850 hover:bg-space-800 text-slate-300 text-xs rounded border border-space-750 transition-colors"
            title="Refresh State"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isPolling ? 'animate-spin text-emerald-400' : ''}`} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {/* Task Composer */}
      <TaskComposer onExecutionCreated={handleExecutionCreated} />

      {/* Visual Centerpiece: Real DAG Execution Canvas */}
      <ExecutionCanvas
        execution={execution}
        status={status}
        events={events}
        attempts={attempts}
        selectedStepId={selectedStepId}
        onSelectStep={setSelectedStepId}
      />

      {/* 2-Column Section: Active Agent Modules & Live Event Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Active Specialists & Inspector */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-space-900 border border-space-800 rounded-lg p-4 font-mono-tech">
            <div className="flex items-center justify-between pb-2 border-b border-space-800 mb-3">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  Active Specialists
                </span>
              </div>
              <span className="text-[10px] text-slate-500">10 WORKERS</span>
            </div>

            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {ALL_10_SPECIALISTS.slice(0, 5).map((spec) => {
                const specAttempts = attempts.filter((a) =>
                  a.step_id?.toLowerCase().includes(spec.id.toLowerCase())
                );
                const hasFailed = specAttempts.some((a) => a.status === 'FAILED');
                const isRunning = specAttempts.some((a) => a.status === 'RUNNING');

                return (
                  <div
                    key={spec.id}
                    className="p-2.5 rounded bg-space-950 border border-space-800 flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="font-bold text-slate-200">{spec.name}</div>
                      <div className="text-[10px] text-slate-500">
                        Attempts: {specAttempts.length} | Model: {spec.modelStatus}
                      </div>
                    </div>
                    <Badge
                      status={isRunning ? 'RUNNING' : hasFailed ? 'FAILED' : 'READY'}
                      size="sm"
                    />
                  </div>
                );
              })}
            </div>
          </div>

          {/* Execution Inspector Drawer for Selected Step */}
          <ExecutionInspector
            execution={execution}
            status={status}
            events={events}
            attempts={attempts}
            artifacts={artifacts}
            selectedStepId={selectedStepId}
            onClose={() => setSelectedStepId(null)}
          />
        </div>

        {/* Right Column: Real-time Live Event Timeline */}
        <div className="lg:col-span-2">
          <LiveEventStream
            events={events}
            maxHeight="max-h-[620px]"
            title="Real-Time Execution Audit Trail"
          />
        </div>
      </div>
    </div>
  );
}
