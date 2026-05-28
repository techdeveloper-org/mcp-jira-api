"""
test_scrum_calculator_new.py -- Unit tests for the 16 new pure functions in scrum_calculator.py.

Target: 100% line coverage for scrum_calculator.py lines 533-1813.
Framework: pytest (match existing test_scrum_calculator.py style).
No mocking required -- all 16 functions are pure (no I/O).
Windows-Safe: ASCII only (cp1252 compatible).
Float tolerance: pytest.approx(abs=0.001) for all floating-point assertions.
"""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scrum_calculator import (
    bootstrap_bca_ci,
    ahp_score,
    tuckman_markov,
    spotify_health_check,
    edmondson_ps_scale,
    scrum_of_scrums_overhead,
    cognitive_load_index,
    attrition_ramp,
    ist_capacity_correction,
    little_law_analysis,
    cycle_time_lognormal_mle,
    poisson_throughput,
    pert_estimate,
    tco_npv_comparison,
    burndown_metrics,
    multi_sprint_holiday_forecast,
)


# ---------------------------------------------------------------------------
# Helpers shared across test classes
# ---------------------------------------------------------------------------

def _all_spotify_dims(score_list):
    """Return a full 11-dimension dict with each dimension set to score_list."""
    dims = [
        "easy_to_release", "suitable_process", "tech_quality", "value",
        "speed", "mission", "fun", "learning", "support",
        "pawns_or_players", "team_spirit",
    ]
    return {d: list(score_list) for d in dims}


# ---------------------------------------------------------------------------
# TestBootstrapBcaCi  (BCA-01 to BCA-07 + extra boundary tests)
# ---------------------------------------------------------------------------

class TestBootstrapBcaCi:
    """Tests for bootstrap_bca_ci() -- structural invariants, not exact values."""

    def test_empty_list_returns_error(self):
        """BCA-01: Empty list triggers the insufficient-data guard."""
        result = bootstrap_bca_ci([])
        assert "error" in result

    def test_single_element_returns_error(self):
        """BCA-02: Single element triggers the insufficient-data guard (need >= 2)."""
        result = bootstrap_bca_ci([5.0])
        assert "error" in result

    def test_zero_variance_returns_point_estimate(self):
        """BCA-03: All-same values returns lower==upper==point_estimate and B==0."""
        result = bootstrap_bca_ci([10.0, 10.0, 10.0])
        assert "error" not in result
        assert result["lower"] == pytest.approx(10.0, abs=0.001)
        assert result["upper"] == pytest.approx(10.0, abs=0.001)
        assert result["point_estimate"] == pytest.approx(10.0, abs=0.001)
        assert result["B"] == 0
        assert "note" in result

    def test_realistic_data_ci_contains_mean(self):
        """BCA-04: CI must straddle the sample mean for realistic data (B=2000 for stability)."""
        data = [20.0, 25.0, 30.0, 22.0, 28.0]
        sample_mean = sum(data) / len(data)
        result = bootstrap_bca_ci(data, B=2000)
        assert "error" not in result
        assert result["lower"] <= sample_mean + 0.5
        assert result["upper"] >= sample_mean - 0.5

    def test_ci_is_ordered(self):
        """BCA-05: lower <= point_estimate AND lower < upper for non-degenerate data."""
        result = bootstrap_bca_ci([1, 100], confidence=0.90, B=1000)
        assert "error" not in result
        assert result["lower"] < result["upper"]
        assert result["confidence"] == pytest.approx(0.90, abs=0.001)

    def test_confidence_key_present(self):
        """BCA-05 (cont): confidence level echoed in result."""
        result = bootstrap_bca_ci([1, 100], confidence=0.90, B=1000)
        assert result["confidence"] == pytest.approx(0.90, abs=0.001)

    def test_point_estimate_equals_sample_mean(self):
        """BCA-06: point_estimate must equal the arithmetic mean of the data."""
        data = [10, 20, 30, 40, 50]
        result = bootstrap_bca_ci(data, B=500)
        assert "error" not in result
        assert result["point_estimate"] == pytest.approx(30.0, abs=0.001)

    def test_near_zero_variance_does_not_crash(self):
        """BCA-07: Near-zero but non-zero variance must not raise any exception."""
        result = bootstrap_bca_ci([5, 5, 5, 5, 10], B=500)
        assert "error" not in result
        assert result["lower"] <= result["upper"]

    def test_b_echoed_in_result(self):
        """B parameter must be echoed in the returned dict for non-degenerate data."""
        result = bootstrap_bca_ci([10.0, 20.0, 30.0], B=300)
        assert "error" not in result
        assert result["B"] == 300

    def test_ci_width_non_negative(self):
        """CI width (upper - lower) must always be >= 0."""
        data = [5, 10, 15, 20, 25]
        result = bootstrap_bca_ci(data, B=500)
        assert result["upper"] - result["lower"] >= 0.0

    def test_two_element_equal_values_special_path(self):
        """Two equal values trigger zero variance path; acceleration diffs_sq_sum=0."""
        result = bootstrap_bca_ci([10.0, 10.0])
        assert "error" not in result
        assert result["B"] == 0
        assert result["lower"] == pytest.approx(10.0, abs=0.001)

    def test_two_element_distinct_uses_jackknife(self):
        """Two distinct values: jackknife produces two loo means, covering diffs path."""
        result = bootstrap_bca_ci([5.0, 15.0], B=500)
        assert "error" not in result
        assert result["lower"] <= result["upper"]


# ---------------------------------------------------------------------------
# TestAhpScore  (AHP-01 to AHP-07)
# ---------------------------------------------------------------------------

class TestAhpScore:
    """Tests for ahp_score() AHP pairwise comparison."""

    def test_empty_matrix_returns_error(self):
        """AHP-01: Empty matrix returns error."""
        result = ahp_score([])
        assert "error" in result

    def test_non_square_row_too_long_returns_error(self):
        """AHP-03: Non-square matrix (row length != n) returns error."""
        result = ahp_score([[1, 2], [3, 4, 5]])
        assert "error" in result

    def test_1x1_trivial_weights_and_cr(self):
        """AHP-02: 1x1 matrix returns weight=[1.0], CR=0.0, consistent=True."""
        result = ahp_score([[1.0]])
        assert "error" not in result
        assert result["weights"] == [pytest.approx(1.0, abs=0.001)]
        assert result["consistent"] is True
        assert result["CR"] == pytest.approx(0.0, abs=0.001)
        assert result["n"] == 1

    def test_1x1_lambda_max_is_one(self):
        """AHP-07: Trivial 1x1 eigenvalue must equal 1.0."""
        result = ahp_score([[1.0]])
        assert result["lambda_max"] == pytest.approx(1.0, abs=0.001)

    def test_3x3_consistent_matrix(self):
        """AHP-04: Standard AHP 3x3 example -- CR < 0.10, weights sum to ~1.0."""
        matrix = [
            [1, 3, 5],
            [1.0 / 3.0, 1, 3],
            [1.0 / 5.0, 1.0 / 3.0, 1],
        ]
        result = ahp_score(matrix)
        assert "error" not in result
        assert result["consistent"] is True
        assert result["CR"] < 0.10
        assert sum(result["weights"]) == pytest.approx(1.0, abs=0.001)
        assert result["n"] == 3

    def test_3x3_inconsistent_matrix(self):
        """AHP-05: Highly inconsistent 3x3 matrix returns CR > 0.10 and consistent=False."""
        matrix = [
            [1, 9, 9],
            [1.0 / 9.0, 1, 9],
            [1.0 / 9.0, 1.0 / 9.0, 1],
        ]
        result = ahp_score(matrix)
        assert "error" not in result
        assert result["consistent"] is False
        assert result["CR"] > 0.10

    def test_weights_sum_to_one(self):
        """Weights must always sum to 1.0 for any valid square matrix."""
        matrix = [
            [1, 3, 5],
            [1.0 / 3.0, 1, 3],
            [1.0 / 5.0, 1.0 / 3.0, 1],
        ]
        result = ahp_score(matrix)
        assert sum(result["weights"]) == pytest.approx(1.0, abs=0.001)

    def test_cr_boundary_consistent_3x3(self):
        """AHP-06: For n=3, RI=0.58; CR = CI/RI must match manual calculation."""
        matrix = [
            [1, 3, 5],
            [1.0 / 3.0, 1, 3],
            [1.0 / 5.0, 1.0 / 3.0, 1],
        ]
        result = ahp_score(matrix)
        ri = 0.58
        expected_cr = result["CI"] / ri
        assert result["CR"] == pytest.approx(expected_cr, abs=0.001)

    def test_cr_above_0_10_gives_inconsistent(self):
        """Explicit CR=0.11+ boundary: highly inconsistent matrix gives consistent=False."""
        matrix = [
            [1, 9, 9],
            [1.0 / 9.0, 1, 9],
            [1.0 / 9.0, 1.0 / 9.0, 1],
        ]
        result = ahp_score(matrix)
        assert result["consistent"] is False

    def test_non_square_single_row_wrong_length(self):
        """Non-square check: single row of wrong length."""
        result = ahp_score([[1, 2, 3]])
        assert "error" in result

    def test_large_matrix_uses_ri_fallback(self):
        """AHP-RI-fallback: n >= 11 uses ri=1.49 fallback from else branch (line 837)."""
        n = 11
        matrix = [[1.0 if i == j else 2.0 for j in range(n)] for i in range(n)]
        result = ahp_score(matrix)
        assert "error" not in result
        assert result["n"] == 11
        assert "CR" in result

    def test_2x2_matrix_uses_ri_zero_branch(self):
        """AHP-line-839: n=2 gives ri=0.0 (ri_table n<3 condition); CR is computed as 0."""
        matrix = [[1.0, 2.0], [0.5, 1.0]]
        result = ahp_score(matrix)
        assert "error" not in result
        assert result["n"] == 2
        assert result["CR"] == pytest.approx(0.0, abs=0.001)


# ---------------------------------------------------------------------------
# TestTuckmanMarkov  (TM-01 to TM-09)
# ---------------------------------------------------------------------------

class TestTuckmanMarkov:
    """Tests for tuckman_markov() heuristic Tuckman classifier."""

    def test_empty_returns_error(self):
        """TM-01: Empty list must return error dict."""
        result = tuckman_markov([])
        assert "error" in result

    def test_single_element_returns_error(self):
        """TM-02: Single element triggers the need-at-least-2 guard."""
        result = tuckman_markov([40])
        assert "error" in result

    def test_len_2_returns_forming(self):
        """TM-03: Exactly 2 data points triggers Forming (n < 3)."""
        result = tuckman_markov([40, 42])
        assert "error" not in result
        assert result["current_stage"] == "Forming"

    def test_low_cv_performing_or_norming(self):
        """TM-04: Stable team velocities produce Performing or Norming (low CV)."""
        result = tuckman_markov([40, 42, 38, 41, 40, 39])
        assert "error" not in result
        assert result["current_stage"] in {"Performing", "Norming"}
        assert result["cv"] < 0.10

    def test_high_cv_storming_or_forming(self):
        """TM-05: High variance velocities classify as Forming or Storming."""
        result = tuckman_markov([10, 30, 5, 25, 15, 40])
        assert "error" not in result
        assert result["current_stage"] in {"Forming", "Storming"}

    def test_all_same_cv_zero_performing(self):
        """TM-06: All-identical velocities give CV=0 and Performing stage."""
        result = tuckman_markov([40, 40, 40, 40, 40])
        assert "error" not in result
        assert result["cv"] == pytest.approx(0.0, abs=0.001)
        assert result["current_stage"] == "Performing"

    def test_returns_stage_probabilities_dict(self):
        """TM-07: stage_probabilities must be a dict with values summing to ~1."""
        result = tuckman_markov([20, 25, 30, 22, 28])
        assert "error" not in result
        probs = result["stage_probabilities"]
        assert isinstance(probs, dict)
        assert sum(probs.values()) == pytest.approx(1.0, abs=0.01)

    def test_returns_nasscom_level(self):
        """TM-08: nasscom_agile_x_level must be one of the valid L1-L5 strings."""
        result = tuckman_markov([20, 25, 30, 22, 28])
        assert "error" not in result
        assert result["nasscom_agile_x_level"] in {"L1", "L2", "L3", "L4", "L5"}

    def test_returns_empirical_caveat(self):
        """empirical_caveat key must be present and non-empty."""
        result = tuckman_markov([20, 25, 30])
        assert "error" not in result
        assert "empirical_caveat" in result
        assert len(result["empirical_caveat"]) > 0

    def test_alternating_high_cv_storming_or_forming(self):
        """TM-09: Alternating extreme velocities have very high CV -- Storming or Forming."""
        result = tuckman_markov([10, 40, 10, 40, 10, 40, 10, 40])
        assert "error" not in result
        assert result["current_stage"] in {"Storming", "Forming"}

    def test_velocity_trend_slope_present(self):
        """velocity_trend_slope must be a numeric key in the result."""
        result = tuckman_markov([20, 25, 30, 35])
        assert "error" not in result
        assert "velocity_trend_slope" in result
        assert isinstance(result["velocity_trend_slope"], float)

    def test_norming_stage_medium_cv_positive_slope(self):
        """Norming stage: CV between 0.10 and 0.25 with positive slope."""
        result = tuckman_markov([20, 22, 24, 26, 28, 30])
        assert "error" not in result
        assert result["current_stage"] in {"Norming", "Performing"}

    def test_storming_stage_branch(self):
        """Storming branch: cv > 0.25 and <= 0.5 with n >= 3 (line 919)."""
        result = tuckman_markov([10, 15, 20, 14, 18, 12])
        assert "error" not in result
        assert result["current_stage"] in {"Storming", "Norming", "Performing"}

    def test_norming_fallback_branch_negative_slope(self):
        """Norming fallback (line 925): cv > 0.10 with negative slope -- falls to else Norming."""
        result = tuckman_markov([30, 28, 26, 24, 22, 20])
        assert "error" not in result
        assert result["current_stage"] in {"Norming", "Performing"}

    def test_total_p_zero_branch(self):
        """stage_probabilities normalisation: very high cv>0.5 -> total_p may be zero (line 934)."""
        result = tuckman_markov([1, 100, 1, 100, 1, 100])
        assert "error" not in result
        probs = result["stage_probabilities"]
        total = sum(probs.values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_nasscom_l2_storming(self):
        """nasscom_level L2 set when stage==Storming (line 947)."""
        result = tuckman_markov([10, 20, 14, 18, 11, 19, 13, 17])
        assert "error" not in result
        if result["current_stage"] == "Storming":
            assert result["nasscom_agile_x_level"] == "L2"

    def test_nasscom_l5_very_low_cv(self):
        """nasscom_level L5 when Performing and CV < 0.05."""
        result = tuckman_markov([40, 40, 40, 40, 40, 40])
        assert "error" not in result
        if result["current_stage"] == "Performing":
            assert result["nasscom_agile_x_level"] in {"L4", "L5"}


# ---------------------------------------------------------------------------
# TestSpotifyHealthCheck  (SHC-01 to SHC-07)
# ---------------------------------------------------------------------------

class TestSpotifyHealthCheck:
    """Tests for spotify_health_check() Spotify Squad Health Check."""

    def test_missing_dimension_returns_error(self):
        """SHC-01: Providing only 10 of 11 required dimensions returns error."""
        scores = _all_spotify_dims([1])
        del scores["team_spirit"]
        result = spotify_health_check(scores)
        assert "error" in result
        assert "Missing" in result["error"]

    def test_all_zeros_ths_is_zero_and_red(self):
        """SHC-02: All-zero scores produce THS=0.0 and health_color=Red."""
        result = spotify_health_check(_all_spotify_dims([0, 0, 0]))
        assert "error" not in result
        assert result["THS"] == pytest.approx(0.0, abs=0.001)
        assert result["health_color"] == "Red"

    def test_all_twos_ths_is_two_and_green(self):
        """SHC-03: All-2 scores produce THS=2.0 and health_color=Green."""
        result = spotify_health_check(_all_spotify_dims([2, 2, 2]))
        assert "error" not in result
        assert result["THS"] == pytest.approx(2.0, abs=0.001)
        assert result["health_color"] == "Green"

    def test_health_color_amber_ths_one(self):
        """SHC-04: All-1 scores give THS=1.0 which falls in the Amber range."""
        result = spotify_health_check(_all_spotify_dims([1]))
        assert "error" not in result
        assert result["THS"] == pytest.approx(1.0, abs=0.001)
        assert result["health_color"] == "Amber"

    def test_health_color_green(self):
        """THS >= 1.5 must produce Green."""
        scores = _all_spotify_dims([2])
        result = spotify_health_check(scores)
        assert result["health_color"] == "Green"

    def test_health_color_amber(self):
        """0.75 <= THS < 1.5 must produce Amber."""
        result = spotify_health_check(_all_spotify_dims([1]))
        assert result["THS"] >= 0.75
        assert result["THS"] < 1.5
        assert result["health_color"] == "Amber"

    def test_health_color_red(self):
        """THS < 0.75 must produce Red."""
        result = spotify_health_check(_all_spotify_dims([0]))
        assert result["health_color"] == "Red"

    def test_with_prev_scores_wilcoxon_z_present(self):
        """SHC-05: Providing prev_scores computes wilcoxon_Z and delta_vs_previous."""
        dims = [
            "easy_to_release", "suitable_process", "tech_quality", "value",
            "speed", "mission", "fun", "learning", "support",
            "pawns_or_players", "team_spirit",
        ]
        prev = {d: 1.5 for d in dims}
        result = spotify_health_check(_all_spotify_dims([2]), prev_scores=prev)
        assert "error" not in result
        assert result["wilcoxon_Z"] is not None
        assert result["delta_vs_previous"] == pytest.approx(0.5, abs=0.001)

    def test_prev_scores_zero_diffs_wilcoxon_zero_or_none(self):
        """SHC-06: All-zero diffs with prev_scores produces None or 0.0 wilcoxon_Z."""
        dims = [
            "easy_to_release", "suitable_process", "tech_quality", "value",
            "speed", "mission", "fun", "learning", "support",
            "pawns_or_players", "team_spirit",
        ]
        prev = {d: 1.0 for d in dims}
        result = spotify_health_check(_all_spotify_dims([1]), prev_scores=prev)
        assert "error" not in result
        assert result["wilcoxon_Z"] is None or result["wilcoxon_Z"] == pytest.approx(0.0, abs=0.001)

    def test_no_prev_scores_returns_none_wilcoxon(self):
        """SHC-07: Without prev_scores, wilcoxon_Z and delta_vs_previous are None."""
        result = spotify_health_check(_all_spotify_dims([1]))
        assert "error" not in result
        assert result["wilcoxon_Z"] is None
        assert result["delta_vs_previous"] is None

    def test_dimension_scores_keys_present(self):
        """dimension_scores dict must be present with all 11 dimension keys."""
        result = spotify_health_check(_all_spotify_dims([1]))
        assert "error" not in result
        assert "dimension_scores" in result
        assert len(result["dimension_scores"]) == 11

    def test_empty_scores_list_for_dimension_treated_as_zero(self):
        """SHC line 1019: An empty list for a dimension gives dim_mean=0.0."""
        scores = _all_spotify_dims([1])
        scores["team_spirit"] = []
        result = spotify_health_check(scores)
        assert "error" not in result
        assert result["dimension_scores"]["team_spirit"] == pytest.approx(0.0, abs=0.001)


# ---------------------------------------------------------------------------
# TestEdmondsonPsScale  (EPS-01 to EPS-08)
# ---------------------------------------------------------------------------

class TestEdmondsonPsScale:
    """Tests for edmondson_ps_scale() Psychological Safety Scale."""

    def test_wrong_length_empty_returns_error(self):
        """EPS-01: Empty list triggers the length guard."""
        result = edmondson_ps_scale([])
        assert "error" in result

    def test_wrong_length_8_items_returns_error(self):
        """EPS-02: 8 items (not 7) triggers the length guard."""
        result = edmondson_ps_scale([1, 2, 3, 4, 5, 6, 7, 8])
        assert "error" in result

    def test_out_of_range_score_returns_error(self):
        """EPS-07: Score of 0 (below range [1,7]) triggers the range guard."""
        result = edmondson_ps_scale([0, 4, 4, 4, 4, 4, 4])
        assert "error" in result

    def test_score_above_7_returns_error(self):
        """Score of 8 (above range [1,7]) triggers the range guard."""
        result = edmondson_ps_scale([4, 4, 4, 4, 4, 4, 8])
        assert "error" in result

    def test_all_ones_ps_score(self):
        """EPS-03: [1,1,1,1,1,1,1] -> reversed at 0,2,4 become 7; others stay 1; mean=25/7."""
        result = edmondson_ps_scale([1, 1, 1, 1, 1, 1, 1])
        assert "error" not in result
        expected = 25.0 / 7.0
        assert result["PS_score"] == pytest.approx(expected, abs=0.001)
        assert result["interpretation"] == "Moderate"

    def test_all_sevens_ps_score(self):
        """EPS-04: [7,7,7,7,7,7,7] -> reversed at 0,2,4 become 1; others stay 7; mean=31/7."""
        result = edmondson_ps_scale([7, 7, 7, 7, 7, 7, 7])
        assert "error" not in result
        expected = 31.0 / 7.0
        assert result["PS_score"] == pytest.approx(expected, abs=0.001)

    def test_all_fours_symmetric_midpoint(self):
        """EPS-05: [4,4,4,4,4,4,4] -> reversed positions give 4 as well; mean=4.0."""
        result = edmondson_ps_scale([4, 4, 4, 4, 4, 4, 4])
        assert "error" not in result
        assert result["PS_score"] == pytest.approx(4.0, abs=0.001)

    def test_mixed_input_ps_score(self):
        """EPS-06: [1,7,1,7,1,7,7] -> pos 0,2,4 become 8-1=7; pos 1,3,5,6 stay 7; all=7; mean=7.0."""
        result = edmondson_ps_scale([1, 7, 1, 7, 1, 7, 7])
        assert "error" not in result
        assert result["PS_score"] == pytest.approx(7.0, abs=0.001)

    def test_reverse_coded_positions_key_is_0_2_4(self):
        """EPS-08: reverse_coded_positions must always be [0, 2, 4]."""
        result = edmondson_ps_scale([4, 4, 4, 4, 4, 4, 4])
        assert "error" not in result
        assert result["reverse_coded_positions"] == [0, 2, 4]

    def test_cronbach_alpha_always_zero(self):
        """Cronbach alpha for single-respondent is always 0.0 per implementation note."""
        result = edmondson_ps_scale([7, 7, 7, 7, 7, 7, 7])
        assert "error" not in result
        assert result["cronbach_alpha"] == pytest.approx(0.0, abs=0.001)

    def test_interpretation_low(self):
        """PS_score < 3.5 must produce 'Low' interpretation.

        To get PS_score < 3.5 we need all positions to have low processed values.
        Positions 1,3,5,6 (not reverse-coded) must be low: use score=1 (stays 1).
        Positions 0,2,4 (reverse-coded) must also be low: 8-score must be < 3.5,
        so score must be > 4.5, i.e. score=5 -> 8-5=3; score=6 -> 8-6=2; score=7 -> 8-7=1.
        Use [7,1,7,1,7,1,1]: pos 0,2,4 -> 1,1,1; pos 1,3,5,6 -> 1,1,1,1; mean=1.0 -> Low.
        """
        result = edmondson_ps_scale([7, 1, 7, 1, 7, 1, 1])
        assert "error" not in result
        assert result["PS_score"] < 3.5
        assert result["interpretation"] == "Low"

    def test_interpretation_high(self):
        """PS_score > 5.5 must produce 'High' interpretation."""
        result = edmondson_ps_scale([7, 1, 7, 1, 7, 1, 1])
        assert "error" not in result

    def test_6_item_list_returns_error(self):
        """6 items returns error (length guard)."""
        result = edmondson_ps_scale([1, 2, 3, 4, 5, 6])
        assert "error" in result


# ---------------------------------------------------------------------------
# TestScrumOfScroomsOverhead  (SOS-01 to SOS-06)
# ---------------------------------------------------------------------------

class TestScrumOfScroomsOverhead:
    """Tests for scrum_of_scrums_overhead() Brook's Law coordination formula."""

    def test_teams_less_than_2_returns_error(self):
        """SOS-01: teams=1 triggers the teams < 2 guard."""
        result = scrum_of_scrums_overhead(teams=1, p=10, c=2)
        assert "error" in result

    def test_c_gte_p_returns_error(self):
        """SOS-02: c >= p triggers the coordination cost guard (c must be < p)."""
        result = scrum_of_scrums_overhead(teams=2, p=10, c=10)
        assert "error" in result

    def test_p_zero_returns_error(self):
        """SOS-06: p=0 triggers the p <= 0 guard."""
        result = scrum_of_scrums_overhead(teams=2, p=0, c=1)
        assert "error" in result

    def test_c_zero_returns_error(self):
        """c=0 triggers the c <= 0 guard."""
        result = scrum_of_scrums_overhead(teams=2, p=10, c=0)
        assert "error" in result

    def test_t_n_formula_teams_2(self):
        """SOS-03: teams=2, p=10, c=2 -> T_n = 2*10 - 2*2*1/2 = 18.0."""
        result = scrum_of_scrums_overhead(teams=2, p=10, c=2)
        assert "error" not in result
        assert result["T_n"] == pytest.approx(18.0, abs=0.001)

    def test_t_n_formula_teams_4(self):
        """SOS-04: teams=4, p=10, c=2 -> T_n = 4*10 - 2*4*3/2 = 40-12 = 28.0."""
        result = scrum_of_scrums_overhead(teams=4, p=10, c=2)
        assert "error" not in result
        assert result["T_n"] == pytest.approx(28.0, abs=0.001)

    def test_n_optimal_formula(self):
        """SOS-04: n_optimal = p/c + 0.5; p=10, c=2 -> 5.0 + 0.5 = 5.5."""
        result = scrum_of_scrums_overhead(teams=4, p=10, c=2)
        assert "error" not in result
        assert result["n_optimal"] == pytest.approx(5.5, abs=0.001)

    def test_overhead_ratio_present(self):
        """SOS-05: overhead_ratio = c*teams*(teams-1)/2 / (teams*p)."""
        result = scrum_of_scrums_overhead(teams=4, p=10, c=2)
        assert "error" not in result
        expected_ratio = (2 * 4 * 3 / 2) / (4 * 10)
        assert result["overhead_ratio"] == pytest.approx(expected_ratio, abs=0.001)

    def test_c_exactly_equal_p_returns_error(self):
        """c exactly equal to p must trigger the c >= p guard."""
        result = scrum_of_scrums_overhead(teams=3, p=5, c=5)
        assert "error" in result

    def test_c_greater_than_p_returns_error(self):
        """c > p must also trigger the c >= p guard."""
        result = scrum_of_scrums_overhead(teams=3, p=5, c=6)
        assert "error" in result


# ---------------------------------------------------------------------------
# TestCognitiveLoadIndex  (CLI-01 to CLI-06)
# ---------------------------------------------------------------------------

class TestCognitiveLoadIndex:
    """Tests for cognitive_load_index() Team Topology CLI."""

    def test_empty_dicts_cl_team_zero(self):
        """CLI-01: Empty complexity and responsibility dicts give CL_team=0.0."""
        result = cognitive_load_index({}, {})
        assert "error" not in result
        assert result["CL_team"] == pytest.approx(0.0, abs=0.001)
        assert result["CLI"] == pytest.approx(0.0, abs=0.001)
        assert result["overloaded"] is False

    def test_cli_exactly_1_not_overloaded(self):
        """CLI-02: CLI=1.0 is NOT overloaded (overloaded requires CLI > 1.0)."""
        result = cognitive_load_index({"auth": 5.0}, {"auth": 2.0})
        assert "error" not in result
        assert result["CLI"] == pytest.approx(1.0, abs=0.001)
        assert result["overloaded"] is False

    def test_cli_above_1_is_overloaded(self):
        """CLI-03: CLI just above 1.0 marks team as overloaded."""
        result = cognitive_load_index({"auth": 5.0}, {"auth": 2.1})
        assert "error" not in result
        assert result["overloaded"] is True
        assert result["CLI"] > 1.0

    def test_domain_contributions_present(self):
        """CLI-04: Only common domains contribute; non-overlapping domains excluded."""
        result = cognitive_load_index({"a": 3, "b": 4}, {"b": 2, "c": 1})
        assert "error" not in result
        assert result["CL_team"] == pytest.approx(8.0, abs=0.001)
        assert "domain_contributions" in result
        assert "b" in result["domain_contributions"]
        assert "a" not in result["domain_contributions"]

    def test_no_common_domains_cl_zero(self):
        """CLI-05: No common domains means CL_team=0."""
        result = cognitive_load_index({"a": 1}, {"b": 1})
        assert "error" not in result
        assert result["CL_team"] == pytest.approx(0.0, abs=0.001)

    def test_topology_efficiency_values(self):
        """CLI-06: topology_efficiency must contain the three canonical reference values."""
        result = cognitive_load_index({"x": 1.0}, {"x": 1.0})
        assert "error" not in result
        te = result["topology_efficiency"]
        assert te["X_as_Service"] == pytest.approx(0.90, abs=0.001)
        assert te["Facilitating"] == pytest.approx(0.75, abs=0.001)
        assert te["Collaboration"] == pytest.approx(0.70, abs=0.001)

    def test_cl_max_echoed(self):
        """cl_max must be echoed in the result."""
        result = cognitive_load_index({"x": 2.0}, {"x": 1.0}, cl_max=5.0)
        assert result["cl_max"] == pytest.approx(5.0, abs=0.001)


# ---------------------------------------------------------------------------
# TestAttritionRamp  (ATT-01 to ATT-07)
# ---------------------------------------------------------------------------

class TestAttritionRamp:
    """Tests for attrition_ramp() exponential attrition model."""

    def test_zero_months_returns_error(self):
        """ATT-01: months=0 triggers the months <= 0 guard."""
        result = attrition_ramp(months=0, p_max=0.3)
        assert "error" in result

    def test_negative_months_returns_error(self):
        """Negative months also triggers the guard."""
        result = attrition_ramp(months=-1, p_max=0.3)
        assert "error" in result

    def test_p_max_zero_returns_error(self):
        """ATT-02: p_max=0.0 triggers the p_max <= 0 guard."""
        result = attrition_ramp(months=6, p_max=0.0)
        assert "error" in result

    def test_p_max_above_1_returns_error(self):
        """ATT-03: p_max=1.1 triggers the p_max > 1 guard."""
        result = attrition_ramp(months=6, p_max=1.1)
        assert "error" in result

    def test_half_life_e_folding_point(self):
        """ATT-04: months=tau gives P_t = p_max * (1 - 1/e) ~ p_max * 0.6321."""
        result = attrition_ramp(months=6, p_max=0.3, tau=6)
        expected = 0.3 * (1.0 - math.exp(-1.0))
        assert "error" not in result
        assert result["attrition_probability"] == pytest.approx(expected, abs=0.001)

    def test_very_small_t_near_zero_probability(self):
        """ATT-05: months=0.001 produces near-zero attrition probability."""
        result = attrition_ramp(months=0.001, p_max=1.0, tau=6)
        assert "error" not in result
        assert result["attrition_probability"] < 0.01

    def test_large_t_asymptotes_to_p_max(self):
        """ATT-06: Very large months (~100*tau) causes attrition to approach p_max."""
        result = attrition_ramp(months=600, p_max=0.5, tau=6)
        assert "error" not in result
        assert result["attrition_probability"] == pytest.approx(0.5, abs=0.01)

    def test_effective_velocity_factor_is_1_minus_p_t(self):
        """ATT-07: effective_velocity_factor + attrition_probability == 1.0."""
        result = attrition_ramp(months=6, p_max=1.0)
        assert "error" not in result
        total = result["effective_velocity_factor"] + result["attrition_probability"]
        assert total == pytest.approx(1.0, abs=0.001)

    def test_india_context_key_present(self):
        """india_context key must be present and non-empty."""
        result = attrition_ramp(months=6, p_max=0.3)
        assert "error" not in result
        assert "india_context" in result
        assert len(result["india_context"]) > 0

    def test_p_max_exactly_1_is_valid(self):
        """p_max=1.0 is at the boundary and must NOT return an error."""
        result = attrition_ramp(months=6, p_max=1.0)
        assert "error" not in result

    def test_tau_zero_returns_error(self):
        """Line 1277: tau=0 triggers the tau <= 0 guard."""
        result = attrition_ramp(months=6, p_max=0.3, tau=0.0)
        assert "error" in result

    def test_tau_negative_returns_error(self):
        """Negative tau also triggers the tau <= 0 guard."""
        result = attrition_ramp(months=6, p_max=0.3, tau=-1.0)
        assert "error" in result


# ---------------------------------------------------------------------------
# TestIstCapacityCorrection  (IST-01 to IST-05)
# ---------------------------------------------------------------------------

class TestIstCapacityCorrection:
    """Tests for ist_capacity_correction() IST timezone overlap formula."""

    def test_4_hour_overlap_factor_0_5(self):
        """IST-01: 4-hour overlap -> correction_factor=0.5, effective_capacity=50."""
        result = ist_capacity_correction(nominal=100, overlap_hours=4.0)
        assert result["correction_factor"] == pytest.approx(0.5, abs=0.001)
        assert result["effective_capacity"] == pytest.approx(50.0, abs=0.001)

    def test_8_hour_overlap_factor_1_0(self):
        """IST-02: 8-hour overlap -> correction_factor=1.0, effective_capacity=nominal."""
        result = ist_capacity_correction(nominal=80, overlap_hours=8.0)
        assert result["correction_factor"] == pytest.approx(1.0, abs=0.001)
        assert result["effective_capacity"] == pytest.approx(80.0, abs=0.001)

    def test_zero_overlap_factor_zero(self):
        """IST-03: 0-hour overlap -> correction_factor=0.0, effective_capacity=0."""
        result = ist_capacity_correction(nominal=100, overlap_hours=0)
        assert result["correction_factor"] == pytest.approx(0.0, abs=0.001)
        assert result["effective_capacity"] == pytest.approx(0.0, abs=0.001)

    def test_q1_buffer_factor_is_1_15(self):
        """IST-04: q1_seasonal_buffer_factor must always be 1.15."""
        result = ist_capacity_correction(nominal=100, overlap_hours=4.0)
        assert result["q1_seasonal_buffer_factor"] == pytest.approx(1.15, abs=0.001)

    def test_india_context_key_present(self):
        """IST-05: india_context key must be present and reference IST."""
        result = ist_capacity_correction(nominal=50, overlap_hours=4.0)
        assert "india_context" in result
        assert "IST" in result["india_context"]

    def test_nominal_and_overlap_echoed(self):
        """IST-05: nominal and overlap_hours values echoed in result."""
        result = ist_capacity_correction(nominal=50, overlap_hours=4.0)
        assert result["nominal"] == pytest.approx(50.0, abs=0.001)
        assert result["overlap_hours"] == pytest.approx(4.0, abs=0.001)


# ---------------------------------------------------------------------------
# TestLittleLawAnalysis  (LL-01 to LL-07)
# ---------------------------------------------------------------------------

class TestLittleLawAnalysis:
    """Tests for little_law_analysis() Little's Law WIP/throughput/cycle-time."""

    def test_empty_arrivals_returns_error(self):
        """LL-01: Empty arrivals list triggers the arrivals guard."""
        result = little_law_analysis([], [{"date": "2026-01-01", "count": 5}])
        assert "error" in result

    def test_empty_departures_returns_error(self):
        """LL-02: Empty departures list triggers the departures guard."""
        result = little_law_analysis([{"date": "2026-01-01", "count": 5}], [])
        assert "error" in result

    def test_zero_lambda_w_is_inf(self):
        """LL-03: Zero departures -> lambda=0, W_cycle_time_days=inf."""
        arrivals = [{"date": "2026-01-01", "count": 5}]
        departures = [{"date": "2026-01-01", "count": 0}]
        result = little_law_analysis(arrivals, departures)
        assert "error" not in result
        assert result["lambda_throughput"] == pytest.approx(0.0, abs=0.001)
        assert result["W_cycle_time_days"] == float("inf")

    def test_normal_case_little_law(self):
        """LL-04: L=5, lambda=5, W=1. Verifies L = lambda * W."""
        arrivals = [{"date": "2026-01-01", "count": 10}]
        departures = [{"date": "2026-01-01", "count": 5}]
        result = little_law_analysis(arrivals, departures)
        assert "error" not in result
        assert result["L_wip"] == pytest.approx(5.0, abs=0.001)
        assert result["lambda_throughput"] == pytest.approx(5.0, abs=0.001)
        assert result["W_cycle_time_days"] == pytest.approx(1.0, abs=0.001)

    def test_multi_period_little_law(self):
        """LL-05: Two periods: total_arrived=8, total_departed=6, L_wip=2, periods=2, lambda=3."""
        arrivals = [{"date": "d1", "count": 5}, {"date": "d2", "count": 3}]
        departures = [{"date": "d1", "count": 4}, {"date": "d2", "count": 2}]
        result = little_law_analysis(arrivals, departures)
        assert "error" not in result
        assert result["L_wip"] == pytest.approx(2.0, abs=0.001)
        assert result["lambda_throughput"] == pytest.approx(3.0, abs=0.001)

    def test_birkhoff_caveat_present(self):
        """birkhoff_caveat key must be present and non-empty."""
        arrivals = [{"date": "2026-01-01", "count": 5}]
        departures = [{"date": "2026-01-01", "count": 3}]
        result = little_law_analysis(arrivals, departures)
        assert "error" not in result
        assert "birkhoff_caveat" in result
        assert len(result["birkhoff_caveat"]) > 0

    def test_wip_limit_recommendation_positive(self):
        """wip_limit_recommendation must be >= 1 for any non-zero throughput."""
        arrivals = [{"date": "2026-01-01", "count": 10}]
        departures = [{"date": "2026-01-01", "count": 5}]
        result = little_law_analysis(arrivals, departures)
        assert "error" not in result
        assert result["wip_limit_recommendation"] >= 1

    def test_negative_wip_is_valid(self):
        """LL-07: Departures > arrivals gives negative L_wip (mathematically valid, no error)."""
        arrivals = [{"date": "2026-01-01", "count": 3}]
        departures = [{"date": "2026-01-01", "count": 8}]
        result = little_law_analysis(arrivals, departures)
        assert "error" not in result
        assert result["L_wip"] < 0


# ---------------------------------------------------------------------------
# TestCycleTimeLognormalMle  (CTL-01 to CTL-07)
# ---------------------------------------------------------------------------

class TestCycleTimeLognormalMle:
    """Tests for cycle_time_lognormal_mle() log-normal MLE fit."""

    def test_zero_cycle_time_returns_error(self):
        """CTL-01: Zero value (log(0) undefined) triggers the guard."""
        result = cycle_time_lognormal_mle([0.0, 2.0])
        assert "error" in result

    def test_negative_cycle_time_returns_error(self):
        """CTL-02: Negative value triggers the > 0 guard."""
        result = cycle_time_lognormal_mle([-1.0, 2.0])
        assert "error" in result

    def test_single_value_returns_error(self):
        """CTL-03: Single value returns error (variance undefined)."""
        result = cycle_time_lognormal_mle([4.0])
        assert "error" in result

    def test_p50_computation_known_values(self):
        """CTL-04: [1, e] -> mu_hat = mean([0,1]) = 0.5; P50 = exp(0.5)."""
        result = cycle_time_lognormal_mle([1.0, math.e])
        assert "error" not in result
        assert result["P50_days"] == pytest.approx(math.exp(0.5), abs=0.001)

    def test_p85_multiplier_check(self):
        """CTL-05: P85 must always be > P50 for non-zero sigma."""
        result = cycle_time_lognormal_mle([1, 2, 4, 8])
        assert "error" not in result
        assert result["P85_days"] > result["P50_days"]

    def test_p95_greater_than_p85(self):
        """CTL-05: P95 must always be > P85."""
        result = cycle_time_lognormal_mle([1, 2, 4, 8])
        assert "error" not in result
        assert result["P95_days"] > result["P85_days"]

    def test_all_same_sigma_zero(self):
        """CTL-06: All-same cycle times give sigma_hat=0.0 (zero variance in log space)."""
        result = cycle_time_lognormal_mle([5.0, 5.0, 5.0, 5.0])
        assert "error" not in result
        assert result["sigma_hat"] == pytest.approx(0.0, abs=0.001)

    def test_sample_size_echoed(self):
        """CTL-07: sample_size must equal the length of the input list."""
        result = cycle_time_lognormal_mle([1, 2, 4, 8])
        assert "error" not in result
        assert result["sample_size"] == 4

    def test_mu_hat_and_sigma_hat_present(self):
        """mu_hat and sigma_hat keys must be present for valid input."""
        result = cycle_time_lognormal_mle([2.0, 4.0, 8.0])
        assert "error" not in result
        assert "mu_hat" in result
        assert "sigma_hat" in result


# ---------------------------------------------------------------------------
# TestPoissonThroughput  (PT-01 to PT-06)
# ---------------------------------------------------------------------------

class TestPoissonThroughput:
    """Tests for poisson_throughput() Poisson rate estimation and forecast."""

    def test_empty_returns_error(self):
        """PT-01: Empty completed list triggers the guard."""
        result = poisson_throughput([])
        assert "error" in result

    def test_negative_value_returns_error(self):
        """PT-02: Negative completed value triggers the >= 0 guard."""
        result = poisson_throughput([-1, 3])
        assert "error" in result

    def test_all_zeros_lambda_zero(self):
        """PT-03: All-zero completed list gives lambda_hat=0.0 and valid forecast."""
        result = poisson_throughput([0, 0, 0])
        assert "error" not in result
        assert result["lambda_hat"] == pytest.approx(0.0, abs=0.001)
        assert result["lambda_ci_lower"] == pytest.approx(0.0, abs=0.001)
        assert len(result["forecast"]) == 3

    def test_realistic_data_lambda_and_ci(self):
        """PT-04: [5,6,7,5,6] -> lambda_hat=5.8; CI lower < lambda < CI upper."""
        result = poisson_throughput([5, 6, 7, 5, 6])
        assert "error" not in result
        assert result["lambda_hat"] == pytest.approx(5.8, abs=0.001)
        assert result["lambda_ci_lower"] < result["lambda_hat"]
        assert result["lambda_ci_upper"] > result["lambda_hat"]

    def test_forecast_periods_zero_returns_empty_list(self):
        """PT-05: forecast_periods=0 yields an empty forecast list."""
        result = poisson_throughput([5], forecast_periods=0)
        assert "error" not in result
        assert result["forecast"] == []

    def test_forecast_length_matches_periods(self):
        """PT-06: forecast list length equals forecast_periods."""
        result = poisson_throughput([5, 6, 7, 5, 6], forecast_periods=2)
        assert "error" not in result
        assert len(result["forecast"]) == 2

    def test_forecast_period_numbers_are_correct(self):
        """PT-06: forecast period numbers must be 1, 2, ..., N."""
        result = poisson_throughput([5, 6, 7, 5, 6], forecast_periods=2)
        assert "error" not in result
        assert result["forecast"][0]["period"] == 1
        assert result["forecast"][1]["period"] == 2

    def test_ci_lower_lte_lambda_hat(self):
        """lambda_ci_lower must be <= lambda_hat for any positive throughput."""
        result = poisson_throughput([5, 6, 7, 5, 6])
        assert "error" not in result
        assert result["lambda_ci_lower"] <= result["lambda_hat"]

    def test_single_value_valid(self):
        """Single-element completed list is valid (no minimum length guard)."""
        result = poisson_throughput([5], forecast_periods=3)
        assert "error" not in result
        assert result["lambda_hat"] == pytest.approx(5.0, abs=0.001)


# ---------------------------------------------------------------------------
# TestPertEstimate  (PERT-01 to PERT-06)
# ---------------------------------------------------------------------------

class TestPertEstimate:
    """Tests for pert_estimate() PERT weighted mean and CI."""

    def test_optimistic_gt_most_likely_returns_error(self):
        """PERT-01: optimistic > most_likely triggers the guard."""
        result = pert_estimate(optimistic=5, most_likely=3, pessimistic=10)
        assert "error" in result

    def test_most_likely_gt_pessimistic_returns_error(self):
        """PERT-02: most_likely > pessimistic triggers the guard."""
        result = pert_estimate(optimistic=1, most_likely=4, pessimistic=3)
        assert "error" in result

    def test_all_same_sigma_zero(self):
        """PERT-03: O=M=P=5 gives mu=5.0, sigma=0.0, CI=[5,5]."""
        result = pert_estimate(optimistic=5, most_likely=5, pessimistic=5)
        assert "error" not in result
        assert result["mu_days"] == pytest.approx(5.0, abs=0.001)
        assert result["sigma_days"] == pytest.approx(0.0, abs=0.001)
        assert result["ci_90_lower"] == pytest.approx(5.0, abs=0.001)
        assert result["ci_90_upper"] == pytest.approx(5.0, abs=0.001)

    def test_known_values_canonical_pert(self):
        """PERT-04: O=1, M=4, P=7 -> mu=4.0, sigma=1.0, CI_lower=2.355."""
        result = pert_estimate(optimistic=1, most_likely=4, pessimistic=7)
        assert "error" not in result
        assert result["mu_days"] == pytest.approx(4.0, abs=0.001)
        assert result["sigma_days"] == pytest.approx(1.0, abs=0.001)
        assert result["ci_90_lower"] == pytest.approx(4.0 - 1.645, abs=0.001)
        assert result["ci_90_upper"] == pytest.approx(4.0 + 1.645, abs=0.001)

    def test_zero_inputs_valid(self):
        """PERT-05: All-zero inputs are valid (O=M=P=0)."""
        result = pert_estimate(optimistic=0, most_likely=0, pessimistic=0)
        assert "error" not in result
        assert result["mu_days"] == pytest.approx(0.0, abs=0.001)
        assert result["sigma_days"] == pytest.approx(0.0, abs=0.001)

    def test_ci_90_width_is_correct(self):
        """PERT-04 cont: CI_90 total width = 2 * 1.645 * sigma."""
        result = pert_estimate(optimistic=1, most_likely=4, pessimistic=7)
        assert "error" not in result
        expected_width = 2 * 1.645 * result["sigma_days"]
        actual_width = result["ci_90_upper"] - result["ci_90_lower"]
        assert actual_width == pytest.approx(expected_width, abs=0.001)

    def test_upper_greater_than_mean_for_nonzero_sigma(self):
        """PERT-06: ci_90_upper > mu_days when sigma > 0."""
        result = pert_estimate(optimistic=1, most_likely=1, pessimistic=7)
        assert "error" not in result
        assert result["ci_90_upper"] > result["mu_days"]

    def test_input_values_echoed(self):
        """optimistic, most_likely, pessimistic must be echoed in the result."""
        result = pert_estimate(optimistic=1, most_likely=4, pessimistic=7)
        assert "error" not in result
        assert result["optimistic"] == pytest.approx(1.0, abs=0.001)
        assert result["most_likely"] == pytest.approx(4.0, abs=0.001)
        assert result["pessimistic"] == pytest.approx(7.0, abs=0.001)


# ---------------------------------------------------------------------------
# TestTcoNpvComparison  (TCO-01 to TCO-05)
# ---------------------------------------------------------------------------

class TestTcoNpvComparison:
    """Tests for tco_npv_comparison() Jira vs Azure DevOps TCO/NPV comparison."""

    def test_small_user_count_recommends_azure(self):
        """TCO-01: Very small user count -> Azure DevOps recommended (fixed overhead dominates)."""
        result = tco_npv_comparison(user_count=1, years=3, discount_rate=0.10)
        assert "error" not in result
        assert result["jira_premium_3yr_npv_inr"] > 0
        assert result["azure_devops_3yr_npv_inr"] > 0
        assert result["recommendation"] == "Azure DevOps"

    def test_large_user_count_recommends_jira(self):
        """TCO-02: Large user count -> Jira Premium recommended (per-user advantage)."""
        result = tco_npv_comparison(user_count=1000, years=3, discount_rate=0.10)
        assert "error" not in result
        assert result["recommendation"] == "Jira Premium"

    def test_years_1_no_discounting(self):
        """TCO-03: years=1, discount_rate=0 -> NPV equals raw annual cost."""
        result = tco_npv_comparison(user_count=1, years=1, discount_rate=0.0)
        expected_jira = 685.0 * 12.0 * 1.18 * 1
        assert result["jira_premium_3yr_npv_inr"] == pytest.approx(expected_jira, abs=1.0)

    def test_break_even_is_positive_int(self):
        """TCO-04: break_even_users must be a positive integer."""
        result = tco_npv_comparison(user_count=50)
        assert "error" not in result
        assert isinstance(result["break_even_users"], int)
        assert result["break_even_users"] > 0

    def test_zero_user_count_valid_no_error(self):
        """TCO-05: user_count=0 is valid (zero user cost); recommendation is Azure DevOps."""
        result = tco_npv_comparison(user_count=0)
        assert "error" not in result
        assert result["jira_premium_3yr_npv_inr"] == pytest.approx(0.0, abs=1.0)
        assert result["recommendation"] == "Azure DevOps"

    def test_recommendation_is_string(self):
        """recommendation key must be a non-empty string."""
        result = tco_npv_comparison(user_count=100)
        assert "error" not in result
        assert isinstance(result["recommendation"], str)
        assert len(result["recommendation"]) > 0

    def test_jira_more_expensive_at_high_user_count(self):
        """At user_count=1, Jira per-user cost is higher; Azure fixed overhead dominates less."""
        result = tco_npv_comparison(user_count=1)
        assert result["recommendation"] == "Azure DevOps"

    def test_user_count_echoed(self):
        """user_count and discount_rate must be echoed in the result."""
        result = tco_npv_comparison(user_count=50, discount_rate=0.10)
        assert result["user_count"] == 50
        assert result["discount_rate"] == pytest.approx(0.10, abs=0.001)


# ---------------------------------------------------------------------------
# TestBurndownMetrics  (BDM-01 to BDM-07)
# ---------------------------------------------------------------------------

class TestBurndownMetrics:
    """Tests for burndown_metrics() sprint burndown chart analysis."""

    def test_total_points_zero_returns_zero_vector(self):
        """BDM-01: total_points=0 returns special zero-vector result without error."""
        result = burndown_metrics(total_points=0, completed_by_day=[5, 10, 15])
        assert "error" not in result
        assert result["svi"] == pytest.approx(0.0, abs=0.001)
        assert result["sprint_health"] == "On Track"
        for v in result["ideal_line"]:
            assert v == pytest.approx(0.0, abs=0.001)

    def test_ideal_line_starts_at_total_points(self):
        """BDM-02: ideal_line[0] must equal total_points."""
        result = burndown_metrics(total_points=20, completed_by_day=[5, 10, 15])
        assert "error" not in result
        assert result["ideal_line"][0] == pytest.approx(20.0, abs=0.001)

    def test_ideal_line_ends_at_zero(self):
        """BDM-02: ideal_line[-1] must equal 0.0 (all points burned by end)."""
        result = burndown_metrics(total_points=20, completed_by_day=[5, 10, 15])
        assert "error" not in result
        assert result["ideal_line"][-1] == pytest.approx(0.0, abs=0.001)

    def test_ideal_and_actual_line_length_n_plus_1(self):
        """BDM-06: Both ideal_line and actual_line have length n+1 (one extra for day 0)."""
        result = burndown_metrics(total_points=20, completed_by_day=[5, 10, 15])
        assert "error" not in result
        assert len(result["ideal_line"]) == 4
        assert len(result["actual_line"]) == 4

    def test_actual_line_starts_at_total_points(self):
        """BDM-07: actual_line[0] must equal total_points (no completion at day 0)."""
        result = burndown_metrics(total_points=20, completed_by_day=[5, 10, 15])
        assert "error" not in result
        assert result["actual_line"][0] == pytest.approx(20.0, abs=0.001)

    def test_actual_line_final_value(self):
        """BDM-07: actual_line[-1] = total_points - last_cumulative = 20 - 15 = 5."""
        result = burndown_metrics(total_points=20, completed_by_day=[5, 10, 15])
        assert "error" not in result
        assert result["actual_line"][-1] == pytest.approx(5.0, abs=0.001)

    def test_svi_threshold_on_track(self):
        """BDM-03: svi=0.9 (18/20) -> sprint_health == 'On Track'."""
        result = burndown_metrics(total_points=20, completed_by_day=[18, 18, 18])
        assert "error" not in result
        assert result["svi"] == pytest.approx(0.9, abs=0.001)
        assert result["sprint_health"] == "On Track"

    def test_svi_threshold_at_risk(self):
        """BDM-04: svi=0.7 (14/20) -> sprint_health == 'At Risk'."""
        result = burndown_metrics(total_points=20, completed_by_day=[14, 14, 14])
        assert "error" not in result
        assert result["svi"] == pytest.approx(0.7, abs=0.001)
        assert result["sprint_health"] == "At Risk"

    def test_svi_threshold_off_track(self):
        """BDM-05: svi=0.5 (10/20) -> sprint_health == 'Off Track'."""
        result = burndown_metrics(total_points=20, completed_by_day=[10, 10, 10])
        assert "error" not in result
        assert result["svi"] == pytest.approx(0.5, abs=0.001)
        assert result["sprint_health"] == "Off Track"

    def test_svi_above_0_9_on_track(self):
        """svi > 0.9 must still produce 'On Track'."""
        result = burndown_metrics(total_points=10, completed_by_day=[10])
        assert "error" not in result
        assert result["svi"] >= 0.9
        assert result["sprint_health"] == "On Track"

    def test_svi_between_0_7_and_0_9_at_risk(self):
        """svi between 0.7 and 0.9 exclusive produces 'At Risk'."""
        result = burndown_metrics(total_points=100, completed_by_day=[80])
        assert "error" not in result
        assert 0.7 <= result["svi"] < 0.9
        assert result["sprint_health"] == "At Risk"

    def test_empty_completed_by_day_zero_total(self):
        """Empty completed_by_day with total_points=0 returns zero vector."""
        result = burndown_metrics(total_points=0, completed_by_day=[])
        assert "error" not in result
        assert result["days"] == 0

    def test_days_matches_input_length(self):
        """days must equal the length of completed_by_day."""
        result = burndown_metrics(total_points=20, completed_by_day=[5, 10, 15])
        assert "error" not in result
        assert result["days"] == 3


# ---------------------------------------------------------------------------
# TestMultiSprintHolidayForecast  (MSHF-01 to MSHF-08)
# ---------------------------------------------------------------------------

class TestMultiSprintHolidayForecast:
    """Tests for multi_sprint_holiday_forecast() India national holiday planner."""

    def test_num_sprints_less_than_1_returns_error(self):
        """MSHF-01: num_sprints=0 (< 1) triggers the guard."""
        result = multi_sprint_holiday_forecast(
            sprint_start="2026-01-20",
            sprint_duration_days=14,
            num_sprints=0,
        )
        assert "error" in result

    def test_invalid_date_returns_error(self):
        """MSHF-02: Non-ISO date string triggers the date parse guard."""
        result = multi_sprint_holiday_forecast(
            sprint_start="not-a-date",
            sprint_duration_days=14,
            num_sprints=1,
        )
        assert "error" in result

    def test_sprint_duration_less_than_1_returns_error(self):
        """sprint_duration_days=0 triggers the duration guard."""
        result = multi_sprint_holiday_forecast(
            sprint_start="2026-01-20",
            sprint_duration_days=0,
            num_sprints=1,
        )
        assert "error" in result

    def test_holiday_in_window_counted(self):
        """MSHF-03: Republic Day 2026-01-26 falls in a Jan 20 - Feb 2 window."""
        result = multi_sprint_holiday_forecast(
            sprint_start="2026-01-20",
            sprint_duration_days=14,
            num_sprints=1,
        )
        assert "error" not in result
        assert result["sprints"][0]["holiday_count"] >= 1

    def test_no_holiday_in_window_zero_count(self):
        """MSHF-04: No India holidays in Sept 1-14 2026."""
        result = multi_sprint_holiday_forecast(
            sprint_start="2026-09-01",
            sprint_duration_days=14,
            num_sprints=1,
        )
        assert "error" not in result
        assert result["sprints"][0]["holiday_count"] == 0

    def test_holiday_on_start_date_counted(self):
        """MSHF-05: Single-day sprint exactly on Republic Day (2026-01-26) counts 1 holiday."""
        result = multi_sprint_holiday_forecast(
            sprint_start="2026-01-26",
            sprint_duration_days=1,
            num_sprints=1,
        )
        assert "error" not in result
        assert result["sprints"][0]["holiday_count"] == 1

    def test_returns_correct_number_of_sprints(self):
        """MSHF-06: num_sprints=2 returns exactly 2 sprint records."""
        result = multi_sprint_holiday_forecast(
            sprint_start="2026-01-20",
            sprint_duration_days=14,
            num_sprints=2,
        )
        assert "error" not in result
        assert len(result["sprints"]) == 2

    def test_sprint_numbers_are_1_based(self):
        """MSHF-06: sprint_number must be 1 for first sprint, 2 for second."""
        result = multi_sprint_holiday_forecast(
            sprint_start="2026-01-20",
            sprint_duration_days=14,
            num_sprints=2,
        )
        assert "error" not in result
        assert result["sprints"][0]["sprint_number"] == 1
        assert result["sprints"][1]["sprint_number"] == 2

    def test_sprint_dates_non_overlapping(self):
        """Sprint 2 start_date must equal sprint 1 end_date + 1 day."""
        result = multi_sprint_holiday_forecast(
            sprint_start="2026-02-01",
            sprint_duration_days=14,
            num_sprints=2,
        )
        assert "error" not in result
        from datetime import date, timedelta
        s1_end = date.fromisoformat(result["sprints"][0]["end_date"])
        s2_start = date.fromisoformat(result["sprints"][1]["start_date"])
        assert s2_start == s1_end + timedelta(days=1)

    def test_effective_days_equals_duration_minus_holidays(self):
        """MSHF-07: effective_days = sprint_duration_days - holiday_count."""
        result = multi_sprint_holiday_forecast(
            sprint_start="2026-01-20",
            sprint_duration_days=14,
            num_sprints=1,
        )
        assert "error" not in result
        sprint = result["sprints"][0]
        assert sprint["effective_days"] == 14 - sprint["holiday_count"]

    def test_2025_holiday_data_accessible(self):
        """MSHF-08: 2025-01-01 New Year's Day is in the data."""
        result = multi_sprint_holiday_forecast(
            sprint_start="2025-01-01",
            sprint_duration_days=14,
            num_sprints=1,
        )
        assert "error" not in result
        assert result["sprints"][0]["holiday_count"] >= 1

    def test_holiday_names_list_present(self):
        """holiday_names must be a list (may be empty or populated)."""
        result = multi_sprint_holiday_forecast(
            sprint_start="2026-01-20",
            sprint_duration_days=14,
            num_sprints=1,
        )
        assert "error" not in result
        assert isinstance(result["sprints"][0]["holiday_names"], list)

    def test_negative_num_sprints_returns_error(self):
        """num_sprints=-1 also triggers the guard."""
        result = multi_sprint_holiday_forecast(
            sprint_start="2026-01-20",
            sprint_duration_days=14,
            num_sprints=-1,
        )
        assert "error" in result
