# Threat_Ops.ai Frontend

Cyber-Resilient Infrastructure Platform - Security Operations Dashboard

## Overview

Real-time security monitoring and response dashboard built with React, Tailwind CSS, and glassmorphism design principles.

## Tech Stack

- **React 18** + Vite
- **Tailwind CSS** (custom dark-mode theme)
- **socket.io-client** (real-time events)
- **Recharts** (data visualization)
- **Framer Motion** (animations)

## Quick Start

### Prerequisites
- Node.js 18+
- npm 9+

### Installation

```bash
cd /Users/aryan/Developer/Threat_Ops.ai/frontend
npm install
```

### Development (Mock Mode)

```bash
# Run with mock data (no backend required)
VITE_USE_MOCK=true npm run dev
```

Open http://localhost:5173

### Development (Live Backend)

```bash
npm run dev
```

### Production Build

```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Route-level views
│   ├── services/
│   │   ├── api.js      # HTTP calls (mock-aware)
│   │   └── socket.js   # WebSocket logic (mock-aware)
│   ├── hooks/          # Custom React hooks
│   ├── mock/
│   │   └── data.js     # Sample data for demos
│   ├── utils/          # Helpers
│   ├── App.jsx         # Main dashboard layout
│   ├── main.jsx        # Entry point
│   └── index.css       # Design system
├── tailwind.config.js  # Theme configuration
├── vite.config.js      # Build configuration
└── package.json
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_USE_MOCK` | `false` | Enable mock data mode |
| `VITE_API_URL` | `http://localhost:3001/api` | Backend API URL |
| `VITE_SOCKET_URL` | `http://localhost:3001` | WebSocket server URL |

## Design System

### Colors
- **Background**: Deep navy (`#0a0e1a` → `#1e293b`)
- **Normal**: Muted green (`#22c55e`)
- **Warning**: Amber (`#f59e0b`)
- **Critical**: Red (`#ef4444`)

### Components
- `.glass-panel` - Translucent glassmorphism container
- `.glass-card` - Smaller glassmorphism card
- `.status-badge` - Status indicator (normal/warning/critical)
- `.btn-primary` / `.btn-danger` / `.btn-ghost` - Button styles

## Acceptance Tests

After running `npm run dev`, verify:

- [ ] Dev server starts on http://localhost:5173
- [ ] Dark navy background is visible
- [ ] Sidebar with navigation items appears on left
- [ ] Header shows "Security Operations" title
- [ ] Clock updates every second
- [ ] Four metric cards display (Active Devices, Events/min, Active Alerts, Blocked Threats)
- [ ] Glassmorphism panels have translucent blur effect
- [ ] No errors in browser console
- [ ] Page title shows "Threat_Ops.ai"

## Next Modules

After verifying this skeleton, the following modules can be added:
1. Alert components (AlertCard, AlertPanel, AlertDetail)
2. Device components (DeviceCard, DeviceList, DeviceMap)
3. Telemetry charts (LiveChart, HistoricalChart)
4. Playbook components (PlaybookList, PlaybookRunner)
5. Response action modals
