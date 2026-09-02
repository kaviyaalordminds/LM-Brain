'use client';

import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { ActivityEvent, SpecialistAgent, ExecutiveTwin, Project } from '../types';
import { mockActivity, mockSpecialists, mockExecutiveTwins } from '../mock';
import { agentService } from '../api/agentService';
import { twinService } from '../api/twinService';

interface SimulationContextType {
  isPlaying: boolean;
  currentStep: number;
  simulatedEvents: ActivityEvent[];
  progress: number;
  activeProject: Project | null;
  agents: SpecialistAgent[];
  twins: ExecutiveTwin[];
  selectedAgentId: string | null;
  setSelectedAgentId: (id: string | null) => void;
  selectedTwinId: string | null;
  setSelectedTwinId: (id: string | null) => void;
  selectedProjectId: string | null;
  setSelectedProjectId: (id: string | null) => void;
  startSimulation: () => void;
  pauseSimulation: () => void;
  stepForward: () => void;
  resetSimulation: () => void;
}

const SimulationContext = createContext<SimulationContextType | undefined>(undefined);

export function SimulationProvider({ children }: { children: React.ReactNode }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const [simulatedEvents, setSimulatedEvents] = useState<ActivityEvent[]>([]);
  const [progress, setProgress] = useState(0);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [agents, setAgents] = useState<SpecialistAgent[]>([]);
  const [twins, setTwins] = useState<ExecutiveTwin[]>([]);
  
  // Selection states for Right Context Panel
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [selectedTwinId, setSelectedTwinId] = useState<string | null>(null);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize data
  useEffect(() => {
    const init = async () => {
      const a = await agentService.getAgents();
      const t = await twinService.getTwins();
      setAgents(a.map(item => ({ ...item, status: 'ready', progress: 0 })));
      setTwins(t.map(item => ({ ...item, status: 'standby', currentAssignment: undefined })));
    };
    init();
  }, []);

  const resetSimulation = async () => {
    setIsPlaying(false);
    setCurrentStep(-1);
    setSimulatedEvents([]);
    setProgress(0);
    setActiveProject(null);
    setSelectedAgentId(null);
    setSelectedTwinId(null);
    setSelectedProjectId(null);
    
    const a = await agentService.getAgents();
    const t = await twinService.getTwins();
    setAgents(a.map(item => ({ ...item, status: 'ready', progress: 0 })));
    setTwins(t.map(item => ({ ...item, status: 'standby', currentAssignment: undefined })));
    
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const runStep = (stepIndex: number) => {
    if (stepIndex >= mockActivity.length) {
      setIsPlaying(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      return;
    }

    const event = mockActivity[stepIndex];
    setSimulatedEvents(prev => [...prev, event]);
    setCurrentStep(stepIndex);

    const totalSteps = mockActivity.length;
    const progressPercent = Math.round(((stepIndex + 1) / totalSteps) * 100);
    setProgress(progressPercent);

    // Deep state transitions matching the 7-day demonstration target
    setAgents(prevAgents => {
      return prevAgents.map(agent => {
        // Spawn step (steps 6, 7, 8)
        if (stepIndex === 6 && agent.id === 'agent-frontend') {
          return { ...agent, status: 'spawn', progress: 10, currentTask: 'Init layout structure' };
        }
        if (stepIndex === 7 && agent.id === 'agent-backend') {
          return { ...agent, status: 'spawn', progress: 10, currentTask: 'Init API routing' };
        }
        if (stepIndex === 8 && (agent.id === 'agent-database' || agent.id === 'agent-testing')) {
          return { ...agent, status: 'spawn', progress: 10, currentTask: 'Prepare test and DB schema' };
        }
        if (stepIndex === 8 && agent.id === 'agent-security') {
          return { ...agent, status: 'spawn', progress: 10, currentTask: 'Set security policy' };
        }

        // Run step
        if (stepIndex === 9 && agent.id === 'agent-frontend') {
          return { ...agent, status: 'running', progress: 70, lastActivity: 'Coding layout.tsx...' };
        }
        if (stepIndex === 10 && agent.id === 'agent-frontend') {
          return { ...agent, status: 'complete', progress: 100, lastActivity: 'Layout file saved.' };
        }
        if (stepIndex === 10 && agent.id === 'agent-backend') {
          return { ...agent, status: 'running', progress: 60, lastActivity: 'Writing API contact routes...' };
        }

        if (stepIndex === 11 && agent.id === 'agent-database') {
          return { ...agent, status: 'running', progress: 80, lastActivity: 'Running migrations...' };
        }
        if (stepIndex === 11 && agent.id === 'agent-backend') {
          return { ...agent, status: 'complete', progress: 100 };
        }

        if (stepIndex === 12 && agent.id === 'agent-database') {
          return { ...agent, status: 'complete', progress: 100 };
        }
        if (stepIndex === 12 && agent.id === 'agent-testing') {
          return { ...agent, status: 'running', progress: 40, lastActivity: 'Running test suites...' };
        }

        // Verification fails (step 13)
        if (stepIndex === 13 && agent.id === 'agent-testing') {
          return { ...agent, status: 'failed', progress: 45, lastActivity: 'Verification failed: middleware session token check failure' };
        }

        // Reflection (step 14)
        if (stepIndex === 14 && agent.id === 'agent-backend') {
          return { ...agent, status: 'reflect', lastActivity: 'Analyzing logs for middleware session failure...' };
        }

        // Retry (step 15, 16)
        if (stepIndex === 15 && agent.id === 'agent-backend') {
          return { ...agent, status: 'retry', progress: 50, lastActivity: 'Re-planning fix step...' };
        }
        if (stepIndex === 16 && agent.id === 'agent-backend') {
          return { ...agent, status: 'running', progress: 90, lastActivity: 'Applying bypass configuration...' };
        }

        // Re-run Verification (step 17, 18)
        if (stepIndex === 17 && agent.id === 'agent-backend') {
          return { ...agent, status: 'complete', progress: 100 };
        }
        if (stepIndex === 17 && agent.id === 'agent-testing') {
          return { ...agent, status: 'running', progress: 90, lastActivity: 'Re-running unit test suites...' };
        }
        if (stepIndex === 18 && agent.id === 'agent-testing') {
          return { ...agent, status: 'complete', progress: 100, lastActivity: 'All tests passed.' };
        }
        if (stepIndex === 18 && agent.id === 'agent-security') {
          return { ...agent, status: 'complete', progress: 100, lastActivity: 'Security audit passed.' };
        }

        // Terminate completed agents (step 19)
        if (stepIndex === 19) {
          return { ...agent, status: 'terminate', progress: 100 };
        }

        return agent;
      });
    });

    setTwins(prevTwins => {
      return prevTwins.map(twin => {
        // Activate CTO Twin and CMO Twin (step 4)
        if (stepIndex === 4 && twin.role === 'CTO') {
          return {
            ...twin,
            status: 'active',
            currentAssignment: 'Architecture validation for Company Website Platform',
            activationReason: 'Task requires major technical architecture decision.'
          };
        }
        if (stepIndex === 4 && twin.role === 'CMO') {
          return {
            ...twin,
            status: 'active',
            currentAssignment: 'Validating brand design guidelines.'
          };
        }
        // Complete twins assignments near the end (step 18)
        if (stepIndex === 18 && (twin.role === 'CTO' || twin.role === 'CMO')) {
          return {
            ...twin,
            status: 'completed',
            currentAssignment: undefined
          };
        }
        return twin;
      });
    });

    // Handle project status
    if (stepIndex === 0) {
      setActiveProject({
        id: 'simulated-project',
        name: 'Simulated Company Website Platform',
        description: 'A website campaign platform spawned dynamically via demo workspace.',
        mode: 'advanced',
        status: 'planning',
        progress: 5,
        agents: ['agent-frontend', 'agent-backend', 'agent-database', 'agent-testing', 'agent-security'],
        twins: ['twin-cto', 'twin-cmo'],
        requirements: [
          { id: 'sim-req-1', text: 'Responsive, modern landing page matching brand guidelines.', category: 'functional', status: 'pending' },
          { id: 'sim-req-2', text: 'Secure contact form with email submission backend.', category: 'functional', status: 'pending' },
          { id: 'sim-req-3', text: 'SQLite database connection configuration.', category: 'functional', status: 'pending' }
        ],
        plan: [
          { id: 'sim-step-1', title: 'Perception & Goals Analysis', description: 'Analyze constraints and targets.', status: 'completed', dependencies: [], successCriteria: 'Intent understood.' },
          { id: 'sim-step-2', title: 'Knowledge Retrieval', description: 'Query Obsidian Vault for Guidelines.', status: 'running', dependencies: ['sim-step-1'], successCriteria: 'Vault read complete.' },
          { id: 'sim-step-3', title: 'Codebase Creation', description: 'Frontend and Backend execution.', status: 'pending', dependencies: ['sim-step-2'], successCriteria: 'Builds cleanly.' },
          { id: 'sim-step-4', title: 'System Verification', description: 'Run automated verification tests.', status: 'pending', dependencies: ['sim-step-3'], successCriteria: 'All tests pass.' }
        ],
        successCriteria: ['Lighthouse performance score > 90', 'No hardcoded credentials'],
        constraints: ['Self-hosted locally']
      });
    }

    if (activeProject || stepIndex >= 0) {
      setActiveProject(prev => {
        // Fallback if prev is null
        const currentProject = prev || {
          id: 'simulated-project',
          name: 'Simulated Company Website Platform',
          description: 'A website campaign platform spawned dynamically via demo workspace.',
          mode: 'advanced',
          status: 'planning',
          progress: 5,
          agents: ['agent-frontend', 'agent-backend', 'agent-database', 'agent-testing', 'agent-security'],
          twins: ['twin-cto', 'twin-cmo'],
          requirements: [
            { id: 'sim-req-1', text: 'Responsive, modern landing page matching brand guidelines.', category: 'functional', status: 'pending' },
            { id: 'sim-req-2', text: 'Secure contact form with email submission backend.', category: 'functional', status: 'pending' },
            { id: 'sim-req-3', text: 'SQLite database connection configuration.', category: 'functional', status: 'pending' }
          ],
          plan: [
            { id: 'sim-step-1', title: 'Perception & Goals Analysis', description: 'Analyze constraints and targets.', status: 'completed', dependencies: [], successCriteria: 'Intent understood.' },
            { id: 'sim-step-2', title: 'Knowledge Retrieval', description: 'Query Obsidian Vault for Guidelines.', status: 'running', dependencies: ['sim-step-1'], successCriteria: 'Vault read complete.' },
            { id: 'sim-step-3', title: 'Codebase Creation', description: 'Frontend and Backend execution.', status: 'pending', dependencies: ['sim-step-2'], successCriteria: 'Builds cleanly.' },
            { id: 'sim-step-4', title: 'System Verification', description: 'Run automated verification tests.', status: 'pending', dependencies: ['sim-step-3'], successCriteria: 'All tests pass.' }
          ],
          successCriteria: ['Lighthouse performance score > 90', 'No hardcoded credentials'],
          constraints: ['Self-hosted locally']
        };

        let status = currentProject.status;
        let currentPhase = currentProject.currentPhase || 'Requirements Map';
        let plan = [...currentProject.plan];
        let requirements = [...currentProject.requirements];

        if (stepIndex === 2) {
          requirements = requirements.map(r => r.id === 'sim-req-1' ? { ...r, status: 'satisfied' } : r);
          plan[1] = { ...plan[1], status: 'completed' };
          plan[2] = { ...plan[2], status: 'running' };
          currentPhase = 'Knowledge Retrieval';
        }
        if (stepIndex === 5) {
          status = 'running';
          currentPhase = 'Workforce Active';
        }
        if (stepIndex === 12) {
          status = 'verification';
          plan[2] = { ...plan[2], status: 'completed' };
          plan[3] = { ...plan[3], status: 'running' };
          currentPhase = 'Running Tests';
        }
        if (stepIndex === 13) {
          status = 'needs_review';
          plan[3] = { ...plan[3], status: 'failed' };
          requirements = requirements.map(r => r.id === 'sim-req-2' ? { ...r, status: 'failed' } : r);
          currentPhase = 'Verification Failed';
        }
        if (stepIndex === 15) {
          status = 'running';
          plan[3] = { ...plan[3], status: 'retrying' };
          currentPhase = 'Reflecting & Retrying';
        }
        if (stepIndex === 18) {
          status = 'verification';
          requirements = requirements.map(r => ({ ...r, status: 'satisfied' }));
          plan[3] = { ...plan[3], status: 'completed' };
          currentPhase = 'All Tests Passed';
        }
        if (stepIndex === 21) {
          status = 'completed';
          currentPhase = 'Completed & Synced';
        }

        return {
          ...currentProject,
          status,
          currentPhase,
          plan,
          requirements,
          progress: progressPercent
        };
      });
    }
  };

  const startSimulation = () => {
    if (isPlaying) return;
    setIsPlaying(true);
    let nextStep = currentStep + 1;
    if (nextStep >= mockActivity.length) {
      resetSimulation().then(() => {
        setIsPlaying(true);
        runStep(0);
      });
      return;
    }
    runStep(nextStep);

    timerRef.current = setInterval(() => {
      nextStep += 1;
      if (nextStep < mockActivity.length) {
        runStep(nextStep);
      } else {
        setIsPlaying(false);
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
      }
    }, 2000);
  };

  const pauseSimulation = () => {
    setIsPlaying(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const stepForward = () => {
    pauseSimulation();
    const nextStep = currentStep + 1;
    if (nextStep < mockActivity.length) {
      runStep(nextStep);
    }
  };

  return (
    <SimulationContext.Provider
      value={{
        isPlaying,
        currentStep,
        simulatedEvents,
        progress,
        activeProject,
        agents,
        twins,
        selectedAgentId,
        setSelectedAgentId,
        selectedTwinId,
        setSelectedTwinId,
        selectedProjectId,
        setSelectedProjectId,
        startSimulation,
        pauseSimulation,
        stepForward,
        resetSimulation
      }}
    >
      {children}
    </SimulationContext.Provider>
  );
}

export function useSimulation() {
  const context = useContext(SimulationContext);
  if (!context) {
    throw new Error('useSimulation must be used within a SimulationProvider');
  }
  return context;
}
