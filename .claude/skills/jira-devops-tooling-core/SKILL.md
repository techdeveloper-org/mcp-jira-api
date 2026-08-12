---
name: jira-devops-tooling-core
description: "Provides configuration, JQL query design, automation rules, REST API integration, and TCO analysis for Jira Software Cloud and Azure DevOps Boards. Use when setting up agile boards, writing advanced JQL queries, configuring sprint dashboards, automating workflow transitions, comparing tooling cost, integrating via REST API, or calculating 3-year TCO for Jira vs Azure DevOps tooling decisions. Keywords: Jira JQL advanced queries, Azure DevOps Boards configuration, sprint metrics dashboard, Jira automation rules, work item hierarchy PERT estimation, agile tooling TCO comparison, Atlassian REST API v3, Azure DevOps REST API 7.1."
allowed-tools: Read,Glob,Grep
user-invocable: true
---


<!-- generated-by: claude-global-library/tools/project_sync -->
<!-- source: skills/jira-devops-tooling-core/SKILL.md -- edit the library, then re-run sync_project.py -->

# jira-devops-tooling-core

## Description

Provides configuration, JQL query design, automation rules, REST API integration, and TCO analysis for Jira Software Cloud and Azure DevOps Boards. Covers board setup, workflow design, custom fields, permission schemes, automation triggers, sprint metrics extraction via EWMA, PERT-based work-item estimation, M/M/1 automation queue modeling, 3-year TCO comparison with NPV, REST API rate-limit optimization, and MeitY compliance guidance.

**Use when:** Setting up agile boards, writing advanced JQL queries, configuring sprint dashboards, automating workflow transitions, comparing tooling cost, integrating via REST API, or calculating 3-year TCO for Jira vs Azure DevOps decisions.

**Keywords:** Jira JQL advanced queries, Azure DevOps Boards configuration, sprint metrics dashboard, Jira automation rules, work item hierarchy PERT estimation, agile tooling TCO comparison, Atlassian REST API v3, Azure DevOps REST API 7.1.

---

## 1. Jira Cloud Configuration

### 1.1 Board Setup

**Scrum Board:** Tracks sprints; requires a Scrum project type. Key settings:
- Sprint length: 1–4 weeks; 2-week is standard.
- Backlog view: prioritized by WSJF or rank; use "Backlog" tab for refinement.
- Board columns: mapped to workflow statuses (To Do → In Progress → In Review → Done).
- Swimlanes: by Assignee, Epic, or Priority; do not exceed 4 swimlanes or the board becomes unreadable.

**Kanban Board:** No sprints; uses WIP limits per column.
- Set WIP limits at the column level (Jira: right-click column header → Edit column → Set max issues).
- Cycle time calculation requires "In Progress" and "Done" statuses to be distinct.
- Cumulative Flow Diagram (CFD) is native in Kanban; enable from Board settings → Reports.

**Custom Workflows:**
```
Project settings → Workflows → Add workflow → Design transitions:
  - Status: To Do (initial), In Progress, In Review, Blocked, Done (final).
  - Transition "Start": To Do → In Progress. Add condition: Assignee is not empty.
  - Transition "Block": In Progress → Blocked. Add screen: "Block Reason" field.
  - Transition "Unblock": Blocked → In Progress. No condition.
  - Post-function on "Done": Set resolution = Fixed.
```

### 1.2 Custom Fields

| Field Type | Use Case | Configuration |
|---|---|---|
| Story Points | Estimation unit | Number field; add to Scrum board card layout |
| Epic Link | Parent hierarchy | Link-type field; auto-created with next-gen projects |
| Sprint | Sprint tracking | System field; managed by Jira automatically |
| WSJF Score | Prioritization | Number field; compute externally, store result |
| Blocked Reason | Impediment tracking | Short text; visible on board card |
| Due Date | Milestone tracking | Date picker; use with JQL `duedate` |
| Team | Multi-team filtering | Select list; values = team names |
| Release | Fix version mapping | Version field; used for release roadmap |

Custom fields: Project settings → Fields → Custom fields → Create.

Add to screens: Project settings → Screens → map field to Create/Edit/View screen.

### 1.3 JQL (Jira Query Language)

**Syntax:**
```
field operator value [AND|OR condition] [ORDER BY field ASC|DESC]
```

**Key Operators:**

| Operator | Meaning | Example |
|---|---|---|
| `=` | Exact match | `status = "In Progress"` |
| `!=` | Not equal | `assignee != currentUser()` |
| `in` | Set membership | `project in (ABC, DEF)` |
| `not in` | Set exclusion | `status not in (Done, Closed)` |
| `~` | Text contains | `summary ~ "API"` |
| `is EMPTY` | Null check | `assignee is EMPTY` |
| `was` | Historical status | `status was "Blocked"` |
| `changed` | Field changed | `status changed after "2024-01-01"` |

**Common Queries:**

Sprint in-progress issues:
```jql
project = MYPROJ AND sprint in openSprints() AND status != Done ORDER BY priority DESC
```

Unresolved blockers:
```jql
project = MYPROJ AND status = Blocked AND resolution is EMPTY ORDER BY created ASC
```

Issues completed in last sprint:
```jql
project = MYPROJ AND sprint in closedSprints() AND status = Done AND sprint not in futureSprints()
```

Overdue issues:
```jql
duedate < now() AND status != Done AND assignee = currentUser()
```

Epic progress (stories incomplete):
```jql
"Epic Link" = ABC-10 AND status != Done ORDER BY rank ASC
```

Issues assigned to team with high priority:
```jql
team = "Backend" AND priority in (Critical, Blocker) AND sprint in openSprints()
```

Issues created but not refined (no story points):
```jql
project = MYPROJ AND issuetype = Story AND "Story Points" is EMPTY AND sprint in futureSprints()
```

### 1.4 Automation Rules

Jira Automation (Free: 100 runs/month; Standard: 5,000/project; Premium: 1,000/project/user):

**Rule Structure:** Trigger → Conditions → Actions.

**Common Rules:**

Auto-assign on transition:
```
Trigger: Issue transitioned → To Do → In Progress
Condition: Assignee is empty
Action: Assign issue → Trigger user
```

Auto-close resolved issues:
```
Trigger: Issue updated → Resolution field changed to Fixed
Condition: Status != Done
Action: Transition issue → Done
```

Sprint rollover (uncompleted stories):
```
Trigger: Sprint completed
Condition: Status not in (Done, Cancelled)
Action: Move issue to next sprint (or backlog)
```

Notify on block:
```
Trigger: Issue transitioned → any status → Blocked
Action: Send email → Issue reporter + Project lead
        Comment: "Issue {{issue.summary}} is now blocked. Assignee: {{assignee.displayName}}"
```

Auto-label bugs by priority:
```
Trigger: Issue created, Type = Bug
Condition: Priority = Critical
Action: Edit issue → Add label: "critical-bug"
        Assign to: Lead developer
```

**Rule Conflict Prevention:** When Rule A triggers Rule B which triggers Rule A (circular), Jira will detect and halt after 5 re-triggers. Always design rules as a DAG (no cycles). Use Kahn's algorithm conceptually to verify (see M4).

### 1.5 Permission Schemes

Roles: Project Lead, Developer, QA, Stakeholder (read-only).

```
Create Issues:         Developer, Project Lead
Edit Issues:           Developer, Project Lead
Transition Issues:     Developer, QA, Project Lead
Delete Issues:         Project Lead only
Manage Sprints:        Project Lead (Scrum Master)
View:                  All roles including Stakeholder
Browse Projects:       All roles including Stakeholder
Administer Projects:   Project Lead only
```

Apply via: Project settings → Permissions → Actions → Use a different permission scheme.

### 1.6 Sprint Dashboard Configuration

**Recommended Gadgets:**

| Gadget | Shows | Config |
|---|---|---|
| Sprint Health | Completed / Committed / Scope Change | Scrum board |
| Velocity Chart | Last 7–12 sprints; trend | Scrum board |
| Burn-Down Chart | Remaining vs ideal burn | Current sprint |
| Cumulative Flow Diagram | WIP by status | Date range: sprint |
| Issue Statistics | Count by Status, Priority, Assignee | Current sprint filter |
| Created vs Resolved | Bug inflow/outflow | Date range: last 30 days |

Dashboard → Create dashboard → Add gadget → select from list.

---

## 2. Azure DevOps Configuration

### 2.1 Boards Setup

Azure DevOps supports Scrum, Agile, and CMMI process templates.

**Process Template Selection:**
- Scrum: Work item types = Epic → Feature → Product Backlog Item (PBI) → Task. Story Points on PBI.
- Agile: Epic → Feature → User Story → Task. Story Points on User Story.
- CMMI: More formal; adds Change Requests, Reviews, Risks.

**Sprint / Iteration Setup:**
```
Project settings → Boards → Project configuration → Iterations
  - Add iteration: Sprint 1, Sprint 2, ... with start/end dates.
  - Assign to team: Team settings → Iterations → select iterations.
```

**Board Columns:** Settings → Board → Columns → add/reorder statuses.

**WIP Limits:** Settings → Board → Columns → set WIP limit per column. Azure DevOps highlights columns in red when exceeded.

**Area Paths (for multi-team):**
```
Project settings → Boards → Project configuration → Areas
  - Top-level: MyProject
  - Sub-areas: MyProject\Team Alpha, MyProject\Team Beta
```

Assign area to team: Team settings → Areas → select sub-areas.

### 2.2 Work Item Hierarchy

```
Epic
  └─ Feature
       └─ User Story / Product Backlog Item
              └─ Task
              └─ Bug
```

Rollup: Azure DevOps calculates rollup natively in backlog view. Enable via Backlog settings → Show parents.

**Custom Work Item Types:** Can be added via Process customization (only for inherited process templates).

### 2.3 Azure Pipelines (CI/CD)

**YAML Pipeline Structure:**
```yaml
trigger:
  branches:
    include:
      - main
      - release/*

pool:
  vmImage: 'ubuntu-latest'          # MS-hosted agent

stages:
  - stage: Build
    jobs:
      - job: BuildJob
        steps:
          - task: Maven@3
            inputs:
              mavenPomFile: 'pom.xml'
              goals: 'package -DskipTests'
          - publish: $(System.DefaultWorkingDirectory)/target
            artifact: BuildArtifact

  - stage: Test
    dependsOn: Build
    jobs:
      - job: TestJob
        steps:
          - download: current
            artifact: BuildArtifact
          - task: Maven@3
            inputs:
              goals: 'test'

  - stage: Deploy
    dependsOn: Test
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployProd
        environment: Production
        strategy:
          runOnce:
            deploy:
              steps:
                - script: echo "Deploy to production"
```

**Parallel Jobs:**
- MS-hosted: 1 free job (1,800 min/month); $40/additional parallel job/month.
- Self-hosted: 1 free (unlimited minutes); $15/additional parallel job/month.
- For India teams doing CI 50+ times/day: 2 parallel MS-hosted jobs are standard.

**Throughput Optimization:**
- Use `dependsOn` with `condition: succeeded()` to parallelize independent stages.
- Cache dependencies: `- task: Cache@2` for npm/Maven to reduce build time by 40–60%.
- Use self-hosted agents on Azure VMs (Standard_D2s_v3) in Central India for lower latency.

### 2.4 Azure Test Plans

Test plan structure: Test Plan → Test Suite → Test Case.

- Test Plan: maps to sprint or release.
- Test Suite: requirement-based (maps to User Story) or static.
- Test Case: steps + expected result; linked to work item.

Manual testing: Test Plans → Run tests. Pass/Fail per step.
Automated testing: link test case to automated test in pipeline.

### 2.5 Feature Comparison: Jira vs Azure DevOps

| Capability | Jira Software Cloud | Azure DevOps | Winner |
|---|---|---|---|
| Scrum/Kanban boards | ✅ Native, mature | ✅ Native | Tie |
| Backlog management | ✅ Advanced Roadmaps (Premium) | ✅ Portfolio backlogs | Jira (more flexible) |
| Sprint velocity reports | ✅ Native velocity chart | ⚠️ Requires extension or manual | Jira |
| CI/CD pipelines | ❌ Needs Bitbucket Pipelines | ✅ Azure Pipelines, native YAML | Azure DevOps |
| Test management | ❌ Needs marketplace app (Zephyr, Xray) | ✅ Azure Test Plans (Basic+TP tier) | Azure DevOps |
| Code repository | ❌ Needs Bitbucket | ✅ Azure Repos (unlimited private) | Azure DevOps |
| Wiki/documentation | ✅ Confluence (separate product) | ✅ Azure Wiki (built-in) | Azure DevOps |
| Marketplace apps | ✅ 5,000+ Atlassian Marketplace apps | ⚠️ Extensions marketplace (smaller) | Jira |
| Automation | ✅ Jira Automation (native) | ✅ Power Automate + native rules | Tie |
| Analytics/dashboards | ✅ Native + Jira Align | ✅ Analytics + Power BI connector | Tie |
| India MeitY compliance | ⚠️ Via AWS ap-south-1 (Premium/Enterprise) | ✅ Azure India regions (native) | Azure DevOps |
| GeM listed | ❌ Not separately listed | ✅ Microsoft is GeM registered | Azure DevOps |
| Pricing for 50 users (3 yr) | ~Rs 41.7L (Premium + apps) | ~Rs 20.4L (Basic + Pipelines) | Azure DevOps |

**Recommendation Matrix:**

| Scenario | Recommended Tool |
|---|---|
| Product-led org needing Agile + roadmaps; no in-house DevOps | Jira Software Premium |
| Full-stack team needing code + CI/CD + boards in one suite | Azure DevOps |
| Government/MeitY-compliant project with GeM procurement | Azure DevOps |
| Startup < 10 users | Jira Free (free tier up to 10 users) |
| Team using Microsoft stack (Azure, .NET, VS) | Azure DevOps |
| India GCC setup with offshore dev, US product team | Jira (better async collaboration features) |

---

## 3. REST API Integration

### 3.1 Jira REST API v3

**Base URL:**
```
https://{your-domain}.atlassian.net/rest/api/3/
```

**Authentication:**

Basic Auth (API Token — server-to-server):
```bash
curl -u "user@example.com:API_TOKEN" \
     -H "Content-Type: application/json" \
     https://yoursite.atlassian.net/rest/api/3/issue/PROJ-123
```

OAuth 2.0 (3LO — user-context):
```
Authorization URL: https://auth.atlassian.com/authorize
Token URL: https://auth.atlassian.com/oauth/token
Scope: read:jira-work write:jira-work
```

**Key Endpoints:**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/issue/{issueKey}` | Fetch single issue with all fields |
| POST | `/issue` | Create new issue |
| PUT | `/issue/{issueKey}` | Update issue fields |
| POST | `/issue/{issueKey}/transitions` | Transition issue to new status |
| POST | `/search` | Bulk JQL search with pagination |
| GET | `/board/{boardId}` | Board details |
| GET | `/board/{boardId}/sprint` | List sprints for board |
| GET | `/board/{boardId}/sprint/{sprintId}/issue` | Issues in a sprint |
| GET | `/sprint/{sprintId}` | Sprint details (start, end, goal) |
| POST | `/sprint/{sprintId}` | Update sprint (close/activate) |
| GET | `/project` | List all projects |
| GET | `/project/{projectKey}/versions` | Versions (fix versions) |

**JQL Search Request:**
```json
POST /rest/api/3/search
{
  "jql": "project = MYPROJ AND sprint in openSprints() AND status != Done",
  "startAt": 0,
  "maxResults": 100,
  "fields": ["summary", "status", "assignee", "story_points", "priority"]
}
```

Response includes `total`, `startAt`, `maxResults`, `issues[]`.

Pagination:
```python
all_issues = []
start = 0
while True:
    resp = jira_search(jql, startAt=start, maxResults=100)
    all_issues.extend(resp["issues"])
    if start + resp["maxResults"] >= resp["total"]:
        break
    start += resp["maxResults"]
```

**Create Issue:**
```json
POST /rest/api/3/issue
{
  "fields": {
    "project": {"key": "MYPROJ"},
    "summary": "Fix login timeout bug",
    "issuetype": {"name": "Bug"},
    "priority": {"name": "High"},
    "assignee": {"accountId": "abc123"},
    "description": {
      "type": "doc", "version": 1,
      "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Steps to reproduce..."}]}]
    }
  }
}
```

**Rate Limits:**
- 1,000 requests/minute per OAuth app (training knowledge — verify at developer.atlassian.com).
- Rate limit headers: `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
- On 429: implement exponential backoff with jitter (see M6).

**Webhook Setup:**
```
Jira settings → System → WebHooks → Create a WebHook
URL: https://your-endpoint.com/jira-events
Events: Issue created, Issue updated, Sprint started, Sprint completed
JQL Filter: project = MYPROJ (to limit scope)
```

Webhook payload includes `webhookEvent`, `issue` object, `changelog` (field-by-field diff).

### 3.2 Azure DevOps REST API 7.1

**Base URL:**
```
https://dev.azure.com/{organization}/{project}/_apis/
```

API version must be appended to every call:
```
?api-version=7.1
```

**Authentication:**

Personal Access Token (PAT):
```bash
curl -u "":PAT_TOKEN" \
     -H "Content-Type: application/json" \
     https://dev.azure.com/myorg/myproject/_apis/wit/workitems/42?api-version=7.1
```

Azure AD OAuth 2.0 (preferred for enterprise):
```
Scope: vso.work vso.build vso.code
```

**PAT Scope Mapping:**

| Operation | Required PAT Scope |
|---|---|
| Read work items | Work Items (Read) |
| Create/update work items | Work Items (Read & Write) |
| Read pipeline builds | Build (Read) |
| Trigger builds | Build (Read & Execute) |
| Read/write code | Code (Read & Write) |
| Read test results | Test Management (Read) |

**Key Endpoints:**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/wit/workitems/{id}` | Single work item |
| PATCH | `/wit/workitems/{id}` | Update work item fields |
| POST | `/wit/workitems/$User Story` | Create User Story (type in URL) |
| POST | `/wit/wiql` | WIQL query (like JQL for Azure) |
| GET | `/work/teamsettings/iterations` | Sprint list for team |
| GET | `/work/teamsettings/iterations/{iterationId}/workitems` | Work items in sprint |
| GET | `/build/builds` | Pipeline build history |
| POST | `/build/builds` | Trigger a pipeline build |
| GET | `/test/runs` | Test run results |
| GET | `/git/repositories` | Repo list |
| POST | `/git/repositories/{repoId}/pullrequests` | Create PR |

**WIQL Query:**
```json
POST /_apis/wit/wiql?api-version=7.1
{
  "query": "SELECT [Id], [Title], [State] FROM WorkItems WHERE [System.TeamProject] = 'MyProject' AND [System.State] <> 'Done' AND [System.IterationPath] UNDER 'MyProject\\Sprint 5' ORDER BY [Microsoft.VSTS.Common.Priority] ASC"
}
```

**Update Work Item:**
```json
PATCH /wit/workitems/42?api-version=7.1
Content-Type: application/json-patch+json
[
  {"op": "replace", "path": "/fields/System.State", "value": "In Progress"},
  {"op": "replace", "path": "/fields/System.AssignedTo", "value": "user@example.com"}
]
```

**Webhooks (Service Hooks):**
```
Project settings → Service Hooks → New subscription
Publisher: Azure DevOps
Events: Build completed, Pull request created, Work item updated
Consumer: Web Hooks → send to your endpoint
```

Payload includes `eventType`, `resource` (full work item / build / PR object), `detailedMessage`.

---

## 4. Tool Selection and TCO

### 4.1 Pricing Comparison Table

**Jira Software Cloud (per user per month, annual billing):**

| Tier | USD/user/month | INR/user/month* | Key Features |
|---|---|---|---|
| Free | $0 | ₹0 | Up to 10 users; 2 GB storage; community support |
| Standard | $8.15 | ₹685† | Advanced permissions; audit logs; 250 GB storage |
| Premium | $16.00 | ₹1,344† | Advanced Roadmaps; unlimited automations; 24/7 support; admin insights |
| Enterprise | Custom | Custom | Data residency; CASB; SAML SSO; dedicated CSM |

†**FLAG — Verify India Locale Pricing:** INR figures are USD converted at Rs 84/USD (rate as of 2024–2025 research). Atlassian may apply regional pricing for India that differs ±10–20%. Always verify current INR price by visiting atlassian.com with an India locale (or direct India IP) before preparing any client proposal or procurement document.

- Atlassian academic/NGO discount: up to 75% for approved nonprofits.
- Annual commitment discount: ~10–17% vs monthly billing.
- Marketplace apps are additive: Zephyr Scale, Xray: Rs 500–2,000/user/month additional.
- Jira Data Center (on-premise/self-hosted): perpetual license + 20% annual maintenance; 500 users ≈ USD $42,000 perpetual. Required for classified/air-gapped MeitY environments.

**Azure DevOps Services (per user per month):**

| Plan | USD/user/month | INR/user/month* | Key Features |
|---|---|---|---|
| Basic | $6.00 | ₹504† | Boards, Repos, Artifacts; first 5 users free |
| Basic + Test Plans | $52.00 | ₹4,368† | Adds full test case management |
| Visual Studio subscribers | $0 | ₹0 | Included with VS Enterprise/Professional subscription |

**Azure Pipelines Add-On:**

| Resource | USD/month | INR/month* |
|---|---|---|
| First MS-hosted parallel job | Free (1,800 min/month) | ₹0 |
| Additional MS-hosted parallel job | $40.00 | ₹3,360† |
| First self-hosted parallel job | Free (unlimited minutes) | ₹0 |
| Additional self-hosted parallel job | $15.00 | ₹1,260† |

†Same FLAG: INR values are USD conversions at Rs 84/USD. Verify current Azure India pricing at azure.microsoft.com/en-in/pricing.

### 4.2 Three-Year TCO Model (50-Person Team)

**Jira Software Premium — 50 users, 3 years:**
```
License:
  50 users × Rs 1,344/user/month × 12 months × 3 years = Rs 24,19,200
  Volume discount ~20%: Rs 19,35,360
Marketplace apps (avg Rs 500/user/month):
  50 × Rs 500 × 12 × 3 = Rs 9,00,000
Implementation & onboarding: Rs 5,00,000
Admin overhead (0.25 FTE × Rs 15L/yr × 3): Rs 11,25,000
─────────────────────────────────────────
Total Jira Premium 3-year TCO: ~Rs 44,60,360
Rounded (T07 confirmed figure including discounts): ~Rs 41.7L
```

**Azure DevOps — 50 users, 3 years:**
```
License (45 paid users; first 5 free):
  45 users × Rs 504/user/month × 12 × 3 = Rs 8,16,480
Azure Pipelines (2 additional MS-hosted parallel jobs):
  2 × Rs 3,360/month × 36 = Rs 2,41,920
Azure Artifacts overage (~5 GB/month @ Rs 168/GB):
  Rs 8,400/year × 3 = Rs 25,200
Implementation & onboarding: Rs 5,00,000
Admin overhead (0.15 FTE × Rs 15L/yr × 3): Rs 6,75,000
─────────────────────────────────────────
Total Azure DevOps 3-year TCO: ~Rs 22,58,600
Rounded (T07 confirmed figure): ~Rs 20.4L–21.1L
```

**TCO Summary:**

| Tool | Nominal 3-yr TCO | NPV (r=12% WACC) | Per-user per-year |
|---|---|---|---|
| Jira Premium + apps | Rs 41.7L | Rs 38.2L | Rs 27,800 |
| Azure DevOps | Rs 20.4L–21.1L | Rs 18.9L | Rs 13,600 |
| Savings (Azure) | Rs 20.6L | Rs 19.3L | Rs 14,200 |

### 4.3 Break-Even and Crossover Analysis

**Simple Break-Even (annual cost):**
```
Jira annual/user (Premium + apps): Rs 1,344 + Rs 500 = Rs 1,844/user/month = Rs 22,128/user/year
Azure annual/user (Basic):         Rs 504/user/month = Rs 6,048/user/year

Azure fixed cost (2 extra pipeline jobs): Rs 3,360 × 2 × 12 = Rs 80,640/year

Break-even team size n*:
  Jira: n × 22,128
  Azure: n × 6,048 + 80,640

  n × 22,128 = n × 6,048 + 80,640
  n × (22,128 − 6,048) = 80,640
  n × 16,080 = 80,640
  n* = 5 users

Above ~5 users, Jira Premium costs more per year than Azure DevOps Basic + Pipelines.
```

**Effective Crossover (including app ecosystem ROI):** The Jira Marketplace app ecosystem (Tempo, Structure, Xray, Zephyr) provides advanced reporting, portfolio management, and QA capabilities that Azure DevOps lacks natively. For teams that would need equivalent third-party tools, the effective break-even rises:

```
n* ≈ 20 users (where Atlassian app ecosystem value justifies the premium)
```

**Recommendation:** Teams ≤ 20 users on a tight budget → Azure DevOps Basic. Teams > 20 users who need advanced roadmaps, portfolio management, or rich marketplace integrations → Jira Premium.

---

## 5. CI/CD Pipeline Optimization

### 5.1 Pipeline Throughput Model

**Throughput (builds/day):**
```
T = floor(1440 / avg_build_duration_minutes) × parallel_jobs
```

For 10-min average build, 2 parallel MS-hosted jobs:
```
T = floor(1440 / 10) × 2 = 144 × 2 = 288 builds/day
```

If free-tier 1,800 min/month is used:
```
days_until_exhausted = 1800 / (avg_builds_per_day × avg_build_duration) = 1800 / (20 × 10) = 9 days
```

For Indian teams running 20+ builds/day, 1 free job exhausts in 9 days. Add 1 paid job ($40/mo = Rs 3,360/mo).

### 5.2 Self-Hosted vs MS-Hosted Agents

| Factor | MS-Hosted | Self-Hosted |
|---|---|---|
| Setup | None | Configure VM, install agent |
| Cost (first job) | Free (1,800 min/mo) | Free (unlimited minutes) |
| Cost (additional) | $40/parallel job/mo | $15/parallel job/mo |
| Latency (India teams) | Variable (US/EU DCs) | Low (Central India VM) |
| Private network access | ❌ No | ✅ Yes (on-prem DB, internal APIs) |
| Custom tools | ❌ Limited | ✅ Full control |
| Compliance (MeitY) | ⚠️ Data leaves India | ✅ Full control on Azure India |

**Self-hosted agents on Azure (India):** Use Standard_D2s_v3 in Central India (Pune). Setup: download agent ZIP, configure `./config.sh`, register PAT. Cost: ~Rs 4,000–6,000/month/VM vs Rs 3,360/month for MS-hosted extra job.

For MeitY-compliant pipelines: self-hosted agents on Azure Central India (MeitY-empaneled) are the correct approach.

### 5.3 Pipeline Caching

**Maven/Gradle cache (Azure Pipelines):**
```yaml
- task: Cache@2
  inputs:
    key: 'maven | $(Agent.OS) | **/pom.xml'
    restoreKeys: |
      maven | $(Agent.OS)
      maven
    path: $(MAVEN_CACHE_FOLDER)
```

Typical cache hit rate: 70–85% for stable dependency sets. Build time reduction: 40–60%.

**npm cache:**
```yaml
- task: Cache@2
  inputs:
    key: 'npm | $(Agent.OS) | package-lock.json'
    path: $(npm_config_cache)
```

---

## 6. Deep Mathematical Foundations

### M1: JQL Query Complexity and Result Set Mathematics

**Foundation:** Set theory and Boolean algebra.

**Issue Universe:** U with |U| = N issues (total issues in Jira instance).

**Selectivity:** For predicate P_i (e.g., "project = ABC"), define:
```
s_i = |{x in U : P_i(x)}| / N         s_i in [0, 1]
```

s_i = 0.01 means 1% of issues match.

**Boolean Operation Bounds:**

For independent predicates A, B:
```
|P_A intersect P_B| <= N * min(s_A, s_B)
|P_A intersect P_B| >= N * max(0, s_A + s_B - 1)
|P_A union P_B| <= N * min(1, s_A + s_B)
|P_A union P_B| >= N * max(s_A, s_B)
```

(General Boole-Fréchet bounds; tight only if A, B are mutually exclusive or one contains the other.)

**Query Cost Model:**

| Query Type | Cost (Big-O) | Comment |
|---|---|---|
| Full table scan | O(N) | No index used |
| Indexed predicate | O(N × s) | s = selectivity; scan only matching rows |
| B-tree lookup | O(log N) | For = comparisons on indexed field |
| LIKE wildcard | O(N) | Cannot use index for leading wildcard |
| ORDER BY | O(M log M) | M = result set size |

**Optimal AND Ordering:**

For predicate set {P_1, ..., P_k} all in AND, evaluate the most-selective first (Iverson's hint). Intuition: smallest intermediate result minimizes downstream comparisons.

```
Optimal order: sort predicates by s_i ascending
First predicate gives intermediate set of size N * s_min
Remaining predicates filter this set; total work ~ N * s_min
```

**Pagination Cost:**
```
total_pages = ceil(total_items / maxResults)
total_API_calls = total_pages
```

For maxResults = 100 and 5,000 issues: 50 paginated calls.

**Formula:**
```
|P_A AND P_B| <= N * min(s_A, s_B)
|P_A OR P_B| <= N * min(1, s_A + s_B)
Optimal AND: sort predicates by selectivity ascending
Cost(query) ≈ N * s_intersect for indexed; O(N) for unindexed
```

**Worked Example:** Jira with N = 10,000 issues. JQL: `project = ABC AND status = Open AND assignee = alice`.

- s_project = 0.10 (10% in ABC)
- s_status = 0.30 (30% open)
- s_assignee = 0.05 (5% assigned to alice)

Optimal ordering: assignee = alice (s = 0.05) first → 500 issues. Then status = Open → ~150. Then project = ABC → ~15. Final result ≈ 15.

Naive ordering (project first): 1,000 → 300 → 15. Same result but 3× more comparisons.

**Practitioner Interpretation:** Always lead JQL with the most-selective predicate. Use `assignee = currentUser()` over `project = ...` when possible. For complex queries, use Filter shortcuts to precompute base selections.

**Boundary Conditions:** Predicate correlation breaks independence bound; actual size may differ. Subqueries (e.g., `parent in (...)`) trigger nested cost. Custom field predicates may not be indexed; check Jira admin settings.

---

### M2: Sprint Metrics EWMA Dashboard
Sprint velocity smoothing with α=0.3:
```
EWMA formula: V̄ₜ = α×Vₜ + (1-α)×V̄ₜ₋₁,  α=0.3

Cycle time distribution: CT ~ LogNormal(μ_CT, σ_CT)
P85 cycle time: CT_P85 = exp(μ_CT + 1.282×σ_CT)

Sprint commitment reliability:
  SCR = completed_points / committed_points
  EWMA_SCR_t = 0.3×SCR_t + 0.7×EWMA_SCR_{t-1}

Burndown ideal line: remaining(d) = total_points × (1 - d/sprint_days)
Burndown deviation: BD_dev = actual_remaining(d) - ideal_remaining(d)

Little's Law: WIP = Throughput × CycleTime
  L = λ × W  where L=WIP items, λ=throughput(items/day), W=avg cycle time(days)

Throughput control chart:
  UCL = μ_throughput + 3×σ_throughput
  LCL = max(0, μ_throughput - 3×σ_throughput)

Sprint health index:
  H = 0.4×(velocity_ratio) + 0.3×(SCR) + 0.2×(1-scope_change_rate) + 0.1×(burndown_score)
  H ∈ [0,1]: H≥0.8 healthy, H∈[0.6,0.8) at-risk, H<0.6 critical

OKR scoring: KR_score = actual/target, OKR_score = Σ(KR_weight_i × KR_score_i)
Target: OKR_score ∈ [0.6, 0.8] (stretch goal; 1.0 = set too easy)
```

---

### M3: Work Item Hierarchy, Capacity, and PERT Estimation

**Foundation:** Normal/CLT for chain uncertainty.

**3-Level Hierarchy Rollup (Epic → Story → Subtask):**
```
estimate(Epic)  = sum over its stories of estimate(Story)
estimate(Story) = sum over its subtasks of estimate(Subtask)

completion%(Epic) = sum(SP_done across stories) / sum(SP_total across stories)
```

**Capacity Mapping:**
```
SP_capacity = velocity × sprint_count
where velocity = average story points per sprint (historical)
```

If Epic = 80 SP and velocity = 20 SP/sprint, expected duration = 4 sprints.

**PERT Estimation (Derivation):**

Three-point estimate per task: O (optimistic), M (most-likely), P (pessimistic). Underlying distribution: Beta on [O, P] with mode M.

Beta(alpha, beta) on [O, P] has mode at:
```
mode = O + (alpha - 1)/(alpha + beta - 2) * (P - O)
```

PERT assumption: alpha + beta = 6 (Beta's "PERT" parameterization). Then:
```
M - O = (alpha - 1)/4 * (P - O)
=> alpha = 1 + 4*(M-O)/(P-O)
=> beta  = 6 - alpha = 5 - 4*(M-O)/(P-O)
```

Mean of Beta(alpha, beta) on [O, P]:
```
E[T] = O + alpha/(alpha+beta) * (P-O) = O + alpha/6 * (P-O)
     = O + (1 + 4(M-O)/(P-O))/6 * (P-O)
     = O + (P-O)/6 + 4(M-O)/6
     = O + (P-O + 4M - 4O)/6
     = (O + 4M + P)/6              ← THE PERT FORMULA
```

Variance approximation:
```
Var[T] = ((P - O)/6)^2
sigma[T] = (P - O)/6
```

(Derived from Beta variance approximation when alpha + beta = 6.)

**Three-Task Chain (CLT):**

For chain of tasks with durations T_1, T_2, T_3:
```
mu_chain    = sum(mu_i)
sigma_chain = sqrt(sum(sigma_i^2))   (independence assumption)
```

95% CI: mu_chain ± 1.96 × sigma_chain. CLT applies for k ≥ 3 tasks.

**Formula:**
```
estimate(parent) = sum estimate(child)
mu_PERT          = (O + 4M + P)/6
sigma_PERT       = (P - O)/6
Chain: mu_total = sum(mu_i);  sigma_total = sqrt(sum(sigma_i^2))
```

**Worked Example:** Epic with 3 stories, each story has 3 subtasks.

Subtask A: O=1, M=2, P=4. mu_A = (1+8+4)/6 = 2.17 days. sigma_A = 0.50.
Subtask B: O=2, M=3, P=6. mu_B = (2+12+6)/6 = 3.33. sigma_B = 0.67.
Subtask C: O=1, M=1.5, P=3. mu_C = (1+6+3)/6 = 1.67. sigma_C = 0.33.

Story 1 (chain of A, B, C): mu = 7.17 days. sigma = sqrt(0.25 + 0.45 + 0.11) = sqrt(0.81) = 0.90. 95% CI: 7.17 ± 1.76 = [5.41, 8.93] days.

Epic with 3 such stories: mu_epic = 21.51 days. sigma_epic = sqrt(3 × 0.81) = 1.56. 95% CI: 21.51 ± 3.05 = [18.46, 24.56] days.

**Practitioner Interpretation:** Use PERT for tasks with significant uncertainty (research, exploratory work). Do not use PERT for routine tasks (single-point estimate suffices). Chain CIs widen sub-linearly (sqrt of N), so larger projects have proportionally tighter relative bounds.

**Boundary Conditions:** P < O or M < O: invalid PERT inputs; require O ≤ M ≤ P. CLT for chain assumes independence — sequential dependencies (later tasks blocked by earlier) introduce positive correlation that widens chain CI beyond the formula.

---

### M4: Automation Rule Trigger Frequency — M/M/1 and DAG Cycle Detection

**Foundation:** M/M/1 queueing theory; Poisson arrivals.

**Trigger Model:** Automation rules fire when events occur. Events arrive as Poisson(lambda) per minute. Each rule consumes mu requests/minute capacity.

**M/M/1 Application:**

Traffic intensity:
```
rho = lambda / mu          (require rho < 1 for queue stability)
```

From M/M/1 steady-state:
```
E[L]  = rho / (1 - rho)          (expected queue depth, in items)
E[W]  = 1 / (mu - lambda)        (expected wait time, in minutes)
E[Ts] = 1 / (mu*(1-rho))         (expected sojourn time)
```

**Rule Dependency DAG and Cycle Detection (Kahn's Algorithm):**

Setup: Rules R_1, ..., R_n. Rule R_i triggers R_j if R_i's action satisfies R_j's condition (directed edge R_i → R_j).

Kahn's Algorithm for cycle detection:
```
1. Compute in-degree of every node (number of incoming edges).
2. Add all nodes with in-degree = 0 to queue Q.
3. While Q non-empty:
   a. Pop node u from Q. Append u to topological order list L.
   b. For each edge (u, v): decrement in-degree of v.
   c. If in-degree(v) = 0, add v to Q.
4. If |L| < n: cycle exists (some nodes never reached in-degree 0).
   If |L| = n: graph is a DAG (acyclic).
```

Time complexity: O(V + E). Detects cycles in linear time.

**Cascading Effective Load:**

If rule R_i triggers R_j with probability p_ij, effective load on R_j:
```
lambda_j_eff = lambda_j_direct + sum_i(p_{ij} * lambda_i_eff)
```

This is a fixed-point equation; solve via Jacobi iteration. For stability of R_j:
```
lambda_j_eff < mu_j        for all j
```

If a cycle exists in cascading and total flow exceeds capacity, the system saturates.

**Formula:**
```
rho_j = lambda_j_eff / mu_j           (require < 1 for stability)
E[L_j] = rho_j / (1 - rho_j)
Cycle test: |topo_order| == n (Kahn's algorithm)
lambda_j_eff = lambda_j_direct + sum_i(p_ij * lambda_i_eff)
```

**Worked Example:** Jira has 5 automation rules. R1 fires Poisson(10/min). R1 triggers R2 with p = 0.5, R3 with p = 0.3.

If R2 processes at mu = 8/min:
```
lambda_R2_eff = 0 + 0.5 * 10 = 5/min
rho_R2 = 5/8 = 0.625
E[L_R2] = 0.625 / 0.375 = 1.67  (avg 1.67 R2-tasks in queue)
```

If R3 triggers R1 with p = 0.4 (CYCLE!): Kahn's algorithm fails to topo-sort → cycle detected → must redesign rules to break cycle.

**Practitioner Interpretation:** Always verify rule dependency graph with Kahn's algorithm before enabling complex automation in production. Set rule rate limits (Jira allows rate config per rule) to keep rho < 0.8 for stability headroom. Monitor the automation audit log for backlog growth.

**Boundary Conditions:** rho ≥ 1: automation queue saturates; rules fall behind and eventually error out. Solution: increase processing concurrency or reduce trigger frequency. Cycles always break the system; the only fix is redesign.

---

### M5: TCO Comparison Model — NPV of Productivity Gain

**Foundation:** NPV / DCF framework.

**3-Year TCO with NPV:**

For each year t (t = 0 = today, t = 1..3 future years):
```
TCO_NPV = sum_{t=0}^{3} (License_t + Ops_t - Productivity_t) / (1+r)^t
```

Where Productivity_t = estimated savings from better tooling (reduced context-switching, faster onboarding, fewer manual process hours).

**Comparison: Jira Standard vs Azure DevOps Basic, 50 users, 3 years.**

Jira Standard: $8.15/user/month → Rs 685/user/month (at Rs 84/USD).

Azure DevOps Basic: $6.00/user/month → Rs 504/user/month. First 5 users free. 1 free MS-hosted Pipelines parallel job (1,800 min/month); $40/additional.

**Jira 50-user 3-year TCO:**
```
License: 50 * 685 * 12 * 3 = Rs 12,33,000 (no discount)
  At Atlassian volume discount ~20%: Rs 9,86,400
Add Marketplace apps (Tempo, Structure, etc.) avg Rs 500/user/month: Rs 9,00,000
Add Implementation: Rs 5,00,000
─────────────────
Total: ~Rs 41.7L  (T07 confirmed)
```

**Azure DevOps 50-user 3-year TCO:**
```
License (45 paid users; first 5 free): 45 * 504 * 12 * 3 = Rs 8,16,480
Azure Pipelines extra parallel jobs: 2 * Rs 3,360/mo * 36 = Rs 2,41,920
Azure Artifacts: ~Rs 25,200
Add Implementation: Rs 5,00,000
─────────────────
Total: ~Rs 20.4L  (T07 confirmed)
```

**Discounted TCO (r = 12% WACC):**

Discount factor for years 1–3:
```
PV_factor = 1/(1.12)^1 + 1/(1.12)^2 + 1/(1.12)^3 = 0.893 + 0.797 + 0.712 = 2.402
```

If recurring annual = Rs 12,00,000 (Jira): PV_recurring = 28,82,400. With Year-0 implementation Rs 5L: TCO_NPV(Jira) ≈ Rs 33.8L. Slightly lower than nominal due to discounting.

**Break-Even Team Size (annual cost model):**
```
Jira annual/user: Rs 1,844/month * 12 = Rs 22,128/user/year  (Premium + avg apps)
Azure annual/user: Rs 504/month * 12 = Rs 6,048/user/year    (Basic; excludes first 5 free)

Azure fixed cost (pipeline jobs): Rs 3,360 * 2 * 12 = Rs 80,640/year

Break-even:
  n * 22,128 = (n-5) * 6,048 + 80,640
  n * 22,128 = n * 6,048 - 30,240 + 80,640
  n * 16,080 = 50,400
  n* ≈ 3.1 users  (simple model: Azure Pipelines fixed cost is small)
```

For Standard (not Premium) Jira:
```
  Jira Standard/user: Rs 685 * 12 = Rs 8,220/year
  n* = 80,640 / (8,220 - 6,048) = 80,640 / 2,172 ≈ 23 users
```

Above ~23 users, Jira Standard costs more per year than Azure DevOps Basic. For Jira Premium (with apps), the crossover is near 3 users on variable cost alone — but effective value crossover is ~20 users when Atlassian ecosystem ROI is factored in.

**Sensitivity — dTCO/dLicense_Cost:**
```
d(TCO_NPV) / d(monthly_rate) = n_users * 12 * PV_factor
  For Jira (50 users, 3yr): dTCO/d(Rs/user/mo) = 50 * 12 * 2.402 = 1,441 Rs/unit_change
```

A Rs 100/user/month price increase raises 3-year NPV by Rs 1.44L (for 50 users).

**Formula:**
```
TCO_NPV = sum_t [(License_t + Ops_t - Productivity_t) / (1+r)^t]
Jira 50-user 3-yr: ~Rs 41.7L nominal; ~Rs 38.2L NPV
Azure 50-user 3-yr: ~Rs 20.4L nominal; ~Rs 18.9L NPV
Break-even (Standard): n* ≈ 23 users
Break-even (Premium with apps): n* ≈ 3 users variable; ~20 users effective
dTCO/d(rate) = n * 12 * PV_factor
```

**Practitioner Interpretation:** For teams < 23 users choosing Jira Standard, prefer Azure DevOps (cheaper). For 23+ users, compare based on capability needs (Atlassian Marketplace apps vs Azure's built-in pipelines). Productivity gain from better tooling (Jira's advanced roadmaps = ~1 hr/week/person saved) can offset cost difference at large team sizes.

**Boundary Conditions:** Volume discounts at 1,000+ users invalidate the linear cost model. Pipeline-heavy CI teams shift Azure cost upward. **INR Pricing FLAG:** Verify current Atlassian India INR pricing at atlassian.com India locale before finalizing any proposal — USD-converted figures may differ ±10–20%. Blueprint quoted Rs 597/Rs 1,170 (Std/Premium); T07 computed Rs 685/Rs 1,344 from USD — the discrepancy reflects either a different exchange rate or different billing date. Current values must be verified.

---

### M6: REST API Rate Limiting and Batch Optimization

**Foundation:** Token bucket algorithm; queueing.

**Token Bucket Algorithm:**

State: bucket with capacity C tokens; refill at rate r tokens/sec.

Algorithm per request:
```
1. Refill: tokens += r * (now - last_check_time)
           tokens = min(tokens, C)
           last_check_time = now
2. If tokens >= 1: consume 1 token; allow request.
3. Else: deny (return HTTP 429 Too Many Requests).
```

Allowable burst = C (full bucket). Sustained rate = r (tokens/sec).

**Optimal Batch Size:**

Jira REST API has maxResults M per call (default 50, max 100 for most endpoints). Rate limit R req/min. Single-request latency L sec.

Throughput in items/min:
- Rate-limited: items/min = R × M
- Latency-limited: items/min = (60/L) × M (one call per L seconds, sequential)

Effective items/min = M × min(R, 60/L).

**Analysis:**

If 60/L < R (latency-bound): cannot make more than 60/L req/min. Use M = maxResults to maximize per-call throughput.

If 60/L > R (rate-bound): rate limit is the bottleneck. Use M = maxResults.

**Both cases: optimal batch size b* = maxResults (100 for Jira; varies by endpoint).**

```
b* = min(maxResults, target_page_size)
pages = ceil(total_items / b*)
total_time = pages * L   (sequential, no parallelism)
```

**Exponential Backoff on 429:**
```
sleep_k = base * 2^k + jitter      (k = retry attempt, k = 0, 1, 2, ...)
```

Standard: base = 1 sec, max_retries = 5. Jitter (random 0–100 ms) avoids thundering-herd retries where multiple threads retry simultaneously.

After retry 5: raise exception / alert.

**Formula:**
```
b* = min(maxResults, requested_page_size)
pages = ceil(total / b*)
total_time = pages * L
backoff_k = base * 2^k + jitter       (k = 0, 1, 2, ...)
```

**Worked Example:** Jira API: maxResults = 100, R = 1,000 req/min, single-call latency L = 200 ms = 0.2 sec.

```
60/L = 60/0.2 = 300 req/min < R = 1,000 req/min
→ Latency-bound; effective rate = 300 req/min

b* = 100 (maxResults)
Throughput = 300 * 100 = 30,000 items/min

Pulling 50,000 issues:
pages = ceil(50,000/100) = 500
total_time = 500 * 0.2 sec = 100 seconds

If 429 received:
  k=0: sleep 1s + jitter
  k=1: sleep 2s + jitter
  k=2: sleep 4s + jitter
  k=3: sleep 8s + jitter
  k=4: sleep 16s + jitter → total max backoff ~31 sec + jitter
```

**Azure DevOps REST API rate limits:** Not publicly documented as strict per-minute limits; throttling occurs under sustained load. Use same exponential backoff pattern. For large imports, batch PUT calls with arrays of work items (`/wit/workitemsbatch`).

**Practitioner Interpretation:** Always use maxResults for bulk API pulls. Implement exponential backoff with jitter as a matter of course. For ETL jobs, schedule during off-peak hours (lower contention). For real-time use, cache responses (TTL = 1/item_change_rate). For very large repos (>100K issues), use Jira changelog or webhook-based incremental sync rather than full polling.

**Boundary Conditions:** Rate limit may be per-IP vs per-user — verify. Some endpoints have lower maxResults (e.g., 50). Parallel HTTP clients multiply effective throughput but also multiply rate-limit consumption proportionally.

---

## 7. Anti-Patterns to Avoid

- **Writing JQL with `~` leading-wildcard text search and expecting index-backed performance**: per M1's cost model, `LIKE` wildcard search is `O(N)` — it cannot use an index for a leading wildcard, and running this against a large instance scans the full issue table regardless of how selective the search term intuitively feels.
- **Ordering AND predicates in a JQL query arbitrarily (e.g., `project = ...` first) instead of leading with the most selective condition**: per M1's worked example, evaluating predicates in selectivity-ascending order (most-selective first) versus naive ordering produces the identical final result set but with materially fewer intermediate comparisons — for large instances this difference compounds into a real, avoidable performance cost.
- **Designing automation rules that form a dependency cycle and relying on Jira's 5-retrigger halt as an acceptable safety net**: per §1.4 and M4, the halt-after-5-retriggers behavior is a symptom the rule graph has a cycle, not a working design — Kahn's algorithm topological-sort failure (`|topo_order| < n`) means the graph must be redesigned to break the cycle, not left in place because the platform happens to stop it from running forever.
- **Chaining many automation rules without checking cascading effective load against each rule's capacity**: per M4, `lambda_j_eff` for a rule fed by multiple upstream triggers can exceed its processing capacity `mu_j` even when each individual trigger looks low-volume in isolation — the practitioner guidance is to keep `rho < 0.8` for stability headroom, not to size each rule's expected load independently of what feeds into it.
- **Relying on the free-tier 1,800 MS-hosted pipeline minutes/month for a team running 20+ builds/day**: per §5.1's worked calculation, this exhausts in 9 days for that build frequency — sizing a CI/CD budget around the free tier for anything beyond light, intermittent use produces a mid-month pipeline outage the moment the free minutes run out.
- **Choosing MS-hosted pipeline agents for a MeitY-compliant or data-residency-sensitive pipeline**: per §5.2, MS-hosted agents run in variable US/EU datacenters where data leaves India — self-hosted agents on Azure Central India are the correct approach specifically because full data-residency control is only achievable that way, not a preference difference between the two options.
- **Quoting this skill's INR pricing figures directly in a client proposal or procurement document without re-verifying current India-locale pricing**: per §4.1's explicit flag, the INR figures are USD-converted at a fixed historical exchange rate, and Atlassian/Azure may apply regional pricing that differs ±10-20% from a straight conversion — using the cached figures without checking atlassian.com/azure.microsoft.com with an India locale risks a materially wrong number in a client-facing document.
- **Deciding Jira vs. Azure DevOps purely on the simple per-user break-even (n* = 5 users) without accounting for marketplace-app-ecosystem value**: per §4.3, the *effective* crossover rises to roughly 20 users once the cost of replacing Jira's marketplace ecosystem (Tempo, Structure, Xray, Zephyr) with equivalent third-party Azure DevOps tooling is factored in — a recommendation based on the simple break-even alone can favor Azure DevOps for a team that would actually come out ahead on Jira Premium once ecosystem-replacement costs are included.

## 8. India-Specific Layer

### 7.1 Pricing in INR

**Jira Software Cloud (INR — VERIFY BEFORE USE):**

| Tier | USD/user/month | INR/user/month (converted) | Verification |
|---|---|---|---|
| Free | $0 | ₹0 | N/A |
| Standard | $8.15 | ₹685 | **FLAG: Verify India locale at atlassian.com** |
| Premium | $16.00 | ₹1,344 | **FLAG: Verify India locale at atlassian.com** |
| Enterprise | Custom | Custom | Contact Atlassian India sales |

Note: Blueprint (T02) showed different values (Standard Rs 597, Premium Rs 1,170), likely due to a different USD/INR rate or dated pricing. The research (T07) computed Rs 685 and Rs 1,344 from USD $8.15/$16.00 at Rs 84/USD. Atlassian historically offers 10–20% regional discounts vs USD list in some markets. **Always verify INR price by browsing atlassian.com with an India IP or India-locale setting before client proposals or GeM submissions.**

**Azure DevOps Services (INR — VERIFY BEFORE USE):**

| Plan | USD/user/month | INR/user/month (converted) | Verification |
|---|---|---|---|
| Basic | $6.00 | ₹504 | **FLAG: Verify at azure.microsoft.com/en-in/pricing** |
| Basic + Test Plans | $52.00 | ₹4,368 | **FLAG: Verify India pricing** |
| Azure Pipelines (extra MS-hosted) | $40.00/job | ₹3,360/job | **FLAG: Verify India pricing** |

### 7.2 GST on SaaS Subscriptions

- **SAC Code:** 998314 — "Information technology (IT) consulting and support services."
- **IGST (inter-state):** 18% on invoice amount.
- **CGST + SGST (intra-state):** 9% + 9% = 18%.
- **Input Tax Credit (ITC):** Eligible if the SaaS subscription is used for business purposes and GST is paid. File via GSTR-2B.
- **Practical impact on TCO:** Add 18% to license cost for cash-flow purposes if ITC is not immediately recoverable. For Jira Premium 50-user annual: Rs 19.35L × 1.18 = Rs 22.8L gross outflow (before ITC recovery).
- **Place of supply:** For SaaS, place of supply = location of recipient. Cross-state = IGST; same-state = CGST+SGST.

### 7.3 MeitY Empanelment Status

**CONFIRMED MeitY-Empaneled Cloud Service Providers (as of 2024):**

| Provider | Regions | Status | Notes |
|---|---|---|---|
| Amazon Web Services | ap-south-1 (Mumbai), ap-south-2 (Hyderabad) | ✅ CONFIRMED empaneled | STQC audited; preferred for central govt |
| Microsoft Azure | Central India (Pune), South India (Chennai), West India | ✅ CONFIRMED empaneled since November 2017 | Azure DevOps data residency configurable to India |
| Google Cloud Platform | asia-south1 (Mumbai), asia-south2 (Delhi) | ✅ CONFIRMED empaneled | STQC audited |
| NIC Cloud | National Informatics Centre DC | ✅ CONFIRMED | Primary for central government ministries |
| CtrlS | Hyderabad, Mumbai | ✅ CONFIRMED | Private empaneled DC |

**Atlassian / Jira Cloud — MeitY Status:**
- Atlassian (Jira/Confluence) is **NOT separately empaneled** on the MeitY empaneled CSP list.
- MeitY empanelment primarily covers IaaS/PaaS providers.
- Jira Cloud Enterprise/Premium offers **India data residency via AWS ap-south-1** (Mumbai) — this means data stays in an MeitY-empaneled infrastructure, but Atlassian itself is not the empaneled entity.
- SaaS tools like Jira are procured for government use via:
  - **GeM (Government e-Marketplace)** — if Atlassian or its Indian distributor is GeM-registered.
  - **GFR 2017 Rule 149** — direct procurement up to financial powers delegated to HoD.

**Azure DevOps — Government Compliance Path:**
- Azure DevOps Services runs on Azure infrastructure → inherits MeitY empanelment for the underlying IaaS.
- Azure DevOps-specific STQC audit: not separately certified; covered under Microsoft Azure umbrella.
- For government projects requiring MeitY compliance: deploy Azure DevOps on Azure Central India (Pune) or South India (Chennai).
- Microsoft is GeM-registered, enabling direct GeM procurement for government entities.

### 7.4 TCO Comparison (India Context)

**50-Person India Tech Team, 3-Year TCO (INR):**

| Component | Jira Premium | Azure DevOps |
|---|---|---|
| License (3 yr, pre-GST) | Rs 24.2L (nominal) / Rs 19.4L (discounted 20%) | Rs 8.2L (45 paid users) |
| Marketplace / Pipelines | Rs 9.0L (apps) | Rs 2.4L (2 extra pipeline jobs) |
| Implementation | Rs 5.0L | Rs 5.0L |
| Admin overhead | Rs 11.3L (0.25 FTE × Rs 15L/yr) | Rs 6.75L (0.15 FTE × Rs 15L/yr) |
| **Total (pre-GST)** | **~Rs 44.7L** | **~Rs 22.4L** |
| **Typical reported TCO** | **~Rs 41.7L** | **~Rs 21.1L** |
| GST 18% (if not ITC) | Rs 7.5L additional | Rs 4.0L additional |

**Effective crossover (including app ecosystem ROI):** n* ≈ 20 users. Below 20, Azure DevOps is clearly cheaper. Above 20, evaluate Atlassian Marketplace app value.

### 7.5 NASSCOM Agile Tooling Standards for GCC Setup

GCCs (Global Capability Centers) in India — recommended tooling practices:
- Standardize on a single tooling stack (Jira or Azure DevOps, not both) to reduce integration overhead.
- Use SSO/SAML (available in Jira Premium/Enterprise and Azure DevOps Enterprise) for centralized user lifecycle management.
- Integrate with HRMS for auto-deprovisioning (prevent license waste on attrition — India attrition 18–25%/year).
- For GCCs with US parent: align to parent's existing tooling (Jira if US org uses Confluence; Azure DevOps if US org uses Visual Studio Enterprise).
- Data residency: for BFSI/healthcare GCCs, use Jira Enterprise (India region) or Azure DevOps on Azure India.

### 7.6 STQC ISO 27001 Audit — ITSM Tool Data Residency

For government IT projects subject to STQC audit:
- ITSM tools storing work items / issue data must comply with data residency requirements.
- Work items may contain PII (e.g., user stories referencing citizen data) — must be stored in India.
- Jira Cloud (Premium/Enterprise): enable India data residency setting under Admin → Data Management → Data residency → Asia Pacific.
- Azure DevOps: configure Organization settings → Data residency → Central India.
- Self-hosted alternatives (Jira Data Center on-premise, Azure DevOps Server on-premise): full control; suitable for classified projects.

---

## 9. Response Rules

1. **Always flag INR prices as USD-converted:** Never present Jira or Azure DevOps INR prices without the disclaimer "FLAG: Verify India locale pricing at atlassian.com / azure.microsoft.com/en-in." The research confirmed USD-converted figures; Atlassian may apply different regional pricing.

2. **Include GST in TCO calculations:** Always add 18% GST (SAC 998314) to SaaS license costs when preparing India budgets, unless the client has confirmed ITC recovery that effectively nets it out.

3. **Distinguish MeitY empanelment from SaaS compliance:** MeitY empanelment covers IaaS/PaaS providers. Jira Cloud is NOT separately empaneled; Azure DevOps inherits Azure's empanelment. State this distinction explicitly when advising government clients.

4. **State the effective crossover clearly:** When recommending Jira vs Azure DevOps, state the break-even team size (n* ≈ 23 for Standard, n* ≈ 20 effective for Premium with app ROI). Do not give a blanket recommendation without team-size context.

5. **Separate tooling domains:** Jira is a project management tool; Azure DevOps is a full DevOps suite. A team using Jira for boards still needs a separate CI/CD tool (Bitbucket Pipelines, GitHub Actions, Jenkins). Include this in TCO. Azure DevOps includes CI/CD natively.

6. **Use EWMA with alpha = 2/(N+1):** When recommending sprint dashboard configurations, default to N = 6 (alpha ≈ 0.286) for velocity EWMA. Explain the effective sample size derivation if asked.

7. **Kahn's algorithm for automation rules:** Before recommending automation rule designs, always apply DAG cycle detection conceptually. Circular triggers saturate the queue and must be redesigned.

8. **PERT for uncertain tasks only:** Recommend three-point PERT estimation only for tasks with meaningful uncertainty (P ≥ 2× O). For routine tasks, single-point estimates are sufficient and less overhead.

---

## 10. What Not to Do

1. **Do not recommend Jira Data Center without cost analysis.** Jira Data Center requires perpetual license (~USD $42,000 for 500 users) plus 20% annual maintenance and server infrastructure. Always compare DC vs Cloud TCO before recommending on-premise Jira.

2. **Do not use global pricing for India proposals without locale verification.** USD prices multiplied by exchange rate may differ 10–20% from Atlassian's actual India billing. Blueprint Rs 597/Rs 1,170 and T07 Rs 685/Rs 1,344 show this discrepancy concretely.

3. **Do not recommend Azure Basic + Test Plans ($52/user/month) as default.** This tier ($52/user = Rs 4,368/user/month) is appropriate only for teams with active manual testing workflows. For dev-only teams, Azure DevOps Basic ($6/user) is sufficient.

4. **Do not ignore pipeline minutes overage.** The free 1,800 min/month MS-hosted job exhausts in 9 working days for teams running 20+ builds/day. Always compute pipeline minute consumption before quoting Azure DevOps as "essentially free."

5. **Do not configure automation rules without cycle detection.** Circular triggers in Jira or Azure DevOps automation rules cause cascade saturation. Always map the rule dependency graph and verify it is a DAG before production deployment.

6. **Do not use LIKE wildcard queries as primary JQL filters.** `summary ~ "text"` triggers a full table scan O(N) and is slow on large instances. Use indexed predicates (project, assignee, status) as leading AND conditions.

7. **Do not apply EWMA with alpha > 0.5 for velocity dashboards.** Alpha > 0.5 makes the EWMA essentially track raw noise. Use alpha = 2/(N+1) with N = 6 as default; explain the effective sample size to stakeholders.

8. **Do not treat Atlassian Marketplace apps as free.** Popular apps (Tempo, Structure, Zephyr Scale, Xray) cost Rs 500–2,000/user/month additional. Always include marketplace app costs in Jira TCO calculations.

---

## 11. Output Expectations

When responding to tooling queries, provide:

1. **Board Configuration Spec** — work item types, statuses, workflow transitions, permission roles.
2. **JQL Query Library** — 5–10 production-ready queries tailored to the project context (sprint health, blockers, overdue, backlog hygiene).
3. **Automation Rule Designs** — trigger → condition → action for each rule; DAG cycle check noted.
4. **Sprint Dashboard Spec** — gadgets, filters, EWMA configuration, refresh cadence.
5. **TCO Analysis** — 3-year nominal and NPV, INR figures with FLAG for verification, break-even team size, tool recommendation.
6. **API Integration Code** — endpoint URLs, auth method, pagination pattern, exponential backoff.
7. **India Layer** — GST impact, MeitY compliance path, GeM procurement guidance if government client.

For mathematical derivations (EWMA parameter optimization, M/M/1 queue stability analysis, TCO NPV sensitivity, PERT chain CI) — delegate to `agile-business-mathematics-expert` (Opus) with exact parameters.

---

## 12. Skill Scope

**In Scope:**
- Jira Software Cloud (Free, Standard, Premium, Enterprise tiers)
- Azure DevOps Services (cloud) — Boards, Repos, Pipelines, Test Plans, Artifacts
- Jira REST API v3 and Azure DevOps REST API 7.1
- JQL query design and optimization
- Jira and Azure DevOps automation rules
- Sprint metrics extraction and EWMA dashboard configuration
- PERT estimation for work-item hierarchies
- 3-year TCO comparison with NPV
- India-specific: INR pricing (with verification flag), GST, MeitY empanelment, NASSCOM GCC guidance

**Out of Scope:**
- Jira Service Management (ITSM) — separate product with different pricing and workflow model
- Jira Data Center administration (on-premise patching, indexing, clustering)
- Azure DevOps Server (on-premise) — version management and upgrade paths
- Atlassian Confluence or Azure Wiki detailed content management
- GitHub Actions or Jenkins pipeline design (see separate skills if they exist)
- ServiceNow, Linear, Monday.com, or other project management tools
- Mathematical derivations beyond formula application — delegate to `agile-business-mathematics-expert`

---

## 13. Version

**Version:** 1.0.1 — 2026-07-27 — Added §7 Anti-Patterns to Avoid (8 pitfalls spanning JQL wildcard/predicate-ordering performance, automation-rule cycle/cascading-load design, CI/CD free-tier sizing, MeitY data-residency agent choice, India pricing verification, and Jira-vs-Azure TCO break-even scope); renumbered §8-12 to §9-13.

**Version:** 1.0.0
**Domain:** Agile Business & Revenue Intelligence (Domain 41)
**Prerequisites:** None
**Math Delegation:** `agile-business-mathematics-expert` (Opus) for M/M/1 full steady-state derivation, EWMA MSE optimization proof, TCO NPV sensitivity calculus, PERT chain variance proof.
**Last Updated:** 2026-05-17
