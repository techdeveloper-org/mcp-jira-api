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


# ---------------------------------------------------------------------------
# India Holiday Name Lookup (supplement to INDIA_NATIONAL_HOLIDAYS_2025_2026)
# Used by multi_sprint_holiday_forecast to return human-readable holiday names.
# ---------------------------------------------------------------------------
_INDIA_HOLIDAY_NAMES = {
    "2025-01-01": "New Year's Day",
    "2025-01-26": "Republic Day",
    "2025-03-14": "Holi",
    "2025-03-31": "Eid al-Fitr",
    "2025-04-10": "Ram Navami",
    "2025-04-14": "Dr. B.R. Ambedkar Jayanti",
    "2025-04-18": "Good Friday",
    "2025-05-12": "Buddha Purnima",
    "2025-06-07": "Eid ul-Adha",
    "2025-08-15": "Independence Day",
    "2025-10-02": "Gandhi Jayanti",
    "2025-10-20": "Diwali",
    "2025-11-05": "Guru Nanak Jayanti",
    "2025-12-25": "Christmas Day",
    "2026-01-01": "New Year's Day",
    "2026-01-26": "Republic Day",
    "2026-03-03": "Holi",
    "2026-03-20": "Eid al-Fitr",
    "2026-03-30": "Ram Navami",
    "2026-04-03": "Good Friday",
    "2026-04-14": "Dr. B.R. Ambedkar Jayanti",
    "2026-05-27": "Eid ul-Adha",
    "2026-05-31": "Buddha Purnima",
    "2026-08-15": "Independence Day",
    "2026-10-02": "Gandhi Jayanti",
    "2026-10-08": "Dussehra",
    "2026-11-09": "Diwali",
    "2026-11-24": "Guru Nanak Jayanti",
    "2026-12-25": "Christmas Day",
}


# ---------------------------------------------------------------------------
# Normal distribution helper (NormalDist requires Python 3.8 statistics module)
# ---------------------------------------------------------------------------

def _normal_cdf(x):
    # type: (float) -> float
    """Compute the CDF of the standard normal distribution at x.

    Uses the complementary error function (erfc) from the math module.
    CDF(x) = 0.5 * erfc(-x / sqrt(2))

    Args:
        x: The point at which to evaluate the standard normal CDF.

    Returns:
        Probability P(Z <= x) as a float in [0.0, 1.0].
    """
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def _normal_inv_cdf(p):
    # type: (float) -> float
    """Compute the inverse CDF (quantile function) of the standard normal distribution.

    Uses a rational approximation (Beasley-Springer-Moro algorithm) for
    p in (0, 1). Clamps extreme inputs to avoid infinite results.

    Args:
        p: Probability in (0.0, 1.0). Values at or outside this range are
           clamped to (1e-15, 1 - 1e-15).

    Returns:
        z such that P(Z <= z) = p for Z ~ N(0, 1).
    """
    p = max(1e-15, min(1.0 - 1e-15, p))
    if p < 0.5:
        t = math.sqrt(-2.0 * math.log(p))
    else:
        t = math.sqrt(-2.0 * math.log(1.0 - p))

    c0 = 2.515517
    c1 = 0.802853
    c2 = 0.010328
    d1 = 1.432788
    d2 = 0.189269
    d3 = 0.001308

    numerator = c0 + c1 * t + c2 * t * t
    denominator = 1.0 + d1 * t + d2 * t * t + d3 * t * t * t
    z = t - numerator / denominator

    if p < 0.5:
        z = -z
    return z


# ---------------------------------------------------------------------------
# Function 1: bootstrap_bca_ci
# ---------------------------------------------------------------------------

def bootstrap_bca_ci(
    data,
    confidence=0.95,
    B=1000,
):
    # type: (List[float], float, int) -> Dict[str, Any]
    """Compute a BCa (bias-corrected and accelerated) bootstrap confidence interval.

    Algorithm:
      theta_hat = mean(data)
      Boot B resamples: theta_star[b] = mean(random.choices(data, k=n))
      Bias correction: z0 = Phi_inv(count(theta_star < theta_hat) / B)
      Jackknife: theta_loo[i] = mean(data without element i)
      Acceleration: a = sum((m - theta_loo[i])^3) / (6 * sum((m - theta_loo[i])^2)^1.5)
        where m = mean(theta_loo)
      Adjusted quantiles:
        z_lo = Phi_inv((1-confidence)/2); z_hi = Phi_inv((1+confidence)/2)
        alpha1 = Phi(z0 + (z0 + z_lo) / (1 - a*(z0 + z_lo)))
        alpha2 = Phi(z0 + (z0 + z_hi) / (1 - a*(z0 + z_hi)))
      lower = percentile of sorted theta_star at alpha1; upper at alpha2

    Args:
        data: List of numeric values (at least 2 required). Used as-is.
        confidence: Confidence level as a fraction in (0, 1). Default 0.95.
        B: Number of bootstrap resamples. Default 1000.

    Returns:
        Dict with keys:
            lower (float): BCa lower bound.
            upper (float): BCa upper bound.
            point_estimate (float): Observed mean of data.
            confidence (float): The confidence level used.
            B (int): Number of bootstrap resamples.
        On error: {"error": str}.
        Zero-variance case: lower=upper=point_estimate, B=0, note key added.
    """
    if len(data) < 2:
        return {"error": "Insufficient data for BCa bootstrap: need at least 2 values"}

    n = len(data)
    theta_hat = statistics.mean(data)

    data_vals = list(data)
    all_same = (max(data_vals) == min(data_vals))
    if all_same:
        val = float(theta_hat)
        return {
            "lower": val,
            "upper": val,
            "point_estimate": val,
            "confidence": confidence,
            "B": 0,
            "note": "Zero variance data: point estimate only",
        }

    random.seed(None)
    boot_stats = []
    for _ in range(B):
        resample = random.choices(data_vals, k=n)
        boot_stats.append(statistics.mean(resample))

    count_less = sum(1 for v in boot_stats if v < theta_hat)
    prop = count_less / float(B)
    prop = max(1e-15, min(1.0 - 1e-15, prop))
    z0_val = _normal_inv_cdf(prop)

    theta_loo = []
    for i in range(n):
        loo = data_vals[:i] + data_vals[i + 1:]
        theta_loo.append(statistics.mean(loo))

    theta_loo_mean = statistics.mean(theta_loo)
    diffs = [theta_loo_mean - v for v in theta_loo]
    diffs_cubed = sum(d ** 3 for d in diffs)
    diffs_sq_sum = sum(d ** 2 for d in diffs)
    if diffs_sq_sum == 0.0:
        a_val = 0.0
    else:
        a_val = diffs_cubed / (6.0 * (diffs_sq_sum ** 1.5))

    z_lo = _normal_inv_cdf((1.0 - confidence) / 2.0)
    z_hi = _normal_inv_cdf((1.0 + confidence) / 2.0)

    denom_lo = 1.0 - a_val * (z0_val + z_lo)
    denom_hi = 1.0 - a_val * (z0_val + z_hi)
    if denom_lo == 0.0:
        denom_lo = 1e-15
    if denom_hi == 0.0:
        denom_hi = 1e-15

    alpha1 = _normal_cdf(z0_val + (z0_val + z_lo) / denom_lo)
    alpha2 = _normal_cdf(z0_val + (z0_val + z_hi) / denom_hi)

    alpha1 = max(0.0, min(1.0, alpha1))
    alpha2 = max(0.0, min(1.0, alpha2))

    boot_sorted = sorted(boot_stats)
    lower = float(_percentile(boot_sorted, alpha1))
    upper = float(_percentile(boot_sorted, alpha2))

    return {
        "lower": round(lower, 4),
        "upper": round(upper, 4),
        "point_estimate": round(float(theta_hat), 4),
        "confidence": confidence,
        "B": B,
    }


# ---------------------------------------------------------------------------
# Function 2: ahp_score
# ---------------------------------------------------------------------------

def ahp_score(criteria_matrix):
    # type: (List[List[float]]) -> Dict[str, Any]
    """Compute AHP (Analytic Hierarchy Process) pairwise comparison weights and consistency.

    Algorithm:
      1. Validate square matrix; handle n==1 trivially.
      2. Normalize columns: norm[i][j] = criteria_matrix[i][j] / col_sum[j].
      3. Weights: w[i] = mean(norm[i][j] for j in range(n)).
      4. Power iteration (up to 100 iters, tolerance 1e-6) for convergence.
      5. lambda_max = (1/n) * sum(sum(criteria_matrix[i][j]*w[j]) / w[i] for i).
      6. CI = (lambda_max - n) / (n - 1); RI from Saaty table; CR = CI / RI.
      7. consistent = CR < 0.10.

    RI table (Saaty, 1980):
      index 0..10 => [0, 0, 0, 0.58, 0.90, 1.12, 1.24, 1.32, 1.41, 1.45, 1.49]

    Args:
        criteria_matrix: Square n x n list-of-lists of positive floats representing
                         pairwise preference ratios. Row i, column j = preference of
                         criterion i over criterion j.

    Returns:
        Dict with keys:
            weights (List[float]): Normalized priority weights summing to 1.0.
            lambda_max (float): Largest eigenvalue approximation.
            CI (float): Consistency Index.
            CR (float): Consistency Ratio.
            consistent (bool): True if CR < 0.10.
            n (int): Matrix dimension.
        On error: {"error": str}.
    """
    if not criteria_matrix:
        return {"error": "AHP matrix must be square"}

    n = len(criteria_matrix)
    for row in criteria_matrix:
        if len(row) != n:
            return {"error": "AHP matrix must be square"}

    if n == 1:
        return {
            "weights": [1.0],
            "lambda_max": 1.0,
            "CI": 0.0,
            "CR": 0.0,
            "consistent": True,
            "n": 1,
        }

    col_sums = []
    for j in range(n):
        col_sums.append(sum(criteria_matrix[i][j] for i in range(n)))

    norm = []
    for i in range(n):
        row_norm = []
        for j in range(n):
            cs = col_sums[j] if col_sums[j] != 0.0 else 1e-15
            row_norm.append(criteria_matrix[i][j] / cs)
        norm.append(row_norm)

    weights = []
    for i in range(n):
        weights.append(sum(norm[i][j] for j in range(n)) / float(n))

    for _ in range(100):
        w_new = []
        for i in range(n):
            row_val = sum(criteria_matrix[i][j] * weights[j] for j in range(n))
            w_new.append(row_val)
        total = sum(w_new)
        if total == 0.0:
            total = 1e-15
        w_new = [x / total for x in w_new]
        max_diff = max(abs(w_new[i] - weights[i]) for i in range(n))
        weights = w_new
        if max_diff < 1e-6:
            break

    lambda_max_sum = 0.0
    for i in range(n):
        weighted_sum_i = sum(criteria_matrix[i][j] * weights[j] for j in range(n))
        w_i = weights[i] if weights[i] != 0.0 else 1e-15
        lambda_max_sum += weighted_sum_i / w_i
    lambda_max = lambda_max_sum / float(n)

    ci_val = (lambda_max - n) / float(n - 1)

    ri_table = [0.0, 0.0, 0.0, 0.58, 0.90, 1.12, 1.24, 1.32, 1.41, 1.45, 1.49]
    if n >= 3 and n < len(ri_table):
        ri = ri_table[n]
    elif n >= len(ri_table):
        ri = 1.49
    else:
        ri = 0.0

    cr_val = ci_val / ri if ri > 0.0 else 0.0
    consistent = cr_val < 0.10

    return {
        "weights": [round(w, 6) for w in weights],
        "lambda_max": round(lambda_max, 6),
        "CI": round(ci_val, 6),
        "CR": round(cr_val, 6),
        "consistent": consistent,
        "n": n,
    }


# ---------------------------------------------------------------------------
# Function 3: tuckman_markov
# ---------------------------------------------------------------------------

def tuckman_markov(velocity_history):
    # type: (List[float]) -> Dict[str, Any]
    """Classify team Tuckman stage from velocity history using CV and trend heuristics.

    Algorithm:
      mean_v = mean(velocity_history)
      std_v = stdev(velocity_history) for len >= 2, else 0
      cv = std_v / mean_v if mean_v > 0 else 1.0
      slope = linear regression slope using enumerate
      Stage rules (first match):
        len < 3 or cv > 0.5 -> "Forming"
        0.25 < cv <= 0.5    -> "Storming"
        0.10 < cv <= 0.25 and slope >= 0 -> "Norming"
        cv <= 0.10 and slope >= 0         -> "Performing"
        else -> "Norming"
      Stage probabilities: derived from CV distance to stage boundaries.
      nasscom_level: Forming->L1, Storming->L2, Norming->L3, Performing->L4 or L5.

    Note: This is a heuristic classifier based on velocity CV and trend.
    It is NOT derived from a true Markov transition matrix.

    Args:
        velocity_history: List of sprint velocities (floats), ordered oldest-first.
                          Minimum 2 data points required.

    Returns:
        Dict with keys:
            current_stage (str): Tuckman stage name.
            stage_probabilities (Dict[str, float]): Soft probabilities for all 4 stages.
            cv (float): Coefficient of variation of velocity.
            velocity_trend_slope (float): Linear regression slope of velocity over time.
            nasscom_agile_x_level (str): NASSCOM AgileX maturity level.
            empirical_caveat (str): Explanation that this is a heuristic, not a true Markov model.
        On error: {"error": str}.
    """
    if len(velocity_history) < 2:
        return {"error": "Need at least 2 velocity data points"}

    mean_v = statistics.mean(velocity_history)
    if len(velocity_history) >= 2:
        std_v = statistics.stdev(velocity_history)
    else:
        std_v = 0.0

    cv = std_v / mean_v if mean_v > 0.0 else 1.0

    n = len(velocity_history)
    indices = list(range(n))
    sum_i = sum(indices)
    sum_v = sum(velocity_history)
    sum_iv = sum(i * v for i, v in enumerate(velocity_history))
    sum_i2 = sum(i * i for i in indices)
    denom = n * sum_i2 - sum_i * sum_i
    if denom == 0.0:
        slope = 0.0
    else:
        slope = (n * sum_iv - sum_i * sum_v) / float(denom)

    if n < 3 or cv > 0.5:
        stage = "Forming"
    elif cv > 0.25:
        stage = "Storming"
    elif cv > 0.10 and slope >= 0.0:
        stage = "Norming"
    elif cv <= 0.10 and slope >= 0.0:
        stage = "Performing"
    else:
        stage = "Norming"

    forming_p = max(0.0, min(1.0, cv / 0.5)) if cv <= 0.5 else 1.0
    storming_p = max(0.0, min(1.0, (cv - 0.10) / 0.40)) if 0.10 <= cv <= 0.50 else 0.0
    norming_p = max(0.0, min(1.0, (0.25 - cv) / 0.15)) if cv <= 0.25 else 0.0
    performing_p = max(0.0, min(1.0, (0.10 - cv) / 0.10)) if cv <= 0.10 else 0.0

    total_p = forming_p + storming_p + norming_p + performing_p
    if total_p == 0.0:
        total_p = 1.0
    stage_probabilities = {
        "Forming": round(forming_p / total_p, 4),
        "Storming": round(storming_p / total_p, 4),
        "Norming": round(norming_p / total_p, 4),
        "Performing": round(performing_p / total_p, 4),
    }

    if stage == "Performing":
        nasscom_level = "L4" if cv > 0.05 else "L5"
    elif stage == "Norming":
        nasscom_level = "L3"
    elif stage == "Storming":
        nasscom_level = "L2"
    else:
        nasscom_level = "L1"

    return {
        "current_stage": stage,
        "stage_probabilities": stage_probabilities,
        "cv": round(cv, 4),
        "velocity_trend_slope": round(slope, 4),
        "nasscom_agile_x_level": nasscom_level,
        "empirical_caveat": (
            "Tuckman stage classification based on velocity CV and trend heuristics; "
            "not derived from a true Markov transition matrix"
        ),
    }


# ---------------------------------------------------------------------------
# Function 4: spotify_health_check
# ---------------------------------------------------------------------------

_SPOTIFY_DIMENSIONS = [
    "easy_to_release",
    "suitable_process",
    "tech_quality",
    "value",
    "speed",
    "mission",
    "fun",
    "learning",
    "support",
    "pawns_or_players",
    "team_spirit",
]


def spotify_health_check(dimension_scores, prev_scores=None):
    # type: (Dict[str, List[int]], Optional[Dict[str, Any]]) -> Dict[str, Any]
    """Compute Spotify Squad Health Check Team Health Score (THS).

    Validates that all 11 required dimensions are present, computes per-dimension
    means, overall THS (uniform weights), health color, and optionally a
    Wilcoxon signed-rank Z statistic comparing current to previous period.

    Wilcoxon signed-rank (paired, n=11):
      d[i] = dim_mean[i] - prev_mean[i]
      Rank |d[i]| (non-zero only); W = sum(sign(d[i]) * rank(|d[i]|))
      Z = W / sqrt(n*(n+1)*(2*n+1)/6) where n = count of non-zero d[i]

    Args:
        dimension_scores: Dict mapping each of the 11 dimension names to a
                          list of integer scores (0=unhealthy, 1=neutral, 2=healthy).
        prev_scores: Optional dict mapping dimension names to previous mean scores
                     (floats) for quarter-on-quarter delta computation.

    Returns:
        Dict with keys:
            THS (float): Mean across all 11 dimension means (range 0.0-2.0).
            dimension_scores (Dict[str, float]): Per-dimension mean scores.
            health_color (str): "Green" (THS>=1.5), "Amber" (>=0.75), "Red" (<0.75).
            wilcoxon_Z (float or None): Z statistic if prev_scores provided.
            delta_vs_previous (float or None): THS - previous THS if prev_scores provided.
        On error: {"error": str}.
    """
    missing = [d for d in _SPOTIFY_DIMENSIONS if d not in dimension_scores]
    if missing:
        return {"error": "Missing Spotify health dimensions: " + ", ".join(missing)}

    dim_means = {}
    for d in _SPOTIFY_DIMENSIONS:
        scores_list = dimension_scores[d]
        if not scores_list:
            dim_means[d] = 0.0
        else:
            dim_means[d] = statistics.mean(scores_list)

    ths = sum(dim_means[d] for d in _SPOTIFY_DIMENSIONS) / 11.0

    if ths >= 1.5:
        health_color = "Green"
    elif ths >= 0.75:
        health_color = "Amber"
    else:
        health_color = "Red"

    wilcoxon_z = None
    delta = None
    if prev_scores is not None:
        diffs = []
        for d in _SPOTIFY_DIMENSIONS:
            prev_val = float(prev_scores.get(d, 0.0))
            diffs.append(dim_means[d] - prev_val)

        nonzero_diffs = [(i, v) for i, v in enumerate(diffs) if v != 0.0]
        n_nz = len(nonzero_diffs)
        if n_nz > 0:
            abs_diffs = sorted(
                range(n_nz),
                key=lambda k: abs(nonzero_diffs[k][1])
            )
            ranks = [0.0] * n_nz
            for rank_pos, orig_idx in enumerate(abs_diffs):
                ranks[orig_idx] = float(rank_pos + 1)

            w_stat = 0.0
            for k in range(n_nz):
                sign_val = 1.0 if nonzero_diffs[k][1] > 0.0 else -1.0
                w_stat += sign_val * ranks[k]

            variance_w = n_nz * (n_nz + 1) * (2 * n_nz + 1) / 6.0
            wilcoxon_z = round(w_stat / math.sqrt(variance_w), 4) if variance_w > 0.0 else 0.0

        prev_dim_means_all = [float(prev_scores.get(d, 0.0)) for d in _SPOTIFY_DIMENSIONS]
        prev_ths = sum(prev_dim_means_all) / 11.0
        delta = round(ths - prev_ths, 4)

    return {
        "THS": round(ths, 4),
        "dimension_scores": {d: round(dim_means[d], 4) for d in _SPOTIFY_DIMENSIONS},
        "health_color": health_color,
        "wilcoxon_Z": round(wilcoxon_z, 4) if wilcoxon_z is not None else None,
        "delta_vs_previous": delta,
    }


# ---------------------------------------------------------------------------
# Function 5: edmondson_ps_scale
# ---------------------------------------------------------------------------

def edmondson_ps_scale(item_scores):
    # type: (List[int]) -> Dict[str, Any]
    """Compute Edmondson Psychological Safety Scale score from 7 Likert items.

    Applies reverse coding to items at positions 0, 2, 4 (0-indexed):
      reversed_score = 8 - score
    Computes PS_score = mean of all 7 processed scores (range 1.0-7.0).

    Cronbach alpha note: With a single list of 7 items (single respondent), the
    inter-item variance is undefined. The approximation below treats the 7
    processed scores as a set and computes alpha using total and inter-item
    variance. The result is informational only for single-respondent input.

    Args:
        item_scores: List of exactly 7 integers, each in [1, 7].

    Returns:
        Dict with keys:
            PS_score (float): Mean psychological safety score (1.0-7.0).
            cronbach_alpha (float): Estimated Cronbach alpha (0.0 for single respondent).
            interpretation (str): "Low" (<3.5), "Moderate" (3.5-5.5), "High" (>5.5).
            reverse_coded_positions (List[int]): [0, 2, 4].
        On error: {"error": str}.
    """
    if len(item_scores) != 7:
        return {"error": "item_scores must contain exactly 7 values"}

    for s in item_scores:
        if not (1 <= s <= 7):
            return {"error": "All item scores must be integers in range [1, 7]"}

    processed = []
    for i, s in enumerate(item_scores):
        if i in (0, 2, 4):
            processed.append(8 - s)
        else:
            processed.append(s)

    ps_score = statistics.mean(processed)

    k = 7
    # Single-respondent input: Cronbach alpha requires multiple respondents per item.
    # With one flat list of k scores, inter-item variance is undefined; return 0.0.
    alpha = 0.0

    if ps_score < 3.5:
        interpretation = "Low"
    elif ps_score <= 5.5:
        interpretation = "Moderate"
    else:
        interpretation = "High"

    return {
        "PS_score": round(ps_score, 4),
        "cronbach_alpha": round(alpha, 4),
        "interpretation": interpretation,
        "reverse_coded_positions": [0, 2, 4],
    }


# ---------------------------------------------------------------------------
# Function 6: scrum_of_scrums_overhead
# ---------------------------------------------------------------------------

def scrum_of_scrums_overhead(teams, p, c):
    # type: (int, float, float) -> Dict[str, Any]
    """Compute Scrum of Scrums Brook's Law coordination overhead.

    Formula (Brook's Law adaptation):
      T_n = teams * p - c * teams * (teams - 1) / 2
      n_optimal = p / c + 0.5  (rounded team count for max throughput)
      overhead_ratio = (c * teams * (teams-1) / 2) / (teams * p)

    Args:
        teams: Number of scrum teams (>= 2).
        p: Baseline productivity per team (must be > 0).
        c: Coordination cost per team pair (must be > 0 and < p).

    Returns:
        Dict with keys:
            T_n (float): Net team throughput after coordination overhead.
            n_optimal (float): Optimal number of teams for max throughput.
            overhead_ratio (float): Fraction of capacity consumed by coordination.
            teams (int): Input team count.
            productivity_per_team (float): Input p value.
            coordination_cost (float): Input c value.
        On error: {"error": str}.
    """
    if teams < 2:
        return {"error": "teams must be >= 2"}
    if p <= 0.0:
        return {"error": "productivity_per_team (p) must be > 0"}
    if c <= 0.0:
        return {"error": "coordination_cost (c) must be > 0"}
    if c >= p:
        return {"error": "coordination_cost (c) must be < productivity_per_team (p)"}

    t_n = teams * p - c * teams * (teams - 1) / 2.0
    n_optimal = p / c + 0.5
    total_capacity = teams * p
    overhead = c * teams * (teams - 1) / 2.0
    overhead_ratio = overhead / total_capacity if total_capacity > 0.0 else 0.0

    return {
        "T_n": round(t_n, 4),
        "n_optimal": round(n_optimal, 4),
        "overhead_ratio": round(overhead_ratio, 4),
        "teams": teams,
        "productivity_per_team": float(p),
        "coordination_cost": float(c),
    }


# ---------------------------------------------------------------------------
# Function 7: cognitive_load_index
# ---------------------------------------------------------------------------

def cognitive_load_index(complexity, responsibility, cl_max=10.0):
    # type: (Dict[str, float], Dict[str, float], float) -> Dict[str, Any]
    """Compute Team Topology Cognitive Load Index (CLI).

    Formula:
      common_domains = intersection of complexity.keys() and responsibility.keys()
      CL_team = sum(complexity[d] * responsibility[d] for d in common_domains)
      CLI = CL_team / cl_max
      overloaded = CLI > 1.0
      domain_contributions = {d: complexity[d]*responsibility[d] for d in common_domains}

    Args:
        complexity: Dict mapping domain name to complexity weight (float >= 0).
        responsibility: Dict mapping domain name to responsibility fraction (float >= 0).
        cl_max: Maximum cognitive load threshold (default 10.0, must be > 0).

    Returns:
        Dict with keys:
            CL_team (float): Raw cognitive load sum.
            CLI (float): Normalized cognitive load index (CL_team / cl_max).
            overloaded (bool): True if CLI > 1.0.
            domain_contributions (Dict[str, float]): Per-domain load product.
            cl_max (float): The threshold used.
            topology_efficiency (Dict[str, float]): Reference efficiency factors by
                team topology mode (X_as_Service: 0.90, Facilitating: 0.75,
                Collaboration: 0.70).
    """
    common_domains = set(complexity.keys()) & set(responsibility.keys())
    cl_team = sum(complexity[d] * responsibility[d] for d in common_domains)
    cli = cl_team / cl_max if cl_max > 0.0 else 0.0
    overloaded = cli > 1.0
    domain_contributions = {
        d: round(complexity[d] * responsibility[d], 4) for d in common_domains
    }

    return {
        "CL_team": round(cl_team, 4),
        "CLI": round(cli, 4),
        "overloaded": overloaded,
        "domain_contributions": domain_contributions,
        "cl_max": float(cl_max),
        "topology_efficiency": {
            "X_as_Service": 0.90,
            "Facilitating": 0.75,
            "Collaboration": 0.70,
        },
    }


# ---------------------------------------------------------------------------
# Function 8: attrition_ramp
# ---------------------------------------------------------------------------

def attrition_ramp(months, p_max, tau=6.0):
    # type: (float, float, float) -> Dict[str, Any]
    """Model cumulative attrition probability over time using exponential saturation.

    Formula:
      P_t = p_max * (1 - exp(-months / tau))
      effective_velocity_factor = 1.0 - P_t

    tau context (NASSCOM HR 2024):
      tau=6 for experienced hires; tau=12 for fresh graduates.

    Args:
        months: Time elapsed in months (must be > 0).
        p_max: Maximum asymptotic attrition probability (must be in (0, 1]).
        tau: Exponential decay time constant in months (default 6.0, must be > 0).

    Returns:
        Dict with keys:
            attrition_probability (float): Cumulative attrition probability at t=months.
            months (float): Input time elapsed.
            tau_months (float): Time constant used.
            p_max (float): Maximum attrition fraction.
            effective_velocity_factor (float): 1 - attrition_probability.
            india_context (str): NASSCOM HR context note.
        On error: {"error": str}.
    """
    if months <= 0.0:
        return {"error": "months must be > 0"}
    if p_max <= 0.0 or p_max > 1.0:
        return {"error": "p_max must be in (0, 1]"}
    if tau <= 0.0:
        return {"error": "tau must be > 0"}

    p_t = p_max * (1.0 - math.exp(-months / tau))
    effective_factor = 1.0 - p_t

    return {
        "attrition_probability": round(p_t, 4),
        "months": float(months),
        "tau_months": float(tau),
        "p_max": float(p_max),
        "effective_velocity_factor": round(effective_factor, 4),
        "india_context": (
            "tau=6 for experienced hires (NASSCOM HR 2024); "
            "tau=12 for fresh graduates"
        ),
    }


# ---------------------------------------------------------------------------
# Function 9: ist_capacity_correction
# ---------------------------------------------------------------------------

def ist_capacity_correction(nominal, overlap_hours=4.0):
    # type: (float, float) -> Dict[str, Any]
    """Apply IST distributed team capacity correction for timezone overlap.

    Formula:
      correction_factor = overlap_hours / 8.0
      effective_capacity = nominal * correction_factor

    India context:
      IST UTC+5:30; typical US-India overlap ~4 hours/day
      (9am-1pm IST morning standup window).
      Q1 (Jan-Mar) applies +15% attrition buffer.

    Args:
        nominal: Nominal capacity in story points or hours (float).
        overlap_hours: Daily effective collaboration hours (default 4.0).

    Returns:
        Dict with keys:
            effective_capacity (float): Adjusted capacity after timezone correction.
            nominal (float): Input nominal capacity.
            overlap_hours (float): Input overlap hours.
            correction_factor (float): overlap_hours / 8.0.
            q1_seasonal_buffer_factor (float): 1.15 (Q1 Jan-Mar buffer constant).
            india_context (str): Context note about IST and Q1 attrition.
    """
    correction_factor = overlap_hours / 8.0
    effective_capacity = nominal * correction_factor

    return {
        "effective_capacity": round(effective_capacity, 4),
        "nominal": float(nominal),
        "overlap_hours": float(overlap_hours),
        "correction_factor": round(correction_factor, 4),
        "q1_seasonal_buffer_factor": 1.15,
        "india_context": (
            "IST UTC+5:30; typical US-India overlap 4h/day "
            "(9am-1pm IST morning standup window); "
            "Q1 Jan-Mar applies +15% attrition buffer"
        ),
    }


# ---------------------------------------------------------------------------
# Function 10: little_law_analysis
# ---------------------------------------------------------------------------

def little_law_analysis(arrivals, departures):
    # type: (List[Dict[str, Any]], List[Dict[str, Any]]) -> Dict[str, Any]
    """Apply Little's Law to compute WIP, throughput, and cycle time estimates.

    Formula:
      L_wip = total_arrived - total_departed
      lambda_throughput = total_departed / periods
      W_cycle_time_days = L_wip / lambda_throughput  (inf if throughput=0)
      wip_limit_recommendation = max(1, int(lambda_throughput * 2))

    Birkhoff caveat: The ergodic theorem requires a stationary process.
    Interpret W_cycle_time_days as ensemble average only if arrival/departure
    rates are stable over the observation window.

    Args:
        arrivals: List of dicts with keys "date" (str) and "count" (int).
        departures: List of dicts with keys "date" (str) and "count" (int).

    Returns:
        Dict with keys:
            L_wip (float): Current WIP (arrived minus departed).
            lambda_throughput (float): Throughput items per period.
            W_cycle_time_days (float): Estimated cycle time. float("inf") if
                throughput is zero.
            birkhoff_caveat (str): Ergodic theorem applicability note.
            wip_limit_recommendation (int): Suggested WIP limit (2x throughput).
        On error: {"error": str}.
    """
    if not arrivals:
        return {"error": "arrivals list must not be empty"}
    if not departures:
        return {"error": "departures list must not be empty"}

    total_arrived = sum(a["count"] for a in arrivals)
    total_departed = sum(d["count"] for d in departures)
    l_wip = float(total_arrived - total_departed)
    periods = len(arrivals)
    lambda_throughput = float(total_departed) / float(periods) if periods > 0 else 0.0

    if lambda_throughput > 0.0:
        w_cycle = l_wip / lambda_throughput
    else:
        w_cycle = float("inf")

    wip_limit = max(1, int(lambda_throughput * 2))

    return {
        "L_wip": round(l_wip, 4),
        "lambda_throughput": round(lambda_throughput, 4),
        "W_cycle_time_days": round(w_cycle, 4) if w_cycle != float("inf") else w_cycle,
        "birkhoff_caveat": (
            "Birkhoff ergodic theorem requires stationary process; "
            "interpret W_cycle_time_days as ensemble average only if "
            "arrival/departure rates are stable"
        ),
        "wip_limit_recommendation": wip_limit,
    }


# ---------------------------------------------------------------------------
# Function 11: cycle_time_lognormal_mle
# ---------------------------------------------------------------------------

def cycle_time_lognormal_mle(cycle_times):
    # type: (List[float]) -> Dict[str, Any]
    """Fit a log-normal distribution to cycle time data via maximum likelihood estimation.

    Algorithm (MLE for log-normal):
      log_times = [log(t) for t in cycle_times]
      mu_hat = mean(log_times)
      sigma_sq = variance(log_times)  (sample variance)
      sigma_hat = sqrt(sigma_sq)
      Percentiles via inverse log-normal:
        P50 = exp(mu_hat)
        P85 = exp(mu_hat + 1.036 * sigma_hat)
        P95 = exp(mu_hat + 1.645 * sigma_hat)

    Args:
        cycle_times: List of positive cycle time values in days (all must be > 0).
                     Minimum 2 values required.

    Returns:
        Dict with keys:
            mu_hat (float): MLE estimate of log-normal location parameter.
            sigma_hat (float): MLE estimate of log-normal scale parameter.
            P50_days (float): Median cycle time estimate.
            P85_days (float): 85th percentile cycle time estimate.
            P95_days (float): 95th percentile cycle time estimate.
            sample_size (int): Number of data points used.
        On error: {"error": str}.
    """
    if len(cycle_times) < 2:
        return {"error": "cycle_times must contain at least 2 values"}

    for t in cycle_times:
        if t <= 0.0:
            return {"error": "All cycle_times must be > 0"}

    log_times = [math.log(t) for t in cycle_times]
    mu_hat = statistics.mean(log_times)
    sigma_sq = statistics.variance(log_times)
    sigma_hat = math.sqrt(sigma_sq)

    p50 = math.exp(mu_hat)
    p85 = math.exp(mu_hat + 1.036 * sigma_hat)
    p95 = math.exp(mu_hat + 1.645 * sigma_hat)

    return {
        "mu_hat": round(mu_hat, 6),
        "sigma_hat": round(sigma_hat, 6),
        "P50_days": round(p50, 4),
        "P85_days": round(p85, 4),
        "P95_days": round(p95, 4),
        "sample_size": len(cycle_times),
    }


# ---------------------------------------------------------------------------
# Function 12: poisson_throughput
# ---------------------------------------------------------------------------

def poisson_throughput(completed, forecast_periods=3):
    # type: (List[int], int) -> Dict[str, Any]
    """Fit a Poisson model to throughput data and generate period-level forecasts.

    Algorithm:
      lambda_hat = mean(completed)
      n_total = sum(completed)
      Wilson-Hilferty chi-squared approximation for Poisson CI:
        _chi2_ppf(p, df): nu*(1 - 2/(9*nu) + z*sqrt(2/(9*nu)))^3
        lower_95 = chi2_ppf(0.025, 2*n_total) / 2
        upper_95 = chi2_ppf(0.975, 2*(n_total+1)) / 2
      Per-period CI bounds: divide by len(completed).

    Args:
        completed: List of non-negative integers of completed items per sprint.
                   Minimum 1 value required; all values must be >= 0.
        forecast_periods: Number of future periods to forecast (default 3).

    Returns:
        Dict with keys:
            lambda_hat (float): Estimated Poisson rate (mean throughput).
            lambda_ci_lower (float): 95% CI lower bound on lambda_hat.
            lambda_ci_upper (float): 95% CI upper bound on lambda_hat.
            forecast (List[Dict]): Per-period forecast with expected, ci_lower, ci_upper.
        On error: {"error": str}.
    """
    if not completed:
        return {"error": "completed list must not be empty"}

    for c in completed:
        if c < 0:
            return {"error": "All completed values must be >= 0"}

    lambda_hat = statistics.mean(completed)
    n_total = sum(completed)
    n_obs = len(completed)

    def _chi2_ppf(p, df):
        # type: (float, float) -> float
        """Wilson-Hilferty chi-squared quantile approximation.

        Approximates the p-th quantile of chi-squared(df) distribution.

        Args:
            p: Probability (0, 1).
            df: Degrees of freedom.

        Returns:
            Approximate quantile value as float.
        """
        if df <= 0:
            return 0.0
        z = _normal_inv_cdf(p)
        nu = float(df)
        factor = 1.0 - 2.0 / (9.0 * nu) + z * math.sqrt(2.0 / (9.0 * nu))
        if factor <= 0.0:
            return 0.0
        return nu * (factor ** 3)

    lower_95_total = _chi2_ppf(0.025, 2 * n_total) / 2.0
    upper_95_total = _chi2_ppf(0.975, 2.0 * (n_total + 1)) / 2.0

    lambda_ci_lower = lower_95_total / float(n_obs) if n_obs > 0 else 0.0
    lambda_ci_upper = upper_95_total / float(n_obs) if n_obs > 0 else 0.0

    forecast = []
    for k in range(forecast_periods):
        forecast.append({
            "period": k + 1,
            "expected": round(lambda_hat, 4),
            "ci_lower": round(lambda_ci_lower, 4),
            "ci_upper": round(lambda_ci_upper, 4),
        })

    return {
        "lambda_hat": round(lambda_hat, 4),
        "lambda_ci_lower": round(lambda_ci_lower, 4),
        "lambda_ci_upper": round(lambda_ci_upper, 4),
        "forecast": forecast,
    }


# ---------------------------------------------------------------------------
# Function 13: pert_estimate
# ---------------------------------------------------------------------------

def pert_estimate(optimistic, most_likely, pessimistic):
    # type: (float, float, float) -> Dict[str, Any]
    """Compute PERT (Program Evaluation and Review Technique) estimate with 90% CI.

    Formula:
      mu = (optimistic + 4 * most_likely + pessimistic) / 6
      sigma = (pessimistic - optimistic) / 6
      ci_90_lower = mu - 1.645 * sigma
      ci_90_upper = mu + 1.645 * sigma

    Args:
        optimistic: Best-case estimate in days (optimistic <= most_likely).
        most_likely: Most probable estimate in days.
        pessimistic: Worst-case estimate in days (pessimistic >= most_likely).

    Returns:
        Dict with keys:
            mu_days (float): PERT weighted mean estimate.
            sigma_days (float): PERT standard deviation.
            ci_90_lower (float): 90% confidence interval lower bound.
            ci_90_upper (float): 90% confidence interval upper bound.
            optimistic (float): Input optimistic value.
            most_likely (float): Input most_likely value.
            pessimistic (float): Input pessimistic value.
        On error: {"error": str}.
    """
    if optimistic > most_likely:
        return {"error": "optimistic must be <= most_likely"}
    if most_likely > pessimistic:
        return {"error": "most_likely must be <= pessimistic"}

    mu = (optimistic + 4.0 * most_likely + pessimistic) / 6.0
    sigma = (pessimistic - optimistic) / 6.0
    ci_lower = mu - 1.645 * sigma
    ci_upper = mu + 1.645 * sigma

    return {
        "mu_days": round(mu, 4),
        "sigma_days": round(sigma, 4),
        "ci_90_lower": round(ci_lower, 4),
        "ci_90_upper": round(ci_upper, 4),
        "optimistic": float(optimistic),
        "most_likely": float(most_likely),
        "pessimistic": float(pessimistic),
    }


# ---------------------------------------------------------------------------
# Function 14: tco_npv_comparison
# ---------------------------------------------------------------------------

def tco_npv_comparison(user_count, years=3, discount_rate=0.10):
    # type: (int, int, float) -> Dict[str, Any]
    """Compare 3-year TCO NPV for Jira Premium vs Azure DevOps (India pricing, INR).

    Pricing basis (INR, 2025):
      Jira Premium: INR 685/user/month (inclusive of cloud hosting)
      Azure DevOps: INR 430/user/month + INR 200,000/year fixed overhead
      GST: 18% applied to both (multiplier 1.18)

    NPV formula (annual cash flows):
      NPV = sum(CF / (1+discount_rate)^t for t in 1..years)

    Break-even: n* = azure_overhead_fixed / (jira_annual_per_user - azure_annual_per_user)

    Args:
        user_count: Number of users (must be >= 1).
        years: NPV horizon in years (default 3).
        discount_rate: Annual discount rate as fraction (default 0.10 = 10%).

    Returns:
        Dict with keys:
            jira_premium_3yr_npv_inr (float): NPV of Jira Premium total cost.
            azure_devops_3yr_npv_inr (float): NPV of Azure DevOps total cost.
            break_even_users (int): User count at which total costs equalize.
            recommendation (str): "Jira Premium" or "Azure DevOps".
            user_count (int): Input user count.
            discount_rate (float): Discount rate used.
    """
    jira_annual_per_user = 685.0 * 12.0 * 1.18
    azure_annual_per_user = 430.0 * 12.0 * 1.18
    azure_overhead_fixed = 200000.0

    jira_cf_per_year = jira_annual_per_user * user_count
    azure_cf_per_year = azure_annual_per_user * user_count + azure_overhead_fixed

    jira_npv = sum(
        jira_cf_per_year / ((1.0 + discount_rate) ** t)
        for t in range(1, years + 1)
    )
    azure_npv = sum(
        azure_cf_per_year / ((1.0 + discount_rate) ** t)
        for t in range(1, years + 1)
    )

    user_cost_diff = jira_annual_per_user - azure_annual_per_user
    if user_cost_diff > 0.0:
        break_even = int(math.ceil(azure_overhead_fixed / user_cost_diff))
    else:
        break_even = 0

    recommendation = "Jira Premium" if user_count >= break_even else "Azure DevOps"

    return {
        "jira_premium_3yr_npv_inr": round(jira_npv, 2),
        "azure_devops_3yr_npv_inr": round(azure_npv, 2),
        "break_even_users": break_even,
        "recommendation": recommendation,
        "user_count": user_count,
        "discount_rate": discount_rate,
    }


# ---------------------------------------------------------------------------
# Function 15: burndown_metrics
# ---------------------------------------------------------------------------

def burndown_metrics(total_points, completed_by_day):
    # type: (int, List[float]) -> Dict[str, Any]
    """Compute sprint burndown chart metrics from daily cumulative completion data.

    Algorithm:
      n = len(completed_by_day)
      ideal_line[i] = total_points - total_points * (i / n) for i in range(n+1)
      actual_line[i] = total_points - cumulative_completed[i] (prepend 0 for day 0)
      remaining = actual_line[-1]
      ideal_remaining = ideal_line[n]  (= 0 for last point)
      deviation_pct = (remaining - ideal_remaining) / total_points * 100
      svi = actual_completed_last_day / total_points
      sprint_health: svi>=0.9->"On Track", svi>=0.7->"At Risk", else->"Off Track"

    Args:
        total_points: Total story points committed for the sprint (must be >= 0).
        completed_by_day: List of cumulative completed story points per day.
                          Index 0 is end of day 1, last index is final sprint day.

    Returns:
        Dict with keys:
            ideal_line (List[float]): Ideal burndown from total_points to 0.
            actual_line (List[float]): Actual remaining points by day (starting at total_points).
            deviation_pct (float): Percentage deviation from ideal at final day.
            svi (float): Sprint Velocity Index = actual_completed / total_points.
            sprint_health (str): "On Track", "At Risk", or "Off Track".
            total_points (int): Input total points.
            days (int): Number of days in the data.
    """
    n = len(completed_by_day)

    if total_points == 0:
        return {
            "ideal_line": [0.0] * (n + 1),
            "actual_line": [0.0] * (n + 1),
            "deviation_pct": 0.0,
            "svi": 0.0,
            "sprint_health": "On Track",
            "total_points": 0,
            "days": n,
        }

    ideal_line = [
        float(total_points) - float(total_points) * (float(i) / float(n))
        for i in range(n + 1)
    ]

    cumulative = [0.0] + list(completed_by_day)
    actual_line = [float(total_points) - c for c in cumulative]

    remaining = actual_line[-1]
    ideal_remaining = ideal_line[-1]
    deviation_pct = (remaining - ideal_remaining) / float(total_points) * 100.0

    actual_completed = float(completed_by_day[-1]) if completed_by_day else 0.0
    svi = actual_completed / float(total_points)

    if svi >= 0.9:
        sprint_health = "On Track"
    elif svi >= 0.7:
        sprint_health = "At Risk"
    else:
        sprint_health = "Off Track"

    return {
        "ideal_line": [round(v, 4) for v in ideal_line],
        "actual_line": [round(v, 4) for v in actual_line],
        "deviation_pct": round(deviation_pct, 4),
        "svi": round(svi, 4),
        "sprint_health": sprint_health,
        "total_points": total_points,
        "days": n,
    }


# ---------------------------------------------------------------------------
# Function 16: multi_sprint_holiday_forecast
# ---------------------------------------------------------------------------

def multi_sprint_holiday_forecast(sprint_start, sprint_duration_days, num_sprints):
    # type: (str, int, int) -> Dict[str, Any]
    """Forecast India national holidays across multiple consecutive sprint windows.

    Uses INDIA_NATIONAL_HOLIDAYS_2025_2026 frozenset for date matching and
    _INDIA_HOLIDAY_NAMES dict for human-readable names. Dates outside 2025-2026
    will show 0 holidays with no error.

    Args:
        sprint_start: Sprint 1 start date as ISO string "YYYY-MM-DD".
        sprint_duration_days: Duration of each sprint in calendar days (must be >= 1).
        num_sprints: Number of consecutive sprints to forecast (must be >= 1).

    Returns:
        Dict with key:
            sprints (List[Dict]): Per-sprint forecast records, each containing:
                sprint_number (int): 1-based sprint index.
                start_date (str): Sprint start date "YYYY-MM-DD".
                end_date (str): Sprint end date "YYYY-MM-DD" (inclusive).
                holiday_count (int): Number of India holidays in window.
                holiday_names (List[str]): Names of holidays in window.
                effective_days (int): sprint_duration_days minus holiday_count.
        On error: {"error": str}.
    """
    if sprint_duration_days < 1:
        return {"error": "sprint_duration_days must be >= 1"}
    if num_sprints < 1:
        return {"error": "num_sprints must be >= 1"}

    try:
        start_d = date.fromisoformat(sprint_start)
    except ValueError:
        return {"error": "sprint_start must be a valid ISO date string YYYY-MM-DD"}

    from datetime import timedelta

    sprints_result = []
    for k in range(num_sprints):
        s_start = start_d + timedelta(days=k * sprint_duration_days)
        s_end = s_start + timedelta(days=sprint_duration_days - 1)

        holidays_in_sprint = []
        for h_str in INDIA_NATIONAL_HOLIDAYS_2025_2026:
            h_date = date.fromisoformat(h_str)
            if s_start <= h_date <= s_end:
                holidays_in_sprint.append(h_str)

        holidays_in_sprint.sort()
        holiday_names = [
            _INDIA_HOLIDAY_NAMES.get(h, "India National Holiday")
            for h in holidays_in_sprint
        ]
        effective_days = sprint_duration_days - len(holidays_in_sprint)

        sprints_result.append({
            "sprint_number": k + 1,
            "start_date": s_start.isoformat(),
            "end_date": s_end.isoformat(),
            "holiday_count": len(holidays_in_sprint),
            "holiday_names": holiday_names,
            "effective_days": effective_days,
        })

    return {"sprints": sprints_result}
