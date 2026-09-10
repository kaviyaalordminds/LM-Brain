import React from 'react';
import { DemoBanner } from '../common/DemoBanner';
import { Header } from './Header';
import { PageId, Sidebar } from './Sidebar';

interface AppLayoutProps {
  children: React.ReactNode;
  currentPage: PageId;
  onNavigate: (page: PageId) => void;
  activeRunId?: string;
  isRunActive?: boolean;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  currentPage,
  onNavigate,
  activeRunId,
  isRunActive,
}) => {
  return (
    <div className="flex flex-col h-screen bg-[#0B0F19] text-slate-100 overflow-hidden font-sans">
      {/* Enterprise Demo Banner */}
      <DemoBanner />

      <div className="flex flex-1 overflow-hidden">
        {/* Persistent Global Sidebar */}
        <Sidebar
          currentPage={currentPage}
          onNavigate={onNavigate}
          activeRunId={activeRunId}
          isRunActive={isRunActive}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-[#0B0F19]">
          <Header
            currentPage={currentPage}
            activeRunId={activeRunId}
            onNavigate={onNavigate}
          />
          <main className="flex-1 overflow-y-auto p-6 md:p-8">
            <div className="max-w-7xl mx-auto space-y-6">{children}</div>
          </main>
        </div>
      </div>
    </div>
  );
};
