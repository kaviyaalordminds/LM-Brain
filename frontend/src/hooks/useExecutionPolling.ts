import { useState, useEffect, useCallback, useRef } from 'react';
import { orchestratorApi } from '../lib/api/orchestrator';
import {
  Execution,
  ExecutionEvent,
  DispatchAttempt,
  LineageArtifact,
  ExecutionStatusResponse,
} from '../lib/types';

interface UseExecutionPollingResult {
  execution: Execution | null;
  status: ExecutionStatusResponse | null;
  events: ExecutionEvent[];
  attempts: DispatchAttempt[];
  artifacts: LineageArtifact[];
  isLoading: boolean;
  isPolling: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useExecutionPolling(executionId?: string | null): UseExecutionPollingResult {
  const [execution, setExecution] = useState<Execution | null>(null);
  const [status, setStatus] = useState<ExecutionStatusResponse | null>(null);
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [attempts, setAttempts] = useState<DispatchAttempt[]>([]);
  const [artifacts, setArtifacts] = useState<LineageArtifact[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isPolling, setIsPolling] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const activeIdRef = useRef<string | null>(executionId || null);
  activeIdRef.current = executionId || null;

  const fetchData = useCallback(async () => {
    if (!executionId) {
      setExecution(null);
      setStatus(null);
      setEvents([]);
      setAttempts([]);
      setArtifacts([]);
      setError(null);
      return;
    }

    try {
      const [execData, statusData, eventsData, attemptsData, artifactsData] = await Promise.all([
        orchestratorApi.getExecution(executionId).catch(() => null),
        orchestratorApi.getExecutionStatus(executionId).catch(() => null),
        orchestratorApi.getExecutionEvents(executionId).catch(() => []),
        orchestratorApi.getExecutionAttempts(executionId).catch(() => []),
        orchestratorApi.getExecutionArtifacts(executionId).catch(() => []),
      ]);

      if (activeIdRef.current === executionId) {
        if (execData) setExecution(execData);
        if (statusData) setStatus(statusData);
        if (eventsData) setEvents(eventsData);
        if (attemptsData) setAttempts(attemptsData);
        if (artifactsData) setArtifacts(artifactsData);
        setError(null);
      }
    } catch (err: any) {
      if (activeIdRef.current === executionId) {
        setError(err?.message || 'Failed to fetch execution data');
      }
    }
  }, [executionId]);

  // Initial fetch
  useEffect(() => {
    if (!executionId) return;
    setIsLoading(true);
    fetchData().finally(() => setIsLoading(false));
  }, [executionId, fetchData]);

  // Polling loop
  useEffect(() => {
    if (!executionId) return;

    const currentStatus = execution?.status || status?.status;
    const isTerminal =
      currentStatus === 'COMPLETED' ||
      currentStatus === 'FAILED' ||
      currentStatus === 'CANCELLED';

    if (isTerminal) {
      setIsPolling(false);
      return;
    }

    setIsPolling(true);
    const interval = setInterval(() => {
      fetchData();
    }, 1200);

    return () => {
      clearInterval(interval);
      setIsPolling(false);
    };
  }, [executionId, execution?.status, status?.status, fetchData]);

  return {
    execution,
    status,
    events,
    attempts,
    artifacts,
    isLoading,
    isPolling,
    error,
    refetch: fetchData,
  };
}
