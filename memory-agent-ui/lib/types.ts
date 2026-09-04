export type ApprovalStatus =
  | 'pending'
  | 'unverified'
  | 'validated'
  | 'approved'
  | 'rejected'
  | 'retrieved';

export type ValidationStatus = 'passed' | 'failed' | 'pending';

export interface EvidenceItem {
  id: string;
  source: string;
  title?: string | null;
  content: string;
  retrievedAt: string;
  relevance: number;
  validationStatus: ValidationStatus;
  approvalStatus: ApprovalStatus;
}

export interface MemoryResult {
  id: string;
  query: string;
  content: string;
  sources: string[];
  evidenceRefs: EvidenceItem[];
  relevance: number;
  timestamp: string;
  approvalStatus: ApprovalStatus;
  targetNote?: string | null;
  taskId?: string | null;
  sourceNote?: string | null;
  matchedSection?: string | null;
  evidenceExcerpt?: string | null;
  relevanceReason?: string | null;
}

export interface TaskScope {
  taskType: string;
  domain?: string | null;
  entity?: string | null;
  platform?: string | null;
  discriminators?: string[];
  requirements: string[];
  rawQuery: string;
}

export interface KnowledgeGapItem {
  requirement: string;
  status: 'satisfied' | 'missing' | 'partial';
  matchedNote?: string | null;
  relevance: number;
  reason?: string | null;
  evidenceExcerpt?: string | null;
}

export interface RejectedCandidate {
  sourceNote: string;
  title: string;
  relevance: number;
  rejectionReason: string;
}

export interface VaultScanStats {
  foldersScanned: number;
  totalFilesDiscovered: number;
  markdownFilesIndexed: number;
  candidatesEvaluated: number;
  acceptedCount: number;
  rejectedCount: number;
}

export interface SearchResponse {
  results: MemoryResult[];
  found: boolean;
  count: number;
  taskScope?: TaskScope | null;
  knowledgeGaps?: KnowledgeGapItem[];
  rejectedCandidates?: RejectedCandidate[];
  vaultScanStats?: VaultScanStats | null;
  debugInfo?: Record<string, any>;
}

export interface ResearchResponse {
  evidence: EvidenceItem[];
  sources: string[];
  count: number;
  taskScope?: TaskScope | null;
}

export interface ValidationResult {
  status: ApprovalStatus;
  reason: string;
  approved: boolean;
  assessment: Record<string, any>;
}

export interface WriteResponse {
  noteId?: string | null;
  status: 'written' | 'rejected' | string;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface ContextResponse {
  taskId: string;
  context: MemoryResult[];
  sources: string[];
  timestamp: string;
  taskScope?: TaskScope | null;
  knowledgeGaps?: KnowledgeGapItem[];
}

export interface HealthResponse {
  status: string;
  service: string;
}

export interface VaultTreeNode {
  name: string;
  path: string;
  isDir: boolean;
  size?: number;
  children?: VaultTreeNode[];
}

export interface VaultFileDetail {
  path: string;
  name: string;
  sizeBytes: number;
  lastModified: string;
  content: string;
  frontmatter?: Record<string, any>;
  headings?: string[];
  tags?: string[];
}
