import { Project } from '../types';
import { mockProjects } from '../mock';

export const projectService = {
  getProjects: async (): Promise<Project[]> => {
    return new Promise((resolve) => setTimeout(() => resolve([...mockProjects]), 100));
  },
  getProjectById: async (id: string): Promise<Project | undefined> => {
    return new Promise((resolve) => resolve(mockProjects.find(p => p.id === id)));
  },
  createProject: async (project: Omit<Project, 'id'>): Promise<Project> => {
    const newProject: Project = {
      ...project,
      id: `project-${Date.now()}`
    };
    mockProjects.unshift(newProject);
    return new Promise((resolve) => setTimeout(() => resolve(newProject), 150));
  }
};
