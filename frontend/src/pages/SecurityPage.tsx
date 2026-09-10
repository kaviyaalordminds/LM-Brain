import React from 'react';
import {
  AlertTriangle,
  ArrowDown,
  CheckCircle2,
  Cpu,
  FileCode,
  FolderGit2,
  Lock,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  Terminal,
  XCircle,
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Card } from '../components/common/Card';

export const SecurityPage: React.FC = () => {
  const boundaries = [
    { title: 'Reasoning Model', status: 'PLANNING ONLY ✓', desc: 'Synthesizes machine-validatable structured plans. NEVER granted raw execution handles or system credentials.', variant: 'success' as const },
    { title: 'Specialist Execution', status: 'CONTROLLED ✓', desc: 'All execution occurs via bounded specialist adapters with explicit tool permissions.', variant: 'success' as const },
    { title: 'SecurityGuard', status: 'ACTIVE ✓', desc: 'Hardened boundary intercepting twin actions, tool permissions, and unauthorized privilege escalations.', variant: 'success' as const },
    { title: 'Workspace Isolation', status: 'SANDBOXED ✓', desc: 'Path traversal attacks (../../) strictly blocked. File mutation restricted exclusively to assigned workspace sandbox.', variant: 'success' as const },
    { title: 'Files API', status: 'CONTROLLED ✓', desc: 'Bounded file creation, update, and inspection with size limits and MIME validation.', variant: 'success' as const },
    { title: 'Command Execution', status: 'ALLOWLISTED ✓', desc: 'Allowlisted commands only (npm build, test, lint). Parameter injection sanitization enforced.', variant: 'success' as const },
    { title: 'Git Integration', status: 'CONTROLLED ✓', desc: 'Automated commits and branches bounded strictly within local repository worktrees.', variant: 'success' as const },
    { title: 'Docker Integration', status: 'CONTROLLED ✓', desc: 'Isolated container lifecycles with strict CPU/memory limits and mock adapters for offline safety.', variant: 'success' as const },
    { title: 'Arbitrary Shell Access', status: 'BLOCKED ✓', desc: 'Raw os.system(), subprocess(), and unrestricted PowerShell commands are intercepted and rejected.', variant: 'danger' as const },
  ];

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="space-y-1">
        <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          Security Boundaries & Architectural Guardrails
        </h1>
        <p className="text-xs md:text-sm text-slate-400">
          Enforces zero-trust execution boundaries: Reasoning models plan, SecurityGuard verifies, and Specialists execute in isolated sandboxes.
        </p>
      </div>

      {/* Security Architecture Flow Diagram */}
      <Card
        title="Execution Boundary Guard Architecture"
        subtitle="Visual representation of SecurityGuard protection layers"
        icon={<Lock className="w-4 h-4 text-emerald-400" />}
        badge={<Badge variant="authoritative" size="sm">ZERO TRUST</Badge>}
      >
        <div className="p-6 rounded-xl bg-[#080C14] border border-slate-800 text-center font-mono text-xs space-y-4">
          <div className="max-w-md mx-auto space-y-3">
            <div className="p-3 rounded-lg bg-indigo-950/60 border border-indigo-700/60 text-indigo-300 font-bold">
              Reasoning Engine (LLM)
              <span className="text-[10px] text-indigo-400 block font-normal">Planning & Intent Normalization ONLY</span>
            </div>

            <div className="text-slate-500 font-bold flex justify-center items-center gap-1">
              <ArrowDown className="w-4 h-4 text-slate-500" />
              <span>Emits Validated Declarative Plan</span>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 font-bold">
              Specialist Execution Engine
              <span className="text-[10px] text-slate-400 block font-normal">Subtask Decomposition & Registry Assignment</span>
            </div>

            <div className="text-slate-500 font-bold flex justify-center items-center gap-1">
              <ArrowDown className="w-4 h-4 text-emerald-500 animate-bounce" />
              <span className="text-emerald-400">Mandatory Security Verification</span>
            </div>

            <div className="p-4 rounded-xl bg-emerald-950/70 border border-emerald-500/80 text-emerald-300 font-bold text-sm shadow-lg shadow-emerald-950/40 flex items-center justify-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              SecurityGuard Boundary
            </div>

            <div className="text-slate-500 font-bold flex justify-center items-center gap-1">
              <ArrowDown className="w-4 h-4 text-slate-500" />
              <span>Allowlisted Operations Only</span>
            </div>

            <div className="p-3.5 rounded-lg bg-cyan-950/50 border border-cyan-800/60 text-cyan-300 font-semibold space-y-1">
              <span>Controlled Capabilities (Sandboxed)</span>
              <div className="grid grid-cols-3 gap-1.5 text-[10px] pt-1">
                <span className="bg-slate-900/80 p-1 rounded border border-slate-800">Workspace Sandbox</span>
                <span className="bg-slate-900/80 p-1 rounded border border-slate-800">Files API</span>
                <span className="bg-slate-900/80 p-1 rounded border border-slate-800">Allowlisted Commands</span>
                <span className="bg-slate-900/80 p-1 rounded border border-slate-800">Git Worktree</span>
                <span className="bg-slate-900/80 p-1 rounded border border-slate-800">Docker Isolated</span>
                <span className="bg-slate-900/80 p-1 rounded border border-slate-800">ASR Audio Service</span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Security Boundaries Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {boundaries.map((b, idx) => (
          <div
            key={idx}
            className="p-4 rounded-xl border border-slate-800 bg-[#111827] space-y-2 hover:border-slate-700 transition-colors shadow-sm"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-200">{b.title}</h3>
              <Badge variant={b.variant} size="sm" dot>{b.status}</Badge>
            </div>
            <p className="text-[11px] text-slate-400 font-sans leading-relaxed">{b.desc}</p>
          </div>
        ))}
      </div>

      {/* Threat Mitigation Summary */}
      <Card
        title="Threat Mitigation Matrix"
        subtitle="Hardened protections against common agentic execution vulnerabilities"
        icon={<ShieldAlert className="w-4 h-4 text-amber-400" />}
      >
        <div className="overflow-x-auto text-xs font-mono">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase">
                <th className="pb-3 font-semibold">ATTACK VECTOR</th>
                <th className="pb-3 font-semibold">INTERCEPTING BOUNDARY</th>
                <th className="pb-3 font-semibold">STATUS</th>
                <th className="pb-3 font-semibold">TEST COVERAGE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              <tr>
                <td className="py-3 font-bold text-slate-300">PowerShell / Bash Command Injection</td>
                <td className="py-3 text-slate-400">SecurityGuard + CommandExecutor</td>
                <td className="py-3"><Badge variant="danger" size="sm">BLOCKED</Badge></td>
                <td className="py-3 text-emerald-400">test_9_security_rejection_of_powershell</td>
              </tr>
              <tr>
                <td className="py-3 font-bold text-slate-300">Path Traversal (../../etc/passwd)</td>
                <td className="py-3 text-slate-400">SoftwareWorkspaceAdapter</td>
                <td className="py-3"><Badge variant="danger" size="sm">BLOCKED</Badge></td>
                <td className="py-3 text-emerald-400">test_6_controlled_failure_recovery</td>
              </tr>
              <tr>
                <td className="py-3 font-bold text-slate-300">Executive Twin Direct System Mutation</td>
                <td className="py-3 text-slate-400">SecurityGuard.validate_twin_action()</td>
                <td className="py-3"><Badge variant="danger" size="sm">BLOCKED</Badge></td>
                <td className="py-3 text-emerald-400">test_12_security_guard_blocks_unauthorized</td>
              </tr>
              <tr>
                <td className="py-3 font-bold text-slate-300">Infinite Execution Loop Exhaustion</td>
                <td className="py-3 text-slate-400">AutonomousControlLoop Bounds Limit</td>
                <td className="py-3"><Badge variant="warning" size="sm">BOUNDED (3 Max)</Badge></td>
                <td className="py-3 text-emerald-400">test_8_bounded_repeated_failure</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
