import React from 'react';
import {
  ExecutiveTwin,
  OrchestrationStatus,
  StepExecutionRecord,
  WorkflowStage,
} from '../../types';
import { AutonomousExecutionPipeline } from '../workforce/AutonomousExecutionPipeline';

export interface WorkflowPipelineProps {
  stages: WorkflowStage[];
  currentStageIndex: number;
  onSelectStage?: (index: number) => void;
  selectedStageIndex?: number;
  executiveTwin?: ExecutiveTwin;
  selectedSpecialists?: Record<string, string>;
  specialistExecutions?: StepExecutionRecord[];
  isExecuting?: boolean;
  overallStatus?: OrchestrationStatus;
}

export const WorkflowPipeline: React.FC<WorkflowPipelineProps> = ({
  stages,
  currentStageIndex,
  onSelectStage,
  selectedStageIndex,
  executiveTwin,
  selectedSpecialists,
  specialistExecutions,
  isExecuting,
  overallStatus,
}) => {
  return (
    <AutonomousExecutionPipeline
      stages={stages}
      currentStageIndex={currentStageIndex}
      selectedStageIndex={selectedStageIndex}
      onSelectStage={onSelectStage}
      executiveTwin={executiveTwin}
      selectedSpecialists={selectedSpecialists}
      specialistExecutions={specialistExecutions}
      isExecuting={isExecuting}
      overallStatus={overallStatus}
    />
  );
};
