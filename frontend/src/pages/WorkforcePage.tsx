import React, { useState } from 'react';
import {
  ArrowRight,
  Bot,
  Brain,
  CheckCircle2,
  Cpu,
  Database,
  Eye,
  Layers,
  Play,
  RotateCcw,
  Search,
  ShieldCheck,
  Sparkles,
  Tag,
  Users,
  Zap,
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { PageId } from '../components/layout/Sidebar';
import { ExecutiveTwinModal } from '../components/workforce/ExecutiveTwinModal';
import { mockExecutiveTwins, mockSpecialists } from '../mock';
import { ExecutiveTwin, WorkflowRun, WorkRequest } from '../types';

interface WorkforcePageProps {
  onNavigate?: (page: PageId) => void;
  onSelectRun?: (run: WorkflowRun) => void;
}

export const WorkforcePage: React.FC<WorkforcePageProps> = ({
  onNavigate,
  onSelectRun,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [activeTwinModal, setActiveTwinModal] = useState<ExecutiveTwin | null>(null);

  const controlLayerModules = [
    { name: 'Master Orchestrator', role: 'Central Autonomous Control Loop', icon: Cpu, desc: 'Controls lifecycle state transitions, bounds enforcement, and empirical verification gating.' },
    { name: 'Perception / Intent Normalization', role: 'Intent Parsing & Capability Extraction', icon: Search, desc: 'Normalizes raw user requirements into declarative capability requirements and success criteria.' },
    { name: 'Reasoning Service & Validator', role: 'Bounded Structured Planning', icon: Brain, desc: 'Constructs validated acyclic plans without exposing sensitive reasoning chain-of-thought.' },
    { name: 'Capability Manager & Registry', role: 'Authoritative Worker Resolution', icon: Bot, desc: 'Matches declared plan capabilities against registered active specialist agents in the registry.' },
    { name: 'Observation / QA Service', role: 'Empirical Evidence Capture', icon: Eye, desc: 'Collects artifact SHA-256 checksums, test execution logs, and exit codes without hallucinated claims.' },
    { name: 'Reflection / Recovery Engine', role: 'Autonomous Failure Diagnosis', icon: RotateCcw, desc: 'Diagnoses execution errors and synthesizes bounded re-plans up to the max recovery budget (3/3).' },
    { name: 'Company Knowledge & Memory', role: 'Authoritative Obsidian Gateway', icon: Database, desc: 'Authoritative Obsidian abstraction ensuring unverified claims never pollute corporate memory.' },
  ];

  const categories = ['ALL', 'Engineering', 'Creative / Visual', 'Voice / Audio', 'Documents / Office', 'Marketing / Copy', 'Infrastructure', 'QA / Verification', 'Communication'];

  const filteredSpecialists = selectedCategory === 'ALL'
    ? mockSpecialists
    : mockSpecialists.filter(s => s.category === selectedCategory);

  const handleOpenTwin = (twin: ExecutiveTwin) => {
    setActiveTwinModal(twin);
  };

  const handleViewRunFromModal = (run: WorkflowRun) => {
    if (onSelectRun) onSelectRun(run);
    if (onNavigate) onNavigate('live-run');
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="space-y-1">
        <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Bot className="w-5 h-5 text-indigo-400" />
          Autonomous Workforce Registry
        </h1>
        <p className="text-xs md:text-sm text-slate-400">
          Hierarchical architecture: Control Layer, Conditional Strategic Executive Twins, and Sandboxed Specialist Workers.
        </p>
      </div>

      {/* 1. Control Layer */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
            <h2 className="text-sm font-bold text-slate-100 font-mono tracking-wider uppercase">
              1. Control Layer (Autonomous Brain & Orchestration)
            </h2>
          </div>
          <Badge variant="primary" size="sm">Core Infrastructure</Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {controlLayerModules.map((mod, idx) => {
            const Icon = mod.icon;
            return (
              <div
                key={idx}
                className="p-4 rounded-xl border border-slate-800 bg-[#111827] space-y-2 hover:border-slate-700 transition-colors shadow-sm"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-indigo-950/80 border border-indigo-800/60 flex items-center justify-center text-indigo-400 shrink-0">
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-200">{mod.name}</h3>
                    <p className="text-[10px] font-mono text-indigo-400">{mod.role}</p>
                  </div>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">{mod.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. Executive Twins (Interactive Cards) */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <h2 className="text-sm font-bold text-slate-100 font-mono tracking-wider uppercase">
              2. Strategic Decision Makers (Executive Twins)
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="conditional" size="sm">CONDITIONAL ACTIVATION</Badge>
            <span className="text-xs text-amber-300 font-mono text-[11px] flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5" />
              Click any Twin card to View & Activate Demo
            </span>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-amber-950/10 border border-amber-800/30 text-xs text-amber-200/90 leading-relaxed font-sans flex items-start gap-2.5">
          <ShieldCheck className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <strong>Architectural Rule:</strong> Executive Twins are conditional strategic decision-makers. They do NOT run continuously for every routine task and never execute system shell/file mutations directly.
          </div>
        </div>

        {/* Interactive Twin Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {mockExecutiveTwins.map((twin) => (
            <div
              key={twin.twinId}
              onClick={() => handleOpenTwin(twin)}
              className="p-5 rounded-xl border border-amber-900/40 bg-[#121826] space-y-3 hover:border-amber-500/80 hover:bg-[#152033] hover:shadow-lg hover:shadow-amber-950/30 transition-all cursor-pointer group relative flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-lg bg-amber-950/90 border border-amber-700/70 flex items-center justify-center font-bold font-mono text-amber-400 group-hover:scale-105 transition-transform shadow-sm">
                      {twin.role}
                    </div>
                    <div>
                      <h3 className="text-xs font-bold text-slate-100 group-hover:text-amber-200 transition-colors">
                        {twin.title}
                      </h3>
                      <span className="text-[10px] font-mono text-slate-500">{twin.twinId}</span>
                    </div>
                  </div>
                  <Badge variant="conditional" size="sm">CONDITIONAL</Badge>
                </div>

                <div className="text-xs text-slate-300 font-sans leading-relaxed">
                  <span className="text-slate-500 text-[11px] font-mono block">Strategic Scope:</span>
                  {twin.strategicScope}
                </div>

                <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-slate-800 text-[11px] text-slate-400 font-mono">
                  <span className="text-amber-400 font-semibold block mb-0.5">Activation Trigger:</span>
                  {twin.activationCondition}
                </div>
              </div>

              {/* Action Prompt Strip */}
              <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs font-mono">
                <span className="text-slate-500 text-[11px]">Click to Inspect</span>
                <span className="text-amber-400 font-semibold flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                  VIEW / ACTIVATE <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Specialist Workforce */}
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-500" />
            <h2 className="text-sm font-bold text-slate-100 font-mono tracking-wider uppercase">
              3. Specialist Workforce ({mockSpecialists.length} Registered Categories)
            </h2>
          </div>

          {/* Category Filter Pills */}
          <div className="flex flex-wrap gap-1.5 text-xs font-mono">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-2.5 py-1 rounded-md text-xs transition-all ${
                  selectedCategory === cat
                    ? 'bg-indigo-600 text-white font-semibold'
                    : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSpecialists.map((spec) => (
            <div
              key={spec.specialistId}
              className="p-4 rounded-xl border border-slate-800 bg-[#111827] space-y-3 hover:border-slate-700 transition-colors shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-bold text-slate-100">{spec.name}</h3>
                  <span className="text-[10px] font-mono text-indigo-400">{spec.category}</span>
                </div>
                <Badge variant={spec.status === 'ACTIVE' ? 'success' : 'default'} size="sm" dot>
                  {spec.status}
                </Badge>
              </div>

              <p className="text-[11px] text-slate-400 leading-relaxed">{spec.description}</p>

              {/* Capabilities */}
              <div className="space-y-1">
                <span className="text-[10px] font-mono uppercase text-slate-500 font-bold block">
                  Capabilities:
                </span>
                <div className="flex flex-wrap gap-1">
                  {spec.capabilities.map((c) => (
                    <span
                      key={c.name}
                      className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800"
                    >
                      {c.name} (v{c.version})
                    </span>
                  ))}
                </div>
              </div>

              {/* Authorized Tools */}
              <div className="pt-2 border-t border-slate-800/70 text-[10px] font-mono text-slate-500 flex items-center justify-between">
                <span>Security Level: <strong className="text-slate-300">{spec.securityLevel}</strong></span>
                <span>{spec.authorizedTools.length} Tools Authorized</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Active Executive Twin Detail & Demo Modal */}
      {activeTwinModal && (
        <ExecutiveTwinModal
          twin={activeTwinModal}
          onClose={() => setActiveTwinModal(null)}
          onViewRun={handleViewRunFromModal}
        />
      )}
    </div>
  );
};
