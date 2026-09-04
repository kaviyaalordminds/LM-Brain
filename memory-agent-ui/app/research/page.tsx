'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { 
  Globe, Search, Loader2, ExternalLink, ShieldCheck, CheckCircle2, 
  XCircle, ArrowRight, BookPlus, RefreshCw, FileText, Sparkles, Layers
} from 'lucide-react';
import { researchMemory, validateEvidence, writeKnowledge, searchMemory } from '@/lib/api';
import { ResearchResponse, EvidenceItem, ValidationResult, WriteResponse, SearchResponse } from '@/lib/types';
import { SearchResults } from '@/components/SearchResults';

function ResearchPageContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q') || 'E-commerce website design patterns and microservices architecture';

  const [query, setQuery] = useState(initialQuery);
  const [taskId, setTaskId] = useState('');
  
  // Step states
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [researchData, setResearchData] = useState<ResearchResponse | null>(null);
  const [validationData, setValidationData] = useState<ValidationResult | null>(null);
  const [writeData, setWriteData] = useState<WriteResponse | null>(null);
  const [verifyData, setVerifyData] = useState<SearchResponse | null>(null);

  // Target note state for write-back
  const [targetNote, setTargetNote] = useState('');
  const [customContent, setCustomContent] = useState('');

  // Loading states
  const [loadingResearch, setLoadingResearch] = useState(false);
  const [loadingValidation, setLoadingValidation] = useState(false);
  const [loadingWrite, setLoadingWrite] = useState(false);
  const [loadingVerify, setLoadingVerify] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (searchParams.get('q')) {
      const q = searchParams.get('q')!;
      setQuery(q);
      executeResearch(q);
    }
  }, [searchParams]);

  const executeResearch = async (searchQuery: string) => {
    if (!searchQuery.trim() || loadingResearch) return;
    setLoadingResearch(true);
    setError(null);
    setValidationData(null);
    setWriteData(null);
    setVerifyData(null);
    setStep(1);

    try {
      const res = await researchMemory(searchQuery, taskId || undefined);
      setResearchData(res);
      
      // Pre-fill target note and content for write-back
      const sanitizedName = searchQuery
        .replace(/[^a-zA-Z0-9\s-_]/g, '')
        .trim()
        .replace(/\s+/g, '_');
      setTargetNote(`Research/Web/${sanitizedName}.md`);

      const summaryContent = res.evidence
        .map(e => `### ${e.title || 'Research Finding'}\n${e.content}\n*Source: ${e.source}*`)
        .join('\n\n');
      setCustomContent(summaryContent);
    } catch (err: any) {
      setError(err.message || 'Research failed');
      setResearchData(null);
    }
    setLoadingResearch(false);
  };

  const handleResearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeResearch(query);
  };

  const handleValidate = async () => {
    if (!researchData || !researchData.evidence.length || loadingValidation) return;
    setLoadingValidation(true);
    setError(null);

    try {
      const res = await validateEvidence(researchData.evidence, query);
      setValidationData(res);
      setStep(2);
    } catch (err: any) {
      setError(err.message || 'Validation failed');
    }
    setLoadingValidation(false);
  };

  const handleWriteBack = async () => {
    if (!customContent.trim() || !targetNote.trim() || loadingWrite) return;
    setLoadingWrite(true);
    setError(null);

    try {
      const status = validationData?.approved ? 'validated' : 'unverified';
      const res = await writeKnowledge(
        customContent,
        targetNote,
        status,
        researchData?.evidence || [],
        taskId || undefined
      );
      setWriteData(res);
      setStep(3);
    } catch (err: any) {
      setError(err.message || 'Write to vault failed');
    }
    setLoadingWrite(false);
  };

  const handleVerify = async () => {
    if (!query.trim() || loadingVerify) return;
    setLoadingVerify(true);
    setError(null);

    try {
      const res = await searchMemory(query, taskId || undefined);
      setVerifyData(res);
      setStep(4);
    } catch (err: any) {
      setError(err.message || 'Verification search failed');
    }
    setLoadingVerify(false);
  };

  return (
    <div className="space-y-6">
      {/* Workflow Progress Bar */}
      <div className="p-4 rounded-2xl bg-[#0F1420] border border-slate-800">
        <div className="grid grid-cols-4 gap-2 text-center text-xs font-mono">
          <div className={`p-2 rounded-lg border transition-all ${
            researchData ? 'bg-sky-500/10 border-sky-500/30 text-sky-300' : 'bg-slate-900 border-slate-800 text-slate-500'
          }`}>
            <div className="text-[10px] text-slate-500">STEP 1</div>
            <div className="font-bold flex items-center justify-center gap-1 mt-0.5">
              <Globe className="w-3.5 h-3.5" />
              <span>Jina Discovery</span>
            </div>
          </div>

          <div className={`p-2 rounded-lg border transition-all ${
            validationData ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' : 'bg-slate-900 border-slate-800 text-slate-500'
          }`}>
            <div className="text-[10px] text-slate-500">STEP 2</div>
            <div className="font-bold flex items-center justify-center gap-1 mt-0.5">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Validation</span>
            </div>
          </div>

          <div className={`p-2 rounded-lg border transition-all ${
            writeData ? 'bg-purple-500/10 border-purple-500/30 text-purple-300' : 'bg-slate-900 border-slate-800 text-slate-500'
          }`}>
            <div className="text-[10px] text-slate-500">STEP 3</div>
            <div className="font-bold flex items-center justify-center gap-1 mt-0.5">
              <BookPlus className="w-3.5 h-3.5" />
              <span>Obsidian Write</span>
            </div>
          </div>

          <div className={`p-2 rounded-lg border transition-all ${
            verifyData ? 'bg-teal-500/10 border-teal-500/30 text-teal-300' : 'bg-slate-900 border-slate-800 text-slate-500'
          }`}>
            <div className="text-[10px] text-slate-500">STEP 4</div>
            <div className="font-bold flex items-center justify-center gap-1 mt-0.5">
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Re-Retrieval</span>
            </div>
          </div>
        </div>
      </div>

      {/* Step 1: Input & Trigger */}
      <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 shadow-xl space-y-3">
        <div>
          <h1 className="text-base font-bold text-white tracking-wide">
            Autonomous Web Research &amp; Knowledge Ingestion
          </h1>
          <p className="text-xs text-slate-400 font-mono">
            POST /api/v1/memory/research &bull; Controlled real web discovery via Jina Reader &amp; Search
          </p>
        </div>

        <form onSubmit={handleResearchSubmit} className="space-y-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Research query (e.g. E-commerce website design patterns, Instagram ad specifications)..."
            className="w-full bg-[#090D15] border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 font-mono"
          />
          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={loadingResearch}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white text-xs font-semibold shadow-md shadow-sky-500/20 transition-all flex items-center gap-2"
            >
              {loadingResearch ? <Loader2 className="w-4 h-4 animate-spin" /> : <Globe className="w-4 h-4" />}
              <span>{loadingResearch ? 'Researching Live Web...' : '1. Trigger Jina Research'}</span>
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400 font-mono">
          {error}
        </div>
      )}

      {/* Step 1 Results: Discovered Evidence */}
      {researchData && (
        <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-sky-400" />
              <span className="text-xs font-bold text-white font-mono">
                Discovered Evidence ({researchData.evidence.length} items from {researchData.sources.length} sources)
              </span>
            </div>

            {/* Validate Action Button */}
            <button
              onClick={handleValidate}
              disabled={loadingValidation}
              className="px-4 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold font-mono flex items-center gap-1.5 transition-all shadow-md"
            >
              {loadingValidation ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ShieldCheck className="w-3.5 h-3.5" />}
              <span>2. Validate Evidence</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-3">
            {researchData.evidence.map((ev, idx) => (
              <div key={ev.id || idx} className="p-3.5 rounded-xl bg-[#090D15] border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white font-mono">{ev.title || `Finding #${idx + 1}`}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold uppercase">
                    {ev.approvalStatus}
                  </span>
                </div>
                <p className="text-xs text-slate-300 font-sans leading-relaxed">{ev.content}</p>
                <div className="text-[10px] font-mono text-slate-500 truncate">Source: {ev.source}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Step 2: Validation Result */}
      {validationData && (
        <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-bold text-white font-mono">
                Validation &amp; Trust Assessment Result
              </span>
            </div>
            <span className={`px-2.5 py-0.5 rounded font-mono text-xs font-bold uppercase ${
              validationData.approved
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
            }`}>
              {validationData.status} ({validationData.approved ? 'APPROVED' : 'REJECTED'})
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-[#090D15] border border-slate-800 text-xs font-mono text-slate-300 space-y-2">
            <div className="text-slate-400">Reason: {validationData.reason}</div>
            <div className="text-[11px] text-slate-500">
              Assessment: {JSON.stringify(validationData.assessment)}
            </div>
          </div>

          {/* Write back form */}
          <div className="p-4 rounded-xl bg-[#0B0F19] border border-slate-800 space-y-3">
            <div className="text-xs font-bold text-purple-300 font-mono flex items-center gap-2">
              <BookPlus className="w-4 h-4" />
              <span>Configure Obsidian Vault Write-Back</span>
            </div>
            <div>
              <label className="text-[10px] font-mono text-slate-400 block mb-1">Target Vault Path:</label>
              <input
                type="text"
                value={targetNote}
                onChange={(e) => setTargetNote(e.target.value)}
                className="w-full bg-[#090D15] border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-purple-500"
              />
            </div>
            <div>
              <label className="text-[10px] font-mono text-slate-400 block mb-1">Content to Ingest:</label>
              <textarea
                rows={5}
                value={customContent}
                onChange={(e) => setCustomContent(e.target.value)}
                className="w-full bg-[#090D15] border border-slate-800 rounded-lg p-3 text-xs font-mono text-slate-300 focus:outline-none focus:border-purple-500"
              />
            </div>
            <button
              onClick={handleWriteBack}
              disabled={loadingWrite}
              className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold font-mono flex items-center gap-2 transition-all shadow-md shadow-purple-600/20"
            >
              {loadingWrite ? <Loader2 className="w-4 h-4 animate-spin" /> : <BookPlus className="w-4 h-4" />}
              <span>3. Write to Obsidian Vault</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Write Confirmation */}
      {writeData && (
        <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 text-purple-400">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-bold text-white font-mono">
                Knowledge Successfully Ingested into Obsidian Vault
              </span>
            </div>
            <span className="text-[10px] font-mono text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
              STATUS: {writeData.status.toUpperCase()}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-[#090D15] border border-slate-800 text-xs font-mono text-slate-300 space-y-1.5">
            <div>Note ID / Path: <strong className="text-purple-300">{writeData.noteId || targetNote}</strong></div>
            <div className="text-[11px] text-slate-500">Timestamp: {writeData.timestamp}</div>
          </div>

          <button
            onClick={handleVerify}
            disabled={loadingVerify}
            className="px-5 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-bold font-mono flex items-center gap-2 transition-all shadow-md"
          >
            {loadingVerify ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            <span>4. Re-Query Memory Agent to Verify Knowledge Ingestion</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Step 4: Verification Re-Retrieval Results */}
      {verifyData && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 text-xs font-mono text-emerald-300 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>
              <strong>Full Lifecycle Verified:</strong> The Memory Agent now recognizes the newly written note in internal search!
            </span>
          </div>
          <SearchResults
            results={verifyData.results || []}
            found={verifyData.found}
            query={query}
            taskScope={verifyData.taskScope}
            knowledgeGaps={verifyData.knowledgeGaps}
          />
        </div>
      )}
    </div>
  );
}

export default function ResearchPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs font-mono text-slate-500">Loading Research...</div>}>
      <ResearchPageContent />
    </Suspense>
  );
}
