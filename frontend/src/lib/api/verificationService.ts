import { VerificationResult } from '../types';
import { mockProjects } from '../mock';

export const verificationService = {
  getVerificationResults: async (): Promise<VerificationResult[]> => {
    const results = mockProjects
      .filter(p => p.verificationResult)
      .map(p => p.verificationResult!);
    return new Promise((resolve) => setTimeout(() => resolve(results), 100));
  },
  runVerification: async (projectId: string): Promise<VerificationResult> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const result: VerificationResult = {
          id: `ver-${projectId}`,
          taskName: `Verify ${projectId}`,
          status: 'passed',
          timestamp: new Date().toISOString(),
          logs: [
            '[Testing] Initializing security checks...',
            '[Testing] Unit tests verified successfully.',
            '[Testing] Final state checkpoint checked.'
          ],
          duration: '3.1s'
        };
        resolve(result);
      }, 1000);
    });
  }
};
export type { VerificationResult };
