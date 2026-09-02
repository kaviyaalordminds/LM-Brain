import { Tool } from '../types';
import { mockTools } from '../mock';

export const toolService = {
  getTools: async (): Promise<Tool[]> => {
    return new Promise((resolve) => setTimeout(() => resolve([...mockTools]), 100));
  },
  toggleToolStatus: async (id: string): Promise<Tool | undefined> => {
    const tool = mockTools.find(t => t.id === id);
    if (tool) {
      tool.status = tool.status === 'active' ? 'disabled' : 'active';
    }
    return new Promise((resolve) => resolve(tool));
  }
};
