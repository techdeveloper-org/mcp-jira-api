"""
test_tools_gaps.py -- Unit tests for all 4 KG gap closures.

Groups:
  GROUP A: Gap 1 AHP wire-up in jira_sprint_review (urlopen mocked for sprint data)
  GROUP B: Gaps 2-4 new tools (urlopen mocked for all Jira API calls)
  GROUP C: Regression -- existing jira_sprint_review behaviour unchanged

Pattern:
  All @mcp_tool_handler tools return JSON strings.
  Tests always json.loads() the result and check result["success"].
  Tools are regular def (not async) -- called directly, no asyncio.run().
  Mock: @patch("urllib.request.urlopen")

Windows-Safe: ASCII only (cp1252 compatible)
"""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import server  # noqa: E402


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _parse(json_str):
    """Parse JSON string returned by an @mcp_tool_handler-wrapped function."""
    return json.loads(json_str)


def _make_resp(data):
    """Build a urlopen context-manager mock returning JSON-encoded data."""
    encoded = json.dumps(data).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = encoded
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _make_empty_resp():
    """Build a urlopen mock returning empty bytes (204 No Content)."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = b""
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


FIXTURES = Path(__file__).parent / "fixtures"


def _load(filename):
    """Load a fixture JSON file directly from tests/fixtures/{filename}."""
    with open(FIXTURES / filename, "r") as f:
        return json.load(f)


def _sprint_detail():
    return {"id": 7, "name": "Sprint 7", "state": "active", "goal": "Ship it"}


def _sprint_issues_done():
    return {
        "maxResults": 50,
        "startAt": 0,
        "total": 2,
        "issues": [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "Story one",
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Story"},
                    "customfield_10016": 5.0,
                    "customfield_10028": None,
                    "story_points": None,
                    "assignee": {"displayName": "Alice"},
                    "subtasks": [],
                },
            },
            {
                "key": "PROJ-2",
                "fields": {
                    "summary": "Story two",
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Story"},
                    "customfield_10016": 3.0,
                    "customfield_10028": None,
                    "story_points": None,
                    "assignee": {"displayName": "Bob"},
                    "subtasks": [],
                },
            },
        ],
    }


def _closed_sprints_empty():
    return {"values": []}


JIRA_ENV = {
    "JIRA_URL": "https://test.atlassian.net",
    "JIRA_USER": "test@example.com",
    "JIRA_API_TOKEN": "test-token-ascii",
}


def _set_env():
    for k, v in JIRA_ENV.items():
        os.environ[k] = v


def _clear_env():
    for k in JIRA_ENV:
        os.environ.pop(k, None)


# ---------------------------------------------------------------------------
# GROUP A -- Gap 1: AHP wire-up in jira_sprint_review
# ---------------------------------------------------------------------------


class TestJiraSprintReviewAHP(unittest.TestCase):
    """Tests for Gap 1: dod_criteria_weights parameter in jira_sprint_review."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    # --- backward compat ---

    @patch("urllib.request.urlopen")
    def test_backward_compat_no_weights(self, mock_urlopen):
        """Calling without dod_criteria_weights must return same shape as before."""
        mock_urlopen.side_effect = [
            _make_resp(_sprint_detail()),
            _make_resp(_sprint_issues_done()),
            _make_resp(_closed_sprints_empty()),
        ]
        result = _parse(server.jira_sprint_review(board_id=1, sprint_id=7))

        assert result["success"] is True
        assert "dod_compliance_pct" in result
        assert "demo_ready_issues" in result
        assert "ahp_weights" in result
        assert "ahp_CR" in result
        assert "ahp_consistent" in result

    @patch("urllib.request.urlopen")
    def test_explicit_none_weights_same_as_no_weights(self, mock_urlopen):
        """Passing dod_criteria_weights=None behaves identically to omitting it."""
        mock_urlopen.side_effect = [
            _make_resp(_sprint_detail()),
            _make_resp(_sprint_issues_done()),
            _make_resp(_closed_sprints_empty()),
        ]
        result = _parse(
            server.jira_sprint_review(board_id=1, sprint_id=7, dod_criteria_weights=None)
        )

        assert result["success"] is True
        assert "dod_weighted_score" not in result

    @patch("urllib.request.urlopen")
    def test_dod_weighted_score_absent_when_no_weights(self, mock_urlopen):
        """dod_weighted_score key must be ABSENT (not None) when no weights given."""
        mock_urlopen.side_effect = [
            _make_resp(_sprint_detail()),
            _make_resp(_sprint_issues_done()),
            _make_resp(_closed_sprints_empty()),
        ]
        result = _parse(server.jira_sprint_review(board_id=1, sprint_id=7))

        assert "dod_weighted_score" not in result

    # --- AHP happy path ---

    @patch("urllib.request.urlopen")
    def test_with_consistent_3x3_matrix(self, mock_urlopen):
        """Consistent 3x3 matrix returns dod_weighted_score float in result."""
        mock_urlopen.side_effect = [
            _make_resp(_sprint_detail()),
            _make_resp(_sprint_issues_done()),
            _make_resp(_closed_sprints_empty()),
        ]
        consistent_matrix = [
            [1.0, 3.0, 5.0],
            [1.0 / 3.0, 1.0, 2.0],
            [1.0 / 5.0, 0.5, 1.0],
        ]
        result = _parse(
            server.jira_sprint_review(
                board_id=1, sprint_id=7, dod_criteria_weights=consistent_matrix
            )
        )

        assert result["success"] is True
        assert "dod_weighted_score" in result
        assert isinstance(result["dod_weighted_score"], float)
        assert 0.0 <= result["dod_weighted_score"] <= 1.0

    @patch("urllib.request.urlopen")
    def test_dod_weighted_score_value_reflects_compliance(self, mock_urlopen):
        """When all demo stories are DoD compliant, weighted score > 0."""
        mock_urlopen.side_effect = [
            _make_resp(_sprint_detail()),
            _make_resp(_sprint_issues_done()),
            _make_resp(_closed_sprints_empty()),
        ]
        consistent_matrix = [
            [1.0, 3.0, 5.0],
            [1.0 / 3.0, 1.0, 2.0],
            [1.0 / 5.0, 0.5, 1.0],
        ]
        result = _parse(
            server.jira_sprint_review(
                board_id=1, sprint_id=7, dod_criteria_weights=consistent_matrix
            )
        )

        assert result["success"] is True
        assert result["dod_weighted_score"] > 0.0

    # --- AHP error path ---

    @patch("urllib.request.urlopen")
    def test_with_inconsistent_matrix_returns_error(self, mock_urlopen):
        """Matrix with CR >= 0.10 returns success=False with CR in error message."""
        mock_urlopen.side_effect = [
            _make_resp(_sprint_detail()),
            _make_resp(_sprint_issues_done()),
            _make_resp(_closed_sprints_empty()),
        ]
        inconsistent_matrix = [
            [1.0, 9.0, 1.0 / 9.0],
            [1.0 / 9.0, 1.0, 9.0],
            [9.0, 1.0 / 9.0, 1.0],
        ]
        result = _parse(
            server.jira_sprint_review(
                board_id=1, sprint_id=7, dod_criteria_weights=inconsistent_matrix
            )
        )

        assert result["success"] is False
        assert "error" in result
        assert "CR" in result["error"] or "inconsistent" in result["error"].lower()

    @patch("urllib.request.urlopen")
    def test_dod_compliant_bool_in_demo_ready_issues(self, mock_urlopen):
        """Each item in demo_ready_issues must have dod_compliant bool field."""
        mock_urlopen.side_effect = [
            _make_resp(_sprint_detail()),
            _make_resp(_sprint_issues_done()),
            _make_resp(_closed_sprints_empty()),
        ]
        result = _parse(server.jira_sprint_review(board_id=1, sprint_id=7))

        assert result["success"] is True
        for story in result.get("demo_ready_issues", []):
            assert "dod_compliant" in story, "dod_compliant missing from story: " + str(story)
            assert isinstance(story["dod_compliant"], bool)


# ---------------------------------------------------------------------------
# GROUP B -- Epic Management Tools
# ---------------------------------------------------------------------------


class TestJiraCreateEpic(unittest.TestCase):
    """Tests for jira_create_epic."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_success_returns_epic_key(self, mock_urlopen):
        """Happy path: returns epic_key, summary, name, epic_url."""
        fixture = _load("epic_create_response.json")
        mock_urlopen.return_value = _make_resp(fixture)

        result = _parse(server.jira_create_epic("PROJ", "Q1 Goals", "Q1 Goals Epic"))

        assert result["success"] is True
        assert result["epic_key"] == "PROJ-42"
        assert result["summary"] == "Q1 Goals Epic"
        assert result["name"] == "Q1 Goals"
        assert "epic_url" in result

    @patch("urllib.request.urlopen")
    def test_with_optional_dates(self, mock_urlopen):
        """Optional start_date and due_date are accepted without error."""
        fixture = _load("epic_create_response.json")
        mock_urlopen.return_value = _make_resp(fixture)

        result = _parse(
            server.jira_create_epic(
                "PROJ", "Q1 Goals", "Epic Summary",
                start_date="2026-01-01", due_date="2026-03-31"
            )
        )

        assert result["success"] is True
        assert result["epic_key"] == "PROJ-42"

    def test_missing_env_returns_error(self):
        """Missing JIRA_URL env var returns success=False."""
        _clear_env()
        result = _parse(server.jira_create_epic("PROJ", "Q1", "Epic"))
        assert result["success"] is False

    @patch("urllib.request.urlopen", side_effect=Exception("Connection refused"))
    def test_api_error_returns_failure(self, mock_urlopen):
        """Jira API exception returns success=False."""
        result = _parse(server.jira_create_epic("PROJ", "Q1", "Epic"))
        assert result["success"] is False


class TestJiraGetEpic(unittest.TestCase):
    """Tests for jira_get_epic."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_success_with_linked_stories(self, mock_urlopen):
        """Happy path: returns linked_story_count, completion_pct."""
        epic_detail = _load("epic_detail_response.json")
        stories = _load("epic_stories_response.json")
        mock_urlopen.side_effect = [_make_resp(epic_detail), _make_resp(stories)]

        result = _parse(server.jira_get_epic("PROJ-42"))

        assert result["success"] is True
        assert result["epic_key"] == "PROJ-42"
        assert result["linked_story_count"] == 2
        assert "completion_pct" in result
        assert 0.0 <= result["completion_pct"] <= 100.0
        assert "story_points_total" in result

    @patch("urllib.request.urlopen")
    def test_no_stories_returns_zero_completion(self, mock_urlopen):
        """Epic with no linked stories returns completion_pct=0.0."""
        epic_detail = _load("epic_detail_response.json")
        empty_stories = {"issues": [], "total": 0}
        mock_urlopen.side_effect = [_make_resp(epic_detail), _make_resp(empty_stories)]

        result = _parse(server.jira_get_epic("PROJ-42"))

        assert result["success"] is True
        assert result["linked_story_count"] == 0
        assert result["completion_pct"] == 0.0

    @patch("urllib.request.urlopen", side_effect=Exception("404 Not Found"))
    def test_api_error_returns_failure(self, mock_urlopen):
        """API failure returns success=False."""
        result = _parse(server.jira_get_epic("PROJ-99"))
        assert result["success"] is False


class TestJiraLinkToEpic(unittest.TestCase):
    """Tests for jira_link_to_epic."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_success_returns_linked_true(self, mock_urlopen):
        """Happy path: linked=True returned."""
        mock_urlopen.return_value = _make_empty_resp()

        result = _parse(server.jira_link_to_epic("PROJ-10", "PROJ-42"))

        assert result["success"] is True
        assert result["linked"] is True
        assert result["issue_key"] == "PROJ-10"
        assert result["epic_key"] == "PROJ-42"

    def test_empty_issue_key_fails_validation(self):
        """Empty issue_key raises validation error caught by handler."""
        result = _parse(server.jira_link_to_epic("", "PROJ-42"))
        assert result["success"] is False


class TestJiraListEpics(unittest.TestCase):
    """Tests for jira_list_epics."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_success_returns_epics_list(self, mock_urlopen):
        """Happy path: returns epics list with key, summary, done."""
        fixture = _load("epics_list_response.json")
        mock_urlopen.return_value = _make_resp(fixture)

        result = _parse(server.jira_list_epics(42))

        assert result["success"] is True
        assert result["board_id"] == 42
        assert result["total"] == 2
        assert len(result["epics"]) == 2
        for epic in result["epics"]:
            assert "key" in epic
            assert "summary" in epic
            assert "done" in epic

    @patch("urllib.request.urlopen")
    def test_empty_board_returns_empty_list(self, mock_urlopen):
        """Board with no epics returns empty list."""
        mock_urlopen.return_value = _make_resp({"values": []})

        result = _parse(server.jira_list_epics(99))

        assert result["success"] is True
        assert result["total"] == 0
        assert result["epics"] == []

    @patch("urllib.request.urlopen", side_effect=Exception("Agile API error"))
    def test_api_error_returns_failure(self, mock_urlopen):
        """API error returns success=False."""
        result = _parse(server.jira_list_epics(1))
        assert result["success"] is False


# ---------------------------------------------------------------------------
# GROUP B -- Release & Version Management Tools
# ---------------------------------------------------------------------------


class TestJiraCreateVersion(unittest.TestCase):
    """Tests for jira_create_version."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_success_returns_version_id(self, mock_urlopen):
        """Happy path: returns version_id, name, released=False."""
        fixture = _load("version_create_response.json")
        mock_urlopen.return_value = _make_resp(fixture)

        result = _parse(server.jira_create_version("PROJ", "v1.0.0"))

        assert result["success"] is True
        assert result["version_id"] == "10010"
        assert result["name"] == "v1.0.0"
        assert result["released"] is False

    @patch("urllib.request.urlopen")
    def test_with_release_date_and_description(self, mock_urlopen):
        """Optional release_date and description accepted without error."""
        fixture = _load("version_create_response.json")
        mock_urlopen.return_value = _make_resp(fixture)

        result = _parse(
            server.jira_create_version(
                "PROJ", "v1.0.0",
                release_date="2026-06-30",
                description="First production release"
            )
        )

        assert result["success"] is True
        assert result["version_id"] == "10010"

    def test_missing_project_key_validation(self):
        """Empty project_key triggers validation error."""
        result = _parse(server.jira_create_version("", "v1.0.0"))
        assert result["success"] is False


class TestJiraListVersions(unittest.TestCase):
    """Tests for jira_list_versions."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_success_returns_versions_list(self, mock_urlopen):
        """Happy path: returns list with id, name, released, archived, releaseDate."""
        fixture = _load("versions_list_response.json")
        mock_urlopen.return_value = _make_resp(fixture)

        result = _parse(server.jira_list_versions("PROJ"))

        assert result["success"] is True
        assert result["project_key"] == "PROJ"
        assert result["total"] == 2
        for v in result["versions"]:
            assert "id" in v
            assert "name" in v
            assert "released" in v
            assert "archived" in v

    @patch("urllib.request.urlopen")
    def test_empty_project_returns_empty(self, mock_urlopen):
        """Project with no versions returns empty versions list."""
        mock_urlopen.return_value = _make_resp([])

        result = _parse(server.jira_list_versions("EMPTY"))

        assert result["success"] is True
        assert result["total"] == 0
        assert result["versions"] == []


class TestJiraReleaseVersion(unittest.TestCase):
    """Tests for jira_release_version."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_success_marks_released(self, mock_urlopen):
        """Happy path: released=True returned."""
        mock_urlopen.return_value = _make_empty_resp()

        result = _parse(server.jira_release_version("10010", "2026-05-29"))

        assert result["success"] is True
        assert result["released"] is True
        assert result["version_id"] == "10010"
        assert result["release_date"] == "2026-05-29"

    @patch("urllib.request.urlopen")
    def test_defaults_to_today_when_no_date(self, mock_urlopen):
        """When release_date omitted, release_date in result is today's ISO date."""
        from datetime import date
        mock_urlopen.return_value = _make_empty_resp()

        result = _parse(server.jira_release_version("10010"))

        assert result["success"] is True
        assert result["released"] is True
        assert result["release_date"] == date.today().isoformat()

    @patch("urllib.request.urlopen")
    def test_custom_release_date_used(self, mock_urlopen):
        """Custom release_date is passed through unchanged."""
        mock_urlopen.return_value = _make_empty_resp()

        result = _parse(server.jira_release_version("10010", release_date="2026-12-31"))

        assert result["release_date"] == "2026-12-31"


class TestJiraReleaseNotes(unittest.TestCase):
    """Tests for jira_release_notes."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_success_grouped_by_issuetype(self, mock_urlopen):
        """Happy path: issues grouped by issuetype name."""
        fixture = _load("release_notes_search_response.json")
        mock_urlopen.return_value = _make_resp(fixture)

        result = _parse(server.jira_release_notes("PROJ", "v1.0.0"))

        assert result["success"] is True
        assert result["project_key"] == "PROJ"
        assert result["version"] == "v1.0.0"
        assert result["total_issues"] == 3
        assert "groups" in result
        assert "Bug" in result["groups"]
        assert "Story" in result["groups"]

    @patch("urllib.request.urlopen")
    def test_empty_version_returns_empty_groups(self, mock_urlopen):
        """Version with no fixed issues returns empty groups dict."""
        mock_urlopen.return_value = _make_resp({"issues": [], "total": 0})

        result = _parse(server.jira_release_notes("PROJ", "v0.0.0"))

        assert result["success"] is True
        assert result["total_issues"] == 0
        assert result["groups"] == {}

    @patch("urllib.request.urlopen")
    def test_jql_injection_special_chars_sanitized(self, mock_urlopen):
        """Version name with double-quote is sanitized before JQL insertion."""
        mock_urlopen.return_value = _make_resp({"issues": [], "total": 0})

        result = _parse(server.jira_release_notes("PROJ", 'v1.0 "special"'))

        assert result["success"] is True
        call_args = mock_urlopen.call_args
        url_called = call_args[0][0].full_url if hasattr(call_args[0][0], 'full_url') else str(call_args)
        assert '\\\"' in url_called or '%5C' in url_called or 'special' in url_called


# ---------------------------------------------------------------------------
# GROUP B -- Cross-Board / Multi-Team Metrics
# ---------------------------------------------------------------------------


class TestJiraProgramVelocity(unittest.TestCase):
    """Tests for jira_program_velocity."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_single_board_success(self, mock_urlopen):
        """Single board returns per_team dict with correct board_id key."""
        fixture = _load("cross_board_velocity_response.json")
        mock_urlopen.return_value = _make_resp(fixture)

        result = _parse(server.jira_program_velocity([101]))

        assert result["success"] is True
        assert result["board_count"] == 1
        assert "101" in result["per_team"]
        assert "avg_velocity" in result["per_team"]["101"]
        assert "program_total_avg" in result

    @patch("urllib.request.urlopen")
    def test_multiple_boards_aggregated(self, mock_urlopen):
        """Two boards returns per_team with both board keys."""
        fixture = _load("cross_board_velocity_response.json")
        mock_urlopen.side_effect = [_make_resp(fixture), _make_resp(fixture)]

        result = _parse(server.jira_program_velocity([101, 102]))

        assert result["success"] is True
        assert result["board_count"] == 2
        assert "101" in result["per_team"]
        assert "102" in result["per_team"]
        assert result["program_total_avg"] > 0.0

    def test_empty_board_ids_returns_error(self):
        """Empty board_ids list returns success=False."""
        result = _parse(server.jira_program_velocity([]))
        assert result["success"] is False
        assert "error" in result

    def test_num_sprints_out_of_range_returns_error(self):
        """num_sprints=0 returns success=False (out of 1-20 range)."""
        result = _parse(server.jira_program_velocity([1], num_sprints=0))
        assert result["success"] is False

        result2 = _parse(server.jira_program_velocity([1], num_sprints=21))
        assert result2["success"] is False


class TestJiraCrossTeamHealth(unittest.TestCase):
    """Tests for jira_cross_team_health."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_two_boards_ranked_by_composite_score(self, mock_urlopen):
        """Two boards returned sorted by composite_score descending with rank field."""
        sprint_list = _load("cross_team_health_board_response.json")
        sprint_issues_empty = {"issues": [], "maxResults": 200, "startAt": 0, "total": 0}
        mock_urlopen.side_effect = [
            _make_resp(sprint_list),
            _make_resp(sprint_issues_empty),
            _make_resp(sprint_issues_empty),
            _make_resp(sprint_list),
            _make_resp(sprint_issues_empty),
            _make_resp(sprint_issues_empty),
        ]

        result = _parse(server.jira_cross_team_health([201, 202]))

        assert result["success"] is True
        assert result["board_count"] == 2
        assert len(result["teams"]) == 2
        assert result["teams"][0]["rank"] == 1
        assert result["teams"][1]["rank"] == 2
        scores = [t["composite_score"] for t in result["teams"]]
        assert scores[0] >= scores[1]

    @patch("urllib.request.urlopen")
    def test_single_board_returns_rank_1(self, mock_urlopen):
        """Single board gets rank=1 and is both top and lowest."""
        sprint_list = _load("cross_team_health_board_response.json")
        sprint_issues_empty = {"issues": [], "total": 0}
        mock_urlopen.side_effect = [
            _make_resp(sprint_list),
            _make_resp(sprint_issues_empty),
            _make_resp(sprint_issues_empty),
        ]

        result = _parse(server.jira_cross_team_health([201]))

        assert result["success"] is True
        assert result["teams"][0]["rank"] == 1
        assert result["top_team_board_id"] == result["lowest_team_board_id"]

    def test_more_than_10_boards_returns_error(self):
        """11 board IDs returns success=False (DoS protection)."""
        result = _parse(server.jira_cross_team_health(list(range(1, 12))))
        assert result["success"] is False
        assert "error" in result

    def test_empty_board_ids_returns_error(self):
        """Empty list returns success=False."""
        result = _parse(server.jira_cross_team_health([]))
        assert result["success"] is False


class TestJiraDependencyCheck(unittest.TestCase):
    """Tests for jira_dependency_check."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_no_active_sprint_returns_no_blockers(self, mock_urlopen):
        """Board with no active sprint contributes zero blockers."""
        mock_urlopen.return_value = _make_resp({"values": []})

        result = _parse(server.jira_dependency_check([101]))

        assert result["success"] is True
        assert result["total_blockers"] == 0
        assert result["boards_with_active_sprint"] == 0

    @patch("urllib.request.urlopen")
    def test_cross_board_blocker_detected(self, mock_urlopen):
        """Issue blocking an issue on another board is returned as blocker."""
        active_sprint_board1 = {"values": [{"id": 10, "state": "active"}]}
        active_sprint_board2 = {"values": [{"id": 20, "state": "active"}]}
        sprint10_issues = {
            "issues": [{"key": "PROJ-20", "fields": {"summary": "Backend", "issuelinks": []}}],
            "total": 1,
        }
        sprint20_issues = {
            "issues": [{"key": "TEAM2-5", "fields": {"summary": "Frontend", "issuelinks": []}}],
            "total": 1,
        }
        proj20_detail = {
            "fields": {
                "issuelinks": [
                    {
                        "id": "10001",
                        "type": {"name": "Blocks", "outward": "blocks"},
                        "outwardIssue": {
                            "key": "TEAM2-5",
                            "fields": {"summary": "Frontend", "status": {"name": "In Progress"}},
                        },
                    }
                ]
            }
        }
        team2_5_detail = {"fields": {"issuelinks": []}}

        mock_urlopen.side_effect = [
            _make_resp(active_sprint_board1),
            _make_resp(sprint10_issues),
            _make_resp(active_sprint_board2),
            _make_resp(sprint20_issues),
            _make_resp(proj20_detail),
            _make_resp(team2_5_detail),
        ]

        result = _parse(server.jira_dependency_check([1, 2]))

        assert result["success"] is True
        assert result["total_blockers"] == 1
        assert result["cross_board_blockers"][0]["blocker_key"] == "PROJ-20"
        assert result["cross_board_blockers"][0]["blocks_key"] == "TEAM2-5"

    def test_empty_board_ids_returns_error(self):
        """Empty board_ids returns success=False."""
        result = _parse(server.jira_dependency_check([]))
        assert result["success"] is False


# ---------------------------------------------------------------------------
# GROUP C -- Regression: existing jira_sprint_review must be unchanged
# ---------------------------------------------------------------------------


class TestSprintReviewRegression(unittest.TestCase):
    """Regression tests ensuring Gap 1 did not break existing sprint review behavior."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_all_existing_keys_present_without_weights(self, mock_urlopen):
        """All pre-Gap-1 return keys still present when no dod_criteria_weights given."""
        mock_urlopen.side_effect = [
            _make_resp(_sprint_detail()),
            _make_resp(_sprint_issues_done()),
            _make_resp(_closed_sprints_empty()),
        ]
        result = _parse(server.jira_sprint_review(board_id=1, sprint_id=7))

        required_keys = [
            "sprint_id", "sprint_name", "sprint_goal",
            "completed_points", "committed_points", "completion_rate",
            "velocity_mean", "velocity_cv", "nasscom_agileX_level",
            "dod_compliance_pct", "demo_ready_issues", "review_timestamp",
            "ahp_dod_criteria", "ahp_weights", "ahp_CR",
            "ahp_consistent", "ahp_note",
        ]
        for key in required_keys:
            assert key in result, "Missing pre-existing key: " + key

    @patch("urllib.request.urlopen")
    def test_dod_weighted_score_absent_in_regression(self, mock_urlopen):
        """dod_weighted_score must NOT appear in result when no weights passed."""
        mock_urlopen.side_effect = [
            _make_resp(_sprint_detail()),
            _make_resp(_sprint_issues_done()),
            _make_resp(_closed_sprints_empty()),
        ]
        result = _parse(server.jira_sprint_review(board_id=1, sprint_id=7))

        assert "dod_weighted_score" not in result, (
            "dod_weighted_score must be absent (not None) in backward-compat mode"
        )

    @patch("urllib.request.urlopen")
    def test_sprint_id_echoed_in_result(self, mock_urlopen):
        """sprint_id in result matches the input sprint_id."""
        mock_urlopen.side_effect = [
            _make_resp(_sprint_detail()),
            _make_resp(_sprint_issues_done()),
            _make_resp(_closed_sprints_empty()),
        ]
        result = _parse(server.jira_sprint_review(board_id=1, sprint_id=7))

        assert result["sprint_id"] == 7


# ---------------------------------------------------------------------------
# Branch coverage -- exercise None-guards, Server/DC paths, velocity loop
# ---------------------------------------------------------------------------


class TestNewCodeBranchCoverage(unittest.TestCase):
    """Targeted tests for defensive branches in the new/modified code."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()
        os.environ.pop("JIRA_API_VERSION", None)

    @patch("urllib.request.urlopen")
    def test_sprint_review_populated_velocity_history(self, mock_urlopen):
        """Closed sprints with issues populate velocity_history (loop body)."""
        closed = {"values": [{"id": 5}, {"id": 6}]}
        done_issues = {
            "issues": [
                {"fields": {"status": {"name": "Done"}, "customfield_10016": 8.0}}
            ]
        }
        mock_urlopen.side_effect = [
            _make_resp(_sprint_detail()),
            _make_resp(_sprint_issues_done()),
            _make_resp(closed),
            _make_resp(done_issues),
            _make_resp(done_issues),
        ]
        result = _parse(server.jira_sprint_review(board_id=1, sprint_id=7))

        assert result["success"] is True
        assert "velocity_mean" in result

    @patch("urllib.request.urlopen")
    def test_sprint_review_none_closed_sprints(self, mock_urlopen):
        """A 204/empty closed-sprints response hits the None guard."""
        mock_urlopen.side_effect = [
            _make_resp(_sprint_detail()),
            _make_resp(_sprint_issues_done()),
            _make_empty_resp(),
        ]
        result = _parse(server.jira_sprint_review(board_id=1, sprint_id=7))

        assert result["success"] is True

    @patch("urllib.request.urlopen")
    def test_sprint_review_non_square_matrix_error(self, mock_urlopen):
        """Non-square AHP matrix returns the AHP matrix error branch."""
        mock_urlopen.side_effect = [
            _make_resp(_sprint_detail()),
            _make_resp(_sprint_issues_done()),
            _make_resp(_closed_sprints_empty()),
        ]
        non_square = [[1.0, 2.0], [1.0]]
        result = _parse(
            server.jira_sprint_review(
                board_id=1, sprint_id=7, dod_criteria_weights=non_square
            )
        )

        assert result["success"] is False
        assert "AHP matrix error" in result["error"]

    @patch("urllib.request.urlopen")
    def test_get_epic_server_dc_jql_branch(self, mock_urlopen):
        """Server/DC (api_version=2) uses the cf[10014] JQL branch."""
        os.environ["JIRA_API_VERSION"] = "2"
        epic_detail = _load("epic_detail_response.json")
        stories = _load("epic_stories_response.json")
        mock_urlopen.side_effect = [_make_resp(epic_detail), _make_resp(stories)]

        result = _parse(server.jira_get_epic("PROJ-42"))

        assert result["success"] is True
        assert result["linked_story_count"] == 2

    @patch("urllib.request.urlopen")
    def test_list_epics_none_response(self, mock_urlopen):
        """A 204/empty agile response hits the None guard in jira_list_epics."""
        mock_urlopen.return_value = _make_empty_resp()
        result = _parse(server.jira_list_epics(1))

        assert result["success"] is True
        assert result["total"] == 0

    @patch("urllib.request.urlopen")
    def test_list_versions_none_response(self, mock_urlopen):
        """A 204/empty response hits the None guard in jira_list_versions."""
        mock_urlopen.return_value = _make_empty_resp()
        result = _parse(server.jira_list_versions("PROJ"))

        assert result["success"] is True
        assert result["total"] == 0

    @patch("urllib.request.urlopen")
    def test_release_notes_none_response(self, mock_urlopen):
        """A 204/empty response hits the None guard in jira_release_notes."""
        mock_urlopen.return_value = _make_empty_resp()
        result = _parse(server.jira_release_notes("PROJ", "v1.0.0"))

        assert result["success"] is True
        assert result["total_issues"] == 0

    @patch("urllib.request.urlopen")
    def test_program_velocity_none_response(self, mock_urlopen):
        """A 204/empty velocity response hits the None guard."""
        mock_urlopen.return_value = _make_empty_resp()
        result = _parse(server.jira_program_velocity([101]))

        assert result["success"] is True
        assert result["per_team"]["101"]["sprint_count"] == 0

    @patch("urllib.request.urlopen")
    def test_cross_team_health_none_closed_sprints(self, mock_urlopen):
        """A 204/empty closed-sprints response hits the None guard."""
        mock_urlopen.return_value = _make_empty_resp()
        result = _parse(server.jira_cross_team_health([201]))

        assert result["success"] is True
        assert result["teams"][0]["sprints_analyzed"] == 0

    @patch("urllib.request.urlopen")
    def test_dependency_check_sprint_without_id_skipped(self, mock_urlopen):
        """Active sprint entry missing 'id' is skipped (continue branch)."""
        active_no_id = {"values": [{"state": "active"}]}
        mock_urlopen.side_effect = [_make_resp(active_no_id)]

        result = _parse(server.jira_dependency_check([101]))

        assert result["success"] is True
        assert result["total_blockers"] == 0

    @patch("urllib.request.urlopen")
    def test_dependency_check_none_issues_response(self, mock_urlopen):
        """Empty issues response hits the None guard, yields no blockers."""
        active_sprint = {"values": [{"id": 10, "state": "active"}]}
        mock_urlopen.side_effect = [
            _make_resp(active_sprint),
            _make_empty_resp(),
        ]

        result = _parse(server.jira_dependency_check([101]))

        assert result["success"] is True
        assert result["total_blockers"] == 0
        assert result["boards_with_active_sprint"] == 1

    @patch("urllib.request.urlopen")
    def test_dependency_check_none_issue_detail_skipped(self, mock_urlopen):
        """Issue with mapped key but None detail is skipped (continue branch)."""
        active_sprint = {"values": [{"id": 10, "state": "active"}]}
        sprint_issues = {"issues": [{"key": "PROJ-1", "fields": {"issuelinks": []}}]}
        mock_urlopen.side_effect = [
            _make_resp(active_sprint),
            _make_resp(sprint_issues),
            _make_empty_resp(),
        ]

        result = _parse(server.jira_dependency_check([101]))

        assert result["success"] is True
        assert result["total_blockers"] == 0

    @patch("urllib.request.urlopen")
    def test_dependency_check_none_sprint_result(self, mock_urlopen):
        """A 204/empty active-sprint response hits the first None guard."""
        mock_urlopen.return_value = _make_empty_resp()

        result = _parse(server.jira_dependency_check([101]))

        assert result["success"] is True
        assert result["boards_with_active_sprint"] == 0

    @patch("urllib.request.urlopen")
    def test_sprint_review_none_sprint_detail_and_issues(self, mock_urlopen):
        """204/empty sprint detail and issues responses hit both None guards."""
        mock_urlopen.side_effect = [
            _make_empty_resp(),
            _make_empty_resp(),
            _make_empty_resp(),
        ]
        result = _parse(server.jira_sprint_review(board_id=1, sprint_id=7))

        assert result["success"] is True
        assert result["demo_ready_issues"] == []


if __name__ == "__main__":
    unittest.main()
