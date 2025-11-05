# AI-Pal Dashboard Deployment Guide

## Overview

The AI-Pal Dashboard is a React + TypeScript application that provides real-time visualization of agency metrics, goal tracking, and system monitoring for the AI-Pal system.

## Development

### Prerequisites
- Node.js 18+
- npm 9+

### Setup

```bash
cd dashboard
npm install
```

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000
```

### Running Locally

```bash
npm run dev
```

The dashboard will be available at `http://localhost:5173`

### Building for Production

```bash
npm run build
```

This creates a production build in the `dist/` directory.

## Deployment Options

### Option 1: Integrated with FastAPI (Recommended for Production)

Deploy the dashboard directly from the FastAPI server:

1. Build the dashboard:
```bash
npm run build
```

2. Copy the build output to your FastAPI static directory:
```bash
cp -r dist/* /path/to/ai-pal/static/
```

3. Update FastAPI to serve the dashboard:

```python
# In your FastAPI app initialization
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Serve static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

# This serves index.html for all non-API routes
```

The dashboard will be available at `http://localhost:8000/dashboard`

### Option 2: Standalone SPA Deployment

Deploy the built dashboard as a standalone application:

1. Build the dashboard:
```bash
npm run build
```

2. Deploy the `dist/` directory to your hosting:

**Using Nginx:**
```nginx
server {
    listen 3000;
    server_name localhost;

    location / {
        root /path/to/dashboard/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }

    location /ws {
        proxy_pass ws://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Using Node/Express:**
```javascript
import express from 'express';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const app = express();
const __dirname = dirname(fileURLToPath(import.meta.url));

app.use(express.static('dist'));
app.get('*', (req, res) => {
  res.sendFile('dist/index.html', { root: __dirname });
});

app.listen(3000);
```

### Option 3: Docker Deployment

**Dockerfile for integrated deployment:**

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM python:3.11
WORKDIR /app
COPY --from=builder /app/dist /app/static
# Continue with FastAPI setup...
```

**Dockerfile for standalone deployment:**

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
```

## Features

### Currently Implemented
- **Login/Authentication**: Mock authentication (requires backend integration)
- **Navigation**: Sidebar with collapsible menu
- **ARI Metrics**: 7-dimensional agency visualization with radar chart
- **Overview Tab**: Quick system status and metrics
- **View Management**: Tab-based view switching

### Coming Soon
- **FFE Goals**: Goal tracking and progress visualization
- **System Health**: Real-time service status monitoring
- **Personality**: Strength profile and personality insights
- **Learn-by-Teaching**: Teaching mode interface
- **Audit Logs**: Detailed audit trail viewing
- **Real-time Updates**: WebSocket integration for live data

## API Integration

The dashboard expects the following API endpoints:

### Required Endpoints
- `GET /api/health` - System health check
- `GET /api/metrics` - Prometheus metrics
- `GET /api/users/{userId}/ari` - ARI metrics
- `GET /api/users/{userId}/goals` - User goals
- `GET /api/users/{userId}/profile` - User profile
- `GET /api/users/{userId}/personality` - Personality data
- `GET /api/users/{userId}/audit-logs` - Audit logs
- `WS /ws/dashboard/{userId}` - WebSocket for real-time updates

## Performance

### Build Optimization
- Minified and tree-shaken production builds
- Code splitting for faster initial load
- Asset optimization with Vite

### Runtime Optimization
- Component lazy loading
- Efficient re-renders with React hooks
- Local state management with Zustand
- Caching of API responses

## Troubleshooting

### CORS Issues
If you see CORS errors, ensure the FastAPI/backend is configured with proper CORS headers:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Connection Issues
1. Verify the `VITE_API_URL` environment variable is correct
2. Check that the backend API is running and accessible
3. Use browser DevTools to inspect network requests

### WebSocket Connection Issues
1. Ensure WebSocket is properly configured in proxy/firewall
2. Check that `VITE_WS_URL` is correctly set
3. Verify backend WebSocket endpoint is running

## Production Checklist

- [ ] Update `.env` with production API URLs
- [ ] Run production build: `npm run build`
- [ ] Test all dashboard features against production API
- [ ] Configure HTTPS/TLS certificates
- [ ] Set up proper authentication/JWT handling
- [ ] Configure CORS for production domain
- [ ] Set up monitoring and error tracking
- [ ] Test responsive design on multiple devices
- [ ] Verify accessibility (a11y) compliance
- [ ] Set up CDN for static assets (optional)

## Support

For issues or questions about the dashboard, check:
1. Browser console for error messages
2. Network tab for failed API calls
3. Backend logs for API errors
4. Dashboard GitHub issues
