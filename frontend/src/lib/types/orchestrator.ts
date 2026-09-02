export type ExecutionStatus =
  | 'CREATED'
  | 'PLANNING'
  | 'PLANNED'
  | 'RUNNING'
  | 'PAUSED'
  | 'RECOVERING'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

export type ExecutionPhase =
  | 'INTENT_NORMALIZATION'
  | 'PLANNING'
  | 'SCHEDULING'
  | 'DISPATCHING'
  | 'VERIFYING'
  | 'RECOVERING'
  | 'FINALIZING';

export type StepLifecycle =
  | 'PENDING'
  | 'READY'
  | 'QUEUED'
  | 'DISPATCHED'
  | 'RUNNING'
  | 'VERIFYING'
  | 'COMPLETED'
  | 'FAILED'
  | 'BLOCKED'
  | 'SKIPPED';

export type EventType =
  | 'EXECUTION_CREATED'
  | 'PLAN_REQUESTED'
  | 'PLAN_RECEIVED'
  | 'STEP_READY'
  | 'STEP_QUEUED'
  | 'STEP_DISPATCHED'
  | 'STEP_STARTED'
  | 'STEP_COMPLETED'
  | 'STEP_FAILED'
  | 'VERIFICATION_STARTED'
  | 'VERIFICATION_PASSED'
  | 'VERIFICATION_FAILED'
  | 'RETRY_SCHEDULED'
  | 'RECOVERY_STARTED'
  | 'REPLAN_REQUESTED'
  | 'REPLAN_RECEIVED'
  | 'ARTIFACT_CREATED'
  | 'EXECUTION_PAUSED'
  | 'EXECUTION_RESUMED'
  | 'EXECUTION_CANCELLED'
  | 'EXECUTION_COMPLETED'
  | 'EXECUTION_FAILED'
  | 'MEMORY_CONTEXT_FETCHED';

export type TrustState =
  | 'UNVERIFIED'
  | 'VALIDATED'
  | 'APPROVED'
  | 'REJECTED'
  | 'RETRIEVED'
  | 'PENDING';

export interface Execution {
  execution_id: string;
  request_id: string;
  user_request: string;
  plan_id?: string | null;
  plan_version: number;
  status: ExecutionStatus;
  phase: ExecutionPhase;
  created_at: string;
  updated_at: string;
  completed_steps: string[];
  failed_steps: string[];
  running_steps: string[];
  blocked_steps: string[];
  pending_steps: string[];
  artifacts: string[];
  events: string[];
  attempts: string[];
  error?: string | null;
  metadata: Record<string, any>;
  correlation_id: string;
}

export interface ExecutionStatusResponse {
  execution_id: string;
  status: ExecutionStatus;
  phase: ExecutionPhase;
  plan_id?: string | null;
  plan_version: number;
  completed_steps: string[];
  failed_steps: string[];
  blocked_steps: string[];
  running_steps: string[];
  pending_steps: string[];
  error?: string | null;
}

export interface ExecutionEvent {
  event_id: string;
  event_type: EventType;
  execution_id: string;
  plan_id?: string | null;
  plan_version?: number | null;
  step_id?: string | null;
  task_id?: string | null;
  attempt_id?: string | null;
  correlation_id: string;
  timestamp: string;
  payload: Record<string, any>;
}

export interface LineageArtifact {
  artifact_id: string;
  execution_id: string;
  plan_id: string;
  plan_version: number;
  step_id: string;
  task_id: string;
  attempt_id: string;
  specialist_id: string;
  artifact_type: string;
  path: string;
  url: string;
  content: string;
  is_mock: boolean;
  parent_artifact_ids: string[];
  source_evidence_refs: string[];
  trust_state: TrustState;
  verification_status: string;
  created_at: string;
  checksum?: string | null;
}

export interface DispatchAttempt {
  attempt_id: string;
  execution_id: string;
  step_id: string;
  task_id: string;
  specialist_id: string;
  attempt_number: number;
  status: string;
  started_at: string;
  completed_at?: string | null;
  error?: string | null;
  output?: any;
  model_name?: string | null;
  provider?: string | null;
}

export interface PlanStep {
  step_id: string;
  specialist: string;
  description: string;
  dependencies: string[];
  priority?: number;
  verification_requirements?: Record<string, any> | string[];
  memory_requirement?: boolean;
  research_requirement?: boolean;
  status?: StepLifecycle;
  retry_policy?: {
    max_retries: number;
    backoff_factor?: number;
  };
}

export interface Plan {
  plan_id: string;
  plan_version: number;
  user_intent?: string;
  steps: PlanStep[];
  created_at?: string;
}

export interface SystemHealth {
  status: string;
  service: string;
  dependencies?: {
    planner?: string;
    memory?: string;
  };
}

export interface SpecialistInfo {
  id: string;
  name: string;
  category: 'BUILD' | 'DATA' | 'QUALITY';
  description: string;
  defaultModel: string;
  modelStatus: 'NOT CONFIGURED' | 'AVAILABLE' | 'OFFLINE';
  activeTask?: string;
  currentAttempt?: number;
  state: StepLifecycle | 'IDLE';
  capabilities: string[];
}
