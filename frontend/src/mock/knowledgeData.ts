import { ObsidianDocument } from '../types';

export const mockObsidianKnowledge: ObsidianDocument[] = [
  {
    documentId: 'doc_company_profile',
    vaultPath: 'company_knowledge/default/company_profile.md',
    title: 'NovaPulse Robotics — Authoritative Profile',
    content: `# NovaPulse Robotics
Authoritative Corporate Knowledge Base (Company Obsidian Vault)

## Overview
NovaPulse Robotics provides next-generation autonomous warehouse robotics, fleet orchestration platforms, and high-reliability industrial automation solutions.

## Core Products & Services
1. Fleet Orchestrator 4.0: Distributed multi-agent mission allocation and real-time path routing.
2. Autonomous AMR-500: Heavy-payload omnidirectional automated mobile robot with LiDAR SLAM.
3. Cloud Telemetry & Analytics API: Real-time telemetry, predictive maintenance, and fleet health monitoring.

## Contact Information
- Inquiries: contact@novapulse.io
- Security & Compliance: security@novapulse.io
- HQ: Innovation Park, Cyber Hub East
`,
    facts: [
      {
        statement: 'Company name is NovaPulse Robotics',
        state: 'FACT',
        source: 'obsidian_vault:company_profile.md',
        confidence: 1.0,
      },
      {
        statement: 'Company description: Autonomous warehouse robotics and fleet orchestration solutions',
        state: 'FACT',
        source: 'obsidian_vault:company_profile.md',
        confidence: 1.0,
      },
      {
        statement: 'Products: Fleet Orchestrator 4.0, Autonomous AMR-500, Cloud Telemetry API',
        state: 'FACT',
        source: 'obsidian_vault:company_profile.md',
        confidence: 1.0,
      },
      {
        statement: 'Primary contact email is contact@novapulse.io',
        state: 'FACT',
        source: 'obsidian_vault:company_profile.md',
        confidence: 1.0,
      },
      {
        statement: 'Security authority email is security@novapulse.io',
        state: 'FACT',
        source: 'obsidian_vault:company_profile.md',
        confidence: 1.0,
      },
    ],
    confidence: 1.0,
    lastModified: '2026-09-08T10:15:00Z',
  },
  {
    documentId: 'doc_branding_guidelines',
    vaultPath: 'company_knowledge/branding/brand_standards.md',
    title: 'Brand Standards & Design Architecture',
    content: `# Brand Standards
- Primary Palette: Slate (#0F172A), Deep Indigo (#4338CA), Electric Cyan (#06B6D4)
- Typography: Inter for UI, JetBrains Mono for system metrics and telemetry
- Tone: Professional, authoritative, industrial-grade, safety-critical
`,
    facts: [
      {
        statement: 'Primary brand palette uses Slate (#0F172A) and Indigo (#4338CA)',
        state: 'FACT',
        source: 'obsidian_vault:brand_standards.md',
        confidence: 1.0,
      },
      {
        statement: 'Tone must be professional, authoritative, and safety-critical',
        state: 'FACT',
        source: 'obsidian_vault:brand_standards.md',
        confidence: 1.0,
      },
    ],
    confidence: 1.0,
    lastModified: '2026-09-01T14:20:00Z',
  },
  {
    documentId: 'doc_security_policy',
    vaultPath: 'company_knowledge/compliance/security_governance.md',
    title: 'Autonomous System Security Governance',
    content: `# Security Governance Rules
- All file operations must be restricted to the allocated workspace directory.
- Direct shell access is strictly blocked; only allowlisted commands via Controlled Command Executor are permitted.
- Executive Twins are conditional strategic decision-makers and must NEVER execute system code directly.
- Obsidian Vault is the single authoritative source of truth. External reasoning cannot overwrite vault facts without validation.
`,
    facts: [
      {
        statement: 'File operations are strictly bound to isolated workspaces',
        state: 'FACT',
        source: 'obsidian_vault:security_governance.md',
        confidence: 1.0,
      },
      {
        statement: 'Arbitrary shell execution is forbidden; allowlisted execution only',
        state: 'FACT',
        source: 'obsidian_vault:security_governance.md',
        confidence: 1.0,
      },
      {
        statement: 'Obsidian is authoritative source of truth; writeback requires empirical verification',
        state: 'FACT',
        source: 'obsidian_vault:security_governance.md',
        confidence: 1.0,
      },
    ],
    confidence: 1.0,
    lastModified: '2026-09-05T09:00:00Z',
  },
];
