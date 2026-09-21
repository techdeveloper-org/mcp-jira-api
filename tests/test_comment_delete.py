"""
test_comment_delete.py -- Unit tests for jira_delete_comment.

Added to clean up duplicate comments the gap in jira_list_comments (#12)
exposed: DSHN-74 and DSHN-75 in a real Dashanan session each carried a
duplicate disclosure comment, posted because nothing could read comments
back before this tool existed. Fixes techdeveloper-org/mcp-jira-api#13.

Pattern: mirrors tests/test_comment_read.py exactly.

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


def _make_empty_resp():
    """Build a urlopen context-manager mock returning an empty 204 body."""
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


class TestDeleteCommentSuccess(unittest.TestCase):
    """jira_delete_comment: a real 204 delete succeeds cleanly."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_delete_returns_success_on_204(self, mock_urlopen):
        mock_urlopen.return_value = _make_empty_resp()

        result = _parse(server.jira_delete_comment("PROJ-123", "10464"))

        assert result["success"] is True
        assert result["issue_key"] == "PROJ-123"
        assert result["comment_id"] == "10464"
        assert result["deleted"] is True

    @patch("urllib.request.urlopen")
    def test_delete_uses_delete_method_on_correct_path(self, mock_urlopen):
        mock_urlopen.return_value = _make_empty_resp()

        _parse(server.jira_delete_comment("PROJ-123", "10464"))

        req = mock_urlopen.call_args[0][0]
        assert req.get_method() == "DELETE"
        url = req.full_url if hasattr(req, "full_url") else str(req)
        assert "/issue/PROJ-123/comment/10464" in url


class TestDeleteCommentErrorPropagation(unittest.TestCase):
    """jira_delete_comment: an already-deleted or nonexistent comment errors out."""

    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_comment_not_found_404_returns_failure(self, mock_urlopen):
        """Deleting an already-deleted/nonexistent comment is a real error, not
        silently treated as success -- the caller should know it did nothing."""
        err = urllib.error.HTTPError(
            url="https://test.atlassian.net/rest/api/3/issue/PROJ-1/comment/99999",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )
        err.read = lambda: b'{"errorMessages":["Comment does not exist"],"errors":{}}'
        mock_urlopen.side_effect = err

        result = _parse(server.jira_delete_comment("PROJ-1", "99999"))

        assert result["success"] is False
        assert "error" in result


if __name__ == "__main__":
    unittest.main()
