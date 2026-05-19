"""
test_agile_client.py -- Unit tests for agile_client.py.

All HTTP calls are mocked via unittest.mock.patch('urllib.request.urlopen')
per CONTRACT #4. Target: 80%+ coverage.

Windows-Safe: ASCII only (cp1252 compatible)
"""

import base64
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agile_client import (
    _agile_url,
    _build_agile_auth_header,
    _agile_request,
    _AGILE_BASE,
)


def _make_mock_response(data, status=200):
    """Build a mock urllib response object returning JSON-encoded data.

    Args:
        data: Python dict to JSON-encode as response body.
        status: HTTP status code (unused by urlopen context manager directly).

    Returns:
        MagicMock configured to behave as a urllib response context manager.
    """
    encoded = json.dumps(data).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = encoded
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _make_empty_response():
    """Build a mock urllib response for 204 No Content (empty body).

    Returns:
        MagicMock configured to return empty bytes from read().
    """
    mock_resp = MagicMock()
    mock_resp.read.return_value = b""
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _basic_cfg():
    """Return a minimal Basic-auth config dict for test use.

    Returns:
        Config dict matching the shape from server._get_config().
    """
    return {
        "url": "https://test.atlassian.net",
        "user": "test@example.com",
        "token": "test-token-ascii-only",
        "api_version": "3",
        "auth_method": "basic",
    }


def _bearer_cfg():
    """Return a minimal Bearer-auth config dict for test use.

    Returns:
        Config dict with auth_method set to 'bearer'.
    """
    cfg = _basic_cfg()
    cfg["auth_method"] = "bearer"
    return cfg


# ---------------------------------------------------------------------------
# TestAgileUrl
# ---------------------------------------------------------------------------

class TestAgileUrl(unittest.TestCase):
    """Tests for _agile_url() URL construction."""

    def test_url_construction_simple_path(self):
        """Concatenates base URL, AGILE_BASE, and path correctly."""
        cfg = _basic_cfg()
        url = _agile_url(cfg, "board")
        assert url == "https://test.atlassian.net/rest/agile/1.0/board"

    def test_url_with_query_params(self):
        """Appends query string as part of the path segment."""
        cfg = _basic_cfg()
        url = _agile_url(cfg, "board/1/sprint?maxResults=50")
        assert url == "https://test.atlassian.net/rest/agile/1.0/board/1/sprint?maxResults=50"

    def test_url_contains_agile_base_prefix(self):
        """URL always contains /rest/agile/1.0 prefix."""
        cfg = _basic_cfg()
        url = _agile_url(cfg, "sprint/42/issue")
        assert "/rest/agile/1.0/" in url

    def test_path_does_not_double_slash(self):
        """No double slash between AGILE_BASE and path."""
        cfg = _basic_cfg()
        url = _agile_url(cfg, "rapid/charts/velocity")
        assert "//" not in url.replace("https://", "")


# ---------------------------------------------------------------------------
# TestBuildAgileAuthHeader
# ---------------------------------------------------------------------------

class TestBuildAgileAuthHeader(unittest.TestCase):
    """Tests for _build_agile_auth_header()."""

    def test_basic_auth_format(self):
        """Basic auth header starts with 'Basic ' and is Base64-encoded."""
        cfg = _basic_cfg()
        header = _build_agile_auth_header(cfg)
        assert header.startswith("Basic ")
        encoded_part = header[len("Basic "):]
        decoded = base64.b64decode(encoded_part).decode("utf-8")
        assert decoded == "test@example.com:test-token-ascii-only"

    def test_bearer_token_format(self):
        """Bearer auth header starts with 'Bearer ' and contains token verbatim."""
        cfg = _bearer_cfg()
        header = _build_agile_auth_header(cfg)
        assert header == "Bearer test-token-ascii-only"

    def test_basic_is_default_when_auth_method_basic(self):
        """auth_method 'basic' always produces Basic header."""
        cfg = _basic_cfg()
        cfg["auth_method"] = "basic"
        header = _build_agile_auth_header(cfg)
        assert header.startswith("Basic ")


# ---------------------------------------------------------------------------
# TestAgileRequest
# ---------------------------------------------------------------------------

class TestAgileRequest(unittest.TestCase):
    """Tests for _agile_request() covering GET, POST, 204, and error paths."""

    @patch("urllib.request.urlopen")
    def test_successful_get_returns_json(self, mock_urlopen):
        """Successful GET returns parsed JSON dict."""
        data = {"maxResults": 50, "total": 2, "values": [{"id": 1}]}
        mock_urlopen.return_value = _make_mock_response(data)
        result = _agile_request(_basic_cfg(), "GET", "board")
        assert result["total"] == 2
        assert len(result["values"]) == 1

    @patch("urllib.request.urlopen")
    def test_successful_post_returns_json(self, mock_urlopen):
        """Successful POST with body returns parsed JSON dict."""
        data = {"id": 99, "name": "Sprint 99", "state": "future"}
        mock_urlopen.return_value = _make_mock_response(data)
        body = {"originBoardId": 1, "name": "Sprint 99"}
        result = _agile_request(_basic_cfg(), "POST", "sprint", body=body)
        assert result["id"] == 99

    @patch("urllib.request.urlopen")
    def test_204_returns_none(self, mock_urlopen):
        """204 No Content (empty body) returns None."""
        mock_urlopen.return_value = _make_empty_response()
        result = _agile_request(_basic_cfg(), "POST", "sprint/10")
        assert result is None

    @patch("urllib.request.urlopen")
    def test_http_error_raises_runtime_error(self, mock_urlopen):
        """HTTP error response raises RuntimeError with status code in message."""
        err_body = json.dumps({"errorMessages": ["Sprint not found"], "errors": {}}).encode()
        http_err = HTTPError(
            url="https://test.atlassian.net/rest/agile/1.0/sprint/999",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=io.BytesIO(err_body),
        )
        mock_urlopen.side_effect = http_err
        with pytest.raises(RuntimeError, match="404"):
            _agile_request(_basic_cfg(), "GET", "sprint/999")

    @patch("urllib.request.urlopen")
    def test_http_error_message_included_in_runtime_error(self, mock_urlopen):
        """RuntimeError message includes the Jira error messages."""
        err_body = json.dumps({"errorMessages": ["Board does not exist"], "errors": {}}).encode()
        http_err = HTTPError(
            url="https://test.atlassian.net/rest/agile/1.0/board/999",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=io.BytesIO(err_body),
        )
        mock_urlopen.side_effect = http_err
        with pytest.raises(RuntimeError, match="Board does not exist"):
            _agile_request(_basic_cfg(), "GET", "board/999")

    @patch("urllib.request.urlopen")
    def test_path_prefix_is_agile_10(self, mock_urlopen):
        """The actual URL sent to urlopen contains /rest/agile/1.0/."""
        data = {"values": []}
        mock_urlopen.return_value = _make_mock_response(data)
        _agile_request(_basic_cfg(), "GET", "board")
        call_args = mock_urlopen.call_args
        req_obj = call_args[0][0]
        assert "/rest/agile/1.0/board" in req_obj.full_url

    @patch("urllib.request.urlopen")
    def test_authorization_header_set_in_request(self, mock_urlopen):
        """Authorization header is present in the outgoing request object."""
        data = {"values": []}
        mock_urlopen.return_value = _make_mock_response(data)
        _agile_request(_basic_cfg(), "GET", "board")
        call_args = mock_urlopen.call_args
        req_obj = call_args[0][0]
        assert "Authorization" in req_obj.headers

    @patch("urllib.request.urlopen")
    def test_bearer_auth_config_uses_bearer_header(self, mock_urlopen):
        """Bearer config produces Bearer Authorization header."""
        data = {"values": []}
        mock_urlopen.return_value = _make_mock_response(data)
        _agile_request(_bearer_cfg(), "GET", "board")
        call_args = mock_urlopen.call_args
        req_obj = call_args[0][0]
        auth = req_obj.headers.get("Authorization", "")
        assert auth.startswith("Bearer ")

    @patch("urllib.request.urlopen")
    def test_http_error_non_json_body_still_raises(self, mock_urlopen):
        """Non-JSON error body still raises RuntimeError with status code."""
        http_err = HTTPError(
            url="https://test.atlassian.net/rest/agile/1.0/sprint",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=io.BytesIO(b"Internal Server Error"),
        )
        mock_urlopen.side_effect = http_err
        with pytest.raises(RuntimeError, match="500"):
            _agile_request(_basic_cfg(), "GET", "sprint/1")
