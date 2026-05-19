"""
scrum_calculator.py -- Pure statistical computation for Scrum Master tools.

No network I/O. No external dependencies. Python 3.8+ stdlib only.
Uses: random, statistics, math, datetime.

All functions are stateless and side-effect-free (pure functions).
Monte Carlo simulation uses random.seed(None) -- non-deterministic by design.

India Holiday Constant:
  INDIA_NATIONAL_HOLIDAYS_2025_2026: frozenset of ISO date strings (YYYY-MM-DD)
  Covers: Republic Day, Holi, Ram Navami, Good Friday, Eid al-Fitr (approx),
          Buddha Purnima, Eid ul-Adha (approx), Independence Day, Gandhi Jayanti,
          Dussehra, Diwali, Guru Nanak Jayanti, Christmas, and New Year's Day.
  UPDATE REQUIRED: Add 2027 dates before January 2027 sprint cycles.

Benchmark References:
  NASSCOM Industry Average Velocity: 35-45 story points per 2-week sprint
  NASSCOM AgileX Maturity Levels (by velocity CV):
    L1: CV > 0.35  (Highly variable)
    L2: CV 0.25-0.35 (Building rhythm)
    L3: CV 0.15-0.25 (Good predictability)
    L4: CV 0.05-0.15 (Strong predictability)
    L5: CV < 0.05  (Industry-leading)

Windows-Safe: ASCII only (cp1252 compatible)
"""

import math
import random
import statistics
from datetime import date
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# India National Holiday Calendar 2025-2026
# UPDATE REQUIRED: Add 2027 dates before January 2027 sprint planning cycles.
# Sources: Government of India gazette notifications. Islamic holidays
# (Eid al-Fitr, Eid ul-Adha) are moon-sighting dependent -- dates are approximate.
# ---------------------------------------------------------------------------
INDIA_NATIONAL_HOLIDAYS_2025_2026 = frozenset([
    # 2025 India National Holidays
    "2025-01-01",  # New Year's Day
    "2025-01-26",  # Republic Day
    "2025-03-14",  # Holi
    "2025-03-31",  # Eid al-Fitr (approximate)
    "2025-04-10",  # Ram Navami
    "2025-04-14",  # Dr. B.R. Ambedkar Jayanti
    "2025-04-18",  # Good Friday
    "2025-05-12",  # Buddha Purnima
    "2025-06-07",  # Eid ul-Adha (approximate)
    "2025-08-15",  # Independence Day
    "2025-10-02",  # Gandhi Jayanti
    "2025-10-20",  # Diwali (approximate; varies by region)
    "2025-11-05",  # Guru Nanak Jayanti (approximate)
    "2025-12-25",  # Christmas Day
    # 2026 India National Holidays
    "2026-01-01",  # New Year's Day
    "2026-01-26",  # Republic Day
    "2026-03-03",  # Holi (approximate)
    "2026-03-20",  # Eid al-Fitr (approximate)
    "2026-03-30",  # Ram Navami (approximate)
    "2026-04-03",  # Good Friday
    "2026-04-14",  # Dr. B.R. Ambedkar Jayanti
    "2026-05-27",  # Eid ul-Adha (approximate)
    "2026-05-31",  # Buddha Purnima (approximate)
    "2026-08-15",  # Independence Day
    "2026-10-02",  # Gandhi Jayanti
    "2026-10-08",  # Dussehra (approximate)
    "2026-11-09",  # Diwali (approximate)
    "2026-11-24",  # Guru Nanak Jayanti (approximate)
    "2026-12-25",  # Christmas Day
])


def _nasscom_agile_x_level(cv: float) -> str:
    """Map velocity coefficient of variation to NASSCOM AgileX maturity level.

    Args:
        cv: Coefficient of variation of velocity (non-negative float).

    Returns:
        NASSCOM AgileX level string: "L1", "L2", "L3", "L4", or "L5".
    """
    if cv > 0.35:
        return "L1"
    if cv > 0.25:
        return "L2"
    if cv > 0.15:
        return "L3"
    if cv > 0.05:
        return "L4"
    return "L5"


def _percentile(sorted_vals: List[float], p: float) -> float:
    """Compute a percentile from a pre-sorted list using index formula.

    Args:
        sorted_vals: Sorted list of numeric values (ascending).
        p: Percentile as a fraction in [0.0, 1.0].

    Returns:
        Percentile value as float.
    """
    idx = int(p * len(sorted_vals))
    idx = min(idx, len(sorted_vals) - 1)
    return float(sorted_vals[idx])


def velocity_stats(velocity_history: List[int]) -> Dict[str, Any]:
    """Compute descriptive velocity statistics from historical sprint velocities.

    Computes mean, population standard deviation, coefficient of variation,
    Velocity Stability Index, and NASSCOM AgileX maturity level. Handles
    edge cases: empty list returns error dict; single value returns stddev=0.0.

    Args:
        velocity_history: List of completed story points per sprint (integers),
                          ordered oldest-first. Minimum 1 value required for
                          basic stats; 2+ values for meaningful stddev.

    Returns:
        Dict with keys:
            mean (float): Arithmetic mean velocity.
            stddev (float): Population standard deviation (0.0 for single value).
            cv (float): Coefficient of variation (stddev / mean). 0.0 if mean is 0.
            vsi (float): Velocity Stability Index (1 - cv, clamped to [0, 1]).
            nasscom_agileX_level (str): AgileX level "L1" through "L5".
            nasscom_benchmark_note (str): Comparison to NASSCOM 35-45 SP/sprint range.
            sprints_sampled (int): Number of velocity data points used.

    Raises:
        ValueError: If velocity_history is None (empty list returns error dict).
    """
    if not velocity_history:
        return {"error": "velocity_history is empty"}

    mean_val = statistics.mean(velocity_history)

    if len(velocity_history) > 1:
        stddev_val = statistics.pstdev(velocity_history)
    else:
        stddev_val = 0.0

    if mean_val > 0:
        cv_val = stddev_val / mean_val
    else:
        cv_val = 0.0

    vsi_val = max(0.0, min(1.0, 1.0 - cv_val))
    agile_x_level = _nasscom_agile_x_level(cv_val)

    if mean_val < 35:
        benchmark_note = "Below NASSCOM benchmark (35-45 SP/2-week sprint)"
    elif mean_val <= 45:
        benchmark_note = "Within NASSCOM benchmark (35-45 SP/2-week sprint)"
    else:
        benchmark_note = "Above NASSCOM benchmark (35-45 SP/2-week sprint)"

    return {
        "mean": round(mean_val, 2),
        "stddev": round(stddev_val, 2),
        "cv": round(cv_val, 4),
        "vsi": round(vsi_val, 4),
        "nasscom_agileX_level": agile_x_level,
        "nasscom_benchmark_note": benchmark_note,
        "sprints_sampled": len(velocity_history),
    }


def monte_carlo_forecast(
    velocity_samples: List[int],
    remaining_points: int,
    iterations: int = 10000,
) -> Dict[str, Any]:
    """Run a Monte Carlo simulation to forecast sprint completion probability.

    Uses random.seed(None) -- non-deterministic by design (CONTRACT #3).
    Filters out zero/negative velocity samples before simulation. Samples
    velocities by random selection from the filtered input list.

    Algorithm: For each iteration, randomly sample velocities from
    velocity_samples until cumulative sum reaches remaining_points.
    Count the number of sprints needed. Repeat for 'iterations' runs.
    Return percentile distribution of sprint counts.

    Args:
        velocity_samples: Historical velocity data points (integers).
                          Zero/negative values are filtered out before simulation.
        remaining_points: Total story points remaining (must be >= 1).
        iterations: Number of simulation runs. Default 10_000 per CONTRACT #3.

    Returns:
        Dict with keys (per CONTRACT #3):
            p50 (float): 50th percentile sprints needed.
            p70 (float): 70th percentile sprints needed.
            p85 (float): 85th percentile sprints needed.
            p95 (float): 95th percentile sprints needed.
            mean_sprints (float): Arithmetic mean sprints across simulations.
            std_sprints (float): Standard deviation of sprints across simulations.
            samples_used (int): Number of positive velocity samples used as input.

    Raises:
        ValueError: If velocity_samples is empty after filtering or if all
                    velocity values are <= 0, or if remaining_points < 1.
    """
    if not velocity_samples:
        raise ValueError("velocity_samples must not be empty")

    positive_samples = [v for v in velocity_samples if v > 0]
    if not positive_samples:
        raise ValueError("All velocity samples are zero or negative; cannot forecast")

    if remaining_points < 1:
        raise ValueError("remaining_points must be >= 1")

    random.seed(None)
    results = []
    for _ in range(iterations):
        sprints = 0
        remaining = remaining_points
        while remaining > 0:
            v = random.choice(positive_samples)
            remaining -= v
            sprints += 1
        results.append(sprints)

    results.sort()
    n = len(results)

    mean_s = statistics.mean(results)
    if n > 1:
        std_s = statistics.pstdev(results)
    else:
        std_s = 0.0

    return {
        "p50": float(_percentile(results, 0.50)),
        "p70": float(_percentile(results, 0.70)),
        "p85": float(_percentile(results, 0.85)),
        "p95": float(_percentile(results, 0.95)),
        "mean_sprints": round(mean_s, 2),
        "std_sprints": round(std_s, 2),
        "samples_used": len(positive_samples),
    }


def sprint_capacity(
    members: int,
    sprint_days: int,
    focus_factor: float = 0.7,
    leave_days: int = 0,
    india_holidays: int = 0,
) -> Dict[str, Any]:
    """Calculate sprint capacity in story points.

    Formula:
        effective_days = (members * sprint_days) - leave_days - (members * india_holidays)
        capacity_points = max(0, effective_days) * focus_factor * 2

    The factor of 2 converts person-days to story points assuming 1 SP = 0.5 ideal day.
    Adjust focus_factor to reflect actual sprint overhead (meetings, reviews, etc.).

    Args:
        members: Number of team members contributing to the sprint (>= 1).
        sprint_days: Total working days in sprint excluding weekends (>= 1).
        focus_factor: Fraction of time spent on sprint work (0 < x <= 1.0).
                      Default 0.7 (70%).
        leave_days: Aggregated person-days of planned leave across all members.
        india_holidays: Number of India national holidays in sprint window.
                        Use india_holidays_in_sprint() to compute this value.

    Returns:
        Dict with keys:
            capacity_points (float): Recommended sprint story point commitment.
            capacity_days (float): Effective capacity in person-days.
            focus_factor_used (float): The focus_factor value applied.
            effective_team_days (float): Net person-days after leave and holidays.
            india_holidays_excluded (int): Count of India holidays deducted.
            ist_timezone_note (str): IST/EST overlap coordination note.

    Raises:
        ValueError: If members < 1, sprint_days < 1, or focus_factor not in (0, 1].
    """
    if members < 1:
        raise ValueError("members must be >= 1")
    if sprint_days < 1:
        raise ValueError("sprint_days must be >= 1")
    if focus_factor <= 0.0 or focus_factor > 1.0:
        raise ValueError("focus_factor must be in (0, 1]")

    total_person_days = members * sprint_days
    effective_days = total_person_days - leave_days - (members * india_holidays)
    effective_days = max(0.0, float(effective_days))

    capacity_points = effective_days * focus_factor * 2

    return {
        "capacity_points": round(capacity_points, 1),
        "capacity_days": round(effective_days, 1),
        "focus_factor_used": focus_factor,
        "effective_team_days": round(effective_days, 1),
        "india_holidays_excluded": india_holidays,
        "ist_timezone_note": (
            "IST timezone: 4.5h overlap window with EST (17:30-23:00 IST)"
        ),
    }


def wsjf_score(
    business_value: int,
    time_criticality: int,
    risk_reduction: int,
    job_size: int,
) -> float:
    """Calculate Weighted Shortest Job First (WSJF) prioritization score.

    WSJF = (business_value + time_criticality + risk_reduction) / job_size

    Higher scores indicate higher priority. All inputs should use the
    Fibonacci scale (1, 2, 3, 5, 8, 13, 20) for consistent comparison.

    Args:
        business_value: Business value score (typically 1-20 Fibonacci).
        time_criticality: Time criticality score (typically 1-20 Fibonacci).
        risk_reduction: Risk reduction / opportunity enablement score (1-20).
        job_size: Job size / duration estimate (typically 1-20 Fibonacci).
                  Must be > 0.

    Returns:
        WSJF score as float. Higher scores indicate higher priority.

    Raises:
        ValueError: If job_size is zero or negative.
    """
    if job_size <= 0:
        raise ValueError("job_size cannot be zero or negative")
    return (business_value + time_criticality + risk_reduction) / float(job_size)


def mttr_analysis(
    dates_open: List[str],
    dates_closed: List[str],
) -> Dict[str, Any]:
    """Compute Mean Time To Resolve (MTTR) metrics for impediments or bugs.

    Pairs each close date with the corresponding open date to compute
    resolution time in days. Partial datasets are supported: pass fewer
    close dates than open dates to represent unresolved items.

    Args:
        dates_open: List of ISO date strings ("YYYY-MM-DD") when issues were opened.
        dates_closed: List of ISO date strings for corresponding close dates.
                      Must have same length as or shorter length than dates_open.
                      Pass empty list to compute only open_count.

    Returns:
        Dict with keys:
            mttr_days_mean (float): Mean days to resolve (0.0 if no closed items).
            mttr_days_p85 (float): 85th percentile days to resolve.
            open_count (int): Count of items not yet resolved.
            closed_count (int): Number of resolved items analyzed.
            resolution_layer_note (str): SLA health note based on mean MTTR.

    Raises:
        ValueError: If dates_closed length exceeds dates_open length.
    """
    if len(dates_closed) > len(dates_open):
        raise ValueError(
            "dates_closed length cannot exceed dates_open length"
        )

    resolution_days = []
    for i, closed_str in enumerate(dates_closed):
        open_d = date.fromisoformat(dates_open[i])
        closed_d = date.fromisoformat(closed_str)
        delta = (closed_d - open_d).days
        resolution_days.append(float(max(0, delta)))

    open_count = len(dates_open) - len(dates_closed)
    closed_count = len(resolution_days)

    if not resolution_days:
        mean_days = 0.0
        p85_days = 0.0
    else:
        mean_days = statistics.mean(resolution_days)
        sorted_days = sorted(resolution_days)
        p85_days = _percentile(sorted_days, 0.85)

    if mean_days < 3:
        resolution_note = "Healthy: MTTR < 3 days"
    elif mean_days <= 7:
        resolution_note = "At risk: MTTR 3-7 days"
    else:
        resolution_note = "Critical: MTTR > 7 days"

    return {
        "mttr_days_mean": round(mean_days, 2),
        "mttr_days_p85": round(p85_days, 2),
        "open_count": open_count,
        "closed_count": closed_count,
        "resolution_layer_note": resolution_note,
    }


def retrospective_effectiveness(
    items_created: int,
    items_closed: int,
    total_sprints: int,
) -> Dict[str, Any]:
    """Compute a Retrospective Effectiveness (RE) score.

    RE Score = items_closed / items_created if items_created > 0, else 0.0
    Implementation Velocity (IV) = items_closed / total_sprints

    Format rotation cycles every 4 sprints, keyed by (total_sprints % 4):
      0 -> "4-Ls", 1 -> "Start-Stop-Continue", 2 -> "Mad-Sad-Glad", 3 -> "5-Whys"

    Args:
        items_created: Total retrospective action items created over measurement period.
        items_closed: Total retrospective action items resolved/closed.
        total_sprints: Number of sprints in the measurement period (minimum 1).

    Returns:
        Dict with keys:
            re_score (float): Fraction of action items closed (0.0 to 1.0).
            iv_trend (float): Average action items closed per sprint.
            nasscom_benchmark (str): NASSCOM RE benchmark comparison string.
            recommended_format (str): Suggested retro format for next sprint.

    Raises:
        ValueError: If total_sprints < 1.
    """
    if total_sprints < 1:
        raise ValueError("total_sprints must be >= 1")

    re_score = items_closed / items_created if items_created > 0 else 0.0
    iv_trend = items_closed / total_sprints if total_sprints > 0 else 0.0

    format_rotation = {
        0: "4-Ls",
        1: "Start-Stop-Continue",
        2: "Mad-Sad-Glad",
        3: "5-Whys",
    }
    recommended_format = format_rotation[total_sprints % 4]

    if re_score > 0.85:
        nasscom_benchmark = "L4+"
    elif re_score > 0.70:
        nasscom_benchmark = "L3+"
    else:
        nasscom_benchmark = "Below L3"

    return {
        "re_score": round(re_score, 4),
        "iv_trend": round(iv_trend, 4),
        "nasscom_benchmark": nasscom_benchmark,
        "recommended_format": recommended_format,
    }


def tuckman_estimate(
    velocity_cv: float,
    velocity_trend: float,
    team_age_sprints: int,
) -> str:
    """Estimate team maturity stage using a Tuckman model heuristic.

    Decision matrix (evaluated top-to-bottom, first match wins):
      cv > 0.35 AND team_age_sprints < 4  -> "Forming"
      cv > 0.25                            -> "Storming"
      cv <= 0.25 AND velocity_trend > 0   -> "Norming"
      cv < 0.15 AND velocity_trend >= 0   -> "Performing"
      else                                 -> "Norming"

    Args:
        velocity_cv: Coefficient of variation of velocity (from velocity_stats()).
                     Non-negative float.
        velocity_trend: Numeric trend value; positive = improving, negative = declining.
        team_age_sprints: Number of completed sprints for this team (>= 0).

    Returns:
        One of: "Forming", "Storming", "Norming", "Performing".
    """
    if velocity_cv > 0.35 and team_age_sprints < 4:
        return "Forming"
    if velocity_cv > 0.25:
        return "Storming"
    if velocity_cv <= 0.25 and velocity_trend > 0:
        return "Norming"
    if velocity_cv < 0.15 and velocity_trend >= 0:
        return "Performing"
    return "Norming"


def india_holidays_in_sprint(
    sprint_start_iso: str,
    sprint_end_iso: str,
) -> int:
    """Count India national holidays falling within the sprint date range (inclusive).

    Uses INDIA_NATIONAL_HOLIDAYS_2025_2026 constant. Dates outside the
    2025-2026 range return 0 with no error (holidays for other years are unknown).

    Args:
        sprint_start_iso: Sprint start date as "YYYY-MM-DD" string.
        sprint_end_iso: Sprint end date as "YYYY-MM-DD" string (inclusive).

    Returns:
        Integer count of India national holidays within [sprint_start, sprint_end].

    Raises:
        ValueError: If date strings are not valid ISO format or start > end.
    """
    start_d = date.fromisoformat(sprint_start_iso)
    end_d = date.fromisoformat(sprint_end_iso)

    if start_d > end_d:
        raise ValueError(
            "sprint_start_iso must be <= sprint_end_iso"
        )

    count = 0
    for holiday_str in INDIA_NATIONAL_HOLIDAYS_2025_2026:
        h_date = date.fromisoformat(holiday_str)
        if start_d <= h_date <= end_d:
            count += 1
    return count
