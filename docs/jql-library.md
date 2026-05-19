# JQL Library — Scrum Master Pipeline

> **Contracts honoured:**
> - CONTRACT #1: Agile API is the primary data source. JQL queries in this file are the documented fallback when the Agile API endpoint is unavailable or returns insufficient data.
> - CONTRACT #2: All Agile API paths are relative to `/rest/agile/1.0/` (prefix excluded).
> - CONTRACT #4: All JQL `{PARAM}` placeholders map 1-to-1 to Python variables that can be injected into mocked `urllib.request.urlopen` responses in unit tests.

---

## Parameter Legend

| Placeholder | Type | Example |
|---|---|---|
| `{PROJECT}` | string | `PROJ` |
| `{SPRINT_NAME}` | string | `Sprint 12` |
| `{BOARD_ID}` | integer | `42` |
| `{N_SPRINTS}` | integer | `6` |
| `{FIX_VERSION}` | string | `v2.4.0` |
| `{DAYS_AGO}` | integer | `30` |

---

## Section 1: Sprint Metrics

### SM-001 — Issues in current sprint by assignee

```jql
project = "{PROJECT}"
  AND sprint = "{SPRINT_NAME}"
  AND sprint in openSprints()
  AND assignee is not EMPTY
ORDER BY assignee ASC, status ASC
```

**Purpose:** Assigns per-person workload snapshot for standup preparation.
**Selectivity note:** Returns all open-sprint issues; narrow with `statusCategory != Done` to exclude completed work.
**Recommended maxResults:** 100
**Primary source:** `jira_get_boards` → `jira_sprint_review` (Agile API `/board/{boardId}/sprint/{sprintId}/issue`)
**Fallback:** This JQL query.

---

### SM-002 — Blocked issues in current sprint

```jql
project = "{PROJECT}"
  AND sprint = "{SPRINT_NAME}"
  AND sprint in openSprints()
  AND (status = "Blocked" OR labels = "impediment")
  AND statusCategory != Done
ORDER BY priority ASC, created ASC
```

**Purpose:** Surfaces all impediments requiring Scrum Master action.
**Selectivity note:** Depends on your workflow having a "Blocked" status OR teams using the `impediment` label consistently. Both conditions are ORed to maximise recall.
**Recommended maxResults:** 50
**Primary source:** `jira_get_sprints` + issue detail (Agile API).
**Fallback:** This JQL query.

---

### SM-003 — Issues completed this sprint

```jql
project = "{PROJECT}"
  AND sprint = "{SPRINT_NAME}"
  AND status = Done
  AND status CHANGED TO Done AFTER startOfSprint("{SPRINT_NAME}")
ORDER BY resolutiondate DESC
```

**Purpose:** Measures delivered scope within sprint boundaries.
**Selectivity note:** `status CHANGED TO Done AFTER` filters out issues that carried a Done status from a previous sprint and were re-added.
**Recommended maxResults:** 100
**Primary source:** Agile API `/rapid/charts/burndown` (velocity endpoint).
**Fallback:** This JQL query.

---

### SM-004 — Scope change since sprint start (added after sprint started)

```jql
project = "{PROJECT}"
  AND sprint = "{SPRINT_NAME}"
  AND sprint in openSprints()
  AND issueFunction in addedAfterSprintStart("{PROJECT}", "{SPRINT_NAME}")
ORDER BY created ASC
```

**Purpose:** Tracks mid-sprint scope creep for retrospective analysis.
**Selectivity note:** Requires `jira-misc-workflow-extensions` or equivalent plugin for `issueFunction`. Without it use: `sprint = "{SPRINT_NAME}" AND created > startOfSprint("{SPRINT_NAME}")` as a proxy.
**Recommended maxResults:** 50
**Primary source:** Agile API `/board/{boardId}/sprint/{sprintId}/issue` with `addedAfterSprintStart` filter.
**Fallback:** This JQL query (plugin-dependent variant or date-proxy variant).

---

### SM-005 — Story points completed this sprint

```jql
project = "{PROJECT}"
  AND sprint = "{SPRINT_NAME}"
  AND status = Done
  AND "Story Points" is not EMPTY
ORDER BY resolutiondate DESC
```

**Purpose:** Denominator for velocity calculation. Sum `story_points` field on result set client-side.
**Selectivity note:** Field name varies by instance — common alternatives: `story_points`, `customfield_10016`, `sp`. Confirm field name via `/rest/api/2/field`.
**Recommended maxResults:** 100
**Primary source:** Agile API `/rapid/charts/velocity?rapidViewId={BOARD_ID}` — velocity per sprint already aggregated.
**Fallback:** This JQL query (requires client-side aggregation).

---

### SM-006 — Unestimated issues in sprint

```jql
project = "{PROJECT}"
  AND sprint = "{SPRINT_NAME}"
  AND sprint in openSprints()
  AND "Story Points" is EMPTY
  AND issueType in (Story, Task, Bug)
ORDER BY priority ASC, created ASC
```

**Purpose:** Identifies estimation gaps before sprint midpoint.
**Selectivity note:** Excludes Sub-tasks and Epics intentionally; they are rarely point-estimated.
**Recommended maxResults:** 50
**Primary source:** Agile API sprint issue list filtered client-side for `story_points == null`.
**Fallback:** This JQL query.

---

### SM-007 — Sprint velocity proxy — issues resolved in last N sprints

```jql
project = "{PROJECT}"
  AND sprint in closedSprints()
  AND status = Done
  AND "Story Points" is not EMPTY
  AND sprint not in openSprints()
ORDER BY sprint DESC
```

**Purpose:** Provides a multi-sprint velocity dataset for EWMA calculation (Widget 1 in sprint-dashboard.md).
**Selectivity note:** Returns ALL closed-sprint Done issues; limit to last `{N_SPRINTS}` by post-filtering on sprint name or using sprint ordering. The Agile API velocity chart is strongly preferred.
**Recommended maxResults:** `{N_SPRINTS}` x avg_issues_per_sprint (default 200)
**Primary source:** Agile API `/rapid/charts/velocity?rapidViewId={BOARD_ID}`.
**Fallback:** This JQL query with client-side grouping by sprint.

---

### SM-008 — DoD compliance proxy — Done issues with all sub-tasks closed

```jql
project = "{PROJECT}"
  AND sprint = "{SPRINT_NAME}"
  AND status = Done
  AND issueType in (Story, Task)
  AND subtasks not in openIssues()
ORDER BY resolutiondate DESC
```

**Purpose:** Identifies stories where Definition of Done sub-tasks are all closed, used as numerator for DoD Compliance Rate (Widget 5).
**Selectivity note:** `subtasks not in openIssues()` is a JQL extension; some instances require scripted field evaluation instead. Fallback: fetch parent + sub-task status via REST and evaluate client-side.
**Recommended maxResults:** 100
**Primary source:** Client-side evaluation against Agile API issue list.
**Fallback:** This JQL query.

---

## Section 2: Backlog Health

### BH-001 — Unestimated stories in backlog

```jql
project = "{PROJECT}"
  AND sprint is EMPTY
  AND issueType = Story
  AND "Story Points" is EMPTY
  AND statusCategory != Done
ORDER BY priority ASC, created ASC
```

**Purpose:** Surfaces backlog refinement candidates for the next sprint planning session.
**Selectivity note:** `sprint is EMPTY` targets pure backlog items only; it excludes items in future sprints.
**Recommended maxResults:** 100

---

### BH-002 — Stories without assignee in backlog

```jql
project = "{PROJECT}"
  AND sprint is EMPTY
  AND issueType = Story
  AND assignee is EMPTY
  AND statusCategory != Done
ORDER BY priority ASC, created ASC
```

**Purpose:** Identifies ownership gaps before sprint planning to enable faster commitment.
**Selectivity note:** High-priority unassigned issues are the most urgent; combine with `priority in (High, Highest)` for focused view.
**Recommended maxResults:** 100

---

### BH-003 — Overdue epics

```jql
project = "{PROJECT}"
  AND issueType = Epic
  AND statusCategory != Done
  AND duedate < now()
ORDER BY duedate ASC
```

**Purpose:** Escalation trigger for programme-level delays affecting sprint planning horizon.
**Selectivity note:** Only meaningful if epics have `duedate` populated. Returns zero rows otherwise — verify field usage before exposing in dashboards.
**Recommended maxResults:** 50

---

### BH-004 — High-priority unassigned issues

```jql
project = "{PROJECT}"
  AND priority in (High, Highest, Blocker, Critical)
  AND assignee is EMPTY
  AND statusCategory != Done
  AND sprint is EMPTY
ORDER BY priority ASC, created ASC
```

**Purpose:** Ensures no urgent work sits unowned in the backlog between sprints.
**Selectivity note:** Priority names vary by project scheme. Verify against your project's priority scheme; common alternatives include `Blocker`, `Critical`, `P1`.
**Recommended maxResults:** 50

---

### BH-005 — Issues older than 30 days with no activity

```jql
project = "{PROJECT}"
  AND sprint is EMPTY
  AND statusCategory not in (Done)
  AND updated < -{DAYS_AGO}d
ORDER BY updated ASC
```

**Purpose:** Identifies stale backlog items for grooming or archival.
**Selectivity note:** `{DAYS_AGO}` defaults to 30. Set to 60 or 90 for mature projects with longer planning horizons. Use `updated` not `created` — updated reflects last comment/transition activity.
**Recommended maxResults:** 100

---

### BH-006 — Backlog issues without acceptance criteria label

```jql
project = "{PROJECT}"
  AND sprint is EMPTY
  AND issueType = Story
  AND statusCategory != Done
  AND labels not in ("has-ac", "acceptance-criteria")
ORDER BY priority ASC, created ASC
```

**Purpose:** Enforces the team convention of labelling stories that have acceptance criteria defined.
**Selectivity note:** Effectiveness depends on disciplined label usage. Alternative: use a custom field `Acceptance Criteria` and filter `"Acceptance Criteria" is EMPTY`.
**Recommended maxResults:** 100

---

## Section 3: Impediment Tracking

### IM-001 — All open impediments

```jql
project = "{PROJECT}"
  AND labels = "impediment"
  AND statusCategory != Done
ORDER BY created ASC
```

**Purpose:** Master impediment list for Scrum Master's daily review.
**Selectivity note:** Relies on the `impediment` label being applied consistently (see Automation Rule 1). Combine with `sprint in openSprints()` to scope to current sprint only.
**Recommended maxResults:** 50

---

### IM-002 — Impediments open more than 2 days (escalation trigger)

```jql
project = "{PROJECT}"
  AND labels = "impediment"
  AND statusCategory != Done
  AND created <= -2d
ORDER BY created ASC
```

**Purpose:** Escalation trigger — any impediment open longer than 48 hours should be raised to management.
**Selectivity note:** `-2d` is relative to query execution time. For exact sprint-start-relative calculation, use the Agile API issue list and compute client-side using `created` timestamp.
**Recommended maxResults:** 50

---

### IM-003 — Impediments resolved this sprint

```jql
project = "{PROJECT}"
  AND sprint = "{SPRINT_NAME}"
  AND labels = "impediment"
  AND status CHANGED TO Done AFTER startOfSprint("{SPRINT_NAME}")
ORDER BY resolutiondate DESC
```

**Purpose:** Retrospective data — shows SM effectiveness in clearing impediments within sprint.
**Selectivity note:** Requires `status CHANGED TO` history traversal; may be slow on large projects. Add `AND project = "{PROJECT}"` to help the query planner use the project index.
**Recommended maxResults:** 50

---

### IM-004 — Impediments by resolution layer label

```jql
project = "{PROJECT}"
  AND labels = "impediment"
  AND statusCategory != Done
  AND labels in ("team-layer", "management-layer", "org-layer")
ORDER BY labels ASC, created ASC
```

**Purpose:** Escalation routing — separates issues the team can self-resolve from those requiring management or organisational intervention.
**Selectivity note:** Three mutually exclusive layer labels must be applied by the Scrum Master. Issues without a layer label will not appear here — supplement with IM-001 to catch unlabelled impediments.
**Recommended maxResults:** 50

---

## Section 4: Release Tracking

### RT-001 — Issues by fix version, unresolved

```jql
project = "{PROJECT}"
  AND fixVersion = "{FIX_VERSION}"
  AND resolution is EMPTY
ORDER BY priority ASC, issueType ASC, status ASC
```

**Purpose:** Release scope view showing all outstanding work for a given version.
**Selectivity note:** Resolution field is more reliable than `status != Done` for release tracking because it persists across workflow changes.
**Recommended maxResults:** 200

---

### RT-002 — Issues blocking release (linked blocker type)

```jql
project = "{PROJECT}"
  AND fixVersion = "{FIX_VERSION}"
  AND resolution is EMPTY
  AND issue in linkedIssues("{PROJECT}", "is blocked by")
ORDER BY priority ASC, created ASC
```

**Purpose:** Critical path for release gate — these issues cannot ship until their blockers are resolved.
**Selectivity note:** Link type name varies: `"is blocked by"`, `"blocks"`, `"Blocker"`. Confirm via `/rest/api/2/issueLinkType`.
**Recommended maxResults:** 100

---

### RT-003 — Unresolved critical or blocker priority issues

```jql
project = "{PROJECT}"
  AND fixVersion = "{FIX_VERSION}"
  AND resolution is EMPTY
  AND priority in (Blocker, Critical, Highest)
ORDER BY priority ASC, created ASC
```

**Purpose:** Release readiness gate — any issue in this set blocks go/no-go decision.
**Selectivity note:** Priority names must match your project's priority scheme. Highest is the standard Jira term; Blocker/Critical are common custom schemes.
**Recommended maxResults:** 100

---

### RT-004 — Release candidate issues

```jql
project = "{PROJECT}"
  AND fixVersion = "{FIX_VERSION}"
  AND resolution is not EMPTY
  AND status = Done
ORDER BY resolutiondate DESC
```

**Purpose:** Positive release scope — issues confirmed resolved and included in the release build.
**Selectivity note:** Cross-reference with RT-001 (unresolved) to derive total release completeness percentage client-side: `done / (done + unresolved) x 100`.
**Recommended maxResults:** 200

---

## Section 5: SLA Breach

### SL-001 — Issues past due date in current sprint

```jql
project = "{PROJECT}"
  AND sprint = "{SPRINT_NAME}"
  AND sprint in openSprints()
  AND duedate < now()
  AND statusCategory != Done
ORDER BY duedate ASC
```

**Purpose:** Immediate SLA breach alert — these issues have breached their committed delivery date.
**Selectivity note:** Meaningful only if issues have `duedate` set. Many teams use sprint end date as implicit due date — if so, this query should compare against the sprint end date retrieved from the Agile API.
**Recommended maxResults:** 50

---

### SL-002 — Stories not started by sprint midpoint

```jql
project = "{PROJECT}"
  AND sprint = "{SPRINT_NAME}"
  AND sprint in openSprints()
  AND status = "To Do"
  AND issueType in (Story, Task)
ORDER BY priority ASC, created ASC
```

**Purpose:** Early-warning indicator that sprint commitment is at risk.
**Selectivity note:** Query must be executed after the sprint midpoint date (computed from Agile API `sprint.startDate` + `sprint.endDate`). Execute client-side time check before running this query.
**Recommended maxResults:** 50

---

### SL-003 — Issues open longer than story-point x 2 days

```jql
project = "{PROJECT}"
  AND sprint = "{SPRINT_NAME}"
  AND sprint in openSprints()
  AND statusCategory != Done
  AND "Story Points" is not EMPTY
  AND created < -{DAYS_AGO}d
ORDER BY created ASC
```

**Purpose:** Proxy for cycle-time SLA breach where `{DAYS_AGO}` = `story_points * 2` (computed per issue client-side and used as a fixed filter for the batch query).
**Selectivity note:** Because JQL cannot do per-row arithmetic comparisons, the client must: (1) fetch all open sprint issues, (2) compute `age_days > story_points * 2` per issue, (3) surface violations. This JQL returns a superset; filter client-side.
**Recommended maxResults:** 100

---

## Agile API Endpoint Reference

> All paths are **relative to `/rest/agile/1.0/`** per CONTRACT #2. The `agile_client.py` helper `_agile_request(cfg, method, path, body=None)` prepends the full base URL automatically.

---

### AGI-001 — List boards

| Field | Value |
|---|---|
| **Method** | `GET` |
| **Path** | `board` |
| **MCP Tool** | `jira_get_boards` |
| **Key request params** | `projectKeyOrId` (optional), `type` (`scrum` \| `kanban`), `startAt`, `maxResults` |
| **Key response fields** | `values[].id`, `values[].name`, `values[].type`, `values[].location.projectKey` |
| **Cloud availability** | Yes |
| **Server/DC availability** | Yes (Jira Software 7.x+) |
| **JQL fallback** | Not applicable — no JQL equivalent for board listing |

---

### AGI-002 — List sprints for a board

| Field | Value |
|---|---|
| **Method** | `GET` |
| **Path** | `board/{boardId}/sprint` |
| **MCP Tool** | `jira_get_sprints` |
| **Key request params** | `state` (`active` \| `future` \| `closed`), `startAt`, `maxResults` |
| **Key response fields** | `values[].id`, `values[].name`, `values[].state`, `values[].startDate`, `values[].endDate`, `values[].goal` |
| **Cloud availability** | Yes |
| **Server/DC availability** | Yes |
| **JQL fallback** | `sprint in openSprints() AND project = "{PROJECT}"` (returns issues, not sprint metadata) |

---

### AGI-003 — Create sprint

| Field | Value |
|---|---|
| **Method** | `POST` |
| **Path** | `sprint` |
| **MCP Tool** | `jira_create_sprint` |
| **Key request params (body)** | `name` (string), `originBoardId` (integer), `startDate` (ISO-8601), `endDate` (ISO-8601), `goal` (string, optional) |
| **Key response fields** | `id`, `name`, `state`, `startDate`, `endDate`, `originBoardId` |
| **Cloud availability** | Yes |
| **Server/DC availability** | Yes |
| **JQL fallback** | Not applicable — write operation |
| **Note** | Sprint is created in `future` state; must be activated via AGI-004 |

---

### AGI-004 — Update sprint state (start / close)

| Field | Value |
|---|---|
| **Method** | `POST` |
| **Path** | `sprint/{sprintId}` |
| **MCP Tools** | `jira_start_sprint`, `jira_close_sprint` |
| **Key request params (body)** | `state` (`active` to start, `closed` to close), `startDate` (required when activating), `endDate` (required when activating) |
| **Key response fields** | `id`, `state`, `startDate`, `endDate` |
| **Cloud availability** | Yes |
| **Server/DC availability** | Yes |
| **JQL fallback** | Not applicable — write operation |
| **Note** | Only one sprint per board can be in `active` state. Attempting to activate a second sprint returns HTTP 400. |

---

### AGI-005 — Issues in a sprint (Agile board view)

| Field | Value |
|---|---|
| **Method** | `GET` |
| **Path** | `board/{boardId}/sprint/{sprintId}/issue` |
| **MCP Tools** | `jira_sprint_review`, `jira_daily_standup` (fallback path) |
| **Key request params** | `jql` (additional filter), `fields` (comma-separated field list), `startAt`, `maxResults` |
| **Key response fields** | `issues[].key`, `issues[].fields.summary`, `issues[].fields.status.name`, `issues[].fields.assignee.displayName`, `issues[].fields.story_points`, `issues[].fields.labels`, `issues[].fields.subtasks` |
| **Cloud availability** | Yes |
| **Server/DC availability** | Yes |
| **JQL fallback** | `project = "{PROJECT}" AND sprint = "{SPRINT_NAME}"` — see SM-001 through SM-008 |

---

### AGI-006 — Velocity chart data

| Field | Value |
|---|---|
| **Method** | `GET` |
| **Path** | `rapid/charts/velocity?rapidViewId={boardId}` |
| **MCP Tool** | `jira_get_velocity` |
| **Key request params** | `rapidViewId` (required, same as `boardId`) |
| **Key response fields** | `sprints[].id`, `sprints[].name`, `velocityStatEntries.{sprintId}.estimated.value`, `velocityStatEntries.{sprintId}.completed.value` |
| **Cloud availability** | Yes (GreenHopper/Software API) |
| **Server/DC availability** | Yes (Jira Software 7.x+; may require Agile licence) |
| **JQL fallback** | SM-007 with client-side grouping and summation |
| **Note** | `rapid/charts/` prefix is part of the GreenHopper legacy API surface; behaviour is identical on Cloud and Server but not versioned under `/agile/1.0/`. Include full path suffix in `_agile_request` path argument. |

---

### AGI-007 — Burndown chart data

| Field | Value |
|---|---|
| **Method** | `GET` |
| **Path** | `rapid/charts/burndown?rapidViewId={boardId}&sprintId={sprintId}` |
| **MCP Tool** | `jira_get_sprint_metrics` |
| **Key request params** | `rapidViewId` (required), `sprintId` (required) |
| **Key response fields** | `changes` (dict keyed by timestamp), `changes.{ts}[].column.notDone` (remaining points), `startTime`, `endTime`, `completeTime`, `isInitialEstimateStatistic` |
| **Cloud availability** | Yes |
| **Server/DC availability** | Yes (Jira Software 7.x+) |
| **JQL fallback** | SM-003 (completed) + SM-004 (scope change) combined for a manual burndown approximation |
| **Note** | Response structure uses Unix epoch milliseconds as keys inside `changes`. Parse as `int(ts) / 1000` for Python `datetime`. |

---

### AGI-008 — Move issues to sprint

| Field | Value |
|---|---|
| **Method** | `POST` |
| **Path** | `sprint/{sprintId}/issue` |
| **MCP Tool** | (internal helper; not exposed as standalone MCP tool) |
| **Key request params (body)** | `issues` (list of issue keys, e.g. `["PROJ-1", "PROJ-2"]`) |
| **Key response fields** | HTTP 204 No Content on success |
| **Cloud availability** | Yes |
| **Server/DC availability** | Yes |
| **JQL fallback** | Not applicable — write operation |
| **Note** | Used by `jira_create_sprint` implementation to bulk-assign seed issues after sprint creation. |
