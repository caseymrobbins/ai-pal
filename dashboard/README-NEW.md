# AI-Pal Dashboard

A comprehensive React + TypeScript web dashboard for the AI-Pal system, providing real-time visualization of agency metrics, FFE goal tracking, system monitoring, and more.

## 🚀 Quick Start

### Prerequisites
- Node.js 20.19+ or 22.12+
- npm 9+

### Installation

```bash
cd dashboard
npm install
```

### Development

```bash
npm run dev
```

The dashboard will be available at `http://localhost:5173` with hot module reloading.

### Production Build

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory (~760KB gzipped).

## 📊 Features

### Implemented
- **🔐 Authentication**: Login screen with JWT token support
- **📈 Agency Metrics (ARI)**: 7-dimensional radar chart visualization with real-time tracking
- **🎯 FFE Goals**: Goal creation, progress tracking, and momentum loop visualization
- **🏥 System Health**: Service status monitoring, performance metrics, and uptime tracking
- **📋 Audit Logs**: 25+ event types with filtering and search capabilities
- **💡 Personality Profile**: Strength discovery and development tracking (stub)
- **📚 Learn-by-Teaching**: Interactive learning mode (stub)
- **🎨 Responsive Design**: Works seamlessly on mobile, tablet, and desktop

## 🏗️ Deployment

### Option 1: Integrated with FastAPI

```python
from fastapi import FastAPI
from src.dashboard_integration import integrate_dashboard

app = FastAPI()
if integrate_dashboard(app):
    print("Dashboard available at http://localhost:8000/dashboard")
```

### Option 2: Standalone

Deploy the `dist/` folder to any static hosting or use Docker.

### Docker

```bash
docker build -t ai-pal-dashboard:latest .
docker run -p 3000:3000 ai-pal-dashboard:latest
```

## 🔌 API Integration

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete deployment and API integration guide.

## 📁 Project Structure

```
dashboard/
├── src/
│   ├── api/client.ts          # API client
│   ├── components/            # Dashboard components
│   ├── store/store.ts         # State management
│   ├── App.tsx               # Main app
│   └── index.css             # Tailwind styles
├── dist/                      # Production build
├── Dockerfile                 # Container setup
└── package.json
```

## 📈 Build Output

- CSS: ~23 KB gzipped
- JS: ~234 KB gzipped
- Total: ~258 KB gzipped

## 🌍 Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers

## 📚 Resources

- [React](https://react.dev)
- [TypeScript](https://www.typescriptlang.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Vite](https://vite.dev/)
- [Zustand](https://github.com/pmndrs/zustand)
