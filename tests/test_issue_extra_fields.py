"""
test_issue_extra_fields.py -- Unit tests for story_points/components/parent
support on jira_create_issue and jira_update_issue.

Covers the gap found while wiring claude-global-library's Sprint Planning
pipeline: neither tool previously accepted story_points, components, or
parent, even though the pipeline docs assumed all three existed.

Pattern:
  All @mcp_tool_handler tools return JSON strings.
  Tests always json.loads() the result and check result["success"].
  Mock: @patch("urllib.request.urlopen")
  Request body inspection: json.loads(req.data.decode("utf-8"))

Windows-Safe: ASCII only (cp1252 compatible)
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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


def _set_env(extra=None):
    import os
    for k, v in JIRA_ENV.items():
        os.environ[k] = v
    if extra:
        for k, v in extra.items():
            os.environ[k] = v


def _clear_env(extra=None):
    import os
    for k in JIRA_ENV:
        os.environ.pop(k, None)
    if extra:
        for k in extra:
            os.environ.pop(k, None)


class TestCreateIssueStoryPoints(unittest.TestCase):
    """jira_create_issue: story_points writes to the configured custom field."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env(extra=["JIRA_STORY_POINTS_FIELD"])

    @patch("urllib.request.urlopen")
    def test_story_points_writes_default_field(self, mock_urlopen):
        """With no JIRA_STORY_POINTS_FIELD set, writes to customfield_10016."""
        mock_urlopen.return_value = _make_resp({"key": "PROJ-1", "id": "1001"})

        result = _parse(
            server.jira_create_issue(
                "PROJ", "New Story", issue_type="Story", story_points=5.0
            )
        )

        assert result["success"] is True
        assert result["issue_key"] == "PROJ-1"

        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        assert body["fields"]["customfield_10016"] == 5.0

    @patch("urllib.request.urlopen")
    def test_story_points_respects_env_override(self, mock_urlopen):
        """JIRA_STORY_POINTS_FIELD overrides the default custom field ID."""
        _set_env(extra={"JIRA_STORY_POINTS_FIELD": "customfield_99999"})
        mock_urlopen.return_value = _make_resp({"key": "PROJ-2", "id": "1002"})

        result = _parse(
            server.jira_create_issue(
                "PROJ", "New Story", issue_type="Story", story_points=8.0
            )
        )

        assert result["success"] is True
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        assert body["fields"]["customfield_99999"] == 8.0
        assert "customfield_10016" not in body["fields"]

    @patch("urllib.request.urlopen")
    def test_omitted_story_points_field_absent(self, mock_urlopen):
        """Omitting story_points writes no story-points field at all."""
        mock_urlopen.return_value = _make_resp({"key": "PROJ-3", "id": "1003"})

        result = _parse(server.jira_create_issue("PROJ", "Plain Task"))

        assert result["success"] is True
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        assert "customfield_10016" not in body["fields"]


class TestCreateIssueComponents(unittest.TestCase):
    """jira_create_issue: components is comma-split into Jira's component objects."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_components_split_and_shaped(self, mock_urlopen):
        mock_urlopen.return_value = _make_resp({"key": "PROJ-4", "id": "1004"})

        result = _parse(
            server.jira_create_issue(
                "PROJ", "New Story", components="Backend, Auth ,Frontend"
            )
        )

        assert result["success"] is True
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        assert body["fields"]["components"] == [
            {"name": "Backend"},
            {"name": "Auth"},
            {"name": "Frontend"},
        ]

    @patch("urllib.request.urlopen")
    def test_omitted_components_field_absent(self, mock_urlopen):
        mock_urlopen.return_value = _make_resp({"key": "PROJ-5", "id": "1005"})

        result = _parse(server.jira_create_issue("PROJ", "Plain Task"))

        assert result["success"] is True
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        assert "components" not in body["fields"]


class TestCreateIssueParent(unittest.TestCase):
    """jira_create_issue: parent enables Sub-task creation."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_parent_sets_parent_key_field(self, mock_urlopen):
        mock_urlopen.return_value = _make_resp({"key": "PROJ-11", "id": "1011"})

        result = _parse(
            server.jira_create_issue(
                "PROJ", "Dev sub-task", issue_type="Sub-task", parent="PROJ-10"
            )
        )

        assert result["success"] is True
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        assert body["fields"]["parent"] == {"key": "PROJ-10"}
        assert body["fields"]["issuetype"] == {"name": "Sub-task"}

    @patch("urllib.request.urlopen")
    def test_omitted_parent_field_absent(self, mock_urlopen):
        mock_urlopen.return_value = _make_resp({"key": "PROJ-12", "id": "1012"})

        result = _parse(server.jira_create_issue("PROJ", "Plain Task"))

        assert result["success"] is True
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        assert "parent" not in body["fields"]

    def test_invalid_parent_key_rejected(self):
        """A path-injection-shaped parent key is rejected before any request."""
        result = _parse(
            server.jira_create_issue(
                "PROJ", "Dev sub-task", issue_type="Sub-task",
                parent="PROJ-1/../../other",
            )
        )
        assert result["success"] is False


class TestUpdateIssueExtraFields(unittest.TestCase):
    """jira_update_issue: story_points and components update after creation."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env(extra=["JIRA_STORY_POINTS_FIELD"])

    @patch("urllib.request.urlopen")
    def test_story_points_update_writes_default_field(self, mock_urlopen):
        mock_urlopen.return_value = _make_empty_resp()

        result = _parse(server.jira_update_issue("PROJ-1", story_points=3.0))

        assert result["success"] is True
        assert "customfield_10016" in result["updated_fields"]
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        assert body["fields"]["customfield_10016"] == 3.0

    @patch("urllib.request.urlopen")
    def test_components_update_replaces_list(self, mock_urlopen):
        mock_urlopen.return_value = _make_empty_resp()

        result = _parse(server.jira_update_issue("PROJ-1", components="QA, Docs"))

        assert result["success"] is True
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        assert body["fields"]["components"] == [{"name": "QA"}, {"name": "Docs"}]

    @patch("urllib.request.urlopen")
    def test_backward_compat_existing_fields_still_work(self, mock_urlopen):
        """Pre-existing update fields are unaffected by the new parameters."""
        mock_urlopen.return_value = _make_empty_resp()

        result = _parse(server.jira_update_issue("PROJ-1", summary="Renamed"))

        assert result["success"] is True
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        assert body["fields"]["summary"] == "Renamed"
        assert "customfield_10016" not in body["fields"]
        assert "components" not in body["fields"]


class TestExtractStoryPointsHelper(unittest.TestCase):
    """_extract_story_points: the configured field wins priority when passed."""

    def test_no_cfg_uses_hardcoded_candidates_only(self):
        fields = {"customfield_10016": 5.0}
        assert server._extract_story_points(fields) == 5.0

    def test_cfg_configured_field_not_in_hardcoded_list_wins(self):
        cfg = {"story_points_field": "customfield_99999"}
        fields = {"customfield_99999": 8.0, "customfield_10016": 3.0}
        # The configured field must win even though a hardcoded candidate
        # also has a value -- an operator who set JIRA_STORY_POINTS_FIELD
        # explicitly said which field is correct for their instance.
        assert server._extract_story_points(fields, cfg) == 8.0

    def test_cfg_configured_field_absent_falls_back(self):
        cfg = {"story_points_field": "customfield_99999"}
        fields = {"customfield_10016": 5.0}
        assert server._extract_story_points(fields, cfg) == 5.0

    def test_cfg_configured_field_equals_default_still_works(self):
        cfg = {"story_points_field": "customfield_10016"}
        fields = {"customfield_10016": 13.0}
        assert server._extract_story_points(fields, cfg) == 13.0

    def test_no_recognized_field_returns_zero(self):
        assert server._extract_story_points({"summary": "x"}) == 0.0


class TestSpFieldsParamHelper(unittest.TestCase):
    """_sp_fields_param: builds a fields= query fragment covering the
    configured Story Points field."""

    def test_default_cfg_no_duplicate(self):
        cfg = {"story_points_field": "customfield_10016"}
        result = server._sp_fields_param(cfg, "status")
        parts = result.split(",")
        assert parts[0] == "status"
        assert parts.count("customfield_10016") == 1

    def test_non_default_cfg_field_appended(self):
        cfg = {"story_points_field": "customfield_99999"}
        result = server._sp_fields_param(cfg, "summary,status")
        assert "customfield_99999" in result.split(",")

    def test_no_extra_still_includes_configured_field(self):
        cfg = {"story_points_field": "customfield_99999"}
        result = server._sp_fields_param(cfg)
        assert "customfield_99999" in result.split(",")


class TestConfiguredFieldEndToEnd(unittest.TestCase):
    """jira_get_epic: a non-default JIRA_STORY_POINTS_FIELD reaches both the
    outgoing Jira query AND the extracted story_points_total -- the exact
    gap found in review (write path was fixed, read path was not)."""

    def setUp(self):
        _set_env(extra={"JIRA_STORY_POINTS_FIELD": "customfield_99999"})

    def tearDown(self):
        _clear_env(extra=["JIRA_STORY_POINTS_FIELD"])

    @patch("urllib.request.urlopen")
    def test_configured_field_requested_and_summed(self, mock_urlopen):
        epic_detail = {
            "fields": {
                "summary": "Q1 Goals",
                "status": {"name": "In Progress"},
            }
        }
        stories = {
            "issues": [
                {"fields": {"status": {"name": "Done"}, "customfield_99999": 5.0}},
                {"fields": {"status": {"name": "To Do"}, "customfield_99999": 3.0}},
            ]
        }
        mock_urlopen.side_effect = [_make_resp(epic_detail), _make_resp(stories)]

        result = _parse(server.jira_get_epic("PROJ-42"))

        assert result["success"] is True
        assert result["story_points_total"] == 8.0
        assert result["done_story_count"] == 1

        # Second call is the linked-stories search -- its URL must request
        # the configured field, not just the hardcoded defaults.
        stories_req = mock_urlopen.call_args_list[1][0][0]
        stories_url = (
            stories_req.full_url if hasattr(stories_req, "full_url") else str(stories_req)
        )
        assert "customfield_99999" in stories_url


if __name__ == "__main__":
    unittest.main()
