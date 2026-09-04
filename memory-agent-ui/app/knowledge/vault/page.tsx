'use client';

import React, { useState, useEffect } from 'react';
import { VaultExplorer } from '@/components/VaultExplorer';
import { FileViewer } from '@/components/FileViewer';
import { VaultTreeNode, VaultFileDetail } from '@/lib/types';
import { getVaultTree, getVaultFile } from '@/lib/api';

export default function VaultPage() {
  const [treeRoot, setTreeRoot] = useState<VaultTreeNode | null>(null);
  const [totalFiles, setTotalFiles] = useState<number>(0);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<VaultFileDetail | null>(null);
  const [loadingTree, setLoadingTree] = useState<boolean>(true);
  const [loadingFile, setLoadingFile] = useState<boolean>(false);

  useEffect(() => {
    async function loadTree() {
      setLoadingTree(true);
      try {
        const res = await getVaultTree();
        setTreeRoot(res.root);
        setTotalFiles(res.totalFiles);
        // Default select index file if present
        if (res.root?.children && res.root.children.length > 0) {
          const firstDir = res.root.children[0];
          if (firstDir.children && firstDir.children.length > 0) {
            handleSelectFile(firstDir.children[0].path);
          }
        }
      } catch (err) {
        console.error('Failed to load tree:', err);
      }
      setLoadingTree(false);
    }
    loadTree();
  }, []);

  const handleSelectFile = async (relPath: string) => {
    setSelectedPath(relPath);
    setLoadingFile(true);
    try {
      const fileData = await getVaultFile(relPath);
      setSelectedFile(fileData);
    } catch (err) {
      console.error('Failed to read file:', err);
      setSelectedFile(null);
    }
    setLoadingFile(false);
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-base font-bold text-white tracking-wide font-sans">
            Obsidian Knowledge Base
          </h1>
          <p className="text-xs text-slate-400 font-mono">
            Source of Truth &bull; {totalFiles} Markdown Notes Tracked
          </p>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 min-h-0">
        {/* Left Column: Hierarchical Tree Explorer */}
        <div className="lg:col-span-1 h-full min-h-0">
          <VaultExplorer
            root={treeRoot}
            selectedPath={selectedPath}
            onSelectFile={handleSelectFile}
            loading={loadingTree}
          />
        </div>

        {/* Right Column: File Reader */}
        <div className="lg:col-span-2 h-full min-h-0">
          <FileViewer file={selectedFile} loading={loadingFile} />
        </div>
      </div>
    </div>
  );
}
