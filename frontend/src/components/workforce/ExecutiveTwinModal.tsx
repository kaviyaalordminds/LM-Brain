import React, { useEffect, useState } from 'react';
import {
  ArrowDown,
  ArrowRight,
  Bot,
  Brain,
  CheckCircle2,
  Cpu,
  Database,
  FileCheck2,
  Lock,
  Play,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Terminal,
  X,
  Zap,
} from 'lucide-react';
import { ExecutiveTwin, WorkflowRun, WorkRequest } from '../../types';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';

interface ExecutiveTwinModalProps {
  twin: ExecutiveTwin | null;
  onClose: () => void;
  onViewRun: (run: WorkflowRun) => void;
}

export const ExecutiveTwinModal: React.FC<ExecutiveTwinModalProps> = ({
  twin,
  onClose,
  onViewRun,
}) => {
  if (!twin) return null;

  // Preset demo prompts per Executive Twin
  const demoPrompts: Record<string, { prompt: string; capabilities: string[]; specialists: { name: string; role: string; task: string }[]; recommendation: string }> = {
    CMO: {
      prompt: 'Create a complete marketing launch strategy for our new product.',
      capabilities: ['content_creation', 'poster_design', 'graphic_design', 'ppt'],
      specialists: [
        { name: 'Content Creation Specialist', role: 'Marketing / Copy', task: 'Synthesize product launch narrative & press release' },
        { name: 'Poster Specialist', role: 'Creative / Visual', task: 'Compose marketing poster and digital banner vectors' },
        { name: 'Graphic Design Specialist', role: 'Creative / Visual', task: 'Render brand vector illustrations & icon assets' },
        { name: 'PPT / Presentation Specialist', role: 'Documents / Office', task: 'Structure executive launch pitch deck' },
      ],
      recommendation: 'Target enterprise supply chain leaders with a reliability-first narrative. Decompose into multi-channel press releases, visual posters, and technical launch decks.',
    },
    CEO: {
      prompt: 'Evaluate the strategic priorities for launching a new company product.',
      capabilities: ['content_creation', 'document', 'ppt', 'communication_response'],
      specialists: [
        { name: 'Content Creation Specialist', role: 'Strategy / Copy', task: 'Draft corporate executive vision brief' },
        { name: 'Document Specialist', role: 'Documents / Office', task: 'Synthesize organizational governance memorandum' },
        { name: 'PPT / Presentation Specialist', role: 'Documents / Office', task: 'Construct board of directors strategy presentation' },
        { name: 'Communication / Response Specialist', role: 'Communication', task: 'Format verified executive summary communication' },
      ],
      recommendation: 'Prioritize strategic market expansion in autonomous logistics. Align departmental OKRs and initiate cross-functional readiness reviews.',
    },
    COO: {
      prompt: 'Optimize the operational workflow and resource allocation for a new product launch.',
      capabilities: ['software_development', 'deployment', 'spreadsheet', 'communication_response'],
      specialists: [
        { name: 'Software Development Specialist', role: 'Engineering', task: 'Analyze CI/CD pipeline capacity and workflow bottlenecks' },
        { name: 'Deployment Specialist', role: 'Infrastructure', task: 'Verify staging container resource limits and cluster elasticity' },
        { name: 'Spreadsheet Specialist', role: 'Documents / Office', task: 'Model operational resource and compute allocation table' },
        { name: 'Communication / Response Specialist', role: 'Communication', task: 'Generate operations readiness status briefing' },
      ],
      recommendation: 'Establish high-throughput execution pipelines, allocate staging compute buffers, and enforce bounded 3-retry recovery limits across all automated workflows.',
    },
    CTO: {
      prompt: 'Evaluate the technical architecture and security requirements for a new product platform.',
      capabilities: ['software_development', 'web_development', 'build_validation', 'deployment'],
      specialists: [
        { name: 'Software Development Specialist', role: 'Engineering', task: 'Define sandboxed module boundaries and API interfaces' },
        { name: 'Web Development Specialist', role: 'Engineering', task: 'Implement responsive frontend architecture' },
        { name: 'Build & Test Specialist', role: 'QA / Verification', task: 'Configure strict build validation & empirical test suites' },
        { name: 'Deployment Specialist', role: 'Infrastructure', task: 'Package isolated container deployment manifest' },
      ],
      recommendation: 'Enforce zero-trust architecture: SecurityGuard must intercept all execution calls, workspace isolation must be sandboxed, and arbitrary shell execution remains blocked.',
    },
    CFO: {
      prompt: 'Evaluate the budget, ROI and financial risks for a new product launch.',
      capabilities: ['spreadsheet', 'document', 'ppt', 'communication_response'],
      specialists: [
        { name: 'Spreadsheet Specialist', role: 'Documents / Office', task: 'Model cash flow, compute unit costs, and ROI sensitivity projections' },
        { name: 'Document Specialist', role: 'Documents / Office', task: 'Author financial risk assessment and governance memo' },
        { name: 'PPT / Presentation Specialist', role: 'Documents / Office', task: 'Structure financial deck for quarterly risk committee' },
        { name: 'Communication / Response Specialist', role: 'Communication', task: 'Synthesize executive budget sign-off summary' },
      ],
      recommendation: 'Approve compute budget with 18% contingency buffer. Financial risk is modeled as LOW under strict execution time and token consumption limits.',
    },
  };

  const config = demoPrompts[twin.role] || demoPrompts.CMO;

  // Progressive demo execution state
  const [demoState, setDemoState] = useState<'IDLE' | 'PROGRESSING' | 'COMPLETED'>('IDLE');
  const [activeStepIndex, setActiveStepIndex] = useState<number>(0);
  const [generatedRun, setGeneratedRun] = useState<WorkflowRun | null>(null);

  const steps = [
    { label: 'USER REQUEST', desc: 'Business goal received' },
    { label: 'STRATEGIC SCOPE DETECTED', desc: `${twin.role} scope analyzed by Master Orchestrator` },
    { label: `${twin.role} TWIN ACTIVATED`, desc: 'Conditional strategic review initiated' },
    { label: `${twin.role} STRATEGIC ANALYSIS`, desc: 'High-level business decomposition synthesized' },
    { label: 'CAPABILITY REQUIREMENTS', desc: 'Identified concrete required capabilities' },
    { label: 'SPECIALIST SELECTION', desc: `${config.specialists.length} registered specialists matched in registry` },
    { label: 'SPECIALIST EXECUTION', desc: 'Concrete execution inside sandboxed boundaries' },
    { label: 'REVIEW / VERIFICATION', desc: `${twin.role} review policy passed (Evidence-backed)` },
    { label: 'COMPLETED', desc: 'Verified strategic outcome recorded in memory' },
  ];

  const handleStartTwinDemo = () => {
    setDemoState('PROGRESSING');
    setActiveStepIndex(0);

    // Progressive deterministic step timer
    let current = 0;
    const interval = setInterval(() => {
      current += 1;
      if (current < steps.length) {
        setActiveStepIndex(current);
      } else {
        clearInterval(interval);
        setDemoState('COMPLETED');

        // Create completed WorkflowRun object matching LiveRun format
        const runId = `RUN-${twin.role}-${Math.floor(Math.random() * 900) + 100}`;
        const newRun: WorkflowRun = {
          runId,
          requestId: `req_${twin.role.toLowerCase()}_${Date.now()}`,
          userGoal: config.prompt,
          status: 'COMPLETED',
          durationSeconds: 12.4,
          isDemo: true,
          startedAt: new Date(Date.now() - 12400).toISOString(),
          completedAt: new Date().toISOString(),
          currentStageIndex: 9,
          executiveTwinActivated: twin,
          stages: [
            { key: 'PERCEPTION', label: 'Perception', shortDescription: `Strategic ${twin.role} scope detected`, status: 'COMPLETED', durationMs: 250, timestamp: '10:00:01' },
            { key: 'COMPANY_KNOWLEDGE', label: 'Company Knowledge', shortDescription: 'Retrieved authoritative facts from Company Obsidian', status: 'COMPLETED', durationMs: 380, timestamp: '10:00:01' },
            { key: 'REASONING', label: 'Reasoning', shortDescription: `${twin.role} Twin activated for strategic decomposition`, status: 'COMPLETED', durationMs: 780, timestamp: '10:00:02' },
            { key: 'PLAN_VALIDATION', label: 'Plan Validation', shortDescription: 'Validated strategic plan & capability requirements', status: 'COMPLETED', durationMs: 150, timestamp: '10:00:03' },
            { key: 'CAPABILITY_SELECTION', label: 'Capability Selection', shortDescription: `Selected ${config.specialists.length} specialists from registry`, status: 'COMPLETED', durationMs: 210, timestamp: '10:00:03' },
            { key: 'SPECIALIST_DELEGATION', label: 'Specialist Delegation', shortDescription: 'Assigned bounded tasks under SecurityGuard rules', status: 'COMPLETED', durationMs: 220, timestamp: '10:00:04' },
            { key: 'CONTROLLED_EXECUTION', label: 'Controlled Execution', shortDescription: 'Executed concrete files in sandbox', status: 'COMPLETED', durationMs: 3100, timestamp: '10:00:07' },
            { key: 'OBSERVATION_QA', label: 'Observation / QA', shortDescription: 'Captured empirical evidence & execution hashes', status: 'COMPLETED', durationMs: 650, timestamp: '10:00:08' },
            { key: 'VERIFICATION', label: 'Verification', shortDescription: `${twin.role} strategic review confirmed all criteria passed`, status: 'COMPLETED', durationMs: 540, timestamp: '10:00:09' },
            { key: 'MEMORY_WRITEBACK', label: 'Memory Writeback', shortDescription: 'Persisted approved strategic record to Obsidian', status: 'COMPLETED', durationMs: 480, timestamp: '10:00:10' },
          ],
          reasoningPlan: {
            planId: `plan_${twin.role.toLowerCase()}_demo`,
            goal: config.prompt,
            dependencies: [],
            successCriteria: [
              `${twin.role} strategic review confirms policy alignment`,
              'All required specialist collateral generated and verified',
              'Controlled execution verified in sandboxed workspace',
              'Approved outcome persisted in Company Obsidian',
            ],
            assumptions: ['Company profile in Obsidian is authoritative'],
            requiredCapabilities: config.capabilities,
            confidence: 0.98,
            verificationRequirements: [`${twin.role} review approval`, 'Empirical evidence recorded'],
            steps: config.specialists.map((s, idx) => ({
              stepId: String(idx + 1).padStart(2, '0'),
              objective: s.task,
              requiredCapability: config.capabilities[idx] || 'strategic_task',
              specialistRole: s.name,
              dependencies: idx > 0 ? [String(idx).padStart(2, '0')] : [],
              expectedOutput: `${s.task} synthesized and verified`,
              verificationRequirement: 'Artifact non-empty & valid',
              riskLevel: 'LOW',
              parameters: {},
            })),
          },
          knowledgeRetrieved: [],
          selectedSpecialists: config.capabilities.reduce((acc, cap, i) => {
            acc[cap] = config.specialists[i]?.name || 'Specialist';
            return acc;
          }, {} as Record<string, string>),
          specialistExecutions: config.specialists.map((s, idx) => ({
            stepId: String(idx + 1).padStart(2, '0'),
            objective: s.task,
            requiredCapability: config.capabilities[idx] || 'strategic_task',
            specialistId: s.name,
            specialistName: s.name,
            status: 'COMPLETED',
            output: `Synthesized verified output for ${s.task}`,
            artifacts: [`${s.name.replace(/\s+/g, '_')}_output.md`],
            evidenceIds: [`ev_${twin.role.toLowerCase()}_${idx + 1}`],
            durationSeconds: 1.2,
          })),
          workspaceFiles: config.specialists.map((s, i) => ({
            path: `${s.name.replace(/\s+/g, '_')}_collateral_${i + 1}.md`,
            operation: 'CREATE',
            status: 'SUCCESS',
            sizeBytes: 1540 + i * 200,
            mimeType: 'text/markdown',
            contentSnippet: `# ${s.task}\nProduced by ${s.name} under ${twin.role} Executive Twin strategic direction.\nStatus: VERIFIED`,
          })),
          validations: [
            {
              operation: 'LINT',
              command: 'lint-policy-compliance',
              status: 'PASSED',
              exitCode: 0,
              output: `All generated documents comply with ${twin.role} strategic review guidelines.`,
              restrictedShell: true,
            },
          ],
          evidenceItems: [
            {
              evidenceId: `ev_${twin.role.toLowerCase()}_01`,
              category: 'VERIFICATION',
              timestamp: new Date().toISOString(),
              systemGenerated: true,
              description: `${twin.role} Executive Review outcome: APPROVED (100% confidence)`,
            },
          ],
          verificationChecklist: [
            { criterion: `${twin.role} strategic review completed`, passed: true, details: 'Review outcome: APPROVED' },
            { criterion: 'Capability decomposition validated', passed: true, details: `${config.capabilities.length} capabilities resolved` },
            { criterion: 'Specialist collateral synthesized in sandbox', passed: true, details: `${config.specialists.length} artifacts present` },
            { criterion: 'Memory writeback recorded to Obsidian', passed: true, details: 'Vault persistence approved' },
          ],
          memoryWriteback: {
            status: 'COMPLETED',
            source: 'Company Obsidian',
            targetVaultPath: `company_knowledge/strategy/${twin.role.toLowerCase()}_decision.md`,
            recordedState: `${twin.role} strategic evaluation complete: ${config.recommendation}`,
            approvalStatus: 'APPROVED',
            factsPersisted: [
              { statement: `${twin.role} strategic recommendation approved: ${config.recommendation}`, state: 'FACT', source: `workflow:${runId}` },
            ],
            timestamp: new Date().toISOString(),
          },
          recoveryHistory: [],
          auditEvents: [],
        };

        setGeneratedRun(newRun);
      }
    }, 450);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-[#0F172A] border border-amber-900/60 rounded-2xl max-w-3xl w-full shadow-2xl overflow-hidden my-8 max-h-[90vh] flex flex-col text-slate-100 font-sans">
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-800 bg-gradient-to-r from-amber-950/40 via-slate-900 to-[#0F172A] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-950/90 border border-amber-700/80 flex items-center justify-center font-mono font-extrabold text-amber-400 text-lg shadow-md">
              {twin.role}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white">{twin.title}</h2>
                <Badge variant="conditional" size="sm">CONDITIONAL ACTIVATION</Badge>
              </div>
              <span className="text-xs font-mono text-slate-400">{twin.twinId}</span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
          {/* 1. Twin Profile & Conditions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1.5">
              <span className="text-[10px] uppercase font-mono font-bold text-slate-500 block">
                Strategic Decision Scope
              </span>
              <p className="text-slate-200 leading-relaxed">{twin.strategicScope}</p>
            </div>

            <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-800/40 space-y-1.5">
              <span className="text-[10px] uppercase font-mono font-bold text-amber-400 block">
                Activation Trigger Condition
              </span>
              <p className="text-slate-300 leading-relaxed font-mono text-[11px]">{twin.activationCondition}</p>
            </div>
          </div>

          {/* 2. Executive Twin Boundary Principle */}
          <div className="p-4 rounded-xl bg-[#080C14] border border-indigo-950 space-y-3 font-mono">
            <div className="flex items-center justify-between">
              <span className="text-indigo-400 font-bold tracking-wider uppercase text-[10px] flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5" />
                EXECUTIVE TWIN BOUNDARY PRINCIPLE
              </span>
              <span className="text-[10px] text-rose-400 font-bold">MUTATION GUARDED</span>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-1 text-center text-[11px]">
              <div className="p-2 rounded bg-amber-950/60 border border-amber-700/60 text-amber-300 font-semibold flex-1 min-w-[110px]">
                {twin.role} Twin (Strategic Reasoning)
              </div>
              <span className="text-slate-600 font-bold">→</span>
              <div className="p-2 rounded bg-slate-900 border border-slate-700 text-slate-200 font-semibold flex-1 min-w-[110px]">
                Capability Specs
              </div>
              <span className="text-slate-600 font-bold">→</span>
              <div className="p-2 rounded bg-indigo-950/60 border border-indigo-700/60 text-indigo-300 font-semibold flex-1 min-w-[110px]">
                Specialist Workforce (Concrete Work)
              </div>
              <span className="text-slate-600 font-bold">→</span>
              <div className="p-2 rounded bg-emerald-950/60 border border-emerald-700/60 text-emerald-300 font-semibold flex-1 min-w-[110px]">
                Controlled Sandbox
              </div>
            </div>

            <p className="text-slate-400 text-[11px] font-sans pt-1">
              <strong className="text-slate-200">Rule:</strong> Executive Twins NEVER directly execute shell commands, filesystem mutations, or raw code. They synthesize strategic direction and delegate concrete subtasks to registered specialist workers.
            </p>
          </div>

          {/* 3. Demo Trigger Action Box */}
          <div className="p-5 rounded-xl border border-amber-900/50 bg-[#121826] space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="space-y-0.5">
                <span className="text-xs font-bold text-amber-300 flex items-center gap-1.5 font-mono">
                  <Sparkles className="w-4 h-4" />
                  Deterministic Strategic Twin Demo
                </span>
                <p className="text-slate-400 text-[11px]">
                  Demonstrates Master Orchestrator detecting strategic scope and activating the {twin.role} Twin.
                </p>
              </div>

              {demoState === 'IDLE' && (
                <Button
                  variant="amber"
                  size="md"
                  onClick={handleStartTwinDemo}
                  icon={<Play className="w-4 h-4 fill-current" />}
                >
                  ACTIVATE TWIN DEMO
                </Button>
              )}
            </div>

            <div className="p-3 rounded-lg bg-[#080C14] border border-slate-800 text-slate-300 font-mono text-[11px]">
              <span className="text-slate-500 text-[10px] block uppercase font-bold mb-1">Demo Work Request:</span>
              <span className="text-indigo-200">"{config.prompt}"</span>
            </div>

            {/* Progressive Workflow Stepper */}
            {demoState !== 'IDLE' && (
              <div className="space-y-3 pt-2">
                <div className="text-[10px] font-mono uppercase text-slate-400 font-bold tracking-wider">
                  Autonomous Progression Flow ({activeStepIndex + 1}/{steps.length})
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {steps.map((st, i) => {
                    const isDone = activeStepIndex >= i;
                    const isCurrent = activeStepIndex === i && demoState === 'PROGRESSING';

                    return (
                      <div
                        key={i}
                        className={`p-2.5 rounded-lg border text-[11px] font-mono transition-all space-y-0.5 ${
                          isCurrent
                            ? 'bg-amber-950/50 border-amber-500 text-amber-200 shadow-md ring-1 ring-amber-500'
                            : isDone
                            ? 'bg-emerald-950/20 border-emerald-800/40 text-slate-300'
                            : 'bg-slate-900/40 border-slate-800 text-slate-500'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold truncate">{st.label}</span>
                          {isDone ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                          ) : (
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-600" />
                          )}
                        </div>
                        <span className="text-[10px] text-slate-400 block truncate">{st.desc}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Completed Strategic Outcome Card */}
            {demoState === 'COMPLETED' && (
              <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-600/60 space-y-4 font-mono">
                <div className="flex items-center justify-between border-b border-emerald-800/60 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="font-bold text-emerald-400 text-xs tracking-wider uppercase">
                      {twin.role} ACTIVATED — STRATEGIC DECISION COMPLETE
                    </span>
                  </div>
                  <Badge variant="authoritative" size="sm">VERIFIED ✓</Badge>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">
                    Strategic Recommendation:
                  </span>
                  <p className="text-slate-200 font-sans text-xs bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 leading-relaxed">
                    {config.recommendation}
                  </p>
                </div>

                {/* Selected Specialists Breakdown */}
                <div className="space-y-1.5">
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">
                    Specialist Workforce Selected by Registry:
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {config.specialists.map((s, idx) => (
                      <div
                        key={idx}
                        className="p-2 rounded bg-slate-900 border border-slate-800 text-[11px] flex items-center justify-between"
                      >
                        <div>
                          <div className="font-bold text-slate-200">{s.name}</div>
                          <div className="text-[10px] text-slate-500 font-sans">{s.task}</div>
                        </div>
                        <Badge variant="default" size="sm">ACTIVE</Badge>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Evidence & Memory Confirmation */}
                <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3 text-[11px]">
                  <span className="text-slate-400">
                    Memory Writeback: <strong className="text-emerald-400">Recorded to Company Obsidian</strong>
                  </span>

                  {generatedRun && (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => {
                        onViewRun(generatedRun);
                        onClose();
                      }}
                      icon={<ArrowRight className="w-3.5 h-3.5" />}
                      iconPosition="right"
                    >
                      VIEW RUN IN LIVE TIMELINE
                    </Button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 bg-[#0B0F19] flex items-center justify-between shrink-0 text-xs font-mono">
          <span className="text-slate-500">
            {twin.role} Twin Status: <strong className="text-amber-400">CONDITIONAL (Scope Bounded)</strong>
          </span>
          <Button variant="outline" size="sm" onClick={onClose}>
            Close Detail
          </Button>
        </div>
      </div>
    </div>
  );
};
