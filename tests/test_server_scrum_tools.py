"""
test_server_scrum_tools.py -- Unit tests for the 15 Scrum Master tools in server.py.

IMPORTANT: All server tool functions are wrapped with @mcp_tool_handler which:
  - Returns a JSON string (not a dict)
  - Catches ALL exceptions and returns {"success": False, "error": ...} JSON
  - Never re-raises exceptions to the caller

Tests must json.loads() the result and inspect "success"/"error" fields.
For env-var tests we check that success==False and error mentions the missing var.

All HTTP calls are mocked via unittest.mock.patch('urllib.request.urlopen')
per CONTRACT #4. Uses jira_env fixture from conftest.py.

Tools covered (15):
  Group A (infrastructure): jira_get_boards, jira_get_sprints, jira_create_sprint,
                             jira_start_sprint, jira_close_sprint
  Group B (ceremonies):     jira_plan_sprint, jira_daily_standup, jira_sprint_review,
                             jira_retrospective, jira_refine_backlog
  Group C (analytics):      jira_get_velocity, jira_get_sprint_metrics,
                             jira_track_impediments, jira_team_health,
                             jira_monte_carlo_forecast

Windows-Safe: ASCII only (cp1252 compatible)
"""

import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.conftest import fixture_loader


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _parse(json_str):
    """Parse a JSON string returned by an @mcp_tool_handler-wrapped function.

    Args:
        json_str: JSON string from a server tool call.

    Returns:
        Parsed Python dict.
    """
    return json.loads(json_str)


def _make_urlopen_response(data):
    """Build a MagicMock that looks like a urllib urlopen context manager.

    Args:
        data: Python dict or list to JSON-encode as response body.

    Returns:
        MagicMock configured as a context manager returning JSON bytes.
    """
    encoded = json.dumps(data).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = encoded
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _make_empty_urlopen_response():
    """Build a MagicMock returning empty bytes (204 No Content).

    Returns:
        MagicMock configured to return b'' from read().
    """
    mock_resp = MagicMock()
    mock_resp.read.return_value = b""
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# Group A: Agile Infrastructure tools (tools 11-15 of 25)
# ---------------------------------------------------------------------------

class TestJiraGetBoards:
    """Tests for jira_get_boards tool."""

    @patch("urllib.request.urlopen")
    def test_happy_path_returns_board_list(self, mock_urlopen, jira_env):
        """Happy path: returns boards list from Agile API response."""
        fixture = fixture_loader("agile", "board_list")
        mock_urlopen.return_value = _make_urlopen_response(fixture)

        import server
        raw = server.jira_get_boards()
        result = _parse(raw)

        assert result["success"] is True
        assert "boards" in result
        assert result["count"] == 2
        assert result["boards"][0]["board_id"] == 1

    @patch("urllib.request.urlopen")
    def test_filters_by_project_key(self, mock_urlopen, jira_env):
        """project_key filter appears in the outgoing Agile API URL."""
        fixture = fixture_loader("agile", "board_list")
        mock_urlopen.return_value = _make_urlopen_response(fixture)

        import server
        server.jira_get_boards(project_key="DEMO")

        call_args = mock_urlopen.call_args
        req_url = call_args[0][0].full_url
        assert "DEMO" in req_url or "projectKeyOrId" in req_url

    def test_missing_env_returns_error_json(self, monkeypatch):
        """Missing JIRA_URL returns success=False JSON with environment error."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        raw = server.jira_get_boards()
        result = _parse(raw)

        assert result["success"] is False
        assert "JIRA_URL" in result.get("error", "")

    @patch("urllib.request.urlopen")
    def test_board_type_field_in_each_board(self, mock_urlopen, jira_env):
        """Each board dict in result contains board_type field."""
        fixture = fixture_loader("agile", "board_list")
        mock_urlopen.return_value = _make_urlopen_response(fixture)

        import server
        result = _parse(server.jira_get_boards())

        for board in result["boards"]:
            assert "board_type" in board


class TestJiraGetSprints:
    """Tests for jira_get_sprints tool."""

    @patch("urllib.request.urlopen")
    def test_happy_path_returns_sprint_list(self, mock_urlopen, jira_env):
        """Happy path: returns sprint list for a board."""
        fixture = fixture_loader("agile", "sprint_list")
        mock_urlopen.return_value = _make_urlopen_response(fixture)

        import server
        result = _parse(server.jira_get_sprints(board_id=1))

        assert result["success"] is True
        assert result["board_id"] == 1
        assert result["count"] == 3
        assert result["sprints"][0]["sprint_id"] == 10

    @patch("urllib.request.urlopen")
    def test_state_filter_in_request_url(self, mock_urlopen, jira_env):
        """state filter is included in the outgoing Agile API request URL."""
        fixture = fixture_loader("agile", "sprint_list")
        mock_urlopen.return_value = _make_urlopen_response(fixture)

        import server
        server.jira_get_sprints(board_id=1, state="active")

        req_url = mock_urlopen.call_args[0][0].full_url
        assert "state=active" in req_url

    def test_missing_env_returns_error_json(self, monkeypatch):
        """Missing env vars returns success=False JSON."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_get_sprints(board_id=1))
        assert result["success"] is False

    @patch("urllib.request.urlopen")
    def test_sprint_fields_present(self, mock_urlopen, jira_env):
        """Each sprint dict contains all expected fields."""
        fixture = fixture_loader("agile", "sprint_list")
        mock_urlopen.return_value = _make_urlopen_response(fixture)

        import server
        result = _parse(server.jira_get_sprints(board_id=1))

        sprint = result["sprints"][0]
        for field in ("sprint_id", "sprint_name", "state", "start_date", "end_date", "goal"):
            assert field in sprint


class TestJiraCreateSprint:
    """Tests for jira_create_sprint tool."""

    @patch("urllib.request.urlopen")
    def test_happy_path_returns_sprint_id(self, mock_urlopen, jira_env):
        """Happy path: new sprint returned with sprint_id."""
        response_data = {
            "id": 99,
            "name": "Sprint 99",
            "state": "future",
            "startDate": "2026-03-01T09:00:00.000Z",
            "endDate": "2026-03-15T09:00:00.000Z",
            "goal": "Test goal",
            "originBoardId": 1,
        }
        mock_urlopen.return_value = _make_urlopen_response(response_data)

        import server
        result = _parse(server.jira_create_sprint(board_id=1, name="Sprint 99", goal="Test goal"))

        assert result["success"] is True
        assert result["sprint_id"] == 99
        assert result["state"] == "future"
        assert result["board_id"] == 1

    def test_empty_name_returns_error_json(self, jira_env):
        """Empty sprint name returns success=False JSON (caught by decorator)."""
        import server
        result = _parse(server.jira_create_sprint(board_id=1, name=""))
        assert result["success"] is False
        assert "empty" in result.get("error", "").lower()

    def test_missing_env_returns_error_json(self, monkeypatch):
        """Missing env vars returns success=False JSON."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_create_sprint(board_id=1, name="Sprint X"))
        assert result["success"] is False


class TestJiraStartSprint:
    """Tests for jira_start_sprint tool."""

    @patch("urllib.request.urlopen")
    def test_happy_path_activated_true(self, mock_urlopen, jira_env):
        """Happy path: activated is True and state is active."""
        response_data = {
            "id": 11,
            "name": "Sprint 11",
            "state": "active",
            "startDate": "2026-01-20T09:00:00.000Z",
            "endDate": "2026-02-03T09:00:00.000Z",
            "goal": "Deliver dashboard module",
        }
        mock_urlopen.return_value = _make_urlopen_response(response_data)

        import server
        result = _parse(server.jira_start_sprint(sprint_id=11))

        assert result["success"] is True
        assert result["activated"] is True
        assert result["state"] == "active"
        assert result["sprint_id"] == 11

    def test_missing_env_returns_error_json(self, monkeypatch):
        """Missing env vars returns success=False JSON."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_start_sprint(sprint_id=11))
        assert result["success"] is False

    @patch("urllib.request.urlopen")
    def test_request_body_sets_state_active(self, mock_urlopen, jira_env):
        """POST body sent to Agile API includes state=active."""
        response_data = {"id": 11, "name": "Sprint 11", "state": "active"}
        mock_urlopen.return_value = _make_urlopen_response(response_data)

        import server
        server.jira_start_sprint(sprint_id=11)

        req_obj = mock_urlopen.call_args[0][0]
        body_sent = json.loads(req_obj.data.decode("utf-8"))
        assert body_sent["state"] == "active"


class TestJiraCloseSprint:
    """Tests for jira_close_sprint tool."""

    @patch("urllib.request.urlopen")
    def test_happy_path_closed_true(self, mock_urlopen, jira_env):
        """Happy path: closed is True and state is closed."""
        response_data = {
            "id": 10,
            "name": "Sprint 10",
            "state": "closed",
            "completeDate": "2026-01-19T17:00:00.000Z",
        }
        mock_urlopen.return_value = _make_urlopen_response(response_data)

        import server
        result = _parse(server.jira_close_sprint(sprint_id=10))

        assert result["success"] is True
        assert result["closed"] is True
        assert result["state"] == "closed"
        assert result["sprint_id"] == 10

    def test_missing_env_returns_error_json(self, monkeypatch):
        """Missing env vars returns success=False JSON."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_close_sprint(sprint_id=10))
        assert result["success"] is False

    @patch("urllib.request.urlopen")
    def test_request_body_sets_state_closed(self, mock_urlopen, jira_env):
        """POST body sent to Agile API includes state=closed."""
        response_data = {"id": 10, "name": "Sprint 10", "state": "closed"}
        mock_urlopen.return_value = _make_urlopen_response(response_data)

        import server
        server.jira_close_sprint(sprint_id=10)

        req_obj = mock_urlopen.call_args[0][0]
        body_sent = json.loads(req_obj.data.decode("utf-8"))
        assert body_sent["state"] == "closed"


class TestJiraMoveIssuesToSprint:
    """Tests for jira_move_issues_to_sprint tool."""

    @patch("urllib.request.urlopen")
    def test_happy_path_moved_count(self, mock_urlopen, jira_env):
        """Happy path: moved_count matches the number of keys passed."""
        mock_urlopen.return_value = _make_empty_urlopen_response()

        import server
        result = _parse(server.jira_move_issues_to_sprint(
            sprint_id=35, issue_keys="FAB-1,FAB-2,FAB-3"
        ))

        assert result["success"] is True
        assert result["sprint_id"] == 35
        assert result["moved_count"] == 3
        assert result["batches"] == 1
        assert result["issue_keys"] == ["FAB-1", "FAB-2", "FAB-3"]

    @patch("urllib.request.urlopen")
    def test_request_body_sets_issues_array(self, mock_urlopen, jira_env):
        """POST body sent to Agile API includes the issues array."""
        mock_urlopen.return_value = _make_empty_urlopen_response()

        import server
        server.jira_move_issues_to_sprint(sprint_id=35, issue_keys="FAB-1, FAB-2")

        req_obj = mock_urlopen.call_args[0][0]
        body_sent = json.loads(req_obj.data.decode("utf-8"))
        assert body_sent["issues"] == ["FAB-1", "FAB-2"]

    @patch("urllib.request.urlopen")
    def test_batches_over_fifty_keys(self, mock_urlopen, jira_env):
        """More than 50 keys are sent in successive batches of 50."""
        mock_urlopen.return_value = _make_empty_urlopen_response()
        keys = ",".join("FAB-%d" % i for i in range(1, 61))  # 60 keys

        import server
        result = _parse(server.jira_move_issues_to_sprint(
            sprint_id=35, issue_keys=keys
        ))

        assert result["success"] is True
        assert result["moved_count"] == 60
        assert result["batches"] == 2
        assert mock_urlopen.call_count == 2

    def test_empty_issue_keys_returns_error_json(self, jira_env):
        """Empty/whitespace-only issue_keys returns success=False, not a crash."""
        import server
        result = _parse(server.jira_move_issues_to_sprint(
            sprint_id=35, issue_keys="   ,  ,"
        ))
        assert result["success"] is False

    def test_missing_env_returns_error_json(self, monkeypatch):
        """Missing env vars returns success=False JSON."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_move_issues_to_sprint(
            sprint_id=35, issue_keys="FAB-1"
        ))
        assert result["success"] is False


# ---------------------------------------------------------------------------
# Group B: Ceremony Facilitation tools (tools 16-20 of 25)
# ---------------------------------------------------------------------------

class TestJiraPlanSprint:
    """Tests for jira_plan_sprint tool."""

    @patch("urllib.request.urlopen")
    def test_happy_path_capacity_computed(self, mock_urlopen, jira_env):
        """Happy path: capacity dict is present and capacity_points > 0."""
        sprint_detail = fixture_loader("agile", "sprint_detail")
        sprint_issues = fixture_loader("agile", "sprint_issues")

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(sprint_issues),
        ]

        import server
        result = _parse(server.jira_plan_sprint(
            board_id=1, sprint_id=11, members=5, sprint_days=10, focus_factor=0.7
        ))

        assert result["success"] is True
        assert "capacity" in result
        assert result["capacity"]["capacity_points"] > 0
        assert result["sprint_id"] == 11

    @patch("urllib.request.urlopen")
    def test_india_holidays_counted_when_dates_provided(self, mock_urlopen, jira_env):
        """When sprint dates span Republic Day (2026-01-26), holiday count >= 1."""
        sprint_detail = fixture_loader("agile", "sprint_detail")
        sprint_issues = fixture_loader("agile", "sprint_issues")

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(sprint_issues),
        ]

        import server
        result = _parse(server.jira_plan_sprint(
            board_id=1, sprint_id=11, members=5, sprint_days=10,
            sprint_start_iso="2026-01-20", sprint_end_iso="2026-02-03"
        ))
        assert result["success"] is True
        assert result["india_holidays_in_sprint"] >= 1

    def test_missing_env_returns_error_json(self, monkeypatch):
        """Missing env vars returns success=False JSON."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_plan_sprint(
            board_id=1, sprint_id=11, members=5, sprint_days=10
        ))
        assert result["success"] is False

    @patch("urllib.request.urlopen")
    def test_sprint_issues_count_correct(self, mock_urlopen, jira_env):
        """sprint_issues_count matches the number of issues in fixture (5)."""
        sprint_detail = fixture_loader("agile", "sprint_detail")
        sprint_issues = fixture_loader("agile", "sprint_issues")

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(sprint_issues),
        ]

        import server
        result = _parse(server.jira_plan_sprint(
            board_id=1, sprint_id=11, members=5, sprint_days=10
        ))
        assert result["sprint_issues_count"] == 5


class TestJiraDailyStandup:
    """Tests for jira_daily_standup tool."""

    @patch("urllib.request.urlopen")
    def test_happy_path_groups_by_assignee(self, mock_urlopen, jira_env):
        """Happy path: progress_by_assignee contains Alice (from fixture)."""
        sprint_detail = fixture_loader("agile", "sprint_detail")
        sprint_issues = fixture_loader("agile", "sprint_issues")

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(sprint_issues),
        ]

        import server
        result = _parse(server.jira_daily_standup(sprint_id=11))

        assert result["success"] is True
        assert "progress_by_assignee" in result
        assert "Alice" in result["progress_by_assignee"]

    @patch("urllib.request.urlopen")
    def test_blocked_issues_detected_by_impediment_label(self, mock_urlopen, jira_env):
        """Issues with 'impediment' label appear in blocked_issues list."""
        sprint_detail = fixture_loader("agile", "sprint_detail")
        sprint_issues = fixture_loader("agile", "sprint_issues")

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(sprint_issues),
        ]

        import server
        result = _parse(server.jira_daily_standup(sprint_id=11))

        # DEMO-103 has label 'impediment' in fixture
        blocked_keys = [b["issue_key"] for b in result["blocked_issues"]]
        assert "DEMO-103" in blocked_keys

    def test_missing_env_returns_error_json(self, monkeypatch):
        """Missing env vars returns success=False JSON."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_daily_standup(sprint_id=11))
        assert result["success"] is False

    @patch("urllib.request.urlopen")
    def test_done_count_matches_fixture(self, mock_urlopen, jira_env):
        """done_count = 3 (DEMO-101, 104, 105 are Done in fixture)."""
        sprint_detail = fixture_loader("agile", "sprint_detail")
        sprint_issues = fixture_loader("agile", "sprint_issues")

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(sprint_issues),
        ]

        import server
        result = _parse(server.jira_daily_standup(sprint_id=11))

        assert result["done_count"] == 3
        assert result["total_issues"] == 5


class TestJiraSprintReview:
    """Tests for jira_sprint_review tool."""

    @patch("urllib.request.urlopen")
    def test_happy_path_velocity_stats_present(self, mock_urlopen, jira_env):
        """Happy path: velocity_mean and nasscom_agileX_level present."""
        sprint_detail = fixture_loader("agile", "sprint_detail")
        sprint_issues = fixture_loader("agile", "sprint_issues")
        closed_sprints_empty = {"values": [], "total": 0}

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(sprint_issues),
            _make_urlopen_response(closed_sprints_empty),
        ]

        import server
        result = _parse(server.jira_sprint_review(board_id=1, sprint_id=11))

        assert result["success"] is True
        assert "velocity_mean" in result
        assert "nasscom_agileX_level" in result
        assert "completed_points" in result

    @patch("urllib.request.urlopen")
    def test_completion_rate_between_0_and_100(self, mock_urlopen, jira_env):
        """completion_rate is in [0.0, 100.0]."""
        sprint_detail = fixture_loader("agile", "sprint_detail")
        sprint_issues = fixture_loader("agile", "sprint_issues")
        closed_sprints_empty = {"values": [], "total": 0}

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(sprint_issues),
            _make_urlopen_response(closed_sprints_empty),
        ]

        import server
        result = _parse(server.jira_sprint_review(board_id=1, sprint_id=11))

        assert 0.0 <= result["completion_rate"] <= 100.0

    def test_missing_env_returns_error_json(self, monkeypatch):
        """Missing env vars returns success=False JSON."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_sprint_review(board_id=1, sprint_id=11))
        assert result["success"] is False


class TestJiraRetrospective:
    """Tests for jira_retrospective tool."""

    @patch("urllib.request.urlopen")
    def test_happy_path_format_rotation_present(self, mock_urlopen, jira_env):
        """Happy path: recommended_format is a non-empty string."""
        sprint_detail = fixture_loader("agile", "sprint_detail")
        closed_sprints = {"values": [], "total": 0}

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(closed_sprints),
        ]

        import server
        result = _parse(server.jira_retrospective(sprint_id=11, board_id=1))

        assert result["success"] is True
        assert isinstance(result["recommended_format"], str)
        assert len(result["recommended_format"]) > 0

    @patch("urllib.request.urlopen")
    def test_re_score_between_zero_and_one(self, mock_urlopen, jira_env):
        """RE score is in [0.0, 1.0]."""
        sprint_detail = fixture_loader("agile", "sprint_detail")
        closed_sprints = {"values": [], "total": 0}

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(closed_sprints),
        ]

        import server
        result = _parse(server.jira_retrospective(sprint_id=11, board_id=1))

        assert 0.0 <= result["re_score"] <= 1.0

    def test_missing_env_returns_error_json(self, monkeypatch):
        """Missing env vars returns success=False JSON."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_retrospective(sprint_id=11, board_id=1))
        assert result["success"] is False


class TestJiraRefineBacklog:
    """Tests for jira_refine_backlog tool."""

    @patch("urllib.request.urlopen")
    def test_happy_path_returns_stories(self, mock_urlopen, jira_env):
        """Happy path: wsjf_ordered_stories list is present in result."""
        search_result = fixture_loader("rest", "issue_search_sprint")
        mock_urlopen.return_value = _make_urlopen_response(search_result)

        import server
        result = _parse(server.jira_refine_backlog(project_key="DEMO"))

        assert result["success"] is True
        assert "wsjf_ordered_stories" in result
        assert result["project_key"] == "DEMO"

    @patch("urllib.request.urlopen")
    def test_wsjf_template_present_per_story(self, mock_urlopen, jira_env):
        """Each story has a wsjf_template dict with the four required keys."""
        search_result = fixture_loader("rest", "issue_search_sprint")
        mock_urlopen.return_value = _make_urlopen_response(search_result)

        import server
        result = _parse(server.jira_refine_backlog(project_key="DEMO"))

        for story in result["wsjf_ordered_stories"]:
            tpl = story["wsjf_template"]
            for key in ("business_value", "time_criticality", "risk_reduction", "job_size"):
                assert key in tpl

    def test_empty_project_key_returns_error_json(self, jira_env):
        """Empty project_key returns success=False JSON (caught by decorator)."""
        import server
        result = _parse(server.jira_refine_backlog(project_key=""))
        assert result["success"] is False
        assert "empty" in result.get("error", "").lower()

    def test_missing_env_returns_error_json(self, monkeypatch):
        """Missing env vars returns success=False JSON."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_refine_backlog(project_key="DEMO"))
        assert result["success"] is False

    @patch("urllib.request.urlopen")
    def test_recommendations_list_non_empty(self, mock_urlopen, jira_env):
        """refinement_recommendations is a non-empty list."""
        search_result = fixture_loader("rest", "issue_search_sprint")
        mock_urlopen.return_value = _make_urlopen_response(search_result)

        import server
        result = _parse(server.jira_refine_backlog(project_key="DEMO"))

        assert isinstance(result["refinement_recommendations"], list)
        assert len(result["refinement_recommendations"]) > 0


# ---------------------------------------------------------------------------
# Group C: Analytics tools (tools 21-25 of 25)
# ---------------------------------------------------------------------------

class TestJiraGetVelocity:
    """Tests for jira_get_velocity tool."""

    @patch("urllib.request.urlopen")
    def test_happy_path_velocity_stats_present(self, mock_urlopen, jira_env):
        """Happy path via velocity chart endpoint: velocity_stats in result."""
        velocity_chart = fixture_loader("agile", "velocity_chart")
        mock_urlopen.return_value = _make_urlopen_response(velocity_chart)

        import server
        result = _parse(server.jira_get_velocity(board_id=1))

        assert result["success"] is True
        assert "velocity_stats" in result
        assert "velocity_history" in result
        assert result["board_id"] == 1

    @patch("urllib.request.urlopen")
    def test_ewma_last_is_non_negative(self, mock_urlopen, jira_env):
        """ewma_last >= 0 and ewma_alpha == 0.3."""
        velocity_chart = fixture_loader("agile", "velocity_chart")
        mock_urlopen.return_value = _make_urlopen_response(velocity_chart)

        import server
        result = _parse(server.jira_get_velocity(board_id=1))

        assert result["ewma_last"] >= 0.0
        assert result["ewma_alpha"] == 0.3

    @patch("urllib.request.urlopen")
    def test_fallback_to_closed_sprints_when_velocity_fails(self, mock_urlopen, jira_env):
        """Falls back to closed sprint enumeration when velocity chart returns 404."""
        from urllib.error import HTTPError
        import io as _io

        err = HTTPError(
            url="https://test.atlassian.net/rest/agile/1.0/rapid/charts/velocity",
            code=404, msg="Not Found", hdrs={}, fp=_io.BytesIO(b'{"errorMessages": []}')
        )
        fallback = _make_urlopen_response({"values": [], "total": 0})
        mock_urlopen.side_effect = [err, fallback]

        import server
        result = _parse(server.jira_get_velocity(board_id=1))

        assert result["success"] is True
        assert result["sprints_analyzed"] == 0

    def test_missing_env_returns_error_json(self, monkeypatch):
        """Missing env vars returns success=False JSON."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_get_velocity(board_id=1))
        assert result["success"] is False


class TestJiraGetSprintMetrics:
    """Tests for jira_get_sprint_metrics tool."""

    @patch("urllib.request.urlopen")
    def test_happy_path_health_field_present(self, mock_urlopen, jira_env):
        """Happy path: sprint_health is a valid health string."""
        sprint_detail = fixture_loader("agile", "sprint_detail")
        sprint_issues = fixture_loader("agile", "sprint_issues")

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(sprint_issues),
        ]

        import server
        result = _parse(server.jira_get_sprint_metrics(board_id=1, sprint_id=11))

        assert result["success"] is True
        assert result["sprint_health"] in ("On Track", "At Risk", "Off Track")

    @patch("urllib.request.urlopen")
    def test_issue_counts_sum_to_total(self, mock_urlopen, jira_env):
        """done + in_progress + todo == total_issues."""
        sprint_detail = fixture_loader("agile", "sprint_detail")
        sprint_issues = fixture_loader("agile", "sprint_issues")

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(sprint_issues),
        ]

        import server
        result = _parse(server.jira_get_sprint_metrics(board_id=1, sprint_id=11))

        total = result["done_issues"] + result["in_progress_issues"] + result["todo_issues"]
        assert total == result["total_issues"]

    def test_missing_env_returns_error_json(self, monkeypatch):
        """Missing env vars returns success=False JSON."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_get_sprint_metrics(board_id=1, sprint_id=11))
        assert result["success"] is False

    @patch("urllib.request.urlopen")
    def test_sprint_id_echoed_in_result(self, mock_urlopen, jira_env):
        """sprint_id and board_id are echoed in result."""
        sprint_detail = fixture_loader("agile", "sprint_detail")
        sprint_issues = fixture_loader("agile", "sprint_issues")

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(sprint_issues),
        ]

        import server
        result = _parse(server.jira_get_sprint_metrics(board_id=1, sprint_id=11))

        assert result["sprint_id"] == 11
        assert result["board_id"] == 1


class TestJiraTrackImpediments:
    """Tests for jira_track_impediments tool."""

    @patch("urllib.request.urlopen")
    def test_happy_path_mttr_computed(self, mock_urlopen, jira_env):
        """Happy path: mttr_days_mean is present and non-negative."""
        impediment_fixture = fixture_loader("rest", "issue_search_impediment")
        mock_urlopen.return_value = _make_urlopen_response(impediment_fixture)

        import server
        result = _parse(server.jira_track_impediments(project_key="DEMO"))

        assert result["success"] is True
        assert "mttr_days_mean" in result
        assert result["mttr_days_mean"] >= 0.0
        assert result["project_key"] == "DEMO"

    @patch("urllib.request.urlopen")
    def test_open_impediments_count_correct(self, mock_urlopen, jira_env):
        """open_impediments == 1 (one In Progress impediment in fixture)."""
        impediment_fixture = fixture_loader("rest", "issue_search_impediment")
        mock_urlopen.return_value = _make_urlopen_response(impediment_fixture)

        import server
        result = _parse(server.jira_track_impediments(project_key="DEMO"))

        assert result["open_impediments"] == 1

    @patch("urllib.request.urlopen")
    def test_closed_impediments_count_correct(self, mock_urlopen, jira_env):
        """closed_impediments_count == 1 (one Done impediment in fixture)."""
        impediment_fixture = fixture_loader("rest", "issue_search_impediment")
        mock_urlopen.return_value = _make_urlopen_response(impediment_fixture)

        import server
        result = _parse(server.jira_track_impediments(project_key="DEMO"))

        assert result["closed_impediments_count"] == 1

    def test_missing_env_returns_error_json(self, monkeypatch):
        """Missing env vars returns success=False JSON."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_track_impediments(project_key="DEMO"))
        assert result["success"] is False

    @patch("urllib.request.urlopen")
    def test_escalation_required_is_boolean(self, mock_urlopen, jira_env):
        """escalation_required is a boolean value."""
        impediment_fixture = fixture_loader("rest", "issue_search_impediment")
        mock_urlopen.return_value = _make_urlopen_response(impediment_fixture)

        import server
        result = _parse(server.jira_track_impediments(project_key="DEMO"))

        assert isinstance(result["escalation_required"], bool)


class TestJiraTeamHealth:
    """Tests for jira_team_health tool."""

    @patch("urllib.request.urlopen")
    def test_happy_path_tuckman_stage_present(self, mock_urlopen, jira_env):
        """Happy path: tuckman_stage is one of the four valid Tuckman stages."""
        sprint_issues = fixture_loader("agile", "sprint_issues")
        closed_one_sprint = {"values": [{"id": 10, "name": "Sprint 10", "state": "closed"}], "total": 1}

        mock_urlopen.side_effect = [
            _make_urlopen_response(closed_one_sprint),
            _make_urlopen_response(sprint_issues),
        ]

        import server
        result = _parse(server.jira_team_health(board_id=1))

        assert result["success"] is True
        valid_stages = {"Forming", "Storming", "Norming", "Performing"}
        assert result["tuckman_stage"] in valid_stages
        assert result["board_id"] == 1

    @patch("urllib.request.urlopen")
    def test_recommended_intervention_non_empty(self, mock_urlopen, jira_env):
        """recommended_intervention is a non-empty string."""
        mock_urlopen.side_effect = [
            _make_urlopen_response({"values": [], "total": 0}),
        ]

        import server
        result = _parse(server.jira_team_health(board_id=1))

        assert len(result["recommended_intervention"]) > 0

    def test_missing_env_returns_error_json(self, monkeypatch):
        """Missing env vars returns success=False JSON."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_team_health(board_id=1))
        assert result["success"] is False

    @patch("urllib.request.urlopen")
    def test_india_attrition_note_present(self, mock_urlopen, jira_env):
        """india_attrition_note is present and mentions India."""
        mock_urlopen.side_effect = [
            _make_urlopen_response({"values": [], "total": 0}),
        ]

        import server
        result = _parse(server.jira_team_health(board_id=1))

        assert "india_attrition_note" in result
        assert "India" in result["india_attrition_note"]


class TestJiraMonteCarloForecast:
    """Tests for jira_monte_carlo_forecast tool."""

    @patch("urllib.request.urlopen")
    def test_happy_path_p85_gte_p50(self, mock_urlopen, jira_env):
        """Happy path: p85_sprints >= p50_sprints."""
        velocity_chart = fixture_loader("agile", "velocity_chart")
        mock_urlopen.return_value = _make_urlopen_response(velocity_chart)

        import server
        result = _parse(server.jira_monte_carlo_forecast(board_id=1, remaining_story_points=100))

        assert result["success"] is True
        assert result["p85_sprints"] >= result["p50_sprints"]

    @patch("urllib.request.urlopen")
    def test_p95_gte_p85(self, mock_urlopen, jira_env):
        """p95_sprints >= p85_sprints."""
        velocity_chart = fixture_loader("agile", "velocity_chart")
        mock_urlopen.return_value = _make_urlopen_response(velocity_chart)

        import server
        result = _parse(server.jira_monte_carlo_forecast(board_id=1, remaining_story_points=100))

        assert result["p95_sprints"] >= result["p85_sprints"]

    @patch("urllib.request.urlopen")
    def test_p85_weeks_ist_equals_p85_times_two(self, mock_urlopen, jira_env):
        """p85_weeks_ist == round(p85_sprints * 2, 1)."""
        velocity_chart = fixture_loader("agile", "velocity_chart")
        mock_urlopen.return_value = _make_urlopen_response(velocity_chart)

        import server
        result = _parse(server.jira_monte_carlo_forecast(board_id=1, remaining_story_points=100))

        expected = round(result["p85_sprints"] * 2, 1)
        assert result["p85_weeks_ist"] == expected

    def test_remaining_points_zero_returns_error_json(self, jira_env):
        """remaining_story_points < 1 returns success=False JSON (caught by decorator)."""
        import server
        result = _parse(server.jira_monte_carlo_forecast(board_id=1, remaining_story_points=0))
        assert result["success"] is False
        assert "remaining_story_points" in result.get("error", "")

    def test_missing_env_returns_error_json(self, monkeypatch):
        """Missing env vars returns success=False JSON."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_monte_carlo_forecast(board_id=1, remaining_story_points=100))
        assert result["success"] is False

    @patch("urllib.request.urlopen")
    def test_insufficient_samples_returns_error_json(self, mock_urlopen, jira_env):
        """Fewer than 2 positive velocity samples returns success=False JSON."""
        from urllib.error import HTTPError
        import io as _io

        vel_err = HTTPError(
            url="https://test.atlassian.net/rest/agile/1.0/rapid/charts/velocity",
            code=404, msg="Not Found", hdrs={}, fp=_io.BytesIO(b'{"errorMessages": []}')
        )
        fallback = _make_urlopen_response({"values": [], "total": 0})
        mock_urlopen.side_effect = [vel_err, fallback]

        import server
        result = _parse(server.jira_monte_carlo_forecast(board_id=1, remaining_story_points=50))
        assert result["success"] is False
        assert "Fewer than 2" in result.get("error", "")

    @patch("urllib.request.urlopen")
    def test_iterations_echoed_in_result(self, mock_urlopen, jira_env):
        """iterations value is echoed in result dict."""
        velocity_chart = fixture_loader("agile", "velocity_chart")
        mock_urlopen.return_value = _make_urlopen_response(velocity_chart)

        import server
        result = _parse(server.jira_monte_carlo_forecast(
            board_id=1, remaining_story_points=80, iterations=500
        ))
        assert result["iterations"] == 500

    @patch("urllib.request.urlopen")
    def test_india_it_note_present(self, mock_urlopen, jira_env):
        """india_it_note is present in the result."""
        velocity_chart = fixture_loader("agile", "velocity_chart")
        mock_urlopen.return_value = _make_urlopen_response(velocity_chart)

        import server
        result = _parse(server.jira_monte_carlo_forecast(board_id=1, remaining_story_points=80))

        assert "india_it_note" in result
        assert len(result["india_it_note"]) > 0
