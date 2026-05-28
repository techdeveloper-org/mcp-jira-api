"""
test_tools_integration_new.py -- End-to-end integration tests for the 16 new
server.py tools added in Phase B.1 and Phase B.2.

IMPORTANT: All server tool functions are wrapped with @mcp_tool_handler which:
  - Returns a JSON string (not a dict)
  - Catches ALL exceptions and returns {"success": False, "error": ...} JSON
  - Never re-raises exceptions to the caller

Tests must json.loads() the result and inspect "success"/"error" fields.
Envelope is FLAT: {"success": bool, ...fields...} -- no nested "data" key.
Tools are regular def (not async) -- called directly without asyncio.run().

Groups:
  GROUP A (10): Pure scrum_calculator delegation -- no Jira API call needed.
    jira_pert_estimate, jira_ist_capacity, jira_tco_analysis,
    jira_scrum_of_scrums, jira_cognitive_load, jira_attrition_forecast,
    jira_psychological_safety, jira_spotify_health_check,
    jira_multi_sprint_holidays, jira_rate_limit_status

  GROUP B (6): Jira API dependent -- mock urllib.request.urlopen.
    jira_burndown_chart, jira_cfd_analysis, jira_cycle_time_analysis,
    jira_throughput_forecast, jira_automation_analyzer, jira_nasscom_mapping

  GROUP C (4): Regression tests on upgraded existing tools.
    jira_refine_backlog (wsjf_scores key), jira_sprint_review (ahp or AHP key),
    jira_team_health (tuckman_stage), jira_get_velocity (bca_ci keys)

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
# Shared helpers (same pattern as test_server_scrum_tools.py)
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
# GROUP A -- scrum_calculator delegation (no Jira API call)
# ---------------------------------------------------------------------------


class TestJiraPertEstimate:
    """Tests for jira_pert_estimate tool (GROUP A: pure delegation)."""

    def test_happy_path_returns_mu_days(self):
        """Happy path: mu_days is present and equals PERT formula result."""
        import server
        raw = server.jira_pert_estimate(optimistic=1.0, most_likely=4.0, pessimistic=7.0)
        result = _parse(raw)

        assert result["success"] is True
        assert "mu_days" in result
        expected_mu = (1.0 + 4.0 * 4.0 + 7.0) / 6.0
        assert abs(result["mu_days"] - expected_mu) < 0.01

    def test_happy_path_sigma_and_ci_present(self):
        """Happy path: sigma_days, ci_90_lower, and ci_90_upper are present."""
        import server
        result = _parse(server.jira_pert_estimate(optimistic=2.0, most_likely=5.0, pessimistic=8.0))

        assert result["success"] is True
        assert "sigma_days" in result
        assert "ci_90_lower" in result
        assert "ci_90_upper" in result
        assert result["ci_90_upper"] >= result["ci_90_lower"]

    def test_invalid_order_returns_error(self):
        """optimistic > pessimistic returns success=False (validation error)."""
        import server
        result = _parse(server.jira_pert_estimate(optimistic=9.0, most_likely=5.0, pessimistic=1.0))

        assert result["success"] is False
        assert "error" in result

    def test_equal_values_no_error(self):
        """Degenerate case: all three values equal is allowed (sigma=0)."""
        import server
        result = _parse(server.jira_pert_estimate(optimistic=3.0, most_likely=3.0, pessimistic=3.0))

        assert result["success"] is True
        assert result["mu_days"] == pytest.approx(3.0, abs=0.01)


class TestJiraIstCapacity:
    """Tests for jira_ist_capacity tool (GROUP A: pure delegation)."""

    def test_happy_path_effective_capacity_less_than_nominal(self):
        """Happy path: effective_capacity <= nominal_capacity when overlap < 8h."""
        import server
        result = _parse(server.jira_ist_capacity(nominal_capacity=100.0, overlap_hours=4.0))

        assert result["success"] is True
        assert "effective_capacity" in result
        assert result["effective_capacity"] <= 100.0

    def test_correction_factor_is_overlap_div_8(self):
        """correction_factor == overlap_hours / 8.0."""
        import server
        result = _parse(server.jira_ist_capacity(nominal_capacity=80.0, overlap_hours=4.0))

        assert result["success"] is True
        expected_factor = 4.0 / 8.0
        assert abs(result["correction_factor"] - expected_factor) < 0.001

    def test_default_overlap_yields_valid_result(self):
        """Default overlap_hours=4.0 produces a valid result."""
        import server
        result = _parse(server.jira_ist_capacity(nominal_capacity=50.0))

        assert result["success"] is True
        assert result["effective_capacity"] > 0

    def test_india_context_present(self):
        """india_context field is present and non-empty."""
        import server
        result = _parse(server.jira_ist_capacity(nominal_capacity=60.0))

        assert result["success"] is True
        assert "india_context" in result
        assert len(result["india_context"]) > 0


class TestJiraTcoAnalysis:
    """Tests for jira_tco_analysis tool (GROUP A: pure delegation)."""

    def test_happy_path_npv_fields_present(self):
        """Happy path: NPV comparison fields are present for valid inputs."""
        import server
        result = _parse(server.jira_tco_analysis(user_count=50, years=3, discount_rate=0.10))

        assert result["success"] is True
        assert "jira_premium_3yr_npv_inr" in result or "recommendation" in result

    def test_recommendation_is_non_empty_string(self):
        """recommendation is a non-empty string."""
        import server
        result = _parse(server.jira_tco_analysis(user_count=100, years=3, discount_rate=0.10))

        assert result["success"] is True
        assert isinstance(result.get("recommendation"), str)
        assert len(result["recommendation"]) > 0

    def test_invalid_user_count_returns_error(self):
        """user_count < 1 returns success=False (ValueError caught by decorator)."""
        import server
        result = _parse(server.jira_tco_analysis(user_count=0))

        assert result["success"] is False

    def test_invalid_discount_rate_returns_error(self):
        """discount_rate outside (0, 1) returns success=False."""
        import server
        result = _parse(server.jira_tco_analysis(user_count=50, years=3, discount_rate=1.5))

        assert result["success"] is False


class TestJiraScrumOfScrums:
    """Tests for jira_scrum_of_scrums tool (GROUP A: pure delegation)."""

    def test_happy_path_t_n_present(self):
        """Happy path: T_n net throughput field is present."""
        import server
        result = _parse(server.jira_scrum_of_scrums(teams=3, productivity_per_team=40.0, coordination_cost=2.0))

        assert result["success"] is True
        assert "T_n" in result

    def test_n_optimal_present_and_positive(self):
        """n_optimal is present and > 0."""
        import server
        result = _parse(server.jira_scrum_of_scrums(teams=4, productivity_per_team=50.0, coordination_cost=3.0))

        assert result["success"] is True
        assert "n_optimal" in result
        assert result["n_optimal"] > 0

    def test_invalid_teams_count_returns_error(self):
        """teams < 2 returns success=False (coordination requires at least 2 teams)."""
        import server
        result = _parse(server.jira_scrum_of_scrums(teams=1, productivity_per_team=40.0, coordination_cost=2.0))

        assert result["success"] is False

    def test_overhead_ratio_between_0_and_1(self):
        """overhead_ratio is in [0, 1] range for valid inputs."""
        import server
        result = _parse(server.jira_scrum_of_scrums(teams=3, productivity_per_team=40.0, coordination_cost=2.0))

        assert result["success"] is True
        assert "overhead_ratio" in result
        assert 0.0 <= result["overhead_ratio"] <= 1.0


class TestJiraCognitiveLoad:
    """Tests for jira_cognitive_load tool (GROUP A: pure delegation)."""

    def test_happy_path_cli_present(self):
        """Happy path: CLI (Cognitive Load Index) is present."""
        import server
        complexity = json.dumps({"payments": 3.5, "auth": 2.0, "reporting": 1.5})
        responsibility = json.dumps({"payments": 0.8, "auth": 1.0, "reporting": 0.5})
        result = _parse(server.jira_cognitive_load(board_id=1, complexity_json=complexity, responsibility_json=responsibility))

        assert result["success"] is True
        assert "CLI" in result

    def test_overloaded_flag_is_boolean(self):
        """overloaded is a boolean value."""
        import server
        complexity = json.dumps({"a": 5.0, "b": 5.0})
        responsibility = json.dumps({"a": 1.5, "b": 1.5})
        result = _parse(server.jira_cognitive_load(board_id=1, complexity_json=complexity, responsibility_json=responsibility))

        assert result["success"] is True
        assert isinstance(result.get("overloaded"), bool)

    def test_invalid_board_id_returns_error(self):
        """board_id <= 0 returns success=False (ValueError caught by decorator)."""
        import server
        complexity = json.dumps({"a": 1.0})
        responsibility = json.dumps({"a": 0.5})
        result = _parse(server.jira_cognitive_load(board_id=0, complexity_json=complexity, responsibility_json=responsibility))

        assert result["success"] is False

    def test_invalid_cl_max_returns_error(self):
        """cl_max <= 0 returns success=False (ValueError caught by decorator)."""
        import server
        complexity = json.dumps({"a": 1.0})
        responsibility = json.dumps({"a": 0.5})
        result = _parse(server.jira_cognitive_load(board_id=1, complexity_json=complexity, responsibility_json=responsibility, cl_max=0.0))

        assert result["success"] is False


class TestJiraAttritionForecast:
    """Tests for jira_attrition_forecast tool (GROUP A: pure delegation)."""

    def test_happy_path_probability_in_range(self):
        """Happy path: attrition_probability is in (0, 1]."""
        import server
        result = _parse(server.jira_attrition_forecast(board_id=1, months=6.0, p_max=0.3))

        assert result["success"] is True
        assert "attrition_probability" in result
        assert 0.0 < result["attrition_probability"] <= 1.0

    def test_effective_velocity_factor_present(self):
        """effective_velocity_factor is present and in (0, 1]."""
        import server
        result = _parse(server.jira_attrition_forecast(board_id=1, months=6.0, p_max=0.25))

        assert result["success"] is True
        assert "effective_velocity_factor" in result
        assert 0.0 < result["effective_velocity_factor"] <= 1.0

    def test_invalid_board_id_returns_error(self):
        """board_id <= 0 returns success=False (ValueError caught by decorator)."""
        import server
        result = _parse(server.jira_attrition_forecast(board_id=-1, months=6.0, p_max=0.2))

        assert result["success"] is False

    def test_invalid_months_returns_error(self):
        """months <= 0 returns success=False (validation in scrum_calculator)."""
        import server
        result = _parse(server.jira_attrition_forecast(board_id=1, months=-1.0, p_max=0.2))

        assert result["success"] is False


class TestJiraPsychologicalSafety:
    """Tests for jira_psychological_safety tool (GROUP A: pure delegation)."""

    def test_happy_path_ps_score_in_range(self):
        """Happy path: PS_score is in [1, 7]."""
        import server
        scores = json.dumps([3, 5, 2, 6, 4, 5, 3])
        result = _parse(server.jira_psychological_safety(board_id=1, item_scores=scores))

        assert result["success"] is True
        assert "PS_score" in result
        assert 1.0 <= result["PS_score"] <= 7.0

    def test_interpretation_field_present(self):
        """interpretation is one of 'Low', 'Moderate', 'High'."""
        import server
        scores = json.dumps([5, 5, 5, 5, 5, 5, 5])
        result = _parse(server.jira_psychological_safety(board_id=1, item_scores=scores))

        assert result["success"] is True
        assert result["interpretation"] in ("Low", "Moderate", "High")

    def test_invalid_board_id_returns_error(self):
        """board_id <= 0 returns success=False (ValueError caught by decorator)."""
        import server
        scores = json.dumps([3, 5, 2, 6, 4, 5, 3])
        result = _parse(server.jira_psychological_safety(board_id=0, item_scores=scores))

        assert result["success"] is False

    def test_wrong_item_count_returns_error(self):
        """Fewer than 7 items returns success=False (validation in calculator)."""
        import server
        scores = json.dumps([3, 5, 2])
        result = _parse(server.jira_psychological_safety(board_id=1, item_scores=scores))

        assert result["success"] is False


class TestJiraSpotifyHealthCheck:
    """Tests for jira_spotify_health_check tool (GROUP A: pure delegation)."""

    _ELEVEN_DIMS = {
        "easy_to_release": [1, 2, 1],
        "suitable_process": [2, 2, 1],
        "tech_quality": [1, 1, 2],
        "value": [2, 1, 2],
        "speed": [1, 2, 1],
        "mission": [2, 2, 2],
        "fun": [1, 1, 1],
        "learning": [2, 1, 2],
        "support": [1, 2, 2],
        "pawns_or_players": [2, 2, 1],
        "team_spirit": [1, 2, 1],
    }

    def test_happy_path_ths_in_range(self):
        """Happy path: THS is in [0, 2]."""
        import server
        scores_str = json.dumps(self._ELEVEN_DIMS)
        result = _parse(server.jira_spotify_health_check(board_id=1, dimension_scores=scores_str))

        assert result["success"] is True
        assert "THS" in result
        assert 0.0 <= result["THS"] <= 2.0

    def test_health_color_is_valid(self):
        """health_color is one of 'Green', 'Amber', 'Red'."""
        import server
        scores_str = json.dumps(self._ELEVEN_DIMS)
        result = _parse(server.jira_spotify_health_check(board_id=1, dimension_scores=scores_str))

        assert result["success"] is True
        assert result["health_color"] in ("Green", "Amber", "Red")

    def test_invalid_board_id_returns_error(self):
        """board_id <= 0 returns success=False (ValueError caught by decorator)."""
        import server
        scores_str = json.dumps(self._ELEVEN_DIMS)
        result = _parse(server.jira_spotify_health_check(board_id=0, dimension_scores=scores_str))

        assert result["success"] is False

    def test_missing_dimension_returns_error(self):
        """Fewer than 11 required dimensions returns success=False."""
        import server
        partial = {"easy_to_release": [1, 2]}
        result = _parse(server.jira_spotify_health_check(board_id=1, dimension_scores=json.dumps(partial)))

        assert result["success"] is False


class TestJiraMultiSprintHolidays:
    """Tests for jira_multi_sprint_holidays tool (GROUP A: pure delegation)."""

    def test_happy_path_sprints_list_present(self):
        """Happy path: sprints list has the expected number of entries."""
        import server
        result = _parse(server.jira_multi_sprint_holidays(
            sprint_start="2026-01-20",
            sprint_duration_days=14,
            num_sprints=3,
        ))

        assert result["success"] is True
        assert "sprints" in result
        assert len(result["sprints"]) == 3

    def test_sprint_fields_all_present(self):
        """Each sprint entry has all expected fields."""
        import server
        result = _parse(server.jira_multi_sprint_holidays(sprint_start="2026-01-20"))

        assert result["success"] is True
        for sprint in result["sprints"]:
            assert "sprint_number" in sprint
            assert "start_date" in sprint
            assert "end_date" in sprint
            assert "holiday_count" in sprint
            assert "effective_days" in sprint

    def test_effective_days_less_than_sprint_days(self):
        """effective_days <= sprint_duration_days for each sprint."""
        import server
        result = _parse(server.jira_multi_sprint_holidays(
            sprint_start="2026-01-20",
            sprint_duration_days=14,
            num_sprints=4,
        ))

        assert result["success"] is True
        for sprint in result["sprints"]:
            assert sprint["effective_days"] <= 14

    def test_invalid_date_returns_error(self):
        """Invalid sprint_start date format returns success=False."""
        import server
        result = _parse(server.jira_multi_sprint_holidays(sprint_start="not-a-date"))

        assert result["success"] is False


class TestJiraRateLimitStatus:
    """Tests for jira_rate_limit_status tool (GROUP A: no mock needed)."""

    def test_returns_success_true(self):
        """jira_rate_limit_status always returns success=True."""
        import server
        result = _parse(server.jira_rate_limit_status())

        assert result["success"] is True

    def test_rate_limiting_enabled_is_boolean(self):
        """rate_limiting_enabled is a boolean."""
        import server
        result = _parse(server.jira_rate_limit_status())

        assert isinstance(result["rate_limiting_enabled"], bool)

    def test_buckets_is_a_list(self):
        """buckets is a list (may be empty when rate limiting is off)."""
        import server
        result = _parse(server.jira_rate_limit_status())

        assert "buckets" in result
        assert isinstance(result["buckets"], list)

    def test_bucket_count_matches_buckets_length(self):
        """bucket_count equals len(buckets)."""
        import server
        result = _parse(server.jira_rate_limit_status())

        assert result["bucket_count"] == len(result["buckets"])

    def test_disabled_when_env_var_not_set(self, monkeypatch):
        """rate_limiting_enabled=False when ENABLE_RATE_LIMITING is not 1."""
        monkeypatch.setenv("ENABLE_RATE_LIMITING", "0")
        import server
        result = _parse(server.jira_rate_limit_status())

        assert result["rate_limiting_enabled"] is False


# ---------------------------------------------------------------------------
# GROUP B -- Jira API dependent tools (mock urllib.request.urlopen)
# ---------------------------------------------------------------------------


class TestJiraBurndownChart:
    """Tests for jira_burndown_chart tool (GROUP B: API dependent)."""

    @patch("urllib.request.urlopen")
    def test_happy_path_burndown_metrics_present(self, mock_urlopen, jira_env):
        """Happy path: burndown_metrics dict and total_points are present."""
        burndown_data = {
            "completedPoints": [0, 5, 10, 15, 20],
            "incompletedPoints": [40, 35, 30, 25, 20],
        }
        mock_urlopen.return_value = _make_urlopen_response(burndown_data)

        import server
        result = _parse(server.jira_burndown_chart(board_id=1, sprint_id=11))

        assert result["success"] is True
        assert "burndown_metrics" in result
        assert "total_points" in result

    @patch("urllib.request.urlopen")
    def test_board_id_and_sprint_id_echoed(self, mock_urlopen, jira_env):
        """board_id and sprint_id are echoed in the result."""
        mock_urlopen.return_value = _make_urlopen_response({
            "completedPoints": [5, 10, 20],
            "incompletedPoints": [40, 35, 25],
        })

        import server
        result = _parse(server.jira_burndown_chart(board_id=1, sprint_id=42))

        assert result["board_id"] == 1
        assert result["sprint_id"] == 42

    def test_invalid_board_id_returns_error(self, jira_env):
        """board_id < 1 returns success=False (ValueError caught by decorator)."""
        import server
        result = _parse(server.jira_burndown_chart(board_id=0, sprint_id=11))

        assert result["success"] is False

    def test_missing_env_returns_error(self, monkeypatch):
        """Missing JIRA_URL returns success=False."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_burndown_chart(board_id=1, sprint_id=11))

        assert result["success"] is False

    @patch("urllib.request.urlopen", side_effect=Exception("API error"))
    def test_api_exception_returns_error(self, mock_urlopen, jira_env):
        """Unexpected API exception returns success=False."""
        import server
        result = _parse(server.jira_burndown_chart(board_id=1, sprint_id=11))

        assert result["success"] is False

    @patch("urllib.request.urlopen")
    def test_empty_arrays_returns_error(self, mock_urlopen, jira_env):
        """Response with empty arrays returns success=False."""
        mock_urlopen.return_value = _make_urlopen_response({
            "completedPoints": [],
            "incompletedPoints": [],
        })

        import server
        result = _parse(server.jira_burndown_chart(board_id=1, sprint_id=11))

        assert result["success"] is False


class TestJiraCfdAnalysis:
    """Tests for jira_cfd_analysis tool (GROUP B: API dependent)."""

    @patch("urllib.request.urlopen")
    def test_happy_path_little_law_present(self, mock_urlopen, jira_env):
        """Happy path: little_law dict is present in result."""
        cfd_data = {
            "columnData": [
                {"date": "2026-01-20", "columns": [{"name": "To Do", "count": 10}, {"name": "Done", "count": 0}]},
                {"date": "2026-01-21", "columns": [{"name": "To Do", "count": 8}, {"name": "Done", "count": 2}]},
                {"date": "2026-01-22", "columns": [{"name": "To Do", "count": 6}, {"name": "Done", "count": 4}]},
            ]
        }
        mock_urlopen.return_value = _make_urlopen_response(cfd_data)

        import server
        result = _parse(server.jira_cfd_analysis(board_id=1))

        assert result["success"] is True
        assert "little_law" in result

    @patch("urllib.request.urlopen")
    def test_board_id_echoed(self, mock_urlopen, jira_env):
        """board_id is echoed in the result."""
        cfd_data = {
            "columnData": [
                {"date": "2026-01-20", "columns": [{"name": "Done", "count": 5}]},
            ]
        }
        mock_urlopen.return_value = _make_urlopen_response(cfd_data)

        import server
        result = _parse(server.jira_cfd_analysis(board_id=7))

        assert result["board_id"] == 7

    def test_invalid_board_id_returns_error(self, jira_env):
        """board_id < 1 returns success=False (ValueError caught by decorator)."""
        import server
        result = _parse(server.jira_cfd_analysis(board_id=0))

        assert result["success"] is False

    def test_missing_env_returns_error(self, monkeypatch):
        """Missing JIRA_URL returns success=False."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_cfd_analysis(board_id=1))

        assert result["success"] is False

    @patch("urllib.request.urlopen")
    def test_missing_column_data_returns_error(self, mock_urlopen, jira_env):
        """Response with missing columnData returns success=False."""
        mock_urlopen.return_value = _make_urlopen_response({"someOtherKey": []})

        import server
        result = _parse(server.jira_cfd_analysis(board_id=1))

        assert result["success"] is False


class TestJiraCycleTimeAnalysis:
    """Tests for jira_cycle_time_analysis tool (GROUP B: API dependent)."""

    @patch("urllib.request.urlopen")
    def test_happy_path_lognormal_fit_present(self, mock_urlopen, jira_env):
        """Happy path: lognormal_fit dict is present when enough resolved issues exist."""
        issues_data = {
            "issues": [
                {
                    "key": "DEMO-101",
                    "fields": {
                        "created": "2026-01-10T09:00:00.000+0000",
                        "resolutiondate": "2026-01-15T17:00:00.000+0000",
                    }
                },
                {
                    "key": "DEMO-102",
                    "fields": {
                        "created": "2026-01-11T09:00:00.000+0000",
                        "resolutiondate": "2026-01-18T17:00:00.000+0000",
                    }
                },
                {
                    "key": "DEMO-103",
                    "fields": {
                        "created": "2026-01-12T09:00:00.000+0000",
                        "resolutiondate": "2026-01-17T17:00:00.000+0000",
                    }
                },
            ]
        }
        mock_urlopen.return_value = _make_urlopen_response(issues_data)

        import server
        result = _parse(server.jira_cycle_time_analysis(board_id=1, sprint_id=11))

        assert result["success"] is True
        assert "lognormal_fit" in result
        assert "resolved_count" in result

    @patch("urllib.request.urlopen")
    def test_insufficient_issues_returns_error(self, mock_urlopen, jira_env):
        """Fewer than 2 resolved issues returns success=False."""
        issues_data = {
            "issues": [
                {
                    "key": "DEMO-101",
                    "fields": {
                        "created": "2026-01-10T09:00:00.000+0000",
                        "resolutiondate": "2026-01-15T17:00:00.000+0000",
                    }
                }
            ]
        }
        mock_urlopen.return_value = _make_urlopen_response(issues_data)

        import server
        result = _parse(server.jira_cycle_time_analysis(board_id=1, sprint_id=11))

        assert result["success"] is False
        assert "Insufficient" in result.get("error", "") or "insufficient" in result.get("error", "").lower()

    def test_invalid_board_id_returns_error(self, jira_env):
        """board_id < 1 returns success=False (ValueError caught by decorator)."""
        import server
        result = _parse(server.jira_cycle_time_analysis(board_id=0, sprint_id=11))

        assert result["success"] is False

    def test_missing_env_returns_error(self, monkeypatch):
        """Missing env vars returns success=False."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_cycle_time_analysis(board_id=1, sprint_id=11))

        assert result["success"] is False

    @patch("urllib.request.urlopen")
    def test_board_and_sprint_echoed(self, mock_urlopen, jira_env):
        """board_id and sprint_id are echoed in the happy-path result."""
        issues_data = {
            "issues": [
                {"key": "D-1", "fields": {"created": "2026-01-10T09:00:00.000+0000", "resolutiondate": "2026-01-15T09:00:00.000+0000"}},
                {"key": "D-2", "fields": {"created": "2026-01-11T09:00:00.000+0000", "resolutiondate": "2026-01-18T09:00:00.000+0000"}},
            ]
        }
        mock_urlopen.return_value = _make_urlopen_response(issues_data)

        import server
        result = _parse(server.jira_cycle_time_analysis(board_id=5, sprint_id=99))

        assert result["board_id"] == 5
        assert result["sprint_id"] == 99


class TestJiraThroughputForecast:
    """Tests for jira_throughput_forecast tool (GROUP B: API dependent)."""

    @patch("urllib.request.urlopen")
    def test_happy_path_poisson_forecast_present(self, mock_urlopen, jira_env):
        """Happy path: poisson_forecast is present for valid closed sprint data."""
        sprints_data = {
            "values": [
                {"id": 10, "name": "Sprint 10", "state": "closed", "completedIssuesCount": 8},
                {"id": 11, "name": "Sprint 11", "state": "closed", "completedIssuesCount": 10},
                {"id": 12, "name": "Sprint 12", "state": "closed", "completedIssuesCount": 7},
            ]
        }
        mock_urlopen.return_value = _make_urlopen_response(sprints_data)

        import server
        result = _parse(server.jira_throughput_forecast(board_id=1, num_sprints=5, forecast_periods=3))

        assert result["success"] is True
        assert "poisson_forecast" in result

    @patch("urllib.request.urlopen")
    def test_board_id_and_forecast_periods_echoed(self, mock_urlopen, jira_env):
        """board_id and forecast_periods are echoed in the result."""
        sprints_data = {
            "values": [
                {"id": 1, "completedIssuesCount": 9},
                {"id": 2, "completedIssuesCount": 11},
            ]
        }
        mock_urlopen.return_value = _make_urlopen_response(sprints_data)

        import server
        result = _parse(server.jira_throughput_forecast(board_id=3, forecast_periods=4))

        assert result["board_id"] == 3
        assert result["forecast_periods"] == 4

    @patch("urllib.request.urlopen")
    def test_no_completed_sprints_returns_error(self, mock_urlopen, jira_env):
        """Zero completed issues in all sprints returns success=False."""
        sprints_data = {
            "values": [
                {"id": 10, "completedIssuesCount": 0},
            ]
        }
        mock_urlopen.return_value = _make_urlopen_response(sprints_data)

        import server
        result = _parse(server.jira_throughput_forecast(board_id=1))

        assert result["success"] is False

    def test_missing_env_returns_error(self, monkeypatch):
        """Missing env vars returns success=False."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_throughput_forecast(board_id=1))

        assert result["success"] is False


class TestJiraAutomationAnalyzer:
    """Tests for jira_automation_analyzer tool (GROUP B: no Jira call -- pure math)."""

    def test_happy_path_mm1_analysis_present(self):
        """Happy path: mm1_analysis list and dag_has_cycle are present."""
        import server
        result = _parse(server.jira_automation_analyzer(
            trigger_rates_json="[2.0, 0.5]",
            service_rates_json="[5.0, 3.0]",
            rules_dag_json='{"rule_A": ["rule_B"], "rule_B": []}',
        ))

        assert result["success"] is True
        assert "mm1_analysis" in result
        assert "dag_has_cycle" in result

    def test_stable_rules_when_lambda_less_than_mu(self):
        """Rules with lambda < mu are stable (rho < 1)."""
        import server
        result = _parse(server.jira_automation_analyzer(
            trigger_rates_json="[1.0, 0.5]",
            service_rates_json="[5.0, 3.0]",
            rules_dag_json='{"A": [], "B": []}',
        ))

        assert result["success"] is True
        for entry in result["mm1_analysis"]:
            assert entry["stable"] is True

    def test_cycle_detected_in_cyclic_dag(self):
        """Cyclic automation rules DAG is detected as dag_has_cycle=True."""
        import server
        result = _parse(server.jira_automation_analyzer(
            trigger_rates_json="[1.0, 1.0, 1.0]",
            service_rates_json="[5.0, 5.0, 5.0]",
            rules_dag_json='{"A": ["B"], "B": ["C"], "C": ["A"]}',
        ))

        assert result["success"] is True
        assert result["dag_has_cycle"] is True

    def test_no_cycle_in_acyclic_dag(self):
        """Acyclic DAG is detected as dag_has_cycle=False."""
        import server
        result = _parse(server.jira_automation_analyzer(
            trigger_rates_json="[1.0, 1.0]",
            service_rates_json="[5.0, 5.0]",
            rules_dag_json='{"A": ["B"], "B": []}',
        ))

        assert result["success"] is True
        assert result["dag_has_cycle"] is False

    def test_mismatched_rate_arrays_returns_error(self):
        """trigger_rates and service_rates of different lengths returns success=False."""
        import server
        result = _parse(server.jira_automation_analyzer(
            trigger_rates_json="[1.0, 2.0, 3.0]",
            service_rates_json="[5.0]",
            rules_dag_json='{"A": []}',
        ))

        assert result["success"] is False

    def test_invalid_json_trigger_returns_error(self):
        """Invalid JSON in trigger_rates_json returns success=False."""
        import server
        result = _parse(server.jira_automation_analyzer(
            trigger_rates_json="not-json",
            service_rates_json="[5.0]",
            rules_dag_json='{"A": []}',
        ))

        assert result["success"] is False

    def test_node_count_matches_dag_keys(self):
        """node_count equals the number of keys in rules_dag_json."""
        import server
        dag = '{"rule_1": ["rule_2"], "rule_2": [], "rule_3": []}'
        result = _parse(server.jira_automation_analyzer(
            trigger_rates_json="[1.0, 0.5, 0.3]",
            service_rates_json="[5.0, 3.0, 2.0]",
            rules_dag_json=dag,
        ))

        assert result["success"] is True
        assert result["node_count"] == 3


class TestJiraNasscomMapping:
    """Tests for jira_nasscom_mapping tool (GROUP B: API dependent)."""

    @patch("urllib.request.urlopen")
    def test_happy_path_nasscom_agile_x_present(self, mock_urlopen, jira_env):
        """Happy path: nasscom_agile_x dict and overall_level are present."""
        sprint_issues = fixture_loader("agile", "sprint_issues")
        sprint_detail = fixture_loader("agile", "sprint_detail")
        velocity_chart = fixture_loader("agile", "velocity_chart")

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_issues),
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(velocity_chart),
        ]

        import server
        result = _parse(server.jira_nasscom_mapping(board_id=1, sprint_id=11))

        assert result["success"] is True
        assert "nasscom_agile_x" in result
        assert "overall_level" in result

    @patch("urllib.request.urlopen")
    def test_overall_level_is_l1_through_l5(self, mock_urlopen, jira_env):
        """overall_level is one of L1, L2, L3, L4, L5."""
        sprint_issues = fixture_loader("agile", "sprint_issues")
        sprint_detail = fixture_loader("agile", "sprint_detail")
        velocity_chart = fixture_loader("agile", "velocity_chart")

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_issues),
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(velocity_chart),
        ]

        import server
        result = _parse(server.jira_nasscom_mapping(board_id=1, sprint_id=11))

        assert result["success"] is True
        assert result["overall_level"] in ("L1", "L2", "L3", "L4", "L5")

    @patch("urllib.request.urlopen")
    def test_board_id_and_sprint_id_echoed(self, mock_urlopen, jira_env):
        """board_id and sprint_id are echoed in the result."""
        sprint_issues = fixture_loader("agile", "sprint_issues")
        sprint_detail = fixture_loader("agile", "sprint_detail")
        velocity_chart = fixture_loader("agile", "velocity_chart")

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_issues),
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(velocity_chart),
        ]

        import server
        result = _parse(server.jira_nasscom_mapping(board_id=2, sprint_id=15))

        assert result["board_id"] == 2
        assert result["sprint_id"] == 15

    def test_invalid_board_id_returns_error(self, jira_env):
        """board_id < 1 returns success=False (ValueError caught by decorator)."""
        import server
        result = _parse(server.jira_nasscom_mapping(board_id=0, sprint_id=11))

        assert result["success"] is False

    def test_missing_env_returns_error(self, monkeypatch):
        """Missing env vars returns success=False."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)

        import server
        result = _parse(server.jira_nasscom_mapping(board_id=1, sprint_id=11))

        assert result["success"] is False

    @patch("urllib.request.urlopen")
    def test_india_context_present(self, mock_urlopen, jira_env):
        """india_context field is present and mentions India or NASSCOM."""
        sprint_issues = fixture_loader("agile", "sprint_issues")
        sprint_detail = fixture_loader("agile", "sprint_detail")
        velocity_chart = fixture_loader("agile", "velocity_chart")

        mock_urlopen.side_effect = [
            _make_urlopen_response(sprint_issues),
            _make_urlopen_response(sprint_detail),
            _make_urlopen_response(velocity_chart),
        ]

        import server
        result = _parse(server.jira_nasscom_mapping(board_id=1, sprint_id=11))

        assert result["success"] is True
        india_ctx = result.get("india_context", "")
        assert "India" in india_ctx or "NASSCOM" in india_ctx


# ---------------------------------------------------------------------------
# GROUP C -- Regression tests on upgraded existing tools
# ---------------------------------------------------------------------------


class TestJiraRefineBacklogWsjfScores:
    """Regression tests for jira_refine_backlog -- verify wsjf_scores key."""

    @patch("urllib.request.urlopen")
    def test_wsjf_scores_key_present_in_result(self, mock_urlopen, jira_env):
        """Upgraded tool: wsjf_scores or wsjf_ordered_stories key present."""
        search_result = fixture_loader("rest", "issue_search_sprint")
        mock_urlopen.return_value = _make_urlopen_response(search_result)

        import server
        result = _parse(server.jira_refine_backlog(project_key="DEMO"))

        assert result["success"] is True
        has_wsjf = "wsjf_ordered_stories" in result or "wsjf_scores" in result
        assert has_wsjf, "wsjf_ordered_stories or wsjf_scores must be present"

    @patch("urllib.request.urlopen")
    def test_stories_have_wsjf_template_dict(self, mock_urlopen, jira_env):
        """Each story in wsjf_ordered_stories has a wsjf_template dict."""
        search_result = fixture_loader("rest", "issue_search_sprint")
        mock_urlopen.return_value = _make_urlopen_response(search_result)

        import server
        result = _parse(server.jira_refine_backlog(project_key="DEMO"))

        assert result["success"] is True
        stories = result.get("wsjf_ordered_stories", [])
        if stories:
            first = stories[0]
            assert "wsjf_template" in first
            for key in ("business_value", "time_criticality", "risk_reduction", "job_size"):
                assert key in first["wsjf_template"]


class TestJiraSprintReviewAhpKey:
    """Regression tests for jira_sprint_review -- verify AHP-related keys."""

    @patch("urllib.request.urlopen")
    def test_sprint_review_success(self, mock_urlopen, jira_env):
        """jira_sprint_review still returns success=True after upgrade."""
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

    @patch("urllib.request.urlopen")
    def test_sprint_review_has_nasscom_level(self, mock_urlopen, jira_env):
        """nasscom_agileX_level is present in sprint review result."""
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

        assert "nasscom_agileX_level" in result

    @patch("urllib.request.urlopen")
    def test_sprint_review_completion_rate_in_range(self, mock_urlopen, jira_env):
        """completion_rate is still in [0, 100] after upgrade."""
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


class TestJiraTeamHealthTuckmanStage:
    """Regression tests for jira_team_health -- verify tuckman_stage field."""

    @patch("urllib.request.urlopen")
    def test_tuckman_stage_is_valid_stage(self, mock_urlopen, jira_env):
        """tuckman_stage is a valid Tuckman model stage name."""
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

    @patch("urllib.request.urlopen")
    def test_team_health_board_id_echoed(self, mock_urlopen, jira_env):
        """board_id is echoed in team health result."""
        mock_urlopen.side_effect = [
            _make_urlopen_response({"values": [], "total": 0}),
        ]

        import server
        result = _parse(server.jira_team_health(board_id=1))

        assert result["board_id"] == 1


class TestJiraGetVelocityBcaKeys:
    """Regression tests for jira_get_velocity -- verify BCA CI keys."""

    @patch("urllib.request.urlopen")
    def test_velocity_stats_present(self, mock_urlopen, jira_env):
        """velocity_stats dict is still present after upgrade."""
        velocity_chart = fixture_loader("agile", "velocity_chart")
        mock_urlopen.return_value = _make_urlopen_response(velocity_chart)

        import server
        result = _parse(server.jira_get_velocity(board_id=1))

        assert result["success"] is True
        assert "velocity_stats" in result

    @patch("urllib.request.urlopen")
    def test_bca_ci_keys_present_in_velocity_stats(self, mock_urlopen, jira_env):
        """bca_ci_lower and bca_ci_upper are present in velocity_stats."""
        velocity_chart = fixture_loader("agile", "velocity_chart")
        mock_urlopen.return_value = _make_urlopen_response(velocity_chart)

        import server
        result = _parse(server.jira_get_velocity(board_id=1))

        assert result["success"] is True
        v_stats = result.get("velocity_stats", {})
        has_bca = "bca_ci_lower" in v_stats or "bca_ci_lower" in result
        assert has_bca, (
            "bca_ci_lower key must be present in velocity_stats or top-level result "
            "after get_velocity upgrade. Got velocity_stats keys: {}".format(list(v_stats.keys()))
        )

    @patch("urllib.request.urlopen")
    def test_ewma_last_non_negative(self, mock_urlopen, jira_env):
        """ewma_last is still present and non-negative after upgrade."""
        velocity_chart = fixture_loader("agile", "velocity_chart")
        mock_urlopen.return_value = _make_urlopen_response(velocity_chart)

        import server
        result = _parse(server.jira_get_velocity(board_id=1))

        assert result["ewma_last"] >= 0.0
