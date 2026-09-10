import { WorkflowRun } from '../types';
import { mockObsidianKnowledge } from './knowledgeData';
import { mockExecutiveTwins } from './specialistsData';
import { mockAuditEvents } from './auditData';

export const mockRuns: WorkflowRun[] = [
  {
    runId: 'RUN-001',
    requestId: 'req_landing_page_01',
    userGoal: 'Create a small company landing page using the company\'s approved company information.\n\nInclude:\n- company name\n- company description\n- services/products\n- contact information\n\nCreate the project in the controlled software development workspace.\nValidate the generated project.\nOnly report completion after verification.\nRecord the approved completion state in company memory.',
    status: 'COMPLETED',
    durationSeconds: 14.2,
    isDemo: true,
    startedAt: '2026-09-10T09:12:01Z',
    completedAt: '2026-09-10T09:12:15Z',
    currentStageIndex: 9,
    stages: [
      { key: 'PERCEPTION', label: 'Perception', shortDescription: 'Normalized goal and extracted operational intents', status: 'COMPLETED', durationMs: 240, timestamp: '09:12:01' },
      { key: 'COMPANY_KNOWLEDGE', label: 'Company Knowledge', shortDescription: 'Retrieved authoritative facts from Obsidian Vault', status: 'COMPLETED', durationMs: 360, timestamp: '09:12:01' },
      { key: 'REASONING', label: 'Reasoning', shortDescription: 'Constructed machine-validatable structured execution plan', status: 'COMPLETED', durationMs: 400, timestamp: '09:12:02' },
      { key: 'PLAN_VALIDATION', label: 'Plan Validation', shortDescription: 'Validated bounds, schema compliance, and capability availability', status: 'COMPLETED', durationMs: 130, timestamp: '09:12:02' },
      { key: 'CAPABILITY_SELECTION', label: 'Capability Selection', shortDescription: 'Matched required capabilities with registered active specialists', status: 'COMPLETED', durationMs: 180, timestamp: '09:12:02' },
      { key: 'SPECIALIST_DELEGATION', label: 'Specialist Delegation', shortDescription: 'Assigned bounded subtasks to Web & Software Dev Specialists', status: 'COMPLETED', durationMs: 190, timestamp: '09:12:02' },
      { key: 'CONTROLLED_EXECUTION', label: 'Controlled Execution', shortDescription: 'Executed file synthesis inside sandboxed workspace via SecurityGuard', status: 'COMPLETED', durationMs: 3510, timestamp: '09:12:06' },
      { key: 'OBSERVATION_QA', label: 'Observation / QA', shortDescription: 'Collected execution logs, build validation, and artifact hashes', status: 'COMPLETED', durationMs: 720, timestamp: '09:12:06' },
      { key: 'VERIFICATION', label: 'Verification', shortDescription: 'Evaluated all empirical success criteria before declaring success', status: 'COMPLETED', durationMs: 470, timestamp: '09:12:07' },
      { key: 'MEMORY_WRITEBACK', label: 'Memory Writeback', shortDescription: 'Persisted verified completion state to authoritative Company Obsidian', status: 'COMPLETED', durationMs: 510, timestamp: '09:12:07' },
    ],
    reasoningPlan: {
      planId: 'plan_landing_page_01',
      goal: 'Create NovaPulse Robotics landing page using approved Obsidian profile facts',
      dependencies: [],
      successCriteria: [
        'index.html contains exact company name and profile facts',
        'styles.css implements responsive typography and brand palette',
        'app.tsx provides interactive service catalog component',
        'Controlled build validation succeeds with exit code 0',
        'Verification evidence matches all success criteria',
      ],
      assumptions: ['Company profile in Obsidian is authoritative and approved'],
      requiredCapabilities: ['web_development', 'software_development', 'file_operations', 'build_validation'],
      confidence: 0.98,
      verificationRequirements: ['All files exist in sandbox', 'HTML validates', 'Build exit code 0'],
      steps: [
        {
          stepId: '01',
          objective: 'Retrieve approved company information from Company Obsidian',
          requiredCapability: 'company_knowledge_retrieval',
          specialistRole: 'Knowledge Service',
          dependencies: [],
          expectedOutput: 'Authoritative facts for NovaPulse Robotics',
          verificationRequirement: 'Facts confidence score = 1.0',
          riskLevel: 'LOW',
          parameters: { vault_path: 'company_knowledge/default/company_profile.md' },
        },
        {
          stepId: '02',
          objective: 'Create controlled workspace environment sandbox',
          requiredCapability: 'workspace_create',
          specialistRole: 'Software Development Specialist',
          dependencies: ['01'],
          expectedOutput: 'Workspace run-001 initialized',
          verificationRequirement: 'Directory isolation confirmed',
          riskLevel: 'LOW',
          parameters: { workspace_id: 'run-001' },
        },
        {
          stepId: '03',
          objective: 'Create project files (index.html, styles.css, app.tsx, README.md)',
          requiredCapability: 'web_development',
          specialistRole: 'Web Development Specialist',
          dependencies: ['02'],
          expectedOutput: '4 structured web project files written to workspace',
          verificationRequirement: 'Files present and populated',
          riskLevel: 'LOW',
          parameters: { target_files: ['index.html', 'styles.css', 'app.tsx', 'README.md'] },
        },
        {
          stepId: '04',
          objective: 'Validate generated project syntax and bundle integrity',
          requiredCapability: 'build_validation',
          specialistRole: 'Build & Test Specialist',
          dependencies: ['03'],
          expectedOutput: 'Build validation passes with 0 errors',
          verificationRequirement: 'Build exit code == 0',
          riskLevel: 'LOW',
          parameters: { validation_type: 'BUILD_AND_LINT' },
        },
        {
          stepId: '05',
          objective: 'Inspect empirical evidence and test outputs',
          requiredCapability: 'evidence_collection',
          specialistRole: 'Observation / QA',
          dependencies: ['04'],
          expectedOutput: 'Artifact SHA-256 and test report evidence collected',
          verificationRequirement: 'Evidence contains ARTIFACT and TEST entries',
          riskLevel: 'LOW',
          parameters: {},
        },
        {
          stepId: '06',
          objective: 'Verify all operational success criteria',
          requiredCapability: 'verification_evaluation',
          specialistRole: 'Master Orchestrator',
          dependencies: ['05'],
          expectedOutput: 'Verified status approved',
          verificationRequirement: '100% criteria passed',
          riskLevel: 'LOW',
          parameters: {},
        },
        {
          stepId: '07',
          objective: 'Record approved completion state in Company Obsidian memory',
          requiredCapability: 'memory_writeback',
          specialistRole: 'Memory Service',
          dependencies: ['06'],
          expectedOutput: 'Workflow record persisted to Obsidian vault',
          verificationRequirement: 'Obsidian document created with approval flag',
          riskLevel: 'LOW',
          parameters: { target_vault: 'company_knowledge/runs/' },
        },
      ],
    },
    knowledgeRetrieved: [mockObsidianKnowledge[0], mockObsidianKnowledge[1]],
    selectedSpecialists: {
      web_development: 'spec_web_dev_01',
      software_development: 'spec_software_dev_01',
      file_operations: 'spec_software_dev_01',
      build_validation: 'spec_build_test_01',
    },
    specialistExecutions: [
      {
        stepId: '01',
        objective: 'Retrieve approved company facts',
        requiredCapability: 'company_knowledge_retrieval',
        specialistId: 'knowledge_service',
        specialistName: 'Company Knowledge Service',
        status: 'COMPLETED',
        output: 'Retrieved 5 authoritative facts from Obsidian vault.',
        artifacts: [],
        evidenceIds: ['ev_src_01'],
        durationSeconds: 0.36,
      },
      {
        stepId: '02',
        objective: 'Create controlled workspace sandbox',
        requiredCapability: 'workspace_create',
        specialistId: 'spec_software_dev_01',
        specialistName: 'Software Development Specialist',
        status: 'COMPLETED',
        output: 'Initialized workspace "run-001" under controlled sandbox root.',
        artifacts: [],
        evidenceIds: ['ev_log_01'],
        durationSeconds: 0.42,
      },
      {
        stepId: '03',
        objective: 'Create project files in sandbox',
        requiredCapability: 'web_development',
        specialistId: 'spec_web_dev_01',
        specialistName: 'Web Development Specialist',
        status: 'COMPLETED',
        output: 'Synthesized index.html, styles.css, app.tsx, and README.md with verified company details.',
        artifacts: ['index.html', 'styles.css', 'app.tsx', 'README.md'],
        evidenceIds: ['ev_art_01', 'ev_art_02', 'ev_art_03'],
        durationSeconds: 2.15,
      },
      {
        stepId: '04',
        objective: 'Run controlled build and bundle validation',
        requiredCapability: 'build_validation',
        specialistId: 'spec_build_test_01',
        specialistName: 'Build & Test Specialist',
        status: 'COMPLETED',
        output: 'Build validation passed. 0 syntax errors, 4 tests passed.',
        artifacts: ['build_report.json'],
        evidenceIds: ['ev_test_01', 'ev_test_02'],
        durationSeconds: 0.94,
      },
    ],
    workspaceFiles: [
      {
        path: 'index.html',
        operation: 'CREATE',
        status: 'SUCCESS',
        sizeBytes: 1842,
        mimeType: 'text/html',
        modifiedAt: '2026-09-10T09:12:04Z',
        contentSnippet: `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>NovaPulse Robotics — Autonomous Warehouse Intelligence</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="hero">
    <h1>NovaPulse Robotics</h1>
    <p class="tagline">Autonomous warehouse robotics solutions</p>
  </header>
  <section class="services">
    <h2>Core Products</h2>
    <ul>
      <li>Fleet Orchestrator 4.0</li>
      <li>Autonomous AMR-500</li>
      <li>Cloud Telemetry API</li>
    </ul>
  </section>
  <footer class="contact">
    <p>Contact: <a href="mailto:contact@novapulse.io">contact@novapulse.io</a></p>
  </footer>
</body>
</html>`,
      },
      {
        path: 'styles.css',
        operation: 'CREATE',
        status: 'SUCCESS',
        sizeBytes: 940,
        mimeType: 'text/css',
        modifiedAt: '2026-09-10T09:12:05Z',
        contentSnippet: `:root {
  --bg: #0B0F19;
  --text: #F1F5F9;
  --primary: #4338CA;
  --accent: #06B6D4;
}
body {
  margin: 0;
  font-family: 'Inter', sans-serif;
  background: var(--bg);
  color: var(--text);
  padding: 2rem;
}`,
      },
      {
        path: 'app.tsx',
        operation: 'CREATE',
        status: 'SUCCESS',
        sizeBytes: 2150,
        mimeType: 'text/typescript-jsx',
        modifiedAt: '2026-09-10T09:12:05Z',
        contentSnippet: `import React from 'react';

export const LandingPage = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <h1 className="text-4xl font-bold">NovaPulse Robotics</h1>
      <p className="mt-2 text-slate-400">Autonomous warehouse robotics solutions</p>
    </div>
  );
};`,
      },
      {
        path: 'README.md',
        operation: 'CREATE',
        status: 'SUCCESS',
        sizeBytes: 420,
        mimeType: 'text/markdown',
        modifiedAt: '2026-09-10T09:12:06Z',
        contentSnippet: `# NovaPulse Robotics Landing Page
Generated autonomously by LM-Brain Workforce.
Source: Company Obsidian Vault (Authoritative)`,
      },
    ],
    validations: [
      {
        operation: 'BUILD',
        command: 'npm run build -- --production',
        status: 'PASSED',
        exitCode: 0,
        output: 'vite v8.2.2 building for production...\ntransforming...\n✓ 4 modules transformed.\ndist/index.html   0.92 kB\ndist/assets/index.js   14.20 kB\n✓ built in 142ms',
        restrictedShell: true,
      },
      {
        operation: 'TEST',
        command: 'npm run test -- --runInBand',
        status: 'PASSED',
        exitCode: 0,
        output: 'PASS src/__tests__/landing.test.tsx\n  ✓ renders company title (12ms)\n  ✓ includes all 3 core products (8ms)\n  ✓ includes valid contact email (4ms)\n  ✓ adheres to security CSP headers (6ms)\n\nTest Suites: 1 passed, 1 total\nTests: 4 passed, 4 total',
        restrictedShell: true,
      },
    ],
    evidenceItems: [
      {
        evidenceId: 'ev_art_01',
        category: 'ARTIFACT',
        timestamp: '2026-09-10T09:12:05Z',
        systemGenerated: true,
        description: 'Synthesized index.html landing page artifact',
      },
      {
        evidenceId: 'ev_art_02',
        category: 'ARTIFACT',
        timestamp: '2026-09-10T09:12:05Z',
        systemGenerated: true,
        description: 'Synthesized styles.css style bundle artifact',
      },
      {
        evidenceId: 'ev_test_01',
        category: 'TEST',
        timestamp: '2026-09-10T09:12:06Z',
        systemGenerated: true,
        description: 'Automated suite "landing.test.tsx" passed 4/4 tests',
      },
      {
        evidenceId: 'ev_ver_01',
        category: 'VERIFICATION',
        timestamp: '2026-09-10T09:12:07Z',
        systemGenerated: true,
        description: 'Empirical verification passed against all 7 success criteria',
      },
    ],
    verificationChecklist: [
      { criterion: 'Authoritative company information used', passed: true, details: 'Facts sourced from Obsidian company_profile.md' },
      { criterion: 'Required sections created (Header, Services, Contact)', passed: true, details: 'Verified in synthesized AST' },
      { criterion: 'Project files created in controlled workspace', passed: true, details: '4 files present in workspace run-001' },
      { criterion: 'Controlled build validation passed', passed: true, details: 'Exit code 0, 0 compilation warnings' },
      { criterion: 'Unit test suite passed', passed: true, details: '4/4 tests passed in restricted sandbox' },
      { criterion: 'Empirical evidence recorded', passed: true, details: 'Artifact and Test evidence items logged' },
      { criterion: 'Approved completion recorded in Obsidian memory', passed: true, details: 'Memory writeback marked APPROVED' },
    ],
    memoryWriteback: {
      status: 'COMPLETED',
      source: 'Company Obsidian',
      targetVaultPath: 'company_knowledge/runs/run_001_landing_page.md',
      recordedState: 'Landing page workflow verified and completed successfully with 4 files.',
      approvalStatus: 'APPROVED',
      factsPersisted: [
        { statement: 'Landing page created for NovaPulse Robotics in run-001', state: 'FACT', source: 'workflow:run-001' },
        { statement: 'Artifact SHA-256 and 4 unit tests verified', state: 'FACT', source: 'workflow:run-001' },
      ],
      timestamp: '2026-09-10T09:12:07Z',
    },
    recoveryHistory: [],
    auditEvents: mockAuditEvents,
  },
  {
    runId: 'RUN-002',
    requestId: 'req_cmo_campaign_02',
    userGoal: 'Create a complete marketing launch strategy for our new AMR-500 warehouse robot product line.',
    status: 'COMPLETED',
    durationSeconds: 28.4,
    isDemo: true,
    startedAt: '2026-09-10T08:45:10Z',
    completedAt: '2026-09-10T08:45:38Z',
    currentStageIndex: 9,
    stages: [
      { key: 'PERCEPTION', label: 'Perception', shortDescription: 'Strategic marketing requirement detected', status: 'COMPLETED', durationMs: 290, timestamp: '08:45:10' },
      { key: 'COMPANY_KNOWLEDGE', label: 'Company Knowledge', shortDescription: 'Retrieved product specs and brand standards from Obsidian', status: 'COMPLETED', durationMs: 410, timestamp: '08:45:11' },
      { key: 'REASONING', label: 'Reasoning', shortDescription: 'CMO Executive Twin activated for strategic campaign decomposition', status: 'COMPLETED', durationMs: 820, timestamp: '08:45:12' },
      { key: 'PLAN_VALIDATION', label: 'Plan Validation', shortDescription: 'Validated marketing plan & capability requirements', status: 'COMPLETED', durationMs: 160, timestamp: '08:45:12' },
      { key: 'CAPABILITY_SELECTION', label: 'Capability Selection', shortDescription: 'Selected Content, Poster, and Graphic Design specialists', status: 'COMPLETED', durationMs: 210, timestamp: '08:45:13' },
      { key: 'SPECIALIST_DELEGATION', label: 'Specialist Delegation', shortDescription: 'Delegated collateral synthesis across specialists', status: 'COMPLETED', durationMs: 250, timestamp: '08:45:13' },
      { key: 'CONTROLLED_EXECUTION', label: 'Controlled Execution', shortDescription: 'Executed failure recovery on initial asset format, then succeeded', status: 'COMPLETED', durationMs: 14200, timestamp: '08:45:27' },
      { key: 'OBSERVATION_QA', label: 'Observation / QA', shortDescription: 'Recorded marketing deck, poster vector, and copy artifacts', status: 'COMPLETED', durationMs: 890, timestamp: '08:45:28' },
      { key: 'VERIFICATION', label: 'Verification', shortDescription: 'CMO strategic review policy verified all collateral matches brand', status: 'COMPLETED', durationMs: 610, timestamp: '08:45:28' },
      { key: 'MEMORY_WRITEBACK', label: 'Memory Writeback', shortDescription: 'Persisted approved marketing campaign record to Obsidian', status: 'COMPLETED', durationMs: 480, timestamp: '08:45:29' },
    ],
    executiveTwinActivated: mockExecutiveTwins[3], // CMO Twin
    reasoningPlan: {
      planId: 'plan_cmo_campaign_02',
      goal: 'Formulate and synthesize AMR-500 launch campaign under CMO Twin direction',
      dependencies: [],
      successCriteria: [
        'CMO strategic review confirms brand alignment',
        'Executive pitch deck synthesized',
        'Technical whitepaper copy generated',
        'Marketing poster layout exported',
      ],
      assumptions: ['AMR-500 specifications in Obsidian are final'],
      requiredCapabilities: ['content_creation', 'poster_design', 'graphic_design', 'ppt'],
      confidence: 0.96,
      verificationRequirements: ['Brand tone guidelines met', 'All collateral produced'],
      steps: [
        {
          stepId: '01',
          objective: 'CMO Strategic Analysis & Audience Positioning',
          requiredCapability: 'strategic_analysis',
          specialistRole: 'CMO Executive Twin',
          dependencies: [],
          expectedOutput: 'Target audience profiles and value proposition matrices',
          verificationRequirement: 'Strategic decomposition signed off',
          riskLevel: 'LOW',
          parameters: {},
        },
        {
          stepId: '02',
          objective: 'Synthesize Launch Announcement & Product Narrative',
          requiredCapability: 'content_creation',
          specialistRole: 'Content Creation Specialist',
          dependencies: ['01'],
          expectedOutput: 'Press release and product launch narrative',
          verificationRequirement: 'Tone adheres to Obsidian brand guide',
          riskLevel: 'LOW',
          parameters: {},
        },
      ],
    },
    knowledgeRetrieved: [mockObsidianKnowledge[0], mockObsidianKnowledge[1]],
    selectedSpecialists: {
      content_creation: 'spec_content_01',
      poster_design: 'spec_poster_01',
      graphic_design: 'spec_graphic_design_01',
      ppt: 'spec_ppt_01',
    },
    specialistExecutions: [],
    workspaceFiles: [
      { path: 'AMR500_Launch_Strategy.md', operation: 'CREATE', status: 'SUCCESS', sizeBytes: 3120, mimeType: 'text/markdown' },
      { path: 'Press_Release.md', operation: 'CREATE', status: 'SUCCESS', sizeBytes: 1540, mimeType: 'text/markdown' },
      { path: 'Poster_Composition.svg', operation: 'CREATE', status: 'SUCCESS', sizeBytes: 8400, mimeType: 'image/svg+xml' },
    ],
    validations: [
      {
        operation: 'LINT',
        command: 'lint-markdown *.md',
        status: 'PASSED',
        exitCode: 0,
        output: 'All markdown files adhere to corporate terminology guidelines.',
        restrictedShell: true,
      },
    ],
    evidenceItems: [
      { evidenceId: 'ev_cmo_01', category: 'ARTIFACT', timestamp: '2026-09-10T08:45:25Z', systemGenerated: true, description: 'AMR500_Launch_Strategy.md document' },
      { evidenceId: 'ev_cmo_02', category: 'VERIFICATION', timestamp: '2026-09-10T08:45:28Z', systemGenerated: true, description: 'CMO Strategic review passed with 100% brand conformity' },
    ],
    verificationChecklist: [
      { criterion: 'CMO strategic review completed', passed: true, details: 'Executive Twin review outcome: APPROVED' },
      { criterion: 'Brand standards adherence', passed: true, details: 'Checked against doc_branding_guidelines' },
      { criterion: 'Campaign collateral generated', passed: true, details: '3 artifacts in workspace' },
      { criterion: 'Memory writeback recorded', passed: true, details: 'Persisted to Obsidian vault' },
    ],
    memoryWriteback: {
      status: 'COMPLETED',
      source: 'Company Obsidian',
      targetVaultPath: 'company_knowledge/campaigns/amr500_launch.md',
      recordedState: 'AMR-500 launch campaign strategy approved by CMO Twin and recorded in Obsidian.',
      approvalStatus: 'APPROVED',
      factsPersisted: [
        { statement: 'AMR-500 launch campaign collateral finalized', state: 'FACT', source: 'workflow:run-002' },
      ],
      timestamp: '2026-09-10T08:45:29Z',
    },
    recoveryHistory: [
      {
        attempt: 1,
        maxAttempts: 3,
        triggerError: 'Poster layout format error on initial canvas render',
        failureObserved: 'Canvas resolution mismatch in template layout',
        diagnosis: 'Adjusted dimensions to 1920x1080 standard vector spec and re-ran specialist delegation.',
        replannedGoal: 'Regenerate poster layout with bounded vector coordinates',
        replanStepCount: 2,
        status: 'RECOVERED',
      },
    ],
    auditEvents: [],
  },
  {
    runId: 'RUN-003',
    requestId: 'req_bounded_fail_03',
    userGoal: 'Execute migration against unverified external legacy database with unknown schema.',
    status: 'FAILED',
    durationSeconds: 19.8,
    isDemo: true,
    startedAt: '2026-09-10T07:20:00Z',
    completedAt: '2026-09-10T07:20:20Z',
    currentStageIndex: 6,
    stages: [
      { key: 'PERCEPTION', label: 'Perception', shortDescription: 'Parsed database migration objective', status: 'COMPLETED', durationMs: 210, timestamp: '07:20:00' },
      { key: 'COMPANY_KNOWLEDGE', label: 'Company Knowledge', shortDescription: 'No schema documentation found in Obsidian', status: 'COMPLETED', durationMs: 380, timestamp: '07:20:00' },
      { key: 'REASONING', label: 'Reasoning', shortDescription: 'Formulated exploratory database inspection plan', status: 'COMPLETED', durationMs: 450, timestamp: '07:20:01' },
      { key: 'PLAN_VALIDATION', label: 'Plan Validation', shortDescription: 'Plan validated with elevated risk warning', status: 'COMPLETED', durationMs: 140, timestamp: '07:20:01' },
      { key: 'CAPABILITY_SELECTION', label: 'Capability Selection', shortDescription: 'Selected software development specialist', status: 'COMPLETED', durationMs: 190, timestamp: '07:20:01' },
      { key: 'SPECIALIST_DELEGATION', label: 'Specialist Delegation', shortDescription: 'Delegated schema connection', status: 'COMPLETED', durationMs: 180, timestamp: '07:20:01' },
      { key: 'CONTROLLED_EXECUTION', label: 'Controlled Execution', shortDescription: 'Repeated connection failures exhausted maximum recovery bounds (3/3)', status: 'FAILED', durationMs: 18400, timestamp: '07:20:20' },
      { key: 'OBSERVATION_QA', label: 'Observation / QA', shortDescription: 'Failure evidence captured', status: 'SKIPPED' },
      { key: 'VERIFICATION', label: 'Verification', shortDescription: 'Verification blocked due to unrecovered execution failure', status: 'BLOCKED' },
      { key: 'MEMORY_WRITEBACK', label: 'Memory Writeback', shortDescription: 'NOT PERFORMED — unverified failure state prevented from polluting Obsidian', status: 'SKIPPED' },
    ],
    reasoningPlan: {
      planId: 'plan_migration_fail_03',
      goal: 'Attempt legacy database inspection and schema extraction',
      dependencies: [],
      successCriteria: ['Schema extracted and validated'],
      assumptions: [],
      requiredCapabilities: ['software_development', 'file_operations'],
      confidence: 0.45,
      verificationRequirements: ['Schema verification exit code == 0'],
      steps: [
        {
          stepId: '01',
          objective: 'Attempt connect to unverified legacy schema',
          requiredCapability: 'software_development',
          specialistRole: 'Software Development Specialist',
          dependencies: [],
          expectedOutput: 'Schema dump',
          verificationRequirement: 'Connection established',
          riskLevel: 'HIGH',
          parameters: {},
        },
      ],
    },
    knowledgeRetrieved: [],
    selectedSpecialists: { software_development: 'spec_software_dev_01' },
    specialistExecutions: [
      {
        stepId: '01',
        objective: 'Connect to unverified legacy schema',
        requiredCapability: 'software_development',
        specialistId: 'spec_software_dev_01',
        specialistName: 'Software Development Specialist',
        status: 'FAILED',
        output: 'Connection timeout. Target host unreachable.',
        error: 'CONNECTION_REFUSED: Host unreachable at target endpoint',
        artifacts: [],
        evidenceIds: [],
        durationSeconds: 5.0,
      },
    ],
    workspaceFiles: [],
    validations: [
      {
        operation: 'TEST',
        command: 'ping-db-host',
        status: 'FAILED',
        exitCode: 1,
        output: 'ERROR: Connection timeout after 5000ms. Host unreachable.',
        restrictedShell: true,
      },
    ],
    evidenceItems: [
      {
        evidenceId: 'ev_err_01',
        category: 'EXECUTION_LOG',
        timestamp: '2026-09-10T07:20:18Z',
        systemGenerated: true,
        description: 'Repeated connection failure log recorded across 3 attempts',
      },
    ],
    verificationChecklist: [
      { criterion: 'Connection established', passed: false, details: 'Host unreachable' },
      { criterion: 'Schema extracted', passed: false, details: 'Step failed' },
      { criterion: 'Verification criteria passed', passed: false, details: 'Workflow halted' },
    ],
    memoryWriteback: {
      status: 'NOT_PERFORMED',
      source: 'Company Obsidian',
      targetVaultPath: 'company_knowledge/',
      recordedState: 'Unverified failure state blocked from Obsidian vault writeback.',
      approvalStatus: 'NOT_APPLICABLE',
      factsPersisted: [],
      reason: 'Workflow not verified — Authoritative Obsidian memory integrity protected.',
      timestamp: '2026-09-10T07:20:20Z',
    },
    recoveryHistory: [
      {
        attempt: 1,
        maxAttempts: 3,
        triggerError: 'Connection timeout to database endpoint',
        failureObserved: 'Socket connection failed on port 5432',
        diagnosis: 'Attempting retry with fallback protocol adapter.',
        replannedGoal: 'Retry connection with fallback adapter',
        replanStepCount: 1,
        status: 'IN_PROGRESS',
      },
      {
        attempt: 2,
        maxAttempts: 3,
        triggerError: 'Fallback protocol connection failed',
        failureObserved: 'Host route unreachable',
        diagnosis: 'Diagnostic ping failed. Attempting final bounded recovery check.',
        replannedGoal: 'Verify network gateway route',
        replanStepCount: 1,
        status: 'IN_PROGRESS',
      },
      {
        attempt: 3,
        maxAttempts: 3,
        triggerError: 'Gateway route unreachable',
        failureObserved: 'Maximum recovery attempts reached (3/3)',
        diagnosis: 'Max bounded recovery budget exhausted. Clean termination enforced. No infinite loops.',
        replannedGoal: 'Halt workflow cleanly and generate failure evidence',
        replanStepCount: 0,
        status: 'EXHAUSTED',
      },
    ],
    auditEvents: [],
  },
];
