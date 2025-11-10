# AI-PAL Dashboard Implementation Analysis

## Executive Summary

The dashboard has **partial backend integration**. Some components use real API calls while others use hardcoded mock data. The backend API structure is well-defined but many user-specific endpoints expected by the dashboard are **missing** or **not fully implemented**. There's also inconsistency in refresh intervals and no WebSocket support for real-time updates.

---

## 1. CURRENT DATA CONNECTIONS

### 1.1 Components Using REAL API Data

#### ✅ ARIMetrics Component (`dashboard/src/components/ARIMetrics.tsx`)
- **Endpoint Called**: `/users/{userId}/ari`
- **Method**: `client.getARIMetrics(userId)`
- **Refresh Interval**: 30 seconds (line 29)
- **Expected Response**: `ARIMetrics` with `overall_score` and 7-dimension breakdown
- **Status**: CONNECTED TO REAL API

#### ✅ FFEGoals Component (`dashboard/src/components/FFEGoals.tsx`)
- **Endpoint Called**: `/users/{userId}/goals`
- **Method**: `client.getGoals(userId)`
- **Refresh Interval**: One-time fetch on mount (no auto-refresh)
- **Expected Response**: Array of `Goal` objects with progress tracking
- **Status**: CONNECTED TO REAL API

#### ✅ AuditLogs Component (`dashboard/src/components/AuditLogs.tsx`)
- **Endpoint Called**: `/users/{userId}/audit-logs`
- **Method**: `client.getAuditLogs(userId, limit)`
- **Refresh Interval**: One-time fetch on mount
- **Expected Response**: Array of `AuditLog` objects
- **Status**: CONNECTED TO REAL API

#### ✅ BackgroundJobs Component (`dashboard/src/components/BackgroundJobs.tsx`)
- **Endpoints Called**:
  - `GET /api/tasks/list` - List tasks
  - `GET /api/tasks/pending` - Get pending tasks
  - `GET /api/tasks/failed` - Get failed tasks
  - `POST /api/tasks/ari/aggregate-snapshots` - Submit ARI task
  - `POST /api/tasks/ffe/plan-goal` - Submit FFE task
  - `POST /api/tasks/edm/batch-analysis` - Submit EDM task
  - `DELETE /api/tasks/{taskId}` - Cancel task
  - `POST /api/tasks/{taskId}/retry` - Retry task
- **Refresh Interval**: 5 seconds (auto-refresh when enabled, line 74)
- **Status**: CONNECTED TO REAL API

### 1.2 Components Using MOCK/HARDCODED Data

#### ❌ SystemHealth Component (`dashboard/src/components/SystemHealth.tsx`)
- **Line 37-68**: Hardcoded mock services array
- **Line 71-78**: Generated fake metrics data
- **What's Mocked**:
  ```typescript
  mockServices: ServiceStatus[] = [
    { name: 'API Server', status: 'healthy', responseTime: 45, uptime: 99.9 },
    { name: 'Database', status: 'healthy', responseTime: 12, uptime: 99.95 },
    { name: 'Redis Cache', status: 'healthy', responseTime: 5, uptime: 99.8 },
    { name: 'Model Service', status: 'healthy', responseTime: 250, uptime: 99.5 },
    { name: 'Background Jobs', status: 'healthy', responseTime: 100, uptime: 99.7 }
  ]
  ```
- **Random Metrics Generated**:
  - Requests: 500-1500
  - Errors: 0-50
  - Latency: 30-130ms
  - Memory: 40-100MB
- **System Info Hardcoded**:
  - Version: "1.0.0"
  - Environment: "Production"
  - Uptime: "45 days 12h"
  - Deployment: "Kubernetes", Replicas: 3, Region: "us-east-1"
- **Status**: MOSTLY MOCK DATA

#### ⚠️ App Overview (`dashboard/src/App.tsx`, lines 168-182)
- Hardcoded overview stats (all mock):
  - System Status: "Healthy"
  - Active Goals: 5
  - Overall Agency: 78%
- **Status**: HARDCODED STATIC DATA

#### ⚠️ Personality & Teaching (`dashboard/src/App.tsx`, lines 193-250)
- Personality section shows hardcoded strengths list
- Teaching section shows static stats ("15+ subjects", "5-15 minutes")
- No API integration yet
- **Status**: PLACEHOLDER UI ONLY

---

## 2. BACKEND API ENDPOINTS

### 2.1 Implemented Endpoints (in `/src/ai_pal/api/main.py`)

```
System Endpoints:
- GET    /health                                     ✅ Implemented
- GET    /metrics                                    ✅ Implemented

User Endpoints:
- GET    /api/users/{user_id}/profile               ✅ Implemented
- POST   /api/chat                                   ✅ Implemented (Core)

FFE Endpoints:
- POST   /api/ffe/goals                              ✅ Implemented
- GET    /api/ffe/goals/{goal_id}                    ✅ Implemented
- POST   /api/ffe/goals/{goal_id}/plan               ✅ Implemented

Social Endpoints:
- POST   /api/social/groups                          ✅ Implemented
- GET    /api/social/groups                          ✅ Implemented
- GET    /api/social/feed/{group_id}                 ✅ Implemented

Personality Endpoints:
- POST   /api/personality/discover/start             ✅ Implemented
- GET    /api/personality/discover/{session_id}/question  ✅ Implemented
- POST   /api/personality/discover/{session_id}/answer/{question_id}  ✅ Implemented
- POST   /api/personality/discover/{session_id}/complete   ✅ Implemented
- GET    /api/personality/strengths                  ✅ Implemented
- GET    /api/personality/insights                   ✅ Implemented

Teaching Endpoints:
- POST   /api/teaching/start                         ✅ Implemented
- POST   /api/teaching/submit                        ✅ Implemented
- GET    /api/teaching/taught-topics                 ✅ Implemented

Patch Request Endpoints:
- GET    /api/patch-requests                         ✅ Implemented
- GET    /api/patch-requests/pending                 ✅ Implemented
- GET    /api/patch-requests/{request_id}            ✅ Implemented
- POST   /api/patch-requests/{request_id}/approve    ✅ Implemented
```

### 2.2 Task Management Endpoints (in `/src/ai_pal/api/tasks.py`)

```
Task Submission:
- POST   /api/tasks/ari/aggregate-snapshots          ✅ Implemented
- POST   /api/tasks/ffe/plan-goal                    ✅ Implemented
- POST   /api/tasks/edm/batch-analysis               ✅ Implemented

Task Monitoring:
- GET    /api/tasks/status/{task_id}                 ✅ Implemented
- GET    /api/tasks/list                             ✅ Implemented (with filtering)
- GET    /api/tasks/pending                          ✅ Implemented
- GET    /api/tasks/failed                           ✅ Implemented
- DELETE /api/tasks/{task_id}                        ✅ Implemented
- POST   /api/tasks/{task_id}/retry                  ✅ Implemented
- GET    /api/tasks/health                           ✅ Implemented
```

---

## 3. MISSING ENDPOINTS (Expected by Dashboard but NOT in Backend)

### Critical Missing Endpoints

| Expected Endpoint | Dashboard Component | Purpose | Status |
|---|---|---|---|
| `GET /users/{userId}/ari` | ARIMetrics | Get ARI metrics snapshot | MISSING |
| `GET /users/{userId}/goals` | FFEGoals | Get user's FFE goals | MISSING |
| `GET /users/{userId}/audit-logs` | AuditLogs | Get audit logs | MISSING |
| `GET /api/health` (detailed) | SystemHealth | Get service health/metrics | PARTIAL* |
| `POST /users/{userId}/goals` | FFEGoals (create) | Create new goal | EXISTS but NOT for user-specific path |
| `PUT /users/{userId}/goals/{goalId}` | FFEGoals (update) | Update goal | MISSING |
| `POST /users/{userId}/goals/{goalId}/complete` | FFEGoals | Mark goal complete | MISSING |
| `POST /users/{userId}/personality/discover` | Personality section | Start discovery session | EXISTS but NOT for user path |
| `GET /users/{userId}/personality/strengths` | Personality section | Get strengths profile | MISSING |
| `POST /users/{userId}/teaching/start` | Teaching section | Start teaching session | MISSING |
| `GET /users/{userId}/teaching/topics` | Teaching section | Get teaching topics | MISSING |

*Health endpoint exists but returns basic health, not detailed metrics needed for SystemHealth dashboard

### 3.1 Explanation of Missing Endpoints

The dashboard client (`dashboard/src/api/client.ts`) defines these methods that expect user-scoped endpoints:

```typescript
// Lines 102-105: ARIMetrics endpoint - NOT FOUND IN BACKEND
async getARIMetrics(userId: string) {
  const response = await this.client.get(`/users/${userId}/ari`);
  return response.data;
}

// Lines 116-120: Goals endpoints - NOT FOUND IN BACKEND
async getGoals(userId: string, status?: string) {
  const response = await this.client.get(`/users/${userId}/goals`, ...);
  return response.data;
}

// Lines 218-222: Audit logs - NOT FOUND IN BACKEND
async getAuditLogs(userId: string, limit: number = 100, offset: number = 0) {
  const response = await this.client.get(`/users/${userId}/audit-logs`, ...);
  return response.data;
}
```

The backend defines these endpoints but at different paths:
- `/api/ffe/goals` (generic, not user-scoped)
- `/api/personality/discover` (generic, not user-scoped)
- No ARI metrics endpoint at all
- No audit logs endpoint at all

---

## 4. STATE MANAGEMENT

### 4.1 Zustand Store (`dashboard/src/store/store.ts`)

```typescript
interface DashboardStore {
  // Auth
  user: User | null
  token: string | null
  setUser: (user: User) => void
  setToken: (token: string) => void
  logout: () => void

  // Data
  ariMetrics: ARIMetrics | null
  goals: Goal[]
  systemHealth: SystemHealth | null
  loading: Record<string, boolean>  // Keyed by component name
  error: string | null

  // Actions
  setARIMetrics: (metrics: ARIMetrics) => void
  setGoals: (goals: Goal[]) => void
  setSystemHealth: (health: SystemHealth) => void
  setLoading: (key: string, loading: boolean) => void
  setError: (error: string | null) => void
}
```

### 4.2 Data Fetching Pattern

**Standard Pattern Used**:
```typescript
useEffect(() => {
  const fetchData = async () => {
    setLoading('componentName', true);
    try {
      const client = getApiClient();
      const data = await client.getXXX(userId);
      setXXXMetrics(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch');
    } finally {
      setLoading('componentName', false);
    }
  };

  fetchData();
  const interval = setInterval(fetchData, refreshIntervalMs);
  return () => clearInterval(interval);
}, [userId, dependencies]);
```

**No useEffect in components that are UI-only** (Personality, Teaching)

---

## 5. REAL-TIME REQUIREMENTS & POLLING

### Current Polling/Refresh Strategy

| Component | Refresh Interval | Method | Notes |
|---|---|---|---|
| ARIMetrics | 30 seconds | `setInterval` | Lines 29-30 |
| FFEGoals | One-time mount | No refresh | Data doesn't auto-update |
| SystemHealth | 60 seconds | `setInterval` | Lines 91-92 |
| AuditLogs | One-time mount | No refresh | Manual search/filter only |
| BackgroundJobs | 5 seconds (when enabled) | `setInterval` with toggle | User can enable/disable (line 74) |

### WebSocket Support

**Status**: NOT IMPLEMENTED

The API client has a method `getWebSocketURL()` (lines 342-347 in client.ts) but it's **never used anywhere** in the dashboard:

```typescript
getWebSocketURL(endpoint: string): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = this.baseURL.replace(/^https?:\/\//, '').replace(/\/api\/?$/, '');
  const token = this.token ? `?token=${this.token}` : '';
  return `${protocol}//${host}${endpoint}${token}`;
}
```

**No WebSocket connections in components** - all updates are via polling.

### Data That Would Benefit from Real-Time Updates

1. **AuditLogs** - Currently static, should update as new events occur
2. **BackgroundJobs** - Currently polls every 5 seconds, could use WebSocket for instant updates
3. **SystemHealth** - Currently polls every 60 seconds, should reflect immediate issues
4. **ARIMetrics** - Currently polls every 30 seconds, could update more frequently

---

## 6. DATA MODELS & MISMATCHES

### 6.1 Expected Frontend Data Structures

From `dashboard/src/store/store.ts`:

```typescript
interface ARIMetrics {
  overall_score: number
  dimensions: {
    decision_quality: number
    skill_development: number
    ai_reliance: number
    bottleneck_resolution: number
    user_confidence: number
    engagement: number
    autonomy_perception: number
  }
  timestamp: string
}

interface Goal {
  id: string
  title: string
  description: string
  value: number
  status: 'active' | 'completed' | 'paused'
  progress: number
  created_at: string
  updated_at: string
}
```

### 6.2 Expected Audit Log Structure

From `dashboard/src/components/AuditLogs.tsx` (lines 6-13):

```typescript
interface AuditLog {
  id: string
  timestamp: string
  event_type: string
  user_id: string
  details: string
  severity: 'info' | 'warning' | 'error' | 'critical'
}
```

### 6.3 Expected Task Structure

From `dashboard/src/components/BackgroundJobs.tsx` (lines 4-16):

```typescript
interface Task {
  task_id: string
  task_name: string
  task_type: string
  status: string
  user_id?: string
  created_at: string
  started_at?: string
  completed_at?: string
  result?: Record<string, any>
  error_message?: string
  attempts: number
  duration_seconds?: number
}
```

### 6.4 Mismatches with Backend

**Backend API Client Returns** (from `src/ai_pal/api/tasks.py`):

```python
class TaskStatusResponse(BaseModel):
  task_id: str
  task_name: str
  task_type: str
  status: str
  user_id: Optional[str]
  created_at: datetime
  started_at: Optional[datetime]
  completed_at: Optional[datetime]
  result: Optional[Dict[str, Any]]
  error_message: Optional[str]
  attempts: int
  duration_seconds: Optional[float]
```

**Status**: ✅ Task structure matches perfectly

---

## 7. DETAILED FINDINGS SUMMARY

### 7.1 Components Status Table

| Component | Data Source | Implementation | Refresh | Issues |
|---|---|---|---|---|
| ARIMetrics | Real API | Fully connected | 30s polling | ❌ Endpoint missing on backend |
| FFEGoals | Real API | Partially connected | None | ❌ Create/Update/Delete form not functional |
| SystemHealth | Mock data | Hardcoded | 60s polling | ❌ All service data hardcoded, no real metrics |
| AuditLogs | Real API | Partially connected | None | ❌ No auto-refresh, filtering is client-side only |
| BackgroundJobs | Real API | Fully connected | 5s (toggle) | ✅ Fully functional |
| Overview | Hardcoded | Mock | None | ❌ Static placeholder data |
| Personality | UI only | Placeholder | None | ❌ No real personality discovery |
| Teaching | UI only | Placeholder | None | ❌ No real teaching sessions |

### 7.2 Critical Issues

1. **Endpoint Mismatch**: Dashboard expects `/users/{userId}/ari` but backend doesn't provide it
2. **Missing ARI Endpoint**: No ARI metrics endpoint exists in backend
3. **Missing Audit Logs**: No audit logs endpoint exists in backend
4. **Generic vs User-Scoped**: Backend uses generic endpoints (`/api/ffe/goals`) instead of user-scoped (`/users/{userId}/goals`)
5. **Mock Data in Production**: SystemHealth component uses 100% hardcoded mock data
6. **No Error Handling for Missing Endpoints**: Components will silently fail if endpoints don't exist
7. **No Real-Time Updates**: All updates through polling only, no WebSocket support
8. **No Authentication Validation**: Backend allows token as user_id (line 176 in main.py)

### 7.3 Missing Features in Dashboard

- Personality discovery (UI exists, no backend)
- Teaching/Learn-by-Teaching sessions (UI exists, no real functionality)
- Real-time notifications (no WebSocket)
- Settings page (mentioned in sidebar but no implementation)
- Proper error states (components show loading but not errors)

---

## 8. POLLING INTERVALS BREAKDOWN

```
SystemHealth:        60 seconds  (Healthcare-level frequency)
ARIMetrics:          30 seconds  (Good for dashboard updates)
BackgroundJobs:       5 seconds  (Real-time-ish for task monitoring)
FFEGoals:            Never       (Static data after initial load)
AuditLogs:           Never       (Static data after initial load)
```

**Recommendations**:
- Reduce SystemHealth to 30 seconds for better responsiveness
- Add polling to FFEGoals (every 30-60 seconds for goal progress updates)
- Add polling to AuditLogs (every 60 seconds for compliance tracking)
- Implement WebSocket for BackgroundJobs (more efficient than 5-second polling)

---

## 9. API CLIENT vs Backend Endpoint Summary

### Client Methods Defined (in `dashboard/src/api/client.ts`)

```
✅ getHealth()
✅ getMetrics()
✅ getUserProfile(userId)
✅ updateUserProfile(userId, data)
✅ getARIMetrics(userId)           ← ENDPOINT MISSING IN BACKEND
✅ getARIHistory(userId, days)      ← ENDPOINT MISSING IN BACKEND
✅ getGoals(userId, status)         ← PATH MISMATCH (backend: /api/ffe/goals)
✅ getGoal(userId, goalId)          ← ENDPOINT MISSING
✅ createGoal(userId, goalData)     ← PATH MISMATCH
✅ updateGoal(userId, goalId)       ← ENDPOINT MISSING
✅ planGoal(userId, goalId)         ← PATH MISMATCH
✅ completeGoal(userId, goalId)     ← ENDPOINT MISSING
✅ getPersonality(userId)           ← ENDPOINT MISSING
✅ startPersonalityDiscovery(userId) ← ENDPOINT MISSING
✅ getTeachingTopics(userId)        ← ENDPOINT MISSING
✅ startTeachingSession(userId, topicId) ← ENDPOINT MISSING
✅ listTasks(status, userId, limit) ✅ IMPLEMENTED
✅ getTaskStatus(taskId)            ✅ IMPLEMENTED
✅ getPendingTasks(limit)           ✅ IMPLEMENTED
✅ getFailedTasks(limit)            ✅ IMPLEMENTED
✅ submitARIAggregation(...)        ✅ IMPLEMENTED
✅ submitFFEPlanning(...)           ✅ IMPLEMENTED
✅ submitEDMAnalysis(...)           ✅ IMPLEMENTED
✅ cancelTask(taskId)               ✅ IMPLEMENTED
✅ retryTask(taskId)                ✅ IMPLEMENTED
```

