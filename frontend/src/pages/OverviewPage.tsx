import React from 'react';
import {
  Activity,
  ArrowRight,
  Bot,
  Brain,
  CheckCircle2,
  Database,
  FileCheck2,
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
import { mockRuns, mockSpecialists } from '../mock';
import { WorkflowRun, WorkRequest } from '../types';

interface OverviewPageProps {
  onNavigate: (page: PageId) => void;
  onStartRun: (request: WorkRequest, type?: 'STANDARD' | 'CONTROLLED_FAILURE' | 'BOUNDED_FAILURE' | 'STRATEGIC_TWIN') => void;
  onSelectRun: (run: WorkflowRun) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  onNavigate,
  onStartRun,
  onSelectRun,
}) => {
  const primaryDemoRequest: WorkRequest = {
    requestId: 'req_landing_page_01',
    userGoal: `Create a small company landing page using the company's approved company information.

Include:
- company name
- company description
- services/products
- contact information

Create the project in the controlled software development workspace.
Validate the generated project.
Only report completion after verification.
Record the approved completion state in company memory.`,
    requireMemoryWriteback: true,
    requireTwinEvaluation: true,
    availableCapabilities: ['web_development', 'software_development', 'file_operations', 'build_validation'],
  };

  return (
    <div className="space-y-6">
      {/* Hero Header Banner */}
      <div className="p-6 md:p-8 rounded-2xl bg-gradient-to-r from-[#111827] via-[#131C2E] to-[#0B0F19] border border-slate-800 shadow-xl relative overflow-hidden">
        <div className="max-w-3xl space-y-3 relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/80 border border-indigo-700/60 text-indigo-300 text-xs font-mono font-medium">
            <Sparkles className="w-3.5 h-3.5" />
            Autonomous AI Workforce Control Center
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
            Autonomous Workforce
          </h1>
          <p className="text-base text-indigo-200/90 font-medium">
            Turn requirements into verified outcomes.
          </p>
          <p className="text-xs md:text-sm text-slate-400 leading-relaxed max-w-2xl">
            Accepts raw business requirements and autonomously normalizes intent, queries authoritative Company Obsidian knowledge, synthesizes bounded declarative plans, delegates to specialist agents, and executes inside sandboxed boundaries with strict empirical verification.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-3">
            <Button
              variant="primary"
              size="md"
              icon={<Play className="w-4 h-4 fill-white" />}
              onClick={() => {
                onStartRun(primaryDemoRequest, 'STANDARD');
                onNavigate('live-run');
              }}
            >
              Start Primary Demo (Landing Page)
            </Button>
            <Button
              variant="outline"
              size="md"
              icon={<ArrowRight className="w-4 h-4" />}
              iconPosition="right"
              onClick={() => onNavigate('new-work')}
            >
              Submit Custom Work
            </Button>
          </div>
        </div>
      </div>

      {/* Enterprise System Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card variant="default" className="p-0">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>SYSTEM</span>
            <Badge variant="success" size="sm" dot>Operational</Badge>
          </div>
          <div className="text-2xl font-bold text-white mt-2 font-mono">100%</div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            SecurityGuard Active
          </div>
        </Card>

        <Card variant="default" className="p-0">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>ACTIVE RUNS</span>
            <Badge variant="primary" size="sm" dot>LIVE</Badge>
          </div>
          <div className="text-2xl font-bold text-white mt-2 font-mono">1 Active</div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
            <Activity className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
            RUN-001 in flight
          </div>
        </Card>

        <Card variant="default" className="p-0">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>AVAILABLE WORKERS</span>
            <Badge variant="info" size="sm">Registry</Badge>
          </div>
          <div className="text-2xl font-bold text-white mt-2 font-mono">
            {mockSpecialists.length} Specialists
          </div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
            <Bot className="w-3.5 h-3.5 text-cyan-400" />
            5 Conditional Twins
          </div>
        </Card>

        <Card variant="default" className="p-0">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>KNOWLEDGE SOURCE</span>
            <Badge variant="authoritative" size="sm">AUTHORITY</Badge>
          </div>
          <div className="text-lg font-bold text-emerald-400 mt-2 font-mono truncate">
            Company Obsidian
          </div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
            <Database className="w-3.5 h-3.5 text-emerald-400" />
            Authoritative Truth Vault
          </div>
        </Card>
      </div>

      {/* Quick Demonstration Capabilities Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          onClick={() => {
            onStartRun(primaryDemoRequest, 'STANDARD');
            onNavigate('live-run');
          }}
          className="p-5 rounded-xl border border-slate-800 bg-[#111827] hover:border-indigo-500/60 transition-all cursor-pointer group shadow-sm"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-950/80 border border-indigo-800/60 flex items-center justify-center text-indigo-400">
              <Zap className="w-4 h-4" />
            </div>
            <Badge variant="primary" size="sm">Demo 1</Badge>
          </div>
          <h3 className="text-sm font-bold text-slate-100 group-hover:text-indigo-300 transition-colors">
            Autonomous Landing Page Synthesis
          </h3>
          <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Watches a request flow end-to-end through perception, Obsidian retrieval, reasoning, specialist delegation, and verified memory writeback.
          </p>
        </div>

        <div
          onClick={() => {
            onStartRun(
              {
                requestId: 'req_fail_rec_demo',
                userGoal: 'Create company landing page with simulated controlled failure in build step',
                requireMemoryWriteback: true,
                requireTwinEvaluation: false,
                availableCapabilities: ['web_development', 'file_operations'],
              },
              'CONTROLLED_FAILURE'
            );
            onNavigate('live-run');
          }}
          className="p-5 rounded-xl border border-slate-800 bg-[#111827] hover:border-amber-500/60 transition-all cursor-pointer group shadow-sm"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-8 h-8 rounded-lg bg-amber-950/80 border border-amber-800/60 flex items-center justify-center text-amber-400">
              <RotateCcw className="w-4 h-4" />
            </div>
            <Badge variant="warning" size="sm">Demo 2</Badge>
          </div>
          <h3 className="text-sm font-bold text-slate-100 group-hover:text-amber-300 transition-colors">
            Controlled Failure & Reflection Recovery
          </h3>
          <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Witnesses execution failure, failure observation capture, reasoning reflection diagnosis, bounded re-planning, retry, and verified recovery.
          </p>
        </div>

        <div
          onClick={() => {
            onStartRun(
              {
                requestId: 'req_cmo_twin_demo',
                userGoal: 'Create a complete marketing launch strategy for our new AMR-500 product line.',
                requireMemoryWriteback: true,
                requireTwinEvaluation: true,
                availableCapabilities: ['content_creation', 'poster_design', 'graphic_design', 'ppt'],
              },
              'STRATEGIC_TWIN'
            );
            onNavigate('live-run');
          }}
          className="p-5 rounded-xl border border-slate-800 bg-[#111827] hover:border-cyan-500/60 transition-all cursor-pointer group shadow-sm"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-950/80 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
              <Brain className="w-4 h-4" />
            </div>
            <Badge variant="info" size="sm">Demo 3</Badge>
          </div>
          <h3 className="text-sm font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
            Conditional CMO Executive Twin Activation
          </h3>
          <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Demonstrates Master Orchestrator detecting strategic marketing scope and conditionally activating the CMO Executive Twin for campaign decomposition.
          </p>
        </div>
      </div>

      {/* Recent Autonomous Runs Preview Table */}
      <Card
        title="Recent Autonomous Runs"
        subtitle="Historical verification timeline & completed workflows"
        headerAction={
          <Button variant="ghost" size="sm" onClick={() => onNavigate('runs')}>
            View All Runs →
          </Button>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="pb-3 font-semibold">RUN ID</th>
                <th className="pb-3 font-semibold">GOAL / REQUIREMENT</th>
                <th className="pb-3 font-semibold">STATUS</th>
                <th className="pb-3 font-semibold">DURATION</th>
                <th className="pb-3 font-semibold">VERIFICATION</th>
                <th className="pb-3 font-semibold text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {mockRuns.map((run) => (
                <tr key={run.runId} className="hover:bg-slate-900/40 transition-colors">
                  <td className="py-3 font-bold text-slate-200">{run.runId}</td>
                  <td className="py-3 text-slate-300 font-sans max-w-xs truncate">
                    {run.userGoal.split('\n')[0]}
                  </td>
                  <td className="py-3">
                    {run.status === 'COMPLETED' ? (
                      <Badge variant="success" size="sm" dot>COMPLETED</Badge>
                    ) : run.status === 'FAILED' ? (
                      <Badge variant="danger" size="sm" dot>FAILED — BOUNDED</Badge>
                    ) : (
                      <Badge variant="warning" size="sm" dot>{run.status}</Badge>
                    )}
                  </td>
                  <td className="py-3 text-slate-400">{run.durationSeconds}s</td>
                  <td className="py-3">
                    {run.status === 'COMPLETED' ? (
                      <span className="text-emerald-400 font-semibold flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> VERIFIED
                      </span>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>
                  <td className="py-3 text-right">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        onSelectRun(run);
                        onNavigate('live-run');
                      }}
                    >
                      Inspect Timeline
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
