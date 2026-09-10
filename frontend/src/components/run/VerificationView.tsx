import React from 'react';
import { CheckCircle2, FileCheck2, ShieldAlert, ShieldCheck, XCircle } from 'lucide-react';
import { Badge } from '../common/Badge';
import { Card } from '../common/Card';

interface VerificationViewProps {
  checklist?: { criterion: string; passed: boolean; details?: string }[];
  isVerified?: boolean;
}

export const VerificationView: React.FC<VerificationViewProps> = ({
  checklist = [],
  isVerified = false,
}) => {
  return (
    <Card
      title="Empirical Verification & Acceptance Criteria"
      subtitle="Final assertion checkpoint — Completion is declared ONLY after rigorous verification"
      icon={<FileCheck2 className="w-4 h-4 text-emerald-400" />}
      badge={
        isVerified ? (
          <Badge variant="authoritative" size="sm" dot>VERIFIED ✓</Badge>
        ) : (
          <Badge variant="warning" size="sm" dot>VERIFICATION PENDING</Badge>
        )
      }
    >
      <div className="space-y-4">
        <div className="p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-800/40 flex items-center justify-between text-xs font-mono">
          <span className="text-slate-300">
            Rule: <strong>No SUCCESS state is published without empirical verification</strong>
          </span>
          <span className="text-emerald-400 font-bold">
            {isVerified ? 'STATUS: VERIFIED' : 'STATUS: EVALUATING'}
          </span>
        </div>

        {checklist.length === 0 ? (
          <div className="py-6 text-center text-xs text-slate-500 font-mono">
            Awaiting verification phase...
          </div>
        ) : (
          <div className="space-y-2">
            {checklist.map((item, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex items-start justify-between gap-3 text-xs"
              >
                <div className="flex items-start gap-2.5">
                  {item.passed ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  )}
                  <div>
                    <span className="text-slate-200 font-medium">{item.criterion}</span>
                    {item.details && (
                      <p className="text-[11px] text-slate-400 font-mono mt-0.5">{item.details}</p>
                    )}
                  </div>
                </div>
                <span className={`text-[10px] font-mono font-bold uppercase tracking-wider shrink-0 ${
                  item.passed ? 'text-emerald-400' : 'text-rose-400'
                }`}>
                  {item.passed ? 'PASSED' : 'FAILED'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
};
