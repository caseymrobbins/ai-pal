# Dashboard API Integration Guide

## Overview

The AI-Pal Dashboard is fully integrated with the AI-Pal backend API. This guide provides detailed information about how the dashboard communicates with the backend and how to configure it for your environment.

## Backend API Details

**Base URL**: `http://localhost:8000/api` (development)
**Authentication**: Bearer token via `Authorization: Bearer <token>` header
**Content-Type**: `application/json`

### Key Endpoints

See the AI-Pal backend documentation for complete endpoint details:
- **Health Check**: `GET /health`
- **User Profile**: `GET /users/{userId}/profile`
- **ARI Metrics**: `GET /users/{userId}/ari`
- **FFE Goals**: `GET /users/{userId}/goals`
- **Audit Logs**: `GET /users/{userId}/audit-logs`
- And 20+ more endpoints

## API Client Architecture

### File: `src/api/client.ts`

The dashboard uses a centralized `ApiClient` class that:

1. **Manages Authentication**
   - Stores Bearer token securely
   - Automatically injects token in all requests
   - Handles 401 responses by redirecting to login
   - Persists token in localStorage for session persistence

2. **Provides Type-Safe Methods**
   - Organized by domain (Users, ARI, FFE, Social, etc.)
   - Full TypeScript support with interfaces
   - Automatic error handling and response parsing

3. **Handles Request/Response**
   - Request interceptor for token injection
   - Response interceptor for error handling
   - Timeout management (30 seconds)
   - CORS handling

### Usage Example

```typescript
import { getApiClient } from '@/api/client';

// Get API client singleton
const client = getApiClient();

// Fetch user's ARI metrics
const ariMetrics = await client.getARIMetrics(userId);

// Get user's goals
const goals = await client.getGoals(userId);

// Create a new goal
const newGoal = await client.createGoal(userId, {
  title: "Learn TypeScript",
  description: "Master TypeScript for better development",
  value: 8
});
```

## Available API Methods

### System Endpoints

```typescript
// Health check
const health = await client.getHealth();

// Prometheus metrics
const metrics = await client.getMetrics();
```

### User Management

```typescript
// Get user profile
const profile = await client.getUserProfile(userId);

// Update user profile
await client.updateUserProfile(userId, {
  name: "New Name",
  bio: "Updated bio"
});
```

### ARI Metrics

```typescript
// Get current ARI metrics
const ari = await client.getARIMetrics(userId);
// Returns: { overall_score, dimensions: {...}, timestamp }

// Get ARI history (last 30 days)
const history = await client.getARIHistory(userId, 30);
```

### FFE Goals

```typescript
// Get all goals (optionally filtered by status)
const goals = await client.getGoals(userId);
const activeGoals = await client.getGoals(userId, 'PENDING');

// Get single goal
const goal = await client.getGoal(userId, goalId);

// Create goal
const newGoal = await client.createGoal(userId, {
  title: "Complete project",
  description: "Finish the dashboard",
  value: 9
});

// Update goal
await client.updateGoal(userId, goalId, {
  title: "Updated title",
  value: 10
});

// Plan a goal (FFE scoping)
await client.planGoal(userId, goalId);

// Complete a goal
await client.completeGoal(userId, goalId);
```

### Personality Discovery

```typescript
// Get personality profile
const personality = await client.getPersonality(userId);

// Start discovery process
const discovery = await client.startPersonalityDiscovery(userId);

// Update strengths
await client.updateStrengths(userId, [
  "Problem Solving",
  "Communication",
  "Leadership"
]);
```

### Teaching/Protégé Mode

```typescript
// Get available topics
const topics = await client.getTeachingTopics(userId);

// Start teaching session
const session = await client.startTeachingSession(userId, topicId);

// Submit response to lesson
await client.submitTeachingResponse(userId, sessionId, "My response here");

// Get evaluation
const evaluation = await client.evaluateTeachingSession(userId, sessionId);
```

### Social Features

```typescript
// Get user's groups
const groups = await client.getSocialGroups(userId);

// Create new group
const group = await client.createGroup(userId, {
  name: "AI Learning Group",
  description: "Learn AI together"
});

// Share a win
await client.shareWin(userId, {
  title: "Completed goal",
  description: "Successfully finished project",
  goalId: "goal-123"
});

// Get group feed
const feed = await client.getGroupFeed(groupId);
```

### Audit & Security

```typescript
// Get audit logs
const logs = await client.getAuditLogs(userId, limit = 100, offset = 0);

// Get security alerts
const alerts = await client.getSecurityAlerts(userId);
```

### Patch & Appeals

```typescript
// Get pending patches
const patches = await client.getPatchRequests(userId);

// Submit a patch
const patch = await client.submitPatch(userId, {
  title: "Bug fix",
  description: "Fixed login issue"
});

// Approve a patch
await client.approvePatch(userId, patchId);

// Get appeals
const appeals = await client.getAppeals(userId);

// Submit appeal
const appeal = await client.submitAppeal(userId, {
  title: "Appeal decision",
  description: "Request for override"
});
```

### Chat

```typescript
// Send chat message
const response = await client.chat("What are my agency metrics?", {
  userId: userId
});
```

## Configuration

### Environment Variables

Create a `.env` file in the dashboard root:

```env
# API Configuration
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000

# Optional: API timeout (ms)
VITE_API_TIMEOUT=30000
```

### Development vs Production

**Development** (localhost):
```env
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000
```

**Production** (cloud):
```env
VITE_API_URL=https://api.ai-pal.com/api
VITE_WS_URL=wss://api.ai-pal.com
```

## Error Handling

The API client includes comprehensive error handling:

```typescript
try {
  const goals = await client.getGoals(userId);
} catch (error) {
  if (error.response?.status === 401) {
    // Unauthorized - token invalid
    // Automatically redirected to login
  } else if (error.response?.status === 404) {
    // Not found
    console.error('User not found');
  } else if (error.code === 'ECONNABORTED') {
    // Timeout (30 seconds)
    console.error('Request timeout');
  } else {
    console.error('API error:', error.message);
  }
}
```

## Real-Time Updates (WebSocket)

The dashboard supports WebSocket for real-time updates (currently in stub):

```typescript
// Get WebSocket URL
const wsURL = client.getWebSocketURL('/ws/ari/user-123');

// Connect to WebSocket
const ws = new WebSocket(wsURL);

ws.onopen = () => {
  console.log('Connected to real-time updates');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Real-time update:', data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

## Response Data Formats

### ARI Metrics Response

```json
{
  "overall_score": 0.78,
  "dimensions": {
    "decision_quality": 0.85,
    "skill_development": 0.72,
    "ai_reliance": 0.65,
    "bottleneck_resolution": 0.88,
    "user_confidence": 0.80,
    "engagement": 0.75,
    "autonomy_perception": 0.72
  },
  "timestamp": "2024-11-04T22:30:00Z",
  "trend": "stable",
  "confidence": 0.92
}
```

### Goals Response

```json
{
  "id": "goal-123",
  "title": "Learn TypeScript",
  "description": "Master TypeScript features",
  "value": 8,
  "status": "IN_PROGRESS",
  "progress": 45,
  "created_at": "2024-11-01T10:00:00Z",
  "updated_at": "2024-11-04T15:30:00Z",
  "complexity": "MICRO",
  "strength_alignment": ["Problem Solving", "Learning"]
}
```

### Audit Log Response

```json
[
  {
    "id": "log-123",
    "timestamp": "2024-11-04T22:15:00Z",
    "event_type": "GOAL_CREATED",
    "user_id": "user-456",
    "details": "Created goal: Learn TypeScript",
    "severity": "INFO"
  }
]
```

## Authentication Flow

1. **User enters credentials** → Login form
2. **Dashboard creates mock token** → (TODO: Real authentication)
3. **Token stored in localStorage** → Persists session
4. **Token injected in requests** → Authorization header
5. **Backend validates token** → Returns data
6. **401 response** → Token cleared, redirect to login

## Debugging

### Enable Console Logging

```typescript
// In App.tsx or during development
const client = getApiClient();
console.log('API Base URL:', client.baseURL);
console.log('Token stored:', localStorage.getItem('auth_token') ? 'Yes' : 'No');
```

### Check Network Requests

Use browser DevTools Network tab to:
1. Verify requests go to correct URL
2. Check Authorization header is present
3. Inspect response data and errors
4. Monitor WebSocket connections

### Common Issues

**CORS Error**
- Ensure backend has CORS enabled
- Check request headers match backend expectations

**401 Unauthorized**
- Token expired or invalid
- Check localStorage for auth_token
- Clear browser cache and try logging in again

**404 Not Found**
- Verify API endpoint is correct
- Check user ID format matches backend
- Verify backend is running

**Timeout**
- Backend is slow or unresponsive
- Check network latency
- Increase timeout in environment variables

## Next Steps

1. **Implement Real Authentication**
   - Create login endpoint on backend
   - Implement JWT token generation
   - Add password hashing and validation

2. **WebSocket Integration**
   - Implement `/ws/ari/{user_id}` for real-time metrics
   - Implement `/ws/goals/{goal_id}` for goal updates
   - Add real-time notifications

3. **Error Recovery**
   - Implement retry logic for failed requests
   - Add offline support with service workers
   - Implement request queuing during downtime

4. **Performance**
   - Implement request caching
   - Add pagination for large datasets
   - Implement lazy loading for components

## Testing with Backend

### Local Development

```bash
# Terminal 1: Start backend
cd /path/to/ai-pal
python -m uvicorn ai_pal.api.main:app --reload --port 8000

# Terminal 2: Start dashboard
cd dashboard
npm run dev
```

Then navigate to `http://localhost:5173` and test with real API.

### Using Mock Data

If backend isn't available, the dashboard gracefully falls back to mock data defined in components (see `SystemHealth.tsx`, `ARIMetrics.tsx`).

## Support

For API issues:
1. Check [API_DOCUMENTATION.md](../API_DOCUMENTATION.md)
2. Review browser console for errors
3. Check backend logs: `tail -f logs/ai_pal.log`
4. Visit API docs: `http://localhost:8000/docs`
