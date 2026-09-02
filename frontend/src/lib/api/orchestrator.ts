import {
  Execution,
  ExecutionStatusResponse,
  ExecutionEvent,
  LineageArtifact,
  DispatchAttempt,
  Plan,
  SystemHealth,
} from '../types';

const BASE_URL = typeof window !== 'undefined' ? '' : 'http://127.0.0.1:8000';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const data = await res.json();
      if (data.detail) {
        errorDetail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // Ignore JSON parse error on non-json error responses
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const orchestratorApi = {
  async createExecution(user_request: string, context: Record<string, any> = {}): Promise<{ execution_id: string; status: string }> {
    const res = await fetch(`${BASE_URL}/api/v1/executions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_request, context }),
    });
    return handleResponse(res);
  },

  async getExecution(execution_id: string): Promise<Execution> {
    const res = await fetch(`${BASE_URL}/api/v1/executions/${execution_id}`, { cache: 'no-store' });
    return handleResponse<Execution>(res);
  },

  async getExecutionStatus(execution_id: string): Promise<ExecutionStatusResponse> {
    const res = await fetch(`${BASE_URL}/api/v1/executions/${execution_id}/status`, { cache: 'no-store' });
    return handleResponse<ExecutionStatusResponse>(res);
  },

  async getExecutionEvents(execution_id: string): Promise<ExecutionEvent[]> {
    const res = await fetch(`${BASE_URL}/api/v1/executions/${execution_id}/events`, { cache: 'no-store' });
    return handleResponse<ExecutionEvent[]>(res);
  },

  async listExecutions(): Promise<Execution[]> {
    try {
      const res = await fetch(`${BASE_URL}/api/v1/executions`, { cache: 'no-store' });
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  },

  async getExecutionArtifacts(execution_id: string): Promise<LineageArtifact[]> {
    try {
      const res = await fetch(`${BASE_URL}/api/v1/executions/${execution_id}/artifacts`, { cache: 'no-store' });
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  },

  async getExecutionAttempts(execution_id: string): Promise<DispatchAttempt[]> {
    try {
      const res = await fetch(`${BASE_URL}/api/v1/executions/${execution_id}/attempts`, { cache: 'no-store' });
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  },

  async getPlan(plan_id: string): Promise<Plan | null> {
    try {
      const res = await fetch(`${BASE_URL}/api/v1/plans/${plan_id}`, { cache: 'no-store' });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async pauseExecution(execution_id: string): Promise<{ execution_id: string; status: string }> {
    const res = await fetch(`${BASE_URL}/api/v1/executions/${execution_id}/pause`, {
      method: 'POST',
    });
    return handleResponse(res);
  },

  async resumeExecution(execution_id: string): Promise<{ execution_id: string; status: string }> {
    const res = await fetch(`${BASE_URL}/api/v1/executions/${execution_id}/resume`, {
      method: 'POST',
    });
    return handleResponse(res);
  },

  async cancelExecution(execution_id: string): Promise<{ execution_id: string; status: string }> {
    const res = await fetch(`${BASE_URL}/api/v1/executions/${execution_id}/cancel`, {
      method: 'POST',
    });
    return handleResponse(res);
  },

  async checkHealth(): Promise<SystemHealth> {
    const res = await fetch(`${BASE_URL}/health`, { cache: 'no-store' });
    return handleResponse<SystemHealth>(res);
  },

  async checkReady(): Promise<{ status: string; dependencies: { planner: string; memory: string } }> {
    const res = await fetch(`${BASE_URL}/ready`, { cache: 'no-store' });
    return handleResponse(res);
  },
};
