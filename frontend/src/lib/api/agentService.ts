import { SpecialistAgent } from '../types';
import { mockSpecialists } from '../mock';

export const agentService = {
  getAgents: async (): Promise<SpecialistAgent[]> => {
    return new Promise((resolve) => setTimeout(() => resolve([...mockSpecialists]), 100));
  },
  getAgentById: async (id: string): Promise<SpecialistAgent | undefined> => {
    return new Promise((resolve) => resolve(mockSpecialists.find(a => a.id === id)));
  },
  updateAgentStatus: async (id: string, status: SpecialistAgent['status'], progress: number = 0): Promise<SpecialistAgent | undefined> => {
    const agent = mockSpecialists.find(a => a.id === id);
    if (agent) {
      agent.status = status;
      agent.progress = progress;
    }
    return new Promise((resolve) => resolve(agent));
  }
};
