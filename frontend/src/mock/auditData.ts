import { AuditEvent } from '../types';

export const mockAuditEvents: AuditEvent[] = [
  {
    eventId: 'evt_001',
    eventType: 'ORCHESTRATION_STARTED',
    timestamp: '2026-09-10T09:12:01.102Z',
    payload: {
      requestId: 'RUN-001',
      userGoal: 'Create a small company landing page using the company\'s approved company information.',
      requireMemoryWriteback: true,
      securityContext: { isAuthenticated: true, securityLevel: 'standard' },
    },
  },
  {
    eventId: 'evt_002',
    eventType: 'PERCEPTION_COMPLETED',
    timestamp: '2026-09-10T09:12:01.350Z',
    payload: {
      normalizedGoal: 'Synthesize landing page for NovaPulse Robotics using authoritative company profile facts',
      identifiedDomains: ['web_development', 'file_operations', 'build_validation'],
      strategicDecisionRequired: false,
    },
  },
  {
    eventId: 'evt_003',
    eventType: 'KNOWLEDGE_RETRIEVED',
    timestamp: '2026-09-10T09:12:01.710Z',
    payload: {
      sourceSystem: 'Company Obsidian Vault',
      documentsCount: 2,
      factsRetrievedCount: 5,
      authorityLevel: 'AUTHORITATIVE',
      vaultPaths: ['company_knowledge/default/company_profile.md', 'company_knowledge/branding/brand_standards.md'],
    },
  },
  {
    eventId: 'evt_004',
    eventType: 'REASONING_COMPLETED',
    timestamp: '2026-09-10T09:12:02.110Z',
    payload: {
      reasoningMode: 'DEVELOP',
      planId: 'plan_landing_page_01',
      totalSteps: 4,
      riskLevel: 'LOW',
      confidence: 0.98,
      requiredCapabilities: ['web_development', 'software_development', 'file_operations', 'build_validation'],
    },
  },
  {
    eventId: 'evt_005',
    eventType: 'PLAN_VALIDATED',
    timestamp: '2026-09-10T09:12:02.240Z',
    payload: {
      validationResult: 'PASSED',
      ruleSet: 'StrictBoundsValidator_v1',
      cyclesDetected: false,
      unregisteredCapabilities: [],
    },
  },
  {
    eventId: 'evt_006',
    eventType: 'CAPABILITY_SELECTED',
    timestamp: '2026-09-10T09:12:02.420Z',
    payload: {
      capability: 'web_development',
      specialistId: 'spec_web_dev_01',
      specialistName: 'Web Development Specialist',
      matchConfidence: 1.0,
      reason: 'Authoritative capability registry match',
    },
  },
  {
    eventId: 'evt_007',
    eventType: 'SPECIALIST_DELEGATED',
    timestamp: '2026-09-10T09:12:02.610Z',
    payload: {
      delegatedTo: 'spec_web_dev_01',
      workspaceId: 'run-001',
      securityGuardEnforced: true,
      allowedTools: ['file_create', 'file_update', 'file_read', 'build_validate'],
    },
  },
  {
    eventId: 'evt_008',
    eventType: 'EXECUTION_COMPLETED',
    timestamp: '2026-09-10T09:12:06.120Z',
    payload: {
      filesCreated: ['index.html', 'styles.css', 'app.tsx', 'README.md'],
      workspace: 'run-001',
      executionDurationSeconds: 3.51,
      securityViolations: 0,
    },
  },
  {
    eventId: 'evt_009',
    eventType: 'OBSERVATION_RECORDED',
    timestamp: '2026-09-10T09:12:06.840Z',
    payload: {
      artifactsCaptured: 3,
      testsRun: 4,
      testsPassed: 4,
      evidenceCategories: ['ARTIFACT', 'EXECUTION_LOG', 'TEST', 'VERIFICATION'],
    },
  },
  {
    eventId: 'evt_010',
    eventType: 'VERIFICATION_COMPLETED',
    timestamp: '2026-09-10T09:12:07.310Z',
    payload: {
      criteriaEvaluatedCount: 7,
      criteriaPassedCount: 7,
      finalVerificationStatus: 'VERIFIED',
    },
  },
  {
    eventId: 'evt_011',
    eventType: 'MEMORY_WRITEBACK_COMPLETED',
    timestamp: '2026-09-10T09:12:07.820Z',
    payload: {
      targetVaultPath: 'company_knowledge/runs/run_001_landing_page.md',
      status: 'APPROVED',
      factsPersistedCount: 4,
      authoritativeSource: 'Company Obsidian',
    },
  },
  {
    eventId: 'evt_012',
    eventType: 'ORCHESTRATION_COMPLETED',
    timestamp: '2026-09-10T09:12:08.100Z',
    payload: {
      finalStatus: 'COMPLETED',
      totalDurationSeconds: 6.998,
      recoveryAttempts: 0,
    },
  },
];
