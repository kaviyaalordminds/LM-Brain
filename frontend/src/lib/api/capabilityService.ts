import { mockSpecialists } from '../mock';

export const capabilityService = {
  getCapabilities: async (): Promise<string[]> => {
    const caps = Array.from(new Set(mockSpecialists.map(a => a.capability)));
    return new Promise((resolve) => setTimeout(() => resolve(caps), 50));
  }
};
