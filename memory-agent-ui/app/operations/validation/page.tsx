'use client';

import React, { useState } from 'react';
import { ShieldCheck, CheckCircle2, XCircle } from 'lucide-react';
import { validateEvidence } from '@/lib/api';
import { ValidationResult, EvidenceItem } from '@/lib/types';

export default function ValidationPage() {
  const [query, setQuery] = useState('Tesla Autonomous Robotaxi Platform');
  const [source, setSource] = useState('https://ir.tesla.com/press-release');
  const [content, setContent] = useState('Cybercab inductive wireless charging specifications.');
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleValidate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;
    setLoading(true);

    const evItem: EvidenceItem = {
      id: 'ev-test-1',
      source,
      title: 'Official Press Release',
      content,
      retrievedAt: new Date().toISOString(),
      relevance: 0.95,
      validationStatus: 'pending',
      approvalStatus: 'unverified',
    };

    try {
      const res = await validateEvidence([evItem], query);
      setResult(res);
    } catch (err) {
      setResult(null);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 shadow-xl space-y-3">
        <div>
          <h1 className="text-base font-bold text-white tracking-wide">
            Deterministic Evidence Validation
          </h1>
          <p className="text-xs text-slate-400 font-mono">
            POST /api/v1/memory/validate &bull; Rule-based gate (never trusts model claims alone)
          </p>
        </div>

        <form onSubmit={handleValidate} className="space-y-3 font-mono text-xs">
          <div>
            <label className="text-[10px] text-slate-400 block mb-1">Query:</label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full bg-[#090D15] border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
            />
          </div>
          <div>
            <label className="text-[10px] text-slate-400 block mb-1">Source URL/Reference:</label>
            <input
              type="text"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="w-full bg-[#090D15] border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
            />
          </div>
          <div>
            <label className="text-[10px] text-slate-400 block mb-1">Evidence Content:</label>
            <textarea
              rows={3}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="w-full bg-[#090D15] border border-slate-800 rounded-xl p-3 text-white focus:outline-none focus:border-sky-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/20 transition-all font-sans"
          >
            {loading ? 'Evaluating Rules...' : 'Validate Evidence'}
          </button>
        </form>
      </div>

      {result && (
        <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="font-bold text-white">Approval Decision: {result.status}</span>
            <span className={result.approved ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
              {result.approved ? 'APPROVED' : 'REJECTED'}
            </span>
          </div>
          <p className="text-slate-300 font-sans">{result.reason}</p>
          <pre className="text-slate-400 text-[11px]">{JSON.stringify(result.assessment, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
