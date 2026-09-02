import { ExecutiveTwin } from '../types';
import { mockExecutiveTwins } from '../mock';

export const twinService = {
  getTwins: async (): Promise<ExecutiveTwin[]> => {
    return new Promise((resolve) => setTimeout(() => resolve([...mockExecutiveTwins]), 100));
  },
  getTwinById: async (id: string): Promise<ExecutiveTwin | undefined> => {
    return new Promise((resolve) => resolve(mockExecutiveTwins.find(t => t.id === id)));
  },
  updateTwinStatus: async (id: string, status: ExecutiveTwin['status'], assignment?: string): Promise<ExecutiveTwin | undefined> => {
    const twin = mockExecutiveTwins.find(t => t.id === id);
    if (twin) {
      twin.status = status;
      if (assignment !== undefined) twin.currentAssignment = assignment;
    }
    return new Promise((resolve) => resolve(twin));
  }
};
