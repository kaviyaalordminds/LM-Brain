import { Model } from '../types';
import { mockModels } from '../mock';

export const modelService = {
  getModels: async (): Promise<Model[]> => {
    return new Promise((resolve) => setTimeout(() => resolve([...mockModels]), 100));
  },
  toggleModelLoad: async (id: string): Promise<Model | undefined> => {
    const model = mockModels.find(m => m.id === id);
    if (model) {
      if (model.status === 'loaded') {
        model.status = 'unloaded';
      } else if (model.status === 'unloaded' || model.status === 'available') {
        model.status = 'loading';
        setTimeout(() => {
          model.status = 'loaded';
        }, 1500);
      }
    }
    return new Promise((resolve) => resolve(model));
  }
};
