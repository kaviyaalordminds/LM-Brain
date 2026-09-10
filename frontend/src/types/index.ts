/**
 * LM-Brain Frontend Type Definitions
 * Exact mapping to Python backend data contracts in executive_twins
 */

export type OrchestrationStatus =
  | 'RECEIVED'
  | 'PERCEIVING'
  | 'PLANNING'
  | 'VALIDATING'
  | 'SELECTING_CAPABILITIES'
  | 'EXECUTING'
  | 'OBSERVING'
  | 'VERIFYING'
  | 'RECOVERING'
  | 'REPLANNING'
  | 'COMPLETED'
  | 'PARTIAL'
  | 'FAILED'
  | 'BLOCKED'
  | 'NEEDS_INFORMATION';

export type StageStatus =
  | 'WAITING'
  | 'RUNNING'
  | 'COMPLETED'
  | 'FAILED'
  | 'RECOVERING'
  | 'BLOCKED'
  | 'SKIPPED';

export type StageKey =
  | 'PERCEPTION'
  | 'COMPANY_KNOWLEDGE'
  | 'REASONING'
  | 'PLAN_VALIDATION'
  | 'CAPABILITY_SELECTION'
  | 'SPECIALIST_DELEGATION'
  | 'CONTROLLED_EXECUTION'
  | 'OBSERVATION_QA'
  | 'VERIFICATION'
  | 'MEMORY_WRITEBACK';

export interface WorkflowStage {
  key: StageKey;
  label: string;
  shortDescription: string;
  status: StageStatus;
  timestamp?: string;
  durationMs?: number;
  details?: Record<string, any>;
}

export type FactState = 'FACT' | 'INFERENCE' | 'ASSUMPTION' | 'UNKNOWN';

export interface FactItem {
  statement: string;
  state: FactState;
  source: string;
  confidence?: number;
}

export interface ObsidianDocument {
  documentId: string;
  vaultPath: string;
  title: string;
  content: string;
  facts: FactItem[];
  confidence: number;
  lastModified?: string;
}

export type ReasoningMode =
  | 'PLAN'
  | 'DECOMPOSE'
  | 'DECIDE'
  | 'RECOVER'
  | 'REPLAN'
  | 'DEVELOP'
  | 'ANALYZE';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface ReasoningStep {
  stepId: string;
  objective: string;
  requiredCapability: string;
  specialistRole?: string;
  dependencies: string[];
  expectedOutput: string;
  verificationRequirement: string;
  riskLevel: RiskLevel;
  parameters: Record<string, any>;
  rationale?: string;
}

export interface ReasoningPlan {
  planId: string;
  goal: string;
  steps: ReasoningStep[];
  dependencies: string[];
  successCriteria: string[];
  assumptions: string[];
  requiredCapabilities: string[];
  confidence: number;
  verificationRequirements: string[];
}

export type SpecialistStatus = 'ACTIVE' | 'AVAILABLE' | 'BUSY' | 'OFFLINE' | 'UNREGISTERED';

export interface Capability {
  name: string;
  description: string;
  version: string;
  requiredTools: string[];
}

export interface SpecialistMetadata {
  specialistId: string;
  name: string;
  category: string;
  capabilities: Capability[];
  status: SpecialistStatus;
  authorizedTools: string[];
  securityLevel: string;
  description: string;
  isTwin?: boolean;
  activationPolicy?: string;
}

export interface StepExecutionRecord {
  stepId: string;
  objective: string;
  requiredCapability: string;
  specialistId?: string;
  specialistName?: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'SKIPPED';
  output: string;
  artifacts: string[];
  evidenceIds: string[];
  error?: string;
  startedAt?: string;
  completedAt?: string;
  durationSeconds: number;
}

export type EvidenceCategory =
  | 'ARTIFACT'
  | 'EXECUTION_LOG'
  | 'TEST'
  | 'DATA'
  | 'SOURCE'
  | 'API_RESPONSE'
  | 'VERIFICATION';

export interface BaseEvidence {
  evidenceId: string;
  category: EvidenceCategory;
  timestamp: string;
  systemGenerated: boolean;
  description: string;
}

export interface ArtifactEvidence extends BaseEvidence {
  category: 'ARTIFACT';
  artifactUri: string;
  mimeType: string;
  checksumSha256?: string;
}

export interface ExecutionLogEvidence extends BaseEvidence {
  category: 'EXECUTION_LOG';
  executionId: string;
  logSnippet: string;
  exitCode: number;
}

export interface TestEvidence extends BaseEvidence {
  category: 'TEST';
  suiteName: string;
  testsPassed: number;
  testsFailed: number;
  reportUri?: string;
}

export interface VerificationEvidence extends BaseEvidence {
  category: 'VERIFICATION';
  verifierId: string;
  verifiedStatus: string;
  verifiedAt: string;
}

export type TypedEvidence =
  | ArtifactEvidence
  | ExecutionLogEvidence
  | TestEvidence
  | VerificationEvidence
  | BaseEvidence;

export interface WorkspaceFile {
  path: string;
  operation: 'CREATE' | 'UPDATE' | 'READ' | 'DELETE' | 'INSPECT';
  status: 'SUCCESS' | 'FAILED' | 'PENDING';
  sizeBytes?: number;
  contentSnippet?: string;
  mimeType?: string;
  modifiedAt?: string;
}

export interface ValidationRecord {
  operation: 'BUILD' | 'TEST' | 'LINT' | 'SECURITY_SCAN';
  command: string;
  status: 'PASSED' | 'FAILED' | 'RUNNING' | 'PENDING';
  exitCode: number;
  output: string;
  restrictedShell: boolean;
}

export interface MemoryWritebackRecord {
  status: 'COMPLETED' | 'NOT_PERFORMED' | 'FAILED' | 'PENDING';
  source: string;
  targetVaultPath: string;
  recordedState: string;
  approvalStatus: 'APPROVED' | 'REJECTED' | 'NOT_APPLICABLE';
  factsPersisted: FactItem[];
  reason?: string;
  timestamp?: string;
}

export interface RecoveryEvent {
  attempt: number;
  maxAttempts: number;
  triggerError: string;
  failureObserved: string;
  diagnosis: string;
  replannedGoal: string;
  replanStepCount: number;
  status: 'IN_PROGRESS' | 'RECOVERED' | 'EXHAUSTED';
}

export interface AuditEvent {
  eventId: string;
  eventType: string;
  timestamp: string;
  payload: Record<string, any>;
}

export interface ExecutiveTwin {
  twinId: string;
  role: 'CEO' | 'COO' | 'CTO' | 'CMO' | 'CFO';
  title: string;
  strategicScope: string;
  activationCondition: string;
  status: 'CONDITIONAL' | 'ACTIVE' | 'STANDBY';
  responsibilities: string[];
  reviewPolicy: string;
}

export interface WorkRequest {
  requestId: string;
  userGoal: string;
  category?: string;
  requireMemoryWriteback: boolean;
  requireTwinEvaluation: boolean;
  availableCapabilities: string[];
  simulateFailure?: boolean;
  simulateRepeatedFailure?: boolean;
}

export interface WorkflowRun {
  runId: string;
  requestId: string;
  userGoal: string;
  status: OrchestrationStatus;
  stages: WorkflowStage[];
  currentStageIndex: number;
  reasoningPlan?: ReasoningPlan;
  knowledgeRetrieved?: ObsidianDocument[];
  selectedSpecialists: Record<string, string>; // capability -> specialistId
  specialistExecutions: StepExecutionRecord[];
  workspaceFiles: WorkspaceFile[];
  validations: ValidationRecord[];
  evidenceItems: TypedEvidence[];
  verificationChecklist: { criterion: string; passed: boolean; details?: string }[];
  memoryWriteback?: MemoryWritebackRecord;
  recoveryHistory: RecoveryEvent[];
  auditEvents: AuditEvent[];
  executiveTwinActivated?: ExecutiveTwin;
  startedAt: string;
  completedAt?: string;
  durationSeconds: number;
  isDemo: boolean;
}

export interface SystemStats {
  systemStatus: 'Operational' | 'Degraded' | 'Offline';
  activeRunsCount: number;
  completedRunsCount: number;
  availableWorkersCount: number;
  knowledgeDocumentsCount: number;
  evidenceItemsCount: number;
  backendConnected: boolean;
  isDemoMode: boolean;
}
