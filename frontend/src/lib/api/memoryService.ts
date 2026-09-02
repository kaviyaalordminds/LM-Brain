import { MemoryItem } from '../types';
import { mockMemory } from '../mock';

export const memoryService = {
  getMemoryItems: async (): Promise<MemoryItem[]> => {
    return new Promise((resolve) => setTimeout(() => resolve([...mockMemory]), 100));
  },
  addMemoryItem: async (item: Omit<MemoryItem, 'id' | 'timestamp'>): Promise<MemoryItem> => {
    const newItem: MemoryItem = {
      ...item,
      id: `mem-${Date.now()}`,
      timestamp: new Date().toISOString()
    };
    mockMemory.unshift(newItem);
    return new Promise((resolve) => resolve(newItem));
  }
};
