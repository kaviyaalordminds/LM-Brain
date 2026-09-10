import {
  AuditEvent,
  ObsidianDocument,
  OrchestrationStatus,
  ReasoningPlan,
  RecoveryEvent,
  StageStatus,
  TypedEvidence,
  ValidationRecord,
  WorkflowRun,
  WorkflowStage,
  WorkspaceFile,
} from '../types';
import { mockObsidianKnowledge } from './knowledgeData';
import { mockExecutiveTwins } from './specialistsData';

export interface SimulationUpdateCallback {
  (run: WorkflowRun): void;
}

export class LiveRunSimulator {
  private run: WorkflowRun;
  private onUpdate: SimulationUpdateCallback;
  private isCancelled: boolean = false;
  private timeoutId: any = null;
  private stepMode: boolean = false;
  private waitingForStepResolver: (() => void) | null = null;

  constructor(initialRun: WorkflowRun, onUpdate: SimulationUpdateCallback) {
    this.run = JSON.parse(JSON.stringify(initialRun));
    this.onUpdate = onUpdate;
  }

  public cancel(): void {
    this.isCancelled = true;
    if (this.timeoutId) clearTimeout(this.timeoutId);
    if (this.waitingForStepResolver) {
      this.waitingForStepResolver();
      this.waitingForStepResolver = null;
    }
  }

  public setStepMode(enabled: boolean): void {
    this.stepMode = enabled;
  }

  public nextStep(): void {
    if (this.waitingForStepResolver) {
      this.waitingForStepResolver();
      this.waitingForStepResolver = null;
    }
  }

  private async delay(ms: number): Promise<void> {
    if (this.isCancelled) return;
    if (this.stepMode) {
      await new Promise<void>((resolve) => {
        this.waitingForStepResolver = resolve;
      });
      return;
    }
    return new Promise((resolve) => {
      this.timeoutId = setTimeout(resolve, ms);
    });
  }

  private emitUpdate(): void {
    if (!this.isCancelled) {
      this.onUpdate(JSON.parse(JSON.stringify(this.run)));
    }
  }

  private addAuditEvent(eventType: string, payload: Record<string, any>): void {
    const event: AuditEvent = {
      eventId: `evt_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
      eventType,
      timestamp: new Date().toISOString(),
      payload,
    };
    this.run.auditEvents.push(event);
  }

  private updateStage(
    index: number,
    status: StageStatus,
    shortDescription?: string,
    durationMs?: number
  ): void {
    if (this.run.stages[index]) {
      this.run.stages[index].status = status;
      this.run.stages[index].timestamp = new Date().toLocaleTimeString();
      if (shortDescription) this.run.stages[index].shortDescription = shortDescription;
      if (durationMs) this.run.stages[index].durationMs = durationMs;
      this.run.currentStageIndex = index;
    }
  }

  public async startSimulation(
    type: 'STANDARD' | 'CONTROLLED_FAILURE' | 'BOUNDED_FAILURE' | 'STRATEGIC_TWIN'
  ): Promise<void> {
    this.run.startedAt = new Date().toISOString();
    this.run.status = 'PERCEIVING';
    this.addAuditEvent('ORCHESTRATION_STARTED', {
      requestId: this.run.requestId,
      userGoal: this.run.userGoal,
      simulationType: type,
    });
    this.emitUpdate();

    // 1. Stage 0: PERCEPTION
    this.updateStage(0, 'RUNNING', 'Parsing requirement and normalizing intent...');
    this.emitUpdate();
    await this.delay(700);
    if (this.isCancelled) return;

    if (type === 'STRATEGIC_TWIN') {
      this.run.executiveTwinActivated = mockExecutiveTwins[3]; // CMO
      this.updateStage(0, 'COMPLETED', 'Marketing launch requirement identified. Strategic Twin required.', 700);
      this.addAuditEvent('PERCEPTION_COMPLETED', {
        identifiedIntent: 'MARKETING_LAUNCH',
        requiresExecutiveTwin: true,
        twinRole: 'CMO',
      });
    } else {
      this.updateStage(0, 'COMPLETED', 'Goal parsed: Landing page synthesis using approved facts.', 700);
      this.addAuditEvent('PERCEPTION_COMPLETED', {
        identifiedIntent: 'SOFTWARE_WEB_SYNTHESIS',
        requiresExecutiveTwin: false,
      });
    }
    this.emitUpdate();

    // 2. Stage 1: COMPANY KNOWLEDGE
    this.run.status = 'PLANNING';
    this.updateStage(1, 'RUNNING', 'Querying Company Obsidian vault for authoritative profile...');
    this.emitUpdate();
    await this.delay(800);
    if (this.isCancelled) return;

    this.run.knowledgeRetrieved = [mockObsidianKnowledge[0], mockObsidianKnowledge[1]];
    this.updateStage(1, 'COMPLETED', 'Retrieved 5 verified facts from authoritative Obsidian vault.', 800);
    this.addAuditEvent('KNOWLEDGE_RETRIEVED', {
      source: 'Company Obsidian',
      vaultPath: 'company_knowledge/default/company_profile.md',
      authority: 'AUTHORITATIVE',
      factsCount: 5,
    });
    this.emitUpdate();

    // 3. Stage 2: REASONING (No CoT exposed!)
    this.updateStage(2, 'RUNNING', 'Synthesizing structured declarative plan...');
    this.emitUpdate();
    await this.delay(900);
    if (this.isCancelled) return;

    const plan: ReasoningPlan = {
      planId: `plan_${Date.now()}`,
      goal: this.run.userGoal,
      dependencies: [],
      successCriteria: [
        'index.html created with authoritative company information',
        'styles.css generated with brand color token palette',
        'app.tsx created with responsive service catalog',
        'Controlled build validation succeeds with exit code 0',
        'Empirical verification matches all success criteria',
      ],
      assumptions: ['Company Obsidian profile is authoritative'],
      requiredCapabilities: ['web_development', 'software_development', 'file_operations', 'build_validation'],
      confidence: 0.98,
      verificationRequirements: ['All files exist in sandbox', 'Build validation exit code 0'],
      steps: [
        {
          stepId: '01',
          objective: 'Retrieve approved company information',
          requiredCapability: 'company_knowledge_retrieval',
          specialistRole: 'Knowledge Service',
          dependencies: [],
          expectedOutput: 'Approved company facts',
          verificationRequirement: 'Facts verified from Obsidian',
          riskLevel: 'LOW',
          parameters: {},
        },
        {
          stepId: '02',
          objective: 'Create controlled workspace',
          requiredCapability: 'workspace_create',
          specialistRole: 'Software Development Specialist',
          dependencies: ['01'],
          expectedOutput: 'Workspace initialized',
          verificationRequirement: 'Sandbox path bounded',
          riskLevel: 'LOW',
          parameters: { workspace_id: 'run-001' },
        },
        {
          stepId: '03',
          objective: 'Create project files',
          requiredCapability: 'web_development',
          specialistRole: 'Web Development Specialist',
          dependencies: ['02'],
          expectedOutput: 'index.html, styles.css, app.tsx written',
          verificationRequirement: 'Files present in sandbox',
          riskLevel: 'LOW',
          parameters: { files: ['index.html', 'styles.css', 'app.tsx', 'README.md'] },
        },
        {
          stepId: '04',
          objective: 'Validate project',
          requiredCapability: 'build_validation',
          specialistRole: 'Build & Test Specialist',
          dependencies: ['03'],
          expectedOutput: 'Build exit code 0',
          verificationRequirement: 'Build passes with 0 errors',
          riskLevel: 'LOW',
          parameters: {},
        },
        {
          stepId: '05',
          objective: 'Inspect evidence',
          requiredCapability: 'evidence_collection',
          specialistRole: 'Observation / QA',
          dependencies: ['04'],
          expectedOutput: 'Artifact hashes & test reports logged',
          verificationRequirement: 'Evidence set non-empty',
          riskLevel: 'LOW',
          parameters: {},
        },
        {
          stepId: '06',
          objective: 'Verify success criteria',
          requiredCapability: 'verification_evaluation',
          specialistRole: 'Master Orchestrator',
          dependencies: ['05'],
          expectedOutput: 'Verification approved',
          verificationRequirement: '100% criteria passed',
          riskLevel: 'LOW',
          parameters: {},
        },
        {
          stepId: '07',
          objective: 'Record approved completion',
          requiredCapability: 'memory_writeback',
          specialistRole: 'Memory Service',
          dependencies: ['06'],
          expectedOutput: 'Persisted to Obsidian',
          verificationRequirement: 'Obsidian writeback complete',
          riskLevel: 'LOW',
          parameters: {},
        },
      ],
    };

    this.run.reasoningPlan = plan;
    this.updateStage(2, 'COMPLETED', 'Structured 7-step plan generated with mode DEVELOP.', 900);
    this.addAuditEvent('REASONING_COMPLETED', {
      planId: plan.planId,
      stepCount: plan.steps.length,
      mode: 'DEVELOP',
      confidence: 0.98,
    });
    this.emitUpdate();

    // 4. Stage 3: PLAN VALIDATION
    this.run.status = 'VALIDATING';
    this.updateStage(3, 'RUNNING', 'Validating plan schema, security boundaries & capabilities...');
    this.emitUpdate();
    await this.delay(600);
    if (this.isCancelled) return;

    this.updateStage(3, 'COMPLETED', 'Plan validated against StrictBoundsValidator (0 cycles, bounds ok).', 600);
    this.addAuditEvent('PLAN_VALIDATED', { status: 'PASSED', boundsChecked: true });
    this.emitUpdate();

    // 5. Stage 4: CAPABILITY SELECTION
    this.run.status = 'SELECTING_CAPABILITIES';
    this.updateStage(4, 'RUNNING', 'Querying specialist registry for required capabilities...');
    this.emitUpdate();
    await this.delay(650);
    if (this.isCancelled) return;

    this.run.selectedSpecialists = {
      web_development: 'spec_web_dev_01',
      software_development: 'spec_software_dev_01',
      file_operations: 'spec_software_dev_01',
      build_validation: 'spec_build_test_01',
    };
    this.updateStage(4, 'COMPLETED', 'Registry matched 4 active specialists for capabilities.', 650);
    this.addAuditEvent('CAPABILITY_SELECTED', {
      matches: this.run.selectedSpecialists,
      registryStatus: 'ACTIVE',
    });
    this.emitUpdate();

    // 6. Stage 5: SPECIALIST DELEGATION
    this.updateStage(5, 'RUNNING', 'Delegating subtasks to specialist execution engines...');
    this.emitUpdate();
    await this.delay(600);
    if (this.isCancelled) return;

    this.updateStage(5, 'COMPLETED', 'Subtasks delegated. SecurityGuard boundaries verified.', 600);
    this.addAuditEvent('SPECIALIST_DELEGATED', {
      delegates: ['spec_web_dev_01', 'spec_software_dev_01', 'spec_build_test_01'],
      securityGuardActive: true,
    });
    this.emitUpdate();

    // 7. Stage 6: CONTROLLED EXECUTION
    this.run.status = 'EXECUTING';
    this.updateStage(6, 'RUNNING', 'Executing sandboxed file operations via SecurityGuard...');
    this.emitUpdate();

    if (type === 'CONTROLLED_FAILURE') {
      // Simulate Controlled Failure & Recovery Demo Flow
      await this.delay(1000);
      if (this.isCancelled) return;

      this.run.validations.push({
        operation: 'BUILD',
        command: 'npm run build',
        status: 'FAILED',
        exitCode: 1,
        output: 'ERROR: Path traversal violation detected: attempted write outside sandbox root ("../../../etc/hosts").',
        restrictedShell: true,
      });
      this.updateStage(6, 'FAILED', 'Build validation failed: Path traversal blocked by SecurityGuard.', 1000);
      this.addAuditEvent('EXECUTION_FAILED', {
        error: 'SecurityGuard blocked path traversal attempt',
        exitCode: 1,
      });
      this.emitUpdate();

      // RECOVERY SUB-FLOW
      this.run.status = 'RECOVERING';
      this.updateStage(6, 'RECOVERING', 'Observation recorded failure evidence. Diagnosing root cause...');
      this.emitUpdate();
      await this.delay(1200);
      if (this.isCancelled) return;

      const recoveryEvent: RecoveryEvent = {
        attempt: 1,
        maxAttempts: 3,
        triggerError: 'Path traversal blocked outside workspace bounds',
        failureObserved: 'Controlled command executor rejected invalid path',
        diagnosis: 'Reasoning diagnosed path error. Re-planning bounded to workspace-relative path "./index.html".',
        replannedGoal: 'Synthesize files strictly inside workspace sandbox',
        replanStepCount: 3,
        status: 'IN_PROGRESS',
      };
      this.run.recoveryHistory.push(recoveryEvent);
      this.addAuditEvent('RECOVERY_STARTED', { attempt: 1, maxAttempts: 3 });
      this.addAuditEvent('REPLAN_GENERATED', { diagnosis: recoveryEvent.diagnosis });
      this.emitUpdate();

      // Retry execution with corrected plan
      this.run.status = 'REPLANNING';
      await this.delay(1000);
      if (this.isCancelled) return;

      this.run.status = 'EXECUTING';
      this.updateStage(6, 'RUNNING', 'Retrying execution with corrected bounded plan (Attempt 1/3)...');
      this.emitUpdate();
      await this.delay(1200);
      if (this.isCancelled) return;

      recoveryEvent.status = 'RECOVERED';
      this.populateSuccessFiles();
      this.updateStage(6, 'COMPLETED', 'Execution recovered and completed successfully on Retry 1.', 1200);
      this.emitUpdate();
    } else if (type === 'BOUNDED_FAILURE') {
      // Simulate Repeated Bounded Failure Exhaustion
      for (let attempt = 1; attempt <= 3; attempt++) {
        await this.delay(900);
        if (this.isCancelled) return;

        this.run.validations.push({
          operation: 'TEST',
          command: `probe-network-endpoint --attempt=${attempt}`,
          status: 'FAILED',
          exitCode: 1,
          output: `Attempt ${attempt} FAILED: Remote database endpoint unreachable (Timeout 5000ms).`,
          restrictedShell: true,
        });

        const recEv: RecoveryEvent = {
          attempt,
          maxAttempts: 3,
          triggerError: `Connection timeout on attempt ${attempt}`,
          failureObserved: `Host unreachable on port 5432`,
          diagnosis: attempt < 3 ? `Attempting recovery retry ${attempt + 1}/3...` : 'Maximum recovery attempts reached. Terminating execution cleanly.',
          replannedGoal: 'Retry endpoint probe with fallback adapter',
          replanStepCount: 1,
          status: attempt < 3 ? 'IN_PROGRESS' : 'EXHAUSTED',
        };
        this.run.recoveryHistory.push(recEv);
        this.addAuditEvent('RECOVERY_STARTED', { attempt, maxAttempts: 3 });
        this.emitUpdate();
      }

      this.run.status = 'FAILED';
      this.updateStage(6, 'FAILED', 'Maximum recovery attempts reached (3/3). Bounded termination enforced.', 2700);
      this.updateStage(7, 'SKIPPED', 'Observation skipped due to unrecovered failure.');
      this.updateStage(8, 'BLOCKED', 'Verification blocked.');
      this.updateStage(9, 'SKIPPED', 'Memory writeback blocked — unverified state protected.');
      this.run.memoryWriteback = {
        status: 'NOT_PERFORMED',
        source: 'Company Obsidian',
        targetVaultPath: 'company_knowledge/',
        recordedState: 'Unverified workflow state blocked from Obsidian vault writeback.',
        approvalStatus: 'NOT_APPLICABLE',
        factsPersisted: [],
        reason: 'Workflow not verified — Authoritative Obsidian memory integrity protected.',
        timestamp: new Date().toISOString(),
      };
      this.emitUpdate();
      return;
    } else {
      // STANDARD / STRATEGIC_TWIN
      await this.delay(1200);
      if (this.isCancelled) return;

      this.populateSuccessFiles();
      this.updateStage(6, 'COMPLETED', 'Created 4 project files and validated build in sandbox.', 1200);
      this.addAuditEvent('EXECUTION_COMPLETED', { filesCreated: 4, workspace: 'run-001' });
      this.emitUpdate();
    }

    // 8. Stage 7: OBSERVATION / QA
    this.run.status = 'OBSERVING';
    this.updateStage(7, 'RUNNING', 'Collecting empirical evidence, test reports, and artifact checksums...');
    this.emitUpdate();
    await this.delay(800);
    if (this.isCancelled) return;

    this.run.evidenceItems = [
      {
        evidenceId: `ev_art_${Date.now()}`,
        category: 'ARTIFACT',
        timestamp: new Date().toISOString(),
        systemGenerated: true,
        description: 'Synthesized index.html, styles.css, app.tsx, README.md artifacts',
      },
      {
        evidenceId: `ev_test_${Date.now()}`,
        category: 'TEST',
        timestamp: new Date().toISOString(),
        systemGenerated: true,
        description: 'Automated test suite passed 4/4 verification assertions',
      },
      {
        evidenceId: `ev_ver_${Date.now()}`,
        category: 'VERIFICATION',
        timestamp: new Date().toISOString(),
        systemGenerated: true,
        description: 'All 7 acceptance criteria empirically validated',
      },
    ];
    this.updateStage(7, 'COMPLETED', '3 empirical evidence items captured (Artifact, Test, Verification).', 800);
    this.addAuditEvent('OBSERVATION_RECORDED', { evidenceCount: 3 });
    this.emitUpdate();

    // 9. Stage 8: VERIFICATION
    this.run.status = 'VERIFYING';
    this.updateStage(8, 'RUNNING', 'Evaluating success criteria checklist against evidence...');
    this.emitUpdate();
    await this.delay(750);
    if (this.isCancelled) return;

    this.run.verificationChecklist = [
      { criterion: 'Authoritative company information used', passed: true, details: 'Verified from Obsidian facts' },
      { criterion: 'Required sections created (Header, Services, Contact)', passed: true, details: 'Verified in AST' },
      { criterion: 'Project files created in controlled workspace', passed: true, details: '4 files present' },
      { criterion: 'Controlled build validation passed', passed: true, details: 'Exit code 0' },
      { criterion: 'Unit test suite passed', passed: true, details: '4/4 tests passed' },
      { criterion: 'Empirical evidence recorded', passed: true, details: 'Hashes logged' },
      { criterion: 'Approved completion recorded in Obsidian memory', passed: true, details: 'Approval verified' },
    ];
    this.updateStage(8, 'COMPLETED', 'Verification PASSED (7/7 criteria verified).', 750);
    this.addAuditEvent('VERIFICATION_COMPLETED', { status: 'VERIFIED', criteriaCount: 7 });
    this.emitUpdate();

    // 10. Stage 9: MEMORY WRITEBACK
    this.updateStage(9, 'RUNNING', 'Persisting verified outcome to authoritative Company Obsidian...');
    this.emitUpdate();
    await this.delay(700);
    if (this.isCancelled) return;

    this.run.memoryWriteback = {
      status: 'COMPLETED',
      source: 'Company Obsidian',
      targetVaultPath: `company_knowledge/runs/${this.run.runId.toLowerCase()}_summary.md`,
      recordedState: 'Landing page workflow verified and completed successfully with 4 files.',
      approvalStatus: 'APPROVED',
      factsPersisted: [
        { statement: 'Landing page synthesized for NovaPulse Robotics', state: 'FACT', source: `workflow:${this.run.runId}` },
        { statement: 'Artifact SHA-256 and 4 unit tests verified', state: 'FACT', source: `workflow:${this.run.runId}` },
      ],
      timestamp: new Date().toISOString(),
    };
    this.updateStage(9, 'COMPLETED', 'Writeback complete: state recorded to Company Obsidian vault.', 700);
    this.addAuditEvent('MEMORY_WRITEBACK_COMPLETED', {
      vaultPath: this.run.memoryWriteback.targetVaultPath,
      status: 'APPROVED',
    });
    this.emitUpdate();

    // FINISH
    this.run.status = 'COMPLETED';
    this.run.completedAt = new Date().toISOString();
    this.run.durationSeconds = Math.round((new Date(this.run.completedAt).getTime() - new Date(this.run.startedAt).getTime()) / 100) / 10;
    this.addAuditEvent('ORCHESTRATION_COMPLETED', {
      finalStatus: 'COMPLETED',
      durationSeconds: this.run.durationSeconds,
    });
    this.emitUpdate();
  }

  private populateSuccessFiles(): void {
    this.run.workspaceFiles = [
      {
        path: 'index.html',
        operation: 'CREATE',
        status: 'SUCCESS',
        sizeBytes: 1842,
        mimeType: 'text/html',
        modifiedAt: new Date().toLocaleTimeString(),
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
        modifiedAt: new Date().toLocaleTimeString(),
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
        modifiedAt: new Date().toLocaleTimeString(),
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
        modifiedAt: new Date().toLocaleTimeString(),
        contentSnippet: `# NovaPulse Robotics Landing Page
Generated autonomously by LM-Brain Workforce.
Source: Company Obsidian Vault (Authoritative)`,
      },
    ];

    this.run.validations = [
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
    ];

    this.run.specialistExecutions = [
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
    ];
  }
}
