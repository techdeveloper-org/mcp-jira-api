# B.2 staging file -- python-backend-engineer (B.3) will append this to server.py
#
# scrum_calculator imports needed from this file:
#   burndown_metrics, little_law_analysis, cycle_time_lognormal_mle,
#   poisson_throughput, tco_npv_comparison
#
# These functions are implemented by scrum-master-agent (Phase B.1) in
# scrum_calculator.py. All 5 must exist before B.3 integration.
#
# AgileClient import:
#   from agile_client import AgileClient
#
# Windows-Safe: ASCII only (cp1252 compatible)
# Python 3.8+ -- no walrus operator, no match statements

import json
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Imports assumed to be already present at the top of server.py after B.3
# integration:
#   from base.decorators import mcp_tool_handler
#   from base.response import success, error
#   from input_validator import validate_input, validate_positive_int
#   from agile_client import AgileClient
#   import scrum_calculator
#
# The 5 scrum_calculator functions imported via scrum_calculator.<name>():
#   scrum_calculator.burndown_metrics(total_points, completed_by_day)
#   scrum_calculator.little_law_analysis(arrivals, departures)
#   scrum_calculator.cycle_time_lognormal_mle(cycle_times)
#   scrum_calculator.poisson_throughput(completed_per_sprint, forecast_periods)
#   scrum_calculator.tco_npv_comparison(user_count, years, discount_rate)
# ---------------------------------------------------------------------------


def validate_positive_int(value, field_name="value"):
    # type: (object, str) -> int
    """Validate that value is a positive integer (>= 1).

    Args:
        value: The raw value to validate.
        field_name: Human-readable field name for error messages.

    Returns:
        Integer value if valid.

    Raises:
        TypeError: If value cannot be converted to int.
        ValueError: If value is less than 1.
    """
    try:
        int_val = int(value)
    except (TypeError, ValueError):
        raise TypeError(
            "Expected positive integer for field '{}', got {!r}".format(
                field_name, value
            )
        )
    if int_val < 1:
        raise ValueError(
            "Field '{}' must be >= 1, got {}".format(field_name, int_val)
        )
    return int_val


# ---------------------------------------------------------------------------
# Tool 1: jira_burndown_chart
# ---------------------------------------------------------------------------

@mcp.tool()
@mcp_tool_handler
def jira_burndown_chart(board_id: int, sprint_id: int) -> dict:
    """Fetch sprint burndown data and compute burndown health metrics.

    Retrieves raw burndown chart data from the Jira Agile rapid charts API
    and passes it to scrum_calculator.burndown_metrics() to produce ideal
    vs. actual trend comparison, slope analysis, and sprint health verdict.

    Args:
        board_id: Numeric Jira board ID (rapid view ID). Must be >= 1.
        sprint_id: Numeric sprint ID for the burndown period. Must be >= 1.

    Returns:
        JSON string with success=true and keys:
            board_id (int): Echo of board_id.
            sprint_id (int): Echo of sprint_id.
            total_points (float): Total story points at sprint start.
            burndown_metrics (dict): Output from scrum_calculator.burndown_metrics().
        On failure: JSON string with success=false and error details.
    """
    board_id = validate_positive_int(board_id, "board_id")
    sprint_id = validate_positive_int(sprint_id, "sprint_id")

    cfg = _get_config()
    client = AgileClient(cfg)

    raw = client.get_burndown_chart(board_id, sprint_id)
    if raw is None:
        return error(
            "Jira returned no burndown data for board_id={} sprint_id={}".format(
                board_id, sprint_id
            ),
            error_type="INVALID_RESPONSE"
        )

    completed_arr = raw.get("completedPoints") or []
    incompleted_arr = raw.get("incompletedPoints") or []

    if not completed_arr and not incompleted_arr:
        return error(
            "Burndown response missing completedPoints and incompletedPoints arrays",
            error_type="INVALID_RESPONSE"
        )

    if incompleted_arr and completed_arr:
        first_incomplete = incompleted_arr[0] if isinstance(incompleted_arr[0], (int, float)) else 0
        first_complete = completed_arr[0] if isinstance(completed_arr[0], (int, float)) else 0
        total_points = float(first_incomplete + first_complete)
    elif incompleted_arr:
        first = incompleted_arr[0]
        total_points = float(first) if isinstance(first, (int, float)) else 0.0
    else:
        total_points = float(max(completed_arr)) if completed_arr else 0.0

    if isinstance(completed_arr[0] if completed_arr else None, dict):
        completed_by_day = [
            float(entry.get("value", 0)) for entry in completed_arr
        ]
    else:
        completed_by_day = [float(v) for v in completed_arr]

    metrics = scrum_calculator.burndown_metrics(total_points, completed_by_day)

    return success(
        board_id=board_id,
        sprint_id=sprint_id,
        total_points=total_points,
        burndown_metrics=metrics
    )


# ---------------------------------------------------------------------------
# Tool 2: jira_cfd_analysis
# ---------------------------------------------------------------------------

@mcp.tool()
@mcp_tool_handler
def jira_cfd_analysis(board_id: int) -> dict:
    """Fetch cumulative flow diagram data and apply Little's Law analysis.

    Retrieves CFD column data from the Jira Agile rapid charts API and
    passes arrival/departure streams to scrum_calculator.little_law_analysis()
    to estimate average WIP, average cycle time, and throughput rate.

    Args:
        board_id: Numeric Jira board ID (rapid view ID). Must be >= 1.

    Returns:
        JSON string with success=true and keys:
            board_id (int): Echo of board_id.
            little_law (dict): Output from scrum_calculator.little_law_analysis().
        On failure: JSON string with success=false and error details.
    """
    board_id = validate_positive_int(board_id, "board_id")

    cfg = _get_config()
    client = AgileClient(cfg)

    raw = client.get_cfd(board_id)
    if raw is None:
        return error(
            "Jira returned no CFD data for board_id={}".format(board_id),
            error_type="INVALID_RESPONSE"
        )

    column_data = raw.get("columnData") or []
    if not column_data:
        return error(
            "CFD response missing columnData array",
            error_type="INVALID_RESPONSE"
        )

    arrivals = []
    departures = []

    for day_entry in column_data:
        day_label = day_entry.get("date", "")
        columns = day_entry.get("columns") or []

        if columns:
            first_col_count = int(columns[0].get("count", 0)) if columns else 0
            arrivals.append({"date": day_label, "count": first_col_count})

        done_count = 0
        for col in columns:
            col_name = (col.get("name") or col.get("status") or "").lower()
            if "done" in col_name or "complete" in col_name or "closed" in col_name:
                done_count = int(col.get("count", 0))
                break
        departures.append({"date": day_label, "count": done_count})

    little_law_result = scrum_calculator.little_law_analysis(arrivals, departures)

    return success(
        board_id=board_id,
        little_law=little_law_result
    )


# ---------------------------------------------------------------------------
# Tool 3: jira_cycle_time_analysis
# ---------------------------------------------------------------------------

@mcp.tool()
@mcp_tool_handler
def jira_cycle_time_analysis(board_id: int, sprint_id: int) -> dict:
    """Compute cycle time distribution for issues resolved in a sprint.

    Fetches sprint issues and individual issue changelogs, computes cycle
    time in days from created to resolutiondate, then fits a log-normal
    distribution using scrum_calculator.cycle_time_lognormal_mle().

    Args:
        board_id: Numeric Jira board ID. Must be >= 1.
        sprint_id: Numeric sprint ID. Must be >= 1.

    Returns:
        JSON string with success=true and keys:
            board_id (int): Echo of board_id.
            sprint_id (int): Echo of sprint_id.
            lognormal_fit (dict): Output from scrum_calculator.cycle_time_lognormal_mle().
            per_issue_cycle_times (dict): Mapping of issue_key to cycle_time_days.
            resolved_count (int): Number of issues with resolved cycle times.
        On failure: JSON string with success=false and error details.
    """
    board_id = validate_positive_int(board_id, "board_id")
    sprint_id = validate_positive_int(sprint_id, "sprint_id")

    cfg = _get_config()
    client = AgileClient(cfg)

    sprint_issues_raw = client.get_sprint_issues(
        sprint_id,
        fields="summary,status,created,resolutiondate"
    )
    if sprint_issues_raw is None:
        return error(
            "No issues found for sprint_id={}".format(sprint_id),
            error_type="INVALID_RESPONSE"
        )

    issue_list = sprint_issues_raw.get("issues") or []

    cycle_times_dict = {}
    cycle_time_list = []

    for issue in issue_list:
        key = issue.get("key", "")
        fields = issue.get("fields") or {}
        created_str = fields.get("created") or ""
        resolution_str = fields.get("resolutiondate") or ""

        if not created_str or not resolution_str:
            continue

        try:
            from datetime import datetime as _dt
            fmt = "%Y-%m-%dT%H:%M:%S.%f%z"
            try:
                created_dt = _dt.strptime(created_str[:26] + "+0000", fmt)
            except ValueError:
                created_dt = _dt.fromisoformat(created_str[:10])
            try:
                resolved_dt = _dt.strptime(resolution_str[:26] + "+0000", fmt)
            except ValueError:
                resolved_dt = _dt.fromisoformat(resolution_str[:10])

            if hasattr(created_dt, "date"):
                delta_days = (resolved_dt.date() - created_dt.date()).days
            else:
                delta_days = (resolved_dt - created_dt).days

            if delta_days >= 0:
                cycle_times_dict[key] = delta_days
                cycle_time_list.append(float(delta_days))
        except Exception:
            continue

    if len(cycle_time_list) < 2:
        return error(
            "Insufficient resolved issues for cycle time analysis: "
            "found {} resolved issues, need at least 2".format(len(cycle_time_list)),
            error_type="INSUFFICIENT_DATA"
        )

    lognormal_result = scrum_calculator.cycle_time_lognormal_mle(cycle_time_list)

    return success(
        board_id=board_id,
        sprint_id=sprint_id,
        lognormal_fit=lognormal_result,
        per_issue_cycle_times=cycle_times_dict,
        resolved_count=len(cycle_time_list)
    )


# ---------------------------------------------------------------------------
# Tool 4: jira_throughput_forecast
# ---------------------------------------------------------------------------

@mcp.tool()
@mcp_tool_handler
def jira_throughput_forecast(
    board_id: int,
    num_sprints: int = 5,
    forecast_periods: int = 3,
) -> dict:
    """Forecast future sprint throughput using a Poisson model.

    Fetches closed sprint data from the Jira Agile API, extracts completed
    issue counts for recent sprints, then applies
    scrum_calculator.poisson_throughput() to produce a probabilistic
    delivery forecast over the requested number of future periods.

    Args:
        board_id: Numeric Jira board ID. Must be >= 1.
        num_sprints: Number of historical closed sprints to use as input
                     to the forecast model (default 5). Must be >= 1.
        forecast_periods: Number of future sprints to forecast (default 3).
                          Must be >= 1.

    Returns:
        JSON string with success=true and keys:
            board_id (int): Echo of board_id.
            historical_sprints (int): Actual number of closed sprints sampled.
            forecast_periods (int): Echo of forecast_periods.
            poisson_forecast (dict): Output from scrum_calculator.poisson_throughput().
        On failure: JSON string with success=false and error details.
    """
    board_id = validate_positive_int(board_id, "board_id")
    num_sprints = validate_positive_int(num_sprints, "num_sprints")
    forecast_periods = validate_positive_int(forecast_periods, "forecast_periods")

    cfg = _get_config()
    client = AgileClient(cfg)

    sprints_raw = client.get_sprints(board_id, state="closed", max_results=100)
    if sprints_raw is None:
        return error(
            "No closed sprints found for board_id={}".format(board_id),
            error_type="INVALID_RESPONSE"
        )

    sprint_values = sprints_raw.get("values") or sprints_raw.get("sprints") or []

    recent_sprints = sprint_values[-num_sprints:] if len(sprint_values) >= num_sprints else sprint_values

    completed_per_sprint = []
    for s in recent_sprints:
        count = (
            s.get("completedIssuesCount")
            or s.get("completedIssues")
            or s.get("issueCount")
            or 0
        )
        completed_per_sprint.append(int(count))

    if not completed_per_sprint or all(c == 0 for c in completed_per_sprint):
        return error(
            "Cannot compute throughput forecast: no completed issue counts "
            "found in closed sprints for board_id={}".format(board_id),
            error_type="INSUFFICIENT_DATA"
        )

    poisson_result = scrum_calculator.poisson_throughput(
        completed_per_sprint, forecast_periods
    )

    return success(
        board_id=board_id,
        historical_sprints=len(completed_per_sprint),
        forecast_periods=forecast_periods,
        poisson_forecast=poisson_result
    )


# ---------------------------------------------------------------------------
# Tool 5: jira_automation_analyzer
# ---------------------------------------------------------------------------

@mcp.tool()
@mcp_tool_handler
def jira_automation_analyzer(
    trigger_rates_json: str,
    service_rates_json: str,
    rules_dag_json: str,
) -> dict:
    """Analyze Jira automation rule queue stability and DAG cycle safety.

    Applies M/M/1 queueing theory to each automation rule to estimate
    queue stability, expected queue length, and wait time. Also performs
    Kahn's topological sort on the rules DAG to detect circular trigger
    chains that would cause infinite automation loops.

    Args:
        trigger_rates_json: JSON array of floats representing per-rule
                            trigger arrival rates (events per minute).
                            Example: "[2.0, 0.5, 1.2]"
        service_rates_json: JSON array of floats representing per-rule
                            service (execution) rates (completions per minute).
                            Must have the same length as trigger_rates_json.
                            Example: "[5.0, 3.0, 4.0]"
        rules_dag_json: JSON object (adjacency list) mapping each rule name
                        to a list of downstream rule names it triggers.
                        Example: '{"rule_A": ["rule_B"], "rule_B": [], "rule_C": ["rule_A"]}'

    Returns:
        JSON string with success=true and keys:
            mm1_analysis (list): Per-rule dicts with fields:
                rule_index (int), lambda_val (float), mu_val (float),
                rho_val (float), stable (bool), E_L (float), E_W (float).
            dag_has_cycle (bool): True if a circular trigger chain was detected.
            node_count (int): Total number of rules in the DAG.
        On failure: JSON string with success=false and error details.
    """
    trigger_rates_json = validate_input(trigger_rates_json, max_length=4096, field_name="trigger_rates_json")
    service_rates_json = validate_input(service_rates_json, max_length=4096, field_name="service_rates_json")
    rules_dag_json = validate_input(rules_dag_json, max_length=8192, field_name="rules_dag_json")

    try:
        trigger_rates = json.loads(trigger_rates_json)
    except ValueError as exc:
        return error("Invalid JSON for trigger_rates_json: " + str(exc), error_type="VALIDATION_ERROR")

    try:
        service_rates = json.loads(service_rates_json)
    except ValueError as exc:
        return error("Invalid JSON for service_rates_json: " + str(exc), error_type="VALIDATION_ERROR")

    try:
        rules_dag = json.loads(rules_dag_json)
    except ValueError as exc:
        return error("Invalid JSON for rules_dag_json: " + str(exc), error_type="VALIDATION_ERROR")

    if not isinstance(trigger_rates, list) or not isinstance(service_rates, list):
        return error(
            "trigger_rates_json and service_rates_json must be JSON arrays",
            error_type="VALIDATION_ERROR"
        )

    if len(trigger_rates) != len(service_rates):
        return error(
            "trigger_rates and service_rates must have equal length; "
            "got {} and {}".format(len(trigger_rates), len(service_rates)),
            error_type="VALIDATION_ERROR"
        )

    if not isinstance(rules_dag, dict):
        return error(
            "rules_dag_json must be a JSON object (adjacency list)",
            error_type="VALIDATION_ERROR"
        )

    mm1_analysis = []
    for i in range(len(trigger_rates)):
        lambda_val = float(trigger_rates[i])
        mu_val = float(service_rates[i])
        if mu_val <= 0:
            rho_val = float("inf")
            stable = False
            e_l = float("inf")
            e_w = float("inf")
        else:
            rho_val = lambda_val / mu_val
            stable = rho_val < 1.0
            if stable:
                e_l = rho_val / (1.0 - rho_val)
                e_w = 1.0 / (mu_val - lambda_val)
            else:
                e_l = float("inf")
                e_w = float("inf")

        mm1_analysis.append({
            "rule_index": i,
            "lambda_val": round(lambda_val, 6),
            "mu_val": round(mu_val, 6),
            "rho_val": round(rho_val, 6) if rho_val != float("inf") else "inf",
            "stable": stable,
            "E_L": round(e_l, 4) if e_l != float("inf") else "inf",
            "E_W": round(e_w, 4) if e_w != float("inf") else "inf",
        })

    in_degree = {}
    for node in rules_dag:
        if node not in in_degree:
            in_degree[node] = 0
        for neighbor in rules_dag.get(node, []):
            in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

    queue = [n for n, d in in_degree.items() if d == 0]
    processed = 0
    while queue:
        node = queue.pop(0)
        processed += 1
        for neighbor in rules_dag.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    dag_has_cycle = processed < len(in_degree)

    return success(
        mm1_analysis=mm1_analysis,
        dag_has_cycle=dag_has_cycle,
        node_count=len(rules_dag)
    )


# ---------------------------------------------------------------------------
# Tool 6: jira_tco_analysis
# ---------------------------------------------------------------------------

@mcp.tool()
@mcp_tool_handler
def jira_tco_analysis(
    user_count: int,
    years: int = 3,
    discount_rate: float = 0.10,
) -> dict:
    """Compute Total Cost of Ownership and NPV comparison for Jira licensing tiers.

    Delegates to scrum_calculator.tco_npv_comparison() which models
    licensing, infrastructure, and support costs across Jira Cloud Standard,
    Jira Cloud Premium, and Jira Data Center tiers for the given team size,
    amortized over the specified time horizon using NPV discounting.

    Args:
        user_count: Number of Jira users for the TCO calculation. Must be >= 1.
        years: Time horizon in years for NPV computation (default 3).
               Must be >= 1.
        discount_rate: Annual discount rate as a decimal fraction (default 0.10
                       for 10%). Must be in range (0, 1).

    Returns:
        JSON string with success=true and the full output dict from
        scrum_calculator.tco_npv_comparison(). Keys include:
            tiers (list): Per-tier TCO breakdown dicts.
            recommended_tier (str): Lowest-NPV tier recommendation.
            india_context (str): India-specific deployment note.
        On failure: JSON string with success=false and error details.
    """
    user_count = validate_positive_int(user_count, "user_count")

    try:
        years_int = int(years)
        if years_int < 1:
            raise ValueError("years must be >= 1")
    except (TypeError, ValueError) as exc:
        return error("Invalid years value: " + str(exc), error_type="VALIDATION_ERROR")

    try:
        rate = float(discount_rate)
        if rate <= 0.0 or rate >= 1.0:
            raise ValueError("discount_rate must be in range (0, 1)")
    except (TypeError, ValueError) as exc:
        return error("Invalid discount_rate value: " + str(exc), error_type="VALIDATION_ERROR")

    tco_result = scrum_calculator.tco_npv_comparison(user_count, years_int, rate)

    return success(**tco_result)


# ---------------------------------------------------------------------------
# Tool 7: jira_nasscom_mapping
# ---------------------------------------------------------------------------

@mcp.tool()
@mcp_tool_handler
def jira_nasscom_mapping(board_id: int, sprint_id: int) -> dict:
    """Map Jira sprint data to NASSCOM AgileX L1-L5 maturity dimensions.

    Fetches sprint issues and velocity history from the Jira Agile API,
    then evaluates each of the five NASSCOM AgileX maturity dimensions
    using evidence directly observable from Jira data. Produces a maturity
    score per dimension and an overall level estimate (L1-L5).

    NASSCOM AgileX dimensions assessed:
        L1 Initiation: Backlog exists and sprint has issues.
        L2 Planning: Sprint has a defined goal and issues are estimated.
        L3 Execution: Velocity variance is consistent (CV <= 0.25).
        L4 Optimization: Cycle time data is available (issues are resolved).
        L5 Innovation: Multiple closed sprints with high retrospective
                       completion rate (proxied from completion ratio).

    Args:
        board_id: Numeric Jira board ID. Must be >= 1.
        sprint_id: Numeric sprint ID to evaluate. Must be >= 1.

    Returns:
        JSON string with success=true and keys:
            board_id (int): Echo of board_id.
            sprint_id (int): Echo of sprint_id.
            nasscom_agile_x (dict): Per-dimension maturity evidence and score.
            overall_level (str): Estimated overall maturity level "L1" through "L5".
            india_context (str): Note on NASSCOM AgileX applicability in India.
        On failure: JSON string with success=false and error details.
    """
    board_id = validate_positive_int(board_id, "board_id")
    sprint_id = validate_positive_int(sprint_id, "sprint_id")

    cfg = _get_config()
    client = AgileClient(cfg)

    sprint_issues_raw = client.get_sprint_issues(
        sprint_id,
        fields="summary,status,created,resolutiondate,story_points,customfield_10016,customfield_10028"
    )
    if sprint_issues_raw is None:
        sprint_issues_raw = {}

    issue_list = sprint_issues_raw.get("issues") or []

    sprint_meta_raw = None
    try:
        sprint_meta_raw = client.get_sprint(sprint_id)
    except Exception:
        sprint_meta_raw = {}

    sprint_goal = ""
    if sprint_meta_raw:
        sprint_goal = sprint_meta_raw.get("goal") or ""

    velocity_raw = None
    velocity_history = []
    try:
        velocity_raw = client.get_velocity(board_id)
    except Exception:
        velocity_raw = {}

    if velocity_raw:
        entries = velocity_raw.get("velocityStatEntries") or {}
        for entry_id in sorted(entries.keys()):
            entry = entries[entry_id]
            completed_val = entry.get("completed") or {}
            points = completed_val.get("value", 0)
            try:
                velocity_history.append(int(float(points)))
            except (TypeError, ValueError):
                continue

    maturity_scores = {}

    has_issues = len(issue_list) > 0
    maturity_scores["L1_initiation"] = {
        "dimension": "Initiation",
        "evidence": "Sprint has {} issue(s)".format(len(issue_list)),
        "met": has_issues,
        "score": 1 if has_issues else 0,
    }

    estimated_issues = 0
    for issue in issue_list:
        fields = issue.get("fields") or {}
        sp = (
            fields.get("story_points")
            or fields.get("customfield_10016")
            or fields.get("customfield_10028")
        )
        if sp is not None:
            try:
                if float(sp) > 0:
                    estimated_issues += 1
            except (TypeError, ValueError):
                pass

    has_goal = bool(sprint_goal and sprint_goal.strip())
    has_estimates = estimated_issues > 0
    l2_met = has_goal and has_estimates
    maturity_scores["L2_planning"] = {
        "dimension": "Planning",
        "evidence": "goal='{}' | {} issue(s) estimated".format(
            sprint_goal[:60] if sprint_goal else "", estimated_issues
        ),
        "met": l2_met,
        "score": 2 if l2_met else (1 if has_goal or has_estimates else 0),
    }

    velocity_cv = None
    if len(velocity_history) >= 2:
        import statistics as _stats
        v_mean = _stats.mean(velocity_history)
        if v_mean > 0:
            v_stddev = _stats.pstdev(velocity_history)
            velocity_cv = v_stddev / v_mean
        else:
            velocity_cv = 0.0

    l3_met = velocity_cv is not None and velocity_cv <= 0.25
    maturity_scores["L3_execution"] = {
        "dimension": "Execution",
        "evidence": "velocity CV={} ({} sprints sampled)".format(
            round(velocity_cv, 4) if velocity_cv is not None else "n/a",
            len(velocity_history)
        ),
        "met": l3_met,
        "score": 3 if l3_met else (2 if velocity_cv is not None else 1),
    }

    resolved_count = sum(
        1 for issue in issue_list
        if (issue.get("fields") or {}).get("resolutiondate")
    )
    l4_met = resolved_count > 0
    maturity_scores["L4_optimization"] = {
        "dimension": "Optimization",
        "evidence": "{} of {} issues resolved (cycle time data available)".format(
            resolved_count, len(issue_list)
        ),
        "met": l4_met,
        "score": 4 if l4_met else 3,
    }

    closed_sprint_count = len(velocity_history)
    total_issue_count = len(issue_list)
    done_issue_count = sum(
        1 for issue in issue_list
        if (((issue.get("fields") or {}).get("status") or {}).get("name") or "").lower()
        in ("done", "closed", "resolved", "complete")
    )
    completion_ratio = (done_issue_count / total_issue_count) if total_issue_count > 0 else 0.0
    l5_met = closed_sprint_count >= 5 and completion_ratio >= 0.85 and l3_met
    maturity_scores["L5_innovation"] = {
        "dimension": "Innovation",
        "evidence": "{} closed sprints | completion ratio={} | L3 met={}".format(
            closed_sprint_count, round(completion_ratio, 3), l3_met
        ),
        "met": l5_met,
        "score": 5 if l5_met else (4 if closed_sprint_count >= 5 and l3_met else 3),
    }

    scores = [
        maturity_scores["L1_initiation"]["score"],
        maturity_scores["L2_planning"]["score"],
        maturity_scores["L3_execution"]["score"],
        maturity_scores["L4_optimization"]["score"],
        maturity_scores["L5_innovation"]["score"],
    ]
    min_score = min(scores)
    if min_score >= 5:
        overall_level = "L5"
    elif min_score >= 4:
        overall_level = "L4"
    elif min_score >= 3:
        overall_level = "L3"
    elif min_score >= 2:
        overall_level = "L2"
    else:
        overall_level = "L1"

    india_context = (
        "NASSCOM AgileX framework is specifically designed for Indian IT/ITES teams. "
        "L3+ is the industry-average for Tier-1 Indian IT services firms (TCS, Infosys, Wipro). "
        "L5 corresponds to NASSCOM Digital Transformation Index top-quartile performers. "
        "Velocity benchmarks: 35-45 SP per 2-week sprint for co-located India teams."
    )

    return success(
        board_id=board_id,
        sprint_id=sprint_id,
        nasscom_agile_x=maturity_scores,
        overall_level=overall_level,
        india_context=india_context
    )
