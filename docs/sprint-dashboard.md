# Sprint Dashboard — Widget Specifications

> **Audience:** python-backend-engineer (Phase B3) — these specifications define the computation layer for `jira_get_sprint_metrics`, `jira_sprint_review`, and `jira_get_velocity` MCP tools.
>
> **NASSCOM Delivery Excellence thresholds** are applied as the baseline maturity reference. Levels referenced: L4+ (Optimising), L3 (Defined), L2 (Managed).

---

## Threshold Colour Conventions

| Colour | Meaning | Action |
|---|---|---|
| Green | Within acceptable range (L4+) | No action required |
| Amber | Approaching risk boundary (L3) | Monitor; SM reviews at standup |
| Red | Outside acceptable range (L2 or below) | Escalate; SM action required before end of day |

---

## Widget 1 — Velocity EWMA (Exponentially Weighted Moving Average)

### Overview

Tracks sprint-over-sprint delivery trend using an EWMA to smooth outliers and highlight sustained capacity changes.

| Field | Value |
|---|---|
| **Chart type** | Line chart — EWMA line overlaid on bar chart of raw velocity per sprint |
| **Data source** | Agile API `jira_get_velocity` → `GET rapid/charts/velocity?rapidViewId={boardId}` |
| **JQL fallback** | SM-007: closed-sprint Done issues with story points, grouped by sprint client-side |
| **Refresh frequency** | End of each sprint (on `jira_close_sprint` call) + on-demand |

### Formula

```
alpha = 2 / (N + 1)    where N = 6 (6-sprint smoothing window)

EWMA_1 = velocity_1    (seed with first sprint's raw velocity)

EWMA_t = (alpha × velocity_t) + ((1 - alpha) × EWMA_{t-1})
       for t = 2, 3, ..., T
```

Where:
- `velocity_t` = total story points completed in sprint `t` (sum of `completed.value` from Agile API velocity response)
- `alpha ≈ 0.2857` with N=6

### Coefficient of Variation (stability signal)

```
CV = stddev(velocity_1 ... velocity_N) / mean(velocity_1 ... velocity_N)
```

Computed over the last `N` sprints using the raw velocity series, not the EWMA.

### Threshold Alerts

| CV Range | Signal | Colour |
|---|---|---|
| CV < 0.15 | Stable capacity (L4+) | Green |
| 0.15 ≤ CV ≤ 0.25 | Moderate variability (L3) | Amber |
| CV > 0.25 | High variability — team capacity unstable (L2) | Red |

### Notes

- Seed the EWMA with the first sprint's raw velocity when fewer than 6 historical sprints are available; suppress the amber/red signal until 3 sprints of data exist.
- `velocityStatEntries` from the Agile API provides both `estimated.value` (committed) and `completed.value` (delivered). Use `completed.value` for velocity.

---

## Widget 2 — Sprint Burndown

### Overview

Tracks remaining work against the ideal linear burndown line to detect scope creep and delivery risk mid-sprint.

| Field | Value |
|---|---|
| **Chart type** | Area chart — actual remaining story points vs ideal line |
| **Data source** | Agile API `jira_get_sprint_metrics` → `GET rapid/charts/burndown?rapidViewId={boardId}&sprintId={sprintId}` |
| **JQL fallback** | SM-003 (completed) + SM-004 (scope added) combined to reconstruct remaining points per day |
| **Refresh frequency** | Every 4 hours during active sprint |

### Formula

```
Ideal_remaining(day) = Total_SP × (1 - day / sprint_days)

Where:
  Total_SP    = total story points at sprint start (from burndown API startTime snapshot)
  day         = current day index (0 = sprint start, sprint_days = sprint end)
  sprint_days = (endDate - startDate).days from AGI-002 sprint metadata

Deviation% = |Actual_remaining - Ideal_remaining| / Total_SP × 100
```

### Threshold Alerts

| Deviation% | Signal | Colour |
|---|---|---|
| < 10% | On track (L4+) | Green |
| 10% – 25% | Risk — review sprint scope (L3) | Amber |
| > 25% | Off track — SM intervention required (L2) | Red |

### Notes

- The burndown API `changes` dict uses Unix epoch millisecond keys. Convert to day index: `day = (int(ts)/1000 - sprint_start_epoch) / 86400`.
- Scope changes (SM-004) inflate `Total_SP` mid-sprint; recalculate ideal line from the new total when scope is added.
- A flat burndown line (Actual_remaining unchanging over 2+ days) combined with deviation > 10% should trigger the impediment auto-label rule (Automation Rule 1).

---

## Widget 3 — Cumulative Flow Diagram (CFD) Proxy

### Overview

Approximates a CFD using WIP band width to detect bottlenecks and apply Little's Law for cycle time forecasting.

| Field | Value |
|---|---|
| **Chart type** | Stacked area chart — issue count per status category over time |
| **Data source** | Agile API `jira_sprint_review` → `GET board/{boardId}/sprint/{sprintId}/issue` with `fields=status,created,resolutiondate` |
| **JQL fallback** | SM-001 (current sprint issues by status) — executed once per refresh; status counts aggregated client-side |
| **Refresh frequency** | Every 4 hours during active sprint |

### Formula

```
WIP = count of issues in statusCategory "In Progress"

Throughput (TH) = issues transitioned to Done per day
               = count(Done issues) / elapsed_sprint_days

Cycle Time (CT) via Little's Law:
  CT = WIP / TH    (in days)

WIP_limit = team_size × 2
```

### Threshold Alerts

| Condition | Signal | Colour |
|---|---|---|
| WIP ≤ team_size × 2 | Healthy flow (L4+) | Green |
| WIP > team_size × 2 | Overloaded — flow at risk (L3) | Amber |
| WIP > team_size × 3 | Bottleneck — SM must identify and remove blockers (L2) | Red |

### Notes

- `team_size` is not available from the Agile API; it must be passed as a configuration parameter to the MCP tool (e.g., `team_size` field in tool input or `JIRA_TEAM_SIZE` environment variable).
- For the CFD stacked area chart, record a daily snapshot at a consistent time (e.g., 18:00 local) to produce comparable data points.
- Little's Law assumption: stable system. Warn if sprint scope changed more than 15% (detectable via SM-004) as this invalidates the CT estimate.

---

## Widget 4 — Cycle Time P85

### Overview

Measures the 85th percentile cycle time from issue start to resolution within the sprint, to establish a predictable delivery SLA.

| Field | Value |
|---|---|
| **Chart type** | Scatter plot (individual issue cycle times) with P85 horizontal line |
| **Data source** | Agile API `jira_sprint_review` → issue list with `fields=status,resolutiondate,changelog` |
| **JQL fallback** | SM-003 (Done issues this sprint) — fetch with `expand=changelog` to get `In Progress` transition timestamp |
| **Refresh frequency** | On sprint close (`jira_close_sprint`) + on-demand |

### Formula

```
CT_i = resolved_date_i - in_progress_date_i    (in days, fractional)

Where:
  resolved_date_i    = issue.fields.resolutiondate (ISO-8601, parsed to datetime)
  in_progress_date_i = earliest changelog entry where items[].toString == "In Progress"

Sort CT values ascending: CT_sorted = [CT_1, CT_2, ..., CT_n]

P85_index = ceil(0.85 × n)    (1-based index into sorted array)

CT_P85 = CT_sorted[P85_index - 1]    (0-based Python list access)
```

### Threshold Alerts

| CT P85 | Signal | Colour |
|---|---|---|
| < 3 days | Fast delivery (L4+) | Green |
| 3 – 7 days | Acceptable — monitor (L3) | Amber |
| > 7 days | Slow — workflow impediment likely (L2) | Red |

### Notes

- Issues with no `In Progress` transition (e.g., moved directly from To Do → Done) should be excluded from CT calculation and counted separately as `direct_done_count`.
- If `n < 5`, suppress P85 display and show a "Insufficient data" message rather than an unreliable percentile.
- For unit tests (CONTRACT #4): mock `urllib.request.urlopen` to return a changelog response with two transition entries. Verify `CT_P85` matches the expected percentile from the mock data set.

---

## Widget 5 — DoD Compliance Rate

### Overview

Measures the percentage of Done stories that have all DoD checklist sub-tasks closed, enforcing the Definition of Done quality gate.

| Field | Value |
|---|---|
| **Chart type** | Gauge chart (percentage) + trend sparkline (last 6 sprints) |
| **Data source** | Agile API `jira_sprint_review` → issue list with `fields=status,subtasks,issuetype` |
| **JQL fallback** | SM-008 (Done stories with all sub-tasks closed) as numerator; SM-003 as denominator |
| **Refresh frequency** | On sprint close (`jira_close_sprint`) |

### Formula

```
issues_done = count of sprint issues where:
  - issueType in (Story, Task)
  - statusCategory == Done

issues_dod_compliant = count of issues_done where:
  - ALL sub-tasks have statusCategory == Done
  - OR issue has no sub-tasks (counted as compliant if team policy permits)

DoD_Compliance_Rate = (issues_dod_compliant / issues_done) × 100    (percentage)
```

### Threshold Alerts

| DoD% | Signal | Colour |
|---|---|---|
| > 85% | Compliant (L4+) | Green |
| 70% – 85% | Partial compliance — review process (L3) | Amber |
| < 70% | Non-compliant — DoD process failing (L2) | Red |

### Notes

- Sub-task closure check: for each `issue.fields.subtasks[]` entry, the status must be fetched individually via REST API or the Agile API issue response if subtask status is embedded. Cache sub-task statuses to avoid N+1 requests.
- Issues with zero sub-tasks: team policy determines whether they count as compliant. Recommended default: compliant only if DoD checklist sub-task was never required (e.g., issue type = Bug with a hotfix label). Document this policy as a tool configuration parameter.
- The trend sparkline requires storing DoD% per sprint; persist this in the session state or a lightweight cache between `jira_close_sprint` calls.

---

## Widget 6 — Impediment Mean Time to Resolution (MTTR)

### Overview

Measures the average time from impediment label application to issue resolution, quantifying Scrum Master effectiveness in removing blockers.

| Field | Value |
|---|---|
| **Chart type** | Bar chart (MTTR per sprint) + horizontal threshold lines |
| **Data source** | JQL `jira_search_issues` (primary — no Agile API equivalent for label-based queries) |
| **JQL query** | IM-003 (impediments resolved this sprint) with `expand=changelog` to get label application timestamp |
| **Refresh frequency** | On sprint close (`jira_close_sprint`) |

### Formula

```
For each resolved impediment i:
  label_applied_date_i  = earliest changelog entry where items[].toString contains "impediment"
  resolved_date_i       = issue.fields.resolutiondate (ISO-8601)

  resolution_time_i = resolved_date_i - label_applied_date_i    (in days)

MTTR = sum(resolution_time_1 ... resolution_time_n) / n    (arithmetic mean, in days)
```

### Threshold Alerts

| MTTR | Signal | Colour |
|---|---|---|
| < 2 days | Fast resolution (L4+) | Green |
| 2 – 5 days | Moderate — escalation may be needed (L3) | Amber |
| > 5 days | Slow — systemic impediment pattern (L2) | Red |

### Notes

- If `label_applied_date` is unavailable (e.g., the label was applied before changelog was enabled), fall back to `issue.fields.created` as an approximation with a warning flag on the widget.
- Issues carrying the `impediment` label but never reaching Done status are **open impediments** and are excluded from MTTR calculation. They should appear in the IM-001 query results.
- For IM-002 escalation trigger correlation: if MTTR > 5 days AND open impediments from IM-002 count > 0, emit a combined alert: "Persistent impediment pattern detected — MTTR {X} days with {N} impediments > 2 days open."

---

## Widget 7 — Team Health Score (THS)

### Overview

A composite score across multiple delivery dimensions to provide a single-number team health indicator aligned with agile maturity frameworks.

| Field | Value |
|---|---|
| **Chart type** | Radar chart (6 dimensions) + composite score gauge |
| **Data source** | Composite — aggregates outputs from Widgets 1–6 + input from `jira_sprint_review` |
| **Refresh frequency** | On sprint close (`jira_close_sprint`) |

### Dimensions and Weights

| # | Dimension | Source Widget / Query | Weight |
|---|---|---|---|
| D1 | Velocity Stability (1 - CV) | Widget 1 — EWMA CV | 0.20 |
| D2 | Burndown Adherence (1 - deviation%) | Widget 2 | 0.20 |
| D3 | WIP Discipline (1 - WIP/WIP_limit, capped [0,1]) | Widget 3 | 0.15 |
| D4 | Cycle Time (inverse normalised vs P85 target) | Widget 4 | 0.15 |
| D5 | DoD Compliance Rate | Widget 5 | 0.20 |
| D6 | Impediment MTTR (inverse normalised vs 2-day target) | Widget 6 | 0.10 |

### Formula

```
Each dimension D_k is normalised to a [0, 1] scale where 1.0 = best:

  D1_norm = max(0, 1 - CV)
  D2_norm = max(0, 1 - (deviation_pct / 100))
  D3_norm = max(0, min(1, 1 - (WIP / WIP_limit - 1)))    capped at [0, 1]
  D4_norm = max(0, min(1, 3 / CT_P85))    3-day target; capped at 1.0
  D5_norm = DoD_Compliance_Rate / 100
  D6_norm = max(0, min(1, 2 / MTTR))      2-day target; capped at 1.0

Weights = [0.20, 0.20, 0.15, 0.15, 0.20, 0.10]    (sum = 1.00)

THS = (D1_norm × 0.20 + D2_norm × 0.20 + D3_norm × 0.15
      + D4_norm × 0.15 + D5_norm × 0.20 + D6_norm × 0.10) × 10

THS range: [0, 10]
```

### Threshold Alerts

| THS | Signal | Colour |
|---|---|---|
| > 7.0 / 10 | Healthy team (L4+) | Green |
| 5.0 – 7.0 / 10 | Improvement needed (L3) | Amber |
| < 5.0 / 10 | Team at risk — SM intervention required (L2) | Red |

### Notes

- All six widget values must be computed before THS can be calculated. If any widget returns insufficient data (e.g., fewer than 3 sprints for velocity), substitute the dimension with `0.5` (neutral) and flag the score as `partial` in the response payload.
- The radar chart axes should display the raw normalised dimension scores (D1_norm through D6_norm) scaled to [0, 10] for display consistency.
- Store THS per sprint to enable trend visualisation over time. A declining THS over 3 consecutive sprints should trigger an automatic retrospective flag comment on the board's current sprint.
- THS is an internal dashboard metric only — it must not be surfaced to stakeholders outside the Scrum Master role without explicit team agreement.
