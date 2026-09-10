import React from 'react';
import { AlertTriangle, CheckCircle2, Database, ShieldCheck, XCircle } from 'lucide-react';
import { MemoryWritebackRecord } from '../../types';
import { Badge } from '../common/Badge';
import { Card } from '../common/Card';

interface MemoryWritebackViewProps {
  record?: MemoryWritebackRecord;
}

export const MemoryWritebackView: React.FC<MemoryWritebackViewProps> = ({
  record,
}) => {
  if (!record) {
    return (
      <Card
        title="Company Memory Writeback (Obsidian)"
        subtitle="Persistence of verified completion state to authoritative Company Obsidian"
        icon={<Database className="w-4 h-4 text-emerald-400" />}
      >
        <div className="py-6 text-center text-xs text-slate-500 font-mono">
          Writeback executes strictly after Verification phase succeeds...
        </div>
      </Card>
    );
  }

  const isCompleted = record.status === 'COMPLETED';
  const isNotPerformed = record.status === 'NOT_PERFORMED';

  return (
    <Card
      title="Company Memory Writeback (Obsidian Persistence)"
      subtitle="Authoritative writeback gateway — Protects Company Obsidian from unverified facts"
      icon={<Database className="w-4 h-4 text-emerald-400" />}
      badge={
        isCompleted ? (
          <Badge variant="authoritative" size="sm" dot>PERSISTED ✓</Badge>
        ) : (
          <Badge variant="warning" size="sm" dot>BLOCKED / NOT PERFORMED</Badge>
        )
      }
    >
      <div className="space-y-4">
        {isCompleted ? (
          <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-800/40 space-y-3 text-xs font-mono">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-emerald-400 font-bold">
                <CheckCircle2 className="w-4 h-4" />
                <span>Writeback Status: COMPLETED</span>
              </div>
              <Badge variant="success" size="sm">APPROVED</Badge>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-300">
              <div>
                <span className="text-slate-500">Source: </span>
                <strong>{record.source}</strong>
              </div>
              <div>
                <span className="text-slate-500">Target Vault: </span>
                <strong>{record.targetVaultPath}</strong>
              </div>
            </div>

            <div className="p-2.5 rounded bg-slate-900/90 border border-slate-800 text-slate-200">
              <span className="text-slate-500 text-[10px] block uppercase">Recorded State:</span>
              <span>{record.recordedState}</span>
            </div>
          </div>
        ) : (
          <div className="p-4 rounded-lg bg-amber-950/20 border border-amber-800/40 space-y-2 text-xs font-mono">
            <div className="flex items-center gap-2 text-amber-400 font-bold">
              <AlertTriangle className="w-4 h-4" />
              <span>Writeback: NOT PERFORMED</span>
            </div>
            <p className="text-slate-300">
              <strong>Reason: </strong>
              {record.reason || 'Workflow not verified. Unverified state prevented from corrupting Company Obsidian.'}
            </p>
          </div>
        )}
      </div>
    </Card>
  );
};
