import React from 'react';
import { AlertCircle, CheckCircle2, ShieldCheck, Terminal, XCircle } from 'lucide-react';
import { ValidationRecord } from '../../types';
import { Badge } from '../common/Badge';
import { Card } from '../common/Card';
import { CodeBlock } from '../common/CodeBlock';

interface ValidationViewProps {
  validations?: ValidationRecord[];
}

export const ValidationView: React.FC<ValidationViewProps> = ({
  validations = [],
}) => {
  return (
    <Card
      title="Controlled Command Execution & Build / Test Validation"
      subtitle="Allowlisted command executor — Raw arbitrary shell execution is blocked by SecurityGuard"
      icon={<Terminal className="w-4 h-4 text-emerald-400" />}
      badge={<Badge variant="authoritative" size="sm">RESTRICTED SHELL ✓</Badge>}
    >
      <div className="space-y-4">
        {/* Security Rule Header */}
        <div className="p-3 rounded-lg bg-indigo-950/20 border border-indigo-800/40 flex items-center justify-between text-xs font-mono text-indigo-300">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-indigo-400" />
            <span>Security Rule: Command Execution is Allowlist-Only</span>
          </div>
          <span className="text-slate-400">Arbitrary Shell: <strong className="text-rose-400">BLOCKED</strong></span>
        </div>

        {/* Validation Records */}
        {validations.length === 0 ? (
          <div className="py-6 text-center text-xs text-slate-500 font-mono">
            Awaiting build and test validation stage...
          </div>
        ) : (
          <div className="space-y-3">
            {validations.map((v, idx) => {
              const isPassed = v.status === 'PASSED';
              const isFailed = v.status === 'FAILED';

              return (
                <div
                  key={idx}
                  className={`p-3.5 rounded-lg border text-xs font-mono space-y-2 ${
                    isPassed
                      ? 'bg-emerald-950/10 border-emerald-800/40'
                      : isFailed
                      ? 'bg-rose-950/20 border-rose-800/50'
                      : 'bg-slate-900 border-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-200 uppercase tracking-wider">
                        Operation: {v.operation}
                      </span>
                      <span className="text-slate-500">|</span>
                      <span className="text-slate-400 font-normal">$ {v.command}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] text-slate-500">Exit Code: {v.exitCode}</span>
                      {isPassed ? (
                        <Badge variant="success" size="sm" dot>PASSED</Badge>
                      ) : isFailed ? (
                        <Badge variant="danger" size="sm" dot>FAILED</Badge>
                      ) : (
                        <Badge variant="primary" size="sm" dot>RUNNING</Badge>
                      )}
                    </div>
                  </div>

                  <CodeBlock
                    code={v.output}
                    language="shell"
                    title={`Controlled Output (${v.operation})`}
                    maxHeight="max-h-36"
                  />
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Card>
  );
};
