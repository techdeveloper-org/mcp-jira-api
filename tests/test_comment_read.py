"""
test_comment_read.py -- Unit tests for jira_list_comments.

Covers the gap found in a real Dashanan session: two agents both needed to
check whether a comment already existed on a ticket before posting one;
jira_add_comment could write but nothing could read one back, and
jira_get_issue(fields="comment") silently returned a blanked-out response
instead of comment data (see server.py's jira_list_comments docstring for
the root cause). Fixes techdeveloper-org/mcp-jira-api#12.

Pattern:
  All @mcp_tool_handler tools return JSON strings.
  Tests always json.loads() the result and check result["success"].
  Mock: @patch("urllib.request.urlopen")
  Request body inspection: json.loads(req.data.decode("utf-8"))
  GET query-string inspection: req.full_url (see TestConfiguredFieldEndToEnd
    in test_issue_extra_fields.py for the established pattern this mirrors)

Windows-Safe: ASCII only (cp1252 compatible)
"""

import json
import sys
import unittest
import urllib.error
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


def _adf_comment(text):
    """Build a Cloud-shaped ADF comment body for one plain-text paragraph."""
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": text}]}
        ],
    }


class TestListCommentsDecoding(unittest.TestCase):
    """jira_list_comments: comment bodies decode correctly for both API shapes."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_single_page_decodes_adf_and_plain_string_bodies(self, mock_urlopen):
        """One ADF-shaped body (Cloud) and one plain-string body (Server) both
        decode to plain text via the same _adf_to_text reused from jira_get_issue."""
        mock_urlopen.return_value = _make_resp({
            "comments": [
                {
                    "id": "10001",
                    "author": {"displayName": "Alice"},
                    "body": _adf_comment("First comment"),
                    "created": "2026-09-21T10:00:00.000+0000",
                    "updated": "2026-09-21T10:00:00.000+0000",
                },
                {
                    "id": "10002",
                    "author": {"name": "bob"},
                    "body": "Second comment (Server v2 plain string)",
                    "created": "2026-09-21T11:00:00.000+0000",
                    "updated": "2026-09-21T11:00:00.000+0000",
                },
            ],
            "startAt": 0,
            "maxResults": 50,
            "total": 2,
        })

        result = _parse(server.jira_list_comments("PROJ-123"))

        assert result["success"] is True
        assert result["issue_key"] == "PROJ-123"
        assert result["count"] == 2
        assert result["total"] == 2
        assert result["comments"][0]["comment_id"] == "10001"
        assert result["comments"][0]["author"] == "Alice"
        assert result["comments"][0]["body"] == "First comment"
        assert result["comments"][1]["author"] == "bob"
        assert result["comments"][1]["body"] == "Second comment (Server v2 plain string)"

    @patch("urllib.request.urlopen")
    def test_empty_comments_returns_count_zero_not_an_error(self, mock_urlopen):
        """An issue with no comments is a normal, successful empty result."""
        mock_urlopen.return_value = _make_resp({
            "comments": [], "startAt": 0, "maxResults": 50, "total": 0,
        })

        result = _parse(server.jira_list_comments("PROJ-456"))

        assert result["success"] is True
        assert result["count"] == 0
        assert result["total"] == 0
        assert result["comments"] == []


class TestListCommentsPagination(unittest.TestCase):
    """jira_list_comments: start_at/max_results forwarded and clamped correctly."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_start_at_and_max_results_forwarded_in_query_string(self, mock_urlopen):
        mock_urlopen.return_value = _make_resp({
            "comments": [], "startAt": 25, "maxResults": 10, "total": 40,
        })

        result = _parse(server.jira_list_comments("PROJ-1", start_at=25, max_results=10))

        assert result["success"] is True
        req = mock_urlopen.call_args[0][0]
        url = req.full_url if hasattr(req, "full_url") else str(req)
        assert "startAt=25" in url
        assert "maxResults=10" in url

    @patch("urllib.request.urlopen")
    def test_max_results_clamped_at_100(self, mock_urlopen):
        mock_urlopen.return_value = _make_resp({
            "comments": [], "startAt": 0, "maxResults": 100, "total": 0,
        })

        result = _parse(server.jira_list_comments("PROJ-1", max_results=500))

        assert result["success"] is True
        req = mock_urlopen.call_args[0][0]
        url = req.full_url if hasattr(req, "full_url") else str(req)
        assert "maxResults=100" in url
        assert "maxResults=500" not in url


class TestListCommentsErrorPropagation(unittest.TestCase):
    """jira_list_comments: a real Jira API error is not swallowed."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_issue_not_found_404_returns_failure(self, mock_urlopen):
        """404 on a nonexistent issue returns success=False, not a crash or an
        empty comment list masquerading as success."""
        err = urllib.error.HTTPError(
            url="https://test.atlassian.net/rest/api/3/issue/NOPE-1/comment",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )
        err.read = lambda: b'{"errorMessages":["Issue does not exist"],"errors":{}}'
        mock_urlopen.side_effect = err

        result = _parse(server.jira_list_comments("NOPE-1"))

        assert result["success"] is False
        assert "error" in result


if __name__ == "__main__":
    unittest.main()
