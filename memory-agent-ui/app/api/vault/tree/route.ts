import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { VaultTreeNode } from '@/lib/types';
import { OBSIDIAN_VAULT_PATH } from '@/lib/config';

function buildTree(dirPath: string, rootPath: string): { node: VaultTreeNode; count: number } {
  const name = path.basename(dirPath);
  const relPath = path.relative(rootPath, dirPath).replace(/\\/g, '/');
  
  if (!fs.existsSync(dirPath)) {
    return {
      node: { name, path: relPath, isDir: true, children: [] },
      count: 0,
    };
  }

  const stat = fs.statSync(dirPath);
  if (!stat.isDirectory()) {
    return {
      node: { name, path: relPath, isDir: false, size: stat.size },
      count: 1,
    };
  }

  const entries = fs.readdirSync(dirPath);
  const children: VaultTreeNode[] = [];
  let fileCount = 0;

  for (const entry of entries) {
    if (entry.startsWith('.')) continue;
    const fullChild = path.join(dirPath, entry);
    const { node: childNode, count } = buildTree(fullChild, rootPath);
    children.push(childNode);
    fileCount += count;
  }

  children.sort((a, b) => {
    if (a.isDir && !b.isDir) return -1;
    if (!a.isDir && b.isDir) return 1;
    return a.name.localeCompare(b.name);
  });

  return {
    node: { name, path: relPath, isDir: true, children },
    count: fileCount,
  };
}

export async function GET() {
  try {
    const vaultPath = path.resolve(OBSIDIAN_VAULT_PATH);
    if (!fs.existsSync(vaultPath)) {
      return NextResponse.json(
        { error: `Obsidian vault directory not found at: ${vaultPath}` },
        { status: 404 }
      );
    }

    const { node, count } = buildTree(vaultPath, vaultPath);
    return NextResponse.json({ root: node, totalFiles: count });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
