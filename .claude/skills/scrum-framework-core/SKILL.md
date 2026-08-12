---
name: scrum-framework-core
description: "Provides Scrum framework theory, sprint mechanics, velocity distributions, backlog prioritization, and scaled Scrum patterns. Use when designing sprint cadences, facilitating Scrum ceremonies, sizing backlogs, or scaling Scrum across multiple teams. Keywords: scrum master coaching, sprint planning mathematics, velocity distribution, WSJF prioritization, Definition of Done, Scrum of Scrums scaling, agile backlog refinement, sprint capacity planning."
allowed-tools: Read,Glob,Grep
user-invocable: true
---


<!-- generated-by: claude-global-library/tools/project_sync -->
<!-- source: skills/scrum-framework-core/SKILL.md -- edit the library, then re-run sync_project.py -->

# Scrum Framework Core

## Description

This skill provides the complete mathematical and conceptual foundation for Scrum practitioners, coaches, and engineering managers. It covers Scrum values, roles, artifacts, and events; sprint mechanics including capacity planning and velocity forecasting; backlog management with WSJF prioritization and Definition of Done quality gates; Monte Carlo release forecasting; and Scrum of Scroms scaling mathematics.

Use when designing sprint cadences, facilitating Scrum ceremonies, coaching Scrum Masters, sizing and ordering backlogs, forecasting release dates with uncertainty bounds, or scaling Scrum across multiple teams.

Keywords: scrum master coaching, sprint planning mathematics, velocity distribution, WSJF prioritization, Definition of Done, Scrum of Scrums scaling, agile backlog refinement, sprint capacity planning, Monte Carlo forecast, sprint velocity probability.

---

## 1. Scrum Foundations

### 1.1 Scrum Values

Scrum is grounded in five values:

1. **Commitment** — The Scrum Team commits to the Sprint Goal and to each other.
2. **Courage** — Team members have the courage to tackle difficult problems and to be transparent.
3. **Focus** — Everyone focuses on sprint work and the sprint goal; WIP discipline is paramount.
4. **Openness** — The team is open about all work, including impediments and quality concerns.
5. **Respect** — Team members respect each other's skills, experience, and background.

Violations of these values — hidden impediments, scope additions without transparency, unspoken quality issues — are the leading causes of sprint failure. The Scrum Master's primary responsibility is to surface and resolve these violations.

### 1.2 Empirical Pillars

Scrum is built on three empirical pillars:

1. **Transparency** — Significant aspects of the process are visible. Artifacts (Product Backlog, Sprint Backlog, Increment) must be transparent to all stakeholders. Definition of Done makes quality transparent.
2. **Inspection** — Scrum events (Daily Scrum, Sprint Review, Retrospective) are scheduled inspection points. Inspection without adaptation is pointless.
3. **Adaptation** — When inspection reveals deviation, the process or product must be adjusted as soon as possible.

### 1.3 Roles

| Role | Accountability | Key Skill |
|------|---------------|-----------|
| **Product Owner (PO)** | Maximize product value. Owns and orders the Product Backlog. Single voice for stakeholders. | Backlog ordering by WSJF, acceptance criteria writing, stakeholder management. |
| **Scrum Master (SM)** | Ensure Scrum is understood and enacted. Remove impediments. Coach team and organization. | Facilitation, impediment resolution (MTTR), metrics literacy. |
| **Developers** | Create each Sprint's shippable Increment. Self-managing, cross-functional. | Sprint estimation, focus factor management, Definition of Done compliance. |

The PO is the only person who can order the Product Backlog and the only person who can cancel a Sprint.

### 1.4 Artifacts

| Artifact | Commitment | Content |
|----------|-----------|---------|
| **Product Backlog** | Product Goal | Ordered list of everything needed in the product. Product Owner is accountable. |
| **Sprint Backlog** | Sprint Goal | Sprint Goal + selected Product Backlog items + plan for delivering them. Developers own it. |
| **Increment** | Definition of Done | Sum of all Product Backlog items completed during Sprint and all prior Sprints. Must meet DoD to be shippable. |

Each artifact has a commitment that makes progress measurable and actionable.

### 1.5 Events (Ceremonies)

| Event | Time-box | Purpose |
|-------|---------|---------|
| **Sprint** | 1–4 weeks | Container for all other events. Fixed-length iteration. |
| **Sprint Planning** | ≤ 8h (4-week sprint) | Select PBI items, negotiate Sprint Goal, create Sprint Backlog plan. |
| **Daily Scrum** | 15 minutes | 24-hour synchronization plan for Developers. Inspect progress toward Sprint Goal. |
| **Sprint Review** | ≤ 4h (4-week sprint) | Inspect Increment with stakeholders. Update Product Backlog as needed. |
| **Sprint Retrospective** | ≤ 3h (4-week sprint) | Inspect team process and practices. Create improvement plan. |

All events are formal opportunities to inspect and adapt. Skipping or shortening events beyond time-boxes reduces transparency and increases risk.

---

## 2. Sprint Mechanics

### 2.1 Sprint Length Selection

Sprint length drives all planning horizons. Selection criteria:

| Factor | Shorter Sprints (1 week) | Longer Sprints (3–4 weeks) |
|--------|--------------------------|---------------------------|
| Business feedback loop needed | Rapidly changing markets | Stable requirements |
| Technical complexity | Mature CI/CD, automated testing | Complex integrations, hardware |
| Team experience | Experienced Scrum teams | Teams new to Scrum |
| Stakeholder availability | High availability | Limited stakeholder time |

**Recommended default:** 2-week sprints for most software teams. This balances feedback frequency against planning overhead.

Once selected, sprint length must remain constant within a release. Changing sprint length mid-release invalidates historical velocity comparisons.

### 2.2 Sprint Goal Setting

A Sprint Goal is a single objective that gives coherence to the Sprint Backlog. Properties:

- **Specific enough** to guide daily decisions (which work has highest priority today?)
- **Flexible enough** to allow scope adjustments when developers discover complexity
- **Valuable** — stakeholders can assess progress against it at Sprint Review
- **Achievable** — P85 confidence that the team can reach it within sprint capacity (see M1 and M3)

Bad Sprint Goal: "Complete all 12 stories in the Sprint Backlog."
Good Sprint Goal: "Users can search for and bookmark products on mobile without a login."

### 2.3 Sprint Execution

During the sprint, the Sprint Backlog is owned by Developers. Key execution rules:

1. No items are added to the Sprint Backlog by the PO without Developer agreement. Scope changes consume capacity from existing goals.
2. Impediments are raised in the Daily Scrum and resolved by the SM, not carried silently.
3. The Sprint Goal is protected: if scope overflows, Developers negotiate with PO to remove lower-priority items, not extend the sprint.
4. Unfinished items return to the Product Backlog at sprint end — no partial credit.

### 2.4 Sprint Cancellation

Only the Product Owner can cancel a Sprint, and only when the Sprint Goal becomes obsolete (market shift, technology pivot, strategic change). Sprint cancellation is rare. Any completed and "Done" Increment items are accepted; incomplete items are re-estimated and returned to backlog.

---

## 3. Backlog Management

### 3.1 Product Backlog Ordering

The Product Backlog is ordered (not merely prioritized — ordering implies a single ranked list, not buckets). The PO orders using explicit criteria. WSJF (Weighted Shortest Job First) is the mathematically grounded ordering method — see M2 for the full derivation.

Ordering inputs:
- Business value delivered (BV)
- Time criticality (TC) — value degradation over time, regulatory deadlines
- Risk reduction (RR) — elimination of architectural, market, or regulatory risk
- Opportunity enablement (OE) — enables future value streams
- Job size — estimated development effort

### 3.2 Backlog Refinement

Backlog refinement (formerly "grooming") is an ongoing activity, not a single ceremony. The Scrum Guide allocates no more than 10% of the team's capacity to refinement activities. For a 10-day sprint with a 6-person team, this is approximately 6 person-days of refinement effort.

**Definition of Ready (DoR):** Criteria a PBI must meet before it can be pulled into a Sprint Backlog:
- Independent (can be delivered alone)
- Negotiable (not a fixed contract)
- Valuable (delivers measurable value)
- Estimable (Developers can estimate size)
- Small (fits in a sprint)
- Testable (acceptance criteria defined)

### 3.3 Acceptance Criteria and Definition of Done

**Acceptance Criteria (AC):** Story-specific — what must be true for this specific story to be accepted by the PO. Written in Given-When-Then (BDD) or structured prose.

**Definition of Done (DoD):** Team-wide — applied to every story. Includes code review, automated test coverage, security scan, performance baseline, documentation, deployment to staging. The DoD makes quality commitments transparent. See M4 for the AHP-weighted DoD scoring model.

A story is not "done" until both AC and DoD are satisfied. Partial completion (e.g., "code done but tests pending") is an anti-pattern that creates hidden technical debt.

---

## 4. Monte Carlo Forecasting

Monte Carlo release forecasting is the statistically rigorous alternative to velocity-based point estimation. It samples from historical throughput to generate probability distributions over completion dates.

### 4.1 Why Not Velocity Point Estimates?

Using a single velocity number (e.g., "team does 40 SP/sprint, backlog is 200 SP, so 5 sprints") has three structural problems:

1. **No uncertainty quantification.** Velocity varies sprint-to-sprint; a point estimate ignores this variance.
2. **Systematic optimism bias.** P50 (median) estimates are wrong 50% of the time by construction.
3. **Throughput is bimodal.** Daily completions cluster at 0 (non-working days) and small integers, not a smooth distribution.

### 4.2 Monte Carlo 5-Step Algorithm (T05 Confirmed)

**Step 1 — Build Throughput Distribution**

Collect historical daily throughput as a calendar-day array (items completed per day, including zeros for non-working days and weekends). Include zeros — they represent real variance.

- Minimum sample: 3 sprints (~30 data points)
- Recommended: 10+ sprints (100+ data points)
- Do NOT fit to Poisson or Normal; use empirical bootstrap only
- Reason: real throughput is bimodal (zero on non-working days, clustered on working days)

**Step 2 — Define Simulation Parameters**

- N_trials = 100,000 (standard; 10,000 minimum acceptable)
- forecast_window = number of calendar days in sprint or release window
- backlog_size = number of items remaining to forecast

**Step 3 — Run Bootstrap Simulation**

```
results = []
for trial in range(N_trials):
    total = 0
    day = 0
    while total < backlog_size:
        daily_throughput = random.choice(historical_throughput_array)  # sample with replacement
        total += daily_throughput
        day += 1
    results.append(day)
results.sort()
```

**Step 4 — Compute Percentile Predictions**

- P50 (median) — internal team planning target
- P85 — recommended for stakeholder commitments
- P95 — maximum confidence bound for contractual deadlines
- Never report only P50 to stakeholders — creates systematic overconfidence bias

```
P(completion <= d) = #{trials where days <= d} / N_trials
P85 = sorted_results[ceil(0.85 * N_trials)]
```

**Step 5 — Communicate Uncertainty**

Report as range: "Between P50 and P85 days, stakeholder commitment at P85."

Update forecast every sprint with new throughput data (rolling window: last 10–12 sprints; discard older data if process changed).

### 4.3 P50 vs P85 Guidance

| Audience | Percentile | Rationale |
|----------|-----------|-----------|
| Internal team | P50 | Daily planning target; wrong half the time, but balanced |
| Stakeholders / PO | P85 | High-confidence commitment; right 85% of the time |
| Contracts / SLAs | P95 | Near-certain bound; reserve for binding commitments |

---

## 5. Scaling Scrum

### 5.1 Scrum of Scrums (SoS)

When multiple Scrum teams work on a single product:

- Each team sends one representative (usually a Developer or SM) to the SoS meeting
- SoS meets 3× per week (or daily for coordinated sprints)
- Agenda: cross-team dependencies, integration risks, shared impediments
- SoS Ambassador rotates — not always the SM

SoS adds a coordination overhead layer but is far more efficient than fully-connected team communication. See M5 for the Brooks' Law extension derivation that quantifies the optimal team size and SoS break-even.

### 5.2 Large-Scale Scrum (LeSS)

LeSS applies Scrum at 2–8 teams working on a single product:

- Single Product Backlog, single PO
- One Sprint for all teams (synchronized)
- Combined Sprint Review
- Single Definition of Done for all teams
- Teams self-select PBI items each sprint

LeSS Huge (8+ teams) adds Area Product Owners per customer area. LeSS prioritizes team autonomy and reduces coordination structures — few explicit ceremonies beyond standard Scrum.

### 5.3 SAFe (Scaled Agile Framework) Overview

SAFe organizes teams into an Agile Release Train (ART) of 50–125 people, using Program Increments (PIs) of 8–12 weeks. SAFe adds more roles (RTE, Business Owners, System Architects) and ceremonies (PI Planning, System Demo, Inspect and Adapt). It is more prescriptive than LeSS and works better in enterprise compliance environments.

### 5.4 When to Scale and Anti-Patterns

**Scale only when necessary:**
- Multiple teams required due to technical scope (not organizational structure)
- Teams have dependencies on shared components or services
- Coordination overhead of ad-hoc communication exceeds SoS ceremony cost

**Anti-patterns of premature scaling:**
- Splitting a 6-person team into three 2-person "squads" — destroys cross-functional capability
- Adopting SAFe with < 3 teams — ceremony overhead exceeds coordination benefit
- Running SoS without resolving intra-team impediments first — garbage in, garbage out

---

## 6. Deep Mathematical Foundations

### M1: Sprint Velocity Probability Distributions

**Foundation:** F3 (Monte Carlo bootstrap), F5.1 (Normal, CLT).

**First-Principles Derivation:**

Velocity V is the total story points completed in a sprint. Decompose: V = sum_{i=1}^{N} S_i where S_i is the size of story i and N is the number of stories completed.

**Dual-Model Justification:**

(i) **Sum-of-stories model (Normal, for planning):** When N_stories per sprint >= 30, by CLT, V is approximately Normal(mu, sigma^2) with mu = N * E[S], sigma^2 = N * Var(S). Most enterprise sprints have 5–15 stories — well below 30 — but if we extend over 3–6 sprints, total stories >= 30 holds, and CLT applies to release-level forecasts.

(ii) **Daily throughput model (NOT Normal):** Daily completions are bimodal: most days have 0 completions, occasional days have 1–3. Underlying distribution is mixture of point mass at 0 and small-count distribution. CLT fails because sample size is too small (n=10 days) and underlying is highly skewed. Hence use empirical bootstrap for simulation.

(iii) **Practitioner rule:** When sigma/mu > 0.30 (coefficient of variation), fall back to empirical bootstrap for forecasting.

**MLE for Normal:** Given V_1,...,V_n historical sprint velocities (n = 6–10):

```
mu_hat = (1/n) * sum V_i
sigma_hat^2 = (1/(n-1)) * sum (V_i - mu_hat)^2    (unbiased)
```

**Probability Forecast:** P(V >= target):

```
Z = (target - mu_hat) / sigma_hat
P(V >= target) = 1 - Phi(Z) = Phi(-Z)
```

where Phi is the standard normal CDF.

**Seasonal Adjustment (DST and India festival blackout):** Effective working days vary. Adjusted mean:

```
mu_adjusted = mu_hat * (D_effective / D_nominal)
```

Example: India Diwali week reduces D_effective from 10 to 7 days, so mu_adjusted = mu_hat * 0.70.

**Formula:**

```
V_planning ~ Normal(mu_hat, sigma_hat^2)
P(V >= target) = 1 - Phi((target - mu_hat) / sigma_hat)
mu_adjusted_seasonal = mu_hat * (D_effective / D_nominal)
```

**Worked Example:** A Bangalore team has velocities [42, 38, 45, 40, 36, 44] (6 sprints, SP).

mu_hat = 40.83 SP, sigma_hat^2 = 11.77, sigma_hat = 3.43.
Target = 45 SP. Z = (45 - 40.83) / 3.43 = 1.215. P(V >= 45) = Phi(-1.215) = 0.112 = 11.2%.

If Diwali week reduces effective days from 10 to 7:
mu_adjusted = 40.83 * 0.70 = 28.58 SP. Commit only ~28 SP for that sprint.

**Practitioner Interpretation:** Use Normal for planning (commitment, capacity dialogue) when CV < 0.30. Use empirical bootstrap for confidence intervals on aggregate forecasts. Always seasonal-adjust the mean for known reduced-capacity sprints.

**Boundary Conditions:** N < 30 per sprint and CV > 0.30 — switch to empirical bootstrap. If sigma_hat^2 = 0 (zero variation), model degenerates to point mass; check for data quality (likely under-reported variance).

**India Regulatory Values:** Focus Factor 0.7–0.8 (T05 confirmed) used in M3 for capacity arithmetic.

---

### M2: WSJF Backlog Prioritization and Fibonacci Relative Sizing

**Foundation:** None.

**First-Principles Derivation:**

**Cost of Delay (CoD):** Sum of four ordinal value drivers:

```
CoD = BV + TC + RR + OE
```

where BV = User-Business Value, TC = Time Criticality, RR = Risk Reduction, OE = Opportunity Enablement.

**Weighted Shortest Job First (WSJF):**

```
WSJF = CoD / Job_Size
```

**Greedy Optimality Justification:** Given a queue of jobs and infinite resources, processing jobs in decreasing WSJF order minimizes total weighted cost of delay. This is a textbook result for the **single-machine total weighted completion time problem**: optimal schedule sorts by w_i / p_i descending (Smith's rule, 1956).

Proof sketch (exchange argument): Consider adjacent jobs i, j with WSJF_i > WSJF_j (so v_i/p_i > v_j/p_j with v = value, p = job size). Swapping increases cost by p_j*v_i - p_i*v_j > 0 (since v_i*p_j > v_j*p_i). Hence WSJF order is optimal.

**Fibonacci Log-Scale Cognitive Discrimination:**

Fibonacci sequence: {1, 2, 3, 5, 8, 13, 20, 40, 100}. Weber's Law states that the just-noticeable-difference (JND) is proportional to magnitude:

```
Delta_x / x = constant (Weber ratio)
```

For Fibonacci adjacent terms (1->2, 2->3, 3->5, 5->8, 8->13, 13->20):

```
Delta/x = 1/1, 1/2, 2/3, 3/5, 5/8, 7/13
       = 1.000, 0.500, 0.667, 0.600, 0.625, 0.538
```

For large terms (8 onward), Delta/x approaches the golden ratio limit phi-1 = 0.618. All adjacent terms maintain Weber ratio ~0.5–0.7, comfortably above the JND threshold for size estimation (~0.30 for cognitive tasks).

For a linear scale {1,2,...,n}, Delta/x = 1/n -> 0 as n grows. By size 10, the Weber ratio is 0.10, below JND — estimators cannot reliably distinguish 9 vs 10. Hence linear scales compress at scale.

**Formula:**

```
WSJF_i = (BV_i + TC_i + RR_i + OE_i) / Job_Size_i
Priority order: schedule in decreasing WSJF_i
```

**Worked Example:**

| Story | BV | TC | RR | OE | CoD | Size | WSJF |
|-------|----|----|----|----|----|------|------|
| A     | 8  | 5  | 3  | 2  | 18 | 5    | 3.60 |
| B     | 5  | 8  | 8  | 1  | 22 | 3    | 7.33 |
| C     | 13 | 2  | 1  | 5  | 21 | 8    | 2.63 |
| D     | 3  | 13 | 5  | 8  | 29 | 13   | 2.23 |

Priority order: B > A > C > D. Story B is highest priority despite mid-tier CoD because it is small.

**Practitioner Interpretation:** Always sort by WSJF descending; never by CoD alone. A high-CoD large story is dominated by a moderate-CoD tiny story. Fibonacci scale forces estimators to choose between distinct cognitive bins, reducing analysis paralysis.

**Boundary Conditions:** Job_Size = 0 makes WSJF undefined (infinite). Practical convention: minimum Job_Size = 1 (smallest Fibonacci). Story splitting recommended when Size > 20.

**India Regulatory Values:** None.

---

### M3: Sprint Capacity Planning with Bootstrap Confidence Intervals

**Foundation:** F3 (Bootstrap CI).

**First-Principles Derivation:**

**Capacity Formula:**

```
Capacity = (Team_Members * Sprint_Days * Focus_Factor) - Leave_Days
```

Each component:
- Team_Members: count of full-time equivalents (FTE).
- Sprint_Days: working days in sprint duration (excluding weekends/holidays).
- Focus_Factor (FF): empirical fraction of available time spent on sprint work (rest is meetings, support, etc.).
- Leave_Days: planned absence in person-days.

Units: person-days of focused work. Convert to story-point capacity via Capacity_SP = Capacity_days * SP_per_person_day where SP_per_person_day is the team's productivity ratio.

**Empirical Focus Factor:**

```
FF_hat = actual_velocity / theoretical_capacity_no_FF
```

For each of past 6 sprints: FF_i = V_i / (Team_Members * Sprint_Days - Leave_Days).

**Bootstrap CI on Focus Factor (Algorithm):**

```
Input: FF_1, FF_2, ..., FF_n (n=6 historical sprints)
1. For b = 1 to B = 1,000:
   a. Sample n indices with replacement from {1..n} -> {i_1,...,i_n}.
   b. Compute FF*^{(b)} = (1/n) * sum FF_{i_k}.
2. Sort {FF*^{(1)},...,FF*^{(B)}}.
3. 95% CI = [FF*_{25}, FF*_{975}]   (2.5th and 97.5th percentiles).
```

**Formula:**

```
Capacity = (Members * Days * FF_hat) - Leave
95% CI on FF: [FF*_{025}, FF*_{975}]   (B=1,000 bootstrap)
Capacity 95% CI: substitute FF lower/upper into Capacity formula
```

**Worked Example:** 6-person team, 10 sprint days, 4 leave days planned. Historical FF: [0.75, 0.78, 0.72, 0.80, 0.74, 0.77].

mean(FF) = 0.7600. Bootstrap CI (B=1,000) typically returns ~[0.73, 0.79].

Capacity = (6 * 10 * 0.76) - 4 = 41.6 person-days.
Lower bound (FF=0.73): (6*10*0.73) - 4 = 39.8 days.
Upper bound (FF=0.79): (6*10*0.79) - 4 = 43.4 days.

Report: Capacity = 41.6 [39.8, 43.4] person-days.

**Practitioner Interpretation:** Commit to the lower bound; stretch to the upper. Capacity is not a single number — it is a distribution. Use the CI to set sprint commitment range.

**Boundary Conditions:** With n=6 sprints, bootstrap CI may be wide. Need n >= 10 for stable CI. Also FF should be stable — large FF variance indicates external interruptions; address root cause.

**India Regulatory Values:** Focus_Factor 0.7–0.8 (T05 confirmed); India Factories Act / IT-ITES labor law limits effective work to 48 hours/week (~6 focused hours/day after breaks). NASSCOM AgileX velocity benchmarks by team size exist but are not publicly published — use team's own VSI (see agile-metrics-core).

---

### M4: Definition of Done — AHP Weighted Scoring

**Foundation:** F6.1 (AHP).

**First-Principles Derivation:**

Definition of Done has n criteria (e.g., code review, unit tests, security scan, documentation). Each criterion produces a Bernoulli gate: g_i in {0, 1}.

**DoD Composite Score:**

```
DoD_Score = sum_i w_i * g_i / sum_i w_i           (weighted compliance ratio)
```

If all g_i = 1, DoD_Score = 1. If any g_i = 0 weighted appropriately, score < 1. Threshold for "done" typically 0.95.

**AHP for Deriving Weights w_i:**

Build pairwise comparison matrix A (n x n). a_{ij} = importance of criterion i over j on Saaty's 1–9 scale. a_{ji} = 1/a_{ij}.

**Power Iteration for Principal Eigenvalue:**

```
1. Initialize w^0 = (1/n, 1/n, ..., 1/n)
2. Repeat until ||w^{k+1} - w^k|| < 1e-6:
   y = A * w^k
   w^{k+1} = y / sum(y)         (L1 normalize)
3. lambda_max = (A * w)^T * 1 / (w^T * 1)
```

**Consistency Check:**

```
CI = (lambda_max - n) / (n - 1)
CR = CI / RI(n)         (require CR < 0.10)
```

Saaty's Random Index RI(n) for n criteria:

| n  | 1 | 2 | 3    | 4    | 5    | 6    | 7    | 8    | 9    | 10   |
|----|---|---|------|------|------|------|------|------|------|------|
| RI | 0 | 0 | 0.58 | 0.90 | 1.12 | 1.24 | 1.32 | 1.41 | 1.45 | 1.49 |

**Formula:**

```
w = principal eigenvector of A (normalized to sum 1)
lambda_max = (A*w)^T * 1
CI = (lambda_max - n) / (n - 1)
CR = CI / RI(n)         (require CR < 0.10)
DoD_Score = sum_i w_i * g_i
```

**Worked Example:** 4 DoD criteria: (C1 code-review, C2 unit tests, C3 security scan, C4 docs).

Pairwise matrix A:

```
     C1   C2   C3   C4
C1 [ 1,   3,   2,   5  ]
C2 [ 1/3, 1,   1/2, 3  ]
C3 [ 1/2, 2,   1,   4  ]
C4 [ 1/5, 1/3, 1/4, 1  ]
```

After power iteration: w = (0.475, 0.158, 0.293, 0.074). lambda_max ~ 4.07.
CI = (4.07 - 4)/3 = 0.0233. RI(4) = 0.90. CR = 0.0233/0.90 = 0.026. CR < 0.10 -> consistent.

If g = (1, 1, 0, 1) (security scan failed):
DoD_Score = 0.475 + 0.158 + 0 + 0.074 = 0.707 < 0.95 threshold. Story NOT done.

**Practitioner Interpretation:** AHP forces the team to make pairwise comparisons rather than guess weights. CR < 0.10 catches inconsistent judgments. DoD_Score < threshold = not shippable.

**Boundary Conditions:** CR > 0.10 means re-do pairwise judgments. Saaty's RI table limits n <= 15. For larger criteria sets, group hierarchically.

**India Regulatory Values:** NASSCOM DSCI security checklist criteria (NASSCOM Data Security Council of India) can be incorporated as mandatory DoD items for regulated Indian IT projects (banking, healthcare, government). Security scan g_i must = 1 for DSCI-compliant projects.

---

### M5: Scrum of Scrums Coordination Overhead — Brooks' Law Extension

**Foundation:** None.

**First-Principles Derivation:**

**Setup:** n team members, each producing p story-points per sprint individually. Pairwise coordination (sync meetings, handoffs, dependency tracking) costs c story-points-equivalent per pair per sprint.

**Number of pairs:** C(n, 2) = n*(n-1)/2.

**Net team throughput:**

```
T(n) = n * p - c * n * (n - 1) / 2
```

**Optimal Team Size (T09 corrected formula):**

Differentiate with respect to n (treating as continuous):

```
dT/dn = p - c * (2n - 1)/2 = p - c*n + c/2
```

Setting dT/dn = 0:

```
p - c*n + c/2 = 0
c*n = p + c/2
n* = p/c + 1/2   approximately equal to p/c
```

Second derivative: d^2 T / d n^2 = -c < 0. Hence n* is a maximum (concave function).

**CRITICAL NOTE — Blueprint Correction:** The blueprint stated n* = sqrt(2p/c). This formula is **dimensionally inconsistent** — sqrt(story-points / story-points-per-pair) does not yield a count. The correct optimum derived from first principles is n* = p/c + 1/2. Round to nearest integer: n* approximately equals p/c.

**Tradeoff:** For each additional person, you gain p productivity but add coordination cost c*n (because the new person pairs with all existing n members). When n = p/c, marginal benefit equals marginal cost.

**Maximum Throughput:**

```
T(n*) = (p/c) * p - c * (p/c) * (p/c - 1) / 2
      = p^2/c - c * (p^2/c^2 - p/c) / 2
      = p^2/c - p^2/(2c) + p/2
      = p^2 / (2c) + p/2
```

**Scaling Topologies — Comparison:**

Three coordination structures for N teams of size s each (total = N*s people):

1. **Fully connected (no scaling framework):** Every pair of teams syncs. Coordination cost = c * (N*s)(N*s - 1)/2.

2. **Scrum of Scrums (tree, one rep per team):** Each team has 1 rep at SoS. Pairs are: within-team N * s(s-1)/2 + among reps N(N-1)/2. Coordination scales as N + s^2.

3. **LeSS / SAFe (hub-and-spoke):** A coordination layer with M < N teams syncing. Total pairs = N(s-1) + within-team + M(M-1)/2 (cross-team via the M hubs).

**Break-even between SoS and fully-connected:** When N*s(N*s-1)/2 > N*s(s-1)/2 + N(N-1)/2. Simplifying for large N, s: N^2*s^2/2 vs N*s^2/2 + N^2/2. SoS wins when N > 1 — i.e., always for multi-team. The benefit grows as O(N).

**Formula:**

```
T(n) = n*p - c*n*(n-1)/2
n* approximately = p/c + 1/2   (CORRECTED from blueprint)
T(n*) = p^2/(2c) + p/2
```

**Worked Example:**

A development team has p = 8 SP/person/sprint productivity. Coordination cost c = 0.8 SP/pair/sprint (from 30-minute daily standup overhead per pair).

n* = 8/0.8 + 0.5 = 10.5, round to n = 10 or 11.
T(10) = 10*8 - 0.8*10*9/2 = 80 - 36 = 44 SP/sprint.
T(11) = 11*8 - 0.8*11*10/2 = 88 - 44 = 44 SP/sprint.
T(15) = 15*8 - 0.8*15*14/2 = 120 - 84 = 36 SP/sprint (over-staffed).

Adding people beyond 11 reduces throughput due to coordination overhead — Brooks' Law confirmed.

**Practitioner Interpretation:** Team size n* = p/c. If coordination cost is high (chatty product, distributed team, async tools missing), c is large and n* is small (5–7). If coordination cost is low (mature team, async-first), n* can be 10–12. Scrum of Scrums starts being valuable above ~10 people total.

**Boundary Conditions:** p, c are stylized parameters and must be calibrated per team. This is a derivation aid — teams should observe their own throughput-vs-size curve to calibrate p and c empirically.

**India Regulatory Values:** None.

---

### M6: Impediment MTTR and M/M/1 Flow Efficiency

**Foundation:** F5.3 (Poisson), F5.4 (Exponential), F7 (M/M/1).

**First-Principles Derivation:**

**Impediment Arrival Model:** Impediments arrive as a Poisson process with rate lambda_imp per sprint. Each impediment has resolution time T_resolve ~ Exponential(mu) where mu = 1/MTTR_target.

**M/M/1 Queue:** Single Scrum Master serves impediments FIFO. Traffic intensity rho = lambda_imp / mu.

From M/M/1 queueing theory:

```
P(n in queue) = (1 - rho) * rho^n
E[L] = rho / (1 - rho)
E[W] = 1 / (mu - lambda_imp)         (sojourn time)
E[W_queue] = rho / (mu * (1 - rho))  (waiting time before service starts)
```

**Mean Time to Repair (MTTR):**

```
MTTR = E[T_resolve] = 1/mu
```

**Flow Efficiency Derivation:**

```
FE = Active_Time / (Active_Time + Wait_Time)
   = (1/mu) / E[W]
   = (1/mu) / (1/(mu - lambda_imp))
   = (mu - lambda_imp) / mu
   = 1 - rho
```

Hence FE = 1 - rho directly. This connects FE benchmarks to utilization:

| Flow Efficiency | Utilization rho | Interpretation |
|----------------|-----------------|----------------|
| 5–15% (typical) | 85–95% | Heavily loaded; most time in queues |
| 15–25% (improving) | 75–85% | Progress being made on WIP control |
| 25–40% (high-performing) | 60–75% | Healthy flow; sustainable pace |
| 40–70% (world-class) | 30–60% | Lean flow; minimal wait states |

**Practitioner Inversion:** Given observed FE_obs, infer rho_obs = 1 - FE_obs. If FE_obs = 10% (typical), rho = 0.90 — system is heavily loaded.

**Formula:**

```
rho = lambda_imp / mu
E[L] = rho / (1 - rho)
E[W] = 1 / (mu - lambda_imp)
FE = 1 - rho
```

**Worked Example:** Scrum Master resolves on average 5 impediments per 10-day sprint with target MTTR = 1 day. lambda_imp = 0.5/day; mu = 1.0/day. rho = 0.5/1.0 = 0.5.

E[L] = 0.5/0.5 = 1.0 (avg 1 impediment in system).
E[W] = 1/(1.0 - 0.5) = 2.0 days.
FE = 1 - 0.5 = 0.50 = 50% (world-class).

If MTTR = 1.5 days: mu = 0.667, rho = 0.5/0.667 = 0.75. FE = 25% (high-performing).

If MTTR = 2 days: mu = 0.5, rho = 0.5/0.5 = 1.0. Queue is unstable — backlog grows without bound. Root-cause action required immediately.

**Practitioner Interpretation:** To improve FE from 10% to 25%, reduce rho from 0.90 to 0.75. Either reduce impediment arrival rate (root-cause analysis, DevOps investment) or reduce MTTR (clearer escalation paths, dedicated SM time).

**Boundary Conditions:** rho >= 1 means system is unstable — queue grows without bound. Must address root cause. Assumes M/M/1 (exponential service times). For non-exponential service, use M/D/1 model (constant service time), which has lower wait time: E[W_queue]_{M/D/1} = rho / (2*(mu - lambda)).

**India Regulatory Values:** FE benchmarks: 5–15% typical, 25–40% high-performing, 40–70% world-class (T05 confirmed; Kanban University / ASOS industry data).

---

## 7. India-Specific Layer

### 7.1 NASSCOM AgileX Maturity Model

The NASSCOM AgileX Maturity Model provides a 5-level structure for assessing agile adoption maturity in Indian IT organizations. Levels progress from ad-hoc adoption (L1) to continuous improvement with predictable delivery (L5).

| Level | Descriptor | Typical VSI Range | Sprint Length |
|-------|-----------|-------------------|--------------|
| L1 | Scrum naming, waterfall practice | < 0.40 | 2–4 weeks, inconsistent |
| L2 | Sprints running, ceremonies held | 0.40–0.55 | 2 weeks |
| L3 | Metrics tracked, DoD enforced | 0.55–0.70 | 2 weeks, consistent |
| L4 | Monte Carlo forecasting in use | 0.70–0.80 | 2 weeks, predictable |
| L5 | Scaling Scrum, flow metrics active | > 0.80 | 2 weeks, near-zero impediment MTTR |

Note: Exact velocity benchmarks by team size are not publicly published by NASSCOM. Use your team's own VSI trend compared to L1–L5 descriptors.

### 7.2 CMMI-DEV v2.0 and Scrum Integration

Indian IT companies frequently hold CMMI appraisals for export contracts and government bids. CMMI-DEV v2.0 Process Areas map to Scrum events:

| CMMI PA | Scrum Equivalent |
|---------|-----------------|
| Project Planning (PP) | Sprint Planning + Release backlog forecasting |
| Project Monitoring and Control (PMC) | Daily Scrum + burn-down tracking + impediment log |
| Requirements Management (REQM) | Product Backlog + acceptance criteria + DoD |
| Configuration Management (CM) | Definition of Done (version control, branching, CI/CD gates) |
| Measurement and Analysis (MA) | Velocity, VSI, FE, MTTR metrics |
| Process and Product Quality Assurance (PPQA) | Sprint Retrospective improvement actions |

Teams seeking CMMI Level 3 appraisal can map Scrum artifacts to CMMI evidence requirements, avoiding redundant documentation. The Sprint Retrospective action log is the primary evidence for PPQA and OPF (Organizational Process Focus).

### 7.3 IST Timezone Overlap Formulas for Distributed Scrum Teams

IST = UTC+5:30. Standard working hours assumption: 09:00–18:00 local.

| Partner Timezone | IST Gap | Overlap Window (IST) | Overlap Window (Partner) | Overlap Hours |
|-----------------|---------|---------------------|--------------------------|--------------|
| US EST (UTC-5) | 10.5 h | 18:30–22:00 IST | 08:00–11:30 EST | ~3.5 h |
| US PST (UTC-8) | 13.5 h | 21:30–00:00 IST | 08:00–10:30 PST | ~2.5 h |
| UK GMT (UTC+0) | 5.5 h | 14:30–18:00 IST | 09:00–12:30 GMT | ~3.5 h |
| Singapore SGT (UTC+8) | 2.5 h | 09:00–15:30 IST | 11:30–18:00 SGT | ~6.5 h |
| Australia AEST (UTC+10) | 4.5 h | 09:00–13:30 IST | 13:30–18:00 AEST | ~4.5 h |

**Effective Sprint Capacity Adjustment for Distributed Teams:**

```
Effective_Capacity = Nominal_Capacity * (overlap_hours / total_work_hours)
```

For India-US EST distributed team: overlap = 3.5 h / 8 h = 0.4375.

If Nominal_Capacity = 41.6 person-days, Effective_Capacity = 41.6 * 0.44 = 18.3 person-days for synchronous collaboration work. Asynchronous work (coding, test writing) uses full nominal capacity. Apply this adjustment only to collaboration-heavy ceremonies and design sessions.

**Daily Scrum Timing for India-US Teams:**

Recommended: 08:30 IST / 22:00 EST (previous day). This is a stretch for India but falls within extended US hours. For India-UK: 14:30 IST / 09:00 UK works well within standard hours.

**Velocity Penalty for Async-Heavy Teams:**

Distributed teams with > 8-hour gaps (India-US) incur a 10–20% velocity penalty due to delayed decision cycles, async PR review latency, and timezone-induced context switching (T05 confirmed). Factor this into sprint capacity planning.

### 7.4 India IT Attrition Context

India IT sector annual attrition rate: 18–25% (NASSCOM HR benchmarks 2022–2024).

For a 6-person team, expected annual churn: 1.1–1.5 people. Sprint velocity impact of new hire onboarding:

| Onboarding Phase | Duration | Velocity Impact |
|-----------------|---------|-----------------|
| Weeks 0–4 | First month | -15% to -25% (onboarding load on team) |
| Weeks 5–12 | Ramping | -10% to -15% |
| Weeks 13–26 | Contributing | 0% to +5% |
| 6+ months | Full productivity | Baseline restored |

**Attrition-Adjusted Annual Velocity:**

```
V_adjusted = V_base * (1 - (attrition_rate * avg_ramp_months / 12))
```

For attrition = 22%, avg ramp = 4 months:
V_adjusted = V_base * (1 - (0.22 * 4/12)) = V_base * 0.927 = ~7.3% annual velocity loss.

This explains why Indian IT teams experience persistent velocity drift despite team size stability. Scrum Masters should factor attrition-adjusted capacity into quarterly release forecasts.

### 7.5 GeM-Related Sprint Planning for Government Projects

For Indian IT teams delivering on Government e-Marketplace (GeM) contracts, sprint planning must account for government-specific delivery constraints:

- **GeM milestone billing:** Sprints align to contract milestones, not product increments. Sprint Goals must map to billable milestone deliverables.
- **Acceptance testing delays:** Government acceptance cycles add 15–30 days to sprint reviews. Buffer this in release forecasting (add to Monte Carlo forecast window).
- **STQC compliance:** Software Testing and Quality Certification (STQC) requirements may mandate formal test documentation per sprint increment for government systems.
- **MeitY audit sprints:** Cloud-hosted government projects may require MeitY security audit sprints (penetration testing, VAPT) before go-live. These are non-feature sprints; reserve 1 sprint per quarter in release planning.

### 7.6 DPIIT Startup Context

For DPIIT-recognized startups in India (115,000+ registered as of 2024):

- **Definition of Done for funded startups:** Include investor demo-readiness as a DoD gate for Q1–Q2 milestones (investor updates align to sprint reviews).
- **NASSCOM 10,000 Startups:** Startups in this program receive agile coaching as part of the program. NASSCOM AgileX L2 is the typical entry level for funded startups.
- **Product-led growth sprint velocity:** Indian B2B SaaS startups report higher velocity variance (VSI 0.40–0.55) due to rapid pivoting and small team sizes (< 5 Developers). Monte Carlo forecasting is especially important at this stage.

---

## 8. Anti-Patterns to Avoid

- **Reporting only P50 to stakeholders**: a median forecast is wrong 50% of the time by construction (§4.2, Step 4) — external commitments need P85, contractual/SLA bounds need P95; P50 is for internal daily planning only.
- **Fitting throughput to Poisson or Normal instead of empirical bootstrap**: real daily throughput is bimodal (clustered at zero on non-working days, small integers otherwise), so a parametric fit misrepresents the shape the Monte Carlo algorithm is designed to sample directly (§4.2, Step 1).
- **Excluding zero-throughput days from the historical array**: dropping non-working days from the sample understates variance and produces an overconfident forecast — zeros are real data points, not noise to filter (§4.2, Step 1).
- **Using a single velocity point estimate for release planning**: "40 SP/sprint, 200 SP backlog, so 5 sprints" carries none of Monte Carlo's uncertainty quantification, inherits the P50 optimism bias, and assumes a smooth distribution that bimodal throughput does not have (§4.1's three structural problems).
- **Accepting partial completion against AC or DoD**: "code done but tests pending" is explicitly named as an anti-pattern (§3.3) because it creates hidden technical debt that the Definition of Done was designed to make transparent, not negotiable per-story.
- **Changing sprint length mid-release**: altering the cadence invalidates every historical velocity comparison used for forecasting (§2.1) — the Monte Carlo throughput array itself becomes a mix of two different sampling processes.
- **Adding scope to the Sprint Backlog without Developer agreement**: a PO-driven addition mid-sprint consumes capacity from the committed Sprint Goal without the team's consent (§2.3, rule 1) — scope changes are negotiated, not imposed.
- **Extending the sprint instead of negotiating scope when it overflows**: the correct response to overrun is removing lower-priority items with the PO, not moving the sprint boundary (§2.3, rule 3) — extending the timebox breaks the fixed-length container every other measurement (velocity, MTTR, throughput) assumes.
- **Scaling coordination structure past the Brooks'-Law optimum**: adding people or teams beyond `n* = p/c + 1/2` (M5) increases coordination cost faster than it adds productivity — the worked example shows throughput falling from 44 to 36 SP/sprint going from 11 to 15 people; check the throughput-vs-size curve before scaling, don't assume more people always helps.
- **Triaging impediments without an MTTR/flow-efficiency model**: treating impediment resolution as ad hoc instead of grounding SM prioritization in the M/M/1 queueing result (M6) misses which impediments are actually starving flow efficiency versus which are cosmetic.

## Response Rules

1. Always present Monte Carlo forecasting over point estimates for release planning — report P50 and P85 together.
2. When asked for velocity predictions, provide P50 AND P85 — never only P50; explain the difference to stakeholders.
3. Cite specific M-section derivations when explaining formulas (e.g., "see M5 for the Brooks' Law extension derivation").
4. Flag when Tuckman transition probabilities are used — those are illustrative and not empirically validated (see agile-team-health-core for the Tuckman Markov model and its caveats).
5. For India teams, apply IST timezone overlap calculations from Section 7.3 when advising on distributed scrum ceremonies.
6. When advising on team size, show the T(n) = n*p - c*n*(n-1)/2 calculation and derive n* = p/c explicitly.
7. Always enforce DoD-Score >= 0.95 threshold; partial sprint credit ("mostly done") is an anti-pattern.
8. Use the corrected n* = p/c formula, not sqrt(2p/c) — the latter is dimensionally inconsistent.

---

## What Not to Do

- Do not use story points as the primary unit in Monte Carlo simulation — use throughput (items completed per day or per sprint).
- Do not state velocity as a commitment — velocity is a planning input, not a promise; P85 of the Monte Carlo forecast is the stakeholder commitment.
- Do not recommend Scrum for non-iterative work (e.g., pure maintenance/ops flows, linear infrastructure provisioning) — Kanban or SRE practices are more appropriate.
- Do not present Tuckman Markov transition probabilities as empirically validated data — they are illustrative structural models only.
- Do not skip Definition of Done enforcement — accepting partial sprint completion creates invisible technical debt and invalidates velocity tracking.
- Do not use the blueprint formula n* = sqrt(2p/c) — this is dimensionally incorrect; always derive n* = p/c from the T(n) formula.
- Do not assume Normal distribution for daily throughput simulation — use empirical bootstrap; Normal fails due to bimodal zero-mass on non-working days.
- Do not commit to P50 forecast with external stakeholders — always use P85 for stakeholder commitments.

---

## Output Expectations

- Sprint capacity calculations with formula, worked example, and 95% bootstrap confidence interval (using M3 derivation).
- Monte Carlo forecast output showing P50, P85, and P95 with interpretation guidance.
- WSJF-ordered backlog with CoD and Job_Size columns populated (using M2 formula).
- DoD scoring with AHP-weighted criteria and CR < 0.10 consistency verification (using M4 derivation).
- Scrum of Scrums scaling recommendation with n* derivation shown (using M5 formula).
- India-specific timing and attrition adjustments applied when team is India-based or India-US distributed.
- All formulas labelled with their M-section origin for traceability.

---

## Skill Scope

This skill covers: Scrum framework mechanics (roles, artifacts, events, values), sprint capacity planning with bootstrap CI, velocity probability modeling, WSJF backlog prioritization, Definition of Done AHP scoring, Monte Carlo release forecasting, and Scrum of Scrums / LeSS / SAFe overview with coordination overhead mathematics.

This skill does NOT cover: Kanban flow metrics and CFD analysis (see agile-metrics-core), Jira / Azure DevOps tooling configuration (see jira-devops-tooling-core), team psychological safety and Tuckman stage assessment (see agile-team-health-core), or business development and revenue forecasting (see sales-pipeline-core, revenue-pricing-core).

---

## Version

1.0.1 — Added Anti-Patterns to Avoid: P50-only reporting, parametric throughput fitting, dropping zero-throughput days, velocity point estimates, partial AC/DoD completion, mid-release sprint-length changes, unagreed scope addition, sprint extension over renegotiation, past-optimum scaling, ungrounded impediment triage
1.0.0 — Domain 41: Agile Business & Revenue Intelligence initial release (2026-05-17)
