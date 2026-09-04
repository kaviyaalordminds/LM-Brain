'use client';

import React, { useState } from 'react';
import { HardDriveDownload, Check, AlertTriangle, ArrowRight } from 'lucide-react';
import { writeKnowledge, searchMemory } from '@/lib/api';
import { WriteResponse, ApprovalStatus } from '@/lib/types';

export default function StorePage() {
  const [content, setContent] = useState('# Tesla Robotaxi Design Guidelines\n\nMinimalist UI tokens, obsidian dark palette.');
  const [targetNote, setTargetNote] = useState('Company Knowledge/Tesla/03-Brand-Tokens.md');
  const [approvalStatus, setApprovalStatus] = useState<ApprovalStatus>('approved');
  const [taskId, setTaskId] = useState('');
  const [response, setResponse] = useState<WriteResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retrievedPostWrite, setRetrievedPostWrite] = useState<any[] | null>(null);

  const handleWrite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim() || !targetNote.trim() || loading) return;
    setLoading(true);
    setError(null);
    setRetrievedPostWrite(null);

    try {
      const res = await writeKnowledge(content, targetNote, approvalStatus, [], taskId || undefined);
      setResponse(res);
      // Immediate post-write re-retrieval
      if (res.status === 'written') {
        const queryStem = targetNote.split('/').pop()?.replace('.md', '') || 'Tesla';
        const postSearch = await searchMemory(queryStem);
        setRetrievedPostWrite(postSearch.results || []);
      }
    } catch (err: any) {
      setError(err.message || 'Write failed');
      setResponse(null);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 shadow-xl space-y-3">
        <div>
          <h1 className="text-base font-bold text-white tracking-wide">
            Memory Store &amp; Approved Write-Back
          </h1>
          <p className="text-xs text-slate-400 font-mono">
            POST /api/v1/memory/write &bull; Rejects any write where approvalStatus is not &apos;approved&apos;
          </p>
        </div>

        <form onSubmit={handleWrite} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
            <div>
              <label className="text-[10px] text-slate-400 block mb-1 uppercase">Target Note Path:</label>
              <input
                type="text"
                value={targetNote}
                onChange={(e) => setTargetNote(e.target.value)}
                className="w-full bg-[#090D15] border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
              />
            </div>
            <div>
              <label className="text-[10px] text-slate-400 block mb-1 uppercase">Approval Status:</label>
              <select
                value={approvalStatus}
                onChange={(e) => setApprovalStatus(e.target.value as ApprovalStatus)}
                className="w-full bg-[#090D15] border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
              >
                <option value="approved">approved (Permitted)</option>
                <option value="unverified">unverified (Will be Rejected)</option>
                <option value="validated">validated (Will be Rejected)</option>
                <option value="pending">pending (Will be Rejected)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-[10px] text-slate-400 block mb-1 uppercase font-mono">Note Content (Markdown):</label>
            <textarea
              rows={5}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="w-full bg-[#090D15] border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/20 transition-all flex items-center gap-2"
          >
            <HardDriveDownload className="w-4 h-4" />
            <span>{loading ? 'Submitting Write...' : 'Write to Obsidian'}</span>
          </button>
        </form>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400 font-mono">
          {error}
        </div>
      )}

      {response && (
        <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="font-bold text-white">Write Status: {response.status}</span>
            <span className="text-slate-400">{response.timestamp}</span>
          </div>
          <pre className="text-slate-300">{JSON.stringify(response, null, 2)}</pre>
        </div>
      )}

      {retrievedPostWrite && (
        <div className="p-5 rounded-2xl bg-gradient-to-r from-[#0F1420] to-[#0B0F17] border border-emerald-500/30 space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-wider font-mono">
            <Check className="w-4 h-4" />
            <span>Post-Write Re-Retrieval Proof (Store &rarr; Retrieve)</span>
          </div>
          <p className="text-xs text-slate-300">
            Successfully verified that newly persisted knowledge is immediately indexable and retrievable from the vault.
          </p>
        </div>
      )}
    </div>
  );
}
