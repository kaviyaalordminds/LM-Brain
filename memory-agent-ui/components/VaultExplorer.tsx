'use client';

import React, { useState } from 'react';
import { Folder, FolderOpen, FileText, ChevronRight, ChevronDown, Search } from 'lucide-react';
import { VaultTreeNode } from '@/lib/types';

interface VaultExplorerProps {
  root: VaultTreeNode | null;
  selectedPath: string | null;
  onSelectFile: (path: string) => void;
  loading: boolean;
}

const TreeNodeItem: React.FC<{
  node: VaultTreeNode;
  selectedPath: string | null;
  onSelectFile: (path: string) => void;
  filter: string;
  depth?: number;
}> = ({ node, selectedPath, onSelectFile, filter, depth = 0 }) => {
  const [isOpen, setIsOpen] = useState<boolean>(depth < 2);

  if (!node.isDir) {
    if (filter && !node.name.toLowerCase().includes(filter.toLowerCase())) {
      return null;
    }
    const isSelected = selectedPath === node.path;

    return (
      <div
        onClick={() => onSelectFile(node.path)}
        style={{ paddingLeft: `${depth * 14 + 10}px` }}
        className={`flex items-center gap-2 py-1.5 pr-3 rounded-lg text-xs cursor-pointer transition-all ${
          isSelected
            ? 'bg-sky-500/20 text-sky-300 font-bold border border-sky-500/30'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
        }`}
      >
        <FileText className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-sky-400' : 'text-slate-500'}`} />
        <span className="truncate font-mono text-[11px]">{node.name}</span>
      </div>
    );
  }

  // Directory
  const hasMatchingChildren =
    !filter ||
    (node.children &&
      node.children.some(
        (c) =>
          c.name.toLowerCase().includes(filter.toLowerCase()) ||
          (c.isDir && c.children?.some((cc) => cc.name.toLowerCase().includes(filter.toLowerCase())))
      ));

  if (!hasMatchingChildren) return null;

  return (
    <div>
      <div
        onClick={() => setIsOpen(!isOpen)}
        style={{ paddingLeft: `${depth * 14 + 6}px` }}
        className="flex items-center gap-1.5 py-1.5 pr-2 rounded-lg text-xs cursor-pointer text-slate-300 hover:bg-slate-900/60 font-semibold select-none"
      >
        {isOpen ? (
          <ChevronDown className="w-3.5 h-3.5 text-slate-500 shrink-0" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
        )}
        {isOpen ? (
          <FolderOpen className="w-4 h-4 text-purple-400 shrink-0" />
        ) : (
          <Folder className="w-4 h-4 text-purple-400 shrink-0" />
        )}
        <span className="truncate text-xs text-slate-200 font-mono">{node.name || 'AI-Knowledge-Base'}</span>
      </div>

      {isOpen && node.children && (
        <div className="space-y-0.5">
          {node.children.map((child) => (
            <TreeNodeItem
              key={child.path || child.name}
              node={child}
              selectedPath={selectedPath}
              onSelectFile={onSelectFile}
              filter={filter}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const VaultExplorer: React.FC<VaultExplorerProps> = ({
  root,
  selectedPath,
  onSelectFile,
  loading,
}) => {
  const [filter, setFilter] = useState('');

  return (
    <div className="flex flex-col h-full bg-[#0D121F] border border-slate-800 rounded-2xl p-3 shadow-xl">
      {/* Filter Input */}
      <div className="relative mb-3">
        <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
        <input
          type="text"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter notes..."
          className="w-full bg-[#090D15] border border-slate-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500/50 font-mono"
        />
      </div>

      {/* Tree Content */}
      <div className="flex-1 overflow-y-auto pr-1 space-y-0.5">
        {loading ? (
          <div className="p-4 text-center text-xs text-slate-500 font-mono">Loading vault structure...</div>
        ) : root ? (
          <TreeNodeItem
            node={root}
            selectedPath={selectedPath}
            onSelectFile={onSelectFile}
            filter={filter}
          />
        ) : (
          <div className="p-4 text-center text-xs text-slate-500 font-mono">No vault structure loaded.</div>
        )}
      </div>
    </div>
  );
};
