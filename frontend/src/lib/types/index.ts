export interface Requirement {
  id: string;
  text: string;
  category: 'functional' | 'non-functional' | 'constraint' | 'output' | 'context';
  status: 'pending' | 'satisfied' | 'failed';
}

export interface PlanStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'retrying';
  dependencies: string[];
  successCriteria: string;
  assignedAgentId?: string;
}

export interface WorkflowStep {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'retrying' | 'skipped' | 'blocked';
  timestamp?: string;
  duration?: string;
  description: string;
  details?: string[];
}

export interface VerificationResult {
  id: string;
  taskName: string;
  status: 'passed' | 'failed' | 'pending';
  timestamp: string;
  errors?: string[];
  logs: string[];
  duration: string;
}

export interface MemoryItem {
  id: string;
  type: 'retrieved' | 'written' | 'decision' | 'lesson' | 'context';
  title: string;
  content: string;
  usedBy: string[];
  timestamp: string;
  vault: string;
}

export interface Model {
  id: string;
  name: string;
  type: 'reasoning' | 'coding' | 'speech-to-text' | 'vision' | 'image' | 'video' | 'text-to-speech' | 'embeddings' | 'reranking';
  parameters: string;
  quantization: string;
  vram: string;
  status: 'available' | 'loaded' | 'unloaded' | 'loading' | 'unavailable';
  isLocal: boolean;
}

export interface Tool {
  id: string;
  name: string;
  description: string;
  status: 'ready' | 'active' | 'disabled';
  permissionLevel: 'read' | 'write' | 'admin';
  agentAccess: string[];
  lastUsed?: string;
}

export interface SecurityEvent {
  id: string;
  action: string;
  status: 'allowed' | 'blocked' | 'escalated' | 'review_required';
  checks: { name: string; status: 'passed' | 'failed' | 'pending' }[];
  timestamp: string;
}

export interface Artifact {
  id: string;
  name: string;
  path: string;
  type: 'file' | 'code' | 'image' | 'document';
  content: string;
  size?: string;
  createdAt: string;
}

export interface ActivityEvent {
  id: string;
  timestamp: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  component: 'perception' | 'orchestrator' | 'planner' | 'security' | 'agent' | 'memory' | 'verification' | 'input' | 'output';
}

export interface Task {
  id: string;
  query: string;
  mode: 'basic' | 'advanced';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'retrying';
  progress: number;
  startedAt: string;
  duration?: string;
}

export interface ExecutiveTwin {
  id: string;
  name: string;
  role: 'CEO' | 'COO' | 'CTO' | 'CMO' | 'CFO';
  responsibilities: string[];
  currentAssignment?: string;
  status: 'standby' | 'active' | 'planning' | 'reviewing' | 'completed' | 'escalated';
  activationReason?: string;
  recommendations: string[];
  delegatedSpecialists: string[];
  activityLog: string[];
}

export interface SpecialistAgent {
  id: string;
  name: string;
  capability: string;
  status: 'ready' | 'local' | 'offline' | 'coming_online' | 'spawn' | 'assign' | 'running' | 'verify' | 'complete' | 'terminate' | 'failed' | 'reflect' | 'retry';
  currentTask?: string;
  progress: number;
  model: string;
  tools: string[];
  lastActivity: string;
  duration?: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  mode: 'basic' | 'advanced';
  status: 'planning' | 'running' | 'verification' | 'completed' | 'needs_review' | 'failed';
  progress: number;
  agents: string[];
  twins: string[];
  requirements: Requirement[];
  plan: PlanStep[];
  successCriteria: string[];
  constraints: string[];
  currentPhase?: string;
  startTime?: string;
  artifacts?: Artifact[];
  verificationResult?: VerificationResult;
}
