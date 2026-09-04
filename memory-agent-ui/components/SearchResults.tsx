'use client';

import React from 'react';
import { 
  FileText, ShieldCheck, ExternalLink, Sparkles, AlertCircle, 
  CheckCircle2, HelpCircle, Layers, Tag, Globe, ArrowRight, BookOpen,
  Zap, Loader2
} from 'lucide-react';
import { MemoryResult, TaskScope, KnowledgeGapItem, RejectedCandidate, VaultScanStats } from '@/lib/types';
import Link from 'next/link';
import { ChevronDown, ChevronUp, Database, XCircle } from 'lucide-react';

interface SearchResultsProps {
  results: MemoryResult[];
  found: boolean;
  query: string;
  taskScope?: TaskScope | null;
  knowledgeGaps?: KnowledgeGapItem[];
  rejectedCandidates?: RejectedCandidate[];
  vaultScanStats?: VaultScanStats | null;
  onAutoResolveGap?: (query: string) => void;
  isAutoResolving?: boolean;
}

export const SearchResults: React.FC<SearchResultsProps> = ({ 
  results, 
  found, 
  query,
  taskScope,
  knowledgeGaps,
  rejectedCandidates,
  vaultScanStats,
  onAutoResolveGap,
  isAutoResolving
}) => {
  const [showRejected, setShowRejected] = React.useState(false);
  const missingGaps = (knowledgeGaps || []).filter(g => g.status === 'missing');
  const partialGaps = (knowledgeGaps || []).filter(g => g.status === 'partial');
  const satisfiedGaps = (knowledgeGaps || []).filter(g => g.status === 'satisfied');

  return (
    <div className="space-y-5">
      {/* 1. Header & Status */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl bg-[#0F1420] border border-slate-800">
        <div className="text-xs font-mono text-slate-400">
          Query: <span className="text-purple-300 font-semibold">&ldquo;{query}&rdquo;</span>
        </div>
        <div className="flex items-center gap-2 font-mono text-xs">
          <span
            className={`px-3 py-1 rounded-full font-bold text-[11px] flex items-center gap-1.5 ${
              found
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
            }`}
          >
            {found ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>KNOWLEDGE AVAILABLE ({results.length} NOTES)</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-3.5 h-3.5" />
                <span>KNOWLEDGE GAP DETECTED</span>
              </>
            )}
          </span>
          <span className="text-slate-500 px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
            {results.length} results
          </span>
        </div>
      </div>

      {/* 2. Task Understanding Card */}
      {taskScope && (
        <div className="p-4 rounded-xl bg-[#0B0F19] border border-slate-800/80 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold text-sky-400 font-mono">
              <Layers className="w-4 h-4" />
              <span>TASK UNDERSTANDING &amp; INTENT SCOPE</span>
            </div>
            <span className="text-[10px] font-mono text-slate-500 uppercase">
              Type: <strong className="text-slate-300">{taskScope.taskType}</strong>
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
            <div className="p-2.5 rounded-lg bg-[#0F1420] border border-slate-800">
              <span className="text-[10px] text-slate-500 block">Domain:</span>
              <span className="text-slate-200 font-semibold truncate block">
                {taskScope.domain || <span className="text-slate-500 font-normal">Generic / Multi</span>}
              </span>
            </div>
            <div className="p-2.5 rounded-lg bg-[#0F1420] border border-slate-800">
              <span className="text-[10px] text-slate-500 block">Entity:</span>
              <span className="text-slate-200 font-semibold truncate block">
                {taskScope.entity || <span className="text-slate-500 font-normal">None (Unbound)</span>}
              </span>
            </div>
            <div className="p-2.5 rounded-lg bg-[#0F1420] border border-slate-800">
              <span className="text-[10px] text-slate-500 block">Platform:</span>
              <span className="text-slate-200 font-semibold truncate block">
                {taskScope.platform || <span className="text-slate-500 font-normal">General</span>}
              </span>
            </div>
            <div className="p-2.5 rounded-lg bg-[#0F1420] border border-slate-800">
              <span className="text-[10px] text-slate-500 block">Requirements:</span>
              <span className="text-purple-300 font-semibold">
                {taskScope.requirements?.length || 0} sub-clauses
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 3. Knowledge Gaps Assessment Panel */}
      {knowledgeGaps && knowledgeGaps.length > 0 && (
        <div className="p-4 rounded-xl bg-[#0F1420] border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold text-amber-400 font-mono">
              <AlertCircle className="w-4 h-4" />
              <span>REQUIREMENT GAP ASSESSMENT</span>
            </div>
            <div className="flex items-center gap-2 text-[10px] font-mono">
              <span className="text-emerald-400">{satisfiedGaps.length} satisfied</span>
              <span className="text-slate-600">&bull;</span>
              <span className="text-amber-400">{partialGaps.length} partial</span>
              <span className="text-slate-600">&bull;</span>
              <span className="text-rose-400">{missingGaps.length} missing</span>
            </div>
          </div>

          <div className="space-y-2">
            {knowledgeGaps.map((gap, i) => (
              <div
                key={i}
                className={`p-3 rounded-lg border text-xs font-mono flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${
                  gap.status === 'satisfied'
                    ? 'bg-emerald-950/10 border-emerald-500/20 text-emerald-300'
                    : gap.status === 'partial'
                    ? 'bg-amber-950/10 border-amber-500/20 text-amber-300'
                    : 'bg-rose-950/10 border-rose-500/20 text-rose-300'
                }`}
              >
                <div className="space-y-0.5">
                  <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                    <span className="text-xs">{gap.requirement}</span>
                  </div>
                  {gap.reason && (
                    <div className="text-[10px] text-slate-400 font-sans">{gap.reason}</div>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0 text-[10px]">
                  {gap.matchedNote && (
                    <span className="text-slate-400 max-w-[180px] truncate" title={gap.matchedNote}>
                      {gap.matchedNote.split('/').pop()}
                    </span>
                  )}
                  <span
                    className={`px-2 py-0.5 rounded font-bold uppercase text-[9px] ${
                      gap.status === 'satisfied'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : gap.status === 'partial'
                        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    }`}
                  >
                    {gap.status} ({Math.round(gap.relevance * 100)}%)
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Direct 1-Click Auto-Resolve CTA */}
          {missingGaps.length > 0 && onAutoResolveGap && (
            <div className="p-3.5 rounded-lg bg-gradient-to-r from-amber-500/10 via-purple-500/10 to-sky-500/10 border border-amber-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="text-xs text-amber-200 space-y-0.5">
                <div className="font-bold flex items-center gap-1.5 text-white">
                  <Zap className="w-3.5 h-3.5 text-amber-400" />
                  <span>Autonomous Gap Ingestion</span>
                </div>
                <div className="text-[11px] text-slate-300">
                  Automatically research via Jina, validate evidence, and save approved knowledge to Obsidian in 1-click.
                </div>
              </div>
              <button
                onClick={() => onAutoResolveGap(query)}
                disabled={isAutoResolving}
                className="shrink-0 px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-purple-600 hover:from-amber-400 hover:to-purple-500 text-slate-950 font-bold text-xs font-mono flex items-center gap-2 transition-all shadow-md shadow-amber-500/20 disabled:opacity-50"
              >
                {isAutoResolving ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Auto-Resolving &amp; Writing to Obsidian...</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-3.5 h-3.5" />
                    <span>Auto-Resolve Gaps &amp; Save to Obsidian</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* 4. Results List */}
      {results.length === 0 ? (
        <div className="p-8 rounded-2xl bg-[#0F1420] border border-dashed border-slate-800 text-center space-y-3">
          <BookOpen className="w-8 h-8 text-slate-600 mx-auto" />
          <div className="text-xs font-mono text-slate-400 font-semibold">
            No notes found in internal Obsidian vault for this domain.
          </div>
          <p className="text-[11px] text-slate-500 max-w-md mx-auto">
            The Memory Agent correctly avoided returning unrelated company notes. Trigger auto-resolve to automatically perform Jina research, validation, and write to Obsidian.
          </p>
          {onAutoResolveGap && (
            <div className="pt-2">
              <button
                onClick={() => onAutoResolveGap(query)}
                disabled={isAutoResolving}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white text-xs font-semibold shadow-md shadow-sky-500/20 transition-all font-sans"
              >
                {isAutoResolving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
                <span>{isAutoResolving ? 'Auto-Ingesting Knowledge...' : 'Auto-Resolve & Ingest to Obsidian Now'}</span>
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          <div className="text-xs font-mono text-slate-400 flex items-center justify-between">
            <span>Retrieved Vault Knowledge ({results.length} entries):</span>
            <span className="text-emerald-400 font-semibold">&bull; 100% Content Grounded</span>
          </div>
          {results.map((r, idx) => (
            <div
              key={r.id || idx}
              className="p-4 rounded-xl bg-[#0F1420] border border-slate-800 hover:border-purple-500/30 transition-all space-y-2.5"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <FileText className="w-4 h-4 text-purple-400 shrink-0" />
                  <span className="text-xs font-bold text-white font-mono truncate">
                    {r.sourceNote ? r.sourceNote.split('/').pop() : r.query}
                  </span>
                </div>
                <div className="flex items-center gap-2 shrink-0 font-mono text-[10px]">
                  <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
                    {r.approvalStatus}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                    {(r.relevance * 100).toFixed(0)}% Match
                  </span>
                </div>
              </div>

              {r.matchedSection && (
                <div className="p-2 rounded bg-purple-950/20 border border-purple-800/30 text-[11px] font-mono text-purple-300">
                  <strong>Matched Section:</strong> {r.matchedSection}
                </div>
              )}

              {r.evidenceExcerpt && (
                <div className="p-2 rounded bg-slate-900/60 border border-slate-800 text-[11px] font-mono text-slate-300 italic">
                  &ldquo;{r.evidenceExcerpt}&rdquo;
                </div>
              )}

              <p className="text-xs text-slate-300 leading-relaxed font-sans whitespace-pre-line line-clamp-6 hover:line-clamp-none transition-all">
                {r.content}
              </p>

              <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono text-slate-500 pt-2 border-t border-slate-800/60">
                <span className="truncate max-w-sm">Source Note: {r.sourceNote || 'Internal Vault'}</span>
                {r.relevanceReason && <span className="text-emerald-400">{r.relevanceReason}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 5. Evaluated & Rejected Candidates Audit */}
      {rejectedCandidates && rejectedCandidates.length > 0 && (
        <div className="p-4 rounded-xl bg-[#0A0D14] border border-slate-800/80 space-y-3">
          <button
            onClick={() => setShowRejected(!showRejected)}
            className="w-full flex items-center justify-between text-xs font-mono text-slate-400 hover:text-slate-200 transition-colors"
          >
            <div className="flex items-center gap-2">
              <XCircle className="w-4 h-4 text-rose-400" />
              <span>CANDIDATES EVALUATED &amp; REJECTED ({rejectedCandidates.length})</span>
            </div>
            {showRejected ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showRejected && (
            <div className="space-y-2 pt-2 border-t border-slate-800/60">
              {rejectedCandidates.map((rej, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-[#0F1420] border border-slate-800/60 text-xs font-mono space-y-1">
                  <div className="flex items-center justify-between text-slate-300">
                    <span className="font-semibold truncate max-w-md">{rej.sourceNote}</span>
                    <span className="text-[10px] text-rose-400 font-bold">REJECTED</span>
                  </div>
                  <p className="text-[11px] text-slate-400 font-sans">{rej.rejectionReason}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
