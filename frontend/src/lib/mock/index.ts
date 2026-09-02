import {
  Task,
  Project,
  SpecialistAgent,
  ExecutiveTwin,
  ActivityEvent,
  WorkflowStep,
  MemoryItem,
  Model,
  Tool,
  VerificationResult
} from '../types';

export const mockTasks: Task[] = [
  {
    id: 'task-1',
    query: 'Create a complete company landing website.',
    mode: 'advanced',
    status: 'completed',
    progress: 100,
    startedAt: '2026-08-31T09:00:00Z',
    duration: '2m 14s'
  },
  {
    id: 'task-2',
    query: 'Generate a marketing poster for the new AI workforce product launch.',
    mode: 'basic',
    status: 'completed',
    progress: 100,
    startedAt: '2026-08-31T10:15:00Z',
    duration: '18s'
  },
  {
    id: 'task-3',
    query: 'Analyze the AWS cloud deployment cost report and advise optimization.',
    mode: 'advanced',
    status: 'failed',
    progress: 45,
    startedAt: '2026-08-31T11:00:00Z',
    duration: '42s'
  }
];

export const mockProjects: Project[] = [
  {
    id: 'project-website',
    name: 'Company Website Platform',
    description: 'A premium corporate portal built with Next.js, tailwindcss, and TypeScript, backed by SQLite.',
    mode: 'advanced',
    status: 'completed',
    progress: 100,
    startTime: '2026-08-31T09:00:00Z',
    currentPhase: 'Final Verification',
    agents: ['agent-frontend', 'agent-backend', 'agent-database', 'agent-testing', 'agent-security'],
    twins: ['twin-cto', 'twin-cmo'],
    requirements: [
      { id: 'req-1', text: 'Responsive, modern landing page matching brand guidelines.', category: 'functional', status: 'satisfied' },
      { id: 'req-2', text: 'Secure lead contact form with email submission backend.', category: 'functional', status: 'satisfied' },
      { id: 'req-3', text: 'Local SQLite database storing submissions.', category: 'functional', status: 'satisfied' },
      { id: 'req-4', text: 'Unit tests for auth API middleware and page loading.', category: 'functional', status: 'satisfied' },
      { id: 'req-5', text: 'Protected environment variables and API routes.', category: 'constraint', status: 'satisfied' }
    ],
    plan: [
      { id: 'step-1', title: 'Perception & Intent Parsing', description: 'Analyze user requirements and detect required twins & specialists.', status: 'completed', dependencies: [], successCriteria: 'Intent understood and agents selected.' },
      { id: 'step-2', title: 'Knowledge Retrieval', description: 'Query Obsidian Vault for Brand Guidelines and Tech Specs.', status: 'completed', dependencies: ['step-1'], successCriteria: 'Context loaded into orchestrator memory.' },
      { id: 'step-3', title: 'Architecture Definition', description: 'CTO Twin defines technology stack and layout schema.', status: 'completed', dependencies: ['step-2'], successCriteria: 'Architecture plan approved.' },
      { id: 'step-4', title: 'Frontend UI Implementation', description: 'Build component structure, styles, and responsive layout.', status: 'completed', dependencies: ['step-3'], successCriteria: 'React pages compile cleanly.' },
      { id: 'step-5', title: 'Backend & Database Setup', description: 'Create database connections, schemas, and submit handlers.', status: 'completed', dependencies: ['step-3'], successCriteria: 'Routes accept and store form submissions.' },
      { id: 'step-6', title: 'Security Auditing', description: 'Review route authentication, guardrails, and env variables.', status: 'completed', dependencies: ['step-4', 'step-5'], successCriteria: 'No hardcoded credentials, check logs.' },
      { id: 'step-7', title: 'Integrative Testing & Verification', description: 'Run automated end-to-end and unit tests.', status: 'completed', dependencies: ['step-6'], successCriteria: 'All unit and integration tests report passed.' },
      { id: 'step-8', title: 'Memory Checkpointing & Obsidian Update', description: 'Write final codebase metadata, decisions, and lessons learned back to Obsidian.', status: 'completed', dependencies: ['step-7'], successCriteria: 'Vault synchronized.' }
    ],
    successCriteria: [
      'Lighthouse performance score > 90',
      'All security check rules allowed',
      'No missing middleware validation parameters'
    ],
    constraints: [
      'Must run strictly locally without external cloud API dependencies.',
      'Deployment target: local server behind reverse proxy.'
    ],
    artifacts: [
      { id: 'art-1', name: 'App Layout', path: 'src/app/layout.tsx', type: 'code', content: '// Premium Sidebar Shell\nexport default function RootLayout(...) { ... }', createdAt: '2026-08-31T09:01:22Z' },
      { id: 'art-2', name: 'Database Model', path: 'src/lib/db.ts', type: 'code', content: 'import sqlite3 from "sqlite3";\nexport const db = new sqlite3.Database(":memory:");', createdAt: '2026-08-31T09:02:10Z' },
      { id: 'art-3', name: 'Submit Form Route', path: 'src/app/api/contact/route.ts', type: 'code', content: 'export async function POST(req) { \n  // Authenticated form handler \n}', createdAt: '2026-08-31T09:02:45Z' }
    ],
    verificationResult: {
      id: 'ver-website',
      taskName: 'Create a complete company landing website.',
      status: 'passed',
      timestamp: '2026-08-31T09:02:14Z',
      logs: [
        '[System] Initiating test run...',
        '[E2E] Homepage loaded successfully (244ms)',
        '[API] POST /api/contact - Missing credentials response code: 401 (Passed)',
        '[API] POST /api/contact - Valid input saved to SQLite (Passed)',
        '[Security] CORS check: Blocked external wildcards (Passed)',
        '[Audit] Verification completed: 100% tests successful.'
      ],
      duration: '4.8s'
    }
  },
  {
    id: 'project-marketing-campaign',
    name: 'Product Launch Marketing Strategy',
    description: 'Comprehensive campaigns, positioning guidelines, and multimedia launch assets.',
    mode: 'advanced',
    status: 'running',
    progress: 60,
    startTime: '2026-08-31T11:20:00Z',
    currentPhase: 'Asset Generation',
    agents: ['agent-poster', 'agent-content', 'agent-image', 'agent-ppt'],
    twins: ['twin-cmo', 'twin-cfo'],
    requirements: [
      { id: 'req-m1', text: 'Complete marketing launch outline slide deck.', category: 'functional', status: 'satisfied' },
      { id: 'req-m2', text: 'Social media post content calendar for 30 days.', category: 'functional', status: 'satisfied' },
      { id: 'req-m3', text: 'Promotional graphic design layout concept.', category: 'functional', status: 'pending' },
      { id: 'req-m4', text: 'Ad budget and ROI projection breakdown.', category: 'constraint', status: 'satisfied' }
    ],
    plan: [
      { id: 'step-m1', title: 'Requirements Review', description: 'Analyze constraints and targets.', status: 'completed', dependencies: [], successCriteria: 'Objectives mapped.' },
      { id: 'step-m2', title: 'Financial Risk Optimization', description: 'CFO Twin calculates budget boundaries and cost projections.', status: 'completed', dependencies: ['step-m1'], successCriteria: 'Max budget limit determined.' },
      { id: 'step-m3', title: 'Positioning & Pitch Deck Outline', description: 'CMO Twin outputs campaign guidelines.', status: 'completed', dependencies: ['step-m1'], successCriteria: 'Brand guidelines compiled.' },
      { id: 'step-m4', title: 'Copywriting & Content Production', description: 'Content Agent drafts messaging schedule.', status: 'completed', dependencies: ['step-m3'], successCriteria: '30-day schedule written.' },
      { id: 'step-m5', title: 'Asset Graphic Generation', description: 'Image Agent generates visual backdrops.', status: 'running', dependencies: ['step-m3'], successCriteria: 'Assets generated.' },
      { id: 'step-m6', title: 'Final Presentation Compile', description: 'PPT Agent aggregates copy and assets into slide file.', status: 'pending', dependencies: ['step-m4', 'step-m5'], successCriteria: 'Presentation files created.' }
    ],
    successCriteria: [
      'ROI estimate exceeds 2.5x',
      'All slide structures match guidelines'
    ],
    constraints: [
      'Advertising budget capped at $5,000.',
      'Must complete files within 2 hours.'
    ]
  }
];

export const mockExecutiveTwins: ExecutiveTwin[] = [
  {
    id: 'twin-ceo',
    name: 'CEO Twin',
    role: 'CEO',
    responsibilities: [
      'Company long-term strategy',
      'Strategic priorities align',
      'Major business trade-offs',
      'Executive decisions recommendation'
    ],
    status: 'standby',
    recommendations: [
      'Recommend focusing workforce optimization on local offline models to maintain maximum corporate IP security.'
    ],
    delegatedSpecialists: [],
    activityLog: ['Standby mode initiated. ready for strategic scaling.']
  },
  {
    id: 'twin-coo',
    name: 'COO Twin',
    role: 'COO',
    responsibilities: [
      'Operations tracking',
      'Workflows efficiency management',
      'Resource & GPU coordination',
      'Process bottlenecks optimization'
    ],
    status: 'standby',
    recommendations: [],
    delegatedSpecialists: [],
    activityLog: ['Operations checklist updated. Active threads: 0. Ready to optimize pipelines.']
  },
  {
    id: 'twin-cto',
    name: 'CTO Twin',
    role: 'CTO',
    responsibilities: [
      'Technology stack decisions',
      'System & Codebase architecture',
      'Local model parameters optimization',
      'Database and Security compliance roadmaps'
    ],
    status: 'active',
    currentAssignment: 'Architecture validation for Company Website Platform',
    activationReason: 'Task requires major technical architecture decision.',
    recommendations: [
      'Use modular Next.js app router structure.',
      'Leverage local SQLite db to keep client logs offline.',
      'Isolate user API endpoints under a strict JWT middleware layer.'
    ],
    delegatedSpecialists: ['agent-frontend', 'agent-backend', 'agent-database', 'agent-security'],
    activityLog: [
      'Active: Evaluating website design query...',
      'Approved: Next.js + SQLite stack.',
      'Delegated 4 specialist agents for codebase generation.',
      'Reviewed and approved security middleware adjustments.'
    ]
  },
  {
    id: 'twin-cmo',
    name: 'CMO Twin',
    role: 'CMO',
    responsibilities: [
      'Marketing strategy guidelines',
      'Product positioning guidelines',
      'Audience profiling',
      'Asset brand guidelines validation'
    ],
    status: 'active',
    currentAssignment: 'Launch Campaign Guidelines for AI platform',
    activationReason: 'Task request contains high-level branding and copywriting requirements.',
    recommendations: [
      'Focus visual messaging on the concept of "Autonomous Workforce" rather than simple AI chatbot.',
      'Use dark slate gray backgrounds (#0f172a) with deep indigo accents (#6366f1) in all launch posters.'
    ],
    delegatedSpecialists: ['agent-poster', 'agent-content', 'agent-image'],
    activityLog: [
      'Activated for campaign design.',
      'Written brand positioning requirements.',
      'Synced poster rules with Poster Agent and Image Agent.'
    ]
  },
  {
    id: 'twin-cfo',
    name: 'CFO Twin',
    role: 'CFO',
    responsibilities: [
      'GPU resource cost tracking',
      'Model training budgets',
      'Project viability calculation',
      'Financial risk management'
    ],
    status: 'standby',
    recommendations: [],
    delegatedSpecialists: [],
    activityLog: ['Cost calculation models updated. Active inference rate: $0.00/hr (Fully local).']
  }
];

export const mockSpecialists: SpecialistAgent[] = [
  {
    id: 'agent-frontend',
    name: 'Frontend Agent',
    capability: 'Web Development',
    status: 'ready',
    currentTask: 'Build responsive landing page UI shell',
    progress: 100,
    model: 'Local Llama-3-70B-Instruct (Q8)',
    tools: ['Filesystem', 'Terminal', 'Web Browser'],
    lastActivity: 'Completed layout file. Compilation successful.',
    duration: '52s'
  },
  {
    id: 'agent-backend',
    name: 'Backend Agent',
    capability: 'Web Development',
    status: 'ready',
    currentTask: 'Configure SQLite connection and setup submit endpoints',
    progress: 100,
    model: 'Local Qwen-2.5-Coder-32B',
    tools: ['Filesystem', 'Terminal', 'SQLite'],
    lastActivity: 'Finished contact form post route and tests verification.',
    duration: '45s'
  },
  {
    id: 'agent-database',
    name: 'Database Agent',
    capability: 'Spreadsheet / DB',
    status: 'ready',
    currentTask: 'Initialize database table structure and create migrations',
    progress: 100,
    model: 'Local Qwen-2.5-Coder-14B',
    tools: ['SQLite', 'Terminal'],
    lastActivity: 'Table structure validated and seed query executed.',
    duration: '18s'
  },
  {
    id: 'agent-testing',
    name: 'Testing Agent',
    capability: 'Testing & Verification',
    status: 'ready',
    currentTask: 'Run middleware validation unit tests',
    progress: 100,
    model: 'Local Llama-3-8B-Instruct',
    tools: ['Terminal', 'Code Runner'],
    lastActivity: 'All 8 test suites passed. Overall coverage: 94.2%',
    duration: '22s'
  },
  {
    id: 'agent-security',
    name: 'Security Agent',
    capability: 'Deployment / Security',
    status: 'ready',
    currentTask: 'Perform secrets scan and evaluate route guardrails',
    progress: 100,
    model: 'Local DeepSeek-Coder-6.7B',
    tools: ['Terminal', 'File Scan'],
    lastActivity: 'Secrets scan completed. No active key exposures detected.',
    duration: '14s'
  },
  {
    id: 'agent-poster',
    name: 'Poster Agent',
    capability: 'Poster / Graphic Design',
    status: 'ready',
    progress: 0,
    model: 'Local Stable Diffusion XL',
    tools: ['Image Generator', 'Filesystem'],
    lastActivity: 'Awaiting design triggers.'
  },
  {
    id: 'agent-content',
    name: 'Content Agent',
    capability: 'Content Creation',
    status: 'ready',
    currentTask: 'Drafting 30 days of campaign posts',
    progress: 80,
    model: 'Local Llama-3-70B-Instruct (Q8)',
    tools: ['Document Generator'],
    lastActivity: 'Drafted 24 social media posts.',
    duration: '1m 20s'
  },
  {
    id: 'agent-image',
    name: 'Image Agent',
    capability: 'Image Generation',
    status: 'ready',
    currentTask: 'Generate marketing poster backdrop assets',
    progress: 50,
    model: 'Local Flux.1-Schnell',
    tools: ['Image Generator'],
    lastActivity: 'Asset 1 rendered. Generating asset 2...',
    duration: '35s'
  },
  {
    id: 'agent-ppt',
    name: 'PPT Agent',
    capability: 'PPT',
    status: 'ready',
    progress: 0,
    model: 'Local Qwen-2.5-Coder-14B',
    tools: ['PPT Generator'],
    lastActivity: 'Waiting for content guidelines from Content Agent.'
  },
  {
    id: 'agent-logo',
    name: 'Logo / Branding Agent',
    capability: 'Logo / Branding',
    status: 'ready',
    progress: 0,
    model: 'Local Flux.1-Schnell',
    tools: ['Image Generator'],
    lastActivity: 'Idle'
  },
  {
    id: 'agent-audio-trans',
    name: 'Audio Transcription Agent',
    capability: 'Audio Transcription',
    status: 'ready',
    progress: 0,
    model: 'Local Whisper Large V3',
    tools: ['Audio Transcription'],
    lastActivity: 'Idle'
  },
  {
    id: 'agent-audio-gen',
    name: 'Audio Generation Agent',
    capability: 'Audio Generation',
    status: 'ready',
    progress: 0,
    model: 'Local Bark TTS',
    tools: ['TTS'],
    lastActivity: 'Idle'
  },
  {
    id: 'agent-voice-clone',
    name: 'Voice Cloning Agent',
    capability: 'Voice Processing / Cloning',
    status: 'ready',
    progress: 0,
    model: 'Local Coqui XTTS V2',
    tools: ['TTS', 'Audio Tool'],
    lastActivity: 'Idle'
  },
  {
    id: 'agent-doc',
    name: 'Document Agent',
    capability: 'Document',
    status: 'ready',
    progress: 0,
    model: 'Local Llama-3-8B-Instruct',
    tools: ['Document Generator'],
    lastActivity: 'Idle'
  },
  {
    id: 'agent-spreadsheet',
    name: 'Spreadsheet Agent',
    capability: 'Spreadsheet',
    status: 'ready',
    progress: 0,
    model: 'Local Qwen-2.5-Coder-14B',
    tools: ['Spreadsheet Tool'],
    lastActivity: 'Idle'
  },
  {
    id: 'agent-deployment',
    name: 'Deployment Agent',
    capability: 'Deployment',
    status: 'ready',
    progress: 0,
    model: 'Local Qwen-2.5-Coder-32B',
    tools: ['Deployment Tool', 'Terminal'],
    lastActivity: 'Idle'
  },
  {
    id: 'agent-communication',
    name: 'Communication Agent',
    capability: 'Communication',
    status: 'ready',
    progress: 0,
    model: 'Local Qwen-2.5-Coder-14B',
    tools: ['Communication Tool'],
    lastActivity: 'Idle'
  },
  {
    id: 'agent-software-dev',
    name: 'Software Agent',
    capability: 'Software Development',
    status: 'ready',
    progress: 0,
    model: 'Local Qwen-2.5-Coder-32B',
    tools: ['Filesystem', 'Terminal', 'Web Browser', 'Code Runner'],
    lastActivity: 'Idle'
  }
];

export const mockActivity: ActivityEvent[] = [
  { id: 'act-1', timestamp: '2026-08-31T09:00:00Z', message: 'Request received: "Create a complete company landing website."', type: 'info', component: 'input' },
  { id: 'act-2', timestamp: '2026-08-31T09:00:02Z', message: 'Perception identified software-development intent.', type: 'info', component: 'perception' },
  { id: 'act-3', timestamp: '2026-08-31T09:00:03Z', message: 'Company knowledge guidelines retrieved from Obsidian Vault.', type: 'success', component: 'memory' },
  { id: 'act-4', timestamp: '2026-08-31T09:00:05Z', message: 'Planner created 8 execution steps with dependencies.', type: 'info', component: 'planner' },
  { id: 'act-5', timestamp: '2026-08-31T09:00:06Z', message: 'Capability Manager mapped tasks to technology requirements and activated CTO Twin.', type: 'success', component: 'orchestrator' },
  { id: 'act-6', timestamp: '2026-08-31T09:00:08Z', message: 'Security check passed: all requested filesystem paths are sandbox approved.', type: 'success', component: 'security' },
  { id: 'act-7', timestamp: '2026-08-31T09:00:10Z', message: 'Frontend Development Agent spawned.', type: 'info', component: 'agent' },
  { id: 'act-8', timestamp: '2026-08-31T09:00:12Z', message: 'Backend Development Agent spawned.', type: 'info', component: 'agent' },
  { id: 'act-9', timestamp: '2026-08-31T09:00:15Z', message: 'Database Agent and Testing Agent spawned.', type: 'info', component: 'agent' },
  { id: 'act-10', timestamp: '2026-08-31T09:01:00Z', message: 'Frontend Agent finished writing code in app router layout.', type: 'info', component: 'agent' },
  { id: 'act-11', timestamp: '2026-08-31T09:01:15Z', message: 'Backend Agent finished POST handler API code.', type: 'info', component: 'agent' },
  { id: 'act-12', timestamp: '2026-08-31T09:01:30Z', message: 'Database Agent successfully ran local schema migrations.', type: 'info', component: 'agent' },
  { id: 'act-13', timestamp: '2026-08-31T09:01:35Z', message: 'Testing Agent initiated test suite execution.', type: 'info', component: 'agent' },
  { id: 'act-14', timestamp: '2026-08-31T09:01:45Z', message: 'Verification failed: Auth middleware fails on missing session token validation test.', type: 'error', component: 'verification' },
  { id: 'act-15', timestamp: '2026-08-31T09:01:47Z', message: 'Reflection Agent triggered: determined root cause is lack of conditional login bypass in development environment.', type: 'warning', component: 'orchestrator' },
  { id: 'act-16', timestamp: '2026-08-31T09:01:49Z', message: 'Planner added Step 9: "Patch auth session checker" and marked step 7 as retrying.', type: 'info', component: 'planner' },
  { id: 'act-17', timestamp: '2026-08-31T09:02:00Z', message: 'Backend Agent applied session validation patch.', type: 'success', component: 'agent' },
  { id: 'act-18', timestamp: '2026-08-31T09:02:10Z', message: 'Testing Agent re-ran validation tests.', type: 'info', component: 'agent' },
  { id: 'act-19', timestamp: '2026-08-31T09:02:14Z', message: 'Verification passed: 100% tests successful.', type: 'success', component: 'verification' },
  { id: 'act-20', timestamp: '2026-08-31T09:02:18Z', message: 'Specialist Agents completed all active threads and terminated successfully.', type: 'success', component: 'orchestrator' },
  { id: 'act-21', timestamp: '2026-08-31T09:02:22Z', message: 'Syncing project status and lesson summaries to memory...', type: 'info', component: 'memory' },
  { id: 'act-22', timestamp: '2026-08-31T09:02:25Z', message: 'Final state successfully saved to Local Obsidian Vault.', type: 'success', component: 'memory' }
];

export const mockMemory: MemoryItem[] = [
  {
    id: 'mem-brand-guide',
    type: 'retrieved',
    title: 'Company Brand Guidelines',
    content: 'Primary Color: #090d16 (Deep Slate Blue). Accent: #6366f1 (Indigo). Font Family: Inter, sans-serif. Logo asset located in assets/brand/logo.svg.',
    usedBy: ['CMO Twin', 'Poster Agent', 'Frontend Agent'],
    timestamp: '2026-08-31T09:00:03Z',
    vault: 'Lordminds Vault'
  },
  {
    id: 'mem-tech-spec',
    type: 'retrieved',
    title: 'Technology Stack Specification',
    content: 'Target deployment supports Node v24 LTS. Standard framework: Next.js App Router (React 19). SQL database choice: SQLite locally path /data/db.sqlite.',
    usedBy: ['CTO Twin', 'Backend Agent', 'Database Agent'],
    timestamp: '2026-08-31T09:00:03Z',
    vault: 'Lordminds Vault'
  },
  {
    id: 'mem-decision-auth',
    type: 'decision',
    title: 'Local Database Submission Routing',
    content: 'Chose SQLite rather than PostgreSQL to minimize external network requirements during self-hosting. Form inputs are serialized directly using parameterized statements.',
    usedBy: ['Backend Agent', 'Database Agent'],
    timestamp: '2026-08-31T09:01:25Z',
    vault: 'Lordminds Vault'
  },
  {
    id: 'mem-lesson-auth-fail',
    type: 'lesson',
    title: 'Dev Session Token Bypass',
    content: 'Lesson: Unit tests fail if test runner has no mocked token. Configured conditional checking of NODE_ENV === "test" in middleware session verification to permit clean unit tests.',
    usedBy: ['Testing Agent', 'Backend Agent'],
    timestamp: '2026-08-31T09:02:25Z',
    vault: 'Lordminds Vault'
  }
];

export const mockModels: Model[] = [
  { id: 'mod-1', name: 'Llama-3-70B-Instruct (Q8_0)', type: 'reasoning', parameters: '70B', quantization: 'Q8_0', vram: '76 GB', status: 'loaded', isLocal: true },
  { id: 'mod-2', name: 'Qwen-2.5-Coder-32B-Instruct (Q6_K)', type: 'coding', parameters: '32B', quantization: 'Q6_K', vram: '28 GB', status: 'loaded', isLocal: true },
  { id: 'mod-3', name: 'Qwen-2.5-Coder-14B-Instruct (Q8_0)', type: 'coding', parameters: '14B', quantization: 'Q8_0', vram: '16 GB', status: 'available', isLocal: true },
  { id: 'mod-4', name: 'Llama-3-8B-Instruct (Q8_0)', type: 'reasoning', parameters: '8B', quantization: 'Q8_0', vram: '9 GB', status: 'loaded', isLocal: true },
  { id: 'mod-5', name: 'Whisper Large V3 (FP16)', type: 'speech-to-text', parameters: '1.5B', quantization: 'FP16', vram: '4.8 GB', status: 'loaded', isLocal: true },
  { id: 'mod-6', name: 'Flux.1-Schnell (FP8)', type: 'image', parameters: '12B', quantization: 'FP8', vram: '14 GB', status: 'available', isLocal: true },
  { id: 'mod-7', name: 'DeepSeek-Coder-6.7B (Q8_0)', type: 'coding', parameters: '6.7B', quantization: 'Q8_0', vram: '8 GB', status: 'loaded', isLocal: true },
  { id: 'mod-8', name: 'Bark TTS (FP16)', type: 'text-to-speech', parameters: '800M', quantization: 'FP16', vram: '2.5 GB', status: 'available', isLocal: true },
  { id: 'mod-9', name: 'BGE-M3 Embeddings', type: 'embeddings', parameters: '560M', quantization: 'FP16', vram: '1.2 GB', status: 'loaded', isLocal: true }
];

export const mockTools: Tool[] = [
  { id: 'tool-browser', name: 'Web Browser', description: 'Automated chromium-based workspace search and interaction interface.', status: 'active', permissionLevel: 'write', agentAccess: ['agent-frontend', 'agent-testing'] },
  { id: 'tool-terminal', name: 'Terminal Shell', description: 'Local system command runner with sandbox isolation constraints.', status: 'active', permissionLevel: 'admin', agentAccess: ['agent-backend', 'agent-testing', 'agent-security', 'agent-deployment'] },
  { id: 'tool-filesystem', name: 'Filesystem IO', description: 'Read, write, edit local file operations inside approved scopes.', status: 'active', permissionLevel: 'write', agentAccess: ['agent-frontend', 'agent-backend', 'agent-poster', 'agent-content'] },
  { id: 'tool-sqlite', name: 'SQLite Manager', description: 'Create local databases, define schemas, and query tables.', status: 'active', permissionLevel: 'write', agentAccess: ['agent-backend', 'agent-database'] },
  { id: 'tool-code-runner', name: 'Code Runner', description: 'Isolate runtime execution environments to execute test suites.', status: 'active', permissionLevel: 'write', agentAccess: ['agent-testing'] },
  { id: 'tool-obsidian', name: 'Obsidian Connector', description: 'Synchronize markdown vaults and pull brand/architectural knowledge.', status: 'active', permissionLevel: 'read', agentAccess: ['twin-cto', 'twin-cmo'] },
  { id: 'tool-img-gen', name: 'Image Generator', description: 'Text to image models interface (Stable Diffusion / Flux).', status: 'active', permissionLevel: 'write', agentAccess: ['agent-image', 'agent-poster', 'agent-logo'] },
  { id: 'tool-tts', name: 'TTS Voice Cloning', description: 'Clones voice parameters and generates read-aloud task reports.', status: 'active', permissionLevel: 'write', agentAccess: ['agent-audio-gen', 'agent-voice-clone'] }
];
