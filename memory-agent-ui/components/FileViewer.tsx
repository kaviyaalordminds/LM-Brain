'use client';

import React, { useState } from 'react';
import { FileText, Copy, Check, Clock, HardDrive, ShieldCheck, Tag, Hash } from 'lucide-react';
import { VaultFileDetail } from '@/lib/types';

interface FileViewerProps {
  file: VaultFileDetail | null;
  loading: boolean;
}

export const FileViewer: React.FC<FileViewerProps> = ({ file, loading }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!file) return;
    navigator.clipboard.writeText(file.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="h-full rounded-2xl bg-[#0F1420] border border-slate-800 p-8 flex items-center justify-center text-xs text-slate-500 font-mono">
        Reading markdown document...
      </div>
    );
  }

  if (!file) {
    return (
      <div className="h-full rounded-2xl bg-[#0F1420] border border-dashed border-slate-800 p-8 flex flex-col items-center justify-center text-slate-500 text-xs font-mono space-y-2">
        <FileText className="w-8 h-8 text-slate-600 mb-1" />
        <span>Select an Obsidian markdown document from the vault explorer to view.</span>
      </div>
    );
  }

  return (
    <div className="h-full rounded-2xl bg-[#0F1420] border border-slate-800 flex flex-col shadow-xl overflow-hidden">
      {/* Header & Metadata Bar */}
      <div className="p-4 border-b border-slate-800 bg-[#0B0F17]/90 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-bold text-white font-mono">{file.name}</h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
              ✓ RETRIEVED
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-[10px] text-slate-400 font-mono">
            <span>Path: {file.path}</span>
            <span>&bull;</span>
            <span className="flex items-center gap-1">
              <HardDrive className="w-3 h-3 text-slate-500" />
              {(file.sizeBytes / 1024).toFixed(1)} KB
            </span>
            <span>&bull;</span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-slate-500" />
              {file.lastModified ? file.lastModified.split('T')[0] : 'N/A'}
            </span>
          </div>
        </div>

        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 hover:text-white text-xs font-mono transition-all shrink-0"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          <span>{copied ? 'Copied' : 'Copy Content'}</span>
        </button>
      </div>

      {/* Frontmatter Drawer (If Present) */}
      {file.frontmatter && Object.keys(file.frontmatter).length > 0 && (
        <div className="px-4 py-2 bg-slate-950/70 border-b border-slate-800 text-xs font-mono">
          <div className="text-[10px] uppercase text-slate-500 font-bold mb-1">YAML Frontmatter:</div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {Object.entries(file.frontmatter).map(([k, v]) => (
              <div key={k} className="p-1.5 rounded bg-slate-900 border border-slate-800">
                <span className="text-slate-500 block text-[9px]">{k}:</span>
                <span className="text-slate-200 truncate block text-[10px] font-semibold">{String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Document Content */}
      <div className="flex-1 p-5 overflow-y-auto">
        <pre className="font-mono text-xs text-slate-200 whitespace-pre-wrap leading-relaxed">
          {file.content}
        </pre>
      </div>
    </div>
  );
};
