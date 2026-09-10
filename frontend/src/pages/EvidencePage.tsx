import React, { useState } from 'react';
import {
  Archive,
  CheckCircle2,
  Database,
  FileCheck2,
  Filter,
  Layers,
  ScrollText,
  Search,
  ShieldCheck,
  TestTube,
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Card } from '../components/common/Card';
import { CodeBlock } from '../components/common/CodeBlock';
import { mockRuns } from '../mock';
import { EvidenceCategory, TypedEvidence } from '../types';

export const EvidencePage: React.FC = () => {
  const allEvidence = mockRuns.flatMap((r) => r.evidenceItems);
  const [selectedCategory, setSelectedCategory] = useState<EvidenceCategory | 'ALL'>('ALL');
  const [selectedItem, setSelectedItem] = useState<TypedEvidence>(allEvidence[0]);

  const categories: { key: EvidenceCategory; label: string; icon: any }[] = [
    { key: 'ARTIFACT', label: 'Artifact Evidence', icon: Archive },
    { key: 'EXECUTION_LOG', label: 'Execution Logs', icon: ScrollText },
    { key: 'TEST', label: 'Test Evidence', icon: TestTube },
    { key: 'VERIFICATION', label: 'Verification Evidence', icon: FileCheck2 },
  ];

  const filteredEvidence = selectedCategory === 'ALL'
    ? allEvidence
    : allEvidence.filter((e) => e.category === selectedCategory);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="space-y-1">
        <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <FileCheck2 className="w-5 h-5 text-emerald-400" />
          Empirical Evidence Vault
        </h1>
        <p className="text-xs md:text-sm text-slate-400">
          Cryptographically verifiable evidence artifacts, exit code assertions, and empirical proof logs collected by Observation / QA.
        </p>
      </div>

      {/* Evidence Integrity Banner */}
      <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-800/40 flex items-start gap-3 text-xs text-slate-300">
        <ShieldCheck className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-bold text-indigo-300 font-mono">
            EMPIRICAL EVIDENCE vs ASSUMPTIONS
          </span>
          <p className="text-slate-300 leading-relaxed font-sans">
            The LM-Brain verification engine strictly differentiates empirical evidence (SHA-256 hashes, process exit codes, compiled bundle ASTs) from reasoning model assumptions. Success is never declared without physical proof.
          </p>
        </div>
      </div>

      {/* Categories Bar */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setSelectedCategory('ALL')}
          className={`px-3.5 py-2 rounded-lg text-xs font-mono font-medium transition-all ${
            selectedCategory === 'ALL'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'bg-[#111827] text-slate-400 hover:text-slate-200 border border-slate-800'
          }`}
        >
          All Evidence Items ({allEvidence.length})
        </button>
        {categories.map((c) => {
          const Icon = c.icon;
          const count = allEvidence.filter((e) => e.category === c.key).length;
          const isSelected = selectedCategory === c.key;
          return (
            <button
              key={c.key}
              onClick={() => setSelectedCategory(c.key)}
              className={`px-3.5 py-2 rounded-lg text-xs font-mono font-medium transition-all flex items-center gap-2 ${
                isSelected
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-[#111827] text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{c.label}</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 font-bold">
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Evidence Master Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Evidence List */}
        <div className="space-y-2">
          {filteredEvidence.map((item, idx) => {
            const isSelected = selectedItem?.evidenceId === item.evidenceId;
            return (
              <button
                key={item.evidenceId || idx}
                onClick={() => setSelectedItem(item)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all text-xs font-mono space-y-1.5 ${
                  isSelected
                    ? 'bg-indigo-950/60 border-indigo-500/80 text-white shadow-md ring-1 ring-indigo-500/40'
                    : 'bg-[#111827] border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-900'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-200">{item.evidenceId}</span>
                  <Badge variant="primary" size="sm">{item.category}</Badge>
                </div>
                <div className="text-slate-300 font-sans text-xs truncate">
                  {item.description}
                </div>
                <div className="text-[10px] text-slate-500 flex items-center justify-between pt-1">
                  <span>{item.timestamp}</span>
                  <span className="text-emerald-400 font-semibold">✓ Verified</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Evidence Inspector Detail */}
        <div className="lg:col-span-2 space-y-4">
          {selectedItem && (
            <Card
              title={`Evidence Item: ${selectedItem.evidenceId}`}
              subtitle={`Category: ${selectedItem.category}`}
              icon={<FileCheck2 className="w-4 h-4 text-emerald-400" />}
              badge={<Badge variant="success" size="sm" dot>VERIFIED PROOF</Badge>}
            >
              <div className="space-y-4 font-mono text-xs">
                <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2">
                  <div className="text-slate-200 font-sans font-medium text-sm">
                    {selectedItem.description}
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 pt-2 border-t border-slate-800/80">
                    <div>
                      <span>Timestamp: </span>
                      <strong className="text-slate-300">{selectedItem.timestamp}</strong>
                    </div>
                    <div>
                      <span>Origin: </span>
                      <strong className="text-emerald-400">System Generated</strong>
                    </div>
                  </div>
                </div>

                {/* Specific Proof Metadata */}
                <div className="p-4 rounded-lg bg-[#080C14] border border-slate-800 space-y-3">
                  <span className="text-[10px] uppercase tracking-wider text-slate-500 font-bold block">
                    Cryptographic Integrity Proofs
                  </span>
                  <div className="space-y-2 text-[11px]">
                    <div>
                      <span className="text-slate-500">SHA-256 Checksum: </span>
                      <code className="text-indigo-300 block bg-slate-900 p-2 rounded border border-slate-800/80 mt-1 select-all">
                        e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
                      </code>
                    </div>
                    <div>
                      <span className="text-slate-500">Observation Service Sign-off: </span>
                      <strong className="text-emerald-400">obs_qa_service_v1.0 (PASSED)</strong>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
