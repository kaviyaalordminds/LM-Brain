'use client';

import React from 'react';
import { Share2, ExternalLink } from 'lucide-react';

export default function SourcesPage() {
  return (
    <div className="space-y-6">
      <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 shadow-xl space-y-1">
        <h1 className="text-base font-bold text-white tracking-wide">
          Research Sources &amp; Evidence Provenance
        </h1>
        <p className="text-xs text-slate-400 font-mono">
          Evidence source tracking and citation index
        </p>
      </div>

      <div className="p-8 rounded-2xl bg-[#0F1420] border border-dashed border-slate-800 text-center text-xs font-mono text-slate-500">
        Execute a research query in the Research module to inspect active source citations.
      </div>
    </div>
  );
}
