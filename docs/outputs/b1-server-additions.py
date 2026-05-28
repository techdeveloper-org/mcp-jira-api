"""
b1-server-additions.py -- Staging file for Phase B.1 server tool stubs.

These tool stubs are written as if they exist in server.py context.
They depend on the following imports that are already present in server.py:
    from base.decorators import mcp_tool_handler
    from base.response import success, error
    from input_validator import validate_input
    import scrum_calculator
    import json
    from typing import Optional

validate_string and validate_positive_int are thin wrappers defined locally
in this file for standalone readability. In the actual server.py integration,
B.3 (python-backend-engineer) will replace these with the canonical
input_validator.validate_input() calls.

Windows-Safe: ASCII only (cp1252 compatible)
Python 3.8+: no walrus operator, no match statement, no 3.10+ features.
"""

import json
from typing import Optional


# ---------------------------------------------------------------------------
# Local shims for standalone readability (B.3 will inline input_validator calls)
# ---------------------------------------------------------------------------

def validate_string(value, field_name="input", max_length=4096):
    """Shim: delegates to input_validator.validate_input in server.py context.

    Args:
        value: Raw string value to clean.
        field_name: Human-readable field name for error messages.
        max_length: Maximum allowed character length after stripping.

    Returns:
        Cleaned string with null bytes removed and whitespace stripped.

    Raises:
        TypeError: If value is not a str.
        ValueError: If cleaned value exceeds max_length.
    """
    if not isinstance(value, str):
        raise TypeError("Expected str for '{}', got {}".format(field_name, type(value).__name__))
    cleaned = value.replace("\x00", "").strip()
    if len(cleaned) > max_length:
        raise ValueError("Field '{}' exceeds max length {}".format(field_name, max_length))
    return cleaned


def validate_positive_int(value, field_name="input"):
    """Shim: validates that value is a positive integer.

    Args:
        value: Value to validate (must be int and > 0).
        field_name: Human-readable field name for error messages.

    Returns:
        The validated integer value.

    Raises:
        TypeError: If value is not an int.
        ValueError: If value is not > 0.
    """
    if not isinstance(value, int):
        raise TypeError("Expected int for '{}', got {}".format(field_name, type(value).__name__))
    if value <= 0:
        raise ValueError("Field '{}' must be > 0, got {}".format(field_name, value))
    return value


# ---------------------------------------------------------------------------
# NEW TOOL 1: jira_spotify_health_check
# ---------------------------------------------------------------------------

@mcp_tool_handler(tool_name="jira_spotify_health_check")
async def jira_spotify_health_check(
    board_id: int,
    dimension_scores: str,
    prev_dimension_scores: Optional[str] = None,
) -> str:
    """Run Spotify Squad Health Check scoring for a team.

    Computes THS (Team Health Score) across 11 standard dimensions using
    uniform weights. Optionally computes Wilcoxon signed-rank Z statistic
    for quarter-on-quarter delta if prev_dimension_scores is provided.

    11 required dimensions (keys in dimension_scores JSON):
      easy_to_release, suitable_process, tech_quality, value, speed,
      mission, fun, learning, support, pawns_or_players, team_spirit

    Args:
        board_id: Jira board ID for context (used for audit trail, not for data fetch).
        dimension_scores: JSON string mapping each of the 11 dimension names to
            a list of integer scores (0=unhealthy, 1=neutral, 2=healthy).
            Example: '{"easy_to_release": [1, 2, 1], "suitable_process": [2, 2], ...}'
        prev_dimension_scores: Optional JSON string mapping dimension names to
            previous period mean scores (floats) for delta computation.
            Example: '{"easy_to_release": 1.5, "suitable_process": 2.0, ...}'

    Returns:
        JSON string with keys:
            THS (float): Team Health Score 0.0-2.0.
            dimension_scores (Dict[str, float]): Per-dimension mean scores.
            health_color (str): "Green" (>=1.5), "Amber" (>=0.75), "Red" (<0.75).
            wilcoxon_Z (float or null): Z statistic if prev provided.
            delta_vs_previous (float or null): THS delta from previous period.
    """
    validated_board = validate_positive_int(board_id, "board_id")
    scores_dict = json.loads(validate_string(dimension_scores, "dimension_scores"))
    prev_dict = (
        json.loads(validate_string(prev_dimension_scores, "prev_dimension_scores"))
        if prev_dimension_scores
        else None
    )
    result = scrum_calculator.spotify_health_check(scores_dict, prev_scores=prev_dict)
    if "error" in result:
        return error(result["error"], error_type="COMPUTATION_ERROR")
    return success(**result)


# ---------------------------------------------------------------------------
# NEW TOOL 2: jira_psychological_safety
# ---------------------------------------------------------------------------

@mcp_tool_handler(tool_name="jira_psychological_safety")
async def jira_psychological_safety(
    board_id: int,
    item_scores: str,
) -> str:
    """Compute Edmondson Psychological Safety Scale score for a team.

    Applies reverse-coding to items at positions 0, 2, 4 (0-indexed) per
    Edmondson (1999). Returns a PS score in range 1.0-7.0.

    Args:
        board_id: Jira board ID for context (not used for data fetch).
        item_scores: JSON array of exactly 7 integers, each in [1, 7].
            Example: '[3, 5, 2, 6, 4, 5, 3]'
            Items at positions 0, 2, 4 are reverse-coded (8 - score).

    Returns:
        JSON string with keys:
            PS_score (float): Mean psychological safety score (1.0-7.0).
            cronbach_alpha (float): Estimated Cronbach alpha (informational for
                single-respondent input; use multi-respondent data for valid alpha).
            interpretation (str): "Low" (<3.5), "Moderate" (3.5-5.5), "High" (>5.5).
            reverse_coded_positions (List[int]): [0, 2, 4].
    """
    validated_board = validate_positive_int(board_id, "board_id")
    raw_scores = json.loads(validate_string(item_scores, "item_scores"))
    if not isinstance(raw_scores, list):
        return error("item_scores must be a JSON array of 7 integers", error_type="VALIDATION_ERROR")
    result = scrum_calculator.edmondson_ps_scale(raw_scores)
    if "error" in result:
        return error(result["error"], error_type="COMPUTATION_ERROR")
    return success(**result)


# ---------------------------------------------------------------------------
# NEW TOOL 3: jira_cognitive_load
# ---------------------------------------------------------------------------

@mcp_tool_handler(tool_name="jira_cognitive_load")
async def jira_cognitive_load(
    board_id: int,
    complexity_json: str,
    responsibility_json: str,
    cl_max: float = 10.0,
) -> str:
    """Compute Team Topology Cognitive Load Index (CLI) for a team's domain portfolio.

    CLI = sum(complexity[d] * responsibility[d] for d in common domains) / cl_max
    overloaded = CLI > 1.0

    Args:
        board_id: Jira board ID for context (not used for data fetch).
        complexity_json: JSON object mapping domain name to complexity weight (float >= 0).
            Example: '{"payments": 3.5, "auth": 2.0, "reporting": 1.5}'
        responsibility_json: JSON object mapping domain name to responsibility
            fraction (float >= 0).
            Example: '{"payments": 0.8, "auth": 1.0, "reporting": 0.5}'
        cl_max: Maximum cognitive load threshold (default 10.0). Must be > 0.

    Returns:
        JSON string with keys:
            CL_team (float): Raw cognitive load sum across common domains.
            CLI (float): Normalized cognitive load index (CL_team / cl_max).
            overloaded (bool): True if CLI > 1.0.
            domain_contributions (Dict[str, float]): Per-domain load contribution.
            cl_max (float): Threshold used.
            topology_efficiency (Dict[str, float]): Reference mode efficiency factors.
    """
    validated_board = validate_positive_int(board_id, "board_id")
    complexity = json.loads(validate_string(complexity_json, "complexity_json"))
    responsibility = json.loads(validate_string(responsibility_json, "responsibility_json"))
    if cl_max <= 0.0:
        return error("cl_max must be > 0", error_type="VALIDATION_ERROR")
    result = scrum_calculator.cognitive_load_index(complexity, responsibility, cl_max=cl_max)
    return success(**result)


# ---------------------------------------------------------------------------
# NEW TOOL 4: jira_attrition_forecast
# ---------------------------------------------------------------------------

@mcp_tool_handler(tool_name="jira_attrition_forecast")
async def jira_attrition_forecast(
    board_id: int,
    months: float,
    p_max: float,
    tau: float = 6.0,
) -> str:
    """Forecast cumulative attrition impact on team velocity using exponential model.

    P(t) = p_max * (1 - exp(-months / tau))
    effective_velocity_factor = 1 - P(t)

    tau reference values (NASSCOM HR 2024):
      6 months for experienced hires; 12 months for fresh graduates.

    Args:
        board_id: Jira board ID for context (not used for data fetch).
        months: Time elapsed in months (must be > 0).
        p_max: Maximum asymptotic attrition probability; fraction in (0, 1].
        tau: Exponential time constant in months (default 6.0, must be > 0).

    Returns:
        JSON string with keys:
            attrition_probability (float): Cumulative attrition at t=months.
            months (float): Input time.
            tau_months (float): Time constant used.
            p_max (float): Input maximum attrition fraction.
            effective_velocity_factor (float): Remaining effective velocity fraction.
            india_context (str): NASSCOM HR 2024 context note.
    """
    validated_board = validate_positive_int(board_id, "board_id")
    result = scrum_calculator.attrition_ramp(months, p_max, tau=tau)
    if "error" in result:
        return error(result["error"], error_type="VALIDATION_ERROR")
    return success(**result)


# ---------------------------------------------------------------------------
# NEW TOOL 5: jira_pert_estimate
# ---------------------------------------------------------------------------

@mcp_tool_handler(tool_name="jira_pert_estimate")
async def jira_pert_estimate(
    optimistic: float,
    most_likely: float,
    pessimistic: float,
) -> str:
    """Compute a PERT (Program Evaluation and Review Technique) task estimate.

    mu = (optimistic + 4 * most_likely + pessimistic) / 6
    sigma = (pessimistic - optimistic) / 6
    90% CI = mu +/- 1.645 * sigma

    Args:
        optimistic: Best-case estimate in days (must be <= most_likely).
        most_likely: Most probable estimate in days.
        pessimistic: Worst-case estimate in days (must be >= most_likely).

    Returns:
        JSON string with keys:
            mu_days (float): PERT weighted mean estimate in days.
            sigma_days (float): PERT standard deviation in days.
            ci_90_lower (float): 90% CI lower bound in days.
            ci_90_upper (float): 90% CI upper bound in days.
            optimistic (float): Input optimistic value.
            most_likely (float): Input most_likely value.
            pessimistic (float): Input pessimistic value.
    """
    result = scrum_calculator.pert_estimate(optimistic, most_likely, pessimistic)
    if "error" in result:
        return error(result["error"], error_type="VALIDATION_ERROR")
    return success(**result)


# ---------------------------------------------------------------------------
# NEW TOOL 6: jira_scrum_of_scrums
# ---------------------------------------------------------------------------

@mcp_tool_handler(tool_name="jira_scrum_of_scrums")
async def jira_scrum_of_scrums(
    teams: int,
    productivity_per_team: float,
    coordination_cost: float,
) -> str:
    """Compute Scrum of Scrums Brook's Law overhead and optimal team count.

    T_n = teams * p - c * teams * (teams - 1) / 2
    n_optimal = p / c + 0.5
    overhead_ratio = coordination_overhead / total_raw_capacity

    Args:
        teams: Number of participating Scrum teams (must be >= 2).
        productivity_per_team: Baseline sprint velocity per team (must be > 0).
            Typically in story points per sprint.
        coordination_cost: Communication overhead cost per team pair per sprint
            (must be > 0 and < productivity_per_team). Typically in story points.

    Returns:
        JSON string with keys:
            T_n (float): Net throughput after coordination overhead.
            n_optimal (float): Team count that maximizes throughput.
            overhead_ratio (float): Fraction of capacity lost to coordination.
            teams (int): Input team count.
            productivity_per_team (float): Input p value.
            coordination_cost (float): Input c value.
    """
    result = scrum_calculator.scrum_of_scrums_overhead(
        teams, productivity_per_team, coordination_cost
    )
    if "error" in result:
        return error(result["error"], error_type="VALIDATION_ERROR")
    return success(**result)


# ---------------------------------------------------------------------------
# NEW TOOL 7: jira_ist_capacity
# ---------------------------------------------------------------------------

@mcp_tool_handler(tool_name="jira_ist_capacity")
async def jira_ist_capacity(
    nominal_capacity: float,
    overlap_hours: float = 4.0,
) -> str:
    """Compute IST timezone distributed team effective capacity.

    Applies a correction factor for the reduced collaboration window when
    teams span IST (UTC+5:30) and US timezones.

    correction_factor = overlap_hours / 8.0
    effective_capacity = nominal_capacity * correction_factor

    Args:
        nominal_capacity: Nominal sprint capacity in story points or hours.
        overlap_hours: Daily effective collaboration window in hours (default 4.0).
            Typical US-India overlap: 4 hours/day (9am-1pm IST window).

    Returns:
        JSON string with keys:
            effective_capacity (float): Adjusted capacity after timezone correction.
            nominal (float): Input nominal capacity.
            overlap_hours (float): Overlap hours used.
            correction_factor (float): overlap_hours / 8.0.
            q1_seasonal_buffer_factor (float): 1.15 for Q1 Jan-Mar attrition buffer.
            india_context (str): IST timezone and Q1 context note.
    """
    result = scrum_calculator.ist_capacity_correction(nominal_capacity, overlap_hours=overlap_hours)
    return success(**result)


# ---------------------------------------------------------------------------
# NEW TOOL 8: jira_multi_sprint_holidays
# ---------------------------------------------------------------------------

@mcp_tool_handler(tool_name="jira_multi_sprint_holidays")
async def jira_multi_sprint_holidays(
    sprint_start: str,
    sprint_duration_days: int = 14,
    num_sprints: int = 3,
) -> str:
    """Forecast India national holidays across consecutive sprint windows.

    Uses INDIA_NATIONAL_HOLIDAYS_2025_2026 constant from scrum_calculator.py.
    Dates outside 2025-2026 range will show 0 holidays (no error).

    Args:
        sprint_start: Sprint 1 start date as ISO string "YYYY-MM-DD".
        sprint_duration_days: Calendar days per sprint (default 14, must be >= 1).
        num_sprints: Number of consecutive sprints to analyze (default 3, must be >= 1).

    Returns:
        JSON string with key:
            sprints (List[Dict]): Per-sprint records, each with:
                sprint_number (int): 1-based index.
                start_date (str): Sprint start "YYYY-MM-DD".
                end_date (str): Sprint end "YYYY-MM-DD" (inclusive).
                holiday_count (int): India holidays in window.
                holiday_names (List[str]): Holiday names in window.
                effective_days (int): sprint_duration_days - holiday_count.
    """
    clean_start = validate_string(sprint_start, "sprint_start")
    result = scrum_calculator.multi_sprint_holiday_forecast(
        clean_start, sprint_duration_days, num_sprints
    )
    if "error" in result:
        return error(result["error"], error_type="VALIDATION_ERROR")
    return success(**result)


# ---------------------------------------------------------------------------
# NEW TOOL 9: jira_rate_limit_status
# ---------------------------------------------------------------------------

@mcp_tool_handler(tool_name="jira_rate_limit_status")
async def jira_rate_limit_status() -> str:
    """Return the current rate limiter bucket status (read-only).

    Reads the internal rate_limiter module state to report on current token
    counts, capacity, and refill rates for all active buckets. This tool
    makes NO modifications to rate limiter state.

    Only meaningful when ENABLE_RATE_LIMITING=1 is set in the environment.
    When rate limiting is disabled, returns a disabled status report.

    Returns:
        JSON string with keys:
            rate_limiting_enabled (bool): Whether ENABLE_RATE_LIMITING=1 is set.
            buckets (List[Dict]): Per-bucket status records, each with:
                client_id (str): Client identifier.
                bucket_name (str): Bucket name (e.g. "tool_calls").
                capacity (float): Maximum token capacity.
                refill_rate_per_sec (float): Tokens added per second.
                tokens_available (float): Approximate current token count
                    (snapshot; may change immediately after read).
            bucket_count (int): Total number of active buckets.
    """
    import os
    import rate_limiter as _rl

    enabled = os.environ.get("ENABLE_RATE_LIMITING") == "1"

    buckets_snapshot = []
    with _rl._buckets_lock:
        for (client_id, bucket_name), bucket in _rl._buckets.items():
            with bucket._lock:
                bucket._refill()
                buckets_snapshot.append({
                    "client_id": client_id,
                    "bucket_name": bucket_name,
                    "capacity": bucket._capacity,
                    "refill_rate_per_sec": bucket._refill_rate,
                    "tokens_available": round(bucket._tokens, 4),
                })

    return success(
        rate_limiting_enabled=enabled,
        buckets=buckets_snapshot,
        bucket_count=len(buckets_snapshot),
    )


# ===========================================================================
# UPGRADE DIFFS
# B.3 (python-backend-engineer) will splice these blocks into existing tools.
# Each block is labelled with the target function and insertion anchor.
# ===========================================================================

# ---------------------------------------------------------------------------
# UPGRADE 1: jira_refine_backlog -- add WSJF scoring
# TARGET: jira_refine_backlog function in server.py
# ---- INSERT AFTER: the section that builds the backlog item list / template ----
# ---- (search for the return dict construction, insert before it) ----
# ---------------------------------------------------------------------------

# UPGRADE: jira_refine_backlog -- replace static WSJF template with scored ranking
# B.3: locate the return dict in jira_refine_backlog; insert this block before the return.
# Assumes 'backlog_items' is a list of dicts already built from the agile API response.
# Each item must contain or can default: business_value, time_criticality,
# risk_reduction, job_size (all int, Fibonacci scale 1-20).
# ---- BEGIN UPGRADE BLOCK ----
def _upgrade_refine_backlog_wsjf_block(backlog_items):
    """Score and sort backlog items by WSJF priority.

    Computes WSJF = (business_value + time_criticality + risk_reduction) / job_size
    for each backlog item and sorts descending (highest priority first).

    Args:
        backlog_items: List of dicts, each with optional integer keys:
            business_value, time_criticality, risk_reduction, job_size.
            Missing keys default to 1. job_size defaults to 1 if missing or 0.

    Returns:
        List of dicts with added 'wsjf_score' key, sorted descending by wsjf_score.
    """
    import scrum_calculator as _sc
    for item in backlog_items:
        bv = int(item.get("business_value", 1) or 1)
        tc = int(item.get("time_criticality", 1) or 1)
        rr = int(item.get("risk_reduction", 1) or 1)
        js = int(item.get("job_size", 1) or 1)
        if js <= 0:
            js = 1
        try:
            item["wsjf_score"] = round(_sc.wsjf_score(bv, tc, rr, js), 4)
        except (ValueError, ZeroDivisionError):
            item["wsjf_score"] = 0.0
    backlog_items.sort(key=lambda x: x.get("wsjf_score", 0.0), reverse=True)
    return backlog_items
# ---- END UPGRADE BLOCK ----


# ---------------------------------------------------------------------------
# UPGRADE 2: jira_sprint_review -- add AHP DoD criteria scoring
# TARGET: jira_sprint_review function in server.py
# ---- INSERT AFTER: the done_issues / not_delivered breakdown section ----
# ---- (search for 'scope_change_count' or the final return dict, insert before) ----
# ---------------------------------------------------------------------------

# UPGRADE: jira_sprint_review -- AHP criteria matrix for standard 3-criterion DoD
# B.3: insert this block inside jira_sprint_review, before the final return statement.
# Uses a standard 3-criterion DoD matrix: functionality, quality, completeness.
# ---- BEGIN UPGRADE BLOCK ----
def _upgrade_sprint_review_ahp_block():
    """Compute AHP weights for a standard 3-criterion Definition of Done matrix.

    Standard 3-criterion DoD pairwise matrix (functionality/quality/completeness):
      - Functionality is 3x more important than quality
      - Functionality is 5x more important than completeness
      - Quality is 2x more important than completeness

    Returns:
        Dict with AHP result keys or {"error": str} if computation fails.
    """
    import scrum_calculator as _sc
    dod_matrix = [
        [1.0,       3.0,  5.0],
        [1.0 / 3.0, 1.0,  2.0],
        [1.0 / 5.0, 0.5,  1.0],
    ]
    ahp_result = _sc.ahp_score(dod_matrix)
    return {
        "ahp_dod_criteria": ["functionality", "quality", "completeness"],
        "ahp_weights": ahp_result.get("weights", []),
        "ahp_CR": ahp_result.get("CR", None),
        "ahp_consistent": ahp_result.get("consistent", None),
        "ahp_note": (
            "Standard 3-criterion DoD matrix. CR < 0.10 confirms consistent weighting."
        ),
    }
# ---- END UPGRADE BLOCK ----


# ---------------------------------------------------------------------------
# UPGRADE 3: jira_team_health -- replace tuckman_estimate with tuckman_markov
# TARGET: jira_team_health function in server.py, around line 2051
# ---- REPLACE: tuckman_stage = scrum_calculator.tuckman_estimate(...) ----
# ---- WITH: the block below ----
# ---------------------------------------------------------------------------

# UPGRADE: jira_team_health -- replace tuckman_estimate() with tuckman_markov()
# B.3: Find the following block in jira_team_health (approx line 2051 in server.py):
#
#   tuckman_stage = scrum_calculator.tuckman_estimate(
#       velocity_cv=cv_val,
#       velocity_trend=velocity_trend,
#       team_age_sprints=len(velocity_points),
#   )
#
# REPLACE IT WITH:
# ---- BEGIN UPGRADE BLOCK ----
def _upgrade_team_health_tuckman_markov_block(velocity_points):
    """Call tuckman_markov and extract stage and extended metadata.

    Replaces the tuckman_estimate() call in jira_team_health. Provides
    stage probabilities and NASSCOM AgileX level from the new model.

    Args:
        velocity_points: List of sprint velocity integers.

    Returns:
        Tuple of (tuckman_stage str, tuckman_meta dict).
        tuckman_meta contains stage_probabilities, nasscom_agile_x_level,
        empirical_caveat for inclusion in the tool response.
    """
    import scrum_calculator as _sc
    if len(velocity_points) >= 2:
        markov_result = _sc.tuckman_markov(velocity_points)
        if "error" not in markov_result:
            tuckman_stage = markov_result["current_stage"]
            tuckman_meta = {
                "tuckman_stage_probabilities": markov_result["stage_probabilities"],
                "tuckman_nasscom_level": markov_result["nasscom_agile_x_level"],
                "tuckman_empirical_caveat": markov_result["empirical_caveat"],
            }
            return tuckman_stage, tuckman_meta
    tuckman_stage = _sc.tuckman_estimate(
        velocity_cv=float(sum(velocity_points) and 0.5 or 0.5),
        velocity_trend=0.0,
        team_age_sprints=len(velocity_points),
    )
    return tuckman_stage, {}
# ---- END UPGRADE BLOCK ----

# B.3 INTEGRATION INSTRUCTIONS for UPGRADE 3:
# 1. Remove the existing tuckman_estimate() call block (lines ~2051-2055).
# 2. Replace with:
#      tuckman_stage, tuckman_meta = _upgrade_team_health_tuckman_markov_block(velocity_points)
# 3. Merge tuckman_meta into the final return dict of jira_team_health.
# 4. Remove the _upgrade_team_health_tuckman_markov_block helper -- inline the logic directly.


# ---------------------------------------------------------------------------
# UPGRADE 4: jira_get_velocity -- add bootstrap BCa CI as supplemental output
# TARGET: jira_get_velocity function in server.py
# This is SUPPLEMENTAL -- does NOT replace the existing pstdev call.
# ---- INSERT AFTER: result = velocity_stats(velocity_data) ----
# ---------------------------------------------------------------------------

# UPGRADE: jira_get_velocity -- supplement velocity_stats() with BCa bootstrap CI
# B.3: Locate the velocity result dict construction in jira_get_velocity.
# Insert the following block AFTER the velocity_stats() call result is computed.
# 'velocity_points' is the list of int velocity values used in the existing tool.
# ---- BEGIN UPGRADE BLOCK ----
# ---- INSERT AFTER: result = scrum_calculator.velocity_stats(velocity_points) ----
#
#   bca_result = scrum_calculator.bootstrap_bca_ci(
#       [float(v) for v in velocity_points],
#       confidence=0.95,
#       B=1000,
#   )
#   if "error" not in bca_result:
#       result["bca_ci_lower"] = bca_result["lower"]
#       result["bca_ci_upper"] = bca_result["upper"]
#       result["bca_point_estimate"] = bca_result["point_estimate"]
#       result["bca_confidence"] = bca_result["confidence"]
#       result["bca_B"] = bca_result["B"]
#   else:
#       result["bca_note"] = bca_result.get("note", bca_result.get("error", "BCa skipped"))
#
# ---- END UPGRADE BLOCK ----
#
# NOTE: The existing pstdev call in velocity_stats() is NOT replaced.
# BCa CI is additive metadata for callers who need bootstrapped bounds.
# 'result' here refers to the dict returned by velocity_stats() before
# it is wrapped in success(). Add the bca_* keys to that dict directly.
# ---- END UPGRADE INSTRUCTIONS ----
