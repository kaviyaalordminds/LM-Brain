'use client';

import React, { useMemo } from 'react';
import {
  Execution,
  ExecutionStatusResponse,
  ExecutionEvent,
  DispatchAttempt,
  PlanStep,
  StepLifecycle,
} from '../../lib/types';
import { DAGNode } from './DAGNode';
import { EmptyState } from '../ui/EmptyState';
import { ArrowRight, Bot, Cpu, ShieldCheck, Box, AlertCircle, RefreshCw } from 'lucide-react';

interface ExecutionCanvasProps {
  execution: Execution | null;
  status: ExecutionStatusResponse | null;
  events: ExecutionEvent[];
  attempts: DispatchAttempt[];
  selectedStepId?: string | null;
  onSelectStep?: (stepId: string) => void;
  className?: string;
}

export const ExecutionCanvas: React.FC<ExecutionCanvasProps> = ({
  execution,
  status,
  events,
  attempts,
  selectedStepId,
  onSelectStep,
  className = '',
}) => {
  // Extract steps from plan or events
  const steps: PlanStep[] = useMemo(() => {
    // 1. Check if plan is inside execution metadata
    if (execution?.metadata?.plan?.steps) {
      return execution.metadata.plan.steps;
    }
    // 2. Check if PLAN_RECEIVED event has steps
    const planEvent = events.find((e) => e.event_type === 'PLAN_RECEIVED');
    if (planEvent?.payload?.plan?.steps) {
      return planEvent.payload.plan.steps;
    }
    // 3. Fallback: synthesize steps from completed/failed/running/blocked/pending lists
    const allStepIds = Array.from(
      new Set([
        ...(execution?.running_steps || status?.running_steps || []),
        ...(execution?.failed_steps || status?.failed_steps || []),
        ...(execution?.completed_steps || status?.completed_steps || []),
        ...(execution?.blocked_steps || status?.blocked_steps || []),
        ...(execution?.pending_steps || status?.pending_steps || []),
      ])
    );

    if (allStepIds.length > 0) {
      return allStepIds.map((sid) => {
        // Attempt to extract specialist from sid (e.g. step_1_research -> research)
        const parts = sid.split('_');
        const specialist = parts.length > 2 ? parts.slice(2).join(' ') : parts[parts.length - 1] || 'Specialist';
        return {
          step_id: sid,
          specialist,
          description: `Autonomous task execution for ${sid}`,
          dependencies: [],
        };
      });
    }

    return [];
  }, [execution, status, events]);

  // Compute step status map
  const stepStatusMap = useMemo(() => {
    const map: Record<string, { status: StepLifecycle; attempt: number; error: string | null }> = {};
    const running = new Set(execution?.running_steps || status?.running_steps || []);
    const failed = new Set(execution?.failed_steps || status?.failed_steps || []);
    const completed = new Set(execution?.completed_steps || status?.completed_steps || []);
    const blocked = new Set(execution?.blocked_steps || status?.blocked_steps || []);

    steps.forEach((s) => {
      let st: StepLifecycle = 'PENDING';
      if (running.has(s.step_id)) st = 'RUNNING';
      else if (failed.has(s.step_id)) st = 'FAILED';
      else if (completed.has(s.step_id)) st = 'COMPLETED';
      else if (blocked.has(s.step_id)) st = 'BLOCKED';

      // Find attempts for this step
      const stepAttempts = attempts.filter((a) => a.step_id === s.step_id);
      const latestAttempt = stepAttempts[stepAttempts.length - 1];

      map[s.step_id] = {
        status: st,
        attempt: stepAttempts.length,
        error: latestAttempt?.error || (st === 'FAILED' ? execution?.error || status?.error || null : null),
      };
    });
    return map;
  }, [steps, execution, status, attempts]);

  // If no execution exists at all
  if (!execution && !status) {
    return (
      <div className={`flex items-center justify-center p-12 bg-space-950 border border-space-800 rounded-lg min-h-[360px] ${className}`}>
        <EmptyState
          title="No Active Execution"
          description="Dispatch a new natural language task or select a previous execution to visualize its DAG execution graph."
        />
      </div>
    );
  }

  const isPlanning = execution?.status === 'PLANNING' || status?.status === 'PLANNING';
  const isFailed = execution?.status === 'FAILED' || status?.status === 'FAILED';
  const isModelUnavailable =
    execution?.error?.includes('MODEL_UNAVAILABLE') ||
    status?.error?.includes('MODEL_UNAVAILABLE') ||
    attempts.some((a) => a.error?.includes('MODEL_UNAVAILABLE'));

  return (
    <div className={`flex flex-col bg-space-950 border border-space-800 rounded-lg p-5 overflow-hidden shadow-inner ${className}`}>
      {/* Top Telemetry Header of Canvas */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-space-800/80 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-xs font-bold font-mono-tech uppercase tracking-wider text-slate-100">
              DAG Execution Canvas
            </h3>
            <span className="text-[10px] font-mono-tech px-2 py-0.5 rounded bg-space-850 text-slate-400 border border-space-750">
              Plan: {execution?.plan_id || status?.plan_id || 'PENDING_DECOMPOSITION'}
            </span>
          </div>
          <div className="text-[11px] text-slate-400 font-mono-tech mt-1 truncate max-w-xl">
            REQ: "{execution?.user_request || '---'}"
          </div>
        </div>

        {/* Phase & Warning callout */}
        <div className="flex items-center gap-2">
          {isModelUnavailable && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-rose-950/60 border border-rose-800 text-rose-300 text-[11px] font-mono-tech">
              <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
              <span>MODEL_UNAVAILABLE (No LLM key configured)</span>
            </div>
          )}
          {isPlanning && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-cyan-950/40 border border-cyan-800/60 text-cyan-400 text-[11px] font-mono-tech">
              <RefreshCw className="w-3 h-3 animate-spin" />
              <span>Planner decomposing user intent...</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Graph Surface */}
      <div className="relative flex-1 overflow-x-auto p-4 min-h-[300px] flex items-center justify-start bg-grid-workstation rounded-md border border-space-900">
        <div className="flex items-center gap-6 min-w-max">
          {/* Node 0: Request Origin */}
          <div className="flex flex-col items-center">
            <div className="w-56 p-3 rounded-lg bg-space-900 border border-space-750 text-left">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-mono-tech text-slate-500 uppercase">Input Intent</span>
                <span className="text-[9px] font-mono-tech px-1.5 py-0.2 rounded bg-space-800 text-slate-300">USER</span>
              </div>
              <p className="text-xs text-slate-200 line-clamp-3 leading-relaxed font-sans">
                {execution?.user_request || 'Task submitted'}
              </p>
            </div>
            <span className="text-[10px] font-mono-tech text-slate-500 mt-2">Request</span>
          </div>

          <ArrowRight className="w-4 h-4 text-slate-600 shrink-0" />

          {/* Node 1: Planner Agent */}
          <div className="flex flex-col items-center">
            <div className="w-56 p-3 rounded-lg bg-space-900 border border-space-750 text-left">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                  <span className="text-[11px] font-mono-tech font-bold text-slate-200">PLANNER</span>
                </div>
                <span className="text-[9px] font-mono-tech px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                  AGENT
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                {steps.length > 0 ? `${steps.length} Steps Resolved` : isPlanning ? 'Analyzing Intent...' : 'Ready'}
              </p>
            </div>
            <span className="text-[10px] font-mono-tech text-slate-500 mt-2">Decomposition</span>
          </div>

          <ArrowRight className="w-4 h-4 text-slate-600 shrink-0" />

          {/* Node Tier 2: DAG Execution Steps */}
          {steps.length === 0 ? (
            <div className="flex items-center justify-center p-6 border border-dashed border-space-800 rounded-lg text-slate-500 text-xs font-mono-tech">
              {isPlanning ? 'Constructing DAG steps...' : 'No steps in execution plan'}
            </div>
          ) : (
            <div className="grid grid-flow-col auto-cols-max gap-4 items-center">
              {steps.map((step) => {
                const info = stepStatusMap[step.step_id] || { status: 'PENDING', attempt: 0, error: null };
                return (
                  <DAGNode
                    key={step.step_id}
                    step={step}
                    status={info.status}
                    attemptNumber={info.attempt}
                    isSelected={selectedStepId === step.step_id}
                    onClick={() => onSelectStep?.(step.step_id)}
                    error={info.error}
                  />
                );
              })}
            </div>
          )}

          <ArrowRight className="w-4 h-4 text-slate-600 shrink-0" />

          {/* Node 3: Result Verification */}
          <div className="flex flex-col items-center">
            <div className="w-56 p-3 rounded-lg bg-space-900 border border-space-750 text-left">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
                  <span className="text-[11px] font-mono-tech font-bold text-slate-200">VERIFICATION</span>
                </div>
                <span className="text-[9px] font-mono-tech px-1.5 py-0.2 rounded bg-purple-950 text-purple-400 border border-purple-800">
                  POLICY
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                {isFailed ? 'Verification Failed / Halted' : 'Enforcing Criteria'}
              </p>
            </div>
            <span className="text-[10px] font-mono-tech text-slate-500 mt-2">Audit</span>
          </div>

          <ArrowRight className="w-4 h-4 text-slate-600 shrink-0" />

          {/* Node 4: Lineage Artifacts */}
          <div className="flex flex-col items-center">
            <div className="w-56 p-3 rounded-lg bg-space-900 border border-space-750 text-left">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-1.5">
                  <Box className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-[11px] font-mono-tech font-bold text-slate-200">ARTIFACTS</span>
                </div>
                <span className="text-[9px] font-mono-tech px-1.5 py-0.2 rounded bg-space-800 text-slate-300">
                  {execution?.artifacts?.length || 0}
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                {execution?.artifacts && execution.artifacts.length > 0
                  ? `${execution.artifacts.length} Lineage Artifacts`
                  : 'Awaiting Output'}
              </p>
            </div>
            <span className="text-[10px] font-mono-tech text-slate-500 mt-2">Outputs</span>
          </div>
        </div>
      </div>
    </div>
  );
};
