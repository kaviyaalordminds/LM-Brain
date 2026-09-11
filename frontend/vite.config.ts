import { defineConfig, Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');

/**
 * Locate the active or available Python interpreter.
 */
function findPythonExecutable(): string {
  if (process.env.PYTHON_PATH && fs.existsSync(process.env.PYTHON_PATH)) {
    return process.env.PYTHON_PATH;
  }
  if (process.env.VIRTUAL_ENV) {
    const venvPy = process.platform === 'win32'
      ? path.join(process.env.VIRTUAL_ENV, 'Scripts', 'python.exe')
      : path.join(process.env.VIRTUAL_ENV, 'bin', 'python');
    if (fs.existsSync(venvPy)) {
      return venvPy;
    }
  }

  // Check repo-local venv / virtualenvs
  const candidates = [
    path.join(repoRoot, 'venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python'),
    path.join(repoRoot, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python'),
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) {
      return c;
    }
  }

  return 'python';
}

/**
 * Local-Only Development Bridge Plugin.
 * Connects the Vite development server to the existing Python LocalRunner.
 * Binds strictly to localhost. Does NOT implement an arbitrary shell or REST server.
 */
function localDevelopmentBridge(): Plugin {
  return {
    name: 'local-development-bridge',
    configureServer(server) {
      // 1. Health check endpoint
      server.middlewares.use('/api/local-health', (req, res) => {
        if (req.method !== 'GET') {
          res.statusCode = 405;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ error: 'Method not allowed. GET required.' }));
          return;
        }

        res.setHeader('Content-Type', 'application/json');
        const pythonExe = findPythonExecutable();

        const pyProc = spawn(pythonExe, ['-c', 'import sys; print(sys.version)'], {
          cwd: repoRoot,
        });

        pyProc.on('error', () => {
          res.statusCode = 503;
          res.end(JSON.stringify({
            status: 'unavailable',
            pythonAvailable: false,
            message: 'Python interpreter not found. Demo Mode is available.',
          }));
        });

        pyProc.on('close', (code) => {
          if (code === 0) {
            res.statusCode = 200;
            res.end(JSON.stringify({
              status: 'ok',
              pythonAvailable: true,
              pythonExecutable: pythonExe,
              repoRoot,
              bridgeMode: 'LOCAL_DEVELOPMENT_ONLY',
              backend: 'LocalRunner -> MasterOrchestrator -> AutonomousControlLoop',
            }));
          } else {
            res.statusCode = 503;
            res.end(JSON.stringify({
              status: 'unavailable',
              pythonAvailable: false,
              message: 'Python check failed. Demo Mode is available.',
            }));
          }
        });
      });

      // 2. Local Run execution endpoint
      server.middlewares.use('/api/local-run', async (req, res) => {
        if (req.method !== 'POST') {
          res.statusCode = 405;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ error: 'Method not allowed. POST required.' }));
          return;
        }

        // Host security check - localhost only
        const host = req.headers.host || '';
        if (!host.startsWith('localhost:') && !host.startsWith('127.0.0.1:') && host !== 'localhost' && host !== '127.0.0.1') {
          res.statusCode = 403;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ error: 'FORBIDDEN: Local bridge binds exclusively to localhost.' }));
          return;
        }

        let body = '';
        req.on('data', (chunk) => {
          body += chunk;
          if (body.length > 25000) {
            res.statusCode = 413;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({ error: 'PAYLOAD_TOO_LARGE', message: 'Request exceeds size limit.' }));
            req.destroy();
          }
        });

        req.on('end', () => {
          try {
            const data = JSON.parse(body || '{}');
            const goal = (data.request || data.userGoal || '').trim();

            if (!goal) {
              res.statusCode = 400;
              res.setHeader('Content-Type', 'application/json');
              res.end(JSON.stringify({ error: 'INVALID_REQUEST', message: 'Missing required "request" or "userGoal" string.' }));
              return;
            }

            if (goal.length > 10000) {
              res.statusCode = 400;
              res.setHeader('Content-Type', 'application/json');
              res.end(JSON.stringify({ error: 'INVALID_REQUEST', message: 'Request exceeds 10,000 character maximum.' }));
              return;
            }

            const pythonExe = findPythonExecutable();

            // Invoke existing LocalRunner in --json mode
            const pyProcess = spawn(pythonExe, ['-m', 'executive_twins.local_runner', '--json', goal], {
              cwd: repoRoot,
              env: { ...process.env, PYTHONUNBUFFERED: '1' },
            });

            let stdoutData = '';
            let stderrData = '';

            pyProcess.stdout.on('data', (chunk) => {
              stdoutData += chunk.toString();
            });

            pyProcess.stderr.on('data', (chunk) => {
              stderrData += chunk.toString();
            });

            pyProcess.on('error', (err) => {
              res.statusCode = 503;
              res.setHeader('Content-Type', 'application/json');
              res.end(JSON.stringify({
                error: 'LOCAL_BACKEND_UNAVAILABLE',
                message: `Failed to spawn Python LocalRunner: ${err.message}. Demo Mode is available.`,
              }));
            });

            pyProcess.on('close', (code) => {
              res.setHeader('Content-Type', 'application/json');
              try {
                const jsonStart = stdoutData.indexOf('{');
                const jsonEnd = stdoutData.lastIndexOf('}');
                if (jsonStart !== -1 && jsonEnd !== -1 && jsonEnd >= jsonStart) {
                  const jsonStr = stdoutData.substring(jsonStart, jsonEnd + 1);
                  const parsed = JSON.parse(jsonStr);
                  res.statusCode = 200;
                  res.end(JSON.stringify(parsed));
                } else {
                  res.statusCode = 500;
                  res.end(JSON.stringify({
                    error: 'INVALID_BACKEND_RESPONSE',
                    message: 'LocalRunner did not produce structured JSON.',
                    details: stdoutData || stderrData,
                  }));
                }
              } catch (parseErr: any) {
                res.statusCode = 500;
                res.end(JSON.stringify({
                  error: 'JSON_PARSE_ERROR',
                  message: `Failed to parse LocalRunner output: ${parseErr.message}`,
                  details: stdoutData || stderrData,
                }));
              }
            });
          } catch (e: any) {
            res.statusCode = 400;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({ error: 'INVALID_JSON', message: e.message }));
          }
        });
      });
    },
  };
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), localDevelopmentBridge()],
  server: {
    host: '127.0.0.1',
    port: 3000,
    open: false,
  },
});
