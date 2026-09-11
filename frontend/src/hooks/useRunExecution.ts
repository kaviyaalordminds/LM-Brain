import { useCallback, useEffect, useRef, useState } from 'react';
import { localWorkforceApi } from '../api/workforceApi';
import { LiveRunSimulator, mockRuns } from '../mock';
import { WorkflowRun, WorkRequest } from '../types';

export type ExecutionMode = 'DEMO' | 'LOCAL';

export interface BackendHealth {
  status: string;
  pythonAvailable: boolean;
  pythonExecutable?: string;
  message?: string;
}

export function useRunExecution(initialRunId?: string) {
  const [executionMode, setExecutionMode] = useState<ExecutionMode>('LOCAL');
  const [backendHealth, setBackendHealth] = useState<BackendHealth | null>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);

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

  // Check backend health on mount
  useEffect(() => {
    fetch('/api/local-health')
      .then(res => res.json())
      .then(data => {
        setBackendHealth(data);
        if (!data.pythonAvailable) {
          // If python is unavailable, default to DEMO mode
          setExecutionMode('DEMO');
        }
      })
      .catch(() => {
        setBackendHealth({ status: 'unavailable', pythonAvailable: false });
        setExecutionMode('DEMO');
      });
  }, []);

  const startRun = useCallback(
    async (
      request: WorkRequest,
      simulationType: 'STANDARD' | 'CONTROLLED_FAILURE' | 'BOUNDED_FAILURE' | 'STRATEGIC_TWIN' = 'STANDARD'
    ) => {
      setExecutionError(null);

      if (simulatorRef.current) {
        simulatorRef.current.cancel();
      }

      const runTemplate: WorkflowRun = {
        runId: `RUN-${Math.floor(Math.random() * 900) + 100}`,
        requestId: request.requestId || `req_${Date.now()}`,
        userGoal: request.userGoal,
        status: 'EXECUTING',
        durationSeconds: 0,
        isDemo: executionMode === 'DEMO',
        startedAt: new Date().toISOString(),
        currentStageIndex: 0,
        stages: [
          { key: 'PERCEPTION', label: 'Perception', shortDescription: 'Normalizing intent & requirements...', status: 'RUNNING' },
          { key: 'COMPANY_KNOWLEDGE', label: 'Company Knowledge', shortDescription: 'Authoritative Obsidian retrieval pending...', status: 'WAITING' },
          { key: 'REASONING', label: 'Reasoning', shortDescription: 'Structured multi-step planning pending...', status: 'WAITING' },
          { key: 'PLAN_VALIDATION', label: 'Plan Validation', shortDescription: 'DAG bounds & safety check pending...', status: 'WAITING' },
          { key: 'CAPABILITY_SELECTION', label: 'Capability Selection', shortDescription: 'Specialist registry matching pending...', status: 'WAITING' },
          { key: 'SPECIALIST_DELEGATION', label: 'Specialist Delegation', shortDescription: 'SecurityGuard boundary allocation pending...', status: 'WAITING' },
          { key: 'CONTROLLED_EXECUTION', label: 'Controlled Execution', shortDescription: 'Sandboxed capability execution pending...', status: 'WAITING' },
          { key: 'OBSERVATION_QA', label: 'Observation / QA', shortDescription: 'Empirical evidence capture pending...', status: 'WAITING' },
          { key: 'VERIFICATION', label: 'Verification', shortDescription: 'Success criteria verification pending...', status: 'WAITING' },
          { key: 'MEMORY_WRITEBACK', label: 'Memory Writeback', shortDescription: 'Obsidian memory persistence pending...', status: 'WAITING' },
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

      // --- LOCAL REAL MODE ---
      if (executionMode === 'LOCAL') {
        try {
          const realRun = await localWorkforceApi.createRun(request);
          setCurrentRun(realRun);
          setSelectedStageIndex(realRun.currentStageIndex || 0);
          setIsExecuting(false);
        } catch (err: any) {
          const errMsg = err.message || 'Local backend execution failed.';
          setExecutionError(errMsg);
          setIsExecuting(false);
          setCurrentRun(prev => ({
            ...prev,
            status: 'FAILED',
            stages: prev.stages.map((s, idx) =>
              idx === 0 ? { ...s, status: 'FAILED', shortDescription: errMsg } : s
            ),
          }));
        }
        return;
      }

      // --- DEMO SIMULATOR MODE ---
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
    [executionMode]
  );

  const loadRun = useCallback((run: WorkflowRun) => {
    if (simulatorRef.current) {
      simulatorRef.current.cancel();
    }
    setIsExecuting(false);
    setExecutionError(null);
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
    executionMode,
    setExecutionMode,
    backendHealth,
    executionError,
    startRun,
    loadRun,
    triggerControlledFailure,
    triggerRepeatedFailure,
  };
}
