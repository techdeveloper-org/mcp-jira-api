"""
test_workflow_tools.py -- Unit tests for jira_get_workflow_info and
jira_add_workflow_status (GitHub issue #9).

Groups:
  GROUP A: jira_get_workflow_info -- read-only scheme/workflow reporting
  GROUP B: jira_add_workflow_status -- shared-scheme safety refusal
  GROUP C: jira_add_workflow_status -- ambiguous-workflow safety refusal
  GROUP D: jira_add_workflow_status -- input validation (unknown statuses,
           duplicate status, missing insert_after/insert_before)
  GROUP E: jira_add_workflow_status -- happy path (mocked API responses)
  GROUP F: jira_add_workflow_status -- Jira validation rejection

Pattern (matches tests/test_tools_gaps.py):
  All @mcp_tool_handler tools return JSON strings.
  Tests always json.loads() the result and check result["success"].
  Tools are regular def (not async) -- called directly, no asyncio.run().
  Mock: @patch("urllib.request.urlopen"), sequential side_effect list in the
  exact order the tool under test issues its _request() calls.

Windows-Safe: ASCII only (cp1252 compatible)
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import server  # noqa: E402


# ---------------------------------------------------------------------------
# Shared helpers (duplicated from test_tools_gaps.py deliberately -- keeping
# each test module self-contained matches this repo's existing convention).
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


JIRA_ENV = {
    "JIRA_URL": "https://test.atlassian.net",
    "JIRA_USER": "test@example.com",
    "JIRA_API_TOKEN": "test-token-ascii",
    "JIRA_API_VERSION": "3",
}


def _set_env():
    for k, v in JIRA_ENV.items():
        os.environ[k] = v


def _clear_env():
    for k in JIRA_ENV:
        os.environ.pop(k, None)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _project_algo():
    return {"id": "10001", "key": "ALGO", "name": "AlgoSensei"}


def _project(project_id, key, name):
    return {"id": project_id, "key": key, "name": name}


def _scheme_not_shared():
    return {
        "values": [
            {
                "projectIds": ["10001"],
                "workflowScheme": {
                    "id": 5,
                    "name": "ALGO Workflow Scheme",
                    "defaultWorkflow": "ALGO Workflow",
                    "issueTypeMappings": {},
                },
            }
        ]
    }


def _scheme_shared():
    return {
        "values": [
            {
                "projectIds": ["10001", "10002", "10003"],
                "workflowScheme": {
                    "id": 5,
                    "name": "Shared Workflow Scheme",
                    "defaultWorkflow": "Shared Workflow",
                    "issueTypeMappings": {},
                },
            }
        ]
    }


def _scheme_ambiguous():
    return {
        "values": [
            {
                "projectIds": ["10001"],
                "workflowScheme": {
                    "id": 6,
                    "name": "ALGO Multi Workflow Scheme",
                    "defaultWorkflow": "Workflow A",
                    "issueTypeMappings": {"10000": "Workflow B"},
                },
            }
        ]
    }


def _scheme_empty_values():
    return {"values": []}


def _workflow_detail(workflow_name="ALGO Workflow"):
    return {
        "values": [
            {
                "id": {"name": workflow_name},
                "statuses": [
                    {"id": "1", "name": "To Do"},
                    {"id": "2", "name": "In Progress"},
                    {"id": "3", "name": "Done"},
                ],
                "transitions": [
                    {
                        "id": "11",
                        "name": "Start Progress",
                        "from": [{"name": "To Do"}],
                        "to": {"name": "In Progress"},
                        "type": "directed",
                    },
                    {
                        "id": "12",
                        "name": "Done",
                        "from": [{"name": "In Progress"}],
                        "to": {"name": "Done"},
                        "type": "directed",
                    },
                ],
            }
        ]
    }


def _validation_ok():
    return {"errorMessages": [], "errors": []}


def _validation_rejected():
    return {"errorMessages": ["Transition must specify a links field."]}


def _update_ok():
    return {}


# ---------------------------------------------------------------------------
# GROUP A: jira_get_workflow_info
# ---------------------------------------------------------------------------


class TestJiraGetWorkflowInfo(unittest.TestCase):
    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_not_shared_reports_is_shared_false(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _make_resp(_project_algo()),
            _make_resp(_scheme_not_shared()),
            _make_resp(_workflow_detail()),
        ]
        result = _parse(server.jira_get_workflow_info(project_key="ALGO"))

        self.assertTrue(result["success"])
        self.assertFalse(result["is_shared"])
        self.assertEqual(result["shared_with_project_count"], 0)
        self.assertEqual(result["shared_with_projects"], [])
        self.assertEqual(result["workflow_names"], ["ALGO Workflow"])
        self.assertEqual(len(result["workflows"]), 1)
        self.assertEqual(len(result["workflows"][0]["statuses"]), 3)
        self.assertNotIn("safety_note", result)

    @patch("urllib.request.urlopen")
    def test_shared_reports_other_projects(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _make_resp(_project_algo()),
            _make_resp(_scheme_shared()),
            _make_resp(_workflow_detail("Shared Workflow")),
            _make_resp(_project("10002", "FAB", "Fabrication")),
            _make_resp(_project("10003", "SCRUM", "Scrum Team")),
        ]
        result = _parse(server.jira_get_workflow_info(project_key="ALGO"))

        self.assertTrue(result["success"])
        self.assertTrue(result["is_shared"])
        self.assertEqual(result["shared_with_project_count"], 2)
        self.assertIn("FAB (Fabrication)", result["shared_with_projects"])
        self.assertIn("SCRUM (Scrum Team)", result["shared_with_projects"])
        self.assertIn("safety_note", result)
        self.assertIn("confirm_shared_scheme_edit", result["safety_note"])

    @patch("urllib.request.urlopen")
    def test_no_scheme_association_raises(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _make_resp(_project_algo()),
            _make_resp(_scheme_empty_values()),
        ]
        result = _parse(server.jira_get_workflow_info(project_key="ALGO"))

        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "RuntimeError")

    @patch("urllib.request.urlopen")
    def test_server_dc_configuration_refused(self, mock_urlopen):
        os.environ["JIRA_API_VERSION"] = "2"
        result = _parse(server.jira_get_workflow_info(project_key="ALGO"))

        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "RuntimeError")
        self.assertIn("Jira Cloud", result["error"])
        mock_urlopen.assert_not_called()


# ---------------------------------------------------------------------------
# GROUP B: jira_add_workflow_status -- shared-scheme safety refusal
# ---------------------------------------------------------------------------


class TestJiraAddWorkflowStatusSharedSchemeRefusal(unittest.TestCase):
    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_refuses_shared_scheme_without_confirmation(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _make_resp(_project_algo()),
            _make_resp(_scheme_shared()),
            _make_resp(_project("10002", "FAB", "Fabrication")),
            _make_resp(_project("10003", "SCRUM", "Scrum Team")),
        ]
        result = _parse(server.jira_add_workflow_status(
            project_key="ALGO",
            status_name="In Review",
            insert_after_status="In Progress",
            insert_before_status="Done",
        ))

        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "SHARED_WORKFLOW_SCHEME_REFUSED")
        self.assertIn("FAB (Fabrication)", result["shared_with_projects"])
        self.assertIn("SCRUM (Scrum Team)", result["shared_with_projects"])
        # Safety-critical: the mutation calls (validate/update) must never be
        # reached. Only 4 urlopen calls were queued above; if the tool made a
        # 5th call, side_effect would raise StopIteration and this test would
        # fail with that error rather than silently passing.
        self.assertEqual(mock_urlopen.call_count, 4)

    @patch("urllib.request.urlopen")
    def test_proceeds_past_shared_scheme_with_confirmation(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _make_resp(_project_algo()),
            _make_resp(_scheme_shared()),
            _make_resp(_workflow_detail("Shared Workflow")),
            _make_resp(_validation_ok()),
            _make_resp(_update_ok()),
        ]
        result = _parse(server.jira_add_workflow_status(
            project_key="ALGO",
            status_name="In Review",
            insert_after_status="In Progress",
            insert_before_status="Done",
            confirm_shared_scheme_edit=True,
        ))

        self.assertTrue(result["success"])
        self.assertTrue(result["applied"])
        self.assertEqual(result["workflow_name"], "Shared Workflow")


# ---------------------------------------------------------------------------
# GROUP C: jira_add_workflow_status -- ambiguous-workflow safety refusal
# ---------------------------------------------------------------------------


class TestJiraAddWorkflowStatusAmbiguousWorkflow(unittest.TestCase):
    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_refuses_ambiguous_workflow_without_explicit_name(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _make_resp(_project_algo()),
            _make_resp(_scheme_ambiguous()),
        ]
        result = _parse(server.jira_add_workflow_status(
            project_key="ALGO",
            status_name="In Review",
            insert_after_status="In Progress",
            insert_before_status="Done",
        ))

        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "AMBIGUOUS_WORKFLOW")
        self.assertEqual(
            sorted(result["available_workflow_names"]),
            ["Workflow A", "Workflow B"],
        )

    @patch("urllib.request.urlopen")
    def test_unknown_explicit_workflow_name_raises(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _make_resp(_project_algo()),
            _make_resp(_scheme_ambiguous()),
        ]
        result = _parse(server.jira_add_workflow_status(
            project_key="ALGO",
            status_name="In Review",
            insert_after_status="In Progress",
            insert_before_status="Done",
            workflow_name="Workflow Nonexistent",
        ))

        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "ValueError")


# ---------------------------------------------------------------------------
# GROUP D: jira_add_workflow_status -- input validation
# ---------------------------------------------------------------------------


class TestJiraAddWorkflowStatusValidation(unittest.TestCase):
    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    def test_missing_both_insert_points_raises_before_any_network_call(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            result = _parse(server.jira_add_workflow_status(
                project_key="ALGO",
                status_name="In Review",
            ))
            self.assertFalse(result["success"])
            self.assertEqual(result["error_type"], "ValueError")
            mock_urlopen.assert_not_called()

    def test_invalid_status_category_raises_before_any_network_call(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            result = _parse(server.jira_add_workflow_status(
                project_key="ALGO",
                status_name="In Review",
                insert_after_status="In Progress",
                status_category="NOT_A_CATEGORY",
            ))
            self.assertFalse(result["success"])
            self.assertEqual(result["error_type"], "ValueError")
            mock_urlopen.assert_not_called()

    @patch("urllib.request.urlopen")
    def test_unknown_insert_after_status_raises(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _make_resp(_project_algo()),
            _make_resp(_scheme_not_shared()),
            _make_resp(_workflow_detail()),
        ]
        result = _parse(server.jira_add_workflow_status(
            project_key="ALGO",
            status_name="In Review",
            insert_after_status="Does Not Exist",
        ))

        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "ValueError")
        self.assertIn("Does Not Exist", result["error"])

    @patch("urllib.request.urlopen")
    def test_duplicate_status_name_raises(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _make_resp(_project_algo()),
            _make_resp(_scheme_not_shared()),
            _make_resp(_workflow_detail()),
        ]
        result = _parse(server.jira_add_workflow_status(
            project_key="ALGO",
            status_name="In Progress",  # already exists
            insert_after_status="To Do",
        ))

        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "ValueError")
        self.assertIn("already exists", result["error"])


# ---------------------------------------------------------------------------
# GROUP E: jira_add_workflow_status -- happy path
# ---------------------------------------------------------------------------


class TestJiraAddWorkflowStatusHappyPath(unittest.TestCase):
    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_inserts_between_two_statuses(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _make_resp(_project_algo()),
            _make_resp(_scheme_not_shared()),
            _make_resp(_workflow_detail()),
            _make_resp(_validation_ok()),
            _make_resp(_update_ok()),
        ]
        result = _parse(server.jira_add_workflow_status(
            project_key="ALGO",
            status_name="In Review",
            insert_after_status="In Progress",
            insert_before_status="Done",
        ))

        self.assertTrue(result["success"])
        self.assertEqual(result["workflow_name"], "ALGO Workflow")
        self.assertEqual(result["status_name"], "In Review")
        self.assertEqual(result["status_category"], "IN_PROGRESS")
        self.assertTrue(result["validated"])
        self.assertTrue(result["applied"])
        self.assertIn("In Review", result["transitions_added"])
        self.assertIn("Done", result["transitions_added"])

    @patch("urllib.request.urlopen")
    def test_validate_only_does_not_call_update_endpoint(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _make_resp(_project_algo()),
            _make_resp(_scheme_not_shared()),
            _make_resp(_workflow_detail()),
            _make_resp(_validation_ok()),
        ]
        result = _parse(server.jira_add_workflow_status(
            project_key="ALGO",
            status_name="In Review",
            insert_after_status="In Progress",
            insert_before_status="Done",
            validate_only=True,
        ))

        self.assertTrue(result["success"])
        self.assertTrue(result["validated"])
        self.assertFalse(result["applied"])
        # Only 4 calls queued: a 5th (the update call) would raise
        # StopIteration if the tool called it despite validate_only=True.
        self.assertEqual(mock_urlopen.call_count, 4)

    @patch("urllib.request.urlopen")
    def test_insert_after_only_produces_single_transition(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _make_resp(_project_algo()),
            _make_resp(_scheme_not_shared()),
            _make_resp(_workflow_detail()),
            _make_resp(_validation_ok()),
            _make_resp(_update_ok()),
        ]
        result = _parse(server.jira_add_workflow_status(
            project_key="ALGO",
            status_name="Blocked",
            insert_after_status="In Progress",
        ))

        self.assertTrue(result["success"])
        self.assertEqual(result["transitions_added"], ["Blocked"])

    def test_idempotency_key_replays_recorded_result(self):
        # The idempotency store defaults to ~/.claude/memory/mcp-idempotency,
        # which is real state on a developer's machine. This test has never
        # run against this namespace before (no other test in this repo
        # exercises jira_add_workflow_status's idempotency path), so rather
        # than write there and clean up afterward, MCP_IDEMPOTENCY_DIR is
        # pointed at a throwaway temp directory for the duration of the test.
        tmp_dir = tempfile.mkdtemp(prefix="mcp-jira-idempotency-test-")
        os.environ["MCP_IDEMPOTENCY_DIR"] = tmp_dir
        try:
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_urlopen.side_effect = [
                    _make_resp(_project_algo()),
                    _make_resp(_scheme_not_shared()),
                    _make_resp(_workflow_detail()),
                    _make_resp(_validation_ok()),
                    _make_resp(_update_ok()),
                ]
                key = "test-add-workflow-status-key-1"
                first = _parse(server.jira_add_workflow_status(
                    project_key="ALGO",
                    status_name="In Review",
                    insert_after_status="In Progress",
                    insert_before_status="Done",
                    idempotency_key=key,
                ))
                self.assertTrue(first["success"])
                self.assertFalse(first["idempotent_replay"])

                calls_before_replay = mock_urlopen.call_count
                second = _parse(server.jira_add_workflow_status(
                    project_key="ALGO",
                    status_name="In Review",
                    insert_after_status="In Progress",
                    insert_before_status="Done",
                    idempotency_key=key,
                ))
                self.assertTrue(second["success"])
                self.assertTrue(second["idempotent_replay"])
                # No additional urlopen calls made on replay -- the recorded
                # result was returned without re-invoking the Jira API.
                self.assertEqual(mock_urlopen.call_count, calls_before_replay)
        finally:
            os.environ.pop("MCP_IDEMPOTENCY_DIR", None)
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# GROUP F: jira_add_workflow_status -- Jira validation rejection
# ---------------------------------------------------------------------------


class TestJiraAddWorkflowStatusValidationRejected(unittest.TestCase):
    def setUp(self):
        _set_env()

    def tearDown(self):
        _clear_env()

    @patch("urllib.request.urlopen")
    def test_validation_errors_surface_and_block_update(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _make_resp(_project_algo()),
            _make_resp(_scheme_not_shared()),
            _make_resp(_workflow_detail()),
            _make_resp(_validation_rejected()),
        ]
        result = _parse(server.jira_add_workflow_status(
            project_key="ALGO",
            status_name="In Review",
            insert_after_status="In Progress",
            insert_before_status="Done",
        ))

        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "RuntimeError")
        self.assertIn("links field", result["error"])
        # Only 4 calls queued: a 5th (the update call) would raise
        # StopIteration if the tool applied a payload Jira rejected.
        self.assertEqual(mock_urlopen.call_count, 4)


if __name__ == "__main__":
    unittest.main()
