# STRIDE Threat Model -- mcp-jira-api Gap Closure (11 new/modified tools)
<!-- Author: security_defense_architect | Date: 2026-05-29 | Phase: F.1 -->

## System Context

- Local stdio MCP server. No network listener, no public port, no browser.
- Auth: JIRA_URL, JIRA_USER, JIRA_API_TOKEN read from environment variables only.
- Input surface: tool parameters supplied by the Claude Code MCP orchestrator (trusted caller).
- Output: JSON strings over stdio.
- No database, no user accounts, no session, no webhooks.
- Existing mitigations: input_validator.validate_input (null-byte strip, length cap),
  @mcp_tool_handler (catches all exceptions, never leaks tracebacks to the caller by default).

## Tools In Scope

jira_sprint_review (modified), jira_create_epic, jira_get_epic, jira_link_to_epic,
jira_list_epics, jira_create_version, jira_list_versions, jira_release_version,
jira_release_notes, jira_program_velocity, jira_cross_team_health, jira_dependency_check.

---

## STRIDE Findings

| ID | Cat | Affected Tool(s) | Attack Vector | Mitigation Applied | Residual Severity |
|----|-----|------------------|---------------|--------------------|-------------------|
| T-001 | Tampering | jira_release_notes | `version_name` / `project_key` injected into JQL string -> JQL injection (e.g. `" OR 1=1 ORDER BY`) | Double-quotes escaped (`replace('"','\\"')`) for both fields before JQL build; full query URL-encoded via `urllib.request.quote()` | 0 (resolved) |
| T-002 | Tampering | jira_get_epic | `epic_key` injected into JQL value (Cloud `"Epic Link"="<key>"` / Server `cf[10014]="<key>"`) | `epic_key` quote-escaped before JQL build; Server branch now also wraps value in quotes; query URL-encoded | 0 (resolved) |
| T-003 | Tampering / EoP | jira_get_epic, jira_link_to_epic, jira_release_version, jira_list_versions, jira_dependency_check | User-supplied path segment (`epic_key`, `issue_key`, `version_id`, `project_key`) concatenated into REST path -> path traversal (`../`) or endpoint pivot | All path segments URL-encoded with `urllib.request.quote(value, safe="")` so `/` and `.` are percent-encoded | 0 (resolved) |
| I-001 | Info Disclosure | all 11 tools | Jira API error could echo internal detail (URL, token) to caller | `_request()` raises `RuntimeError("Jira API error <code>: <detail>")` where `<detail>` is the Jira-returned errorMessages only -- never the Authorization header or token. `@mcp_tool_handler` returns `{"success": false, "error": <msg>}` with `include_traceback=False` (default) so no stack trace leaks | 0 (acceptable) |
| D-001 | DoS | jira_cross_team_health | Large `board_ids` list -> up to 7 Jira calls per board, unbounded fan-out | Hard cap: `len(board_ids) > 10` returns error before any API call | 0 (resolved) |
| D-002 | DoS | jira_program_velocity, jira_dependency_check | Large `board_ids` list -> many sequential calls | Empty-list guard returns error; calls are sequential (no thread amplification); board_ids supplied by trusted orchestrator. program_velocity additionally bounds `num_sprints` to 1-20 | 0 (acceptable) |
| S-001 | Spoofing | all 11 tools | MITM on Jira HTTPS calls | Out of scope for this layer -- TLS is enforced by Jira Cloud (https URL) and the urllib stack validates certs by default. No code change introduces plaintext HTTP | 0 (acceptable) |
| R-001 | Repudiation | jira_create_epic, jira_create_version, jira_release_version | Mutating calls not locally audit-logged | Jira itself records issue/version history with the authenticated account. Local audit logging is a non-goal for an MCP tool layer | 0 (acceptable) |
| E-001 | Elevation of Privilege | all 11 tools | Crafted key reaches a project the caller should not access | Authorization is enforced server-side by Jira against the API token's permission scope. The tool cannot exceed the token's granted privileges | 0 (acceptable) |

---

## Residual Threat Counts

```
CRITICAL : 0
HIGH     : 0
MEDIUM   : 0
LOW      : 0
INFO     : 0
```

All identified tampering vectors (T-001, T-002, T-003) were actively remediated in code
during F.1 (JQL quote-escaping + path-segment URL-encoding). Remaining items (S/R/I/D/E)
are accepted with documented rationale appropriate to a local stdio MCP server whose sole
network egress is an authenticated, TLS-protected Jira REST endpoint.

F.1_COMPLETE
