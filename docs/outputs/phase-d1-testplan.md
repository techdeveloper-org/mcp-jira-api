<!--
IEEE 829 TEST STRATEGY
Generated: 2026-05-28
Phase C Gate: APPROVED (NLI=1.0, FactScore=0.957)
Project: mcp-jira-api -- scrum_calculator.py new functions + server.py tool wrappers
-->

# IEEE 829 TEST STRATEGY
**Date:** 2026-05-28
**Phase C Gate:** APPROVED (NLI=1.0, FactScore=0.957)
**Prepared by:** test-management-agent
**Existing Baseline:** 143 tests passing (test_scrum_calculator.py + test_server_scrum_tools.py + test_agile_client.py + test_integration_scrum.py)

---

## 1. Scope

### 1.1 Items Under Test

| Category | Count | File | Description |
|----------|-------|------|-------------|
| New pure functions | 16 | scrum_calculator.py (lines 533+) | bootstrap_bca_ci, ahp_score, tuckman_markov, spotify_health_check, edmondson_ps_scale, scrum_of_scrums_overhead, cognitive_load_index, attrition_ramp, ist_capacity_correction, little_law_analysis, cycle_time_lognormal_mle, poisson_throughput, pert_estimate, tco_npv_comparison, burndown_metrics, multi_sprint_holiday_forecast |
| New server tool stubs | 16 | server.py | 9 from Phase B.1 + 7 from Phase B.2 (full list in Section 5.3) |
| Upgraded existing tools | 4 | server.py | jira_refine_backlog, jira_sprint_review, jira_team_health, jira_get_velocity |

### 1.2 Items Not Under Test (Excluded)

- Existing 9 tools in test_server_scrum_tools.py (already passing, regression only)
- agile_client.py HTTP layer (covered by test_agile_client.py)
- base/response.py MCPResponse builder (covered by existing tests)
- input_validator.py and rate_limiter.py (no changes)

### 1.3 Test Environment

- Python 3.8+ (stdlib only for unit tests: unittest.TestCase, math, statistics, random)
- No network access for unit tests; unittest.mock.patch for integration tests
- Windows platform: ASCII-only source files (cp1252 safe)
- Float tolerance: atol=0.001 for all floating-point assertions (pytest.approx or abs() check)

---

## 2. Risk Matrix

### 2.1 HIGH RISK -- Adversarial Testing Required

| Function | Risk Factors | Adversarial Scenarios |
|----------|-------------|----------------------|
| bootstrap_bca_ci | Non-deterministic (random.choices), BCa quantile inversion can diverge, zero-variance path bypasses bootstrap | empty list, single element, all-same values, B=1 edge |
| ahp_score | Power iteration may not converge on near-singular matrix, CR=0.10 exact boundary is classification boundary, non-square input is silently malformed | 1x1 trivial, 3x3 consistent (CR<0.10), 3x3 inconsistent (CR>0.10), non-square (row != n), empty matrix |
| tuckman_markov | len<3 triggers Forming regardless of CV, all-same velocities produce CV=0 (Performing), slope sign determines Norming vs Performing at CV boundary | len=1 error, len=2 Forming, all-same (CV=0), high-variance chaotic velocity |
| edmondson_ps_scale | Reverse coding at positions 0,2,4 must be exact (8-score), wrong-length input must error, all-same scores affect alpha denominator path | len!=7, all 7s (reversed positions), all 1s, mixed edge boundary |
| burndown_metrics | total_points=0 handled separately (returns zeros), svi exactly 0.9 and 0.7 are classification boundaries, empty completed_by_day produces n=0 | total_points=0, completed_by_day=[], svi=0.9 boundary, svi=0.7 boundary |
| little_law_analysis | Division by lambda_throughput=0 must yield float("inf"), empty arrivals or departures must error, negative WIP is mathematically valid | empty arrivals, empty departures, all-zero departures (lambda=0), negative WIP |

### 2.2 MEDIUM RISK -- Standard + Boundary Testing

| Function | Risk Factors | Key Boundaries |
|----------|-------------|----------------|
| spotify_health_check | Exactly 11 required dimensions -- missing any one must error; Wilcoxon Z undefined for n_nz=0; all-same scores make prev_scores delta=0 | missing dimension, all zeros, all 2s, prev_scores provided vs None |
| cognitive_load_index | Empty dicts produce CL_team=0, CLI exactly 1.0 is the overloaded boundary, no common domains means zero load | empty both dicts, CLI=1.0 boundary, single shared domain |
| attrition_ramp | months<=0 must error, p_max>1.0 must error, months=tau gives P_t=0.632*p_max (e-folding point) | months=0 error, months=tau canonical, p_max=1.0 valid, p_max=1.1 error |
| scrum_of_scrums_overhead | teams=1 must error, c>=p must error, c<p valid, n_optimal formula is continuous | teams=1 error, c=p error, teams=2 minimum, n_optimal check |
| cycle_time_lognormal_mle | Zero value in list must error (log(0) undefined), single value must error (variance undefined), all-same gives sigma=0 | zero value, len=1, all-same, [1,2,4,8] P50/P85 check |
| poisson_throughput | Empty list must error, all-zero list gives lambda_hat=0 (valid), forecast_periods=0 gives empty forecast list | empty, all zeros, forecast_periods=0 |
| pert_estimate | optimistic>pessimistic must error, all-same (O=M=P) gives sigma=0, O=1,M=4,P=7 canonical PERT | O>M error, M>P error, O=M=P, canonical (1,4,7) |
| tco_npv_comparison | user_count=0 causes jira_cf_per_year=0 (valid), years=1 tests single-period NPV, discount_rate=0 avoids discounting | user_count=0, years=1, discount_rate=0, recommendation switch point |
| ist_capacity_correction | No error cases (pure formula), overlap_hours=0 gives factor=0, overlap_hours=8 gives factor=1.0 | overlap=0, overlap=4 (canonical), overlap=8 (full day) |
| multi_sprint_holiday_forecast | num_sprints=0 must error (now num_sprints<1), invalid date must error, holiday on sprint boundary must be counted | num_sprints=0 error, invalid date, holiday exactly on start, holiday exactly on end, holiday outside window |

### 2.3 LOW RISK -- Smoke Tests Only

| Category | Rationale |
|----------|-----------|
| All 16 new server.py tool wrappers | Thin delegation wrappers; business logic in scrum_calculator.py or agile_client.py; only happy/invalid/exception paths needed |
| jira_tco_analysis, jira_pert_estimate, jira_ist_capacity | Pure delegation to calculator; envelope format is the only new risk |
| Upgraded tool backward compatibility | Key check: new math output keys added alongside existing keys; no key removal |

---

## 3. Coverage Requirements

| Gate | Metric | Target | Enforcement |
|------|--------|--------|-------------|
| Unit tests (scrum_calculator new functions) | Line coverage | 100% | HARD GATE -- blocks D.2 |
| Integration tests (new server tools) | DRE (Defect Rejection Effectiveness) | 1.0 | HARD GATE |
| Existing test baseline | All 143 existing tests pass | 100% green | HARD GATE |
| Float assertions | Absolute tolerance | atol=0.001 | All floating-point comparisons use pytest.approx(abs=0.001) or abs(result-expected)<0.001 |
| Mock isolation | No real network calls | Zero HTTP in unit tests | Verified by absence of urllib/requests imports in test_scrum_calculator_new.py |

---

## 4. Directives to unit-testing-specialist

### 4.1 File to Create

```
tests/test_scrum_calculator_new.py
```

### 4.2 Framework and Tools

- Framework: `unittest.TestCase` (match existing tests/test_scrum_calculator.py style)
- Import style: `import pytest` at top; use `pytest.approx(expected, abs=0.001)` for floats
- Mock requirement: None. All 16 functions are pure -- no network I/O, no file I/O
- Seeding: Do NOT seed random in tests for bootstrap_bca_ci. Test structural invariants (CI contains mean, CI is ordered) rather than exact values
- ASCII-only: No non-ASCII characters in source file (cp1252 safe for Windows)
- Path setup pattern (match existing):
  ```python
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
  from scrum_calculator import (
      bootstrap_bca_ci, ahp_score, tuckman_markov, spotify_health_check,
      edmondson_ps_scale, scrum_of_scrums_overhead, cognitive_load_index,
      attrition_ramp, ist_capacity_correction, little_law_analysis,
      cycle_time_lognormal_mle, poisson_throughput, pert_estimate,
      tco_npv_comparison, burndown_metrics, multi_sprint_holiday_forecast,
  )
  ```

### 4.3 Required Test Cases per Function (Minimum)

#### 4.3.1 bootstrap_bca_ci

Coverage target: 100% of lines in bootstrap_bca_ci and _normal_cdf and _normal_inv_cdf helpers.

| Test ID | Input | Expected Outcome | Notes |
|---------|-------|-----------------|-------|
| BCA-01 | data=[] | result["error"] contains substring (error key present) | Empty list guard |
| BCA-02 | data=[5.0] | result["error"] present | Single element guard (need >= 2) |
| BCA-03 | data=[10.0, 10.0, 10.0] | result["lower"]==result["upper"]==result["point_estimate"]==10.0; result["B"]==0; "note" key present | Zero variance path |
| BCA-04 | data=[20,25,30,22,28]; B=2000 | result["lower"] <= mean(data) <= result["upper"]; result["lower"] < result["upper"]; result["confidence"]==0.95; result["B"]==2000 | CI must contain the sample mean; run B=2000 for convergence |
| BCA-05 | data=[1,100]; confidence=0.90; B=1000 | result["lower"] < result["upper"]; result["confidence"]==0.90 | Non-default confidence |
| BCA-06 | data=[10,20,30,40,50]; B=500 | result["point_estimate"] == pytest.approx(30.0, abs=0.001) | Point estimate is sample mean |
| BCA-07 | data=[5,5,5,5,10] (near-zero variance, not all-same) | result["lower"] <= result["upper"] (no crash) | Near-zero but non-zero variance |

#### 4.3.2 ahp_score

Coverage target: 100% of lines in ahp_score.

| Test ID | Input | Expected Outcome | Notes |
|---------|-------|-----------------|-------|
| AHP-01 | criteria_matrix=[] | result["error"] present | Empty matrix guard |
| AHP-02 | criteria_matrix=[[1.0]] | result["weights"]==[1.0]; result["consistent"]==True; result["CR"]==0.0; result["n"]==1 | 1x1 trivial case |
| AHP-03 | non-square: [[1,2],[3,4,5]] | result["error"] present | Row length != n guard |
| AHP-04 | Consistent 3x3: [[1,3,5],[1/3,1,3],[1/5,1/3,1]] | sum(result["weights"]) == pytest.approx(1.0, abs=0.001); result["consistent"]==True; result["CR"] < 0.10 | Standard AHP example |
| AHP-05 | Inconsistent 3x3: [[1,9,9],[1/9,1,9],[1/9,1/9,1]] | result["consistent"]==False; result["CR"] > 0.10 | High CR inconsistent matrix |
| AHP-06 | Consistent 3x3 (AHP-04) | result["CR"] == pytest.approx(result["CI"] / 0.58, abs=0.001) | RI table lookup n=3 is 0.58 |
| AHP-07 | 1x1 | result["lambda_max"] == pytest.approx(1.0, abs=0.001) | Trivial eigenvalue |

#### 4.3.3 tuckman_markov

Coverage target: 100% of lines in tuckman_markov.

| Test ID | Input | Expected Outcome | Notes |
|---------|-------|-----------------|-------|
| TM-01 | velocity_history=[] | result["error"] present | Empty list guard |
| TM-02 | velocity_history=[40] | result["error"] present | Single element guard |
| TM-03 | velocity_history=[40, 42] | result["current_stage"]=="Forming" | len=2 triggers Forming (n<3) |
| TM-04 | velocity_history=[40,42,38,41,40,39] | result["current_stage"]=="Performing" OR "Norming"; result["cv"] < 0.10 | Low CV stable velocities |
| TM-05 | velocity_history=[10,30,5,25,15,40] | result["current_stage"] in {"Forming","Storming"} | High variance (CV>0.25) |
| TM-06 | velocity_history=[40,40,40,40,40] (all-same) | result["cv"] == pytest.approx(0.0, abs=0.001); result["current_stage"]=="Performing" | CV=0 special case |
| TM-07 | any valid input | sum(result["stage_probabilities"].values()) == pytest.approx(1.0, abs=0.01) | Probabilities sum to 1 |
| TM-08 | any valid input | result["nasscom_agile_x_level"] in {"L1","L2","L3","L4","L5"} | Valid NASSCOM level |
| TM-09 | velocity_history=[10,40,10,40,10,40,10,40] | result["current_stage"] in {"Storming","Forming"} | Alternating high CV |

#### 4.3.4 spotify_health_check

Coverage target: 100% of lines in spotify_health_check.

_SPOTIFY_DIMENSIONS = [easy_to_release, suitable_process, tech_quality, value, speed, mission, fun, learning, support, pawns_or_players, team_spirit] (11 dimensions)

| Test ID | Input | Expected Outcome | Notes |
|---------|-------|-----------------|-------|
| SHC-01 | Missing one dimension (10 of 11) | result["error"] contains "Missing" | Missing dimension guard |
| SHC-02 | All 11 dimensions, each=[0,0,0] (all zeros) | result["THS"]==0.0; result["health_color"]=="Red" | All-zero minimum |
| SHC-03 | All 11 dimensions, each=[2,2,2] (all twos) | result["THS"]==2.0; result["health_color"]=="Green" | All-two maximum |
| SHC-04 | All 11 dimensions, each=[1] | result["THS"]==pytest.approx(1.0, abs=0.001); result["health_color"]=="Amber" | Amber boundary (THS=1.0, between 0.75 and 1.5) |
| SHC-05 | All 11 dims=[2] + prev_scores={all dim: 1.5} | result["wilcoxon_Z"] is not None; result["delta_vs_previous"] == pytest.approx(0.5, abs=0.001) | With prev_scores, Wilcoxon Z computed |
| SHC-06 | All 11 dims=[1] + prev_scores={all dim: 1.0} | result["wilcoxon_Z"] is None or result["wilcoxon_Z"]==0.0 | Zero diffs gives n_nz=0 |
| SHC-07 | Valid input; no prev_scores | result["wilcoxon_Z"] is None; result["delta_vs_previous"] is None | No prev_scores case |

#### 4.3.5 edmondson_ps_scale

Reverse-coding: positions 0, 2, 4 get (8 - score). Positions 1, 3, 5, 6 unchanged.
PS_score = mean of 7 processed values.

| Test ID | Input | Expected Outcome | Notes |
|---------|-------|-----------------|-------|
| EPS-01 | item_scores=[] (empty) | result["error"] present | Wrong length |
| EPS-02 | item_scores=[1,2,3,4,5,6,7,8] (8 items) | result["error"] present | len!=7 guard |
| EPS-03 | item_scores=[1,1,1,1,1,1,1] | All positions 0,2,4 become 8-1=7; positions 1,3,5,6 stay 1; PS_score=mean([7,1,7,1,7,1,1])=25/7=3.5714; result["PS_score"]==pytest.approx(25/7, abs=0.001); result["interpretation"]=="Moderate" | All-1 reverse coding check |
| EPS-04 | item_scores=[7,7,7,7,7,7,7] | Positions 0,2,4 become 8-7=1; others stay 7; PS_score=mean([1,7,1,7,1,7,7])=31/7=4.4286; result["PS_score"]==pytest.approx(31/7, abs=0.001) | All-7 |
| EPS-05 | item_scores=[4,4,4,4,4,4,4] | Positions 0,2,4 become 4; all same; PS_score=4.0 | Symmetric middle value |
| EPS-06 | item_scores=[1,7,1,7,1,7,7] | result["PS_score"]==pytest.approx(25/7, abs=0.001) | Mixed |
| EPS-07 | item_scores=[0,4,4,4,4,4,4] | result["error"] present | Score out of range [1,7] |
| EPS-08 | item_scores=[4,4,4,4,4,4,4] | result["reverse_coded_positions"]==[0,2,4] | Verify metadata |

#### 4.3.6 scrum_of_scrums_overhead

Formula: T_n = teams*p - c*teams*(teams-1)/2; n_optimal = p/c + 0.5

| Test ID | Input | Expected Outcome | Notes |
|---------|-------|-----------------|-------|
| SOS-01 | teams=1, p=10, c=2 | result["error"] present | teams < 2 guard |
| SOS-02 | teams=2, p=10, c=10 | result["error"] present | c >= p guard |
| SOS-03 | teams=2, p=10, c=2 | result["T_n"]==pytest.approx(20-2*2*1/2, abs=0.001)==pytest.approx(18.0, abs=0.001); result["n_optimal"]==pytest.approx(5.5, abs=0.001) | T_n=teams*p - c*teams*(teams-1)/2 = 2*10 - 2*2*1/2 = 20-2=18 |
| SOS-04 | teams=4, p=10, c=2 | result["T_n"]==pytest.approx(4*10 - 2*4*3/2, abs=0.001)==pytest.approx(28.0, abs=0.001); result["n_optimal"]==pytest.approx(5.5, abs=0.001) | n_optimal = 10/2 + 0.5 = 5.5 |
| SOS-05 | teams=4, p=10, c=2 | result["overhead_ratio"] == pytest.approx(12.0/40.0, abs=0.001) | overhead_ratio = c*teams*(teams-1)/2 / (teams*p) |
| SOS-06 | p=0, teams=2, c=1 | result["error"] present | p <= 0 guard |

#### 4.3.7 cognitive_load_index

| Test ID | Input | Expected Outcome | Notes |
|---------|-------|-----------------|-------|
| CLI-01 | complexity={}, responsibility={} | result["CL_team"]==0.0; result["CLI"]==0.0; result["overloaded"]==False | Empty dicts |
| CLI-02 | complexity={"auth": 5.0}, responsibility={"auth": 2.0} | result["CL_team"]==pytest.approx(10.0, abs=0.001); result["CLI"]==pytest.approx(1.0, abs=0.001); result["overloaded"]==False | CLI=1.0 is not overloaded (requires CLI>1.0) |
| CLI-03 | complexity={"auth": 5.0}, responsibility={"auth": 2.1} | result["overloaded"]==True; result["CLI"] > 1.0 | CLI just above 1.0 |
| CLI-04 | complexity={"a":3,"b":4}, responsibility={"b":2,"c":1} | common_domains={"b"}; result["CL_team"]==pytest.approx(8.0, abs=0.001) | Non-overlapping domains excluded |
| CLI-05 | complexity={"a":1}, responsibility={"b":1} | result["CL_team"]==0.0 | No common domains |
| CLI-06 | valid input | result["topology_efficiency"]["X_as_Service"]==pytest.approx(0.90, abs=0.001) | Metadata present |

#### 4.3.8 attrition_ramp

Formula: P_t = p_max * (1 - exp(-months/tau))

| Test ID | Input | Expected Outcome | Notes |
|---------|-------|-----------------|-------|
| ATT-01 | months=0, p_max=0.3 | result["error"] present | months <= 0 guard |
| ATT-02 | months=6, p_max=0.0 | result["error"] present | p_max <= 0 guard |
| ATT-03 | months=6, p_max=1.1 | result["error"] present | p_max > 1 guard |
| ATT-04 | months=6, p_max=0.3, tau=6 | result["attrition_probability"]==pytest.approx(0.3*(1-math.exp(-1)), abs=0.001) (~0.1896) | E-folding point: t=tau gives P_t = p_max*(1-1/e) |
| ATT-05 | months=0.001, p_max=1.0, tau=6 | result["attrition_probability"] < 0.01 | Very small t gives near-zero attrition |
| ATT-06 | months=100, p_max=0.5, tau=6 | result["attrition_probability"] == pytest.approx(0.5, abs=0.01) | Large t asymptotes to p_max |
| ATT-07 | months=6, p_max=1.0 | result["effective_velocity_factor"] + result["attrition_probability"] == pytest.approx(1.0, abs=0.001) | Invariant: factor + prob = 1 |

#### 4.3.9 ist_capacity_correction

Formula: correction_factor = overlap_hours/8.0; effective_capacity = nominal * correction_factor

| Test ID | Input | Expected Outcome | Notes |
|---------|-------|-----------------|-------|
| IST-01 | nominal=100, overlap_hours=4 | result["correction_factor"]==pytest.approx(0.5, abs=0.001); result["effective_capacity"]==pytest.approx(50.0, abs=0.001) | Canonical 4-hour overlap |
| IST-02 | nominal=80, overlap_hours=8 | result["correction_factor"]==pytest.approx(1.0, abs=0.001); result["effective_capacity"]==pytest.approx(80.0, abs=0.001) | Full day overlap |
| IST-03 | nominal=100, overlap_hours=0 | result["correction_factor"]==0.0; result["effective_capacity"]==0.0 | Zero overlap |
| IST-04 | nominal=100, overlap_hours=4 | result["q1_seasonal_buffer_factor"]==pytest.approx(1.15, abs=0.001) | Q1 buffer constant always present |
| IST-05 | nominal=50, overlap_hours=4 | result["nominal"]==50.0; result["overlap_hours"]==4.0 | Input values echoed |

#### 4.3.10 little_law_analysis

Formula: L_wip = arrivals_total - departures_total; lambda = departures_total / periods; W = L_wip / lambda (inf if lambda=0)

| Test ID | Input | Expected Outcome | Notes |
|---------|-------|-----------------|-------|
| LL-01 | arrivals=[] | result["error"] present | Empty arrivals guard |
| LL-02 | departures=[] | result["error"] present | Empty departures guard |
| LL-03 | arrivals=[{"date":"2026-01-01","count":5}], departures=[{"date":"2026-01-01","count":0}] | result["lambda_throughput"]==0.0; result["W_cycle_time_days"]==float("inf") | Zero throughput |
| LL-04 | arrivals=[{"date":"2026-01-01","count":10}], departures=[{"date":"2026-01-01","count":5}] | result["L_wip"]==5.0; result["lambda_throughput"]==5.0; result["W_cycle_time_days"]==pytest.approx(1.0, abs=0.001) | Normal case |
| LL-05 | arrivals=[{"date":"d1","count":5},{"date":"d2","count":3}], departures=[{"date":"d1","count":4},{"date":"d2","count":2}] | result["L_wip"]==2.0; result["lambda_throughput"]==pytest.approx(3.0, abs=0.001); periods=2 | Multi-period |
| LL-06 | all-zero departures | result["W_cycle_time_days"] is equivalent to float("inf") | Verify inf handling in JSON: "Infinity" or float |
| LL-07 | departures>arrivals | result["L_wip"] < 0 (negative WIP is mathematically valid) | Negative WIP |

#### 4.3.11 cycle_time_lognormal_mle

MLE: mu_hat = mean(log(t)); sigma_hat = sqrt(sample_variance(log(t))); P50 = exp(mu_hat)

| Test ID | Input | Expected Outcome | Notes |
|---------|-------|-----------------|-------|
| CTL-01 | cycle_times=[0.0, 2.0] | result["error"] present | Zero value (log(0) undefined) |
| CTL-02 | cycle_times=[-1.0, 2.0] | result["error"] present | Negative value (must be > 0) |
| CTL-03 | cycle_times=[4.0] | result["error"] present | Single value (variance undefined) |
| CTL-04 | cycle_times=[1.0, math.e] | mu_hat = mean([0, 1]) = 0.5; P50 = exp(0.5) ~= 1.6487; result["P50_days"] == pytest.approx(math.exp(0.5), abs=0.001) | Computable manual case |
| CTL-05 | cycle_times=[1,2,4,8] | result["P85_days"] > result["P50_days"]; result["P95_days"] > result["P85_days"] | Percentile ordering invariant |
| CTL-06 | cycle_times=[5,5,5,5] | result["sigma_hat"] == pytest.approx(0.0, abs=0.001) (all same gives zero variance in log space) | All-same yields sigma=0 |
| CTL-07 | cycle_times=[1,2,4,8] | result["sample_size"]==4 | Sample size echoed |

#### 4.3.12 poisson_throughput

Algorithm: lambda_hat = mean(completed); Wilson-Hilferty CI; forecast list

| Test ID | Input | Expected Outcome | Notes |
|---------|-------|-----------------|-------|
| PT-01 | completed=[] | result["error"] present | Empty list guard |
| PT-02 | completed=[-1, 3] | result["error"] present | Negative value guard |
| PT-03 | completed=[0,0,0] | result["lambda_hat"]==0.0; result["lambda_ci_lower"]==0.0; len(result["forecast"])==3 | All-zero (valid Poisson with lambda=0) |
| PT-04 | completed=[5,6,7,5,6] | result["lambda_hat"]==pytest.approx(5.8, abs=0.001); result["lambda_ci_lower"] < result["lambda_hat"] < result["lambda_ci_upper"] | CI straddles lambda_hat |
| PT-05 | completed=[5], forecast_periods=0 | result["forecast"]==[] | forecast_periods=0 yields empty list |
| PT-06 | completed=[5,6,7,5,6], forecast_periods=2 | len(result["forecast"])==2; result["forecast"][0]["period"]==1; result["forecast"][1]["period"]==2 | Forecast list structure |

#### 4.3.13 pert_estimate

Formula: mu = (O + 4M + P)/6; sigma = (P-O)/6; CI_90 = mu +/- 1.645*sigma

| Test ID | Input | Expected Outcome | Notes |
|---------|-------|-----------------|-------|
| PERT-01 | O=5, M=3, P=10 (O > M) | result["error"] present | optimistic > most_likely guard |
| PERT-02 | O=1, M=4, P=3 (M > P) | result["error"] present | most_likely > pessimistic guard |
| PERT-03 | O=M=P=5 | result["mu_days"]==5.0; result["sigma_days"]==0.0; result["ci_90_lower"]==5.0; result["ci_90_upper"]==5.0 | All-same gives sigma=0 |
| PERT-04 | O=1, M=4, P=7 | mu=(1+16+7)/6=4.0; sigma=(7-1)/6=1.0; ci_lower=4-1.645=2.355; ci_upper=4+1.645=5.645; result["mu_days"]==pytest.approx(4.0, abs=0.001); result["sigma_days"]==pytest.approx(1.0, abs=0.001); result["ci_90_lower"]==pytest.approx(2.355, abs=0.001) | Canonical PERT example |
| PERT-05 | O=0, M=0, P=0 | result["mu_days"]==0.0; result["sigma_days"]==0.0 | Zero inputs |
| PERT-06 | O=1, M=1, P=7 | result["ci_90_upper"] > result["mu_days"] | Upper > mean for non-zero sigma |

#### 4.3.14 tco_npv_comparison

Jira annual per user = 685*12*1.18; Azure annual per user = 430*12*1.18; Azure fixed = 200000

| Test ID | Input | Expected Outcome | Notes |
|---------|-------|-----------------|-------|
| TCO-01 | user_count=1, years=3, discount_rate=0.10 | result["jira_premium_3yr_npv_inr"] > 0; result["azure_devops_3yr_npv_inr"] > 0; result["recommendation"]=="Azure DevOps" (1 user, fixed overhead dominates) | Small user count |
| TCO-02 | user_count=1000, years=3, discount_rate=0.10 | result["recommendation"]=="Jira Premium" (large user count, Jira amortizes) | Large user count |
| TCO-03 | user_count=1, years=1, discount_rate=0.0 | result["jira_premium_3yr_npv_inr"]==pytest.approx(685*12*1.18*1, abs=1.0) | years=1, no discounting |
| TCO-04 | user_count at break_even | result["break_even_users"] is int; result["break_even_users"] > 0 | Break-even is a positive integer |
| TCO-05 | user_count=0 | result["jira_premium_3yr_npv_inr"]==0.0 (no user cost); NPV still computed without error; recommendation is "Azure DevOps" | user_count=0 (Azure fixed overhead) |

#### 4.3.15 burndown_metrics

Formula: ideal_line[i] = total - total*(i/n); actual_line = [total] + [total - cumulative[i]]; svi = completed[-1] / total

| Test ID | Input | Expected Outcome | Notes |
|---------|-------|-----------------|-------|
| BDM-01 | total_points=0, completed_by_day=[5,10,15] | result["svi"]==0.0; result["sprint_health"]=="On Track"; result["ideal_line"]==[0.0]*4 | total_points=0 handled separately |
| BDM-02 | total_points=20, completed_by_day=[5,10,15] | ideal_line has n+1=4 entries; result["ideal_line"][0]==20.0; result["ideal_line"][-1]==0.0 (approximately, but ideal[n]=0 for last) | Wait: ideal_line[-1] = total*(1 - n/n) = total*(1-1) = 0. Verify. |
| BDM-03 | total_points=20, completed_by_day=[18,18,18] | result["svi"]==pytest.approx(18/20, abs=0.001)==0.9; result["sprint_health"]=="On Track" | svi=0.9 exact boundary |
| BDM-04 | total_points=20, completed_by_day=[14,14,14] | result["svi"]==pytest.approx(14/20, abs=0.001)==0.7; result["sprint_health"]=="At Risk" | svi=0.7 exact boundary |
| BDM-05 | total_points=20, completed_by_day=[10,10,10] | result["svi"]==0.5; result["sprint_health"]=="Off Track" | Below 0.7 |
| BDM-06 | total_points=20, completed_by_day=[5,10,15] | len(result["actual_line"])==4; len(result["ideal_line"])==4 (n+1) | List lengths = n+1 |
| BDM-07 | total_points=20, completed_by_day=[5,10,15] | result["actual_line"][0]==20.0 (day 0 = total_points); result["actual_line"][-1]==5.0 (total-15) | Actual line starts at total |

#### 4.3.16 multi_sprint_holiday_forecast

| Test ID | Input | Expected Outcome | Notes |
|---------|-------|-----------------|-------|
| MSHF-01 | sprint_start="2026-01-01", sprint_duration_days=14, num_sprints=0 | result["error"] present | num_sprints < 1 guard |
| MSHF-02 | sprint_start="not-a-date", sprint_duration_days=14, num_sprints=1 | result["error"] present | Invalid date guard |
| MSHF-03 | sprint_start="2026-01-20", sprint_duration_days=14, num_sprints=1 | result["sprints"][0]["holiday_count"] >= 1 (Republic Day 2026-01-26 in window) | Holiday in window detected |
| MSHF-04 | sprint_start="2026-09-01", sprint_duration_days=14, num_sprints=1 | result["sprints"][0]["holiday_count"] == 0 | No holidays in Sept 1-14 |
| MSHF-05 | sprint_start="2026-01-26", sprint_duration_days=1, num_sprints=1 | result["sprints"][0]["holiday_count"] == 1 (Republic Day on exact start date) | Holiday on first day of single-day sprint |
| MSHF-06 | sprint_start="2026-01-20", sprint_duration_days=14, num_sprints=2 | len(result["sprints"])==2; result["sprints"][0]["sprint_number"]==1; result["sprints"][1]["sprint_number"]==2 | Multi-sprint structure |
| MSHF-07 | sprint_start="2026-01-20", sprint_duration_days=14, num_sprints=1 | result["sprints"][0]["effective_days"] == 14 - result["sprints"][0]["holiday_count"] | Effective days formula |
| MSHF-08 | sprint_start="2025-01-01", sprint_duration_days=14, num_sprints=1 | result["sprints"][0]["holiday_count"] >= 1 (New Year 2025-01-01) | 2025 holiday data accessible |

---

## 5. Directives to integration-testing-engineer

### 5.1 File to Create

```
tests/test_tools_integration_new.py
```

### 5.2 Framework and Mock Pattern

- Framework: `unittest.TestCase` (match existing tests/test_server_scrum_tools.py)
- Async: All server tool functions use `asyncio.run()` for invocation
- Mock: `unittest.mock.patch('urllib.request.urlopen')` for ALL HTTP calls (same as test_server_scrum_tools.py)
- Env vars: Use `tests.conftest.fixture_loader` and `jira_env` fixture pattern (see conftest.py)
- Import pattern (match existing):
  ```python
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
  ```

**Response envelope contract (from base/response.py):**
Every tool response is a JSON string. On success: `{"success": true, ...data keys...}`.
On error (from @mcp_tool_handler decorator): `{"success": false, "error": "...", ...}`.
Parse with `json.loads(result)` and assert `data["success"]` is True/False.

**Mock builder pattern (copy exactly from test_server_scrum_tools.py lines 58-80):**
```python
def _make_urlopen_response(data):
    encoded = json.dumps(data).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = encoded
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp
```

### 5.3 New Server Tools -- 3 Paths Each

The 16 new tools are split into two groups based on their implementation. For each tool, test:
- **(a) Happy path**: mock returns valid data; assert `success==True` and expected data keys present
- **(b) Invalid input**: pass bad params (negative IDs, None, empty string); assert `success==False` and `"error"` key present
- **(c) API exception**: mock raises `Exception("network error")`; assert `success==False` and `"error"` key present

#### Group 1: Pure calculator delegation tools (no AgileClient call)

These tools call scrum_calculator functions directly. Mock env vars but no HTTP mock needed for happy path.

| Tool | Required Mock | Key Happy Path Assertions |
|------|---------------|--------------------------|
| jira_tco_analysis | JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN env vars | success==True; "jira_premium_3yr_npv_inr" in data; "recommendation" in data |
| jira_pert_estimate | Env vars | success==True; "mu_days" in data; "sigma_days" in data |
| jira_ist_capacity | Env vars | success==True; "effective_capacity" in data; "correction_factor" in data |
| jira_burndown_chart | Env vars + mock agile_client.get_burndown_data OR calculated from params | success==True; "ideal_line" in data; "svi" in data |
| jira_bootstrap_ci | Env vars | success==True; "lower" in data; "upper" in data |
| jira_ahp_prioritize | Env vars | success==True; "weights" in data; "consistent" in data |
| jira_tuckman_velocity | Env vars + mock for sprint velocity fetch OR inline velocity list | success==True; "current_stage" in data |
| jira_team_psych_safety | Env vars | success==True; "PS_score" in data |
| jira_cognitive_load | Env vars | success==True; "CLI" in data; "overloaded" in data |

#### Group 2: AgileClient-delegating tools (HTTP mock required)

| Tool | Mock Target | Key Happy Path Assertions |
|------|-------------|--------------------------|
| jira_cycle_time_analysis | agile_client sprint issues endpoint | success==True; "P50_days" in data |
| jira_poisson_forecast | agile_client sprint history endpoint | success==True; "lambda_hat" in data; "forecast" in data |
| jira_scrum_of_scrums | Env vars (formula only) | success==True; "T_n" in data; "n_optimal" in data |
| jira_attrition_forecast | Env vars (formula only) | success==True; "attrition_probability" in data |
| jira_holiday_sprint_plan | Env vars + sprint_start param | success==True; "sprints" in data; len > 0 |
| jira_spotify_health | Env vars + dimension scores input | success==True; "THS" in data; "health_color" in data |
| jira_little_law | agile_client board/sprint flow endpoint | success==True; "L_wip" in data; "lambda_throughput" in data |

#### Invalid Input Tests (path b) -- examples

```
jira_tco_analysis: user_count=-1 or user_count="abc" -> success==False, "error" in data
jira_pert_estimate: optimistic=10, most_likely=5, pessimistic=15 (O>M) -> success==False
jira_burndown_chart: total_points=-1 or sprint_id=None -> success==False
jira_holiday_sprint_plan: num_sprints=0 -> success==False
jira_ahp_prioritize: criteria_matrix=[] or non-square matrix -> success==False
```

#### API Exception Tests (path c) -- pattern

```python
with patch('urllib.request.urlopen', side_effect=Exception("network failure")):
    result = asyncio.run(server.jira_cycle_time_analysis(board_id=1, sprint_id=42))
    data = json.loads(result)
    assert data["success"] == False
    assert "error" in data
```

### 5.4 Regression Tests for Upgraded Tools

For each of the 4 upgraded tools, add a regression test class that verifies:
1. Old-style minimal inputs still work (backward compat)
2. New math output keys are present in the response (forward compat)
3. Existing keys are still present (no removals)

#### jira_refine_backlog

```python
class TestJiraRefineBacklogRegression:
    # OLD: called with project_key, sprint_id; returned wsjf_scores, backlog_items
    # NEW: must also return new keys (e.g., "cognitive_load_index" or "tco_analysis")
    def test_old_keys_still_present(self): ...  # assert "wsjf_scores" in data (if it was there)
    def test_new_math_keys_present(self): ...   # assert new Phase B.1/B.2 keys are present
```

#### jira_sprint_review

```python
class TestJiraSprintReviewRegression:
    # OLD: returned "delivered", "not_delivered", "re_score"
    # NEW: must also return "burndown_metrics" or similar new analytical keys
    def test_re_score_still_present(self): ...
    def test_new_burndown_keys_present(self): ...
```

#### jira_team_health

```python
class TestJiraTeamHealthRegression:
    # OLD: returned "tuckman_stage", "composite_score"
    # NEW: must also return "tuckman_markov" or "spotify_health_check" output keys
    def test_tuckman_stage_still_present(self): ...
    def test_spotify_ths_present(self): ...
```

#### jira_get_velocity

```python
class TestJiraGetVelocityRegression:
    # OLD: returned "mean", "stddev", "cv", "nasscom_agileX_level"
    # NEW: must also return "bootstrap_bca_ci" output (lower/upper CI bounds)
    def test_nasscom_level_still_present(self): ...
    def test_bca_ci_keys_present(self): ...  # assert "lower" in data or "bca_ci" in data
```

---

## 6. Acceptance Criteria

All three gates must pass before Phase D.2 agents may proceed.

| Gate ID | Criterion | Measurement | Enforcement Level |
|---------|-----------|-------------|------------------|
| D1-G1 | 100% line coverage for all 16 new scrum_calculator functions | `pytest --cov=scrum_calculator --cov-report=term-missing tests/test_scrum_calculator_new.py`; zero uncovered lines in lines 533-1813 | HARD GATE |
| D1-G2 | DRE = 1.0 for integration tests | All integration tests pass; zero unexpected exceptions from @mcp_tool_handler-wrapped tools; all 3 paths (happy/invalid/exception) pass for all 16 new tools | HARD GATE |
| D1-G3 | All 143 existing tests still pass | `pytest tests/` with no regressions; test count >= 143 | HARD GATE |
| D1-G4 | Float tolerance atol=0.001 | All float assertions use `pytest.approx(abs=0.001)` or equivalent; no `==` on raw floats | Code review gate |
| D1-G5 | ASCII-only source files | Both new test files pass `python -c "open('filename', encoding='cp1252').read()"` without error | Windows compatibility |
| D1-G6 | No real network calls in unit tests | `grep -n "urllib\|requests\|http" tests/test_scrum_calculator_new.py` returns zero matches | Static analysis gate |

---

## STATUS: STRATEGY COMPLETE -- D.2 agents may proceed

**Phase D.1 signed off by:** test-management-agent
**Date:** 2026-05-28
**Pre-condition satisfied:** Phase C Gate APPROVED (NLI=1.0, FactScore=0.957)

**Handoff to:**
- `unit-testing-specialist` -> Create `tests/test_scrum_calculator_new.py` per Section 4
- `integration-testing-engineer` -> Create `tests/test_tools_integration_new.py` per Section 5
