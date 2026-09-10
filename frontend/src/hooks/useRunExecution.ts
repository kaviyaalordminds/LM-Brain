import { useCallback, useEffect, useRef, useState } from 'react';
import { LiveRunSimulator, mockRuns } from '../mock';
import { WorkflowRun, WorkRequest } from '../types';

export function useRunExecution(initialRunId?: string) {
  const [currentRun, setCurrentRun] = useState<WorkflowRun>(() => {
    if (initialRunId) {
      const found = mockRuns.find(r => r.runId === initialRunId);
      if (found) return JSON.parse(JSON.stringify(found));
    }
    return JSON.parse(JSON.stringify(mockRuns[0]));
  });

  const [isExecuting, setIsExecuting] = useState(false);
  const [selectedStageIndex, setSelectedStageIndex] = useState<number>(0);
  const simulatorRef = useRef<LiveRunSimulator | null>(null);

  const startRun = useCallback(
    async (
      request: WorkRequest,
      simulationType: 'STANDARD' | 'CONTROLLED_FAILURE' | 'BOUNDED_FAILURE' | 'STRATEGIC_TWIN' = 'STANDARD'
    ) => {
      if (simulatorRef.current) {
        simulatorRef.current.cancel();
      }

      const runTemplate: WorkflowRun = {
        runId: `RUN-00${Math.floor(Math.random() * 900) + 100}`,
        requestId: request.requestId || `req_${Date.now()}`,
        userGoal: request.userGoal,
        status: 'RECEIVED',
        durationSeconds: 0,
        isDemo: true,
        startedAt: new Date().toISOString(),
        currentStageIndex: 0,
        stages: [
          { key: 'PERCEPTION', label: 'Perception', shortDescription: 'Waiting for normalization...', status: 'WAITING' },
          { key: 'COMPANY_KNOWLEDGE', label: 'Company Knowledge', shortDescription: 'Obsidian retrieval pending...', status: 'WAITING' },
          { key: 'REASONING', label: 'Reasoning', shortDescription: 'Structured planning pending...', status: 'WAITING' },
          { key: 'PLAN_VALIDATION', label: 'Plan Validation', shortDescription: 'Bounds check pending...', status: 'WAITING' },
          { key: 'CAPABILITY_SELECTION', label: 'Capability Selection', shortDescription: 'Registry matching pending...', status: 'WAITING' },
          { key: 'SPECIALIST_DELEGATION', label: 'Specialist Delegation', shortDescription: 'SecurityGuard allocation pending...', status: 'WAITING' },
          { key: 'CONTROLLED_EXECUTION', label: 'Controlled Execution', shortDescription: 'Sandboxed execution pending...', status: 'WAITING' },
          { key: 'OBSERVATION_QA', label: 'Observation / QA', shortDescription: 'Evidence capture pending...', status: 'WAITING' },
          { key: 'VERIFICATION', label: 'Verification', shortDescription: 'Success assertion pending...', status: 'WAITING' },
          { key: 'MEMORY_WRITEBACK', label: 'Memory Writeback', shortDescription: 'Obsidian writeback pending...', status: 'WAITING' },
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

      setCurrentRun(runTemplate);
      setIsExecuting(true);

      const simulator = new LiveRunSimulator(runTemplate, (updatedRun) => {
        setCurrentRun(updatedRun);
        setSelectedStageIndex(updatedRun.currentStageIndex);
        if (['COMPLETED', 'FAILED', 'BLOCKED'].includes(updatedRun.status)) {
          setIsExecuting(false);
        }
      });

      simulatorRef.current = simulator;
      await simulator.startSimulation(simulationType);
    },
    []
  );

  const loadRun = useCallback((run: WorkflowRun) => {
    if (simulatorRef.current) {
      simulatorRef.current.cancel();
    }
    setIsExecuting(false);
    setCurrentRun(JSON.parse(JSON.stringify(run)));
    setSelectedStageIndex(run.currentStageIndex || 0);
  }, []);

  const triggerControlledFailure = useCallback(() => {
    if (!currentRun) return;
    startRun(
      {
        requestId: `req_fail_${Date.now()}`,
        userGoal: currentRun.userGoal,
        requireMemoryWriteback: true,
        requireTwinEvaluation: false,
        availableCapabilities: ['web_development', 'file_operations'],
      },
      'CONTROLLED_FAILURE'
    );
  }, [currentRun, startRun]);

  const triggerRepeatedFailure = useCallback(() => {
    if (!currentRun) return;
    startRun(
      {
        requestId: `req_exhaust_${Date.now()}`,
        userGoal: 'Execute unverified database schema migration against unreachable endpoint',
        requireMemoryWriteback: true,
        requireTwinEvaluation: false,
        availableCapabilities: ['software_development'],
      },
      'BOUNDED_FAILURE'
    );
  }, [currentRun, startRun]);

  useEffect(() => {
    return () => {
      if (simulatorRef.current) {
        simulatorRef.current.cancel();
      }
    };
  }, []);

  return {
    currentRun,
    isExecuting,
    selectedStageIndex,
    setSelectedStageIndex,
    startRun,
    loadRun,
    triggerControlledFailure,
    triggerRepeatedFailure,
  };
}
