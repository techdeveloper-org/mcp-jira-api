HALLUCINATION DETECTION REPORT
================================
Date: 2026-05-28
Agent: hallucination-detector
Phase: C.1
Source File: scrum_calculator.py (functions at line 632+)

Function: bootstrap_bca_ci | Status: PASS | Severity: N/A
  Finding: All BCa components verified.
  (a) Bias correction z0 = _normal_inv_cdf(count(boot < theta_hat) / B) -- CORRECT.
  (b) Jackknife leave-one-out loop present (lines 699-701) -- CORRECT.
  (c) Acceleration a = sum((loo_mean-loo_i)^3) / (6*sum((loo_mean-loo_i)^2)^1.5) -- CORRECT.
      diffs = [theta_loo_mean - v for v in theta_loo] matches spec direction.
  (d) alpha1/alpha2 via _normal_cdf(z0 + (z0+z_lo)/denom) where denom = 1-a*(z0+z_lo) -- CORRECT.
  (e) Zero-variance edge case returns lower=upper=point_estimate, B=0, note key -- CORRECT.

Function: ahp_score | Status: PASS | Severity: N/A
  Finding: All AHP components verified.
  (a) Power iteration: 100-iteration loop with max_diff < 1e-6 convergence break -- CORRECT.
  (b) lambda_max = lambda_max_sum / n where lambda_max_sum += (A*w_i / w_i) -- CORRECT.
  (c) RI table = [0,0,0,0.58,0.90,1.12,1.24,1.32,1.41,1.45,1.49] (11 values, indices 0-10) -- CORRECT.
  (d) consistent = cr_val < 0.10 (strict less-than) -- CORRECT.
  (e) n=1 trivial case returns weights=[1.0], lambda_max=1.0, CI=0.0, CR=0.0 -- CORRECT.

Function: tuckman_markov | Status: PASS | Severity: N/A
  Finding: All Tuckman stage classification components verified.
  (a) CV = std_v / mean_v (stdev / mean, with fallback to 1.0 if mean=0) -- CORRECT.
  (b) Slope via full linear regression (n*sum_iv - sum_i*sum_v) / (n*sum_i2 - sum_i^2) -- CORRECT.
  (c) Stage thresholds: len<3 or cv>0.5->Forming; cv>0.25->Storming; cv>0.10 and slope>=0->Norming;
      cv<=0.10 and slope>=0->Performing; else->Norming -- CORRECT, all 4 boundaries match spec.
      Edge cv=0.25 correctly routes to Norming (strict > for Storming).
  (d) stage_probabilities dict with all 4 stages returned -- CORRECT.
  (e) nasscom_agile_x_level key present; Performing maps L4/L5 by cv<=0.05 sub-test -- CORRECT.

Function: spotify_health_check | Status: PASS | Severity: N/A
  Finding: All Spotify Health Check components verified.
  (a) All 11 dimensions validated via _SPOTIFY_DIMENSIONS list (easy_to_release through team_spirit) -- CORRECT.
  (b) THS = sum(dim_means) / 11.0 (uniform mean) -- CORRECT.
  (c) Health color: >=1.5->Green, >=0.75->Amber, else->Red -- CORRECT thresholds.
  (d) Wilcoxon Z = W / sqrt(n_nz*(n_nz+1)*(2*n_nz+1)/6) where n_nz=count of non-zero diffs,
      W = sum(sign(d)*rank(|d|)) -- CORRECT, matches spec formula exactly.

Function: edmondson_ps_scale | Status: PASS | Severity: N/A
  Finding: Cronbach alpha fix verified — returns 0.0 for single-respondent input as per spec docstring. Reverse coding at positions [0,2,4] correct (8-score). PS_score = mean(processed). All return keys present.
  (a) Reverse coding at positions 0,2,4 with formula 8-s -- CORRECT.
  (b) Reverse formula is 8 - score (not 7-score) -- CORRECT.
  (c) PS_score = mean(processed) -- CORRECT. Test [7,7,7,7,7,7,7]: processed=[1,7,1,7,1,7,7], mean=31/7=4.4286. VERIFIED.
  (d) cronbach_alpha = 0.0 explicitly for single-respondent input (line 1119: alpha = 0.0) -- CORRECT. Docstring contract satisfied.
  (e) reverse_coded_positions: [0,2,4] returned -- CORRECT.
  Functional tests passed: [7,7,7,7,7,7,7]->PS_score=4.4286,alpha=0.0,Moderate; [1,1,1,1,1,1,1]->PS_score=3.5714,alpha=0.0,Moderate.

Function: scrum_of_scrums_overhead | Status: PASS | Severity: N/A
  Finding: All Brook's Law adaptation components verified.
  (a) T_n = teams*p - c*teams*(teams-1)/2.0 -- CORRECT.
  (b) n_optimal = p/c + 0.5 (not just p/c) -- CORRECT.
  (c) Validates c < p (c >= p returns error) -- CORRECT.

Function: cognitive_load_index | Status: PASS | Severity: N/A
  Finding: All Team Topology CLI components verified.
  (a) CL_team uses intersection of complexity.keys() and responsibility.keys() -- CORRECT.
  (b) CLI = CL_team / cl_max -- CORRECT.
  (c) overloaded = CLI > 1.0 (strict greater-than) -- CORRECT.
  (d) topology_efficiency: X_as_Service=0.90, Facilitating=0.75, Collaboration=0.70 -- CORRECT.

Function: attrition_ramp | Status: PASS | Severity: N/A
  Finding: All exponential saturation attrition components verified.
  (a) P_t = p_max * (1.0 - exp(-months/tau)) -- CORRECT.
  (b) effective_velocity_factor = 1.0 - p_t -- CORRECT.
  (c) Validates 0 < p_max <= 1.0 (p_max<=0 or p_max>1.0 -> error) -- CORRECT.
  (d) india_context string mentions tau=6 for experienced hires and tau=12 for fresh graduates -- CORRECT.

Function: ist_capacity_correction | Status: PASS | Severity: N/A
  Finding: All IST capacity correction components verified.
  (a) Divides by 8.0 (float literal, not int 8) -- CORRECT.
  (b) q1_seasonal_buffer_factor = 1.15 returned in result dict -- CORRECT.
  (c) india_context mentions "IST UTC+5:30" -- CORRECT.

Function: little_law_analysis | Status: PASS | Severity: N/A
  Finding: All Little's Law components verified.
  (a) L_wip = total_arrived - total_departed -- CORRECT.
  (b) W = L_wip / lambda_throughput (not lambda*L) -- CORRECT; float("inf") when lambda=0.
  (c) birkhoff_caveat present, non-trivial (mentions ergodic theorem, stationary process) -- CORRECT.
  (d) wip_limit_recommendation = max(1, int(lambda*2)) present -- CORRECT.

Function: cycle_time_lognormal_mle | Status: PASS | Severity: N/A
  Finding: All log-normal MLE components verified.
  (a) Uses math.log (natural log, not log10) -- CORRECT.
  (b) sigma_hat = math.sqrt(statistics.variance(log_times)) -- CORRECT; variance then sqrt,
      not stdev directly (semantically equivalent but matches spec wording).
  (c) P85 multiplier exactly 1.036 -- CORRECT.
  (d) P95 multiplier exactly 1.645 -- CORRECT.
  (e) Validates all cycle_times > 0 with per-element check before computation -- CORRECT.

Function: poisson_throughput | Status: PASS | Severity: N/A
  Finding: All Poisson throughput CI components verified.
  (a) lambda_hat = statistics.mean(completed) -- CORRECT.
  (b) Wilson-Hilferty: nu*(1 - 2/(9*nu) + z*sqrt(2/(9*nu)))^3, exponent is 3 -- CORRECT.
  (c) lower df = 2*n_total (sum of completed), upper df = 2*(n_total+1) -- CORRECT.
  (d) Divides by 2.0 for both lower_95_total and upper_95_total -- CORRECT.

Function: pert_estimate | Status: PASS | Severity: N/A
  Finding: All PERT estimate components verified.
  (a) mu = (O + 4*M + P) / 6.0, factor 4 on most_likely -- CORRECT.
  (b) sigma = (P - O) / 6.0 (not /4) -- CORRECT.
  (c) 1.645 multiplier for both CI bounds (90% CI) -- CORRECT.
  (d) Validates O <= M (optimistic <= most_likely) and M <= P -- CORRECT.

Function: tco_npv_comparison | Status: PASS | Severity: N/A
  Finding: All TCO/NPV components verified.
  (a) Jira: 685.0 * 12.0 * 1.18 per user/year; Azure: 430.0 * 12.0 * 1.18 per user/year -- CORRECT.
  (b) 18% GST factor 1.18 applied to both -- CORRECT.
  (c) NPV = sum(CF / (1+r)^t for t in range(1, years+1)) -- t starts at 1, CORRECT.
  (d) break_even = ceil(azure_overhead_fixed / (jira_per_user - azure_per_user)) per user -- CORRECT.

Function: burndown_metrics | Status: PASS | Severity: N/A
  Finding: All burndown metrics components verified.
  (a) ideal_line = [total - total*(i/n) for i in range(n+1)]: starts at total (i=0),
      ends at 0.0 (i=n) -- CORRECT.
  (b) SVI = actual_completed (= completed_by_day[-1], cumulative total) / total_points -- CORRECT.
  (c) sprint_health thresholds: svi>=0.9->"On Track", svi>=0.7->"At Risk", else->"Off Track" -- CORRECT.

Function: multi_sprint_holiday_forecast | Status: PASS | Severity: N/A
  Finding: All multi-sprint holiday forecast components verified.
  (a) Uses INDIA_NATIONAL_HOLIDAYS_2025_2026 frozenset (module-level constant) -- CORRECT;
      _INDIA_HOLIDAY_NAMES dict used for human-readable names.
  (b) sprint_start parsed via date.fromisoformat() with ValueError catch -- CORRECT.
  (c) Sprint windows: sprint k starts at start_d + k*duration, ends at start + k*duration + duration-1;
      non-overlapping by construction -- CORRECT.
  (d) holiday_names list per sprint returned in each sprint dict -- CORRECT.

NLI_SCORE: 16/16 = 1.0
FACTCHECK_CLAIMS: 16 functions verified
PHASE_C_GATE: APPROVED -- NLI=1.0. Phase D may proceed.

Items requiring fix before Phase D: None
