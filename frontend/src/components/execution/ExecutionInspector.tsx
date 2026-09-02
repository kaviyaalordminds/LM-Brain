'use client';

import React, { useState, useMemo } from 'react';
import {
  Execution,
  ExecutionStatusResponse,
  ExecutionEvent,
  DispatchAttempt,
  LineageArtifact,
  PlanStep,
} from '../../lib/types';
import { Tabs } from '../ui/Tabs';
import { Badge } from '../ui/Badge';
import { CodeBlock } from '../ui/CodeBlock';
import { formatTimestamp, formatDuration } from '../../lib/utils/formatters';
import {
  Info,
  RotateCcw,
  ListTree,
  Box,
  FileCode,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Cpu,
} from 'lucide-react';

interface ExecutionInspectorProps {
  execution: Execution | null;
  status: ExecutionStatusResponse | null;
  events: ExecutionEvent[];
  attempts: DispatchAttempt[];
  artifacts: LineageArtifact[];
  selectedStepId?: string | null;
  onClose?: () => void;
  className?: string;
}

export const ExecutionInspector: React.FC<ExecutionInspectorProps> = ({
  execution,
  status,
  events,
  attempts,
  artifacts,
  selectedStepId,
  onClose,
  className = '',
}) => {
  const [activeTab, setActiveTab] = useState('details');

  // Find selected step if any
  const selectedStep: PlanStep | null = useMemo(() => {
    if (!selectedStepId) return null;
    const planSteps: PlanStep[] =
      execution?.metadata?.plan?.steps ||
      events.find((e) => e.event_type === 'PLAN_RECEIVED')?.payload?.plan?.steps ||
      [];
    return planSteps.find((s) => s.step_id === selectedStepId) || {
      step_id: selectedStepId,
      specialist: 'Specialist',
      description: `Autonomous execution for ${selectedStepId}`,
      dependencies: [],
    };
  }, [selectedStepId, execution, events]);

  // Attempts filtered for this step
  const stepAttempts = useMemo(() => {
    if (!selectedStepId) return attempts;
    return attempts.filter((a) => a.step_id === selectedStepId);
  }, [attempts, selectedStepId]);

  // Events filtered for this step
  const stepEvents = useMemo(() => {
    if (!selectedStepId) return events;
    return events.filter((e) => e.step_id === selectedStepId);
  }, [events, selectedStepId]);

  // Artifacts filtered for this step
  const stepArtifacts = useMemo(() => {
    if (!selectedStepId) return artifacts;
    return artifacts.filter((a) => a.step_id === selectedStepId);
  }, [artifacts, selectedStepId]);

  const tabs = [
    { id: 'details', label: 'Details', icon: <Info className="w-3.5 h-3.5" /> },
    { id: 'attempts', label: 'Attempts', count: stepAttempts.length, icon: <RotateCcw className="w-3.5 h-3.5" /> },
    { id: 'events', label: 'Events', count: stepEvents.length, icon: <ListTree className="w-3.5 h-3.5" /> },
    { id: 'artifacts', label: 'Artifacts', count: stepArtifacts.length, icon: <Box className="w-3.5 h-3.5" /> },
    { id: 'raw', label: 'Raw State', icon: <FileCode className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className={`bg-space-900 border border-space-800 rounded-lg flex flex-col overflow-hidden shadow-lg ${className}`}>
      {/* Top Header */}
      <div className="flex items-center justify-between p-3 border-b border-space-800 bg-space-850">
        <div className="flex items-center gap-2 overflow-hidden">
          <Cpu className="w-4 h-4 text-emerald-400 shrink-0" />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold font-mono-tech text-slate-100">
                {selectedStep ? `STEP: ${selectedStep.step_id}` : 'EXECUTION INSPECTOR'}
              </span>
              {selectedStep && (
                <span className="text-[10px] font-mono-tech px-1.5 py-0.2 rounded bg-space-800 text-slate-400 border border-space-700 uppercase">
                  {selectedStep.specialist}
                </span>
              )}
            </div>
            <div className="text-[10px] text-slate-500 font-mono-tech truncate">
              ID: {execution?.execution_id || status?.execution_id || '---'}
            </div>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="text-[11px] font-mono-tech text-slate-400 hover:text-slate-200 px-2 py-1 rounded hover:bg-space-800"
          >
            CLOSE
          </button>
        )}
      </div>

      {/* Tabs bar */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab Content */}
      <div className="p-4 flex-1 overflow-y-auto max-h-[420px] space-y-3">
        {activeTab === 'details' && (
          <div className="space-y-3 text-xs">
            {selectedStep ? (
              <>
                <div className="p-3 bg-space-950 border border-space-800 rounded-md">
                  <div className="text-[10px] font-mono-tech text-slate-500 uppercase mb-1">Description</div>
                  <div className="text-slate-200 leading-relaxed font-sans">{selectedStep.description}</div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono-tech">
                  <div className="p-2.5 bg-space-950 border border-space-800 rounded">
                    <span className="text-slate-500 block">Specialist</span>
                    <span className="text-slate-200 font-bold uppercase">{selectedStep.specialist}</span>
                  </div>
                  <div className="p-2.5 bg-space-950 border border-space-800 rounded">
                    <span className="text-slate-500 block">Dependencies</span>
                    <span className="text-slate-300">
                      {selectedStep.dependencies?.length ? selectedStep.dependencies.join(', ') : 'None'}
                    </span>
                  </div>
                </div>

                {selectedStep.verification_requirements && (
                  <div className="p-3 bg-space-950 border border-space-800 rounded-md">
                    <div className="text-[10px] font-mono-tech text-slate-500 uppercase mb-1">
                      Verification Criteria
                    </div>
                    <pre className="text-[11px] font-mono-tech text-slate-300 whitespace-pre-wrap">
                      {typeof selectedStep.verification_requirements === 'string'
                        ? selectedStep.verification_requirements
                        : JSON.stringify(selectedStep.verification_requirements, null, 2)}
                    </pre>
                  </div>
                )}
              </>
            ) : (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono-tech">
                  <div className="p-2.5 bg-space-950 border border-space-800 rounded">
                    <span className="text-slate-500 block">Status</span>
                    <span className="text-emerald-400 font-bold">{execution?.status || status?.status || '---'}</span>
                  </div>
                  <div className="p-2.5 bg-space-950 border border-space-800 rounded">
                    <span className="text-slate-500 block">Phase</span>
                    <span className="text-cyan-400 font-bold">{execution?.phase || status?.phase || '---'}</span>
                  </div>
                </div>

                <div className="p-3 bg-space-950 border border-space-800 rounded-md font-mono-tech text-[11px] space-y-1">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Plan ID:</span>
                    <span className="text-slate-300">{execution?.plan_id || status?.plan_id || '---'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Plan Version:</span>
                    <span className="text-slate-300">{execution?.plan_version ?? status?.plan_version ?? 1}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Created At:</span>
                    <span className="text-slate-300">{formatTimestamp(execution?.created_at)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Updated At:</span>
                    <span className="text-slate-300">{formatTimestamp(execution?.updated_at)}</span>
                  </div>
                </div>

                {(execution?.error || status?.error) && (
                  <div className="p-3 bg-rose-950/40 border border-rose-800/80 rounded-md text-xs font-mono-tech text-rose-300">
                    <div className="flex items-center gap-1.5 font-bold mb-1">
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                      <span>Execution Error Notice</span>
                    </div>
                    <p className="leading-relaxed">{execution?.error || status?.error}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'attempts' && (
          <div className="space-y-2">
            {stepAttempts.length === 0 ? (
              <div className="text-center py-8 text-xs font-mono-tech text-slate-500">
                No dispatch attempts recorded yet
              </div>
            ) : (
              stepAttempts.map((att, idx) => (
                <div key={att.attempt_id || idx} className="p-3 bg-space-950 border border-space-800 rounded-md font-mono-tech text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200">Attempt #{att.attempt_number || idx + 1}</span>
                    <Badge status={att.status} size="sm" />
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-400">
                    <span>Specialist: {att.specialist_id || '---'}</span>
                    <span>Duration: {formatDuration(att.started_at, att.completed_at)}</span>
                  </div>
                  {att.error && (
                    <div className="p-2 rounded bg-rose-950/30 border border-rose-900/60 text-rose-300 text-[11px] mt-1">
                      {att.error}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'events' && (
          <div className="space-y-1.5 font-mono-tech text-xs">
            {stepEvents.length === 0 ? (
              <div className="text-center py-8 text-slate-500">No events found</div>
            ) : (
              stepEvents.map((evt) => (
                <div key={evt.event_id} className="p-2 bg-space-950 border border-space-850 rounded flex items-center justify-between gap-2">
                  <div className="truncate">
                    <span className="text-emerald-400 mr-2 font-bold">{evt.event_type}</span>
                    <span className="text-slate-400 text-[11px]">{evt.step_id || ''}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 shrink-0">{formatTimestamp(evt.timestamp)}</span>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'artifacts' && (
          <div className="space-y-2 font-mono-tech text-xs">
            {stepArtifacts.length === 0 ? (
              <div className="text-center py-8 text-slate-500">No artifacts produced</div>
            ) : (
              stepArtifacts.map((art) => (
                <div key={art.artifact_id} className="p-3 bg-space-950 border border-space-800 rounded space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-200 font-bold">{art.artifact_type}</span>
                    <span className="text-[10px] text-emerald-400">{art.trust_state}</span>
                  </div>
                  <div className="text-[11px] text-slate-400 truncate">{art.path || art.url}</div>
                  <div className="text-[10px] text-slate-500">{formatTimestamp(art.created_at)}</div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'raw' && (
          <CodeBlock
            code={JSON.stringify(
              selectedStep ? { step: selectedStep, attempts: stepAttempts, events: stepEvents } : execution || status || {},
              null,
              2
            )}
            language="json"
            title="Raw Payload"
          />
        )}
      </div>
    </div>
  );
};
