'use client';

import React, { useState, useEffect } from 'react';
import { orchestratorApi } from '@/lib/api/orchestrator';
import { ArtifactViewer } from '@/components/artifacts/ArtifactViewer';
import { LineageArtifact } from '@/lib/types';
import { Box, RefreshCw } from 'lucide-react';

export default function ArtifactExplorerPage() {
  const [artifacts, setArtifacts] = useState<LineageArtifact[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadArtifacts = async () => {
    setIsLoading(true);
    try {
      const executions = await orchestratorApi.listExecutions();
      const allArtifacts: LineageArtifact[] = [];
      for (const ex of executions.slice(0, 10)) {
        try {
          const arts = await orchestratorApi.getExecutionArtifacts(ex.execution_id);
          allArtifacts.push(...arts);
        } catch {
          // ignore
        }
      }
      setArtifacts(allArtifacts);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadArtifacts();
  }, []);

  return (
    <div className="space-y-6 font-mono-tech">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-space-900 border border-space-800 rounded-lg shadow-md">
        <div className="flex items-center gap-3">
          <Box className="w-5 h-5 text-emerald-400" />
          <div>
            <h1 className="text-xs font-bold text-slate-100 uppercase tracking-wider">
              Execution Artifact Lineage Explorer
            </h1>
            <div className="text-[11px] text-slate-400">
              Verified source code, schemas, documentation, and configuration outputs
            </div>
          </div>
        </div>

        <button
          onClick={loadArtifacts}
          disabled={isLoading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-space-850 hover:bg-space-800 border border-space-750 text-slate-300 text-xs rounded transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh Artifacts</span>
        </button>
      </div>

      {/* Main Artifacts Component */}
      <ArtifactViewer artifacts={artifacts} />
    </div>
  );
}
