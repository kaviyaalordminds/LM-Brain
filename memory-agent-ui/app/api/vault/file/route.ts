import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { OBSIDIAN_VAULT_PATH } from '@/lib/config';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const relPath = searchParams.get('path');
    if (!relPath) {
      return NextResponse.json({ error: 'Missing path parameter' }, { status: 400 });
    }

    const vaultPath = path.resolve(OBSIDIAN_VAULT_PATH);
    const fullPath = path.resolve(vaultPath, relPath);

    if (!fullPath.startsWith(vaultPath)) {
      return NextResponse.json({ error: 'Invalid path access' }, { status: 403 });
    }

    if (!fs.existsSync(fullPath)) {
      return NextResponse.json({ error: 'File not found' }, { status: 404 });
    }

    const stat = fs.statSync(fullPath);
    const rawContent = fs.readFileSync(fullPath, 'utf-8');

    let body = rawContent;
    let frontmatter: Record<string, any> = {};
    if (rawContent.startsWith('---')) {
      const parts = rawContent.split('---', 3);
      if (parts.length >= 3) {
        body = parts[2].trim();
        parts[1].split('\n').forEach((line) => {
          const colonIdx = line.indexOf(':');
          if (colonIdx !== -1) {
            const k = line.slice(0, colonIdx).trim();
            const v = line.slice(colonIdx + 1).trim();
            if (k) frontmatter[k] = v;
          }
        });
      }
    }

    const headings: string[] = [];
    body.split('\n').forEach((line) => {
      const m = line.match(/^#{1,6}\s+(.+)$/);
      if (m) headings.push(m[1].trim());
    });

    return NextResponse.json({
      path: relPath.replace(/\\/g, '/'),
      name: path.basename(fullPath),
      sizeBytes: stat.size,
      lastModified: stat.mtime.toISOString(),
      content: rawContent,
      frontmatter,
      headings,
    });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
