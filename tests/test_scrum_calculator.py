"""
test_scrum_calculator.py -- Unit tests for scrum_calculator.py.

Pure Python, no mocking required. Target: 90%+ coverage.

Windows-Safe: ASCII only (cp1252 compatible)
"""

import pytest
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scrum_calculator
from scrum_calculator import (
    velocity_stats,
    monte_carlo_forecast,
    sprint_capacity,
    wsjf_score,
    mttr_analysis,
    retrospective_effectiveness,
    tuckman_estimate,
    india_holidays_in_sprint,
    INDIA_NATIONAL_HOLIDAYS_2025_2026,
)


# ---------------------------------------------------------------------------
# TestVelocityStats
# ---------------------------------------------------------------------------

class TestVelocityStats:
    """Tests for velocity_stats() covering happy paths and edge cases."""

    def test_normal_input_returns_all_keys(self):
        """Normal multi-sprint velocity list returns dict with all required keys."""
        result = velocity_stats([20, 25, 30, 22, 28])
        required_keys = {
            "mean", "stddev", "cv", "vsi",
            "nasscom_agileX_level", "nasscom_benchmark_note", "sprints_sampled"
        }
        assert required_keys.issubset(result.keys())

    def test_normal_input_mean_correct(self):
        """Mean is computed correctly from sample list."""
        result = velocity_stats([20, 30])
        assert result["mean"] == 25.0

    def test_empty_list_returns_error_dict(self):
        """Empty list does not raise; returns dict with 'error' key."""
        result = velocity_stats([])
        assert "error" in result
        assert "empty" in result["error"].lower()

    def test_single_value_zero_stddev(self):
        """Single velocity value produces stddev of 0.0."""
        result = velocity_stats([40])
        assert result["stddev"] == 0.0
        assert result["sprints_sampled"] == 1

    def test_nasscom_level_l1_high_cv(self):
        """Very high CV (>0.35) maps to L1 maturity level."""
        # Large variance => cv > 0.35
        result = velocity_stats([5, 50, 5, 50])
        assert result["nasscom_agileX_level"] == "L1"

    def test_nasscom_level_l5_low_cv(self):
        """Very low CV (<0.05) maps to L5 maturity level."""
        # Identical values => cv == 0.0
        result = velocity_stats([40, 40, 40, 40, 40])
        assert result["nasscom_agileX_level"] == "L5"

    def test_nasscom_benchmark_below(self):
        """Mean below 35 triggers below-benchmark note."""
        result = velocity_stats([10, 15, 20])
        assert "Below" in result["nasscom_benchmark_note"]

    def test_nasscom_benchmark_within(self):
        """Mean 35-45 triggers within-benchmark note."""
        result = velocity_stats([35, 40, 45])
        assert "Within" in result["nasscom_benchmark_note"]

    def test_nasscom_benchmark_above(self):
        """Mean above 45 triggers above-benchmark note."""
        result = velocity_stats([50, 60, 70])
        assert "Above" in result["nasscom_benchmark_note"]

    def test_vsi_clamped_to_zero_when_cv_gt_one(self):
        """VSI is clamped to 0.0 when cv > 1.0 (extreme variance)."""
        result = velocity_stats([1, 100])
        assert result["vsi"] >= 0.0

    def test_sprints_sampled_matches_input_length(self):
        """sprints_sampled equals the length of the input list."""
        data = [10, 20, 30, 40, 50]
        result = velocity_stats(data)
        assert result["sprints_sampled"] == len(data)


# ---------------------------------------------------------------------------
# TestMonteCarloForecast
# ---------------------------------------------------------------------------

class TestMonteCarloForecast:
    """Tests for monte_carlo_forecast() -- non-deterministic, test structural invariants."""

    def test_p85_gte_p50(self):
        """p85 percentile must always be >= p50 percentile."""
        result = monte_carlo_forecast([20, 25, 30], remaining_points=100, iterations=500)
        assert result["p85"] >= result["p50"]

    def test_p95_gte_p85(self):
        """p95 percentile must always be >= p85 percentile."""
        result = monte_carlo_forecast([20, 25, 30], remaining_points=100, iterations=500)
        assert result["p95"] >= result["p85"]

    def test_empty_samples_raises_value_error(self):
        """Empty velocity_samples raises ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            monte_carlo_forecast([], remaining_points=50)

    def test_all_zero_samples_raises_value_error(self):
        """All-zero velocity samples raises ValueError."""
        with pytest.raises(ValueError, match="zero or negative"):
            monte_carlo_forecast([0, 0, 0], remaining_points=50)

    def test_remaining_points_less_than_one_raises(self):
        """remaining_points < 1 raises ValueError."""
        with pytest.raises(ValueError, match="remaining_points must be >= 1"):
            monte_carlo_forecast([20, 25], remaining_points=0)

    def test_output_has_all_required_keys(self):
        """Output dict contains all seven CONTRACT #3 keys."""
        result = monte_carlo_forecast([20, 25, 30], remaining_points=50, iterations=200)
        required = {"p50", "p70", "p85", "p95", "mean_sprints", "std_sprints", "samples_used"}
        assert required.issubset(result.keys())

    def test_samples_used_equals_positive_count(self):
        """samples_used reflects count of positive-only velocity samples."""
        # Mix: 3 positive, 2 zero
        result = monte_carlo_forecast([0, 10, 0, 20, 30], remaining_points=50, iterations=200)
        assert result["samples_used"] == 3

    def test_negative_samples_filtered_out(self):
        """Negative velocity samples are filtered before simulation."""
        result = monte_carlo_forecast([-5, 20, 25, -10, 30], remaining_points=50, iterations=200)
        assert result["samples_used"] == 3

    def test_mean_sprints_positive(self):
        """Mean sprints is always positive for valid inputs."""
        result = monte_carlo_forecast([20, 25, 30], remaining_points=100, iterations=500)
        assert result["mean_sprints"] > 0


# ---------------------------------------------------------------------------
# TestSprintCapacity
# ---------------------------------------------------------------------------

class TestSprintCapacity:
    """Tests for sprint_capacity()."""

    def test_no_holidays_no_leave(self):
        """Basic capacity with no holidays or leave."""
        result = sprint_capacity(members=5, sprint_days=10, focus_factor=0.7)
        # effective_days = 5*10 = 50; capacity = 50 * 0.7 * 2 = 70
        assert result["capacity_points"] == 70.0
        assert result["india_holidays_excluded"] == 0

    def test_with_india_holidays_reduces_capacity(self):
        """India holidays reduce capacity compared to no-holiday baseline."""
        no_holiday = sprint_capacity(members=5, sprint_days=10, focus_factor=0.7)
        with_holiday = sprint_capacity(members=5, sprint_days=10, focus_factor=0.7, india_holidays=1)
        assert with_holiday["capacity_points"] < no_holiday["capacity_points"]

    def test_with_leave_days_reduces_capacity(self):
        """Leave days reduce effective capacity."""
        no_leave = sprint_capacity(members=5, sprint_days=10, focus_factor=0.7)
        with_leave = sprint_capacity(members=5, sprint_days=10, focus_factor=0.7, leave_days=5)
        assert with_leave["capacity_points"] < no_leave["capacity_points"]

    def test_capacity_never_negative(self):
        """Capacity points are always >= 0 even with excessive holidays/leave."""
        result = sprint_capacity(
            members=2, sprint_days=5, focus_factor=0.7,
            leave_days=100, india_holidays=10
        )
        assert result["capacity_points"] >= 0.0

    def test_members_less_than_one_raises(self):
        """members < 1 raises ValueError."""
        with pytest.raises(ValueError, match="members"):
            sprint_capacity(members=0, sprint_days=10)

    def test_sprint_days_less_than_one_raises(self):
        """sprint_days < 1 raises ValueError."""
        with pytest.raises(ValueError, match="sprint_days"):
            sprint_capacity(members=5, sprint_days=0)

    def test_focus_factor_zero_raises(self):
        """focus_factor <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="focus_factor"):
            sprint_capacity(members=5, sprint_days=10, focus_factor=0.0)

    def test_focus_factor_greater_than_one_raises(self):
        """focus_factor > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="focus_factor"):
            sprint_capacity(members=5, sprint_days=10, focus_factor=1.1)

    def test_output_contains_ist_timezone_note(self):
        """Output contains the IST timezone coordination note."""
        result = sprint_capacity(members=5, sprint_days=10)
        assert "IST" in result["ist_timezone_note"]

    def test_effective_team_days_matches_capacity_days(self):
        """effective_team_days and capacity_days are identical in output."""
        result = sprint_capacity(members=5, sprint_days=10, focus_factor=0.7)
        assert result["effective_team_days"] == result["capacity_days"]


# ---------------------------------------------------------------------------
# TestWsjfScore
# ---------------------------------------------------------------------------

class TestWsjfScore:
    """Tests for wsjf_score()."""

    def test_normal_calculation(self):
        """WSJF = (BV + TC + RR) / JobSize."""
        score = wsjf_score(business_value=8, time_criticality=5, risk_reduction=3, job_size=4)
        assert score == pytest.approx(4.0, rel=1e-6)

    def test_zero_job_size_raises(self):
        """job_size == 0 raises ValueError."""
        with pytest.raises(ValueError, match="job_size cannot be zero"):
            wsjf_score(business_value=8, time_criticality=5, risk_reduction=3, job_size=0)

    def test_negative_job_size_raises(self):
        """Negative job_size raises ValueError."""
        with pytest.raises(ValueError, match="job_size cannot be zero"):
            wsjf_score(business_value=8, time_criticality=5, risk_reduction=3, job_size=-1)

    def test_higher_cod_higher_score(self):
        """Higher Cost of Delay (BV + TC + RR) yields higher WSJF score."""
        low_cod = wsjf_score(business_value=1, time_criticality=1, risk_reduction=1, job_size=5)
        high_cod = wsjf_score(business_value=8, time_criticality=8, risk_reduction=8, job_size=5)
        assert high_cod > low_cod

    def test_larger_job_size_reduces_score(self):
        """Larger job size reduces WSJF score for the same CoD."""
        small_job = wsjf_score(business_value=8, time_criticality=5, risk_reduction=3, job_size=2)
        large_job = wsjf_score(business_value=8, time_criticality=5, risk_reduction=3, job_size=8)
        assert small_job > large_job

    def test_returns_float(self):
        """Return type is float even for integer inputs."""
        score = wsjf_score(business_value=5, time_criticality=3, risk_reduction=2, job_size=5)
        assert isinstance(score, float)


# ---------------------------------------------------------------------------
# TestMttrAnalysis
# ---------------------------------------------------------------------------

class TestMttrAnalysis:
    """Tests for mttr_analysis()."""

    def test_normal_paired_dates(self):
        """Correctly computes mean days from paired open/close dates."""
        result = mttr_analysis(
            dates_open=["2026-01-01", "2026-01-10"],
            dates_closed=["2026-01-05", "2026-01-14"],
        )
        # Both resolved in 4 days
        assert result["mttr_days_mean"] == pytest.approx(4.0)
        assert result["closed_count"] == 2
        assert result["open_count"] == 0

    def test_empty_returns_zeros(self):
        """Empty open and closed lists return zero MTTR and zero counts."""
        result = mttr_analysis(dates_open=[], dates_closed=[])
        assert result["mttr_days_mean"] == 0.0
        assert result["mttr_days_p85"] == 0.0
        assert result["closed_count"] == 0
        assert result["open_count"] == 0

    def test_mismatched_lengths_raises(self):
        """More closed dates than open dates raises ValueError."""
        with pytest.raises(ValueError, match="cannot exceed"):
            mttr_analysis(
                dates_open=["2026-01-01"],
                dates_closed=["2026-01-05", "2026-01-10"],
            )

    def test_open_count_is_unresolved_items(self):
        """open_count equals number of opened items without matching close."""
        result = mttr_analysis(
            dates_open=["2026-01-01", "2026-01-10", "2026-01-15"],
            dates_closed=["2026-01-05"],
        )
        assert result["open_count"] == 2
        assert result["closed_count"] == 1

    def test_healthy_mttr_note(self):
        """MTTR < 3 days produces 'Healthy' resolution note."""
        result = mttr_analysis(
            dates_open=["2026-01-01"],
            dates_closed=["2026-01-03"],
        )
        assert "Healthy" in result["resolution_layer_note"]

    def test_at_risk_mttr_note(self):
        """MTTR 3-7 days produces 'At risk' resolution note."""
        result = mttr_analysis(
            dates_open=["2026-01-01"],
            dates_closed=["2026-01-06"],
        )
        assert "At risk" in result["resolution_layer_note"]

    def test_critical_mttr_note(self):
        """MTTR > 7 days produces 'Critical' resolution note."""
        result = mttr_analysis(
            dates_open=["2026-01-01"],
            dates_closed=["2026-01-12"],
        )
        assert "Critical" in result["resolution_layer_note"]

    def test_p85_zero_for_single_item(self):
        """Single item p85 is computable and non-negative."""
        result = mttr_analysis(
            dates_open=["2026-01-01"],
            dates_closed=["2026-01-04"],
        )
        assert result["mttr_days_p85"] >= 0.0


# ---------------------------------------------------------------------------
# TestRetrospectiveEffectiveness
# ---------------------------------------------------------------------------

class TestRetrospectiveEffectiveness:
    """Tests for retrospective_effectiveness()."""

    def test_normal_re_score(self):
        """RE score is items_closed / items_created."""
        result = retrospective_effectiveness(items_created=10, items_closed=8, total_sprints=4)
        assert result["re_score"] == pytest.approx(0.8, rel=1e-4)

    def test_zero_items_created_returns_zero_re(self):
        """RE score is 0.0 when items_created is 0."""
        result = retrospective_effectiveness(items_created=0, items_closed=0, total_sprints=3)
        assert result["re_score"] == 0.0

    def test_format_rotation_modulo_4(self):
        """Format rotates every 4 sprints based on total_sprints % 4."""
        r0 = retrospective_effectiveness(items_created=5, items_closed=4, total_sprints=4)
        r1 = retrospective_effectiveness(items_created=5, items_closed=4, total_sprints=5)
        r2 = retrospective_effectiveness(items_created=5, items_closed=4, total_sprints=6)
        r3 = retrospective_effectiveness(items_created=5, items_closed=4, total_sprints=7)
        assert r0["recommended_format"] == "4-Ls"
        assert r1["recommended_format"] == "Start-Stop-Continue"
        assert r2["recommended_format"] == "Mad-Sad-Glad"
        assert r3["recommended_format"] == "5-Whys"

    def test_total_sprints_less_than_one_raises(self):
        """total_sprints < 1 raises ValueError."""
        with pytest.raises(ValueError, match="total_sprints"):
            retrospective_effectiveness(items_created=5, items_closed=4, total_sprints=0)

    def test_nasscom_benchmark_l4_plus_high_re(self):
        """RE score > 0.85 maps to L4+ benchmark."""
        result = retrospective_effectiveness(items_created=10, items_closed=9, total_sprints=1)
        assert result["nasscom_benchmark"] == "L4+"

    def test_nasscom_benchmark_l3_plus_mid_re(self):
        """RE score 0.70-0.85 maps to L3+ benchmark."""
        result = retrospective_effectiveness(items_created=10, items_closed=8, total_sprints=1)
        assert result["nasscom_benchmark"] == "L3+"

    def test_nasscom_benchmark_below_l3_low_re(self):
        """RE score <= 0.70 maps to Below L3 benchmark."""
        result = retrospective_effectiveness(items_created=10, items_closed=5, total_sprints=1)
        assert result["nasscom_benchmark"] == "Below L3"

    def test_iv_trend_equals_closed_per_sprint(self):
        """iv_trend equals items_closed / total_sprints."""
        result = retrospective_effectiveness(items_created=10, items_closed=6, total_sprints=3)
        assert result["iv_trend"] == pytest.approx(2.0, rel=1e-4)


# ---------------------------------------------------------------------------
# TestTuckmanEstimate
# ---------------------------------------------------------------------------

class TestTuckmanEstimate:
    """Tests for tuckman_estimate() decision matrix."""

    def test_forming_high_cv_low_age(self):
        """cv > 0.35 AND age < 4 yields Forming stage."""
        stage = tuckman_estimate(velocity_cv=0.40, velocity_trend=0.0, team_age_sprints=2)
        assert stage == "Forming"

    def test_storming_high_cv_older_team(self):
        """cv > 0.25 with age >= 4 yields Storming (Forming rule does not apply)."""
        stage = tuckman_estimate(velocity_cv=0.30, velocity_trend=0.0, team_age_sprints=6)
        assert stage == "Storming"

    def test_norming_medium_cv_positive_trend(self):
        """cv <= 0.25 AND positive trend yields Norming stage."""
        stage = tuckman_estimate(velocity_cv=0.20, velocity_trend=2.0, team_age_sprints=8)
        assert stage == "Norming"

    def test_performing_low_cv(self):
        """cv < 0.15 AND trend == 0 yields Performing (rule 3 requires trend > 0, trend=0 skips to rule 4)."""
        # Rule 3: cv <= 0.25 AND trend > 0 -> Norming (skipped when trend == 0)
        # Rule 4: cv < 0.15 AND trend >= 0 -> Performing (matches when trend == 0)
        stage = tuckman_estimate(velocity_cv=0.10, velocity_trend=0.0, team_age_sprints=12)
        assert stage == "Performing"

    def test_returns_valid_stage_string(self):
        """Return value is always one of the four Tuckman stage strings."""
        valid_stages = {"Forming", "Storming", "Norming", "Performing"}
        for cv, trend, age in [
            (0.40, 0.0, 1), (0.30, 0.0, 6), (0.20, 2.0, 8), (0.10, 0.5, 12), (0.20, -1.0, 8)
        ]:
            stage = tuckman_estimate(velocity_cv=cv, velocity_trend=trend, team_age_sprints=age)
            assert stage in valid_stages

    def test_norming_fallback_negative_trend_medium_cv(self):
        """cv <= 0.25 AND negative trend AND cv >= 0.15 falls through to Norming default."""
        stage = tuckman_estimate(velocity_cv=0.20, velocity_trend=-1.0, team_age_sprints=8)
        assert stage == "Norming"


# ---------------------------------------------------------------------------
# TestIndiaHolidaysInSprint
# ---------------------------------------------------------------------------

class TestIndiaHolidaysInSprint:
    """Tests for india_holidays_in_sprint()."""

    def test_republic_day_in_jan_sprint(self):
        """Republic Day (2026-01-26) is counted in a January sprint."""
        count = india_holidays_in_sprint("2026-01-20", "2026-02-03")
        assert count >= 1

    def test_independence_day_counted(self):
        """Independence Day (2026-08-15) is counted when sprint spans it."""
        count = india_holidays_in_sprint("2026-08-10", "2026-08-20")
        assert count >= 1

    def test_no_holidays_in_period_without_holidays(self):
        """A sprint window with no known holidays returns 0."""
        # 2026-09-01 to 2026-09-14 has no known India holidays
        count = india_holidays_in_sprint("2026-09-01", "2026-09-14")
        assert count == 0

    def test_single_day_sprint_on_holiday(self):
        """Single-day sprint exactly on a holiday returns 1."""
        count = india_holidays_in_sprint("2026-01-26", "2026-01-26")
        assert count == 1

    def test_invalid_date_raises(self):
        """Invalid ISO date string raises ValueError."""
        with pytest.raises(ValueError):
            india_holidays_in_sprint("not-a-date", "2026-01-26")

    def test_start_after_end_raises(self):
        """start > end raises ValueError."""
        with pytest.raises(ValueError, match="must be <="):
            india_holidays_in_sprint("2026-02-01", "2026-01-20")

    def test_out_of_range_year_returns_zero(self):
        """Sprint window in 2027 (no data) returns 0."""
        count = india_holidays_in_sprint("2027-01-01", "2027-12-31")
        assert count == 0

    def test_full_year_2025_includes_known_holidays(self):
        """Full 2025 window includes all 2025 public holidays."""
        count = india_holidays_in_sprint("2025-01-01", "2025-12-31")
        assert count >= 12  # at least 12 gazetted holidays in 2025
