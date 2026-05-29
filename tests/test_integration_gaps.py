"""
test_integration_gaps.py -- End-to-end flow tests for the 4 KG gap closures.

These tests exercise multi-step flows across the new tools using mocked
urllib.request.urlopen (no live Jira). They verify that IDs and keys flow
correctly between sequential tool calls and that the request shape sent to
Jira matches the documented Pact contract (tests/pacts/jira_api_contracts.md).

All @mcp_tool_handler tools return JSON strings -- tests json.loads() results.
Tools are sync def -- called directly, no asyncio.run().

Windows-Safe: ASCII only (cp1252 compatible)
"""

import json
import os
import sys
import urllib.error
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import server  # noqa: E402


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


def _sprint_detail():
    return {"id": 7, "name": "Sprint 7", "state": "active", "goal": "Ship"}


def _sprint_issues():
    return {
        "total": 1,
        "issues": [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "Story one",
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Story"},
                    "customfield_10016": 5.0,
                    "subtasks": [],
                    "assignee": {"displayName": "Alice"},
                },
            }
        ],
    }


# ---------------------------------------------------------------------------
# Scenario 1: Epic lifecycle -- create -> link -> list
# ---------------------------------------------------------------------------


class TestEpicLifecycleFlow(unittest.TestCase):
    """Epic create, link a story, then list epics on the board."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_create_link_list_flow(self, mock_urlopen):
        """Full epic flow: create returns key, link succeeds, list shows epics."""
        create_resp = {"id": "10042", "key": "PROJ-42"}
        link_resp = b""  # 204 PUT
        list_resp = {
            "values": [{"id": 1, "key": "PROJ-42", "summary": "Q1 Goals", "done": False}],
            "total": 1,
        }
        mock_urlopen.side_effect = [
            _make_resp(create_resp),
            _make_empty_resp(),
            _make_resp(list_resp),
        ]

        created = _parse(server.jira_create_epic("PROJ", "Q1 Goals", "Q1 Goals Epic"))
        assert created["success"] is True
        epic_key = created["epic_key"]
        assert epic_key == "PROJ-42"

        linked = _parse(server.jira_link_to_epic("PROJ-10", epic_key))
        assert linked["success"] is True
        assert linked["epic_key"] == "PROJ-42"

        listed = _parse(server.jira_list_epics(1))
        assert listed["success"] is True
        assert listed["total"] == 1
        assert listed["epics"][0]["key"] == "PROJ-42"


# ---------------------------------------------------------------------------
# Scenario 2: Version lifecycle -- create -> list -> release
# ---------------------------------------------------------------------------


class TestVersionLifecycleFlow(unittest.TestCase):
    """Version create, list, then release; version_id flows between calls."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_create_list_release_flow(self, mock_urlopen):
        """version_id from create is usable in release; list reflects state."""
        create_resp = {"id": "10010", "name": "v1.0.0", "released": False}
        list_resp = [
            {"id": "10010", "name": "v1.0.0", "released": False, "archived": False, "releaseDate": None}
        ]
        mock_urlopen.side_effect = [
            _make_resp(create_resp),
            _make_resp(list_resp),
            _make_empty_resp(),
        ]

        created = _parse(server.jira_create_version("PROJ", "v1.0.0"))
        assert created["success"] is True
        version_id = created["version_id"]
        assert version_id == "10010"

        listed = _parse(server.jira_list_versions("PROJ"))
        assert listed["success"] is True
        assert listed["versions"][0]["id"] == "10010"

        released = _parse(server.jira_release_version(version_id, release_date="2026-06-30"))
        assert released["success"] is True
        assert released["released"] is True
        assert released["version_id"] == "10010"
        assert released["release_date"] == "2026-06-30"

    @patch("urllib.request.urlopen")
    def test_release_notes_jql_contains_fixversion(self, mock_urlopen):
        """release_notes sends a JQL containing the fixVersion filter."""
        mock_urlopen.return_value = _make_resp({"issues": [], "total": 0})

        result = _parse(server.jira_release_notes("PROJ", "v1.0.0"))
        assert result["success"] is True

        req = mock_urlopen.call_args[0][0]
        url = req.full_url if hasattr(req, "full_url") else str(req)
        assert "fixVersion" in url
        assert "v1.0.0" in url


# ---------------------------------------------------------------------------
# Scenario 3: AHP backward compat integration
# ---------------------------------------------------------------------------


class TestAHPBackwardCompatFlow(unittest.TestCase):
    """jira_sprint_review without weights must keep all legacy keys."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_no_weights_keeps_legacy_keys_and_omits_weighted_score(self, mock_urlopen):
        """All pre-existing keys present; dod_weighted_score absent."""
        mock_urlopen.side_effect = [
            _make_resp(_sprint_detail()),
            _make_resp(_sprint_issues()),
            _make_resp({"values": []}),
        ]
        result = _parse(server.jira_sprint_review(board_id=1, sprint_id=7))

        assert result["success"] is True
        for key in ("dod_compliance_pct", "demo_ready_issues", "ahp_weights", "ahp_CR"):
            assert key in result
        assert "dod_weighted_score" not in result

    @patch("urllib.request.urlopen")
    def test_with_weights_adds_weighted_score(self, mock_urlopen):
        """Providing a consistent matrix adds dod_weighted_score to result."""
        mock_urlopen.side_effect = [
            _make_resp(_sprint_detail()),
            _make_resp(_sprint_issues()),
            _make_resp({"values": []}),
        ]
        matrix = [[1.0, 3.0, 5.0], [1.0 / 3.0, 1.0, 2.0], [1.0 / 5.0, 0.5, 1.0]]
        result = _parse(
            server.jira_sprint_review(board_id=1, sprint_id=7, dod_criteria_weights=matrix)
        )

        assert result["success"] is True
        assert "dod_weighted_score" in result


# ---------------------------------------------------------------------------
# Scenario 4: Cross-board aggregation
# ---------------------------------------------------------------------------


class TestCrossBoardAggregationFlow(unittest.TestCase):
    """jira_program_velocity aggregates two boards into per_team keyed by str(id)."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_two_boards_aggregate_with_string_keys(self, mock_urlopen):
        """per_team has string board keys; program_total_avg combines both."""
        v1 = {
            "velocityStatEntries": {
                "1": {"estimated": {"value": 20}, "completed": {"value": 18}},
                "2": {"estimated": {"value": 22}, "completed": {"value": 22}},
            }
        }
        v2 = {
            "velocityStatEntries": {
                "1": {"estimated": {"value": 30}, "completed": {"value": 30}},
                "2": {"estimated": {"value": 28}, "completed": {"value": 26}},
            }
        }
        mock_urlopen.side_effect = [_make_resp(v1), _make_resp(v2)]

        result = _parse(server.jira_program_velocity([101, 102], num_sprints=2))

        assert result["success"] is True
        assert result["board_count"] == 2
        assert "101" in result["per_team"]
        assert "102" in result["per_team"]
        assert result["per_team"]["101"]["avg_velocity"] == 20.0
        assert result["per_team"]["102"]["avg_velocity"] == 28.0
        assert result["program_total_avg"] > 0.0


# ---------------------------------------------------------------------------
# Scenario 5: Error propagation (HTTP 404 -> success False, no leak)
# ---------------------------------------------------------------------------


class TestErrorPropagationFlow(unittest.TestCase):
    """HTTPError from Jira API must surface as success=False, not crash."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    def _http_error(self):
        return urllib.error.HTTPError(
            url="https://test.atlassian.net/rest/api/3/issue/PROJ-99",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )

    @patch("urllib.request.urlopen")
    def test_create_epic_404_returns_failure(self, mock_urlopen):
        """404 on epic create returns success=False."""
        err = self._http_error()
        err.read = lambda: b'{"errorMessages":["Project not found"],"errors":{}}'
        mock_urlopen.side_effect = err

        result = _parse(server.jira_create_epic("NOPE", "X", "Y"))
        assert result["success"] is False
        assert "error" in result

    @patch("urllib.request.urlopen")
    def test_list_versions_404_returns_failure(self, mock_urlopen):
        """404 on list versions returns success=False."""
        err = self._http_error()
        err.read = lambda: b'{"errorMessages":["No project"],"errors":{}}'
        mock_urlopen.side_effect = err

        result = _parse(server.jira_list_versions("NOPE"))
        assert result["success"] is False

    @patch("urllib.request.urlopen")
    def test_program_velocity_api_error_returns_failure(self, mock_urlopen):
        """Generic exception during velocity fetch returns success=False."""
        mock_urlopen.side_effect = Exception("connection reset")
        result = _parse(server.jira_program_velocity([101]))
        assert result["success"] is False


# ---------------------------------------------------------------------------
# Scenario 6: Input validation integration (null byte -> failure)
# ---------------------------------------------------------------------------


class TestInputValidationFlow(unittest.TestCase):
    """validate_input strips null bytes; oversized input raises ValueError."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_null_byte_in_project_key_stripped(self, mock_urlopen):
        """Null byte is stripped from project_key; call proceeds with clean value."""
        mock_urlopen.return_value = _make_resp({"id": "1", "key": "PROJ-1"})

        result = _parse(server.jira_create_epic("PR\x00OJ", "Name", "Summary"))
        # Null byte stripped -> "PROJ"; request proceeds, returns success
        assert result["success"] is True

    def test_oversized_version_name_returns_failure(self):
        """Version name exceeding 4096 chars raises ValueError -> success False."""
        huge = "v" + ("x" * 5000)
        result = _parse(server.jira_release_notes("PROJ", huge))
        assert result["success"] is False
        assert "error" in result


if __name__ == "__main__":
    unittest.main()
