import {
  AuditEvent,
  ExecutiveTwin,
  ObsidianDocument,
  SpecialistMetadata,
  SystemStats,
  TypedEvidence,
  WorkflowRun,
  WorkRequest,
} from '../types';
import {
  mockAuditEvents,
  mockExecutiveTwins,
  mockObsidianKnowledge,
  mockRuns,
  mockSpecialists,
} from '../mock';

/**
 * Workforce API Service Abstraction
 * Defines the clean interface between UI and backend orchestration services.
 * In DEMO MODE, operates against deterministic stateful mock store.
 * Pluggable for real FastAPI backend adapter when backend REST/WebSocket routes are deployed.
 */
export interface IWorkforceApi {
  getSystemStats(): Promise<SystemStats>;
  getRuns(): Promise<WorkflowRun[]>;
  getRunById(runId: string): Promise<WorkflowRun | null>;
  createRun(request: WorkRequest): Promise<WorkflowRun>;
  getSpecialists(): Promise<SpecialistMetadata[]>;
  getExecutiveTwins(): Promise<ExecutiveTwin[]>;
  getCompanyKnowledge(): Promise<ObsidianDocument[]>;
  getEvidenceVault(): Promise<TypedEvidence[]>;
  getAuditLog(): Promise<AuditEvent[]>;
  cancelRun(runId: string): Promise<boolean>;
}

class DemoWorkforceApi implements IWorkforceApi {
  private runs: WorkflowRun[] = [...mockRuns];

  async getSystemStats(): Promise<SystemStats> {
    const active = this.runs.filter(r => ['PERCEIVING', 'PLANNING', 'VALIDATING', 'SELECTING_CAPABILITIES', 'EXECUTING', 'OBSERVING', 'VERIFYING', 'RECOVERING'].includes(r.status)).length;
    const completed = this.runs.filter(r => r.status === 'COMPLETED').length;

    return {
      systemStatus: 'Operational',
      activeRunsCount: active,
      completedRunsCount: completed,
      availableWorkersCount: mockSpecialists.length,
      knowledgeDocumentsCount: mockObsidianKnowledge.length,
      evidenceItemsCount: this.runs.flatMap(r => r.evidenceItems).length,
      backendConnected: false, // Explicitly false for Demo Mode!
      isDemoMode: true,
    };
  }

  async getRuns(): Promise<WorkflowRun[]> {
    return [...this.runs];
  }

  async getRunById(runId: string): Promise<WorkflowRun | null> {
    const run = this.runs.find(r => r.runId.toUpperCase() === runId.toUpperCase());
    return run ? JSON.parse(JSON.stringify(run)) : null;
  }

  async createRun(request: WorkRequest): Promise<WorkflowRun> {
    const nextIndex = this.runs.length + 1;
    const runId = `RUN-00${nextIndex}`;

    const newRun: WorkflowRun = {
      runId,
      requestId: request.requestId || `req_${Date.now()}`,
      userGoal: request.userGoal,
      status: 'RECEIVED',
      durationSeconds: 0,
      isDemo: true,
      startedAt: new Date().toISOString(),
      currentStageIndex: 0,
      stages: [
        { key: 'PERCEPTION', label: 'Perception', shortDescription: 'Waiting for intent normalization...', status: 'WAITING' },
        { key: 'COMPANY_KNOWLEDGE', label: 'Company Knowledge', shortDescription: 'Authoritative Obsidian retrieval pending', status: 'WAITING' },
        { key: 'REASONING', label: 'Reasoning', shortDescription: 'Structured planning awaiting knowledge context', status: 'WAITING' },
        { key: 'PLAN_VALIDATION', label: 'Plan Validation', shortDescription: 'Bounds and cycle checking pending', status: 'WAITING' },
        { key: 'CAPABILITY_SELECTION', label: 'Capability Selection', shortDescription: 'Specialist registry matching pending', status: 'WAITING' },
        { key: 'SPECIALIST_DELEGATION', label: 'Specialist Delegation', shortDescription: 'SecurityGuard boundary allocation pending', status: 'WAITING' },
        { key: 'CONTROLLED_EXECUTION', label: 'Controlled Execution', shortDescription: 'Sandboxed capability execution pending', status: 'WAITING' },
        { key: 'OBSERVATION_QA', label: 'Observation / QA', shortDescription: 'Empirical evidence capture pending', status: 'WAITING' },
        { key: 'VERIFICATION', label: 'Verification', shortDescription: 'Success criteria verification pending', status: 'WAITING' },
        { key: 'MEMORY_WRITEBACK', label: 'Memory Writeback', shortDescription: 'Authoritative Obsidian persistence pending', status: 'WAITING' },
      ],
      selectedSpecialists: {},
      specialistExecutions: [],
      workspaceFiles: [],
      validations: [],
      evidenceItems: [],
      verificationChecklist: [],
      recoveryHistory: [],
      auditEvents: [],
    };

    this.runs.unshift(newRun);
    return JSON.parse(JSON.stringify(newRun));
  }

  async getSpecialists(): Promise<SpecialistMetadata[]> {
    return [...mockSpecialists];
  }

  async getExecutiveTwins(): Promise<ExecutiveTwin[]> {
    return [...mockExecutiveTwins];
  }

  async getCompanyKnowledge(): Promise<ObsidianDocument[]> {
    return [...mockObsidianKnowledge];
  }

  async getEvidenceVault(): Promise<TypedEvidence[]> {
    const allEvidence = this.runs.flatMap(r => r.evidenceItems);
    return allEvidence.length > 0 ? allEvidence : mockRuns[0].evidenceItems;
  }

  async getAuditLog(): Promise<AuditEvent[]> {
    const allAudits = this.runs.flatMap(r => r.auditEvents);
    return allAudits.length > 0 ? allAudits : mockAuditEvents;
  }

  async cancelRun(runId: string): Promise<boolean> {
    const run = this.runs.find(r => r.runId === runId);
    if (run) {
      run.status = 'BLOCKED';
      return true;
    }
    return false;
  }
}

export const workforceApi: IWorkforceApi = new DemoWorkforceApi();
