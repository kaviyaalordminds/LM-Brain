import React from 'react';
import { ArrowDown, CheckCircle2, Circle, Clock, Cpu, ShieldCheck, Terminal, Zap } from 'lucide-react';
import { StepExecutionRecord } from '../../types';
import { Badge } from '../common/Badge';
import { Card } from '../common/Card';

interface SpecialistExecutionViewProps {
  executions?: StepExecutionRecord[];
  workspaceId?: string;
  isExecuting?: boolean;
}

export const SpecialistExecutionView: React.FC<SpecialistExecutionViewProps> = ({
  executions = [],
  workspaceId = 'run-001',
  isExecuting = false,
}) => {
  return (
    <Card
      title="Specialist Execution Engine & Boundary Flow"
      subtitle="Execution Engine strictly routes through SecurityGuard to controlled sandbox capabilities"
      icon={<Cpu className="w-4 h-4 text-indigo-400" />}
      badge={<Badge variant="primary" size="sm" dot>{isExecuting ? 'ACTIVE' : 'READY'}</Badge>}
    >
      <div className="space-y-5">
        {/* Visual Architecture Flow Banner */}
        <div className="p-3.5 rounded-lg bg-[#080C14] border border-slate-800 text-xs font-mono">
          <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-2 font-bold">
            Controlled Execution Chain
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2 text-center">
            <div className="px-3 py-2 rounded bg-indigo-950/60 border border-indigo-800/60 text-indigo-300 font-semibold flex-1 min-w-[120px]">
              Specialist Agent
            </div>
            <span className="text-slate-600 font-bold">→</span>
            <div className="px-3 py-2 rounded bg-slate-900 border border-slate-700 text-slate-200 font-semibold flex-1 min-w-[130px]">
              Execution Engine
            </div>
            <span className="text-slate-600 font-bold">→</span>
            <div className="px-3 py-2 rounded bg-emerald-950/60 border border-emerald-700/60 text-emerald-300 font-semibold flex-1 min-w-[130px] flex items-center justify-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              SecurityGuard
            </div>
            <span className="text-slate-600 font-bold">→</span>
            <div className="px-3 py-2 rounded bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 font-semibold flex-1 min-w-[140px]">
              Controlled Capability
            </div>
          </div>
        </div>

        {/* Controlled Operations Checklist & Execution Log */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Operations Flow */}
          <div className="p-4 rounded-lg bg-slate-900/70 border border-slate-800 space-y-3">
            <div className="text-xs font-mono font-semibold text-slate-300 flex items-center justify-between">
              <span>Controlled Workspace Operations</span>
              <Badge variant="info" size="sm">Workspace: {workspaceId}</Badge>
            </div>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex items-center gap-2 text-emerald-400">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Create workspace sandbox</span>
              </div>
              <div className="flex items-center gap-2 text-emerald-400">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Create project files (index.html, styles.css, app.tsx)</span>
              </div>
              <div className="flex items-center gap-2 text-emerald-400">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Synthesize documentation (README.md)</span>
              </div>
              <div className="flex items-center gap-2 text-emerald-400">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Controlled build validation</span>
              </div>
              <div className="flex items-center gap-2 text-emerald-400">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Verification & Memory writeback</span>
              </div>
            </div>
          </div>

          {/* Active Specialists Executions */}
          <div className="p-4 rounded-lg bg-slate-900/70 border border-slate-800 space-y-3">
            <div className="text-xs font-mono font-semibold text-slate-300">
              Delegated Execution Records
            </div>
            {executions.length === 0 ? (
              <div className="py-4 text-center text-xs text-slate-500 font-mono">
                Executing sandboxed operations...
              </div>
            ) : (
              <div className="space-y-2">
                {executions.map((exec, idx) => (
                  <div key={idx} className="p-2.5 rounded bg-[#0B0F19] border border-slate-800/80 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">{exec.specialistName || exec.specialistId}</span>
                      <span className="text-[10px] font-mono text-emerald-400">✓ {exec.status}</span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono truncate">{exec.output}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};
