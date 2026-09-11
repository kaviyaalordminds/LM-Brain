import React from 'react';
import {
  AlertCircle,
  ArrowDown,
  ArrowRight,
  Bot,
  Brain,
  CheckCircle2,
  Clock,
  Cpu,
  Database,
  Eye,
  FileCheck2,
  Layers,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Terminal,
  UserCheck,
  Zap,
} from 'lucide-react';
import {
  ExecutiveTwin,
  OrchestrationStatus,
  StageKey,
  StageStatus,
  StepExecutionRecord,
  WorkflowStage,
} from '../../types';
import { Badge } from '../common/Badge';

export type ExecutionVisualStatus =
  | 'waiting'
  | 'active'
  | 'completed'
  | 'failed'
  | 'recovering'
  | 'verified';

interface AutonomousExecutionPipelineProps {
  stages: WorkflowStage[];
  currentStageIndex: number;
  selectedStageIndex?: number;
  onSelectStage?: (index: number) => void;
  executiveTwin?: ExecutiveTwin;
  selectedSpecialists?: Record<string, string>;
  specialistExecutions?: StepExecutionRecord[];
  isExecuting?: boolean;
  overallStatus?: OrchestrationStatus;
}

const STAGE_METADATA: Record<
  StageKey,
  {
    role: string;
    sublabel: string;
    icon: React.ComponentType<{ className?: string }>;
  }
> = {
  PERCEPTION: {
    role: 'Perception Agent',
    sublabel: 'Intent & Requirement Normalization',
    icon: Search,
  },
  COMPANY_KNOWLEDGE: {
    role: 'Company Knowledge Service',
    sublabel: 'Authoritative Obsidian Retrieval',
    icon: Database,
  },
  REASONING: {
    role: 'Reasoning Engine',
    sublabel: 'Structured DAG Plan Synthesis',
    icon: Brain,
  },
  PLAN_VALIDATION: {
    role: 'Plan Safety Validator',
    sublabel: 'Strict Bounds & DAG Verification',
    icon: ShieldCheck,
  },
  CAPABILITY_SELECTION: {
    role: 'Capability Matcher',
    sublabel: 'Specialist Registry Discovery',
    icon: Bot,
  },
  SPECIALIST_DELEGATION: {
    role: 'Specialist Delegator',
    sublabel: 'SecurityGuard Boundary Allocation',
    icon: Zap,
  },
  CONTROLLED_EXECUTION: {
    role: 'Software Development Specialist',
    sublabel: 'Sandboxed Workspace Worker',
    icon: Terminal,
  },
  OBSERVATION_QA: {
    role: 'Observation / QA Service',
    sublabel: 'Empirical Evidence Capture',
    icon: Eye,
  },
  VERIFICATION: {
    role: 'Deterministic Verifier',
    sublabel: 'Success Criteria Evaluation',
    icon: FileCheck2,
  },
  MEMORY_WRITEBACK: {
    role: 'Memory Service',
    sublabel: 'Authoritative Obsidian Writeback',
    icon: Database,
  },
};

export const AutonomousExecutionPipeline: React.FC<AutonomousExecutionPipelineProps> = ({
  stages,
  currentStageIndex,
  selectedStageIndex,
  onSelectStage,
  executiveTwin,
  selectedSpecialists,
  specialistExecutions = [],
  isExecuting = false,
  overallStatus = 'EXECUTING',
}) => {
  // Determine exact visual status of each card
  // STRICT RULE: Only ONE card is 'active' at a time!
  const getVisualStatus = (stage: WorkflowStage, idx: number): ExecutionVisualStatus => {
    if (stage.status === 'FAILED') return 'failed';
    if (stage.status === 'RECOVERING' || overallStatus === 'RECOVERING') {
      if (idx === currentStageIndex) return 'recovering';
    }
    // Only the exact active stage when running gets 'active'
    if (stage.status === 'RUNNING' || (isExecuting && idx === currentStageIndex)) {
      return 'active';
    }
    if (stage.status === 'COMPLETED') {
      if (stage.key === 'VERIFICATION' || stage.key === 'MEMORY_WRITEBACK') return 'verified';
      return 'completed';
    }
    return 'waiting';
  };

  const getStageSpecialistInfo = (key: StageKey) => {
    if (key === 'CONTROLLED_EXECUTION') {
      const activeExec =
        specialistExecutions.find((e) => e.status === 'RUNNING') ||
        specialistExecutions[specialistExecutions.length - 1];
      if (activeExec?.specialistName) {
        return activeExec.specialistName;
      }
      return 'Software Development Specialist';
    }
    if (key === 'SPECIALIST_DELEGATION') {
      return 'SecurityGuard Sandbox Assigner';
    }
    return null;
  };

  const activeWorkerName =
    stages[currentStageIndex]
      ? STAGE_METADATA[stages[currentStageIndex].key]?.role || stages[currentStageIndex].label
      : 'Master Orchestrator';

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0B0F19] p-5 md:p-6 shadow-2xl space-y-6">
      {/* Header bar with live active worker indicator */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="flex h-3 w-3 relative">
              <span
                className={`animate-ping absolute inline-flex h-full w-full rounded-full ${
                  isExecuting ? 'bg-indigo-400 opacity-75' : 'bg-emerald-400 opacity-40'
                }`}
              ></span>
              <span
                className={`relative inline-flex rounded-full h-3 w-3 ${
                  isExecuting ? 'bg-indigo-500' : 'bg-emerald-500'
                }`}
              ></span>
            </span>
            <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
              Autonomous Workforce Execution Pipeline
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Active Responsibility Handoff &bull; Single-Worker Ownership &bull; 10 Bounded Stages
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
          <div className="px-3 py-1.5 rounded-lg bg-indigo-950/60 border border-indigo-500/50 text-indigo-200 flex items-center gap-2 shadow-sm">
            <span className="text-indigo-400 uppercase font-semibold text-[10px]">Active Worker:</span>
            <span className="text-white font-bold tracking-tight">{activeWorkerName}</span>
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-slate-300 flex items-center gap-2">
            <span className="text-slate-500 uppercase font-semibold text-[10px]">Progress:</span>
            <span className="text-white font-bold">
              {currentStageIndex + 1} / {stages.length}
            </span>
          </div>
        </div>
      </div>

      {/* Strategic Twin Evaluation Callout */}
      <div className="p-3.5 rounded-xl border border-slate-800/90 bg-[#0F172A]/70 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2.5">
          <UserCheck className={`w-4 h-4 ${executiveTwin ? 'text-amber-400' : 'text-slate-500'}`} />
          <div>
            <span className="text-slate-400 font-semibold font-mono text-[11px] uppercase mr-2">
              Strategic Evaluation:
            </span>
            {executiveTwin ? (
              <span className="text-amber-300 font-bold">
                {executiveTwin.role} Digital Twin ({executiveTwin.twinId}) &bull; Conditionally Activated
              </span>
            ) : (
              <span className="text-slate-400">
                Executive Twin: <strong className="text-slate-300 font-medium">NOT REQUIRED</strong> (Direct autonomous specialist delegation)
              </span>
            )}
          </div>
        </div>
        {executiveTwin && (
          <Badge variant="conditional" size="sm">
            STRATEGIC TWIN ACTIVE
          </Badge>
        )}
      </div>

      {/* Grid of Stages with Moving Glowing Active Border */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
        {stages.map((stage, idx) => {
          const vStatus = getVisualStatus(stage, idx);
          const isSelected = selectedStageIndex === idx;
          const meta = STAGE_METADATA[stage.key] || {
            role: stage.label,
            sublabel: stage.shortDescription,
            icon: Cpu,
          };
          const Icon = meta.icon;
          const specialistInfo = getStageSpecialistInfo(stage.key);

          // Card Styles depending on status
          let cardStyle = 'bg-[#0F172A]/40 border-slate-800/60 text-slate-500 hover:border-slate-700 opacity-60';
          let iconColor = 'text-slate-500 bg-slate-800/40';
          let badgeVariant: 'default' | 'primary' | 'success' | 'danger' | 'warning' = 'default';
          let badgeText = '○ WAITING';

          if (vStatus === 'active') {
            cardStyle = 'active-stage-card border-indigo-500 text-white shadow-2xl ring-2 ring-indigo-400/80 opacity-100 scale-[1.02]';
            iconColor = 'text-cyan-300 bg-indigo-950 ring-2 ring-indigo-400';
            badgeVariant = 'primary';
            badgeText = '● WORKING';
          } else if (vStatus === 'recovering') {
            cardStyle = 'recovering-stage-card border-amber-500 text-amber-200 shadow-2xl ring-2 ring-amber-400/80 opacity-100 scale-[1.02]';
            iconColor = 'text-amber-400 bg-amber-950 ring-2 ring-amber-400';
            badgeVariant = 'warning';
            badgeText = '● RECOVERING';
          } else if (vStatus === 'completed' || vStatus === 'verified') {
            cardStyle = 'bg-[#0F172A]/90 border-emerald-800/60 text-slate-200 hover:border-emerald-700/80 opacity-90';
            iconColor = 'text-emerald-400 bg-emerald-950/80';
            badgeVariant = 'success';
            badgeText = vStatus === 'verified' ? '✓ VERIFIED' : '✓ COMPLETED';
          } else if (vStatus === 'failed') {
            cardStyle = 'bg-rose-950/40 border-rose-600 text-rose-200 ring-2 ring-rose-500/80 opacity-100';
            iconColor = 'text-rose-400 bg-rose-950';
            badgeVariant = 'danger';
            badgeText = '❌ FAILED';
          }

          return (
            <button
              key={stage.key}
              onClick={() => onSelectStage && onSelectStage(idx)}
              className={`p-4 rounded-xl border text-left transition-all duration-300 relative flex flex-col justify-between min-h-[155px] cursor-pointer group ${cardStyle} ${
                isSelected ? 'ring-2 ring-cyan-400 border-cyan-400' : ''
              }`}
            >
              {/* Card Header with Step Number & Status Beacon */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[11px] font-mono font-bold text-slate-400">
                      Step {String(idx + 1).padStart(2, '0')}
                    </span>
                    {vStatus === 'active' && (
                      <span className="flex h-2.5 w-2.5 relative">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500"></span>
                      </span>
                    )}
                    {vStatus === 'completed' && (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    )}
                  </div>

                  <div className={`p-1.5 rounded-lg ${iconColor} transition-transform group-hover:scale-110`}>
                    <Icon className="w-4 h-4" />
                  </div>
                </div>

                {/* Worker & Role Labels */}
                <div>
                  <div className={`text-xs font-bold tracking-tight line-clamp-1 ${vStatus === 'active' ? 'text-white text-[13px]' : 'text-slate-200'}`}>
                    {meta.role}
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono line-clamp-1 mt-0.5">
                    {stage.label}
                  </div>
                </div>
              </div>

              {/* Card Footer with Details & Badge */}
              <div className="space-y-2 mt-2 pt-2 border-t border-slate-800/80">
                {specialistInfo ? (
                  <div className="text-[10px] font-mono text-cyan-300 truncate bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-700/50">
                    Worker: {specialistInfo}
                  </div>
                ) : (
                  <p className="text-[10px] text-slate-400 line-clamp-1 leading-snug">
                    {stage.shortDescription || meta.sublabel}
                  </p>
                )}

                <div className="flex items-center justify-between">
                  <Badge
                    variant={badgeVariant}
                    size="sm"
                    dot={vStatus === 'active' || vStatus === 'recovering'}
                    className={vStatus === 'active' ? 'font-bold shadow-md shadow-indigo-500/30' : ''}
                  >
                    {badgeText}
                  </Badge>

                  {stage.durationMs !== undefined && stage.durationMs > 0 && (
                    <span className="text-[9px] font-mono text-slate-400 flex items-center gap-0.5">
                      <Clock className="w-2.5 h-2.5" />
                      {stage.durationMs}ms
                    </span>
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
