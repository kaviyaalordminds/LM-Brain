import React from 'react';
import {
  Activity,
  AlertCircle,
  Bot,
  Brain,
  CheckCircle2,
  Clock,
  Cpu,
  Database,
  Eye,
  FileCheck2,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Terminal,
  XCircle,
  Zap,
} from 'lucide-react';
import { AuditEvent, OrchestrationStatus, WorkflowStage } from '../../types';
import { Badge } from '../common/Badge';

interface ExecutionTimelineProps {
  stages: WorkflowStage[];
  currentStageIndex: number;
  auditEvents?: AuditEvent[];
  isExecuting?: boolean;
  status?: OrchestrationStatus;
}

export const ExecutionTimeline: React.FC<ExecutionTimelineProps> = ({
  stages,
  currentStageIndex,
  auditEvents = [],
  isExecuting = false,
  status = 'EXECUTING',
}) => {
  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0F172A] p-5 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-bold text-white tracking-tight uppercase">
            Workforce Execution Event Timeline
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          {stages.filter((s) => s.status === 'COMPLETED').length} / {stages.length} Completed
        </span>
      </div>

      <div className="relative pl-6 space-y-3 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {stages.map((stage, idx) => {
          const isCurrent = idx === currentStageIndex && isExecuting;
          const isCompleted = stage.status === 'COMPLETED';
          const isFailed = stage.status === 'FAILED';
          const isRecovering = stage.status === 'RECOVERING';
          const isWaiting = stage.status === 'WAITING';

          let icon = <Clock className="w-3 h-3 text-slate-500" />;
          let iconWrapperClass = 'border-slate-700 bg-slate-900 text-slate-500';
          let rowClass = 'bg-slate-950/40 border-slate-900 text-slate-500';
          let badgeVariant: 'default' | 'primary' | 'success' | 'danger' | 'warning' = 'default';
          let badgeText = 'PENDING';

          if (isCompleted) {
            icon = <CheckCircle2 className="w-3 h-3 text-emerald-400" />;
            iconWrapperClass = 'border-emerald-800 bg-emerald-950 text-emerald-400';
            rowClass = 'bg-slate-900/90 border-slate-800/80 text-slate-200';
            badgeVariant = 'success';
            badgeText = 'COMPLETED';
          } else if (isCurrent) {
            icon = <Activity className="w-3 h-3 text-indigo-400 animate-spin" />;
            iconWrapperClass = 'border-indigo-500 bg-indigo-950 text-indigo-400 ring-2 ring-indigo-500/50';
            rowClass = 'active-stage-card border-indigo-500/80 text-white shadow-md';
            badgeVariant = 'primary';
            badgeText = 'EXECUTING';
          } else if (isRecovering) {
            icon = <RefreshCw className="w-3 h-3 text-amber-400 animate-spin" />;
            iconWrapperClass = 'border-amber-500 bg-amber-950 text-amber-400';
            rowClass = 'recovering-stage-card border-amber-500/80 text-amber-200';
            badgeVariant = 'warning';
            badgeText = 'RECOVERING';
          } else if (isFailed) {
            icon = <XCircle className="w-3 h-3 text-rose-400" />;
            iconWrapperClass = 'border-rose-800 bg-rose-950 text-rose-400';
            rowClass = 'bg-rose-950/30 border-rose-800/60 text-rose-200';
            badgeVariant = 'danger';
            badgeText = 'FAILED';
          }

          return (
            <div key={`timeline_${stage.key}`} className="relative group">
              <div
                className={`absolute -left-6 top-1.5 w-5 h-5 rounded-full border flex items-center justify-center text-[10px] ${iconWrapperClass}`}
              >
                {icon}
              </div>

              <div className={`p-3 rounded-xl border transition-all text-xs ${rowClass}`}>
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] text-slate-500 font-bold">
                      {String(idx + 1).padStart(2, '0')}
                    </span>
                    <strong className="text-white font-sans text-xs">
                      {stage.label}
                    </strong>
                  </div>
                  <div className="flex items-center gap-2">
                    {stage.durationMs !== undefined && stage.durationMs > 0 && (
                      <span className="text-[10px] font-mono text-slate-400">
                        {stage.durationMs}ms
                      </span>
                    )}
                    <Badge variant={badgeVariant} size="sm">
                      {badgeText}
                    </Badge>
                  </div>
                </div>

                <p className="text-[11px] text-slate-400 mt-1 font-sans">
                  {stage.shortDescription}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
