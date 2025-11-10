# Dashboard Integration - Detailed Findings with Code Examples

## 1. MOCK DATA INSTANCES - Exact Locations

### 1.1 SystemHealth Component - Hardcoded Services

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/components/SystemHealth.tsx`
**Lines**: 37-68

```typescript
const mockServices: ServiceStatus[] = [
  {
    name: 'API Server',
    status: healthData.status === 'healthy' ? 'healthy' : 'degraded',
    responseTime: 45,
    uptime: 99.9,
  },
  {
    name: 'Database',
    status: 'healthy',
    responseTime: 12,
    uptime: 99.95,
  },
  {
    name: 'Redis Cache',
    status: 'healthy',
    responseTime: 5,
    uptime: 99.8,
  },
  {
    name: 'Model Service',
    status: 'healthy',
    responseTime: 250,
    uptime: 99.5,
  },
  {
    name: 'Background Jobs',
    status: 'healthy',
    responseTime: 100,
    uptime: 99.7,
  },
];
setServices(mockServices);
```

**Issue**: These are hardcoded values. Only the API Server status uses real health check data.

### 1.2 SystemHealth Component - Generated Mock Metrics

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/components/SystemHealth.tsx`
**Lines**: 71-79

```typescript
// Generate mock metrics
const mockMetrics: MetricDataPoint[] = Array.from({ length: 24 }, (_, i) => ({
  timestamp: `${i}:00`,
  requests: Math.floor(Math.random() * 1000 + 500),
  errors: Math.floor(Math.random() * 50),
  latency: Math.floor(Math.random() * 100 + 30),
  memory: Math.floor(Math.random() * 60 + 40),
}));
setMetrics(mockMetrics);
```

**Issue**: 24 hours of random metric data generated every fetch. These are fake numbers.

### 1.3 SystemHealth Component - Hardcoded System Info

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/components/SystemHealth.tsx`
**Lines**: 249-275

```typescript
<h4 className="font-medium text-gray-700 mb-3">Application</h4>
<dl className="space-y-2 text-sm">
  <div className="flex justify-between">
    <dt className="text-gray-600">Version</dt>
    <dd className="font-medium text-gray-800">1.0.0</dd>
  </div>
  <div className="flex justify-between">
    <dt className="text-gray-600">Environment</dt>
    <dd className="font-medium text-gray-800">Production</dd>
  </div>
  <div className="flex justify-between">
    <dt className="text-gray-600">Uptime</dt>
    <dd className="font-medium text-gray-800">45 days 12h</dd>
  </div>
</dl>

<h4 className="font-medium text-gray-700 mb-3">Infrastructure</h4>
<dl className="space-y-2 text-sm">
  <div className="flex justify-between">
    <dt className="text-gray-600">Deployment</dt>
    <dd className="font-medium text-gray-800">Kubernetes</dd>
  </div>
  <div className="flex justify-between">
    <dt className="text-gray-600">Replicas</dt>
    <dd className="font-medium text-gray-800">3</dd>
  </div>
  <div className="flex justify-between">
    <dt className="text-gray-600">Region</dt>
    <dd className="font-medium text-gray-800">us-east-1</dd>
  </div>
</dl>
```

**Issue**: All hardcoded strings in JSX. No API calls.

### 1.4 App Component - Overview Statistics

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/App.tsx`
**Lines**: 168-182

```typescript
{currentView === 'overview' && (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div className="bg-white rounded-lg shadow p-6">
      <p className="text-gray-600 text-sm font-medium mb-2">System Status</p>
      <p className="text-3xl font-bold text-green-600">Healthy</p>
    </div>
    <div className="bg-white rounded-lg shadow p-6">
      <p className="text-gray-600 text-sm font-medium mb-2">Active Goals</p>
      <p className="text-3xl font-bold text-blue-600">5</p>
    </div>
    <div className="bg-white rounded-lg shadow p-6">
      <p className="text-gray-600 text-sm font-medium mb-2">Overall Agency</p>
      <p className="text-3xl font-bold text-primary-600">78%</p>
    </div>
  </div>
)}
```

**Issue**: "Healthy", 5, and 78% are hardcoded literal values.

### 1.5 App Component - Personality Section

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/App.tsx`
**Lines**: 202-207

```typescript
<h3 className="font-semibold text-purple-900 mb-3">Your Strengths</h3>
<ul className="space-y-2 text-sm text-purple-800">
  <li>✓ Strategic Thinking</li>
  <li>✓ Problem Solving</li>
  <li>✓ Communication</li>
</ul>
```

**Issue**: Hardcoded strengths list. No dynamic data.

---

## 2. MISSING ENDPOINT VERIFICATION

### 2.1 Dashboard Calls vs Backend Reality

#### ARIMetrics Endpoint

**Dashboard Expects**:
```typescript
// File: dashboard/src/api/client.ts, Lines 102-105
async getARIMetrics(userId: string) {
  const response = await this.client.get(`/users/${userId}/ari`);
  return response.data;
}
```

**Backend Search Results**:
```bash
$ grep -r "users.*ari" src/ai_pal/api/
# Result: NO MATCHES
```

**Conclusion**: Endpoint completely missing. Component will fail with 404.

#### FFEGoals Endpoint

**Dashboard Expects**:
```typescript
// File: dashboard/src/api/client.ts, Lines 116-120
async getGoals(userId: string, status?: string) {
  const response = await this.client.get(`/users/${userId}/goals`, {
    params: status ? { status } : undefined,
  });
  return response.data;
}
```

**Backend Provides**:
```python
# File: src/ai_pal/api/main.py, Line 389
@app.post("/api/ffe/goals", response_model=GoalResponse, tags=["FFE"])
async def create_goal(...)
```

**Issue**: 
- Endpoint path doesn't match (`/api/ffe/goals` vs `/users/{userId}/goals`)
- Wrong HTTP method (POST for get, should be GET)
- No user-scoped goals listing

#### AuditLogs Endpoint

**Dashboard Expects**:
```typescript
// File: dashboard/src/api/client.ts, Lines 218-222
async getAuditLogs(userId: string, limit: number = 100, offset: number = 0) {
  const response = await this.client.get(`/users/${userId}/audit-logs`, {
    params: { limit, offset },
  });
  return response.data;
}
```

**Backend Search**:
```bash
$ grep -r "audit" src/ai_pal/api/
# Result: NO MATCHES
```

**Conclusion**: Endpoint completely missing.

---

## 3. POLLING INTERVALS - Code Locations

### 3.1 ARIMetrics - 30 Second Interval

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/components/ARIMetrics.tsx`
**Lines**: 28-31

```typescript
useEffect(() => {
  const fetchARIMetrics = async () => {
    setLoading('ari', true);
    try {
      const client = getApiClient();
      const data = await client.getARIMetrics(userId);
      setARIMetrics(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch ARI metrics');
    } finally {
      setLoading('ari', false);
    }
  };

  fetchARIMetrics();
  const interval = setInterval(fetchARIMetrics, 30000); // ← 30 seconds
  return () => clearInterval(interval);
}, [userId, setARIMetrics, setLoading, setError]);
```

### 3.2 SystemHealth - 60 Second Interval

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/components/SystemHealth.tsx`
**Lines**: 88-92

```typescript
fetchHealthData();
const interval = setInterval(fetchHealthData, 60000); // ← 60 seconds
return () => clearInterval(interval);
```

### 3.3 BackgroundJobs - 5 Second Interval (User Toggle)

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/components/BackgroundJobs.tsx`
**Lines**: 66-80

```typescript
useEffect(() => {
  fetchTasks();

  let interval: ReturnType<typeof setInterval> | null = null;
  if (autoRefresh) {
    interval = setInterval(() => {
      fetchTasks();
    }, 5000); // ← 5 seconds, controlled by checkbox
  }

  return () => {
    if (interval) clearInterval(interval);
  };
}, [filter, autoRefresh]);
```

The toggle is at **Line 313-320**:
```typescript
<label className="flex items-center text-sm">
  <input
    type="checkbox"
    checked={autoRefresh}
    onChange={(e) => setAutoRefresh(e.target.checked)}
    className="mr-2"
  />
  Auto-refresh (5s)
</label>
```

### 3.4 FFEGoals - No Auto-Refresh

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/components/FFEGoals.tsx`
**Lines**: 10-26

```typescript
useEffect(() => {
  const fetchGoals = async () => {
    setLoading('goals', true);
    try {
      const client = getApiClient();
      const data = await client.getGoals(userId);
      setGoals(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch goals');
    } finally {
      setLoading('goals', false);
    }
  };

  fetchGoals();
  // ← NO setInterval HERE - data only fetched once on mount
}, [userId, setGoals, setLoading, setError]);
```

### 3.5 AuditLogs - No Auto-Refresh

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/components/AuditLogs.tsx`
**Lines**: 22-38

```typescript
useEffect(() => {
  const fetchLogs = async () => {
    setLoading('audit', true);
    try {
      const client = getApiClient();
      const data = await client.getAuditLogs(userId, 100);
      setLogs(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch audit logs');
    } finally {
      setLoading('audit', false);
    }
  };

  fetchLogs();
  // ← NO setInterval - data only fetched once on mount
}, [userId, setLoading, setError]);
```

---

## 4. WEBSOCKET - Defined but Unused

### 4.1 WebSocket Method Definition

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/api/client.ts`
**Lines**: 342-347

```typescript
// ============ WebSocket Support ============

getWebSocketURL(endpoint: string): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = this.baseURL.replace(/^https?:\/\//, '').replace(/\/api\/?$/, '');
  const token = this.token ? `?token=${this.token}` : '';
  return `${protocol}//${host}${endpoint}${token}`;
}
```

### 4.2 Usage Search

```bash
$ grep -r "getWebSocketURL\|WebSocket\|ws://" dashboard/src/components/
# Result: NO MATCHES
```

**Conclusion**: WebSocket support is defined in the client but never used anywhere in the dashboard.

---

## 5. STATE MANAGEMENT - Data Flow

### 5.1 Zustand Store Definition

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/store/store.ts`

**ARI Metrics State** (Lines 9-21):
```typescript
export interface ARIMetrics {
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
```

**Goals State** (Lines 23-32):
```typescript
export interface Goal {
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

**Store Interface** (Lines 40-64):
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
  loading: Record<string, boolean>
  error: string | null

  // Actions
  setARIMetrics: (metrics: ARIMetrics) => void
  setGoals: (goals: Goal[]) => void
  setSystemHealth: (health: SystemHealth) => void
  setLoading: (key: string, loading: boolean) => void
  setError: (error: string | null) => void
  // ... goal manipulation methods
}
```

---

## 6. DATA FETCH PATTERN ANALYSIS

### 6.1 Standard Pattern (ARIMetrics Example)

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/components/ARIMetrics.tsx`

```typescript
useEffect(() => {
  const fetchARIMetrics = async () => {
    // 1. Set loading state
    setLoading('ari', true);
    try {
      // 2. Get API client
      const client = getApiClient();
      
      // 3. Call specific endpoint
      const data = await client.getARIMetrics(userId);
      
      // 4. Store in Zustand
      setARIMetrics(data);
      
      // 5. Clear error
      setError(null);
    } catch (err) {
      // 6. Set error state
      setError(err instanceof Error ? err.message : 'Failed to fetch ARI metrics');
    } finally {
      // 7. Clear loading state
      setLoading('ari', false);
    }
  };

  // 8. Initial fetch on mount
  fetchARIMetrics();
  
  // 9. Setup polling interval
  const interval = setInterval(fetchARIMetrics, 30000);
  
  // 10. Cleanup interval on unmount
  return () => clearInterval(interval);
}, [userId, setARIMetrics, setLoading, setError]);
```

This pattern is used consistently in:
- ARIMetrics.tsx
- FFEGoals.tsx
- AuditLogs.tsx
- SystemHealth.tsx
- BackgroundJobs.tsx

---

## 7. AUTHENTICATION - Current Implementation

### 7.1 Frontend Authentication (Mock)

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/App.tsx`
**Lines**: 35-72

```typescript
const handleLogin = async (email: string) => {
  try {
    const client = getApiClient();

    // Generate a JWT-like token (in production, this comes from backend)
    const mockToken = btoa(JSON.stringify({
      user_id: mockUser.id,
      email: email,
      exp: Date.now() + (24 * 60 * 60 * 1000)
    }));

    setUser(mockUser);
    setToken(mockToken);
    setUserId(mockUser.id);
    setAuthenticated(true);

    // Try to verify token works by making a test API call
    try {
      await client.getHealth();
      console.log('✓ Connected to AI-Pal backend API');
    } catch (err) {
      console.warn('⚠ Backend API not available. Using mock data.', err);
    }
  } catch (error) {
    console.error('Login error:', error);
    alert('Login failed. Please try again.');
  }
};
```

**Issue**: Creates fake JWT token in frontend. No backend validation.

### 7.2 Backend Authentication (Insecure)

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/src/ai_pal/api/main.py`
**Lines**: 151-184

```python
async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract user from authorization header

    In production, this would validate JWT tokens.
    For now, we extract user_id from bearer token.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Format: "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
            )

        # In production: validate JWT and extract user_id
        # For now: use token as user_id (for development/testing)
        user_id = token  # ← INSECURE: token used as user_id!

        return user_id

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )
```

**Issue**: The token value itself is used as the user_id. No JWT validation.

---

## 8. COMPONENT IMPLEMENTATION COMPLETENESS

### 8.1 ARIMetrics - Fully Implemented UI, Broken Backend

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/components/ARIMetrics.tsx`

✅ What's Done:
- Radar chart rendering
- 7-dimension metrics display
- Overall score display
- Recommendations section
- Top 3 strengths highlight

❌ What's Broken:
- Backend endpoint doesn't exist
- Will get 404 when trying to fetch

### 8.2 BackgroundJobs - Fully Implemented and Working

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/components/BackgroundJobs.tsx`

✅ What's Done:
- Task submission form (ARI, FFE, EDM)
- Task list with filtering
- Auto-refresh toggle
- Task status monitoring
- Cancel and retry buttons
- Real-time progress tracking

✅ What Works:
- All task endpoints exist and work
- Data structures match perfectly
- Polling interval is configurable

### 8.3 SystemHealth - UI Complete, Data Broken

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/components/SystemHealth.tsx`

✅ What's Done:
- Service status cards
- Metric charts (Recharts)
- Health summary statistics
- System information display

❌ What's Broken:
- All service data hardcoded
- All metrics randomly generated
- System info is fake
- Gets health status but doesn't use it properly

### 8.4 FFEGoals - UI Complete, Create/Edit Broken

**File**: `/Users/caseyrobbins/ai-pal/ai-pal/dashboard/src/components/FFEGoals.tsx`

✅ What's Done:
- Goal display cards
- Progress bars
- Goal filtering
- "New Goal" form UI

❌ What's Broken:
- Create goal form not functional (no submit handler)
- Path mismatch with backend
- No auto-refresh for goal updates
- Update and delete operations not possible

---

## 9. ERROR HANDLING - What's Missing

### 9.1 Error Display Issue

Most components show errors in Zustand store but don't display them:

**Example - SystemHealth.tsx**:
```typescript
catch (err) {
  setError(err instanceof Error ? err.message : 'Failed to fetch health data');
}
// ← Error is set but component doesn't render error state
```

The error appears in store but UI has no error boundary or error message display.

### 9.2 No 404 Handling

When calling missing endpoints (e.g., `/users/{userId}/ari`), components will:
1. Try to fetch
2. Get 404 error
3. Set error in store
4. Show "Loading..." forever or fallback to mock data

Example flow:
```typescript
// Component calls missing endpoint
const data = await client.getARIMetrics(userId);
// ^ Gets 404 response
// Error caught, error state set
// But no error UI displayed to user
// Component stays in loading state
```

---

## 10. REFRESH INTERVAL INCONSISTENCY

| Component | Interval | Rationale | Actual Need |
|---|---|---|---|
| SystemHealth | 60s | Too slow | Should be 30s |
| ARIMetrics | 30s | Good | Matches need |
| BackgroundJobs | 5s | Polling overhead | WebSocket would be better |
| FFEGoals | Never | Wrong | Should be 30-60s |
| AuditLogs | Never | Wrong | Should be 60s |

**Result**: Inconsistent user experience. Some data fresh, some stale.

