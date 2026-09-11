import React, { useState } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { PageId } from './components/layout/Sidebar';
import { useRunExecution } from './hooks/useRunExecution';
import { ArchitecturePage } from './pages/ArchitecturePage';
import { AuditPage } from './pages/AuditPage';
import { EvidencePage } from './pages/EvidencePage';
import { KnowledgePage } from './pages/KnowledgePage';
import { LiveRunPage } from './pages/LiveRunPage';
import { NewWorkPage } from './pages/NewWorkPage';
import { OverviewPage } from './pages/OverviewPage';
import { RunsHistoryPage } from './pages/RunsHistoryPage';
import { SecurityPage } from './pages/SecurityPage';
import { WorkforcePage } from './pages/WorkforcePage';
import { WorkflowRun, WorkRequest } from './types';

export function App() {
  const [currentPage, setCurrentPage] = useState<PageId>('overview');

  const {
    currentRun,
    isExecuting,
    selectedStageIndex,
    setSelectedStageIndex,
    executionMode,
    setExecutionMode,
    backendHealth,
    executionError,
    startRun,
    loadRun,
    triggerControlledFailure,
    triggerRepeatedFailure,
  } = useRunExecution('RUN-001');

  const handleStartRun = (
    request: WorkRequest,
    type: 'STANDARD' | 'CONTROLLED_FAILURE' | 'BOUNDED_FAILURE' | 'STRATEGIC_TWIN' = 'STANDARD'
  ) => {
    startRun(request, type);
    setCurrentPage('live-run');
  };

  const handleSelectRun = (run: WorkflowRun) => {
    loadRun(run);
    setCurrentPage('live-run');
  };

  return (
    <AppLayout
      currentPage={currentPage}
      onNavigate={setCurrentPage}
      activeRunId={currentRun?.runId}
      isRunActive={isExecuting}
      executionMode={executionMode}
      onToggleMode={setExecutionMode}
    >
      {currentPage === 'overview' && (
        <OverviewPage
          onNavigate={setCurrentPage}
          onStartRun={handleStartRun}
          onSelectRun={handleSelectRun}
        />
      )}

      {currentPage === 'new-work' && (
        <NewWorkPage
          onNavigate={setCurrentPage}
          onStartRun={handleStartRun}
          executionMode={executionMode}
          onToggleMode={setExecutionMode}
        />
      )}

      {currentPage === 'live-run' && (
        <LiveRunPage
          run={currentRun}
          isExecuting={isExecuting}
          selectedStageIndex={selectedStageIndex}
          onSelectStageIndex={setSelectedStageIndex}
          onTriggerControlledFailure={triggerControlledFailure}
          onTriggerRepeatedFailure={triggerRepeatedFailure}
          onNavigate={setCurrentPage}
          executionMode={executionMode}
          executionError={executionError}
          onToggleMode={setExecutionMode}
        />
      )}

      {currentPage === 'runs' && (
        <RunsHistoryPage
          onNavigate={setCurrentPage}
          onSelectRun={handleSelectRun}
        />
      )}

      {currentPage === 'workforce' && (
        <WorkforcePage
          onNavigate={setCurrentPage}
          onSelectRun={handleSelectRun}
        />
      )}

      {currentPage === 'knowledge' && <KnowledgePage />}

      {currentPage === 'evidence' && <EvidencePage />}

      {currentPage === 'audit' && <AuditPage />}

      {currentPage === 'security' && <SecurityPage />}

      {currentPage === 'architecture' && <ArchitecturePage />}
    </AppLayout>
  );
}

export default App;
