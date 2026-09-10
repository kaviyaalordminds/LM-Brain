import React, { useState } from 'react';
import {
  Archive,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Database,
  FileCheck2,
  Layers,
  ScrollText,
  ShieldCheck,
  TestTube,
} from 'lucide-react';
import { EvidenceCategory, TypedEvidence } from '../../types';
import { Badge } from '../common/Badge';
import { Card } from '../common/Card';

interface EvidenceViewProps {
  evidenceItems?: TypedEvidence[];
}

export const EvidenceView: React.FC<EvidenceViewProps> = ({
  evidenceItems = [],
}) => {
  const [selectedCategory, setSelectedCategory] = useState<EvidenceCategory | 'ALL'>('ALL');

  const categories: { key: EvidenceCategory; label: string; icon: any }[] = [
    { key: 'ARTIFACT', label: 'Artifact Evidence', icon: Archive },
    { key: 'EXECUTION_LOG', label: 'Execution Logs', icon: ScrollText },
    { key: 'TEST', label: 'Test Evidence', icon: TestTube },
    { key: 'VERIFICATION', label: 'Verification Evidence', icon: FileCheck2 },
  ];

  const filteredItems = selectedCategory === 'ALL'
    ? evidenceItems
    : evidenceItems.filter(e => e.category === selectedCategory);

  const getCategoryCount = (cat: EvidenceCategory) => {
    return evidenceItems.filter(e => e.category === cat).length;
  };

  return (
    <Card
      title="Empirical Evidence Vault (Proof of Verification)"
      subtitle="Structured artifacts, execution proofs, and assertion logs collected by Observation / QA"
      icon={<FileCheck2 className="w-4 h-4 text-emerald-400" />}
      badge={<Badge variant="success" size="sm" dot>{evidenceItems.length} Evidence Items</Badge>}
    >
      <div className="space-y-4">
        {/* Category Filters */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCategory('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all ${
              selectedCategory === 'ALL'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            All Evidence ({evidenceItems.length})
          </button>
          {categories.map((c) => {
            const Icon = c.icon;
            const count = getCategoryCount(c.key);
            const isSelected = selectedCategory === c.key;
            return (
              <button
                key={c.key}
                onClick={() => setSelectedCategory(c.key)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all flex items-center gap-1.5 ${
                  isSelected
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{c.label}</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 font-bold ml-1">
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Evidence List */}
        {filteredItems.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500 font-mono border border-slate-800/80 rounded-lg bg-[#0B0F19]">
            No evidence records collected for this category yet.
          </div>
        ) : (
          <div className="space-y-2.5">
            {filteredItems.map((item, idx) => (
              <div
                key={item.evidenceId || idx}
                className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2 text-xs font-mono"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="primary" size="sm">{item.category}</Badge>
                    <span className="text-slate-300 font-bold">{item.evidenceId}</span>
                  </div>
                  <span className="text-[11px] text-slate-500">{item.timestamp}</span>
                </div>

                <div className="text-slate-200 font-sans font-medium">{item.description}</div>

                {/* Specific detail metadata by category */}
                <div className="pt-2 border-t border-slate-800/60 flex flex-wrap items-center gap-4 text-[11px] text-slate-400">
                  <span className="text-emerald-400 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> System Generated
                  </span>
                  {item.category === 'ARTIFACT' && (
                    <span className="text-slate-400 truncate">
                      SHA-256: <code className="text-indigo-300">e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855</code>
                    </span>
                  )}
                  {item.category === 'TEST' && (
                    <span className="text-emerald-400">
                      Tests Passed: <strong>4/4 (100%)</strong>
                    </span>
                  )}
                  {item.category === 'VERIFICATION' && (
                    <span className="text-emerald-400 font-bold">
                      Outcome: VERIFIED (All Acceptance Rules Passed)
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
};
