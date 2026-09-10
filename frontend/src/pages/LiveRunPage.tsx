import React, { useState } from 'react';
import {
  Activity,
  AlertCircle,
  Archive,
  Bot,
  Brain,
  CheckCircle2,
  Cpu,
  Database,
  Eye,
  FileCheck2,
  FolderGit2,
  Layers,
  Pause,
  Play,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Terminal,
  Zap,
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { StatusIndicator } from '../components/common/StatusIndicator';
import { PageId } from '../components/layout/Sidebar';
import { CapabilitySelectionView } from '../components/run/CapabilitySelectionView';
import { CompanyKnowledgeView } from '../components/run/CompanyKnowledgeView';
import { EvidenceView } from '../components/run/EvidenceView';
import { MemoryWritebackView } from '../components/run/MemoryWritebackView';
import { ReasoningPlanView } from '../components/run/ReasoningPlanView';
import { RecoverySimulationPanel } from '../components/run/RecoverySimulationPanel';
import { SpecialistExecutionView } from '../components/run/SpecialistExecutionView';
import { ValidationView } from '../components/run/ValidationView';
import { VerificationView } from '../components/run/VerificationView';
import { WorkflowPipeline } from '../components/run/WorkflowPipeline';
import { WorkspaceFilesView } from '../components/run/WorkspaceFilesView';
import { WorkflowRun } from '../types';

interface LiveRunPageProps {
  run: WorkflowRun;
  isExecuting: boolean;
  selectedStageIndex: number;
  onSelectStageIndex: (idx: number) => void;
  onTriggerControlledFailure: () => void;
  onTriggerRepeatedFailure: () => void;
  onNavigate: (page: PageId) => void;
}

export const LiveRunPage: React.FC<LiveRunPageProps> = ({
  run,
  isExecuting,
  selectedStageIndex,
  onSelectStageIndex,
  onTriggerControlledFailure,
  onTriggerRepeatedFailure,
  onNavigate,
}) => {
  const [activeTab, setActiveTab] = useState<
    'pipeline' | 'reasoning' | 'knowledge' | 'capabilities' | 'execution' | 'workspace' | 'validation' | 'evidence' | 'verification' | 'memory'
  >('pipeline');

  const isCompleted = run.status === 'COMPLETED';
  const isFailed = run.status === 'FAILED';
  const isRecovering = run.status === 'RECOVERING';

  return (
    <div className="space-y-6">
      {/* Hero Header Section */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-[#111827] via-[#141E33] to-[#0D1322] border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1 min-w-0">
            <div className="flex items-center gap-3">
              <span className="text-sm font-mono font-bold text-indigo-400 bg-indigo-950/80 px-2.5 py-1 rounded border border-indigo-800/60">
                {run.runId}
              </span>
              <StatusIndicator status={run.status} size="lg" />
              {run.executiveTwinActivated && (
                <Badge variant="conditional" size="sm">
                  TWIN: {run.executiveTwinActivated.role} ACTIVATED
                </Badge>
              )}
            </div>
            <h1 className="text-lg md:text-xl font-bold text-white tracking-tight truncate max-w-3xl">
              {run.userGoal.split('\n')[0]}
            </h1>
          </div>

          <div className="flex flex-wrap items-center gap-3 font-mono text-xs">
            <div className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
              Duration: <strong className="text-white">{run.durationSeconds}s</strong>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-emerald-950/30 border border-emerald-800/60 text-emerald-300 flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5" />
              <span>Obsidian: <strong>Authoritative</strong></span>
            </div>
            <Button
              variant="outline"
              size="sm"
              icon={<RotateCcw className="w-3.5 h-3.5" />}
              onClick={() => onNavigate('new-work')}
            >
              New Run
            </Button>
          </div>
        </div>

        {/* Requirements Context Snippet */}
        <div className="text-xs text-slate-400 bg-[#080C14] p-3 rounded-lg border border-slate-800/80 font-sans leading-relaxed">
          <span className="text-[10px] font-mono uppercase text-slate-500 block mb-0.5 font-bold">
            Parsed Business Requirement:
          </span>
          <p className="line-clamp-2 text-slate-300">{run.userGoal}</p>
        </div>
      </div>

      {/* 10-Stage Autonomous Control Loop Pipeline */}
      <WorkflowPipeline
        stages={run.stages}
        currentStageIndex={run.currentStageIndex}
        selectedStageIndex={selectedStageIndex}
        onSelectStage={(idx) => {
          onSelectStageIndex(idx);
          // Auto switch to relevant tab
          const tabMap: Record<number, any> = {
            0: 'reasoning',
            1: 'knowledge',
            2: 'reasoning',
            3: 'reasoning',
            4: 'capabilities',
            5: 'execution',
            6: 'workspace',
            7: 'evidence',
            8: 'verification',
            9: 'memory',
          };
          if (tabMap[idx]) setActiveTab(tabMap[idx]);
        }}
      />

      {/* Failure & Bounded Recovery Simulation Controls */}
      <RecoverySimulationPanel
        recoveryHistory={run.recoveryHistory}
        onTriggerControlledFailure={onTriggerControlledFailure}
        onTriggerRepeatedFailure={onTriggerRepeatedFailure}
        isExecuting={isExecuting}
      />

      {/* Detailed Inspection Tab Navigation */}
      <div className="border-b border-slate-800 flex items-center gap-1 overflow-x-auto pb-1 text-xs font-mono">
        {[
          { id: 'pipeline', label: 'All Modules Overview', icon: Layers },
          { id: 'reasoning', label: 'Structured Plan (No CoT)', icon: Brain },
          { id: 'knowledge', label: 'Obsidian Knowledge', icon: Database },
          { id: 'capabilities', label: 'Capability Registry', icon: Bot },
          { id: 'execution', label: 'Specialist Engine', icon: Cpu },
          { id: 'workspace', label: 'Files API (Sandbox)', icon: FolderGit2 },
          { id: 'validation', label: 'Build & Tests', icon: Terminal },
          { id: 'evidence', label: 'Evidence Vault', icon: FileCheck2 },
          { id: 'verification', label: 'Verification', icon: CheckCircle2 },
          { id: 'memory', label: 'Memory Writeback', icon: Database },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-3 py-2 rounded-t-lg font-medium transition-all flex items-center gap-1.5 shrink-0 ${
                isActive
                  ? 'bg-slate-800 text-indigo-300 border-t-2 border-indigo-500 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Contents */}
      <div className="space-y-6">
        {activeTab === 'pipeline' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ReasoningPlanView plan={run.reasoningPlan} />
              <CompanyKnowledgeView documents={run.knowledgeRetrieved} />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <CapabilitySelectionView selectedSpecialists={run.selectedSpecialists} />
              <SpecialistExecutionView
                executions={run.specialistExecutions}
                workspaceId={run.runId.toLowerCase()}
                isExecuting={isExecuting}
              />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <WorkspaceFilesView files={run.workspaceFiles} workspaceId={run.runId.toLowerCase()} />
              <ValidationView validations={run.validations} />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <VerificationView checklist={run.verificationChecklist} isVerified={isCompleted} />
              <MemoryWritebackView record={run.memoryWriteback} />
            </div>
            <EvidenceView evidenceItems={run.evidenceItems} />
          </div>
        )}

        {activeTab === 'reasoning' && <ReasoningPlanView plan={run.reasoningPlan} />}
        {activeTab === 'knowledge' && <CompanyKnowledgeView documents={run.knowledgeRetrieved} />}
        {activeTab === 'capabilities' && <CapabilitySelectionView selectedSpecialists={run.selectedSpecialists} />}
        {activeTab === 'execution' && (
          <SpecialistExecutionView
            executions={run.specialistExecutions}
            workspaceId={run.runId.toLowerCase()}
            isExecuting={isExecuting}
          />
        )}
        {activeTab === 'workspace' && (
          <WorkspaceFilesView files={run.workspaceFiles} workspaceId={run.runId.toLowerCase()} />
        )}
        {activeTab === 'validation' && <ValidationView validations={run.validations} />}
        {activeTab === 'evidence' && <EvidenceView evidenceItems={run.evidenceItems} />}
        {activeTab === 'verification' && (
          <VerificationView checklist={run.verificationChecklist} isVerified={isCompleted} />
        )}
        {activeTab === 'memory' && <MemoryWritebackView record={run.memoryWriteback} />}
      </div>
    </div>
  );
};
