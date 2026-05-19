# Jira Automation Rules — Scrum Master Pipeline

> These specifications describe Jira native automation rules (Jira Automation / formerly Automation for Jira). They do NOT require the MCP server — they run inside the Jira instance itself. The MCP tools (`jira_add_comment`, `jira_update_issue`) are used when the Scrum Master agent triggers equivalent actions programmatically outside Jira.

**DAG Cycle Check Legend**

| Result | Meaning |
|---|---|
| **SAFE** | The rule cannot trigger itself or create a loop through other rules |
| **UNSAFE** | The rule action fires the same trigger or triggers another rule that loops back |

---

## Rule 1 — Impediment Auto-Label

### Summary

Automatically labels an issue as an impediment when its status has not changed within an active sprint for 48 hours, and adds a comment notifying the assignee and Scrum Master.

### Trigger

| Field | Value |
|---|---|
| **Type** | Scheduled |
| **Schedule** | Every 4 hours (cron: `0 */4 * * *`) |
| **Scope** | Issues matching: `project = "{PROJECT}" AND sprint in openSprints() AND status in ("In Progress", "To Do") AND statusCategory != Done` |

### Conditions

1. The issue is in an **active sprint** (sprint state = `active`).
2. The issue status has **not changed in the last 48 hours** — evaluated via Jira Automation `{{issue.status.lastUpdated}}` older than `now() - 48h`.
3. The issue does **not already have the `impediment` label** — prevents duplicate labelling and avoids re-triggering.

### Actions

| Step | Action | Detail |
|---|---|---|
| 1 | **Add label** | Add label `impediment` to the issue |
| 2 | **Add comment** | `@{{issue.assignee.displayName}} This issue has been in {{issue.status.name}} for more than 48 hours without a status change. It has been flagged as an impediment. Please update the issue or raise a blocker at the next standup.` |

### DAG Cycle Check

**Result: SAFE**

- Trigger: Scheduled (time-based) — not triggered by label addition or comment events.
- The label addition (Action 1) cannot re-fire this rule because the condition in step 3 explicitly excludes issues already carrying the `impediment` label.
- The comment addition (Action 2) does not change issue status or labels, so it cannot trigger any other rule in this specification.

---

## Rule 2 — Daily Standup Reminder

### Summary

Posts a standup reminder comment on each assigned, in-progress issue every weekday morning (09:00 IST / 03:30 UTC), directed at the issue assignee.

### Trigger

| Field | Value |
|---|---|
| **Type** | Scheduled |
| **Schedule** | Monday–Friday at 03:30 UTC (cron: `30 3 * * 1-5`) |
| **Scope** | Issues matching: `project = "{PROJECT}" AND sprint in openSprints() AND assignee is not EMPTY AND statusCategory != Done` |

### Conditions

1. The issue is in an **active sprint** (sprint state = `active`).
2. The issue has an **assignee set** (`assignee is not EMPTY`).
3. The issue is **not in Done status category** — avoids posting reminders on completed work.

### Actions

| Step | Action | Detail |
|---|---|---|
| 1 | **Add comment** | `@{{issue.assignee.displayName}} Daily standup in 30 minutes. Please prepare your update: what did you complete, what are you working on today, and do you have any blockers?` |

### DAG Cycle Check

**Result: SAFE**

- Trigger: Scheduled (time-based) — not triggered by comment events.
- The only action is a comment addition. Jira Automation does not re-fire scheduled rules based on comment creation by the rule itself.
- No label changes, status transitions, or field updates occur that could trigger other rules.

---

## Rule 3 — Sprint Completion Notification

### Summary

When all issues in an active sprint reach Done status, posts a sprint completion notification comment on every sprint issue, signalling that the sprint is ready for closure review.

### Trigger

| Field | Value |
|---|---|
| **Type** | Issue transitioned |
| **Event** | Status changed to `Done` |
| **Scope** | Issues matching: `project = "{PROJECT}" AND sprint in openSprints()` |

### Conditions

1. The issue **belongs to an active sprint** (sprint state = `active`).
2. **All other issues in the same sprint are also in Done status** — evaluated using Jira Automation JQL lookup: `sprint = {{issue.sprint.id}} AND statusCategory != Done AND issue != {{issue.key}}` returns 0 results.
3. The sprint has **at least 1 issue** (prevents firing on empty sprints).

### Actions

| Step | Action | Detail |
|---|---|---|
| 1 | **Re-fetch sprint issues** | JQL: `sprint = {{issue.sprint.id}}` (Automation JQL lookup block) |
| 2 | **For each issue in sprint** | Loop: add comment to each issue |
| 3 | **Add comment (looped)** | `Sprint {{issue.sprint.name}} is complete — all issues have reached Done. This sprint is ready for review and closure. The Scrum Master will schedule the retrospective shortly.` |

### DAG Cycle Check

**Result: SAFE**

- The comment addition (Action 3) does not change any issue's status.
- The trigger is `status changed to Done`. The rule actions do not change status; therefore the rule cannot trigger itself on the same issue.
- The loop adds comments to other sprint issues, but those issues are already in Done status and their status is not changed, so the trigger condition (`status changed to Done`) is not re-fired for them.

---

## Rule 4 — DoD Checklist Sub-task Creation

### Summary

When a Story-type issue transitions to `In Progress`, automatically creates a `dod-checklist` sub-task if one does not already exist. This enforces the Definition of Done process gate.

### Trigger

| Field | Value |
|---|---|
| **Type** | Issue transitioned |
| **Event** | Status changed to `In Progress` |
| **Scope** | Issues matching: `project = "{PROJECT}" AND issueType = Story` |

### Conditions

1. The issue **type is Story** (not Task, Bug, or Sub-task).
2. The issue does **not already have a sub-task with summary containing `dod-checklist`** — checked via Jira Automation sub-task lookup: `parent = {{issue.key}} AND summary ~ "dod-checklist"` returns 0 results.
3. The issue is in an **active sprint** (sprint state = `active`) — prevents creating DoD sub-tasks for backlog refinement transitions on future-sprint stories.

### Actions

| Step | Action | Detail |
|---|---|---|
| 1 | **Create sub-task** | Issue type: `Sub-task`; Summary: `[dod-checklist] Definition of Done checklist for {{issue.key}}`; Assignee: `{{issue.assignee}}`; Description: See sub-task description template below |

**Sub-task description template:**

```
Definition of Done checklist for {{issue.summary}}

[ ] Code reviewed and approved
[ ] Unit tests written and passing
[ ] Integration tests passing
[ ] Documentation updated
[ ] Acceptance criteria verified by PO
[ ] No open sub-tasks remaining
[ ] Deployed to staging environment
```

### DAG Cycle Check

**Result: SAFE**

- Trigger: `status changed to In Progress` on a Story.
- Action: Creates a Sub-task. The new sub-task is of type `Sub-task`, not `Story`, so this rule's `issueType = Story` condition does not match it.
- The sub-task is created in its default status (typically `To Do`), which is not `In Progress`, so the trigger (`status changed to In Progress`) is not fired for the new sub-task.
- Creating a sub-task does not change the parent story's status, so the rule does not re-fire on the parent.

---

## Rule 5 — WSJF Re-score Reminder

### Summary

For issues that remain unestimated (no story points) for more than 14 days after creation, automatically adds a `needs-estimation` label and posts a comment requesting refinement attention.

### Trigger

| Field | Value |
|---|---|
| **Type** | Scheduled |
| **Schedule** | Daily at 06:00 UTC (cron: `0 6 * * *`) |
| **Scope** | Issues matching: `project = "{PROJECT}" AND issueType in (Story, Task) AND "Story Points" is EMPTY AND statusCategory != Done AND created <= -14d` |

### Conditions

1. The issue **has no story points** (`Story Points` field is empty).
2. The issue was **created more than 14 days ago** (`created <= -14d`).
3. The issue is **not already labelled `needs-estimation`** — prevents duplicate labelling on subsequent daily runs.
4. The issue is **not in Done status category** — avoids retrospective noise on already-closed work.

### Actions

| Step | Action | Detail |
|---|---|---|
| 1 | **Add label** | Add label `needs-estimation` to the issue |
| 2 | **Add comment** | `This issue has been open for more than 14 days without story point estimation. Please add story points during the next backlog refinement session so it can be planned into a future sprint. Label \`needs-estimation\` has been applied.` |

### DAG Cycle Check

**Result: SAFE**

- Trigger: Scheduled (time-based) — not triggered by label addition or comment events.
- The label addition (Action 1) cannot re-fire this rule because condition 3 explicitly excludes issues already carrying the `needs-estimation` label.
- The comment addition (Action 2) does not modify story points, status, or labels, so it cannot satisfy the trigger scope JQL on the next run.
- Once story points are added by the team, the issue exits the scheduled rule's scope (`"Story Points" is EMPTY` no longer matches) and is automatically excluded from future runs.
