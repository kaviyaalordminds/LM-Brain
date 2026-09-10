import React from 'react';
import {
  AlertTriangle,
  Bot,
  Brain,
  CheckCircle2,
  Clock,
  Database,
  Eye,
  FileCheck2,
  RefreshCw,
  Search,
  ShieldCheck,
  Terminal,
  Zap,
} from 'lucide-react';
import { StageKey, StageStatus, WorkflowStage } from '../../types';
import { Badge } from '../common/Badge';

interface WorkflowPipelineProps {
  stages: WorkflowStage[];
  currentStageIndex: number;
  onSelectStage?: (index: number) => void;
  selectedStageIndex?: number;
}

export const WorkflowPipeline: React.FC<WorkflowPipelineProps> = ({
  stages,
  currentStageIndex,
  onSelectStage,
  selectedStageIndex,
}) => {
  const getStageIcon = (key: StageKey, status: StageStatus) => {
    const iconClass = 'w-4 h-4';
    switch (key) {
      case 'PERCEPTION':
        return <Search className={iconClass} />;
      case 'COMPANY_KNOWLEDGE':
        return <Database className={iconClass} />;
      case 'REASONING':
        return <Brain className={iconClass} />;
      case 'PLAN_VALIDATION':
        return <ShieldCheck className={iconClass} />;
      case 'CAPABILITY_SELECTION':
        return <Bot className={iconClass} />;
      case 'SPECIALIST_DELEGATION':
        return <Zap className={iconClass} />;
      case 'CONTROLLED_EXECUTION':
        return <Terminal className={iconClass} />;
      case 'OBSERVATION_QA':
        return <Eye className={iconClass} />;
      case 'VERIFICATION':
        return <FileCheck2 className={iconClass} />;
      case 'MEMORY_WRITEBACK':
        return <Database className={iconClass} />;
      default:
        return <CheckCircle2 className={iconClass} />;
    }
  };

  const getStatusBadge = (status: StageStatus) => {
    switch (status) {
      case 'COMPLETED':
        return <Badge variant="success" size="sm" dot>COMPLETED</Badge>;
      case 'RUNNING':
        return <Badge variant="primary" size="sm" dot className="animate-subtle-pulse">RUNNING</Badge>;
      case 'RECOVERING':
        return <Badge variant="warning" size="sm" dot className="animate-subtle-pulse">RECOVERING</Badge>;
      case 'FAILED':
        return <Badge variant="danger" size="sm" dot>FAILED</Badge>;
      case 'BLOCKED':
        return <Badge variant="warning" size="sm" dot>BLOCKED</Badge>;
      case 'SKIPPED':
        return <Badge variant="default" size="sm">SKIPPED</Badge>;
      case 'WAITING':
      default:
        return <Badge variant="default" size="sm">WAITING</Badge>;
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0F172A] p-5 shadow-lg space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
        <div>
          <h2 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
            <Zap className="w-4 h-4 text-indigo-400" />
            Autonomous Control Loop Pipeline
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            10-Stage Deterministic Verification Workflow
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span>Active Phase:</span>
          <span className="text-indigo-300 font-semibold">
            {stages[currentStageIndex]?.label || 'Initial'} ({currentStageIndex + 1}/{stages.length})
          </span>
        </div>
      </div>

      {/* Pipeline Stages Grid / Horizontal Flow */}
      <div className="grid grid-cols-2 sm:grid-cols-5 lg:grid-cols-10 gap-2.5">
        {stages.map((stage, idx) => {
          const isSelected = selectedStageIndex === idx;
          const isCurrent = currentStageIndex === idx && stage.status === 'RUNNING';

          let stateStyle = 'bg-slate-900/60 border-slate-800/70 text-slate-400 hover:border-slate-700';
          if (stage.status === 'COMPLETED') {
            stateStyle = 'bg-emerald-950/20 border-emerald-800/40 text-slate-200 hover:border-emerald-700/60';
          } else if (stage.status === 'RUNNING') {
            stateStyle = 'bg-indigo-950/50 border-indigo-500/80 text-white shadow-md shadow-indigo-950/50 ring-1 ring-indigo-500/50';
          } else if (stage.status === 'RECOVERING') {
            stateStyle = 'bg-amber-950/40 border-amber-500/80 text-amber-200 ring-1 ring-amber-500/40';
          } else if (stage.status === 'FAILED') {
            stateStyle = 'bg-rose-950/30 border-rose-600/60 text-rose-200';
          } else if (stage.status === 'BLOCKED') {
            stateStyle = 'bg-amber-950/20 border-amber-700/40 text-amber-300';
          }

          return (
            <button
              key={stage.key}
              onClick={() => onSelectStage && onSelectStage(idx)}
              className={`p-3 rounded-lg border text-left transition-all relative flex flex-col justify-between min-h-[110px] ${stateStyle} ${
                isSelected ? 'ring-2 ring-indigo-400 border-indigo-400' : ''
              }`}
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold text-slate-400">
                    {String(idx + 1).padStart(2, '0')}
                  </span>
                  <span
                    className={`${
                      stage.status === 'COMPLETED'
                        ? 'text-emerald-400'
                        : stage.status === 'RUNNING'
                        ? 'text-indigo-400'
                        : stage.status === 'RECOVERING'
                        ? 'text-amber-400'
                        : stage.status === 'FAILED'
                        ? 'text-rose-400'
                        : 'text-slate-500'
                    }`}
                  >
                    {getStageIcon(stage.key, stage.status)}
                  </span>
                </div>
                <div className="text-xs font-bold tracking-tight line-clamp-2">
                  {stage.label}
                </div>
              </div>

              <div className="mt-2 pt-2 border-t border-slate-800/60 flex items-center justify-between">
                <span className="text-[9px] font-mono uppercase tracking-wider font-semibold">
                  {stage.status}
                </span>
                {stage.timestamp && (
                  <span className="text-[9px] font-mono text-slate-400">
                    {stage.timestamp}
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
