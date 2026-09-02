import { useState, useEffect, useCallback } from 'react';
import { orchestratorApi } from '../lib/api/orchestrator';

export interface SystemHealthState {
  master: 'UP' | 'DOWN' | 'CONNECTING';
  planner: 'UP' | 'DOWN' | 'UNKNOWN';
  memory: 'UP' | 'DOWN' | 'UNKNOWN';
  persistence: 'SQLITE' | 'IN_MEMORY';
  isReady: boolean;
  lastChecked: string | null;
}

export function useSystemHealth(pollIntervalMs: number = 5000): SystemHealthState {
  const [health, setHealth] = useState<SystemHealthState>({
    master: 'CONNECTING',
    planner: 'UNKNOWN',
    memory: 'UNKNOWN',
    persistence: 'SQLITE',
    isReady: false,
    lastChecked: null,
  });

  const checkHealth = useCallback(async () => {
    try {
      const [healthRes, readyRes] = await Promise.all([
        orchestratorApi.checkHealth().catch(() => null),
        orchestratorApi.checkReady().catch(() => null),
      ]);

      if (healthRes) {
        setHealth({
          master: 'UP',
          planner: readyRes?.dependencies?.planner?.toUpperCase() === 'UP' ? 'UP' : 'DOWN',
          memory: readyRes?.dependencies?.memory?.toUpperCase() === 'UP' ? 'UP' : 'DOWN',
          persistence: 'SQLITE',
          isReady: readyRes?.status === 'ready',
          lastChecked: new Date().toISOString(),
        });
      } else {
        setHealth(prev => ({
          ...prev,
          master: 'DOWN',
          isReady: false,
          lastChecked: new Date().toISOString(),
        }));
      }
    } catch {
      setHealth(prev => ({
        ...prev,
        master: 'DOWN',
        isReady: false,
        lastChecked: new Date().toISOString(),
      }));
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, pollIntervalMs);
    return () => clearInterval(interval);
  }, [checkHealth, pollIntervalMs]);

  return health;
}
