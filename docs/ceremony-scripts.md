# Scrum Ceremony Facilitator Scripts
## mcp-jira-api Scrum Master Pipeline — India IT Edition

**Context:** Offshore India engineering teams coordinating with onshore stakeholders.
**IST/EST Overlap Window:** 08:30–13:00 EST = 17:30–23:00 IST (4.5 effective hours daily).
**Attrition Assumption:** 18–25% annually; capacity model adjusts team size accordingly.
**NASSCOM AgileX Maturity Levels:** L1 (velocity CV > 0.35) → L5 (CV < 0.05).
**MCP Server:** mcp-jira-api (stdio transport); all tool calls use the tools listed per ceremony.

---

## India National Holiday Calendar 2025–2026

Use this list in Sprint Planning to call `india_holidays_in_sprint()` for capacity deduction.

```
INDIA_NATIONAL_HOLIDAYS_2025_2026 = [
  # 2025
  "2025-01-26",  # Republic Day
  "2025-03-14",  # Holi
  "2025-04-10",  # Ram Navami
  "2025-04-14",  # Ambedkar Jayanti / Good Friday (state-dependent; treat as optional)
  "2025-04-18",  # Good Friday (central government)
  "2025-03-31",  # Eid al-Fitr (approximate; confirm with official notification)
  "2025-05-12",  # Buddha Purnima
  "2025-06-07",  # Eid ul-Adha (approximate; confirm with official notification)
  "2025-08-15",  # Independence Day
  "2025-10-02",  # Gandhi Jayanti
  "2025-10-02",  # Gandhi Jayanti (also Mahatma Gandhi birth anniversary)
  "2025-10-02",  # Dussehra (falls close; check exact date for 2025)
  "2025-10-20",  # Diwali (approximate; varies by region)
  "2025-11-05",  # Guru Nanak Jayanti (approximate; check Sikh calendar)
  "2025-12-25",  # Christmas
  # 2026
  "2026-01-26",  # Republic Day
  "2026-03-03",  # Holi (approximate)
  "2026-03-30",  # Ram Navami (approximate)
  "2026-03-20",  # Eid al-Fitr (approximate; confirm with official notification)
  "2026-05-31",  # Buddha Purnima (approximate)
  "2026-05-27",  # Eid ul-Adha (approximate; confirm with official notification)
  "2026-08-15",  # Independence Day
  "2026-10-02",  # Gandhi Jayanti
  "2026-10-08",  # Dussehra (approximate)
  "2026-11-09",  # Diwali (approximate)
  "2026-11-24",  # Guru Nanak Jayanti (approximate)
  "2026-12-25",  # Christmas
]
```

> **Note:** Islamic holidays (Eid al-Fitr, Eid ul-Adha) are moon-sighting dependent. Confirm exact dates with the official Government of India gazette notification each year. Regional holidays (e.g., Onam, Pongal, Bihu) are additional and must be added per team location.

---

---

## CEREMONY 1: Sprint Planning

### Overview

| Parameter | Standard | India IT Adapted |
|-----------|----------|-----------------|
| Time-box | 4 hours | 4 hours (split into 2×2h sessions if needed) |
| Cadence | Start of each 2-week sprint | Start of each 2-week sprint |
| Recommended slot | Local business hours | 17:30–21:30 IST (overlaps EST morning if offshore sync needed) |
| Attendees | Scrum Team + Product Owner | Same + confirm onshore PO availability in EST overlap window |

### Pre-Ceremony Checklist

Run these checks at least 24 hours before Sprint Planning:

- [ ] Backlog refined and WSJF-scored for top 20+ stories (see Backlog Refinement ceremony)
- [ ] Previous sprint closed and velocity recorded
- [ ] Team capacity confirmed (who is on PTO, who is partial this sprint)
- [ ] India national holidays in the sprint window identified

**MCP Tool Calls to Run Before Ceremony:**

```
# 1. Get last 3-6 sprints of velocity data (primary: Agile API)
jira_get_velocity(
  board_id = "<your-board-id>",
  num_sprints = 6
)

# 2. Get WSJF-scored backlog for planning discussion
jira_refine_backlog(
  project_key = "<PROJECT>",
  max_issues = 30,
  include_wsjf = true
)

# 3. Fallback if Agile API unavailable — search completed stories from last sprint
jira_search_issues(
  jql = "project = <PROJECT> AND sprint in closedSprints() AND status = Done ORDER BY updated DESC",
  fields = ["summary", "story_points", "assignee"],
  max_results = 50
)

# 4. Health check before planning session
jira_health_check()
```

### Facilitator Script

**[00:00–00:10] Opening — Set the Stage**

> "Good morning / Good evening team. Welcome to Sprint [N] Planning.
> Our goal today: agree on a sprint goal that delivers meaningful value, and select the right number of stories to fill our capacity — no more, no less.
> We have [X] story points of average velocity over the last [N] sprints. Today we'll confirm our capacity for this sprint, account for holidays and planned leave, then pull stories from the top of the WSJF-ranked backlog."

**[00:10–00:25] Velocity Review**

Present output from `jira_get_velocity`:

- Show velocity for last 3–6 sprints as a table: Sprint | Committed | Completed | Velocity
- Identify trend: improving, stable, or declining
- Note current NASSCOM AgileX maturity level based on velocity CV:
  - L1: CV > 0.35 — "Our velocity is highly variable. We should focus on stability before adding scope."
  - L2: CV 0.25–0.35 — "We're building consistency. Let's aim to narrow the range this sprint."
  - L3: CV 0.15–0.25 — "Good predictability. WSJF adoption is appropriate at this level."
  - L4: CV 0.05–0.15 — "Strong predictability. We can commit with high confidence."
  - L5: CV < 0.05 — "Excellent. Consider throughput-based flow metrics."
- Use **p70 velocity** as the planning target (conservative; 70th percentile of last 6 sprints).

**[00:25–00:45] Capacity Calculation**

> "Let's confirm who is available this sprint."

Fill in this table live during the session:

```
Team Member | Role       | Days Available | Availability % | Effective Days
-----------|------------|---------------|----------------|---------------
[Name]     | Dev        | 10            | 100%           | 10
[Name]     | Dev        | 10            | 80% (partial)  | 8
[Name]     | QA         | 10            | 100%           | 10
TOTAL      |            |               |                | [sum]
```

India IT capacity adjustments:
- Deduct 1 day per India national holiday in the sprint (reference holiday calendar above)
- Call `india_holidays_in_sprint(sprint_start, sprint_end)` from `scrum_calculator.py` for automated count
- Apply annual attrition risk factor: if team has had >2 departures in last 6 months, reduce velocity target by 10%
- IST overlap constraint: for stories requiring real-time onshore collaboration, flag them — they can only progress during the 4.5-hour overlap window (17:30–23:00 IST)

**Formula:**
```
sprint_capacity_points = (team_available_days / team_standard_days) * p70_velocity
```

**[00:45–02:00] Story Selection — WSJF-Based Ordering**

Present the WSJF-ranked backlog from `jira_refine_backlog`. Stories are already ordered by WSJF score (highest first).

> "We pull from the top of this WSJF-ranked list. We stop when the sum of story points equals our sprint capacity. The PO may override ordering only if there is a deadline or dependency reason — and that reason is recorded in the sprint notes."

WSJF reminder formula:
```
WSJF = (Business Value + Time Criticality + Risk Reduction) / Job Size
```
(All scored on Fibonacci: 1, 2, 3, 5, 8, 13, 20)

For each story selected:
1. Confirm Definition of Ready (see Backlog Refinement for DoR checklist)
2. Assign a team member or mark as unassigned for daily pull
3. Record any dependencies between selected stories

**NASSCOM AgileX L2→L3 Progression Note:**
> "Teams at L2 often resist WSJF because it feels like more overhead. The payoff: at L3, stakeholders trust sprint commitments because they understand why stories are prioritized. If you're at L2, introduce WSJF for the top 10 stories only — don't score the whole backlog on day one."

**[02:00–02:15] Sprint Goal Definition**

> "What is the single sentence that describes the purpose of this sprint? It should be measurable and observable by a non-technical stakeholder."

Template:
> "By the end of Sprint [N], we will have [observable outcome] so that [stakeholder benefit]."

Record the sprint goal in Jira via:
```
jira_update_issue(
  issue_key = "<SPRINT-GOAL-TICKET-OR-EPIC>",
  fields = {"summary": "Sprint [N] Goal: [goal text]"}
)
```

**[02:15–02:45] Task Breakdown (optional, if team is L2 or below)**

For teams at L1–L2: break selected stories into tasks (< 1 day each). Add as sub-tasks via `jira_create_issue`.
For L3+ teams: trust story-level commitments; skip task breakdown.

**[02:45–03:00] Risk and Dependency Check**

> "Are there any stories that depend on external teams, third-party APIs, or onshore decisions? Let's flag them now."

- Add label `external-dependency` to flagged stories via `jira_update_issue`
- For IST/EST coordination-dependent stories: note that they can only advance during 17:30–23:00 IST

**[03:00–04:00] Buffer — Questions, Concerns, Parking Lot**

Address any open questions. Items that cannot be resolved now go to the parking lot and are assigned to a specific person with a due date.

### India IT Notes

- **Best slot:** 17:30–21:30 IST ensures both India team and EST-morning onshore stakeholders can attend the first 2 hours together.
- **Q4 attrition spike (Jan–Mar):** India IT historically sees the highest attrition in Q1 of the calendar year. During Jan–Mar sprints, apply a +15% buffer to job size estimates and reduce sprint commitment to 85% of average velocity.
- **Split sessions:** If the team is fully offshore and no onshore attendance is needed, 10:00–14:00 IST is preferable for team energy levels.
- **Sprint 0 teams:** If the team is newly formed, do not use velocity-based planning. Use capacity-based planning (hours) for the first 3 sprints until velocity stabilizes.

### MCP Tools Used in This Ceremony

| Tool | When Used | Example Input |
|------|-----------|--------------|
| `jira_get_velocity` | Velocity review | `board_id="<ID>", num_sprints=6` |
| `jira_refine_backlog` | Story selection | `project_key="PROJ", max_issues=30` |
| `jira_plan_sprint` | Capacity calculation | `team_size=6, sprint_days=10` |
| `jira_update_issue` | Record sprint goal | `issue_key="PROJ-1", fields={...}` |
| `jira_create_issue` | Add tasks (L1-L2 teams) | `project="PROJ", type="Sub-task"` |
| `jira_health_check` | Pre-ceremony verification | _(no parameters)_ |

### Sprint Planning Output Template

```
Sprint [N] Plan
==============
Sprint Goal: [one sentence]
Sprint Start: [YYYY-MM-DD]
Sprint End:   [YYYY-MM-DD]
India Holidays in Sprint: [N] days → [list dates]

Team Capacity:
  Total available days: [X]
  Standard team days:   [Y]
  Capacity ratio:       [X/Y]
  p70 Velocity (last 6 sprints): [Z] points
  Adjusted Sprint Target: [Z * X/Y] points

Stories Committed:
  [PROJ-NNN] [Summary] — [X pts] — [Assignee]
  [PROJ-NNN] [Summary] — [X pts] — [Assignee]
  ...
  TOTAL: [sum] points

External Dependencies: [list or "None"]
Parking Lot: [list or "None"]
NASSCOM AgileX Level (current): [L1/L2/L3/L4/L5]
```

---

---

## CEREMONY 2: Daily Scrum

### Overview

| Parameter | Standard | India IT Adapted |
|-----------|----------|-----------------|
| Time-box | 15 minutes | 15 minutes (hard stop) |
| Cadence | Daily | Daily, skip India national holidays |
| Recommended slot | Team's choice | **09:30 IST** (avoids early morning fatigue; within overlap window if EST sync needed at 08:30 EST = 18:00 IST) |
| Attendees | Development Team | Development Team; Scrum Master facilitates; PO optional |

### Pre-Ceremony Checklist

Run this immediately before the standup (automate with a scheduled script if possible):

- [ ] Burndown chart reviewed — on track or behind?
- [ ] Any stories moved to Done since last standup?
- [ ] Any new blockers added since last standup?

**MCP Tool Calls to Run Before Ceremony (automated pre-standup report):**

```
# Primary: get standup summary — blocked issues, progress since yesterday
jira_daily_standup(
  board_id = "<your-board-id>",
  sprint_id = "<current-sprint-id>"
)

# Fallback if Agile API unavailable — find blocked issues via JQL
jira_search_issues(
  jql = "project = <PROJECT> AND sprint in openSprints() AND labels = impediment AND status != Done",
  fields = ["summary", "assignee", "status", "labels", "updated"],
  max_results = 20
)
```

### Facilitator Script

**[00:00–00:01] Opening**

> "Good morning everyone. It's 09:30, let's do our Daily Scrum. Hard stop at 09:45. This is not a status meeting — it's a synchronization event. We're here to identify blockers and coordinate, not to report to the Scrum Master."

Display the `jira_daily_standup` output on screen (sprint burndown, blocked issues list).

**[00:01–00:12] Three Questions — Round Robin**

Go person by person. Each person answers three questions in 90 seconds or less:

1. **What did I complete since yesterday?**
   → Reference specific Jira issue keys (e.g., "I finished PROJ-142, moved it to Done")

2. **What will I work on today?**
   → Reference specific Jira issue keys (e.g., "Today I'm picking up PROJ-147")

3. **What is blocking me?**
   → Be specific: "I'm waiting for the API spec from the onshore team" or "PROJ-149 has a failing test I can't reproduce — I need help"

Scrum Master notes all blockers on a shared screen during the round robin.

**[00:12–00:14] Impediment Triage**

For each blocker mentioned:

- If blocker < 2 days old: assign it back to the owner to resolve; check again tomorrow.
- If blocker >= 2 days old or unresolvable by the team:
  - Add `impediment` label via `jira_update_issue`
  - Assign to Scrum Master for escalation
  - Log escalation time in the issue comment via `jira_add_comment`

```
# Label an issue as an impediment
jira_update_issue(
  issue_key = "PROJ-149",
  fields = {"labels": ["impediment"]}
)

# Add escalation comment
jira_add_comment(
  issue_key = "PROJ-149",
  body = "Escalated to SM on [date]. Blocking [team member] since [date]. Root cause: [brief description]. Expected resolution: [date or owner]."
)
```

**[00:14–00:15] Closing**

> "That's our standup. Blockers: [list the ones escalated]. Everyone else, please sync offline if you need to go deeper on any of these. See you tomorrow at 09:30."

Scrum Master updates the impediment backlog if any new items were added.

### India IT Notes

- **09:30 IST rationale:** Avoids the 08:00–09:00 IST slot that causes burnout in offshore teams. If onshore EST stakeholders need to observe, 09:30 IST = 23:00 EST the prior day — not suitable for onshore attendance. Reserve IST/EST overlap window for escalations requiring real-time onshore involvement.
- **Holiday handling:** Skip Daily Scrum on India national holidays. Scrum Master sends a written async update via Jira comment or Slack instead.
- **Async standup option (L3+ teams):** For teams at NASSCOM AgileX L3+, consider replacing the synchronous standup with a bot-assisted async standup (Jira automation posting the three questions to a Slack channel at 09:00 IST). Reserve the synchronous slot for Monday sprint syncs and blocker discussions only.
- **Attrition note:** When a team member's last day falls within the sprint, the Scrum Master must immediately rebalance their in-progress stories at the next standup. Flag affected stories with `capacity-risk` label.
- **IST/EST dependency stories:** If a story is blocked on onshore input, the standup comment should include "Awaiting EST response; next check-in at [time in IST overlap window]."

### MCP Tools Used in This Ceremony

| Tool | When Used | Example Input |
|------|-----------|--------------|
| `jira_daily_standup` | Pre-standup report | `board_id="<ID>", sprint_id="<ID>"` |
| `jira_update_issue` | Label impediments | `issue_key="PROJ-N", fields={"labels":["impediment"]}` |
| `jira_add_comment` | Log escalation details | `issue_key="PROJ-N", body="Escalated..."` |
| `jira_search_issues` | Fallback blocker scan | `jql="labels = impediment AND sprint in openSprints()"` |

### Daily Scrum Output Template

```
Daily Scrum — [YYYY-MM-DD] — 09:30 IST
=======================================
Sprint [N] — Day [X] of 10

Burndown Status: [On Track / At Risk / Behind]
  Points Remaining: [X] of [Y] planned

Progress Since Yesterday:
  [PROJ-NNN] moved to Done — [Assignee]
  [PROJ-NNN] moved to In Review — [Assignee]

Today's Focus:
  [Team Member]: working on [PROJ-NNN]
  [Team Member]: working on [PROJ-NNN], [PROJ-NNN]

Blockers / Impediments:
  [PROJ-NNN] — [Description] — Age: [N days] — Owner: [SM/Dev] — Escalated: [Y/N]

Action Items from This Standup:
  - [Action] → [Owner] → [Due]
```

---

---

## CEREMONY 3: Sprint Review

### Overview

| Parameter | Standard | India IT Adapted |
|-----------|----------|-----------------|
| Time-box | 2 hours | 2 hours (30 min for India-specific velocity review) |
| Cadence | Last day of sprint | Last day of sprint |
| Recommended slot | During IST/EST overlap | 18:00–20:00 IST (08:00–10:00 EST) — maximum stakeholder coverage |
| Attendees | Scrum Team + Stakeholders | Same; onshore stakeholders dial in via video; India team presents |

### Pre-Ceremony Checklist

Run 2 hours before the Sprint Review:

- [ ] All stories in sprint verified as Done or moved to next sprint with documented reason
- [ ] Demo environment is up and tested
- [ ] Velocity calculated and NASSCOM AgileX level assessed
- [ ] Previous sprint review action items reviewed

**MCP Tool Calls to Run Before Ceremony:**

```
# Primary: sprint review summary — velocity, DoD compliance, demo list
jira_sprint_review(
  sprint_id = "<completed-sprint-id>",
  board_id = "<your-board-id>"
)

# Get all Done stories for demo ordering
jira_search_issues(
  jql = "project = <PROJECT> AND sprint = '<Sprint Name>' AND status = Done ORDER BY priority DESC",
  fields = ["summary", "story_points", "assignee", "components", "labels"],
  max_results = 50
)

# Identify stories NOT completed (for spillover discussion)
jira_search_issues(
  jql = "project = <PROJECT> AND sprint = '<Sprint Name>' AND status != Done ORDER BY priority DESC",
  fields = ["summary", "story_points", "assignee", "status"],
  max_results = 20
)
```

### Facilitator Script

**[00:00–00:10] Opening and Sprint Summary**

> "Welcome to the Sprint [N] Review. We completed Sprint [N] on [date]. Here is our summary before we begin the demos."

Present key metrics from `jira_sprint_review` output:

```
Sprint [N] Results
  Committed: [X] stories, [Y] points
  Completed: [A] stories, [B] points
  Completion Rate: [B/Y * 100]%
  Velocity: [B] points
  Sprint Goal: [Achieved / Partially Achieved / Not Achieved]
```

**[00:10–00:40] Velocity Review and NASSCOM AgileX Assessment**

Display velocity trend chart (last 6 sprints) and calculate CV:

```
CV = std_dev(velocities) / mean(velocities)
```

Assess NASSCOM AgileX level:
- **L1 (CV > 0.35):** "Our velocity is highly variable — [X] points this sprint vs [Y] last sprint. Our primary improvement goal is predictability. We'll focus on story size consistency and reducing scope changes mid-sprint."
- **L2 (CV 0.25–0.35):** "We're building rhythm. Velocity is stabilizing. Let's continue refining our estimation calibration."
- **L3 (CV 0.15–0.25):** "Good predictability. Stakeholders can now rely on our commitments for release planning."
- **L4 (CV 0.05–0.15):** "Excellent. We're ready to discuss flow metrics and lead time optimization."
- **L5 (CV < 0.05):** "Industry-leading predictability. Consider adopting Kanban flow metrics alongside Scrum velocity."

> **India benchmark note:** India VSI (Value Stream Index) flow efficiency typically runs 6–12% for teams at L1–L2. Target 25–40% for L3+ teams. Flow efficiency is measured as: `value_add_time / total_lead_time * 100`.

**[00:40–01:20] Demo Session**

Work through the Done stories in WSJF priority order (highest business value first).

For each demo item:

> "[Team Member], please walk us through [PROJ-NNN] — [Summary]."

Demo checklist per story:
- [ ] Feature demonstrated in a working environment (not slides)
- [ ] Acceptance criteria verified live during demo
- [ ] Stakeholders asked: "Does this meet your expectation?"
- [ ] Any feedback captured immediately in a Jira comment:

```
jira_add_comment(
  issue_key = "PROJ-NNN",
  body = "Sprint Review feedback from [stakeholder]: [feedback text]. Action: [none / follow-up required]."
)
```

**[01:20–01:30] Spillover Discussion**

For each story NOT completed:
- State the reason (scope change, dependency, complexity underestimate, attrition)
- Decision: carry to next sprint (default) or return to backlog

```
jira_update_issue(
  issue_key = "PROJ-NNN",
  fields = {"labels": ["spillover-sprint-N"]}
)
```

Record spillover count in the team's metrics tracker. Consistent spillover (>2 stories per sprint) triggers a retrospective action item.

**[01:30–01:50] Stakeholder Feedback and Backlog Impact**

> "Based on what you've seen today, do you want to adjust priorities in the upcoming backlog?"

Capture any new requests as brief notes. These are NOT committed in this ceremony — they go to backlog refinement.

New feedback items → create as Jira stories immediately:
```
jira_create_issue(
  project = "<PROJECT>",
  issue_type = "Story",
  summary = "[Stakeholder feedback]: [brief description]",
  description = "Captured during Sprint [N] Review on [date]. Requester: [stakeholder name]. Details: [...]",
  labels = ["sprint-review-feedback", "needs-refinement"]
)
```

**[01:50–02:00] Closing and Next Sprint Preview**

> "Thank you everyone. Sprint [N+1] Planning is on [date]. The top candidates for next sprint are [top 3 WSJF stories]. We'll finalize selection in Planning."

### India IT Notes

- **Presentation ownership:** India team members should present their own work. Avoid the Scrum Master or tech lead narrating on behalf of the team — this signals low L1/L2 team autonomy.
- **Video on policy:** Request all attendees have cameras on for the first 10 minutes. India teams often disable cameras due to bandwidth — acknowledge this and do not penalize it.
- **IST demo scheduling:** If demos require onshore live observation, 18:00–20:00 IST (08:00–10:00 EST) is the optimal slot. Stakeholders in PST (UTC-8) should dial in at 05:00–07:00 PST — flag this as a hardship and offer async video recording as alternative.
- **Attrition impact on demos:** If a team member has left since the start of the sprint and their stories were completed by another member, the replacement presenter should state this explicitly: "I picked up this story from [name] mid-sprint."

### MCP Tools Used in This Ceremony

| Tool | When Used | Example Input |
|------|-----------|--------------|
| `jira_sprint_review` | Pre-ceremony metrics | `sprint_id="<ID>", board_id="<ID>"` |
| `jira_search_issues` | Done stories for demo list | `jql="sprint = '...' AND status = Done"` |
| `jira_add_comment` | Capture stakeholder feedback | `issue_key="PROJ-N", body="Feedback..."` |
| `jira_update_issue` | Label spillover stories | `issue_key="PROJ-N", fields={...}` |
| `jira_create_issue` | Log new backlog items | `project="PROJ", type="Story"` |

### Sprint Review Output Template

```
Sprint [N] Review — [YYYY-MM-DD] — 18:00 IST
=============================================
Sprint Goal: [text] — Status: [Achieved / Partial / Not Achieved]

Velocity:
  Committed: [X] pts | Completed: [Y] pts | Completion Rate: [Y/X*100]%
  6-Sprint Average: [avg] pts | CV: [value] | AgileX Level: [L1-L5]
  India VSI Flow Efficiency: [value]% (Target for L3+: 25-40%)

Demos Completed:
  [PROJ-NNN] — [Summary] — [Presenter] — Stakeholder: [Approved / Feedback pending]
  ...

Spillover (not completed):
  [PROJ-NNN] — [Reason] — Decision: [Carry forward / Return to backlog]

New Backlog Items from Review:
  [PROJ-NNN] — [Summary] — Priority: [TBD in refinement]

Next Sprint Planning: [date at time IST]
```

---

---

## CEREMONY 4: Sprint Retrospective

### Overview

| Parameter | Standard | India IT Adapted |
|-----------|----------|-----------------|
| Time-box | 1.5 hours | 1.5 hours |
| Cadence | Last day of sprint (after Review) | Same day as Review, 30 min after Review ends |
| Recommended slot | After Sprint Review | 20:30–22:00 IST (same day as Review) |
| Attendees | Scrum Team only | Scrum Team only; NO stakeholders; NO management |

### Retrospective Format Rotation

Rotate formats every sprint to avoid habituation. Reset after 4 sprints:

| Sprint Modulo 4 | Format |
|-----------------|--------|
| Sprint % 4 == 1 | **4-Ls** (Liked, Learned, Lacked, Longed For) |
| Sprint % 4 == 2 | **Start-Stop-Continue** |
| Sprint % 4 == 3 | **Mad-Sad-Glad** |
| Sprint % 4 == 0 | **5-Whys** (root cause analysis for top issue) |

### Pre-Ceremony Checklist

- [ ] Previous sprint's retrospective action items reviewed — which were completed?
- [ ] RE (Retrospective Effectiveness) score from last retro calculated
- [ ] Anonymous feedback tool prepared (if using digital boards: FunRetro, Miro, etc.)
- [ ] Timer visible to all participants

**MCP Tool Calls to Run Before Ceremony:**

```
# Generate retrospective context — action items from last sprint, blockers, velocity trend
jira_retrospective(
  sprint_id = "<completed-sprint-id>",
  board_id = "<your-board-id>"
)

# Verify previous retro action items — were they done?
jira_search_issues(
  jql = "project = <PROJECT> AND labels = retro-action AND sprint in closedSprints() ORDER BY updated DESC",
  fields = ["summary", "assignee", "status", "labels"],
  max_results = 20
)
```

### Facilitator Script

**[00:00–00:05] Opening — Safety and Ground Rules**

> "Welcome to the Sprint [N] Retrospective. This is a closed session — team only. Everything said here stays here.
>
> Ground rules:
> 1. We talk about processes and systems, not people. 'The deployment process is slow' — not 'John is slow.'
> 2. We assume positive intent from everyone.
> 3. If you're not comfortable speaking up verbally, write it down anonymously on the digital board.
> 4. We end with commitments, not complaints."

> **Psychological safety note:** Collect written input anonymously before discussion. Report only team-level aggregates to management — never attribute individual feedback to a person. If a team member is silent for two consecutive retros, check in privately.

**[00:05–00:10] Previous Action Item Review**

Display previous sprint's action items from `jira_retrospective` output.

For each action item:
- Status: Done / In Progress / Not Done
- If Not Done: Was it blocked? Does it carry forward? Reassign if original owner is gone.

> "We committed to [N] action items last sprint. [X] are done — well done. [Y] are carrying forward."

**[00:10–00:15] RE Score Review**

Calculate and share the Retrospective Effectiveness (RE) score (from `retrospective_effectiveness()` in `scrum_calculator.py`):

```
RE_score = (action_items_completed / action_items_committed) * 100
```

| RE Score | Interpretation |
|----------|---------------|
| 80–100% | High effectiveness — the team follows through |
| 60–79% | Moderate — some action items are falling through the cracks |
| 40–59% | Low — too many action items; reduce to 2–3 per sprint |
| < 40% | Critical — the retrospective is not driving change; escalate |

> "Our RE score this sprint is [X]%. [Interpretation from table above]."

**[00:15–01:00] Retrospective Format (45 minutes)**

**FORMAT A: 4-Ls (Sprint % 4 == 1)**

Columns: Liked | Learned | Lacked | Longed For

1. (5 min) Silent writing — each person adds sticky notes to all 4 columns anonymously
2. (10 min) SM reads and groups similar items without attribution
3. (20 min) Discuss top 2 items per column; focus on systemic causes
4. (10 min) Vote on top 3 items to act on

**FORMAT B: Start-Stop-Continue (Sprint % 4 == 2)**

Columns: Start Doing | Stop Doing | Continue Doing

1. (5 min) Silent writing
2. (10 min) Read and group
3. (20 min) Discuss top items; each Start and Stop item must have a specific reason
4. (10 min) Vote on top 3

**FORMAT C: Mad-Sad-Glad (Sprint % 4 == 3)**

Columns: What made us Mad | What made us Sad | What made us Glad

1. (5 min) Silent writing — emphasize emotional acknowledgment first
2. (5 min) SM reads items aloud without attribution
3. (25 min) Focus discussion on Mad and Sad items first; end with Glad to close on a positive
4. (10 min) Vote on top 3 Mad/Sad items for action

**FORMAT D: 5-Whys (Sprint % 4 == 0)**

Select the top recurring problem from the previous 3 sprints. Ask "Why?" five times to find root cause.

Example:
- Problem: Velocity dropped by 20% this sprint
- Why 1: Three stories were blocked for >3 days
- Why 2: They needed third-party API integration that wasn't documented
- Why 3: We didn't identify the API dependency during Backlog Refinement
- Why 4: The DoR checklist doesn't include an "external API identified" check
- Why 5: The DoR was written 6 months ago and hasn't been reviewed
- Root Cause: Stale Definition of Ready
- Action: Review and update DoR checklist in next Backlog Refinement

**[01:00–01:20] Action Item Definition**

For each identified improvement area, define a SMART action item:

```
SMART Action Item Template:
  What: [specific action, not vague]
  Who: [one named owner — not "the team"]
  When: [target sprint number or date]
  Acceptance Criterion: [how do we know it's done?]
  Jira Issue: [create immediately]
```

Limit to **2–3 action items maximum per sprint.** More than 3 items dilutes focus and reduces RE score.

Create each action item in Jira immediately:
```
jira_create_issue(
  project = "<PROJECT>",
  issue_type = "Task",
  summary = "[Retro Action Sprint N]: [brief description]",
  description = "Owner: [name]\nTarget Sprint: [N+1]\nAcceptance Criterion: [text]\nContext: Generated from Sprint [N] Retrospective using [format name] format.",
  labels = ["retro-action", "sprint-N-retro"],
  assignee = "[owner-jira-username]"
)
```

**[01:20–01:30] Closing — Commitment and Appreciation**

> "Let's close with a quick round: one word or phrase that describes how you're leaving this retrospective."

Go around the room (or virtual call). Capture the tone — it's a leading indicator of psychological safety.

If the tone is consistently negative for 2+ retros, the Scrum Master should flag this to the Agile Coach privately.

> "Our [N] action items for Sprint [N+1] are: [list]. [Owners] — you own these. Let's make our RE score [target]% next sprint."

### India IT Notes

- **Anonymity is critical in India IT context:** Hierarchical culture norms may suppress candid feedback if names are attached. Always use anonymous input tools for the writing phase.
- **Off-camera participation:** Some team members may be more candid in text than verbally. Accept written input equivalently to verbal contributions.
- **Attrition-related retro topics:** When a team member has left, it is appropriate to discuss the impact on the team (knowledge gaps, morale) but not to critique the departed individual. Focus on: "What process would have made knowledge transfer easier?"
- **Q1 (Jan–Mar) retrospectives:** Expect higher emotional load during India's peak attrition season. The Mad-Sad-Glad format is recommended for Jan–Mar sprints to provide emotional acknowledgment space.
- **Action item carry-forward:** If an action item is not completed and the owner has left the company, reassign it in the first retro after their departure. Do not let it silently drop.
- **IST/EST retro scheduling:** Retros are India-team-internal. No onshore attendance required. Schedule at a time comfortable for the India team — 20:30–22:00 IST is workable but confirm team preference; some may prefer 10:00–11:30 IST the following morning.

### MCP Tools Used in This Ceremony

| Tool | When Used | Example Input |
|------|-----------|--------------|
| `jira_retrospective` | Pre-retro context | `sprint_id="<ID>", board_id="<ID>"` |
| `jira_search_issues` | Previous action item review | `jql="labels = retro-action AND sprint in closedSprints()"` |
| `jira_create_issue` | Log action items | `project="PROJ", type="Task", labels=["retro-action"]` |
| `jira_update_issue` | Mark completed action items | `issue_key="PROJ-N", fields={"status":...}` |
| `jira_add_comment` | Add RE score note | `issue_key="PROJ-RETRO-N", body="RE score: X%..."` |

### Sprint Retrospective Output Template

```
Sprint [N] Retrospective — [YYYY-MM-DD] — 20:30 IST
====================================================
Format: [4-Ls / Start-Stop-Continue / Mad-Sad-Glad / 5-Whys]
Attendance: [N] of [M] team members

RE Score (this sprint): [X]% ([N] of [M] action items completed)
RE Score Trend: [improving / stable / declining]

Previous Action Items:
  [PROJ-NNN] — [Done / Not Done / Carrying Forward] — [Owner]
  ...

Key Themes from Discussion (anonymized, aggregate):
  Positives: [themes]
  Challenges: [themes]
  Root Cause (5-Whys, if applicable): [root cause]

Action Items for Sprint [N+1]:
  1. [PROJ-NNN] — [What] — Owner: [Name] — Due: Sprint [N+1] — Criterion: [text]
  2. [PROJ-NNN] — [What] — Owner: [Name] — Due: Sprint [N+1] — Criterion: [text]
  (max 3)

Closing Sentiment Words: [list of words shared by team]
Psychological Safety Indicator: [Positive / Neutral / Concerning]
```

---

---

## CEREMONY 5: Backlog Refinement

### Overview

| Parameter | Standard | India IT Adapted |
|-----------|----------|-----------------|
| Time-box | 2 hours | 2 hours (max; can be 1h if backlog is well-maintained) |
| Cadence | Mid-sprint (Sprint Day 6–7 of a 10-day sprint) | Same |
| Recommended slot | During business hours | **10:00–12:00 IST** (comfortable India time; also within any IST/EST overlap if PO is onshore) |
| Attendees | Scrum Team + Product Owner | Same; onshore PO should attend if WSJF scoring requires business context |

### Pre-Ceremony Checklist

Run 30 minutes before the session:

- [ ] Raw backlog list exported and sorted by approximate business priority
- [ ] WSJF scoring template prepared
- [ ] Velocity and team capacity context available for estimation calibration
- [ ] Definition of Ready (DoR) checklist printed/displayed

**MCP Tool Calls to Run Before Ceremony:**

```
# Get WSJF-scored backlog — identifies candidates needing refinement
jira_refine_backlog(
  project_key = "<PROJECT>",
  max_issues = 40,
  include_wsjf = true
)

# Get current velocity for estimation context
jira_get_velocity(
  board_id = "<your-board-id>",
  num_sprints = 6
)

# Find stories that are ready (for verification against DoR)
jira_search_issues(
  jql = "project = <PROJECT> AND status = 'Backlog' AND story_points is EMPTY ORDER BY priority DESC",
  fields = ["summary", "description", "acceptanceCriteria", "labels"],
  max_results = 30
)
```

### WSJF Scoring Table

Use this table during the session. Score all dimensions on Fibonacci scale: 1, 2, 3, 5, 8, 13, 20.

```
WSJF Scoring Table — Sprint [N] Backlog Refinement — [date]
============================================================
Story | Business Value | Time Criticality | Risk Reduction | Job Size | WSJF Score
      | (BV)           | (TC)             | (RR)           | (JS)     | = (BV+TC+RR)/JS
------|----------------|-----------------|----------------|----------|------------------
[ID] [Summary] |  |  |  |  | [formula result]
...
```

**Dimension Definitions:**

| Dimension | What to Score High | Score Low When |
|-----------|-------------------|----------------|
| Business Value (BV) | Core user functionality, revenue-generating features, compliance requirements | Technical debt, internal tooling |
| Time Criticality (TC) | Deadline-driven features, regulatory cutoffs, competitive pressure | No external deadline |
| Risk Reduction (RR) | Removes technical risk, unblocks other work, reduces attrition knowledge concentration | Low-risk, isolated feature |
| Job Size (JS) | Large, complex, multi-component work | Small, well-understood, single-component |

**WSJF Formula:**
```
WSJF = (Business_Value + Time_Criticality + Risk_Reduction) / Job_Size
```

Higher WSJF = higher priority. Stories with WSJF >= 5 should be in the top 10.

**India Q4 Attrition Adjustment (Jan–Mar):**
During Q1 (Jan–Mar), apply a +1 to Job Size for stories that require deep knowledge from individuals with >6 months tenure, if those individuals have submitted resignation (or if team attrition rate this year has already exceeded 20%). This reflects the hidden cost of knowledge transfer.

### Definition of Ready (DoR) Checklist

A story is Ready for Sprint Planning only if ALL 6 items are true:

- [ ] **1. Clear Summary:** Story summary is unambiguous; a new team member could understand the intent
- [ ] **2. Acceptance Criteria:** At least 2 testable acceptance criteria written in Given/When/Then or equivalent format
- [ ] **3. Story Points Estimated:** Story point estimate agreed by the team (not by one person alone)
- [ ] **4. Dependencies Identified:** All known upstream dependencies listed (other stories, external APIs, onshore input)
- [ ] **5. External API/Integration Identified:** If the story requires any third-party API or service, the API is documented or accessible in the dev environment
- [ ] **6. Design Artifacts:** UI mockup (if UI story) or data model (if data story) available and linked to the Jira issue

Stories failing DoR go back to the Product Owner with specific missing items noted. They are NOT pulled into Sprint Planning until all 6 DoR items are met.

### Facilitator Script

**[00:00–00:10] Opening and Velocity Context**

> "Welcome to Backlog Refinement for Sprint [N+1] preparation. Our velocity over the last 6 sprints averages [X] points. This session's goal: ensure we have at least [2×X] points of Ready stories at the top of the backlog before Sprint Planning."

> "Two times velocity" is the target backlog buffer — enough Ready stories for one full sprint, plus a reserve if scope changes.

**[00:10–00:50] WSJF Scoring Round**

Display the unscored stories from `jira_refine_backlog` output. For each story in the top 20:

1. PO presents the story in 2 minutes (summary, business context)
2. Team asks clarifying questions (5 minutes max)
3. Each team member silently scores BV, TC, RR (30 seconds)
4. Reveal scores simultaneously (planning poker style or show of hands)
5. If scores diverge by >50%: discuss for 2 minutes, re-score once
6. Estimate Job Size (story points) using team consensus

Record scores in Jira:
```
jira_update_issue(
  issue_key = "PROJ-NNN",
  fields = {
    "story_points": [estimated_points],
    "labels": ["wsjf-scored"],
    "customfield_wsjf": [calculated_wsjf_score]
  }
)
```

**[00:50–01:20] Definition of Ready Verification**

For the top 10 stories by WSJF score, run through the DoR checklist.

For each story:
- Verify all 6 DoR items
- If any are missing: assign the specific missing item to the PO or a team member with a due date (before Sprint Planning)
- Label stories that are Ready: `jira_update_issue` with label `dor-ready`
- Label stories that are NOT Ready: label `dor-incomplete` with comment listing missing items

```
jira_add_comment(
  issue_key = "PROJ-NNN",
  body = "DoR Check [date]: Missing items: [list]. Assigned to: [owner]. Must be complete before Sprint [N+1] Planning on [date]."
)
```

**[01:20–01:40] Story Splitting (if needed)**

Stories with Job Size > 8 are candidates for splitting. A story that takes more than half a sprint is too large — the team cannot pivot or replan effectively.

Splitting approaches:
- **Workflow split:** "User can view orders" → "User can view order list" + "User can view order detail"
- **Data split:** "Support all payment types" → "Support credit card" + "Support UPI" + "Support net banking"
- **Happy path first:** "User can upload documents with validation" → "User can upload documents" + "Add file type and size validation"

```
jira_create_issue(
  project = "<PROJECT>",
  issue_type = "Story",
  summary = "[split from PROJ-NNN]: [specific split story name]",
  description = "Split from parent story [PROJ-NNN] during Sprint [N] Backlog Refinement on [date]. Original story was [X] points; this story is estimated at [Y] points.",
  labels = ["split-story"],
  parent = "PROJ-NNN"
)
```

**[01:40–01:55] Backlog Ordering Confirmation**

Display final WSJF-ranked order of Ready stories. PO confirms or adjusts order with justification.

> "Here are the top [N] Ready stories in WSJF order. Does this ordering align with business priorities for next sprint? Any overrides need a stated reason."

Record the final ordered list as the planning input.

**[01:55–02:00] Closing**

> "We now have [N] Ready stories totaling [X] points — [meets / does not meet] our 2× velocity buffer of [2X] points. Sprint Planning is on [date]."

If buffer is not met: schedule a 30-minute catch-up session with the PO before Sprint Planning to get remaining stories to Ready.

### India IT Notes

- **WSJF buy-in at L2:** Teams at NASSCOM AgileX L2 often find WSJF scoring time-consuming. Reduce friction by pre-scoring Business Value and Time Criticality with the PO before the session. The team only needs to validate BV/TC and add Risk Reduction + Job Size during the meeting.
- **Onshore PO availability:** If the PO is onshore (EST), schedule refinement at 10:00–12:00 IST (00:00–02:00 EST) — this is outside EST business hours. Consider an async pre-refinement: PO records a 5-minute Loom/video for each major story; team watches before the session.
- **India Q4 (Jan–Mar) attrition spike:** During this period, explicitly ask "If [team member] leaves tomorrow, can someone else complete this story?" for any story estimated >5 points. If the answer is no, add Risk Reduction +2 and also assign a shadow/co-owner.
- **Job size calibration:** India teams often underestimate stories involving:
  - Third-party API integrations (hidden auth/rate-limit complexity)
  - Onshore approval gates (dependency on stakeholders in another timezone)
  - Compliance requirements (GDPR, SOC2, DPDP Act India)
  Add a +1 Job Size adjustment for stories in these categories.
- **10:00 IST recommendation:** Avoids post-lunch energy dip (14:00 IST is the worst time for estimation accuracy) and is within IST/EST overlap window if the PO needs to dial in.

### MCP Tools Used in This Ceremony

| Tool | When Used | Example Input |
|------|-----------|--------------|
| `jira_refine_backlog` | WSJF-scored backlog display | `project_key="PROJ", max_issues=40` |
| `jira_get_velocity` | Estimation context | `board_id="<ID>", num_sprints=6` |
| `jira_update_issue` | Record WSJF scores, DoR labels | `issue_key="PROJ-N", fields={...}` |
| `jira_add_comment` | Document DoR failures | `issue_key="PROJ-N", body="DoR missing: ..."` |
| `jira_create_issue` | Create split stories | `project="PROJ", type="Story"` |
| `jira_search_issues` | Find unestimated stories | `jql="story_points is EMPTY AND status = Backlog"` |

### Backlog Refinement Output Template

```
Backlog Refinement — [YYYY-MM-DD] — 10:00 IST
===============================================
Preparing for Sprint [N+1] (starts [date])

Velocity Context (last 6 sprints): avg=[X] pts, CV=[value], AgileX Level=[L]
Target Ready Buffer: [2X] points

Stories Refined and WSJF-Scored:
  Rank | Story        | BV | TC | RR | JS | WSJF | DoR Status
  -----|--------------|----|----|----|----|------|------------
  1    | [PROJ-NNN]  | 8  | 5  | 3  | 3  | 5.33 | Ready
  2    | [PROJ-NNN]  | 5  | 8  | 2  | 5  | 3.00 | Ready
  3    | [PROJ-NNN]  | 13 | 2  | 2  | 8  | 2.13 | DoR incomplete: missing AC
  ...

Stories Split This Session:
  [PROJ-NNN] (original, [X]pts) → [PROJ-NNN1] ([Y]pts) + [PROJ-NNN2] ([Z]pts)

Ready for Sprint Planning: [N] stories, [X] points
DoR Incomplete (needs PO action before planning): [N] stories
  [PROJ-NNN] — Missing: [item] — Owner: [name] — Due: [date]

Q4 Attrition Adjustments Applied: [Y/N — list if yes]
```

---

---

## Appendix: IST/EST Coordination Quick Reference

```
IST Time       EST Time       Suitability
-----------    -----------    --------------------------------------------------
09:30 IST      23:00 EST*     Daily Scrum (India team; EST cannot attend)
10:00 IST      23:30 EST*     Backlog Refinement (India team; EST async only)
17:30 IST      07:00 EST      Sprint Planning start (EST can attend from 08:00 EST)
18:00 IST      07:30 EST      Sprint Review (optimal for EST morning attendance)
20:30 IST      10:00 EST      Retrospective (India team only; EST overlaps but should not attend)
21:30 IST      11:00 EST      Sprint Planning Part 2 / end (EST still available)

* Previous day in EST; not suitable for live EST attendance
```

> All times assume EST (UTC-5). During EDT (UTC-4, Mar–Nov), subtract 1 hour from EST column.

---

## Appendix: NASSCOM AgileX Level Quick Guide

| Level | Velocity CV | Key Characteristics | Recommended Focus |
|-------|-------------|--------------------|--------------------|
| L1 | > 0.35 | Highly variable, unpredictable sprints | Story sizing consistency, reducing mid-sprint scope changes |
| L2 | 0.25–0.35 | Building rhythm, some predictability | WSJF adoption for top-10 backlog, DoR enforcement |
| L3 | 0.15–0.25 | Good predictability, WSJF operational | Flow efficiency improvement, lead time reduction |
| L4 | 0.05–0.15 | Strong predictability, flow metrics active | Throughput optimization, continuous flow exploration |
| L5 | < 0.05 | Industry-leading | Kanban-Scrum hybrid, value stream mapping |

India VSI (Value Stream Index) Flow Efficiency benchmark:
- Typical India IT: 6–12%
- Target for L3+: 25–40%
- Formula: `(value_add_time / total_lead_time) * 100`
