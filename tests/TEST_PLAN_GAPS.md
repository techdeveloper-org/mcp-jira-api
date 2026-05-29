# IEEE 829 Test Plan -- mcp-jira-api Gap Closure
<!-- Author: test_management_agent | Date: 2026-05-29 | Phase: D.1 -->

## 1. Test Scope

All 11 new/modified functions introduced by the 4-gap closure:

| Function | Gap | Change Type |
|----------|-----|-------------|
| jira_sprint_review | 1 | Modified (new optional param + AHP wire-up) |
| jira_create_epic | 2 | New |
| jira_get_epic | 2 | New |
| jira_link_to_epic | 2 | New |
| jira_list_epics | 2 | New |
| jira_create_version | 3 | New |
| jira_list_versions | 3 | New |
| jira_release_version | 3 | New |
| jira_release_notes | 3 | New |
| jira_program_velocity | 4 | New |
| jira_cross_team_health | 4 | New |
| jira_dependency_check | 4 | New |

## 2. Test Approach

All tool functions are wrapped with @mcp_tool_handler which:
- Returns a JSON string (not a dict)
- Catches ALL exceptions and returns {"success": False, "error": "..."} JSON
- Never re-raises to the caller

Test invocation pattern (ALL tests must follow this):
```python
result = json.loads(server.jira_xxx(...))
assert result["success"] is True  # or False
```

Jira API calls mocked via: @patch("urllib.request.urlopen")
Mock response builder: _make_urlopen_response(data) -- returns context manager mock

## 3. Pass Criteria

- 100% line coverage on all new code in server.py (pytest --cov-fail-under=100)
- DRE = 1.0 (all tests pass on first run after fixes)
- All test files ASCII-only

## 4. Risk Matrix

| Tool | Risk | Critical Scenarios |
|------|------|--------------------|
| jira_sprint_review+AHP | HIGH | inconsistent matrix CR>=0.10, None default backward compat, dod_compliant bool tracking |
| jira_create_epic | MEDIUM | Cloud ADF not needed (name field only), validate_input on all string params |
| jira_get_epic | MEDIUM | JQL differs Cloud vs Server, 0 stories edge case |
| jira_link_to_epic | LOW | Simple PUT, validate_input |
| jira_list_epics | LOW | None response from agile_client, empty values list |
| jira_create_version | LOW | Optional fields skipped when None |
| jira_list_versions | LOW | list vs dict response type |
| jira_release_version | MEDIUM | today date fallback, PUT returns None (204) |
| jira_release_notes | HIGH | JQL injection via version_name, grouping logic |
| jira_program_velocity | HIGH | empty board_ids, num_sprints range, multi-board agg |
| jira_cross_team_health | HIGH | ranking logic, >10 boards guard |
| jira_dependency_check | MEDIUM | no active sprint, cross-board detection accuracy |

## 5. Test Group Structure

```
tests/test_tools_gaps.py
  GROUP A -- Gap 1 AHP (no urlopen mock for AHP path; urlopen mocked for sprint data)
    TestJiraSprintReviewAHP
      test_backward_compat_no_weights
      test_with_consistent_3x3_matrix
      test_with_inconsistent_matrix_cr_error
      test_explicit_none_weights_same_as_no_weights
      test_dod_weighted_score_absent_when_no_weights
      test_dod_compliant_bool_in_demo_ready_issues

  GROUP B -- Epic Tools
    TestJiraCreateEpic
      test_success_returns_epic_key
      test_with_optional_dates
      test_missing_env_returns_error
      test_api_error_returns_failure

    TestJiraGetEpic
      test_success_with_linked_stories
      test_no_stories_returns_zero_completion
      test_api_error_returns_failure

    TestJiraLinkToEpic
      test_success_returns_linked_true
      test_empty_issue_key_fails_validation

    TestJiraListEpics
      test_success_returns_epics_list
      test_empty_board_returns_empty_list
      test_api_error_returns_failure

  GROUP B -- Version Tools
    TestJiraCreateVersion
      test_success_returns_version_id
      test_with_release_date_and_description
      test_missing_project_key_validation

    TestJiraListVersions
      test_success_returns_versions_list
      test_empty_project_returns_empty

    TestJiraReleaseVersion
      test_success_marks_released
      test_defaults_to_today_when_no_date
      test_custom_release_date_used

    TestJiraReleaseNotes
      test_success_grouped_by_issuetype
      test_empty_version_returns_empty_groups
      test_jql_injection_special_chars_sanitized

  GROUP B -- Cross-Board Tools
    TestJiraProgramVelocity
      test_single_board_success
      test_multiple_boards_aggregated
      test_empty_board_ids_returns_error
      test_num_sprints_out_of_range_returns_error

    TestJiraCrossTeamHealth
      test_two_boards_ranked_by_composite_score
      test_single_board_returns_rank_1
      test_more_than_10_boards_returns_error

    TestJiraDependencyCheck
      test_no_active_sprint_returns_no_blockers
      test_cross_board_blocker_detected
      test_empty_board_ids_returns_error

  GROUP C -- Regression
    TestSprintReviewRegression
      test_all_existing_keys_present_without_weights
      test_dod_weighted_score_absent_in_regression
```

## 6. Required Test File: tests/test_tools_gaps.py

See execution_plan.md TODO-10 for full implementation.
All tests ASCII-only. setUp sets JIRA_URL, JIRA_USER, JIRA_API_TOKEN env vars.
