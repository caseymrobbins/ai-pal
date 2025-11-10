# Dashboard Integration Quick Reference

## At-a-Glance Status

### Data Connections Status
```
Component          Status        Data Source    Refresh      Critical Issues
─────────────────────────────────────────────────────────────────────────────
ARIMetrics         ⚠️  PARTIAL   Real API       30s          Endpoint MISSING
FFEGoals           ⚠️  PARTIAL   Real API       None         Create/Update ops fail
SystemHealth       ❌  BROKEN    100% MOCK      60s          Hardcoded data only
AuditLogs          ⚠️  PARTIAL   Real API       None         No auto-refresh
BackgroundJobs     ✅  WORKING   Real API       5s toggle    Fully functional
Overview           ❌  BROKEN    Hardcoded      None         Static placeholder
Personality        ❌  NO API    UI only        N/A          No implementation
Teaching           ❌  NO API    UI only        N/A          No implementation
```

## Missing Backend Endpoints (12 total)

### High Priority (Dashboard Currently Broken)
1. `GET /users/{userId}/ari` - ARI metrics not accessible
2. `GET /users/{userId}/goals` - Goals list path wrong
3. `GET /users/{userId}/audit-logs` - Audit logs not available

### Medium Priority (Features Non-Functional)
4. `GET /users/{userId}/ari/history` - ARI history tracking missing
5. `PUT /users/{userId}/goals/{goalId}` - Can't update goals
6. `POST /users/{userId}/goals/{goalId}/complete` - Can't mark goals done
7. `GET /users/{userId}/personality` - Personality data missing
8. `POST /users/{userId}/personality/discover` - User-scoped discovery missing
9. `GET /users/{userId}/personality/strengths` - Strengths profile missing

### Low Priority (Nice-to-Have)
10. `GET /users/{userId}/teaching/topics` - Teaching topics missing
11. `POST /users/{userId}/teaching/start` - Teaching sessions missing
12. `POST /api/health` (detailed) - SystemHealth needs metrics endpoint

## API Endpoint Paths: Frontend vs Backend

### Path Mismatches
| Frontend Expects | Backend Provides | Issue |
|---|---|---|
| `/users/{userId}/ari` | None | MISSING |
| `/users/{userId}/goals` | `/api/ffe/goals` | PATH MISMATCH |
| `/users/{userId}/audit-logs` | None | MISSING |
| `/users/{userId}/personality` | `/api/personality/discover/start` | PATH MISMATCH |

### What's Actually Working
| Endpoint | Status |
|---|---|
| `/api/tasks/*` | ✅ ALL WORKING |
| `/api/ffe/goals` (generic) | ✅ Works but not user-scoped |
| `/api/personality/*` (generic) | ✅ Works but not user-scoped |
| `/health` | ✅ Works (basic only) |
| `/metrics` | ✅ Works (Prometheus format) |

## Real-Time Update Strategy

### Current Approach
- **Polling Only**: All updates via `setInterval`
- **WebSocket**: Defined but never used
- **No Server Sent Events**: No push notifications

### Refresh Intervals (seconds)
```
BackgroundJobs: 5    (user toggleable)
ARIMetrics:    30
SystemHealth:  60
FFEGoals:      ∞     (never)
AuditLogs:     ∞     (never)
```

## Hardcoded Mock Data Locations

### SystemHealth.tsx
- **Lines 37-68**: 5 mock services (API, DB, Redis, Model, Jobs)
- **Lines 71-78**: Random metrics (requests, errors, latency, memory)
- **Lines 241-278**: System info (Version: 1.0.0, Kubernetes, 3 replicas)

### App.tsx Overview
- **Lines 171-172**: "System Status: Healthy"
- **Lines 175-176**: "Active Goals: 5"
- **Lines 179-180**: "Overall Agency: 78%"

### Personality & Teaching Sections
- **Lines 202-207**: Hardcoded strengths list
- **Lines 234-244**: Static stats ("15+ subjects")

## Data Model Alignment

### ✅ Perfectly Aligned
- Task structure (Task*Response matches Task interface)

### ⚠️ Expected but Missing
- ARI metrics structure (defined in store but no backend)
- Goal structure (defined in store but partial implementation)
- Audit log structure (defined in component but no backend)

## Authentication Issues

### Current Implementation
```
// Backend: uses token as user_id (insecure)
// File: src/ai_pal/api/main.py line 176
user_id = token  // WRONG!

// Dashboard: generates mock JWT-like token
// File: dashboard/src/App.tsx lines 49-54
```

### Issue
No proper JWT validation or user extraction from token

## Components That Need API Fixes

### Phase 1 (Critical)
- [ ] Create `/users/{userId}/ari` endpoint
- [ ] Create `/users/{userId}/goals` endpoint  
- [ ] Create `/users/{userId}/audit-logs` endpoint
- [ ] Update SystemHealth to use real data

### Phase 2 (Important)
- [ ] Add user-scoped endpoints for personality
- [ ] Add user-scoped endpoints for teaching
- [ ] Implement goal update/complete operations
- [ ] Add ARI history endpoint

### Phase 3 (Enhancement)
- [ ] Implement WebSocket for real-time updates
- [ ] Add detailed metrics endpoint
- [ ] Implement proper JWT authentication
- [ ] Add error state handling in components

## File References

| File | Purpose | Lines |
|---|---|---|
| dashboard/src/api/client.ts | API client definition | 1-368 |
| dashboard/src/store/store.ts | State management | 1-111 |
| dashboard/src/components/SystemHealth.tsx | Hardcoded mock services | 37-78 |
| dashboard/src/components/ARIMetrics.tsx | ARI data fetching | 1-209 |
| dashboard/src/components/BackgroundJobs.tsx | Task management | 1-459 |
| src/ai_pal/api/main.py | Backend endpoints | 1-1000+ |
| src/ai_pal/api/tasks.py | Task endpoints | 1-500+ |

## Quick Fixes

### Replace SystemHealth Mock with API Call
```typescript
// Change from hardcoded mockServices to:
const healthData = await client.getHealth();
// Then parse response into service status format
```

### Fix Path Mismatches
```
Frontend calls:  /users/{userId}/goals
Backend needs:   /users/{userId}/goals  ← Create this route
Current:         /api/ffe/goals         ← This is generic
```

### Enable Auto-Refresh for Goals & Audit
```typescript
// Add interval to FFEGoals and AuditLogs:
const interval = setInterval(() => {
  fetchData();  
}, 30000);  // 30 seconds
return () => clearInterval(interval);
```

## Testing Checklist

- [ ] Test ARIMetrics endpoint when backend is available
- [ ] Test SystemHealth with real metrics API
- [ ] Test FFEGoals with user-scoped endpoint
- [ ] Test AuditLogs with real data
- [ ] Test WebSocket connection (when implemented)
- [ ] Test error handling for 404/500 responses
- [ ] Test polling intervals match design

