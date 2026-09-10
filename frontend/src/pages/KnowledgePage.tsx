import React, { useState } from 'react';
import {
  CheckCircle2,
  Clock,
  Database,
  FileCode,
  FileText,
  Info,
  Layers,
  Search,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Card } from '../components/common/Card';
import { CodeBlock } from '../components/common/CodeBlock';
import { mockObsidianKnowledge } from '../mock';
import { ObsidianDocument } from '../types';

export const KnowledgePage: React.FC = () => {
  const [selectedDoc, setSelectedDoc] = useState<ObsidianDocument>(mockObsidianKnowledge[0]);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredDocs = mockObsidianKnowledge.filter(
    (d) =>
      d.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.vaultPath.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="space-y-1">
        <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Database className="w-5 h-5 text-emerald-400" />
          Company Knowledge & Obsidian Memory Layer
        </h1>
        <p className="text-xs md:text-sm text-slate-400">
          The single authoritative source of corporate truth. Connected exclusively through backend CompanyKnowledgeService abstraction.
        </p>
      </div>

      {/* Authoritative Obsidian Banner */}
      <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/40 flex items-start gap-3 text-xs text-slate-300">
        <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-bold text-emerald-300 font-mono">
            AUTHORITATIVE MEMORY PRINCIPLE
          </span>
          <p className="text-slate-300 leading-relaxed font-sans">
            Company Obsidian is the single authoritative company knowledge source. External reasoning model generation cannot overwrite company facts without rigorous validation and verified memory writeback.
          </p>
        </div>
      </div>

      {/* Main Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Document List Panel */}
        <div className="space-y-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search vault documents..."
              className="w-full bg-[#080C14] border border-slate-700/80 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-sans"
            />
          </div>

          <div className="space-y-2">
            {filteredDocs.map((doc) => {
              const isSelected = selectedDoc.documentId === doc.documentId;
              return (
                <button
                  key={doc.documentId}
                  onClick={() => setSelectedDoc(doc)}
                  className={`w-full text-left p-3.5 rounded-xl border transition-all text-xs space-y-1.5 ${
                    isSelected
                      ? 'bg-emerald-950/40 border-emerald-500/80 text-white shadow-md ring-1 ring-emerald-500/40'
                      : 'bg-[#111827] border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-900'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200">{doc.title}</span>
                    <Badge variant="authoritative" size="sm">VAULT</Badge>
                  </div>
                  <div className="text-[11px] font-mono text-emerald-400 truncate">
                    {doc.vaultPath}
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono pt-1 flex items-center justify-between">
                    <span>{doc.facts.length} Verified Facts</span>
                    <span>100% Confidence</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Document Detail & Verified Facts Panel */}
        <div className="lg:col-span-2 space-y-4">
          <Card
            title={selectedDoc.title}
            subtitle={`Authoritative Vault Document: ${selectedDoc.vaultPath}`}
            icon={<FileText className="w-4 h-4 text-emerald-400" />}
            badge={<Badge variant="authoritative" size="sm">CONFIDENCE: 100%</Badge>}
          >
            <div className="space-y-4">
              {/* Discrete Fact Items */}
              <div className="space-y-2">
                <span className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider block">
                  Discrete Fact Items Extracted for Workforce:
                </span>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {selectedDoc.facts.map((fact, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1 text-xs"
                    >
                      <div className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                        <span className="text-slate-200 font-medium">{fact.statement}</span>
                      </div>
                      <div className="text-[10px] font-mono text-slate-400 pt-1 flex items-center justify-between">
                        <span>Truth State: <strong className="text-emerald-400">{fact.state}</strong></span>
                        <span className="text-slate-400">{fact.source}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Raw Document Markdown View */}
              <div className="space-y-1.5 pt-2">
                <span className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider block">
                  Authoritative Document Content (Obsidian Markdown):
                </span>
                <CodeBlock
                  code={selectedDoc.content}
                  language="markdown"
                  title={selectedDoc.vaultPath}
                  maxHeight="max-h-80"
                />
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
