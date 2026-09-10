import React from 'react';
import {
  ArrowDown,
  ArrowRight,
  Bot,
  Brain,
  CheckCircle2,
  Cpu,
  Database,
  Eye,
  FileCheck2,
  FolderGit2,
  GitFork,
  Layers,
  Lock,
  RotateCcw,
  Search,
  ShieldCheck,
  Terminal,
  User,
  Zap,
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Card } from '../components/common/Card';

export const ArchitecturePage: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="space-y-1">
        <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <GitFork className="w-5 h-5 text-indigo-400" />
          Autonomous AI Workforce Visual Architecture Map
        </h1>
        <p className="text-xs md:text-sm text-slate-400">
          Complete structural mapping from User Requirement to Verified Outcome and Authoritative Memory Writeback.
        </p>
      </div>

      {/* Main Architecture Diagram Container */}
      <Card
        title="Complete Autonomous Control Flow Architecture"
        subtitle="End-to-end dataflow between perception, reasoning, security boundaries, and specialist execution"
        icon={<Layers className="w-4 h-4 text-indigo-400" />}
        badge={<Badge variant="primary" size="sm">LM-BRAIN ARCHITECTURE</Badge>}
      >
        <div className="p-6 rounded-2xl bg-[#080C14] border border-slate-800 font-mono text-xs space-y-6">
          {/* Level 1: User */}
          <div className="flex justify-center">
            <div className="px-6 py-3 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 font-bold flex items-center gap-2 shadow-md">
              <User className="w-4 h-4 text-indigo-400" />
              <span>USER BUSINESS REQUIREMENT</span>
            </div>
          </div>

          <div className="flex justify-center text-slate-500">
            <ArrowDown className="w-5 h-5" />
          </div>

          {/* Level 2: Master Orchestrator */}
          <div className="flex justify-center">
            <div className="px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-950 via-indigo-900 to-indigo-950 border-2 border-indigo-500 text-white font-extrabold text-sm shadow-xl shadow-indigo-950/60 flex items-center gap-3">
              <Cpu className="w-5 h-5 text-indigo-300" />
              <div>
                <div>MASTER ORCHESTRATOR</div>
                <div className="text-[10px] text-indigo-200 font-normal">Autonomous Control Loop & Bounds Manager</div>
              </div>
            </div>
          </div>

          <div className="flex justify-center text-slate-500">
            <ArrowDown className="w-5 h-5" />
          </div>

          {/* Level 3: Triad (Perception, Knowledge, Reasoning) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto">
            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 text-center space-y-1">
              <Search className="w-5 h-5 text-indigo-400 mx-auto" />
              <div className="font-bold text-slate-200">PERCEPTION</div>
              <div className="text-[10px] text-slate-400">Intent Normalization & Capability Needs</div>
            </div>

            <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-700/60 text-center space-y-1">
              <Database className="w-5 h-5 text-emerald-400 mx-auto" />
              <div className="font-bold text-emerald-300">COMPANY KNOWLEDGE</div>
              <div className="text-[10px] text-emerald-400/80 font-bold">Authoritative Obsidian Vault</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 text-center space-y-1">
              <Brain className="w-5 h-5 text-indigo-400 mx-auto" />
              <div className="font-bold text-slate-200">REASONING ENGINE</div>
              <div className="text-[10px] text-slate-400">Declarative Structured Plan (No CoT)</div>
            </div>
          </div>

          <div className="flex justify-center text-slate-500">
            <ArrowDown className="w-5 h-5" />
          </div>

          {/* Level 4: Capability Manager */}
          <div className="flex justify-center">
            <div className="px-6 py-3 rounded-xl bg-slate-900 border border-slate-700 text-slate-200 font-bold text-xs flex items-center gap-2">
              <Bot className="w-4 h-4 text-cyan-400" />
              <span>CAPABILITY MANAGER & REGISTRY</span>
            </div>
          </div>

          <div className="flex justify-center text-slate-500">
            <ArrowDown className="w-5 h-5" />
          </div>

          {/* Level 5: Split (Executive Twins vs Specialists) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl mx-auto">
            <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-700/60 space-y-2 text-center">
              <div className="font-bold text-amber-300 flex items-center justify-center gap-1.5">
                <span>EXECUTIVE TWINS</span>
                <Badge variant="conditional" size="sm">CONDITIONAL</Badge>
              </div>
              <p className="text-[10px] text-slate-400 font-sans">
                CEO, COO, CTO, CMO, CFO. Activated conditionally only when strategic analysis is required.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-700/60 space-y-2 text-center">
              <div className="font-bold text-indigo-300 flex items-center justify-center gap-1.5">
                <span>SPECIALISTS WORKFORCE</span>
                <Badge variant="primary" size="sm">16 CATEGORIES</Badge>
              </div>
              <p className="text-[10px] text-slate-400 font-sans">
                Software Dev, Web Dev, Poster, Logo, Audio, Graphic, Document, PPT, Deployment, etc.
              </p>
            </div>
          </div>

          <div className="flex justify-center text-slate-500">
            <ArrowDown className="w-5 h-5" />
          </div>

          {/* Level 6: Specialist Execution Engine */}
          <div className="flex justify-center">
            <div className="px-6 py-3 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 font-bold flex items-center gap-2">
              <Cpu className="w-4 h-4 text-indigo-400" />
              <span>SPECIALIST EXECUTION ENGINE</span>
            </div>
          </div>

          <div className="flex justify-center text-emerald-500 font-bold flex items-center gap-1">
            <ArrowDown className="w-5 h-5 animate-bounce" />
            <span className="text-[10px] uppercase">Mandatory Security Barrier</span>
          </div>

          {/* Level 7: SecurityGuard */}
          <div className="flex justify-center">
            <div className="px-8 py-4 rounded-xl bg-emerald-950/90 border-2 border-emerald-500 text-emerald-200 font-extrabold text-sm shadow-xl shadow-emerald-950/60 flex items-center gap-3">
              <ShieldCheck className="w-6 h-6 text-emerald-400" />
              <div>
                <div>SECURITYGUARD</div>
                <div className="text-[10px] text-emerald-300 font-normal">Zero-Trust Command, Path & Privilege Interceptor</div>
              </div>
            </div>
          </div>

          <div className="flex justify-center text-slate-500">
            <ArrowDown className="w-5 h-5" />
          </div>

          {/* Level 8: Controlled Capabilities */}
          <div className="p-4 rounded-xl bg-[#0E1526] border border-cyan-800/60 max-w-3xl mx-auto space-y-2 text-center">
            <span className="font-bold text-cyan-300 text-xs uppercase tracking-wider block">
              Controlled Capabilities (Strictly Sandboxed)
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-[10px]">
              <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300 font-semibold">Workspace</div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300 font-semibold">Files API</div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300 font-semibold">Commands</div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300 font-semibold">Git Worktree</div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300 font-semibold">Docker Box</div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300 font-semibold">ASR Service</div>
            </div>
          </div>

          <div className="flex justify-center text-slate-500">
            <ArrowDown className="w-5 h-5" />
          </div>

          {/* Level 9: Observation / QA */}
          <div className="flex justify-center">
            <div className="px-6 py-3 rounded-xl bg-slate-900 border border-slate-700 text-slate-200 font-bold flex items-center gap-2">
              <Eye className="w-4 h-4 text-emerald-400" />
              <span>OBSERVATION / QA & EMPIRICAL EVIDENCE</span>
            </div>
          </div>

          <div className="flex justify-center text-slate-500">
            <ArrowDown className="w-5 h-5" />
          </div>

          {/* Level 10: Fork (Verification & Memory Writeback vs Reflection & Replan) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {/* Success Branch */}
            <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-600/60 space-y-3">
              <div className="font-bold text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" />
                <span>SUCCESS OUTCOME</span>
              </div>
              <div className="p-3 rounded bg-slate-900/90 border border-slate-800 text-[11px] space-y-1">
                <div className="text-white font-semibold">1. Empirical Verification (7/7 Criteria)</div>
                <div className="text-emerald-400 font-semibold">2. Memory Writeback to Company Obsidian</div>
                <div className="text-slate-400 text-[10px]">Authoritative record approved & persisted</div>
              </div>
            </div>

            {/* Failure Branch */}
            <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-600/60 space-y-3">
              <div className="font-bold text-amber-400 flex items-center gap-1.5">
                <RotateCcw className="w-4 h-4" />
                <span>FAILURE BRANCH</span>
              </div>
              <div className="p-3 rounded bg-slate-900/90 border border-slate-800 text-[11px] space-y-1">
                <div className="text-amber-300 font-semibold">1. Failure Observation Recorded</div>
                <div className="text-amber-300 font-semibold">2. Reasoning Reflection & Diagnosis</div>
                <div className="text-slate-300 font-semibold">3. Bounded Re-Plan & Retry (Max 3 Attempts)</div>
                <div className="text-rose-400 text-[10px]">No infinite loops. Clean bounded termination.</div>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
