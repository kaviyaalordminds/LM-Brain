import React, { useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  Bot,
  Brain,
  CheckCircle2,
  Database,
  FileCode,
  Layers,
  Play,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { PageId } from '../components/layout/Sidebar';
import { WorkRequest } from '../types';

interface NewWorkPageProps {
  onNavigate: (page: PageId) => void;
  onStartRun: (request: WorkRequest, type?: 'STANDARD' | 'CONTROLLED_FAILURE' | 'BOUNDED_FAILURE' | 'STRATEGIC_TWIN') => void;
}

export const NewWorkPage: React.FC<NewWorkPageProps> = ({
  onNavigate,
  onStartRun,
}) => {
  const exampleRequests = [
    {
      id: 'landing-page',
      title: 'Create a company landing page (Primary Demo)',
      tag: 'Primary Demo',
      type: 'STANDARD' as const,
      text: `Create a small company landing page using the company's approved company information.

Include:
- company name
- company description
- services/products
- contact information

Create the project in the controlled software development workspace.
Validate the generated project.
Only report completion after verification.
Record the approved completion state in company memory.`,
    },
    {
      id: 'cmo-campaign',
      title: 'Prepare a marketing launch campaign (CMO Twin Demo)',
      tag: 'Strategic Twin',
      type: 'STRATEGIC_TWIN' as const,
      text: `Create a complete marketing launch strategy for our new AMR-500 autonomous warehouse robot product line.
Decompose brand positioning, campaign narrative, and visual collateral requirements.`,
    },
    {
      id: 'failure-recovery',
      title: 'Simulate controlled build failure & recovery',
      tag: 'Recovery Demo',
      type: 'CONTROLLED_FAILURE' as const,
      text: `Create company landing page with simulated controlled failure in build step.
Exercise observation capture, reasoning reflection diagnosis, re-planning, and verified recovery.`,
    },
    {
      id: 'repeated-failure',
      title: 'Simulate repeated failure exhaustion (Bounded Termination)',
      tag: 'Bounds Demo',
      type: 'BOUNDED_FAILURE' as const,
      text: `Execute database schema migration against unverified external endpoint.
Demonstrates clean termination after 3 recovery attempts without infinite loops.`,
    },
    {
      id: 'doc-generation',
      title: 'Generate project technical architecture documentation',
      tag: 'Documentation',
      type: 'STANDARD' as const,
      text: `Generate comprehensive system architecture documentation for NovaPulse Robotics telemetry pipeline.
Format in markdown and verify all terminology against Obsidian standards.`,
    },
  ];

  const [requestText, setRequestText] = useState(exampleRequests[0].text);
  const [selectedType, setSelectedType] = useState<'STANDARD' | 'CONTROLLED_FAILURE' | 'BOUNDED_FAILURE' | 'STRATEGIC_TWIN'>('STANDARD');
  const [requireMemoryWriteback, setRequireMemoryWriteback] = useState(true);
  const [requireTwinEvaluation, setRequireTwinEvaluation] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!requestText.trim()) return;

    const request: WorkRequest = {
      requestId: `req_${Date.now()}`,
      userGoal: requestText.trim(),
      requireMemoryWriteback,
      requireTwinEvaluation,
      availableCapabilities: ['web_development', 'software_development', 'file_operations', 'build_validation'],
    };

    onStartRun(request, selectedType);
    onNavigate('live-run');
  };

  const handleSelectExample = (example: typeof exampleRequests[0]) => {
    setRequestText(example.text);
    setSelectedType(example.type);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="space-y-1">
        <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-400" />
          Submit Business Requirement to Workforce
        </h1>
        <p className="text-xs md:text-sm text-slate-400">
          The Master Orchestrator will autonomously perceive, retrieve authoritative knowledge, synthesize a bounded plan, and execute via specialist agents.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Work Request Input Form */}
        <div className="lg:col-span-2 space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Card
              title="Work Request Specification"
              subtitle="What do you want the autonomous workforce to accomplish?"
              icon={<Bot className="w-4 h-4 text-indigo-400" />}
              badge={<Badge variant="primary" size="sm">Master Orchestrator</Badge>}
            >
              <div className="space-y-4">
                <div className="space-y-2">
                  <textarea
                    rows={8}
                    value={requestText}
                    onChange={(e) => setRequestText(e.target.value)}
                    placeholder="Enter business requirement in natural language..."
                    className="w-full rounded-lg bg-[#080C14] border border-slate-700/80 p-4 text-sm text-slate-100 placeholder-slate-500 font-sans focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/80 transition-all leading-relaxed"
                  />
                </div>

                {/* Configuration Toggles */}
                <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
                  <label className="flex items-center gap-2 text-slate-300 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={requireMemoryWriteback}
                      onChange={(e) => setRequireMemoryWriteback(e.target.checked)}
                      className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                    />
                    <Database className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Require Memory Writeback (Obsidian)</span>
                  </label>

                  <label className="flex items-center gap-2 text-slate-300 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={requireTwinEvaluation}
                      onChange={(e) => setRequireTwinEvaluation(e.target.checked)}
                      className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                    />
                    <Brain className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Enable Conditional Twin Evaluation</span>
                  </label>
                </div>

                {/* Submit Action */}
                <div className="flex items-center justify-between pt-2">
                  <span className="text-xs text-slate-500 font-mono">
                    Mode: <strong className="text-slate-300 font-semibold">{selectedType}</strong>
                  </span>
                  <Button
                    type="submit"
                    variant="primary"
                    size="lg"
                    icon={<Play className="w-4 h-4 fill-white" />}
                    className="shadow-lg shadow-indigo-900/50"
                  >
                    START WORK
                  </Button>
                </div>
              </div>
            </Card>
          </form>

          {/* Architectural Guardrails Reminder Card */}
          <div className="p-4 rounded-xl border border-slate-800 bg-[#0E1526]/50 flex items-start gap-3 text-xs text-slate-400">
            <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-semibold text-slate-200">Autonomous Execution Boundary Rules</span>
              <p className="leading-relaxed">
                Raw reasoning chain-of-thought is never executed directly. The reasoning model produces a structured plan, which is checked by SecurityGuard before specialist agents create files inside sandboxed workspaces.
              </p>
            </div>
          </div>
        </div>

        {/* Example Presets Sidebar */}
        <div className="space-y-3">
          <div className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 px-1">
            <Zap className="w-3.5 h-3.5 text-indigo-400" />
            Demonstration Presets
          </div>

          <div className="space-y-2">
            {exampleRequests.map((ex) => {
              const isSelected = requestText === ex.text;
              return (
                <button
                  key={ex.id}
                  onClick={() => handleSelectExample(ex)}
                  className={`w-full text-left p-3.5 rounded-xl border transition-all text-xs space-y-1.5 ${
                    isSelected
                      ? 'bg-indigo-950/70 border-indigo-500/80 text-white shadow-md ring-1 ring-indigo-500/50'
                      : 'bg-[#111827] border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-900'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200">{ex.title}</span>
                    <Badge variant={ex.type === 'CONTROLLED_FAILURE' ? 'warning' : ex.type === 'BOUNDED_FAILURE' ? 'danger' : 'primary'} size="sm">
                      {ex.tag}
                    </Badge>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                    {ex.text.split('\n')[0]}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
