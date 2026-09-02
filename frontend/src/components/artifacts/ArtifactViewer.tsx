'use client';

import React, { useState } from 'react';
import { LineageArtifact } from '../../lib/types';
import { TrustBadge } from '../memory/TrustBadge';
import { CodeBlock } from '../ui/CodeBlock';
import { EmptyState } from '../ui/EmptyState';
import { formatTimestamp } from '../../lib/utils/formatters';
import { Box, FileText, CheckCircle2, ShieldCheck, Copy, Check, ExternalLink } from 'lucide-react';

interface ArtifactViewerProps {
  artifacts: LineageArtifact[];
  className?: string;
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({
  artifacts,
  className = '',
}) => {
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | null>(
    artifacts.length > 0 ? artifacts[0].artifact_id : null
  );

  const selectedArtifact = artifacts.find((a) => a.artifact_id === selectedArtifactId) || artifacts[0];

  if (artifacts.length === 0) {
    return (
      <EmptyState
        title="No Artifacts Produced"
        description="Lineage artifacts created during specialist execution (source code, schemas, reports, logs) will appear here."
        icon={<Box className="w-5 h-5 text-slate-400" />}
        className={className}
      />
    );
  }

  return (
    <div className={`grid grid-cols-1 md:grid-cols-3 gap-4 ${className}`}>
      {/* List of artifacts */}
      <div className="bg-space-900 border border-space-800 rounded-lg p-3 space-y-2 overflow-y-auto max-h-[500px]">
        <div className="text-[11px] font-mono-tech text-slate-400 uppercase tracking-wider pb-2 border-b border-space-800">
          Lineage Artifacts ({artifacts.length})
        </div>
        {artifacts.map((art) => {
          const isSelected = selectedArtifact?.artifact_id === art.artifact_id;
          return (
            <div
              key={art.artifact_id}
              onClick={() => setSelectedArtifactId(art.artifact_id)}
              className={`p-2.5 rounded border transition-all cursor-pointer text-left font-mono-tech ${
                isSelected
                  ? 'bg-space-800 border-sky-500 shadow-sm'
                  : 'bg-space-950 hover:bg-space-850 border-space-800'
              }`}
            >
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className="text-xs font-bold text-slate-200 truncate">
                  {art.artifact_type}
                </span>
                <TrustBadge state={art.trust_state} size="sm" />
              </div>
              <div className="text-[10px] text-slate-400 truncate">{art.path || art.url}</div>
              <div className="flex items-center justify-between text-[9px] text-slate-500 mt-1">
                <span>{art.specialist_id}</span>
                <span>{formatTimestamp(art.created_at)}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Artifact Inspector */}
      <div className="md:col-span-2 bg-space-900 border border-space-800 rounded-lg p-4 flex flex-col space-y-3">
        {selectedArtifact ? (
          <>
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-space-800">
              <div>
                <h3 className="text-xs font-bold font-mono-tech text-slate-100 uppercase">
                  {selectedArtifact.artifact_type}
                </h3>
                <div className="text-[11px] font-mono-tech text-slate-400">
                  ID: {selectedArtifact.artifact_id}
                </div>
              </div>
              <TrustBadge state={selectedArtifact.trust_state} size="md" />
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono-tech">
              <div className="p-2 bg-space-950 border border-space-800 rounded">
                <span className="text-slate-500 block text-[10px]">Specialist</span>
                <span className="text-slate-200">{selectedArtifact.specialist_id}</span>
              </div>
              <div className="p-2 bg-space-950 border border-space-800 rounded">
                <span className="text-slate-500 block text-[10px]">Execution</span>
                <span className="text-slate-200">{selectedArtifact.execution_id.slice(0, 8)}...</span>
              </div>
              <div className="p-2 bg-space-950 border border-space-800 rounded">
                <span className="text-slate-500 block text-[10px]">Verification</span>
                <span className="text-emerald-400">{selectedArtifact.verification_status}</span>
              </div>
              <div className="p-2 bg-space-950 border border-space-800 rounded">
                <span className="text-slate-500 block text-[10px]">Checksum</span>
                <span className="text-slate-300">{selectedArtifact.checksum || 'N/A'}</span>
              </div>
            </div>

            {/* Content view */}
            <div className="flex-1">
              <CodeBlock
                code={selectedArtifact.content || '(No content payload)'}
                language={selectedArtifact.artifact_type.toLowerCase()}
                title={selectedArtifact.path || selectedArtifact.url}
                maxHeight="max-h-80"
              />
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
};
