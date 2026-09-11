import React from 'react';
import {
  Activity,
  ArrowRight,
  Bot,
  Brain,
  CheckCircle2,
  Cpu,
  Database,
  FileCode,
  FolderGit2,
  ShieldCheck,
  Sparkles,
  Terminal,
  Zap,
} from 'lucide-react';
import {
  OrchestrationStatus,
  ReasoningPlan,
  SpecialistMetadata,
  StageKey,
  StepExecutionRecord,
  WorkflowStage,
  WorkspaceFile,
} from '../../types';
import { Badge } from '../common/Badge';

interface CurrentActivityPanelProps {
  currentStage?: WorkflowStage;
  currentStageIndex: number;
  totalStages: number;
  reasoningPlan?: ReasoningPlan;
  specialistExecutions?: StepExecutionRecord[];
  workspaceFiles?: WorkspaceFile[];
  selectedSpecialists?: Record<string, string>;
  isExecuting?: boolean;
  status?: OrchestrationStatus;
}

export const CurrentActivityPanel: React.FC<CurrentActivityPanelProps> = ({
  currentStage,
  currentStageIndex,
  totalStages,
  reasoningPlan,
  specialistExecutions = [],
  workspaceFiles = [],
  selectedSpecialists = {},
  isExecuting = false,
  status = 'EXECUTING',
}) => {
  // Derive current specialist & active action
  const activeExecution =
    specialistExecutions.find((e) => e.status === 'RUNNING') ||
    specialistExecutions[specialistExecutions.length - 1];

  const latestFile = workspaceFiles[workspaceFiles.length - 1];

  let activeWorkerName = 'Master Orchestrator';
  let activeRole = 'Global Workforce Coordination';
  let activeAction = currentStage?.shortDescription || 'Orchestrating autonomous workflow execution...';
  let activeCapability = 'workflow_orchestration';
  let activeTarget = 'workspaces/default';

  if (currentStage) {
    switch (currentStage.key) {
      case 'PERCEPTION':
        activeWorkerName = 'Perception Agent';
        activeRole = 'Requirement & Intent Normalization';
        activeCapability = 'intent_normalization';
        activeTarget = 'System Input Stream';
        break;
      case 'COMPANY_KNOWLEDGE':
        activeWorkerName = 'Company Knowledge Service';
        activeRole = 'Obsidian Vault Memory Retrieval';
        activeCapability = 'company_knowledge_retrieval';
        activeTarget = 'company_knowledge/default/company_profile.md';
        break;
      case 'REASONING':
        activeWorkerName = 'Reasoning Engine';
        activeRole = 'Deterministic Plan Synthesis';
        activeCapability = 'structured_dag_planning';
        activeTarget = reasoningPlan ? `${reasoningPlan.steps.length} Steps Formulated` : 'Structured DAG';
        break;
      case 'PLAN_VALIDATION':
        activeWorkerName = 'Plan Safety Validator';
        activeRole = 'DAG Cycle & Boundary Enforcement';
        activeCapability = 'plan_bounds_validation';
        activeTarget = 'StrictBoundsValidator Engine';
        break;
      case 'CAPABILITY_SELECTION':
        activeWorkerName = 'Capability Matcher';
        activeRole = 'Specialist Registry Discovery';
        activeCapability = 'specialist_discovery';
        activeTarget = Object.keys(selectedSpecialists).join(', ') || 'Specialist Registry';
        break;
      case 'SPECIALIST_DELEGATION':
        activeWorkerName = 'Specialist Delegator';
        activeRole = 'SecurityGuard Sandboxing';
        activeCapability = 'task_delegation';
        activeTarget = 'SecurityGuard Sandbox Context';
        break;
      case 'CONTROLLED_EXECUTION':
        activeWorkerName = activeExecution?.specialistName || 'Software Development Specialist';
        activeRole = 'Specialist Worker';
        activeCapability = activeExecution?.requiredCapability || 'file_create';
        activeTarget = latestFile?.path ? `workspaces/default/${latestFile.path}` : 'workspaces/default/index.html';
        activeAction = activeExecution?.objective || latestFile ? `Synthesizing ${latestFile.path}` : 'Executing controlled capability...';
        break;
      case 'OBSERVATION_QA':
        activeWorkerName = 'Observation / QA Service';
        activeRole = 'Empirical Evidence Capture';
        activeCapability = 'evidence_collection';
        activeTarget = 'Evidence Vault';
        break;
      case 'VERIFICATION':
        activeWorkerName = 'Deterministic Verifier';
        activeRole = 'Success Criteria Evaluation';
        activeCapability = 'success_criteria_verification';
        activeTarget = 'Empirical Verification Matrix';
        break;
      case 'MEMORY_WRITEBACK':
        activeWorkerName = 'Memory Service';
        activeRole = 'Obsidian Memory Persistence';
        activeCapability = 'memory_writeback';
        activeTarget = 'Obsidian Vault / Memory Document';
        break;
    }
  }

  const isCompleted = status === 'COMPLETED';
  const isFailed = status === 'FAILED';
  const isRecovering = status === 'RECOVERING' || currentStage?.status === 'RECOVERING';

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0F172A] p-5 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-bold text-white tracking-tight uppercase">
            Live Workforce Activity
          </h3>
        </div>
        <Badge
          variant={isCompleted ? 'success' : isFailed ? 'danger' : isRecovering ? 'warning' : 'primary'}
          size="sm"
          dot={isExecuting}
        >
          {isCompleted ? 'COMPLETED' : isFailed ? 'FAILED' : isRecovering ? 'RECOVERING' : 'EXECUTING'}
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
        {/* Active Worker */}
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-1">
          <span className="text-[10px] text-slate-500 uppercase font-semibold block">
            Current Worker
          </span>
          <div className="text-indigo-300 font-bold text-sm truncate flex items-center gap-1.5 font-sans">
            <Cpu className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
            <span className="truncate">{activeWorkerName}</span>
          </div>
          <span className="text-[11px] text-slate-400 truncate block font-sans">
            {activeRole}
          </span>
        </div>

        {/* Current Objective / Action */}
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-1">
          <span className="text-[10px] text-slate-500 uppercase font-semibold block">
            Current Objective
          </span>
          <div className="text-slate-200 font-medium text-xs line-clamp-2 font-sans">
            {activeAction}
          </div>
        </div>

        {/* Capability / Tool */}
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-1">
          <span className="text-[10px] text-slate-500 uppercase font-semibold block">
            Active Capability
          </span>
          <div className="text-cyan-300 font-semibold truncate flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
            <span className="truncate">{activeCapability}</span>
          </div>
          <span className="text-[10px] text-slate-400 font-mono block">
            Bounded via SecurityGuard
          </span>
        </div>

        {/* Target Workspace / Path */}
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-1">
          <span className="text-[10px] text-slate-500 uppercase font-semibold block">
            Target / Workspace
          </span>
          <div className="text-emerald-300 font-semibold truncate flex items-center gap-1.5">
            <FolderGit2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span className="truncate">{activeTarget}</span>
          </div>
          <span className="text-[10px] text-slate-400 font-mono block">
            Path Security: Strict
          </span>
        </div>
      </div>
    </div>
  );
};
