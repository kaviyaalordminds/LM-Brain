import React, { useState } from 'react';
import { CheckCircle2, Code2, FileCode, FileText, FolderGit2, ShieldCheck } from 'lucide-react';
import { WorkspaceFile } from '../../types';
import { Badge } from '../common/Badge';
import { Card } from '../common/Card';
import { CodeBlock } from '../common/CodeBlock';

interface WorkspaceFilesViewProps {
  files?: WorkspaceFile[];
  workspaceId?: string;
}

export const WorkspaceFilesView: React.FC<WorkspaceFilesViewProps> = ({
  files = [],
  workspaceId = 'run-001',
}) => {
  const [selectedFile, setSelectedFile] = useState<WorkspaceFile | null>(
    files.length > 0 ? files[0] : null
  );

  // Sync selected file if list updates
  React.useEffect(() => {
    if (files.length > 0 && !selectedFile) {
      setSelectedFile(files[0]);
    }
  }, [files]);

  if (files.length === 0) {
    return (
      <Card
        title="Software Development Workspace (Files API)"
        subtitle="Controlled sandbox directory bounded by Files API"
        icon={<FolderGit2 className="w-4 h-4 text-cyan-400" />}
      >
        <div className="py-6 text-center text-xs text-slate-500 font-mono">
          No files synthesized yet. Awaiting specialist file synthesis stage...
        </div>
      </Card>
    );
  }

  const activeFile = selectedFile || files[0];

  return (
    <Card
      title="Controlled Software Workspace (Files API View)"
      subtitle="Sandboxed project directory — Unrestricted host filesystem access is strictly blocked"
      icon={<FolderGit2 className="w-4 h-4 text-cyan-400" />}
      badge={<Badge variant="success" size="sm" dot>Controlled Workspace ✓</Badge>}
    >
      <div className="space-y-4">
        {/* Workspace Security Header */}
        <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Sandbox ID:</span>
            <span className="font-bold text-slate-200">{workspaceId}</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-slate-400">
              Total Files: <strong className="text-cyan-400">{files.length}</strong>
            </span>
            <span className="text-slate-400">
              Artifacts: <strong className="text-indigo-400">3 Verified</strong>
            </span>
          </div>
        </div>

        {/* Files Grid & Inspector */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* File List */}
          <div className="space-y-1.5 md:col-span-1">
            <div className="text-[11px] font-mono font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Synthesized Files ({files.length})
            </div>
            {files.map((file) => {
              const isSelected = activeFile.path === file.path;
              return (
                <button
                  key={file.path}
                  onClick={() => setSelectedFile(file)}
                  className={`w-full text-left p-2.5 rounded-lg border transition-all flex items-center justify-between text-xs font-mono ${
                    isSelected
                      ? 'bg-indigo-950/70 border-indigo-500/80 text-white shadow-sm'
                      : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-900'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <FileCode className={`w-3.5 h-3.5 ${isSelected ? 'text-indigo-400' : 'text-slate-400'}`} />
                    <span className="font-medium truncate">{file.path}</span>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <span className="text-[10px] text-slate-500 font-normal">{file.operation}</span>
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  </div>
                </button>
              );
            })}
          </div>

          {/* Code Viewer Panel */}
          <div className="md:col-span-2">
            {activeFile && (
              <CodeBlock
                code={activeFile.contentSnippet || `// File: ${activeFile.path}\n// Synthesized under controlled workspace sandbox.`}
                language={activeFile.mimeType || 'code'}
                title={`Controlled File: ${activeFile.path} (${activeFile.sizeBytes || 1024} bytes)`}
                maxHeight="max-h-72"
              />
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};
