# F.2 Security Report -- SAST + Secrets + SCA
<!-- Author: devsecops_engineer | Date: 2026-05-29 | Phase: F.2 -->

## F.2.1 SAST (Static Analysis) -- new/modified code

| Check | Result | Evidence |
|-------|--------|----------|
| JQL injection (jira_release_notes) | PASS | `version_name` and `project_key` quote-escaped (server.py:3715-3716); full JQL URL-encoded via `urllib.request.quote()` |
| JQL injection (jira_get_epic) | PASS | `epic_key` quote-escaped (server.py:3466); Cloud + Server branches both quote the value |
| Path-segment injection | PASS | `epic_key`/`issue_key`/`version_id`/`project_key` encoded with `quote(value, safe="")` (server.py:3457, 3523, 3637, 3683, 3965) -- `/` and `.` percent-encoded |
| SSRF | PASS | All requests target `cfg["url"]` (env-derived) + hardcoded path templates; no user-controlled URL base |
| Hardcoded credentials | PASS | No `token=`/`password=`/`secret=`/`api_key=`/`bearer <literal>` in new code (lines 1290-3990) |
| Error message leakage | PASS | `_request()` error = `"Jira API error <code>: <Jira errorMessages>"`; Authorization header/token never included; `@mcp_tool_handler` default `include_traceback=False` |
| Integer validation (board_ids) | PASS | Empty-list guards in all 3 cross-board tools; `num_sprints` bounded 1-20; `len(board_ids) > 10` guard in cross_team_health |
| Input validation (string params) | PASS | All string params pass through `validate_input(field_name=...)` (null-byte strip, length cap) |

## F.2.2 Secrets Detection

| Check | Result | Evidence |
|-------|--------|----------|
| Hardcoded secrets in source | PASS | None found in new code |
| Real credentials in fixtures | PASS | 11 fixture files use only placeholders (`test.atlassian.net`, `test-token`); no real tokens/URLs |
| .env / config files committed | PASS | No new .env or config files added; `.env.example` pre-existing and placeholder-only |

## F.2.3 SCA (Software Composition Analysis)

| Check | Result | Evidence |
|-------|--------|----------|
| New pip dependencies added | PASS | None. New code uses stdlib `urllib.request`, `json`, `datetime` only |
| requirements.txt | UNCHANGED | `mcp==1.26.0`, `fastmcp==3.1.1` (both pinned) |
| requirements-dev.txt | UNCHANGED | `pytest>=7.0.0`, `pytest-cov>=4.0.0` |
| Known CVEs in deps | PASS | No transitive deps introduced by this change; existing pinned versions unmodified |
| License compliance | PASS | No new dependencies -> no new license obligations |

---

## Finding Counts

```
SAST Findings    : 0
Secrets Findings : 0
SCA Findings     : 0
```

F.2 STATUS: PASS
F.2_PASS
