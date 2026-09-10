import React from 'react';
import { CheckCircle2, Database, FileText, Info, ShieldCheck } from 'lucide-react';
import { ObsidianDocument } from '../../types';
import { Badge } from '../common/Badge';
import { Card } from '../common/Card';

interface CompanyKnowledgeViewProps {
  documents?: ObsidianDocument[];
  status?: string;
}

export const CompanyKnowledgeView: React.FC<CompanyKnowledgeViewProps> = ({
  documents,
  status = 'RETRIEVED',
}) => {
  if (!documents || documents.length === 0) {
    return (
      <Card
        title="Company Knowledge & Memory Layer"
        subtitle="Authoritative facts retrieved via CompanyKnowledgeService"
        icon={<Database className="w-4 h-4 text-emerald-400" />}
      >
        <div className="py-6 text-center text-xs text-slate-500 font-mono">
          Waiting for Knowledge Retrieval stage to query Company Obsidian vault...
        </div>
      </Card>
    );
  }

  const primaryDoc = documents[0];

  return (
    <Card
      title="Company Knowledge Layer (Authoritative Source)"
      subtitle="Retrieved via CompanyKnowledgeService backend abstraction"
      icon={<Database className="w-4 h-4 text-emerald-400" />}
      badge={<Badge variant="authoritative" size="sm">AUTHORITATIVE</Badge>}
    >
      <div className="space-y-4">
        {/* Source and Authority Banner */}
        <div className="p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-800/40 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-2 text-emerald-300">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Source: <strong>Company Obsidian Vault</strong></span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-slate-400">
              Authority: <strong className="text-emerald-400">AUTHORITATIVE</strong>
            </span>
            <span className="text-slate-400">
              Status: <strong className="text-emerald-400">✓ {status}</strong>
            </span>
          </div>
        </div>

        {/* Facts List */}
        <div className="space-y-2">
          <div className="text-xs font-mono font-semibold text-slate-300 flex items-center justify-between">
            <span>Verified Company Facts Used:</span>
            <span className="text-[11px] text-slate-500 font-normal">Vault Path: {primaryDoc.vaultPath}</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {primaryDoc.facts.map((fact, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex items-start gap-2.5 text-xs"
              >
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <div className="text-slate-200 font-medium">{fact.statement}</div>
                  <div className="text-[10px] font-mono text-slate-500">
                    State: <strong className="text-emerald-400">{fact.state}</strong> | Source: {fact.source}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Authoritative Obsidian Rule Notice */}
        <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 flex items-start gap-2 text-xs text-slate-400">
          <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
          <p className="text-[11px] leading-relaxed">
            <strong className="text-slate-200">Architectural Rule:</strong> Obsidian is the authoritative company knowledge source. Claude/external reasoning cannot override stored facts without rigorous validation and verified memory writeback.
          </p>
        </div>
      </div>
    </Card>
  );
};
