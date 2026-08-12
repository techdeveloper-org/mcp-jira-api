---
name: agile-metrics-core
description: "Provides mathematical foundations for agile delivery metrics including burn-down/up charts, cumulative flow diagrams, cycle time analysis, throughput, and Monte Carlo forecasting. Use when analyzing team delivery performance, forecasting sprint or release completion, computing flow metrics, or benchmarking velocity stability. Keywords: burn-down chart mathematics, cumulative flow diagram, cycle time percentiles, Monte Carlo sprint forecast, Little's Law throughput, agile velocity stability index, throughput Poisson model."
allowed-tools: Read,Glob,Grep
user-invocable: true
---


<!-- generated-by: claude-global-library/tools/project_sync -->
<!-- source: skills/agile-metrics-core/SKILL.md -- edit the library, then re-run sync_project.py -->

# agile-metrics-core

## Description

Agile delivery teams live and die by the numbers they track. This skill provides the rigorous mathematical foundations for every major metric class in agile: burn-down and burn-up mechanics, Cumulative Flow Diagram (CFD) interpretation via Little's Law, empirical cycle time distributions, Monte Carlo release forecasting, Poisson throughput modeling, and the Velocity Stability Index (VSI). Each section delivers formulas, derivations, worked examples, and practitioner decision rules — not just definitions.

**Use when:** analyzing team delivery performance, forecasting sprint or release completion dates, computing flow metrics to reduce cycle time, benchmarking velocity stability before committing to fixed-scope releases, or designing agile dashboards that surface leading indicators.

**Keywords:** burn-down chart mathematics, cumulative flow diagram, cycle time percentiles, Monte Carlo sprint forecast, Little's Law throughput, agile velocity stability index, throughput Poisson model.

---

## 1. Flow Metrics and Flow Efficiency

Flow efficiency measures the fraction of elapsed time that work is actively being worked on (touch time) versus waiting in queues.

### 1.1 Flow Efficiency Formula

```
FE = Touch_Time / (Touch_Time + Wait_Time) × 100%
```

Where:
- **Touch_Time** — active work time (coding, reviewing, testing while the tester is active)
- **Wait_Time** — passive time (blocked, waiting for PR review, waiting in deployment queue, waiting for sign-off)

Flow Efficiency is measured per-item by tracking timestamps as work items transition through states in Jira/Azure DevOps. Aggregate FE is the average across all items completed in a time window.

### 1.2 Industry Benchmarks

Research source: ASOS internal lean survey, Kanban University publications.

| Category | Flow Efficiency Range | Interpretation |
|---|---|---|
| Typical / average | 5–15% | Teams waste 85–95% of cycle time in queues |
| Improving | 15–25% | Active optimization underway |
| High-performing | 25–40% | Sustained lean practices, strong WIP discipline |
| World-class (rare) | 40–70% | Extreme focus and automated toolchains |

**Key insight:** most teams are surprised to find their FE is below 15%. The bottleneck is almost never development speed — it is queue wait time (code review backlog, deployment pipeline, approval gates). Halving WIP limits will usually double FE within two sprints.

### 1.3 Measuring Flow Efficiency in Practice

From a Jira/Azure DevOps state history:
1. Extract per-item time in each state (date of entry minus date of exit).
2. Classify states: Active (In Progress, Code Review active) vs Passive (Backlog, Ready for Review, Blocked, Ready to Deploy).
3. Compute FE per item: `FE_item = sum(Active_state_durations) / total_calendar_duration`.
4. Aggregate across all items completed in the reporting window.

FE below 10% is a hard signal to investigate WIP and handoff policies before any technical investment.

---

## 2. Velocity and Throughput Analytics

### 2.1 Velocity Stability Index (VSI)

The VSI quantifies a team's delivery predictability over a rolling sprint window.

```
VSI = 1 - (σ_velocity / μ_velocity)   where n = 6–10 sprints
```

Where:
- `σ_velocity` = standard deviation of completed story points across last n sprints
- `μ_velocity` = mean completed story points across same window

VSI = 1 means perfect stability (zero variance). VSI = 0 means σ = μ (coefficient of variation = 100%). Clamp VSI at 0 for σ > μ cases.

### 2.2 VSI Thresholds and Decision Rules

| VSI Range | Maturity Level | Decision Rule |
|---|---|---|
| > 0.75 | High maturity | Safe to make fixed-scope commitments; use mean velocity for planning |
| 0.50–0.75 | Moderate maturity | Use P85 velocity buffer for commitments; investigate instability drivers |
| < 0.50 | Low maturity | **Do not commit to fixed-scope releases.** Use Monte Carlo for probabilistic forecasting only |

**Decision rule — fixed-scope releases:** if VSI < 0.50, the coefficient of variation exceeds 50%, meaning sprint output is highly unpredictable. Committing to a specific scope by a specific date will fail in roughly half of cases. Escalate to leadership with data before committing.

### 2.3 Recommended Observation Window

Use n = 6–10 sprints for VSI computation. Fewer than 6 gives noisy estimates (high bootstrap variance on VSI itself). More than 12 may include historical data that no longer reflects current process or team composition.

### 2.4 NASSCOM Velocity Benchmark Flag

**Important:** NASSCOM does not publish velocity-per-sprint benchmarks for Indian IT teams. No publicly available authoritative source provides velocity benchmarks by team size or seniority tier. Relative VSI improvement (quarter-over-quarter) is more meaningful than absolute velocity comparison across teams. Indian Tier-1 IT firms typically report VSI in the 0.70–0.85 range (training knowledge, not published benchmark — use with caution).

---

## 3. Cumulative Flow Diagrams and Little's Law

### 3.1 Little's Law

Little's Law is the foundational relationship for all flow-based agile metrics:

```
L = λ × W
```

Where:
- **L** = average number of items in the system (WIP)
- **λ** = arrival rate (throughput, items per unit time)
- **W** = average time an item spends in the system (cycle time)

Applied to a Kanban/Scrum flow:

```
Cycle_Time = WIP / Throughput
```

All three variables must use consistent units (e.g., items and days).

**Corollary:** To reduce cycle time, either reduce WIP (apply WIP limits — a policy decision) or increase throughput (add capacity — expensive). WIP limits are always cheaper and faster to implement.

### 3.2 CFD Band Interpretation

A Cumulative Flow Diagram plots cumulative item counts entering each workflow state versus calendar time.

- **Vertical distance** between adjacent bands = WIP at that point in time
- **Horizontal distance** between entry to a state and exit from that state = cycle time for items at that point
- **Band width** for a given state = average age of work in that state
- **Flat band** (horizontal plateau) = work starvation in that state or items blocked from entering
- **Expanding gap** between "In Progress" and "Done" bands = WIP accumulation (items entering faster than completing)

### 3.3 WIP Limits from CFD

From a stable CFD, derive WIP limit target:
```
WIP_target = Throughput_target × CT_target
```

If the team wants cycle time ≤ 2 weeks and throughput = 4 items/week, set WIP limit = 4 × 2 = 8 items.

### 3.4 Throughput Stability

```
CV_throughput = σ_throughput / μ_throughput
```

- CV < 0.5: stable flow
- CV 0.5–1.0: moderate variability, monitor
- CV > 1.0: highly variable, investigate for process disruptions

---

## 4. OKR and Goal Measurement

While OKRs are tracked separately from sprint metrics, agile teams often need to connect delivery metrics to strategic goals.

### 4.1 Objective Score (O-score)

```
O_score = weighted_avg(KR_scores)   where KR scores in [0, 1]
```

Typical KR scoring scale:
- 0.0–0.3 = significantly below target
- 0.4–0.6 = partial progress
- 0.7–1.0 = on track to exceeding target

### 4.2 Key Result Scoring — Linear Interpolation

For a numeric KR with baseline B, target T, and current value C:

```
KR_score = (C - B) / (T - B)    clipped to [0, 1]
```

If C = B: KR_score = 0 (no progress). If C = T: KR_score = 1.0 (target hit). If C > T: clamp at 1.0 or extend target.

### 4.3 Weighted OKR Aggregation

For an objective with n Key Results, each with importance weight w_i:

```
O_score = sum(w_i × KR_score_i) / sum(w_i)
```

Practical recommendation: use equal weights (w_i = 1/n) unless strategic priority clearly differentiates KRs. Over-engineering weights without data adds noise.

### 4.4 Connecting Agile Metrics to OKRs

Common agile metric → OKR link patterns:

| Agile Metric | Likely OKR Dimension |
|---|---|
| Cycle time reduction | Engineering effectiveness |
| Flow Efficiency | Lean delivery capability |
| Defect density | Quality |
| Deployment frequency | Release cadence |
| MTTR (mean time to restore) | Reliability |

---

## 5. Lead Time and Cycle Time Analysis

### 5.1 Definitions

- **Lead time** = total elapsed time from when a request is made (ticket created) to delivery to the customer.
- **Cycle time** = elapsed time from when the team starts active work on an item to delivery.
- **Queue time** = lead time minus cycle time (time before work starts).

For SLA commitments, use **lead time** percentiles — not cycle time — because customers experience lead time, not internal cycle time.

### 5.2 Why Average Lead Time Is Systematically Optimistic

Lead time and cycle time distributions are right-skewed (log-normal shape). A few slow items create a long tail. The mean is pulled toward the tail while the majority of items complete faster. Consequence: using the mean as an SLA guarantee will be breached roughly 50% of the time by definition (if items distribute symmetrically around the mean, not the case here — the mean exceeds the median for right-skewed distributions).

**Example:** If mean cycle time = 8 days, the 85th percentile may be 14 days. Committing to 8-day SLAs means roughly 35–40% of items miss the commitment.

### 5.3 P85 as the SLA Commitment Level

```
SLA_commitment = CT_P85 = exp(μ_ln + 1.036 × σ_ln)    [log-normal model]
```

Using P85 means 85% of items will meet the SLA. For contractual or high-stakes commitments, use P95.

**Rule:** never quote average lead time as a commitment to customers. Quote P85 (or explain confidence levels explicitly). Internal planning uses P50 (median); external commitments use P85; contractual deadlines use P95.

### 5.4 Empirical Percentile from Raw Data (Without Fitting)

For n ≥ 20 cycle time observations (sorted ascending CT_{(1)} ≤ ... ≤ CT_{(n)}):

```
CT_P85 = CT_{(ceil(0.85 × n))}
```

With n < 20, use parametric fit (log-normal MLE — see M3 below) to smooth estimates.

---

## 6. Deep Mathematical Foundations

### M1: Burn-Down and Burn-Up Chart Mathematics

**Foundation:** Stochastic process modeling of sprint remaining work.

#### First-Principles Derivation

**Ideal Burn-Down Line:** Sprint starts with scope S_0 story points, duration T days. Remaining work R(t) decreases linearly under the ideal (constant velocity) assumption:

```
R(t) = S_0 × (1 − t/T)            for t ∈ [0, T]
R(0) = S_0;   R(T) = 0
```

**Actual Burn-Down — Three Stochastic Models:**

**(i) Constant rate (deterministic):** `R(t) = S_0 − r × t` where r = daily burn rate.

ETC (Estimated Time to Complete):
```
ETC_const = R_current / daily_burn_avg
daily_burn_avg = (S_0 − R_current) / t_elapsed
```

**(ii) Exponential decay:** `R(t) = S_0 × e^{−k × t}` where k is fitted via log-regression on first j observations:

```
k = −ln(R(j) / S_0) / j
```

Time to R(t) = 0 is infinite under this model — use t such that R(t) < 1 SP as effective completion time.

**(iii) Stochastic Brownian motion with drift:** `R(t) = S_0 − μ × t + σ × W(t)` where W(t) is standard Brownian motion. Expected first-passage time:

```
E[T_complete | R_current] = R_current / μ
```

**Scope Volatility Index (SVI):** Let scope at day i be S_i (scope changes when items are added or removed during sprint). Define:

```
SVI = σ(S_i) / μ(S_i)    over sprint days i = 1..T
```

Sample size guidance: need at least 10 daily observations for stable SVI. With a 10-day sprint this is exactly met; shorter sprints (5 days) yield directional SVI only.

**Formulas:**
```
R_ideal(t) = S_0 × (1 − t/T)
ETC_const  = R_current / daily_burn_avg
ETC_exp    = ln(S_0) / k   (approximately)
SVI        = σ(S_i) / μ(S_i)
```

**Worked Example:** Sprint: S_0 = 50 SP, T = 10 days. Day 5: R_5 = 22 SP (28 done). `daily_burn_avg = 28/5 = 5.6 SP/day`. `ETC = 22/5.6 = 3.93 days`. Total projected = 5 + 3.93 = 8.93 days ≤ 10. Sprint is on track.

Scope addition event: 6 SP added on day 5 → new R_5 = 28. ETC = 28/5.6 = 5.0 days. Total = 10.0 — at risk.

SVI example: scope observations [50, 50, 52, 52, 56, 56, 56, 56, 56, 56]. μ = 54.0, σ = 2.46. SVI = 2.46/54 = 0.046 = 4.6% (low, healthy). SVI > 15% signals undisciplined product owner.

**Practitioner Interpretation:** Use constant-rate ETC for daily standups. If scope changes exceed 10%, switch to burn-up chart (which separates scope line from progress line). High SVI is a backlog hygiene problem, not an engineering problem.

**Boundary Conditions:** `daily_burn_avg = 0` (no work done) makes ETC infinite — flag immediately in dashboard. Negative SVI is impossible; near-zero SVI may indicate artificially frozen scope (also a red flag worth investigating).

---

### M2: Little's Law and Cumulative Flow Diagram Analysis

**Foundation:** Queueing theory, ergodic processes.

#### First-Principles Derivation

**Little's Law (general statement):** In any stationary system in steady-state:

```
L = λ × W
```

where L = average number in system, λ = arrival rate, W = average sojourn time.

**Proof (time-average argument):** Over long horizon [0, T], total customer-time accumulated = ∫₀ᵀ L(t) dt. This also equals Σᵢ Wᵢ (sum over all customers of their sojourn times) = λ × T × W_avg. Therefore:

```
L_avg × T = λ × T × W_avg
⟹  L_avg = λ × W_avg
```

Formally: by the Birkhoff ergodic theorem, under stationarity, time-average equals ensemble-average. Little's Law holds for any queueing discipline, any service time distribution, and any arrival process — it requires only stationarity.

**Application to Kanban/Scrum:**

λ = throughput (items completed per day), L = WIP (items in the system), W = cycle time. Therefore:

```
Cycle_Time = WIP / Throughput
```

**CFD Geometry:**

```
N_i(t) = cumulative items that entered state i by time t

Vertical distance at time t:
  WIP_state_i(t) = N_i_entered(t) − N_i_exited(t)

Horizontal distance:
  For an item entering state i at time s and exiting at time t: sojourn = t − s
  Average sojourn = average horizontal distance between entry and exit curves

Band width for state i ≈ average age of work in state i
```

**Throughput CV:**
```
CV_throughput = σ_throughput / μ_throughput
```
- CV < 0.5: stable flow
- CV > 1.0: highly variable, investigate

**Worked Example:** Team has avg WIP = 8 items, throughput = 4 items/week.

```
Cycle_Time = 8 / 4 = 2 weeks
```

To hit CT = 1 week: must halve WIP (enforce WIP limit = 4) OR double throughput (add people — expensive, Brooks' Law risks). WIP limit is the first lever to pull.

CFD verification: if the "In Progress" band has thickness 8 items and slope 4 items/week, items spend on average 2 weeks in In Progress — confirming Little's Law geometrically.

**Boundary Conditions:** Little's Law requires stationarity. If throughput is trending or seasonal, use rolling windows of 4–12 weeks to approximate local stationarity. When a new WIP limit policy is applied, allow 1–2 sprint adjustment periods before reading new steady-state values.

---

### M3: Cycle Time Percentile Distributions (Log-Normal MLE)

**Foundation:** Maximum likelihood estimation, log-normal distribution.

#### First-Principles Derivation

**Why Log-Normal for Cycle Times:** Cycle times are right-skewed with a long tail of slow items. The multiplicative delay model: total cycle time = product of independent stage delays (waiting × processing × review × deployment). Taking log:

```
ln(CT) = Σ ln(stage_delay_i)
```

By the Central Limit Theorem on the sum of log-stage-delays, ln(CT) is approximately Normal. Therefore CT is Log-Normal.

**MLE Estimation:** Given n historical cycle times CT_1, ..., CT_n:

```
μ_ln_hat   = (1/n) × Σᵢ ln(CT_i)             [sample mean of log-transformed data]
σ_ln_hat²  = (1/n) × Σᵢ (ln(CT_i) − μ_ln_hat)²   [MLE variance; use 1/(n−1) for unbiased]
```

**Percentile Calculation:**
```
CT_p = exp(μ_ln + σ_ln × Φ⁻¹(p))
```

where Φ⁻¹ is the standard normal quantile (inverse CDF).

Key percentiles:
- P50 (median) = exp(μ_ln)
- P85 = exp(μ_ln + 1.036 × σ_ln)
- P95 = exp(μ_ln + 1.645 × σ_ln)

Note: mean ≠ median for log-normal. Mean = exp(μ_ln + σ_ln²/2) > P50. This is why the mean is systematically optimistic as an SLA target.

**Kolmogorov-Smirnov Goodness-of-Fit Test:**

```
D_n = sup_x |F_n(x) − F_hat(x)|
```

where F_n is the empirical CDF and F_hat is the fitted log-normal CDF. Reject log-normal fit at α = 0.05 if D_n > 1.36/√n (asymptotic critical value). If rejected, try Gamma or Weibull alternatives.

**Worked Example:** 20 historical cycle times (days): [3, 5, 4, 12, 7, 6, 4, 9, 15, 5, 8, 6, 11, 4, 7, 10, 6, 5, 14, 8].

```
μ_ln_hat  = mean(ln values) = 1.962
σ_ln_hat  = 0.444

P50 = exp(1.962)                     = 7.11 days
P85 = exp(1.962 + 1.036 × 0.444)    = exp(2.422) = 11.27 days
P95 = exp(1.962 + 1.645 × 0.444)    = exp(2.692) = 14.76 days
```

SLA commitment: "We deliver within 12 days for 85% of items." Supportable by data.

Compare to arithmetic mean: mean ≈ 7.65 days. If the team quotes 8 days as their SLA, ~35% of items will breach it.

**Boundary Conditions:** With n < 10, fit is unreliable; report percentiles directly from sorted data instead. If KS test rejects log-normal, use empirical CDF percentiles. Items stuck for months (outliers) should be modeled separately or excluded with documentation.

---

### M4: Monte Carlo Sprint and Release Forecasting

**Foundation:** Empirical bootstrap, Monte Carlo simulation, Law of Large Numbers.

#### First-Principles Derivation

**Why Empirical Bootstrap, NOT Poisson:**

Real daily throughput is bimodal: probability mass at 0 (no completions on weekends, holidays, unplanned-work days) + small count values on working days. Poisson assumes mean = variance (equidispersion). Real teams show overdispersion (variance > mean) due to zero-inflation and burst days. Empirical bootstrap preserves the actual distribution shape including the zero-mass and fat tails.

**Algorithm:**

```
INPUT:  D historical daily-throughput data points {d_1, ..., d_D}
        B = backlog size (story points or items)
        N = number of trials (standard: 100,000; minimum acceptable: 10,000)

FOR trial = 1 TO N:
    days = 0
    completed = 0
    WHILE completed < B:
        sample daily_throughput from {d_1,...,d_D} uniformly WITH REPLACEMENT
        completed += daily_throughput
        days += 1
    record days_to_complete[trial] = days

SORT days_to_complete ascending

P50 = days_to_complete[ceil(0.50 × N)]    (internal planning target)
P85 = days_to_complete[ceil(0.85 × N)]    (stakeholder commitment)
P95 = days_to_complete[ceil(0.95 × N)]    (contractual/SLA deadline)
```

**Probability Statement:**
```
P(completion in ≤ d days) = #{trial : days_to_complete[trial] ≤ d} / N
```

**Convergence:** By the Law of Large Numbers, P_hat → P as N → ∞. For N = 100,000, the standard error of the P85 estimate is approximately ±1–2 days for typical agile teams (confirmed empirically by Kanban University practitioners).

**Minimum data requirement:** at least 3 sprints (~30 data points) for stable distribution shape. Recommended: 10+ sprints (100+ data points). Rolling window of 10–12 most recent sprints discards stale data if process has changed.

**Communication Protocol:**
- Report P85 to stakeholders, not P50 alone. P50 creates systematic overconfidence.
- Internal team plans to P50 (expected scenario).
- Stakeholder commitments use P85 (85% confidence).
- SLAs and contractual deadlines use P95 (maximum confidence bound).

**Worked Example:** Backlog = 60 SP. Historical daily throughput (40 days): mixture of 0, 1, 2, 3 SP/day; mean = 1.5 SP/day.

Naive point estimate: 60/1.5 = 40 days. Monte Carlo (N=100,000) returns:
- P50 = 38 days (close to mean — as expected)
- P85 = 45 days (factor of 1.18×)
- P95 = 50 days

Stakeholder communication: "We'll deliver by day 45 with 85% confidence. If you need 95% confidence, plan for day 50."

**Boundary Conditions:** If backlog contains task types not present in historical data (new technology, unfamiliar domain), bootstrap underestimates duration. Solution: split unfamiliar work, estimate separately, combine distributions. If team composition changed significantly, use only post-change data; discard prior history.

---

### M5: Poisson Throughput Model and Flow Forecasting

**Foundation:** Poisson distribution, maximum likelihood estimation, hypothesis testing.

#### First-Principles Derivation

**When Poisson Applies (and When It Does Not):**

Throughput aggregated over a sprint or month often satisfies Poisson assumptions: counting completions at an approximately constant rate over discrete time periods. Poisson is appropriate for sprint-count forecasting and process-change detection. Caveat: daily throughput is overdispersed (daily counts have variance > mean due to zero days and burst days). Always use empirical bootstrap (M4) for simulation; use Poisson for summary statistics and hypothesis testing.

**Likelihood Function:** Given counts k_1, ..., k_n (completions per period over n periods):

```
L(λ) = ∏ᵢ [e^{−λ} × λ^{kᵢ} / kᵢ!]
      = e^{−nλ} × λ^{Σkᵢ} / ∏ kᵢ!
```

Log-likelihood:
```
ℓ(λ) = −nλ + (Σkᵢ) × ln(λ) + const
```

**MLE — Differentiate and Set to Zero:**
```
dℓ/dλ = −n + (Σkᵢ)/λ = 0
⟹  λ_hat = (Σkᵢ) / n = x̄    [sample mean]
```

The MLE for the Poisson rate is simply the sample mean. Second derivative: d²ℓ/dλ² = −Σkᵢ/λ² < 0, confirming maximum.

**Wald (Large-Sample) Confidence Interval:**

Asymptotic variance of λ_hat = λ/n, so:
```
SE(λ_hat) = √(λ_hat / n)
Wald 95% CI: λ_hat ± 1.96 × √(λ_hat / n)
```

Valid when n × λ_hat ≥ 30.

**Garwood (Exact) CI for Small n:**

When n × λ_hat < 30 (few sprints or low throughput), use chi-squared quantiles:
```
CI_lower = 0.5 × χ²(α/2,   df = 2 × Σkᵢ)
CI_upper = 0.5 × χ²(1−α/2, df = 2 × (Σkᵢ + 1))
```

For n ≤ 10 sprints, Garwood is preferred — Wald undercovers.

**Rate Ratio Test (Before vs After Process Change):**

To detect statistically significant throughput improvement after a process change (e.g., new CI/CD pipeline, WIP limit introduction):

```
H₀: λ_after = λ_before

Z = (λ_after_hat − λ_before_hat) / √(λ_a/n_a + λ_b/n_b)

Reject H₀ if |Z| > 1.96  (α = 0.05, two-sided)
```

**Worked Example:** 6 sprints, completions: [8, 10, 9, 7, 11, 9]. Total = 54. λ_hat = 9.0 stories/sprint.

Wald 95% CI: `9.0 ± 1.96 × √(9/6) = 9.0 ± 2.40 = [6.60, 11.40]`

Garwood: χ²(0.025, 108) ≈ 81.8; lower = 81.8/2 / 6 = 6.82. χ²(0.975, 110) ≈ 142; upper = 142/2 / 6 = 11.83. Garwood = [6.82, 11.83] — more conservative.

After 4 sprints with new process: [12, 14, 11, 13]. λ_after = 12.5.

`Z = (12.5 − 9.0) / √(12.5/4 + 9/6) = 3.5 / √(3.125 + 1.5) = 3.5 / 2.15 = 1.63`

|Z| < 1.96 — not statistically significant at α = 0.05 with only 4 post-change sprints. Need more data before claiming process improvement with confidence.

**Overdispersion Check:** Compute Var(kᵢ)/Mean(kᵢ). If ratio significantly > 1, Poisson is misspecified; use Negative Binomial model instead. Variance/mean > 1.5 is a practical trigger for switching.

**Boundary Conditions:** Rate ratio test assumes both periods are stationary within each window. Team composition changes mid-window violate stationarity — split the analysis at the change point. Negative Binomial regression (as overdispersed Poisson) handles excess variance but requires dedicated statistical software.

---

### M6: Velocity Stability Index and Predictability Score

**Foundation:** Coefficient of variation, bootstrap confidence intervals, Wilson score interval.

#### First-Principles Derivation

**Coefficient of Variation:** The CV measures relative dispersion of velocity:

```
CV = σ_v / μ_v    over a sliding window of n = 6–10 sprints
```

**Velocity Stability Index (VSI):**

```
VSI = 1 − CV = 1 − σ_v / μ_v
```

VSI = 1: perfect stability (zero variance). VSI = 0: σ = μ (CV = 100%). VSI < 0: σ > μ — practical interpretation is to clamp at 0.

**Predictability Score (PS):** Fraction of sprints where actual delivery falls within ±10% of commitment:

```
match_i = 1  if  |delivered_i − committed_i| / committed_i ≤ 0.10,  else 0
PS = (Σ match_i) / n
```

**Bootstrap CI for PS:**

1. Resample (commit, delivered) pairs with replacement to form a resample of size n.
2. Compute PS* from the resample.
3. Repeat B = 1,000 times.
4. 95% CI = [PS*_{0.025}, PS*_{0.975}] from the sorted bootstrap distribution.

**Wilson Score CI (Parametric Alternative for PS):**

For binomial proportion p̂ = k/n with z = 1.96:

```
Lower = (p̂ + z²/(2n) − z × √(p̂(1−p̂)/n + z²/(4n²))) / (1 + z²/n)
Upper = (p̂ + z²/(2n) + z × √(p̂(1−p̂)/n + z²/(4n²))) / (1 + z²/n)
```

Wilson gives correct coverage even for small n or extreme proportions (p̂ near 0 or 1) where the Wald CI breaks down.

**Compact forms (z = 1.96, z² ≈ 3.84):**
```
Wilson lower ≈ (PS + 1.92/n − 1.96 × √(PS(1−PS)/n + 0.96/n²)) / (1 + 3.84/n)
Wilson upper ≈ (PS + 1.92/n + 1.96 × √(PS(1−PS)/n + 0.96/n²)) / (1 + 3.84/n)
```

**Formulas:**
```
VSI = 1 − σ_v / μ_v
PS  = #{sprints with |delivered − committed|/committed ≤ 0.10} / n
Wilson 95% CI for PS as above
```

**Worked Example:** Last 8 sprints velocities: [40, 42, 38, 45, 41, 39, 44, 43].

```
μ = 41.5,  σ = 2.39
VSI = 1 − 2.39/41.5 = 1 − 0.0576 = 0.942   → High maturity (>0.75)
```

Commitments vs delivered: [(40,40), (40,42), (40,38), (45,45), (42,41), (40,39), (42,44), (43,43)]. All percentage differences ≤ 10%.

```
PS = 8/8 = 1.0
```

Wilson CI for PS = 1.0, n = 8: Even with 8/8, the CI lower bound is approximately 0.68 (not 1.0). There is real uncertainty — 8 sprints is not enough to claim near-perfect predictability with statistical confidence.

**VSI Decision Rules (from M2 table):**
- VSI > 0.75 → mature team, commit confidently.
- VSI 0.50–0.75 → stabilizing; use lower confidence bound of commitment range.
- VSI < 0.50 → high noise; investigate root causes (constant interruptions, scope creep, poor estimation calibration).

**Boundary Conditions:** `μ_v = 0` makes VSI undefined (divide by zero) — flag data collection error. n < 6 sprints: VSI estimate is noisy; report with Wilson-like CI to convey uncertainty. PS = 1.0 (all sprints hit ±10%) is suspicious — likely indicates commitments well below capacity (sandbagging); investigate if committed velocity matches team's actual demonstrated rate.

---

## 7. Anti-Patterns to Avoid

- **Quoting average (mean) lead time as an SLA commitment to customers**: per §5.2, lead/cycle time distributions are right-skewed (log-normal shape), so the mean is pulled toward the long tail and exceeds the median — committing to the mean means roughly 35-40% of items will breach the commitment; use P85 (external commitments) or P95 (contractual deadlines), never the mean.
- **Committing to a fixed-scope release when VSI < 0.50**: per §2.2's decision rule, a coefficient of variation exceeding 50% means sprint output is highly unpredictable — a fixed-scope, fixed-date commitment at this maturity level fails in roughly half of cases; use Monte Carlo probabilistic forecasting instead, not a point commitment.
- **Comparing raw velocity numbers across different teams**: per §2.4, no authoritative benchmark source publishes velocity-per-sprint by team size or seniority, and story points are not a standardized unit across teams to begin with — relative VSI improvement quarter-over-quarter for the *same* team is meaningful; cross-team absolute velocity comparison is not.
- **Responding to rising cycle time by adding headcount/capacity before checking WIP limits**: per §3.1's Little's Law corollary (`Cycle_Time = WIP / Throughput`), reducing WIP is always cheaper and faster to implement than increasing throughput via added capacity — jumping straight to a hiring/capacity conversation skips the lower-cost lever the formula itself identifies as the correct first move.
- **Computing VSI over a window shorter than 6 sprints or longer than 12**: per §2.3, fewer than 6 sprints gives noisy estimates with high bootstrap variance on VSI itself, while more than 12 risks including historical data from a process or team composition that no longer reflects current reality — both directions produce a VSI that doesn't answer the question it's meant to answer.
- **Using the empirical percentile formula (`CT_P85 = CT_{(ceil(0.85×n))}`) on fewer than 20 observations**: per §5.4, this raw-order-statistic approach requires `n ≥ 20` to be reliable — with fewer observations, a parametric log-normal MLE fit is the specified fallback for smoothing the estimate, not a direct percentile read off a small, noisy sample.
- **Assigning differentiated OKR Key-Result weights without supporting data**: per §4.3, the explicit practical recommendation is equal weights (`w_i = 1/n`) unless strategic priority clearly differentiates KRs — over-engineering weights in the absence of data adds noise to the O-score rather than making it more accurate.
- **Reading a flat band on a Cumulative Flow Diagram as a sign of stability**: per §3.2, a flat (horizontal plateau) band specifically signals work starvation in that state or items blocked from entering — it is a diagnostic red flag, not evidence of healthy, steady flow, and treating it as "nothing changing, so nothing wrong" misses the exact signal CFDs are read for.

## 8. India-Specific Layer

### 7.1 NASSCOM Agile Metrics Context

**Velocity benchmarks:** NASSCOM does not publish velocity-per-sprint benchmarks for Indian IT teams. This is confirmed by web search; no publicly available authoritative source exists. Teams should use their own VSI trend as the primary health indicator rather than external comparison. A VSI consistently above 0.70 is achievable and observed in high-performing Indian IT delivery teams.

**Defect density benchmark:** Indian Tier-1 IT firms (TCS, Infosys, Wipro) target below 0.5 defects per function point as an internal quality metric for software delivery. This is a training-knowledge figure (not a published NASSCOM standard) but is widely referenced in Indian CMMI audit contexts.

### 7.2 India IT Flow Efficiency Context

Indian IT teams often operate in a mixed-mode model (client-facing delivery + internal support). Flow Efficiency benchmarks should account for:
- Offshore governance overhead: approval cycles from client-side (typically US/UK) add systematic wait time, suppressing FE below the 15% global typical level.
- Multi-project assignment: Indian engineers are frequently allocated across 2–3 projects simultaneously, causing context-switching and suppressed FE. Best practice: measure FE per project lane, not across the portfolio.
- Expected FE for India offshore teams working on US/UK client projects: 6–12% is realistic; above 15% is high-performing in this context.

### 7.3 Attrition Impact on Velocity Metrics

Indian IT sector annual attrition: 18–25% (sector-wide, 2022–2024, confirmed). For a team of 10, expect 2–3 departures per year.

**Velocity impact model:**
```
Velocity_adjusted = Velocity_baseline × (1 − attrition_fraction × disruption_factor)
```

Where disruption_factor accounts for the productivity ramp of replacement hires:
- Weeks 0–4 (new hire onboarding): −15% to −25% velocity impact on the team (not just the individual)
- Weeks 5–12 (ramping): −10% to −15% impact
- Full productivity: ~6 months for experienced hire, ~12 months for fresh hire

**Annual attrition velocity cost (for 10-member team, 18% attrition):**

Approximately 1.8 departures/year. Each experienced-hire replacement costs ~6 person-weeks of lost productivity (see agile-team-health-core M6 derivation). Total: 1.8 × 6 = ~11 person-weeks/year ≈ 5.5% of annual team capacity. This should be factored into capacity planning for Indian delivery organizations.

**Practical implications for metrics:**

When VSI drops suddenly for an Indian delivery team, attrition is often the first root cause to investigate — before assuming process failure. A team that loses a key member mid-quarter can see VSI drop from 0.80 to 0.55 within 2–3 sprints; this is recoverable through onboarding, not sprint restructuring.

### 7.4 Distributed Team Cycle Time Effects (IST and Global Timezones)

For Indian teams collaborating with global clients, handoff wait time is a major cycle-time driver:

| Partner Timezone | Gap (h) | Overlap Hours | Async Penalty |
|---|---|---|---|
| US EST (UTC−5) | 10.5 | 4.5 h (17:30–22:00 IST) | High — one-day delay per async handoff |
| US PST (UTC−8) | 13.5 | 1.5 h (20:30–22:00 IST) | Very high — minimal real-time window |
| UK GMT (UTC+0) | 5.5 | 2.5 h (14:30–17:00 IST) | Moderate |
| Singapore SGT | 2.5 | 5.5 h (10:30–16:00 IST) | Low — strong overlap |

**Cycle time correction for distributed teams:**

If a workflow step requires synchronous approval from a US (EST) stakeholder, each such handoff adds ~1 calendar day of wait time (the same-day window closes before approval can come back). For a workflow with 3 such approval steps, expected wait time addition = 3 days. This appears as low FE in CFD analysis but is structural, not a team process problem.

**Recommendation:** for Indian teams with US clients, measure FE excluding timezone-imposed wait (flag it as structural), and track process-controllable FE separately.

### 7.5 STQC and Government IT Project Metrics

For Indian government IT projects delivered under STQC (Software Testing and Quality Certification) or MeitY guidelines:

- **GIGW (Guidelines for Indian Government Websites) quality metrics** should be mapped to Acceptance Criteria in the Definition of Done.
- **CMMI-SVC v2.0 Measurement and Analysis (MA) process area** requires quantitative tracking of service quality metrics, which maps directly to cycle time distributions and FE in an agile context.
- **STQC process compliance** assessments may require documented velocity data, defect density, and test coverage — all derivable from agile metrics with appropriate tooling.

For GeM-sourced project deliveries: project metrics (cycle time, defect density) become contractual deliverables for transparency reports to buyer ministries. Teams should track P85 cycle time for each delivery type as the audit-ready SLA metric.

---

## 9. Response Rules

1. **Always recommend P85, not average, for SLA commitments.** When a user asks "what is our expected delivery time," provide P50 (planning) and P85 (commitment) and explain why average is systematically optimistic for right-skewed distributions.

2. **Always specify the data window for VSI.** VSI without a stated window is ambiguous. Default recommendation is 6–10 most recent sprints. Always flag if n < 6 (noisy estimate) or if a major team event occurred in the window.

3. **Distinguish Monte Carlo simulation inputs (empirical bootstrap) from Poisson model (summary statistics).** These serve different purposes. Monte Carlo forecasts completion dates; Poisson models throughput rates and detects process changes. Do not conflate them.

4. **Little's Law requires stationarity.** When applying WIP = Throughput × CT, always check whether the system is in a stable state. A team in mid-reorganization or ramping from attrition is not stationary — flag this limitation explicitly.

5. **Velocity is a capacity planning tool, not a performance measure.** Do not use velocity to compare different teams. Teams size stories differently, work on different problem domains, and have different compositions. VSI is more meaningful for benchmarking than absolute velocity.

6. **Flow Efficiency benchmarks are context-dependent for India offshore teams.** Global benchmarks (5–15% typical) apply to co-located or low-timezone-gap teams. India-US offshore teams may structurally target 6–12% FE when approval gates are client-controlled. Present this context when interpreting FE results.

7. **Flag NASSCOM benchmark absence explicitly.** When a user asks for NASSCOM velocity benchmarks, state clearly that no published external benchmark exists and redirect to team-relative VSI analysis.

---

## 10. What Not to Do

1. **Do not use velocity for cross-team comparison.** Different teams use story points with different calibration baselines; comparisons are meaningless and create gaming incentives. Use VSI (stability) or throughput in items/sprint (objective count) if comparison is unavoidable.

2. **Do not use average lead time for SLA commitments.** Average lead time for right-skewed distributions will be breached roughly 35–45% of the time. Use P85 for service-level agreements. Using averages for commitments is a systematic failure mode.

3. **Do not report only P50 to stakeholders.** P50 is the median — half of all deliveries will exceed it. Reporting P50 as "the expected date" creates overconfidence and erodes trust when deliveries are late.

4. **Do not apply Poisson simulation for sprint completion forecasting.** Poisson assumes equidispersion (mean = variance), which real daily throughput violates. Use empirical bootstrap Monte Carlo for simulation. Reserve Poisson for rate estimation and hypothesis testing.

5. **Do not use burn-down velocity as a predictor of future sprint velocity.** Within-sprint burn rate can be affected by end-of-sprint heroics, story size clustering, and unplanned work. Sprint-to-sprint velocity (used in VSI) is a better predictor than intra-sprint burn rate.

6. **Do not compute VSI from fewer than 6 sprints.** With n < 6, the coefficient of variation estimate has very high sampling variance — VSI values below 0.60 and above 0.90 are both plausible for a genuinely stable team. Always accompany n < 6 VSI estimates with a caveat.

7. **Do not ignore throughput overdispersion.** If the Poisson dispersion test (Var/Mean > 1.5) fails, do not present Wald CI for throughput as if it is valid. Flag the overdispersion and recommend Negative Binomial or empirical CI.

8. **Do not assume attrition-driven velocity drops are process problems.** Sudden VSI drops in Indian IT teams are frequently caused by attrition and new-hire onboarding, not engineering or process failures. Diagnose before prescribing.

---

## 11. Output Expectations

When applying this skill, outputs should include:

- **Formulas with notation defined:** every symbol explicitly labeled; no ambiguous shorthand.
- **Worked numerical examples:** at least one numeric worked example per metric presented, using realistic agile team data.
- **Benchmark context:** for every metric, state the industry benchmark range and source, and note explicitly when no public benchmark exists (e.g., NASSCOM velocity).
- **India context applied where relevant:** distributed team FE adjustment, attrition-velocity analysis, and GeM/STQC metric mapping when the context is Indian delivery.
- **Decision rules:** for each metric, provide explicit threshold-triggered decision rules (e.g., "if VSI < 0.50, do not commit to fixed-scope releases").
- **Confidence intervals:** for any estimate (PS, λ_hat, percentile), provide a CI or at minimum state sample-size caveats that affect reliability.
- **Limitations flagged:** state when stationarity assumptions are violated, when sample size is too small for reliable estimation, or when empirical data is insufficient.

---

## 12. Skill Scope

This skill covers:
- Burn-down and burn-up chart construction and interpretation
- Cumulative Flow Diagram analysis and Little's Law application
- Cycle time distribution fitting (log-normal MLE) and percentile computation
- Monte Carlo empirical bootstrap for sprint and release forecasting
- Poisson throughput model for rate estimation and process-change detection
- Velocity Stability Index computation and threshold-based decision rules
- Flow Efficiency measurement and benchmark interpretation
- India-specific context: distributed team cycle time effects, attrition impact on velocity metrics, NASSCOM benchmark flags, STQC/CMMI metric mapping

This skill does not cover:
- Jira/Azure DevOps tooling configuration for metric extraction (see `jira-devops-tooling-core`)
- Scrum ceremony facilitation and backlog prioritization (see `scrum-framework-core`)
- Team health assessment and psychological safety scoring (see `agile-team-health-core`)
- OKR strategy design and company-level goal setting
- SAFe/LeSS scaled agile metrics (portfolio-level PI planning metrics are in `scrum-framework-core`)

---

## 13. Version

**Version:** 1.0.1 — 2026-07-27 — Added §7 Anti-Patterns to Avoid (8 pitfalls spanning mean-vs-P85 SLA commitments, VSI-based fixed-scope commitment risk, cross-team velocity comparison, WIP-vs-capacity trade-offs, VSI window sizing, small-sample percentile estimation, unjustified OKR weighting, and CFD flat-band misreading); renumbered §7-12 to §8-13.

**Version:** 1.0.0
**Domain:** Agile Business & Revenue Intelligence (Domain 41)
**Research sources:** ASOS flow efficiency survey, Kanban University publications, T05 empirical research (2026-05-17), T08 synthesis, T10 M1–M6 derivations (agile-business-mathematics-expert, Opus)
**India data confirmed:** NASSCOM benchmark absence (confirmed by search), India IT attrition 18–25% (confirmed), IST timezone gaps (confirmed), STQC/CMMI context (training knowledge)
