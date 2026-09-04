# Memory Agent — Operational Control Plane UI

A dedicated production-grade developer and operations console for the **Memory Agent** service.

---

## 🎯 Architecture
```
MEMORY AGENT UI (Port 3002)
        ↓  HTTP / REST
EXISTING MEMORY AGENT API (Port 8001)
        ↓  Local / BM25 Adapter
EXISTING OBSIDIAN KNOWLEDGE BASE (Source of Truth)
```

## 🚀 Running the Console
```bash
cd memory-agent-ui
npm install
npm run dev
```
Open [http://localhost:3002](http://localhost:3002) in your browser.
