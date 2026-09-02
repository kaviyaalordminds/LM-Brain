import { Task } from '../types';
import { mockTasks } from '../mock';

export const taskService = {
  getTasks: async (): Promise<Task[]> => {
    return new Promise((resolve) => setTimeout(() => resolve([...mockTasks]), 100));
  },
  getTaskById: async (id: string): Promise<Task | undefined> => {
    return new Promise((resolve) => resolve(mockTasks.find(t => t.id === id)));
  },
  createTask: async (query: string, mode: 'basic' | 'advanced'): Promise<Task> => {
    const newTask: Task = {
      id: `task-${Date.now()}`,
      query,
      mode,
      status: 'pending',
      progress: 0,
      startedAt: new Date().toISOString()
    };
    mockTasks.unshift(newTask);
    return new Promise((resolve) => setTimeout(() => resolve(newTask), 150));
  }
};
