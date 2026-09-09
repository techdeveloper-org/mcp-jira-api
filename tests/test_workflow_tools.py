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
import uuid
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


WORKFLOW_ENTITY_ID = "c5ef565c-1b1e-427e-bc3b-e677b0dc027c"
WORKFLOW_VERSION_ID = "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
WORKFLOW_VERSION_NUMBER = 1

_STATUS_REF_TODO = "10001"
_STATUS_REF_IN_PROGRESS = "10002"
_STATUS_REF_DONE = "10003"


def _workflow_detail(
    workflow_name="ALGO Workflow",
    entity_id=WORKFLOW_ENTITY_ID,
    version_id=WORKFLOW_VERSION_ID,
    version_number=WORKFLOW_VERSION_NUMBER,
):
    """Build a GET /workflows/search (plural) response.

    Matches the real ``WorkflowSearchResponse`` / ``JiraWorkflow`` schemas
    (confirmed 2026-09-08, GitHub issue #10, by downloading and parsing the
    full swagger-v3.v3.json spec locally, cross-checked against the actual
    example response body in that spec for this endpoint): a top-level
    "statuses" catalog whose entries carry both "id" (the real Jira status
    id) and "statusReference" -- and the spec's own example response shows
    these two fields holding the *same* value for every status ("id":
    "10003", "statusReference": "10003", etc), which is what
    _fetch_workflow_detail's status_catalog lookup (keyed by "id", queried
    by the workflow-level "statusReference") depends on to resolve a
    status's name/category at all. Using two different-looking values here
    (an earlier version of this fixture used "1"/"2"/"3" ids alongside
    unrelated UUID statusReferences) silently produces a status_catalog
    that never matches, leaving every status name None and
    existing_by_lower empty -- the actual production lookup logic was
    correct; only this fixture's data was unrealistic. "values" holds one
    JiraWorkflow per match, whose own "id" is the workflow's entityId (a
    UUID string, not its display name), "version" is the real {"id",
    "versionNumber"} object used for optimistic locking, "statuses" is a
    list of {"statusReference"} entries pointing into the top-level
    catalog, and "transitions" carries "toStatusReference" plus "links":
    [{"fromStatusReference"}] rather than the older singular endpoint's
    name-based "from"/"to" shape. _fetch_workflow_detail also filters
    "values" by matching "name" against the requested workflow_name --
    omitting "name" here makes every match fail and _fetch_workflow_detail
    raise "Workflow not found", which jira_get_workflow_info silently
    swallows into workflow_detail_errors, so "name" is required here too.
    """
    return {
        "statuses": [
            {
                "id": _STATUS_REF_TODO,
                "statusReference": _STATUS_REF_TODO,
                "name": "To Do",
                "statusCategory": "TODO",
            },
            {
                "id": _STATUS_REF_IN_PROGRESS,
                "statusReference": _STATUS_REF_IN_PROGRESS,
                "name": "In Progress",
                "statusCategory": "IN_PROGRESS",
            },
            {
                "id": _STATUS_REF_DONE,
                "statusReference": _STATUS_REF_DONE,
                "name": "Done",
                "statusCategory": "DONE",
            },
        ],
        "values": [
            {
                "id": entity_id,
                "name": workflow_name,
                "version": {"id": version_id, "versionNumber": version_number},
                "isEditable": True,
                "statuses": [
                    {"statusReference": _STATUS_REF_TODO},
                    {"statusReference": _STATUS_REF_IN_PROGRESS},
                    {"statusReference": _STATUS_REF_DONE},
                ],
                "transitions": [
                    {
                        "id": "11",
                        "name": "Start Progress",
                        "type": "DIRECTED",
                        "toStatusReference": _STATUS_REF_IN_PROGRESS,
                        "links": [{"fromStatusReference": _STATUS_REF_TODO}],
                    },
                    {
                        "id": "12",
                        "name": "Done",
                        "type": "DIRECTED",
                        "toStatusReference": _STATUS_REF_DONE,
                        "links": [{"fromStatusReference": _STATUS_REF_IN_PROGRESS}],
                    },
                ],
            }
        ],
    }


def _workflow_detail_missing_identity(workflow_name="ALGO Workflow"):
    """A GET /workflows/search response entry missing "id" and "version".

    Regression fixture for GitHub issue #10: the pre-fix code did not
    require either field, so a Jira response shaped like this (or a stub
    server/proxy that omits them) would silently send a broken payload
    ("id" as a display name, no "version") instead of failing loudly.
    """
    detail = _workflow_detail(workflow_name)
    entry = dict(detail["values"][0])
    entry.pop("id", None)
    entry.pop("version", None)
    return {"statuses": detail["statuses"], "values": [entry]}


def _decode_request_body(call):
    """Decode the JSON body of one mocked urlopen call's Request object."""
    req = call.args[0]
    return json.loads(req.data.decode("utf-8"))


def _validation_ok():
    """A clean POST /workflows/update/validation response (no errors)."""
    return {"errors": []}


def _validation_rejected():
    """A POST /workflows/update/validation response with one ERROR-level entry.

    Matches the real ``WorkflowValidationErrorList`` schema (confirmed
    2026-09-08, GitHub issue #10, from swagger-v3.v3.json): always
    ``{"errors": [{"message": ..., "level": "WARNING"|"ERROR"}]}``, never
    the ``errorMessages`` key an earlier version of this fixture used --
    that shape is silently ignored by _extract_workflow_validation_errors
    (validation.get("errors") returns None -> treated as no errors at
    all), so a fixture built that way cannot actually exercise the
    validation-rejection code path it is meant to test.
    """
    return {
        "errors": [
            {
                "message": "Transition must specify a links field.",
                "level": "ERROR",
            }
        ]
    }


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

    @patch("urllib.request.urlopen")
    def test_validation_payload_carries_entity_id_version_and_uuid_refs(
        self, mock_urlopen
    ):
        """GitHub issue #10 regression: the payload sent to Jira's validation
        endpoint must identify the workflow by its real entityId + version
        (not its display name, and not omit version), and every
        statusReference must be UUID-formatted (not a plain label like
        "after-status") -- both were the actual cause of the original
        payload's 400 rejection.
        """
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

        validate_call = mock_urlopen.call_args_list[3]
        # POST /workflows/update/validation's body is a
        # WorkflowUpdateValidateRequestBean -- {"payload": <the actual
        # WorkflowUpdateRequest>} -- not the WorkflowUpdateRequest directly
        # (GitHub issue #10 round 3, fix #3). Only the mutation call
        # (POST /workflows/update) takes the request body unwrapped.
        envelope = _decode_request_body(validate_call)
        payload = envelope["payload"]

        self.assertEqual(len(payload["workflows"]), 1)
        workflow_entry = payload["workflows"][0]
        self.assertEqual(workflow_entry["id"], WORKFLOW_ENTITY_ID)
        self.assertEqual(
            workflow_entry["version"],
            {"id": WORKFLOW_VERSION_ID, "versionNumber": WORKFLOW_VERSION_NUMBER},
        )

        for status_entry in payload["statuses"]:
            uuid.UUID(status_entry["statusReference"])  # raises ValueError if not a UUID
        for status_entry in workflow_entry["statuses"]:
            uuid.UUID(status_entry["statusReference"])
        for transition in workflow_entry["transitions"]:
            # toStatusReference lives on the transition itself, not inside
            # links[] (GitHub issue #10 round 3, fix #2) -- links[] only
            # carries fromStatusReference/fromPort/toPort.
            uuid.UUID(transition["toStatusReference"])
            for link in transition["links"]:
                uuid.UUID(link["fromStatusReference"])

    @patch("urllib.request.urlopen")
    def test_new_transitions_carry_sequential_positive_integer_ids_above_existing(
        self, mock_urlopen
    ):
        """GitHub issue #10, round 8 (rounds 4-7 were all wrong on the "id"
        field's format, each live-verified against the real ALGO project):

        - Round 4: hyphenated uuid4() -> "Invalid format".
        - Round 5: omitted "id" entirely -> regressed to round 3's "Missing
          required field" error -- "id" is required after all.
        - Round 6: uuid4().hex (no hyphens) -> same "Invalid format" as
          round 4 -- the field rejects UUID-shaped values generally.
        - Round 7: sequential negative integers -> same "Invalid format" --
          the negative sign was rejected too.

        Round 8: jira_get_workflow_info against the real ALGO project shows
        this workflow's actual transition ids are plain positive decimal
        integers ("1", "11", "21", "31"). Sequential positive integers,
        starting comfortably above any id already present (this fixture's
        existing transitions use "11" and "12"), validated cleanly live.
        """
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

        validate_call = mock_urlopen.call_args_list[3]
        # See test_validation_payload_carries_entity_id_version_and_uuid_refs
        # for why the validation call's body must be unwrapped via "payload".
        envelope = _decode_request_body(validate_call)
        transitions = envelope["payload"]["workflows"][0]["transitions"]

        # The payload now carries the FULL transition graph (existing +
        # new), not just a delta -- see this module's Round 8 header comment
        # in server.py for why a delta-only payload is silently treated as
        # the entire workflow definition by Jira. This fixture's existing
        # workflow has 2 transitions ("11" Start Progress, "12" Done); this
        # call adds 2 more.
        self.assertEqual(len(transitions), 4)
        existing_ids = {"11", "12"}
        new_ids = [t["id"] for t in transitions if t["id"] not in existing_ids]
        self.assertEqual(len(new_ids), 2)
        seen_ids = set()
        for transition_id in new_ids:
            self.assertRegex(transition_id, r"^[0-9]+$")
            self.assertGreater(int(transition_id), 12, "must not collide with an existing id")
            seen_ids.add(transition_id)
        self.assertEqual(len(seen_ids), 2, "each new transition must get a distinct local id")

    @patch("urllib.request.urlopen")
    def test_missing_entity_id_or_version_raises_instead_of_guessing(
        self, mock_urlopen
    ):
        """GitHub issue #10 regression: if the workflow-detail fetch cannot
        produce a real entityId/version, the tool must fail loudly rather
        than fall back to sending the workflow's display name as "id" (the
        original defect) or omitting "version" from the payload.
        """
        mock_urlopen.side_effect = [
            _make_resp(_project_algo()),
            _make_resp(_scheme_not_shared()),
            _make_resp(_workflow_detail_missing_identity()),
        ]
        result = _parse(server.jira_add_workflow_status(
            project_key="ALGO",
            status_name="In Review",
            insert_after_status="In Progress",
            insert_before_status="Done",
        ))

        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "RuntimeError")
        self.assertIn("entityId/version", result["error"])
        # Only 3 calls queued: a 4th (the validate call) would raise
        # StopIteration if the tool proceeded to build/send a payload
        # despite missing identity fields.
        self.assertEqual(mock_urlopen.call_count, 3)

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
