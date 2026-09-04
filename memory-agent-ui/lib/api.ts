import {
  SearchResponse,
  ResearchResponse,
  ValidationResult,
  WriteResponse,
  ContextResponse,
  HealthResponse,
  ApprovalStatus,
  EvidenceItem,
  VaultTreeNode,
  VaultFileDetail,
} from './types';
import { MEMORY_AGENT_API_URL } from './config';

export async function checkBackendHealth(): Promise<{
  online: boolean;
  data?: HealthResponse;
  error?: string;
}> {
  try {
    const res = await fetch(`${MEMORY_AGENT_API_URL}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(2500),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return { online: true, data };
  } catch (err: any) {
    return { online: false, error: err?.message || 'Connection refused' };
  }
}

export async function searchMemory(
  query: string,
  taskId?: string,
  context?: string,
  filters?: Record<string, any>,
  autoResearch?: boolean
): Promise<SearchResponse> {
  const res = await fetch(`${MEMORY_AGENT_API_URL}/api/v1/memory/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      taskId: taskId || null,
      context: context || null,
      filters: filters || {},
      autoResearch: autoResearch ?? false,
    }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Search failed with HTTP ${res.status}`);
  }
  return res.json();
}

export async function researchMemory(
  query: string,
  taskId?: string
): Promise<ResearchResponse> {
  const res = await fetch(`${MEMORY_AGENT_API_URL}/api/v1/memory/research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, taskId: taskId || null }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Research failed with HTTP ${res.status}`);
  }
  return res.json();
}

export async function validateEvidence(
  evidence: EvidenceItem[],
  query: string,
  context?: string
): Promise<ValidationResult> {
  const res = await fetch(`${MEMORY_AGENT_API_URL}/api/v1/memory/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ evidence, query, context: context || null }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Validation failed with HTTP ${res.status}`);
  }
  return res.json();
}

export async function writeKnowledge(
  content: string,
  targetNote: string,
  approvalStatus: ApprovalStatus,
  evidenceRefs: EvidenceItem[] = [],
  taskId?: string
): Promise<WriteResponse> {
  const res = await fetch(`${MEMORY_AGENT_API_URL}/api/v1/memory/write`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      content,
      targetNote,
      approvalStatus,
      evidenceRefs,
      taskId: taskId || null,
    }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Write failed with HTTP ${res.status}`);
  }
  return res.json();
}

export async function getTaskContext(taskId: string): Promise<ContextResponse> {
  const res = await fetch(`${MEMORY_AGENT_API_URL}/api/v1/memory/context/${encodeURIComponent(taskId)}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Context fetch failed with HTTP ${res.status}`);
  }
  return res.json();
}

export async function getVaultTree(): Promise<{ root: VaultTreeNode; totalFiles: number }> {
  const res = await fetch('/api/vault/tree');
  if (!res.ok) throw new Error('Failed to load Obsidian vault tree');
  return res.json();
}

export async function getVaultFile(relPath: string): Promise<VaultFileDetail> {
  const res = await fetch(`/api/vault/file?path=${encodeURIComponent(relPath)}`);
  if (!res.ok) throw new Error(`Failed to read file: ${relPath}`);
  return res.json();
}
