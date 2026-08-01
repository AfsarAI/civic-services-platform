# Performance Metrics Dashboard Story Coverage Analysis

**Story:** TPS-97 — As an administrator, I want to view key performance metrics...  
**Analysis Date:** 2026-07-31  
**Status:** ⚠️ **PARTIALLY COVERED** (Some metrics missing)

---

## 📋 USER STORY REQUIREMENTS

### Acceptance Criteria Mapping

| # | Acceptance Criteria | Status | Evidence |
|---|---|---|---|
| 1 | Administrator can view all KPIs | ⚠️ Partial | Admin dashboard exists but incomplete metrics |
| 2 | Metrics calculated accurately | ✅ | Where implemented, tests verify |
| 3 | Display charts and KPI cards | ⚠️ Partial | Reports endpoint has charts data, dashboard basic |
| 4 | Auto-update when data changes | ❌ Missing | No real-time updates (frontend polling required) |
| 5 | Filter by date range | ⚠️ Partial | Reports support date filtering, dashboard doesn't |
| 6 | Load successfully | ✅ | Dashboard endpoint tested and passing |

---

## 🎯 REQUIRED PERFORMANCE METRICS (9 Total)

### Requirement 1: Total Complaints Received
**Current Status:** ✅ **IMPLEMENTED**
- **API:** `GET /admin/dashboard`
- **Field:** `total_complaints`
- **Test Coverage:** `test_admin_token_access_admin_dashboard` ✅
- **Implementation:** Count all complaints in system/city

### Requirement 2: Average Complaint Resolution Time
**Current Status:** ❌ **MISSING**
- **API Endpoint:** NOT in `/admin/dashboard`
- **Alternative:** Available in `/reports/complaints/summary` (but not real-time)
- **Calculation:** Average of `(resolved_at - created_at)` for resolved complaints
- **Needed:** Add field to admin dashboard
- **Action Required:** Add to dashboard service & controller

### Requirement 3: Average Assignment Time
**Current Status:** ❌ **MISSING**
- **API Endpoint:** NOT implemented
- **Calculation:** Average of `(accepted_at - assigned_at)` for completed assignments
- **Needed:** Implement new metric in dashboard
- **Action Required:** Add calculation & endpoint

### Requirement 4: Number of Open Complaints
**Current Status:** ✅ **IMPLEMENTED**
- **API:** `GET /admin/dashboard`
- **Field:** `open_complaints`
- **Includes:** pending, assigned, in_progress statuses
- **Test Coverage:** Verified in dashboard tests ✅

### Requirement 5: Number of Closed Complaints
**Current Status:** ❌ **MISSING**
- **API Endpoint:** NOT in `/admin/dashboard`
- **Status Included:** Count of `closed` status complaints
- **Note:** Different from `resolved` (resolved ≠ closed)
- **Action Required:** Add to dashboard

### Requirement 6: Field Worker Productivity
**Current Status:** ⚠️ **PARTIAL**
- **API:** `/reports/workers/performance` returns per-worker data
- **Dashboard:** Only shows total/active worker counts
- **Needed:** Summary metrics (avg productivity, completion rate %)
- **Action Required:** Add aggregated productivity to dashboard

### Requirement 7: Complaint Closure Rate
**Current Status:** ❌ **MISSING**
- **Calculation:** `(resolved + closed) / total * 100`
- **Current:** Not in dashboard, available via reports
- **Needed:** Add calculated percentage to dashboard
- **Action Required:** Implement in dashboard service

### Requirement 8: Citizen Satisfaction Rating
**Current Status:** ❌ **MISSING**
- **Model:** `Feedback` table has `rating` field (1-5 stars)
- **Calculation:** Average rating from all feedback records
- **Current:** No endpoint returns this metric
- **Action Required:** Query feedback table, calculate average
- **Implementation Complexity:** Medium (need to query Feedback model)

### Requirement 9: High Priority Pending Complaints
**Current Status:** ❌ **MISSING**
- **Filters:** `priority = 'urgent' AND status IN (pending, assigned)`
- **Current:** Not in dashboard
- **Needed:** Count of high-priority unresolved complaints
- **Action Required:** Add query to dashboard service

---

## 📊 CURRENT IMPLEMENTATION STATUS

### Admin Dashboard Endpoint: `GET /api/v1/admin/dashboard`

**Currently Returns:**

For System Administrators:
```json
{
  "scope": "system",
  "total_complaints": 50,
  "open_complaints": 15,
  "by_status": {
    "pending": 5,
    "assigned": 3,
    "in_progress": 7,
    "resolved": 20,
    "closed": 15,
    "rejected": 2,
    "cancelled": 0
  },
  "total_users": 100,
  "active_users": 95,
  "total_cities": 5,
  "municipal_admins": 12,
  "recent_complaints": [...]
}
```

For Municipal Administrators:
```json
{
  "scope": "municipal",
  "administrator": {...},
  "managed_city": {...},
  "total_complaints": 12,
  "open_complaints": 3,
  "by_status": {...},
  "total_field_workers": 8,
  "active_field_workers": 7,
  "recent_complaints": [...]
}
```

**Missing Fields for KPI Dashboard:**
- ❌ `avg_resolution_time_hours`
- ❌ `avg_assignment_time_hours`
- ❌ `closed_complaints_count`
- ❌ `field_worker_productivity` (aggregated)
- ❌ `closure_rate_percentage`
- ❌ `citizen_satisfaction_rating`
- ❌ `high_priority_pending_count`

---

## 🔍 GAPS ANALYSIS

### Gap 1: Average Resolution Time
**Severity:** High  
**Why:** Critical KPI for service quality  
**Fix:** Add calculation to dashboard service:
```python
resolved = Complaint.query.filter_by(status='resolved').all()
if resolved:
  avg_time = sum((c.resolved_at - c.created_at).total_seconds() 
                 for c in resolved if c.resolved_at) / len(resolved)
  avg_hours = avg_time / 3600
```

### Gap 2: Average Assignment Time
**Severity:** High  
**Why:** Measures operational efficiency  
**Fix:** Add calculation to dashboard service:
```python
completed = ComplaintAssignment.query.filter_by(status='completed').all()
if completed:
  avg_time = sum((a.accepted_at - a.assigned_at).total_seconds() 
                 for a in completed if a.accepted_at) / len(completed)
  avg_hours = avg_time / 3600
```

### Gap 3: Closed Complaints Count
**Severity:** Medium  
**Why:** Different from "resolved" - admin may close without verification  
**Fix:** Query for `status == 'closed'` count (already in by_status)
**Action:** Extract from by_status and show separately

### Gap 4: Field Worker Productivity (Aggregated)
**Severity:** Medium  
**Why:** Helps track team performance  
**Fix:** Aggregate from ComplaintAssignment:
```python
total_assignments = ComplaintAssignment.query.count()
completed = ComplaintAssignment.query.filter_by(status='completed').count()
avg_completion_rate = (completed / total_assignments * 100) if total_assignments > 0 else 0
```

### Gap 5: Complaint Closure Rate
**Severity:** Medium  
**Why:** Shows platform effectiveness  
**Fix:** Calculate from dashboard data:
```python
closure_rate = (resolved_count + closed_count) / total_complaints * 100
```

### Gap 6: Citizen Satisfaction Rating
**Severity:** High  
**Why:** Direct measure of citizen satisfaction  
**Fix:** Query Feedback table:
```python
feedback = Feedback.query.all()
if feedback:
  avg_rating = sum(f.rating for f in feedback) / len(feedback)
```

### Gap 7: High Priority Pending Complaints
**Severity:** Medium  
**Why:** Alerts admin to urgent issues  
**Fix:** Query with filters:
```python
high_priority_pending = Complaint.query.filter(
  Complaint.priority.in_(['urgent', 'high']),
  Complaint.status.in_(['pending', 'assigned'])
).count()
```

---

## 🛠️ IMPLEMENTATION PLAN

### Phase 1: Extend Dashboard Service (Priority: HIGH)

**File:** `/backend/app/api/administrator/service.py`

Add these calculations to `get_dashboard_summary()` method:

```python
# Calculate average resolution time (hours)
resolved_complaints = base_query.filter_by(status='resolved').all()
if resolved_complaints:
  resolution_times = [
    (c.resolved_at - c.created_at).total_seconds() / 3600 
    for c in resolved_complaints if c.resolved_at
  ]
  avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
else:
  avg_resolution_time = 0

# Calculate average assignment time (hours)
completed_assignments = ComplaintAssignment.query.filter_by(status='completed').all()
if completed_assignments:
  assignment_times = [
    (a.accepted_at - a.assigned_at).total_seconds() / 3600 
    for a in completed_assignments if a.accepted_at
  ]
  avg_assignment_time = sum(assignment_times) / len(assignment_times) if assignment_times else 0
else:
  avg_assignment_time = 0

# Field worker aggregated productivity
total_assignments = ComplaintAssignment.query.count()
completed_assignments_count = ComplaintAssignment.query.filter_by(status='completed').count()
worker_completion_rate = (completed_assignments_count / total_assignments * 100) if total_assignments > 0 else 0

# Complaint closure rate
closed_count = counts.get('closed', 0)
resolved_count = counts.get('resolved', 0)
closure_rate = (resolved_count + closed_count) / total * 100 if total > 0 else 0

# Citizen satisfaction rating
from app.models.feedback import Feedback
feedback_records = Feedback.query.all()
avg_satisfaction = (sum(f.rating for f in feedback_records) / len(feedback_records)) if feedback_records else 0

# High priority pending complaints
high_priority_pending = base_query.filter(
  Complaint.priority.in_(['urgent', 'high']),
  Complaint.status.in_(['pending', 'assigned'])
).count()
```

**Return enhanced dashboard data:**
```python
return {
  "scope": "municipal",  # or "system"
  # ... existing fields ...
  
  # NEW KPI metrics
  "avg_resolution_time_hours": avg_resolution_time,
  "avg_assignment_time_hours": avg_assignment_time,
  "closed_complaints_count": counts.get('closed', 0),
  "field_worker_completion_rate_percentage": worker_completion_rate,
  "complaint_closure_rate_percentage": closure_rate,
  "citizen_satisfaction_rating": avg_satisfaction,
  "high_priority_pending_count": high_priority_pending,
}
```

### Phase 2: Update API Documentation

**File:** `/docs/milestone3/openapi-with-user-stories.yaml`

Add detailed response schema for admin dashboard showing all KPI fields with examples.

### Phase 3: Add Tests

**File:** `/backend/tests/integration/test_admin_api.py`

Add test cases:
- `test_dashboard_includes_average_resolution_time` ✅
- `test_dashboard_includes_average_assignment_time` ✅
- `test_dashboard_closure_rate_calculation` ✅
- `test_dashboard_citizen_satisfaction_rating` ✅
- `test_dashboard_high_priority_pending_count` ✅

### Phase 4: Frontend Implementation (Not part of backend)

Dashboard should display:
- KPI Cards: Total complaints, Open complaints, Closed complaints, Citizen satisfaction
- Charts: Resolution time trend, Assignment time trend, Closure rate
- Alerts: High priority pending complaints
- Tables: Recent complaints, Field worker productivity

---

## 🧪 CURRENT TEST COVERAGE

### Tests for Admin Dashboard

| Test Case | Endpoint | Status |
|---|---|---|
| `test_admin_token_access_admin_dashboard` | `/admin/dashboard` | ✅ PASS |
| `test_non_admin_denied_admin_dashboard` | `/admin/dashboard` | ✅ PASS |
| `test_municipal_admin_dashboard_reflects_city_scoped_data` | `/admin/dashboard` | ✅ PASS |

**Missing Tests:**
- ❌ Average resolution time calculation
- ❌ Average assignment time calculation
- ❌ Closure rate percentage
- ❌ Citizen satisfaction rating
- ❌ High priority pending count
- ❌ Field worker productivity aggregation

---

## ✅ ACCEPTANCE CRITERIA STATUS

### AC1: Administrator can view all KPIs
**Current:** ⚠️ Partial  
**Gap:** Missing 5 of 9 KPIs  
**Fix:** Add missing calculations to dashboard service  
**Effort:** Medium (2-3 hours)

### AC2: Metrics calculated accurately
**Current:** ✅ Complete (for existing metrics)  
**Gap:** None for implemented metrics  
**Fix:** N/A

### AC3: Display charts and KPI cards
**Current:** ⚠️ Partial  
**Gap:** Dashboard returns data in flat JSON format  
**Fix:** Frontend needs to format into cards/charts  
**Note:** `/reports` endpoint provides chart-ready time-series data

### AC4: Auto-update when data changes
**Current:** ❌ Not implemented  
**Gap:** No real-time update mechanism  
**Options:**
1. Frontend polling every 30-60 seconds
2. WebSocket real-time updates (not implemented)
3. Scheduled background jobs (not feasible for real-time)
**Recommendation:** Frontend polling is acceptable for MVP

### AC5: Filter by date range
**Current:** ⚠️ Partial  
**Gap:** Dashboard doesn't support date filters  
**Alternative:** Reports endpoint has date filtering  
**Fix:** Add `date_from`/`date_to` parameters to dashboard endpoint  
**Effort:** Low (1 hour)

### AC6: Load successfully
**Current:** ✅ Complete  
**Evidence:** Dashboard endpoint loads correctly (tests passing)

---

## 📋 WORK ITEMS TO COMPLETE STORY

| Item | Complexity | Effort | Priority |
|---|---|---|---|
| Add avg_resolution_time_hours | Low | 15 min | High |
| Add avg_assignment_time_hours | Low | 15 min | High |
| Add closed_complaints_count | Low | 5 min | High |
| Add field_worker_completion_rate | Low | 20 min | High |
| Add closure_rate_percentage | Low | 10 min | High |
| Add citizen_satisfaction_rating | Medium | 30 min | High |
| Add high_priority_pending_count | Low | 10 min | High |
| Add date_from/date_to filters | Low | 30 min | Medium |
| Create new tests | Low | 45 min | High |
| Update API documentation | Low | 20 min | Medium |
| **TOTAL** | **Low-Medium** | **~3 hours** | **High** |

---

## 🎓 CONCLUSION

**Current Status:** ⚠️ **PARTIALLY COVERED**

**What's Working:**
- ✅ Basic dashboard endpoint exists
- ✅ Total complaints available
- ✅ Open complaints available
- ✅ Access control working
- ✅ City scoping working
- ✅ Some tests passing

**What's Missing:**
- ❌ 5 of 9 KPI metrics
- ❌ Date filtering on dashboard
- ❌ Real-time updates
- ❌ Tests for new metrics

**To Complete Story:**
1. Add 7 missing KPI calculations to dashboard service
2. Add date filtering support
3. Create tests for new metrics
4. Update API documentation
5. Frontend displays in KPI card/chart format

**Estimated Effort:** 2-3 hours backend, 4-6 hours frontend

---

## 📝 RECOMMENDED NEXT STEPS

1. **Immediate (Backend):**
   - Add missing KPI calculations to dashboard service ✅
   - Write tests for new metrics ✅
   - Update API spec documentation ✅

2. **Short Term (Frontend):**
   - Create dashboard UI with KPI cards
   - Add charts for trends
   - Implement polling for auto-updates (30-60s interval)
   - Add date filter UI

3. **Future Enhancements:**
   - WebSocket real-time updates
   - Performance optimization for large datasets
   - Export dashboard to PDF/CSV
   - Custom KPI dashboard builder

---

**Analysis Completed:** 2026-07-31  
**Status:** Ready for implementation  
**No blocker issues, straightforward enhancements needed**
