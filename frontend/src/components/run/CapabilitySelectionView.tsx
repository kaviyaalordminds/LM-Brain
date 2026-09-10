import React from 'react';
import { ArrowRight, Bot, CheckCircle2, ShieldCheck, Tag } from 'lucide-react';
import { Badge } from '../common/Badge';
import { Card } from '../common/Card';

interface CapabilitySelectionViewProps {
  selectedSpecialists?: Record<string, string>;
}

export const CapabilitySelectionView: React.FC<CapabilitySelectionViewProps> = ({
  selectedSpecialists,
}) => {
  const capabilityMap: Record<string, { specialistName: string; reason: string; category: string }> = {
    web_development: {
      specialistName: 'Web Development Specialist',
      reason: 'Authoritative capability registry match for HTML/CSS/React authoring',
      category: 'Engineering',
    },
    software_development: {
      specialistName: 'Software Development Specialist',
      reason: 'Sandbox workspace creation & file lifecycle management',
      category: 'Engineering',
    },
    file_operations: {
      specialistName: 'Software Development Specialist',
      reason: 'Controlled Files API handler integration',
      category: 'System Service',
    },
    build_validation: {
      specialistName: 'Build & Test Specialist',
      reason: 'Controlled command execution & bundle verification',
      category: 'QA / Verification',
    },
    content_creation: {
      specialistName: 'Content Creation Specialist',
      reason: 'Marketing narrative & copy synthesis matching brand standards',
      category: 'Marketing / Copy',
    },
    poster_design: {
      specialistName: 'Poster Specialist',
      reason: 'Visual marketing poster layout & vector export',
      category: 'Creative / Visual',
    },
    graphic_design: {
      specialistName: 'Graphic Design Specialist',
      reason: 'UI vector illustrations & brand asset composition',
      category: 'Creative / Visual',
    },
    ppt: {
      specialistName: 'PPT / Presentation Specialist',
      reason: 'Executive slide deck authoring',
      category: 'Documents / Office',
    },
  };

  const selectedEntries = Object.entries(selectedSpecialists || {});

  if (selectedEntries.length === 0) {
    return (
      <Card
        title="Capability Selection & Specialist Registry"
        subtitle="Authoritative capability matching via SpecialistRegistry"
        icon={<Bot className="w-4 h-4 text-indigo-400" />}
      >
        <div className="py-6 text-center text-xs text-slate-500 font-mono">
          Awaiting capability selection phase to resolve specialist assignments...
        </div>
      </Card>
    );
  }

  return (
    <Card
      title="Authoritative Capability Matching & Specialist Resolution"
      subtitle="Registry-matched workers — Dynamic allocation based on declared plan capabilities"
      icon={<Bot className="w-4 h-4 text-indigo-400" />}
      badge={<Badge variant="success" size="sm" dot>REGISTRY: ACTIVE</Badge>}
    >
      <div className="space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {selectedEntries.map(([capKey, specId]) => {
            const info = capabilityMap[capKey] || {
              specialistName: specId,
              reason: 'Capability match in registry',
              category: 'Workforce Specialist',
            };

            return (
              <div
                key={capKey}
                className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-indigo-300 font-semibold flex items-center gap-1.5">
                    <Tag className="w-3.5 h-3.5 text-indigo-400" />
                    {capKey}
                  </span>
                  <Badge variant="default" size="sm">{info.category}</Badge>
                </div>

                <div className="flex items-center gap-2 text-slate-300 font-medium">
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span className="text-white font-semibold">{info.specialistName}</span>
                </div>

                <div className="text-[11px] text-slate-400 font-mono bg-[#0B0F19] p-2 rounded border border-slate-800/80">
                  <span className="text-slate-500">Reason: </span>
                  {info.reason}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
};
