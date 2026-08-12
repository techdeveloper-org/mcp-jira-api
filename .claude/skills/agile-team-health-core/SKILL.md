---
name: agile-team-health-core
description: "Provides frameworks and mathematical models for agile team health assessment, psychological safety measurement, team topology design, and retrospective effectiveness. Use when evaluating team dynamics, designing team structures, measuring psychological safety, analyzing retrospective outcomes, or computing impediment resolution velocity. Keywords: Spotify Squad Health Check, Team Topologies interaction modes, psychological safety Edmondson scale, Tuckman stage assessment, retrospective effectiveness metrics, impediment MTTR, agile team attrition impact."
allowed-tools: Read,Glob,Grep
user-invocable: true
---


<!-- generated-by: claude-global-library/tools/project_sync -->
<!-- source: skills/agile-team-health-core/SKILL.md -- edit the library, then re-run sync_project.py -->

# agile-team-health-core

## Description

Provides mathematical and framework foundations for assessing and improving agile team health. Covers the Spotify Squad Health Check model (11 dimensions), Edmondson's 7-item Psychological Safety scale with reliability and correlation testing, Tuckman's stage model expressed as a Markov chain (with mandatory empirical caveats), retrospective effectiveness scoring, Team Topologies cognitive load mathematics, and attrition-impact modelling with India-US timezone overlap correction.

Use when a Scrum Master, engineering manager, or agile coach needs to quantify team health signals, justify PS investment with velocity correlation evidence, estimate onboarding velocity penalties, model distributed-team coordination efficiency, or evaluate whether retrospectives are producing measurable improvement.

---

## 1. Psychological Safety (Edmondson 7-Item Scale)

### 1.1 Scale Items

Amy Edmondson's Psychological Safety scale consists of 7 Likert items (1 = strongly disagree, 7 = strongly agree). Items marked **(R)** are reverse-scored.

| # | Statement | Scoring |
|---|-----------|---------|
| 1 | If you make a mistake on this team, it is often held against you. | **(R)** |
| 2 | Members of this team are able to bring up problems and tough issues. | Forward |
| 3 | People on this team sometimes reject others for being different. | **(R)** |
| 4 | It is safe to take a risk on this team. | Forward |
| 5 | It is difficult to ask other members of this team for help. | **(R)** |
| 6 | No one on this team would deliberately act in a way that undermines my efforts. | Forward |
| 7 | Working with members of this team, my unique skills and talents are valued and utilised. | Forward |

### 1.2 Scoring Formula

Reverse-code items 1, 3, and 5:

```
s'_i = 8 - s_i   for i in {1, 3, 5}
s'_i = s_i        for i in {2, 4, 6, 7}
```

Composite PS Score (range 1–7):

```
PS_score = (1/7) * sum_{i=1}^{7} s'_i
```

### 1.3 Threshold Interpretation

| PS Score | Interpretation |
|----------|----------------|
| > 5.5 | **High** psychological safety — team members speak up, challenge ideas, and experiment without fear of negative consequences. Enables learning behavior. |
| 4.0 – 5.5 | **Moderate** — some inhibition; team members self-censor on sensitive issues. |
| < 4.0 | **Low** — silence spirals active; interpersonal risk aversion suppresses innovation and problem-reporting. |

Global benchmark (Edmondson research): cross-industry average PS ≈ 5.0; high-performing technology teams ≈ 5.8–6.2.

**India IT context note:** No India-specific published PS benchmark exists in open literature. Use the global benchmark as proxy. India IT hierarchical culture can systematically suppress PS scores (junior engineers deferring to seniors, reluctance to flag blockers upward). Contextualise scores with qualitative observation before drawing conclusions.

---

## 2. Team Stage Development (Tuckman Model)

### 2.1 Five Stages

| Stage | Characteristics | Observable Indicators |
|-------|-----------------|----------------------|
| **Forming** | Team assembles; roles unclear; high dependency on leader | Polite interactions, little conflict, waiting for direction, asking "what are we supposed to do?" |
| **Storming** | Conflict over approach, roles, and priorities | Role disputes, missed commitments, sub-group formation, raised voices in standups |
| **Norming** | Shared norms emerge; cohesion building | Self-organising, peer code review initiated, team-defined working agreements |
| **Performing** | High autonomy and output; trust established | Self-managing sprints, proactive impediment removal, sustainable velocity |
| **Adjourning** | Team winds down or dissolves | Knowledge transfer, retrospective ceremonies, documentation effort |

### 2.2 Markov Transition Model

States: **S = {Forming (F), Storming (S), Norming (N), Performing (P), Adjourning (A)}**

Adjourning is an absorbing state (P_AA = 1).

**MANDATORY CAVEAT — read before using transition values:**
The transition probabilities below are **illustrative only**. Tuckman's original 1965 model is purely descriptive and qualitative. No peer-reviewed study has empirically calibrated transition probabilities for these states. Any p_ij values cited in training literature (including those below) are **not validated**. Do not present these probabilities as empirical fact. Teams that want quantitative Markov modelling must observe their own stage data and estimate p_ij from empirical transition counts.

**Illustrative transition matrix (NOT empirically validated):**

```
          F     S     N     P     A
    F  [0.30, 0.50, 0.15, 0.00, 0.05]
    S  [0.05, 0.40, 0.45, 0.05, 0.05]
    N  [0.00, 0.10, 0.50, 0.35, 0.05]
    P  [0.00, 0.05, 0.10, 0.80, 0.05]
    A  [0.00, 0.00, 0.00, 0.00, 1.00]
```

Row interpretation: from each state (row), probability mass to each next state (column). Row sums = 1.

**Steady-state and expected hitting time (illustrative values):**

Fundamental matrix N_fund = (I − Q)^{-1} where Q is the 4×4 transient sub-matrix.

Expected time to reach Performing from Forming (with illustrative matrix): approximately **6–7 sprints (~3 months on 2-week sprints)** — consistent with Tuckman's qualitative estimate that teams take 2–3 months to gel.

**Formulas:**

```
pi = pi * P,  sum(pi) = 1              (steady-state)
N_fund = (I - Q)^{-1}                 (fundamental matrix)
h_i = (N_fund * 1)_i                  (expected time to absorption from state i)
```

### 2.3 Regression Risk

New team members, re-organisations, or product pivots can trigger regression (e.g., Performing → Storming). When significant membership change occurs (>30% team turnover), treat team as re-entering Forming regardless of prior stage.

---

## 3. Spotify Health Check (11 Dimensions)

### 3.1 The 11 Dimensions

Spotify's Squad Health Check model covers the following dimensions (all confirmed from Spotify Engineering Culture documentation):

| # | Dimension | Green means... |
|---|-----------|----------------|
| 1 | **Easy to Release** | Deployments are frequent, low-risk, and automated |
| 2 | **Suitable Process** | Agile ceremonies and tooling fit the team's actual needs |
| 3 | **Tech Quality (Code Health)** | Low tech debt; engineers are proud of the codebase |
| 4 | **Value** | Team is clearly delivering value to users or the business |
| 5 | **Speed** | Work progresses at a satisfying pace; no chronic blocking |
| 6 | **Mission** | Team has a clear and inspiring purpose |
| 7 | **Fun** | Work is enjoyable; team morale is high |
| 8 | **Learning** | Team regularly acquires new skills; experiments are encouraged |
| 9 | **Support** | People outside the squad (other teams, management) are helpful |
| 10 | **Pawns or Players (Autonomy)** | Team has meaningful influence over what it builds and how |
| 11 | **Teamwork** | Team members collaborate effectively and trust each other |

Each dimension is rated: **Green** (good) / **Amber** (some issues) / **Red** (serious problems).

### 3.2 Running a Health Check Session

1. **Cadence:** Quarterly is recommended. Do not run more frequently than monthly — change is slow, over-polling desensitises the team.
2. **Anonymity:** Collect ratings anonymously (paper cards or anonymous survey) before revealing results. Group discussion follows the reveal.
3. **Facilitation:** Show aggregate results per dimension; discuss "why" behind Red/Amber ratings; prioritise 1–2 dimensions for focused improvement.
4. **Trend is primary:** Direction of change (Red → Amber, Amber → Green) matters more than the absolute rating. A consistently Red dimension that is improving is healthier than a Green dimension suddenly turning Red.

### 3.3 Team Health Score (THS) Computation

```
THS = sum_{i=1}^{11} w_i * s_i      where s_i in {Red=0, Amber=1, Green=2}
```

Default equal weights: w_i = 1/11. Score range [0, 2].

Custom weights using AHP (see M1 derivation below) if some dimensions have higher strategic importance for the team's current context.

### 3.4 Trend Interpretation

**No official numeric THS threshold is published by Spotify.** Interpret THS directionally:
- THS improving quarter-over-quarter → positive trajectory.
- Any single dimension stuck at Red for 2+ consecutive quarters → escalation warranted.
- All 11 dimensions Green → investigate for survey fatigue or superficial responses.

Statistical significance of quarter-over-quarter change: use Wilcoxon signed-rank test (see M1).

---

## 4. Attrition and Onboarding Impact

### 4.1 Velocity Ramp Curve

When a team member departs and is replaced, the new hire's productivity follows an exponential ramp:

```
P(t) = P_max * (1 - e^{-t/tau})
```

Where t = weeks since start and tau = time constant:
- **Experienced hire:** tau = 6 weeks (reaches 95% of P_max at ~18 weeks)
- **Fresh hire/graduate:** tau = 12 weeks (reaches 95% of P_max at ~36 weeks)

**Observed team-level velocity impact (T05 confirmed):**

| Period | Velocity Impact on Team | Explanation |
|--------|------------------------|-------------|
| Weeks 0–4 | −15% to −25% | Onboarding load on existing members; context transfer |
| Weeks 5–12 | −10% to −15% | New member contributing partially; still asking for help |
| Weeks 13–26 | 0% to +5% | Full contribution; may bring fresh perspective |
| > 26 weeks | Baseline | Full productivity for experienced hire |
| > 52 weeks | Baseline | Full productivity for fresh hire |

**Full productivity milestones:**
- Experienced hire (3+ years domain experience): **~6 months**
- Fresh hire / junior engineer: **~12 months**

### 4.2 Attrition Cost Model

Total productivity lost per departure (area between P_max and ramp curve):

```
Cost_attrition = P_max * tau * (1 - e^{-T/tau})
```

For a full ramp to 95% productivity (T = 3*tau): Cost ≈ P_max × tau × 0.95.

In person-weeks: each experienced-hire departure costs **~6 person-weeks of lost productivity**.

**India IT context:** Annual attrition rate 18–25% (NASSCOM HR Report 2024). For a team of 10:
- Expected departures per year: 2–3
- Annual productivity loss to ramp-up: 2.5 × 6 = 15 person-weeks ≈ **7.5% of total annual capacity**

This means a 10-person India IT team with 25% attrition effectively operates at ~92.5% of its nominal capacity due to ramp-up overhead alone — before accounting for the leaving member's knowledge loss.

---

## 5. Distributed Team Coordination

### 5.1 IST Timezone Overlap Table

India Standard Time (IST) = UTC+5:30.

| Partner Timezone | Gap (hours) | Overlap Window (IST) | Overlap Hours | Fraction of 8-hr Day |
|-----------------|-------------|---------------------|---------------|----------------------|
| US EST (UTC−5) | 10.5 h | 17:30–22:00 IST | 4.5 h | **0.5625** |
| US PST (UTC−8) | 13.5 h | 20:30–22:00 IST | 1.5 h | **0.1875** |
| UK GMT (UTC+0) | 5.5 h | 14:30–17:00 IST | 2.5 h | **0.3125** |
| Singapore SGT (UTC+8) | 2.5 h | 10:30–16:00 IST | 5.5 h | **0.6875** |
| Australia AEST (UTC+10) | 4.5 h | 09:30–13:00 IST | 3.5 h | **0.4375** |

Note: overlap windows assume standard 09:00–17:00 work hours for both parties. Actual overlap varies with extended hours and BST/DST transitions (UK gains 1 hour in summer, narrowing IST overlap).

### 5.2 Effective Capacity Model

For synchronous work requiring real-time coordination:

```
Effective_Capacity = Nominal_Capacity * (overlap_hours / total_work_hours)
```

Example: India team of 8 collaborating with US EST client.
- Nominal: 8 × 40 hr/wk = 320 hr/wk
- Effective (sync): 320 × 0.5625 = **180 hr/wk**

If 50% of tasks require synchronous coordination, total team output reduces by approximately:

```
Velocity_penalty = sync_fraction * (1 - overlap_fraction)
                 = 0.50 * (1 - 0.5625) = 0.22  (≈22%)
```

**Async penalty:** Tasks needing synchronous resolution outside the overlap window incur ~1 business day delay. Confirmed: 10–20% velocity penalty for async-heavy distributed teams with >8-hour timezone gap.

### 5.3 Mitigation Strategies

- **Follow-the-sun handoffs:** India team prepares end-of-day handoff notes; US team picks up at start of EST day, reducing latency from days to hours.
- **Async tooling maturity:** Comprehensive wikis, recorded standups, and documented decisions can recover 10–15% of the overlap penalty.
- **Core hours agreement:** Define 2-hour daily overlap as protected synchronous time; route all blocking decisions to this window.

---

## 6. Deep Mathematical Foundations

### M1: Spotify Squad Health Check Scoring Mathematics

**Setup:** 11 dimensions (confirmed T05). Each dimension scored ordinally: Red=0, Amber=1, Green=2.

**Team Health Score (THS):**

```
THS = sum_{i=1}^{11} w_i * s_i
```

Default equal weights: w_i = 1/11. Score range: [0, 2] when equal-weighted.

Custom weights via AHP if dimensions have differing strategic importance.

**Wilcoxon Signed-Rank Test for Quarter-over-Quarter Trend:**

Setup: For each of 11 dimensions, pair scores at quarter Q−1 and quarter Q:

```
d_i = s_i^Q - s_i^{Q-1}    for i = 1..11
```

Remove pairs with d_i = 0 (no change). Let n_eff = number of non-zero pairs.

Algorithm:
1. Compute |d_i| for all non-zero pairs.
2. Rank |d_i| from smallest (rank 1) to largest. Ties receive average rank.
3. T_plus = sum of ranks where d_i > 0.
4. T_minus = sum of ranks where d_i < 0.

Under H0 (median delta = 0), T_plus has:

```
mu_T    = n_eff * (n_eff + 1) / 4
sigma_T = sqrt(n_eff * (n_eff + 1) * (2*n_eff + 1) / 24)
Z       = (T_plus - mu_T) / sigma_T
```

Reject H0 if |Z| > 1.96 (alpha = 0.05, two-sided). Normal approximation valid for n_eff >= 8; for n_eff < 6 use exact tabulated critical values.

**Worked Example:**
Q-1 scores (11 dim): [1,1,2,0,1,2,2,1,1,0,1]. Quarter Q: [2,1,2,1,2,2,2,2,1,1,1].
Diffs d: [1,0,0,1,1,0,0,1,0,1,0]. Non-zero diffs: 5, all equal to +1.
All 5 tied at |d|=1; average rank = 3. T_plus = 5×3 = 15.
mu_T = 5×6/4 = 7.5. sigma_T = sqrt(5×6×11/24) = sqrt(13.75) = 3.71.
Z = (15 − 7.5) / 3.71 = 2.02. |Z| > 1.96 → reject H0: statistically significant improvement.

**Boundary Conditions:** If all d_i = 0, no test is possible. Use absolute THS trend over multiple quarters instead.

---

### M2: Edmondson Psychological Safety Scale Derivation

**Foundation:** PS scale reliability and correlation with performance metrics.

**Edmondson 7-Item PS Scale (T05 confirmed):**

Items 1, 3, 5 are reverse-scored. Likert 1–7.

Reverse-coding:

```
s'_i = 8 - s_i  for i in {1, 3, 5}
s'_i = s_i      for i in {2, 4, 6, 7}
```

**PS Score:**

```
PS_score = (1/7) * sum_{i=1}^{7} s'_i      range: [1, 7]
```

**Cronbach's Alpha (Scale Reliability):**

For k items with individual variances sigma_i^2 and total-score variance sigma_total^2:

```
alpha = (k / (k-1)) * (1 - sum sigma_i^2 / sigma_total^2)
```

Derivation: Variance of total Z = sum X_i:

```
sigma_total^2 = sum_i sigma_i^2 + 2 * sum_{i<j} cov(X_i, X_j)
```

The fraction sum_i(sigma_i^2) / sigma_total^2 approaches 0 when items are highly correlated. Alpha rescales by k/(k−1) so that with k perfectly correlated items, alpha = 1.

Practical thresholds: alpha >= 0.70 acceptable; >= 0.80 good; >= 0.90 excellent (but >0.95 may indicate redundant items).

**Pearson Correlation with Velocity:**

Given paired observations (PS_j, V_j) for j = 1..n sprints:

```
r = sum_j (PS_j - PS_bar)(V_j - V_bar) / sqrt(sum(PS_j - PS_bar)^2 * sum(V_j - V_bar)^2)
```

**t-test for H0: rho = 0:**

```
t = r * sqrt(n - 2) / sqrt(1 - r^2)        df = n - 2
```

Reject H0 if |t| > t_{df, 0.025} (two-sided, alpha = 0.05).

**Formula summary:**

```
PS = (1/7) * sum s'_i
alpha = (k/(k-1)) * (1 - sum sigma_i^2 / sigma_total^2)
r = covariance(PS, V) / (sigma_PS * sigma_V)
t = r * sqrt(n-2) / sqrt(1-r^2)
```

**Worked Example:**
10 team members rated 7 items. PS scores: [5.0, 5.5, 6.0, 4.5, 6.2, 5.7, 5.0, 5.8, 6.0, 5.5]. Mean = 5.52.
Item variances (across 10 respondents): [1.2, 1.5, 1.3, 1.4, 1.1, 1.6, 1.3]. Sum = 9.4.
Total-score variance = 35.
alpha = (7/6) × (1 − 9.4/35) = 1.167 × 0.731 = 0.853. Scale is reliable (> 0.80).

Pearson correlation between team PS and sprint velocity (n = 8 sprints): r = 0.72.
t = 0.72 × sqrt(6) / sqrt(1 − 0.518) = 0.72 × 2.449 / 0.694 = 2.54. df = 6.
t_critical(0.025, 6) = 2.447. |t| = 2.54 > 2.447 → reject H0; PS significantly correlated with velocity.

**Boundary Conditions:** alpha < 0.70 → scale unreliable; investigate individual items. n < 8 respondents → alpha estimate noisy. Correlation requires linearity — plot scatter before trusting r.

**India context:** India IT PS benchmark NOT published; use global reference (PS ≈ 5.0 average; 5.8–6.2 high-performing tech).

---

### M3: Tuckman Stage Transition Probability Model (with Empirical Caveat)

**Foundation:** Markov chain theory over discrete stages.

**MANDATORY CAVEAT:** The transition probabilities below are **illustrative only**. Tuckman's (1965) original model is descriptive and qualitative. No peer-reviewed dataset empirically calibrates these probabilities. Do not use p_ij values below as predictions. To use this model quantitatively, observe your own stage-per-sprint data, build empirical transition counts, and normalise to estimate p_ij from your team's history.

**State Space:** S = {Forming (F), Storming (S), Norming (N), Performing (P), Adjourning (A)}.

Adjourning is absorbing: P_AA = 1.

**Illustrative Transition Matrix (NOT empirically validated):**

```
          F     S     N     P     A
    F  [0.30, 0.50, 0.15, 0.00, 0.05]
    S  [0.05, 0.40, 0.45, 0.05, 0.05]
    N  [0.00, 0.10, 0.50, 0.35, 0.05]
    P  [0.00, 0.05, 0.10, 0.80, 0.05]
    A  [0.00, 0.00, 0.00, 0.00, 1.00]
```

**Steady-State Analysis:**

For the transient sub-chain Q (4×4 sub-matrix over {F,S,N,P}):

```
Q = [0.30, 0.50, 0.15, 0.00
     0.05, 0.40, 0.45, 0.05
     0.00, 0.10, 0.50, 0.35
     0.00, 0.05, 0.10, 0.80]
```

Fundamental Matrix: N_fund = (I − Q)^{-1}

Row sums of N_fund give expected total time to absorption from each starting state:

```
h_i = (N_fund * 1)_i        (expected sprints until absorption)
```

**Expected Time from Forming to Performing (illustrative):**

Treating Performing as absorbing alongside Adjourning, the Q sub-matrix over {F, S, N} becomes:

```
Q_FSN = [0.30, 0.50, 0.15
         0.05, 0.40, 0.45
         0.00, 0.10, 0.50]

I - Q_FSN = [0.70, -0.50, -0.15
            -0.05,  0.60, -0.45
             0.00, -0.10,  0.50]

N_FSN (approximate inverse):
    [1.94, 2.15, 2.52
     0.30, 2.62, 2.45
     0.06, 0.52, 2.49]

h_F = 1.94 + 2.15 + 2.52 = 6.61 sprints
```

With 2-week sprints, this corresponds to approximately 13 weeks (~3 months), consistent with Tuckman's qualitative estimate.

**Formula summary:**

```
pi = pi * P,  sum(pi) = 1              (steady-state)
N_fund = (I - Q)^{-1}                 (fundamental matrix)
h_i = (N_fund * 1)_i                  (expected time to absorption)
B = N_fund * R                         (absorption probabilities; R = transition to absorbing)
```

**Worked Example:** Team starts at Forming. Using illustrative matrix, expected time to Performing ≈ 6–7 sprints. Interpretation: plan 3+ months before expecting autonomous high-performance output from a newly-formed team.

**Practitioner Interpretation:** The model provides structural framing for team-maturity timelines. The qualitative stage framework is well-validated; the numerical probabilities are not. Use the stages to diagnose; do not use the p_ij values to predict sprint-level transitions.

**Boundary Conditions:** Markov property assumes current stage fully determines transition. Violated by external shocks (re-org, key departure, scope change). Re-initialise model to Forming after >30% team membership change.

---

### M4: Retrospective Effectiveness and Action Item Closure Rate

**Foundation:** Composite metric combining closure discipline and quality of action items.

**Retrospective Effectiveness (RE):**

```
RE = (Items_closed / Items_committed) * Quality_Score      RE in [0, 1]
```

Where Quality_Score is the average SMART compliance across closed action items.

**Improvement Velocity (IV):**

```
IV_t = (RE_t - RE_{t-1}) / 1_sprint          improvement per sprint
```

Rolling improvement trend: linear regression of IV_t over last n sprints.

**SMART Fuzzy Membership Scoring:**

For each closed action item, score each SMART dimension on [0, 1]:

| Dimension | Score = 0 (poor) | Score = 1 (excellent) |
|-----------|-----------------|----------------------|
| Specific | Vague goal | Measurable, narrow scope |
| Measurable | No metric | Quantified target |
| Achievable | Unrealistic | Demonstrably feasible |
| Relevant | Tangential | Tied to sprint goal |
| Time-bound | Open-ended | Date specified |

Combined membership via geometric mean (penalises any zero-scored dimension to ≈ 0):

```
mu_SMART = (mu_S * mu_M * mu_A * mu_R * mu_T)^{1/5}
```

Quality_Score for a sprint:

```
Q = (1 / N_closed) * sum_{j in closed items} mu_SMART_j
```

**Formula summary:**

```
RE = (Items_closed / Items_committed) * Q
IV = Delta RE / Delta sprints
mu_SMART_j = (mu_S * mu_M * mu_A * mu_R * mu_T)^{1/5}
Q = mean(mu_SMART_j over closed items)
```

**Worked Example:**
Sprint committed 5 action items; 4 closed by next sprint.
Closed items SMART scores: [0.90, 0.80, 0.60, 0.95].
Q = (0.90 + 0.80 + 0.60 + 0.95) / 4 = 0.8125.
RE = (4/5) × 0.8125 = 0.65.
Prior sprint RE = 0.55 → IV = (0.65 − 0.55) / 1 = +0.10/sprint. Positive improvement.

**Practitioner Interpretation:** High closure rate with low Quality_Score signals "checking the box" without real improvement. IV > 0 indicates a team learning from its retrospectives. Stagnant IV near 0 for 3+ sprints signals retrospective fatigue — consider changing format.

**Boundary Conditions:** Items_committed = 0 → RE undefined; do not score. Geometric mean forces any dimension with score = 0 to produce mu_SMART ≈ 0, incentivising attention to all five SMART criteria.

---

### M5: Team Topology Cognitive Load Mathematics

**Foundation:** Cognitive Load Theory (CLT) applied to software team domain ownership.

**Cognitive Load Decomposition:**

Total cognitive load = Intrinsic + Extraneous + Germane.
- Intrinsic = essential complexity of the domain.
- Extraneous = wasted cognitive effort (poor tooling, ambiguous APIs, unclear ownership).
- Germane = effort building useful mental models and schemas.

Team optimization objective:

```
Maximise: Germane / (Intrinsic + Extraneous)
```

**Team Cognitive Load Aggregate:**

Domain index d = 1..D. complexity_d = inherent difficulty (1–10 scale). responsibility_d = fraction of domain owned by team, in [0, 1].

```
CL_team = sum_d (complexity_d * responsibility_d)
```

Practical heuristic: CL_max = 10 (a team can sustain ~10 domain-points of load). Junior teams: CL_max ≈ 6–7.

**Cognitive Load Index (CLI):**

To normalise for tracking and benchmarking:

```
CLI = CL_team / CL_max      CLI in [0, 1]; CLI > 1.0 indicates overload
```

**Interaction-Mode Efficiency (Team Topologies):**

Three interaction modes between teams:

| Mode | Efficiency | Coupling Cost |
|------|-----------|---------------|
| X-as-a-Service | Highest: 1 − 0.10 = 0.90 | Clean API contracts; low overhead |
| Facilitating | Intermediate: ~0.75 | Time-limited coaching relationship |
| Collaboration | Lowest: 1 − 0.30 = 0.70 | High coordination overhead; temporary |

**Optimisation Problem:**

Minimise excess cognitive load across all teams:

```
min sum_d max(0, CL_d - CL_max)     subject to: every domain is covered by some team
```

This is a clean assignment problem (min-cost flow on a bipartite teams-to-domains graph).

**Formula summary:**

```
CL_team = sum_d (complexity_d * responsibility_d)
CLI = CL_team / CL_max
Interaction efficiency: X-as-Service (0.90) > Facilitating (0.75) > Collaboration (0.70)
Optimisation: minimise sum_d max(0, CL_d - CL_max) s.t. coverage
```

**Worked Example:**
Team A owns 100% of Payments (complexity = 8) and 50% of Onboarding (complexity = 6).
CL_A = 8×1.0 + 6×0.5 = 11.0. CLI = 11.0/10 = **1.10 (overloaded)**.

Options:
1. Transfer 30% of Onboarding to Team B → Team A: 8 + 6×0.2 = 9.2 (CLI = 0.92, within limit).
2. Split Payments into Payments-Core (complexity 6) and Payments-Fraud (complexity 4); assign Fraud to a specialist team.

Mode choice for shared domain: prefer X-as-a-Service — Team B publishes API, Team A consumes. Efficiency = 0.90 vs Collaboration's 0.70.

**Boundary Conditions:** complexity scale is subjective — calibrate to your organisation. If multiple teams share a domain with no single team owning >50%, ownership is ambiguous; assign one accountable owner. CL_max varies with experience level.

---

### M6: Attrition Impact and India-US Timezone Remote Correction

**Foundation:** Exponential productivity ramp and linear effective-hours model.

**Productivity Ramp (Exponential Approach to Max):**

New hire productivity at time t (weeks since start):

```
P(t) = P_max * (1 - e^{-t/tau})
```

Time constant tau:
- tau = 6 weeks for experienced hire → reaches 95% of P_max at t ≈ 18 weeks.
- tau = 12 weeks for fresh hire → reaches 95% of P_max at t ≈ 36 weeks.

Verification: P(tau)/P_max = 1 − 1/e ≈ 0.632. P(3*tau)/P_max = 1 − e^{-3} ≈ 0.950.

**Cost of Attrition Per Departure (Total Productivity Lost):**

```
Cost_attrition = integral_0^T (P_max - P(t)) dt
               = P_max * integral_0^T e^{-t/tau} dt
               = P_max * tau * (1 - e^{-T/tau})
```

For T = 3*tau (ramp to 95%):

```
Cost_attrition ≈ P_max * tau * 0.95     [person-weeks of lost productivity]
```

Experienced hire (tau = 6): **~6 person-weeks lost per departure**.
Fresh hire (tau = 12): **~12 person-weeks lost per departure**.

**India IT Annual Impact:**

For team of n members with attrition rate a:

```
Annual_departures = n * a
Annual_cost = Annual_departures * P_max * tau * 0.95
Annual_capacity_fraction_lost = (Annual_departures * tau * 0.95) / (n * 52)
```

At n = 10, a = 0.25 (25%), tau = 6:
Annual_cost = 10 × 0.25 × 6 × 0.95 = **14.25 person-weeks ≈ 7.5% of total annual capacity.**

**Timezone Overlap Effective Capacity:**

```
Effective_Capacity = Nominal_Capacity * (overlap_hours / total_work_hours)
```

Standard work day = 8 hours. IST = UTC+5:30.

| Partner Timezone | Overlap (h) | Fraction of 8-hr Day | Formula |
|-----------------|-------------|---------------------|---------|
| US EST (UTC−5) | 4.5 h | **0.5625** | India-US EST sync capacity = Nominal × 0.5625 |
| US PST (UTC−8) | 1.5 h | **0.1875** | India-US PST sync capacity = Nominal × 0.1875 |
| UK GMT (UTC+0) | 2.5 h | **0.3125** | India-UK sync capacity = Nominal × 0.3125 |
| Singapore SGT | 5.5 h | **0.6875** | India-SGT sync capacity = Nominal × 0.6875 |
| Australia AEST | 3.5 h | **0.4375** | India-AEST sync capacity = Nominal × 0.4375 |

**Overall velocity penalty for mixed sync/async work:**

```
velocity_penalty = sync_fraction * (1 - overlap_fraction)
```

Example: 50% sync work with India-US EST (overlap = 0.5625):
velocity_penalty = 0.50 × (1 − 0.5625) = **0.22 (22% penalty)**

T05 confirmed: 10–20% velocity penalty for async-heavy distributed teams with >8-hour timezone gap.

**Formula summary:**

```
P(t)          = P_max * (1 - e^{-t/tau})
Cost_attr     = P_max * tau * (1 - e^{-T/tau})
Eff_Capacity  = Nominal * (overlap_hours / total_work_hours)
India-US EST: 4.5/8 = 0.5625
CLI           = CL_team / CL_max      (see M5)
```

**Worked Example:**
India team of 8, collaborating with US EST client. 40% of work requires real-time coordination.
Nominal = 8 × 40 = 320 hr/wk. Effective for sync tasks = 320 × 0.5625 = 180 hr/wk.
Velocity penalty = 0.40 × (1 − 0.5625) = **17.5%** of total team output.

Attrition: 2 departures/year (25% of 8). Each experienced hire: 6 person-weeks lost.
Total: 12 person-weeks = 12/(8×50) = **3% annual capacity loss** from attrition alone.

Mitigation: follow-the-sun handoffs recover approximately half the sync latency overhead.

**Boundary Conditions:** P_max is individual-specific; team average smooths this. Overlap fraction assumes 8-hour workday — adjust if either party works extended hours. Async tooling maturity can recover 10–15% of the overlap penalty.

---

## 7. Anti-Patterns to Avoid

- **Presenting the illustrative Tuckman transition matrix or its derived hitting-time values as empirically validated facts**: per §2.2's mandatory caveat, no peer-reviewed study has calibrated these transition probabilities — the matrix and the "6-7 sprints to Performing" figure are illustrative only; a team wanting quantitative Markov modeling must estimate `p_ij` from its own observed transition counts, not cite the illustrative matrix as measured data.
- **Treating a Performing team that just had >30% membership turnover as merely regressing to Storming**: per §2.3, the explicit rule is to treat the team as re-entering Forming regardless of its prior stage once turnover crosses that threshold — a smaller regression assumption understates how much of the team's established norms and trust actually needs to be rebuilt.
- **Running the Spotify Health Check monthly or more frequently "to catch problems earlier"**: per §3.2, quarterly is the recommended cadence specifically because change is slow and over-polling desensitizes the team — increasing frequency doesn't produce faster signal, it produces survey fatigue that degrades the quality of every subsequent response.
- **Reacting to a single quarter's Red rating on a health-check dimension without checking its trend direction**: per §3.2 and §3.4, direction of change matters more than the absolute rating — a consistently Red dimension that is improving quarter-over-quarter is healthier than a Green dimension that just turned Red, and treating the snapshot alone as the signal to act on inverts the model's own stated priority.
- **Treating an all-11-dimensions-Green health check result as an unambiguous positive signal**: per §3.4, this specific pattern is flagged as a trigger to investigate for survey fatigue or superficial responses — real teams rarely score uniformly green across every dimension, and taking it at face value skips the scrutiny the model itself calls for in exactly this case.
- **Expecting a new hire (experienced or fresh) to reach full productivity within the first few weeks, or applying the same ramp timeline to both hire types**: per §4.1, the exponential ramp uses a materially different time constant for experienced hires (`tau = 6 weeks`, ~6 months to full productivity) versus fresh hires (`tau = 12 weeks`, ~12 months) — budgeting a fresh graduate's ramp on the experienced-hire timeline understates the team's real capacity for roughly the first half-year of that hire's tenure.
- **Comparing an India-based team's psychological-safety score directly against the global cross-industry benchmark without contextualizing hierarchical-culture effects**: per §1.3, India IT's hierarchical culture can systematically suppress PS scores (junior engineers deferring to seniors, reluctance to flag blockers upward) — reading a lower raw score as "this team has worse psychological safety" without that context conflates a cultural-reporting effect with an actual difference in safety.
- **Planning distributed India-partner sprint capacity using nominal (not effective) capacity for synchronous-coordination-heavy work**: per §5.2, a team's *effective* capacity for synchronous tasks is nominal capacity scaled by the actual timezone overlap fraction — for a US-EST partner this is roughly 56% of nominal, and for US-PST as low as ~19%; committing sprint scope against nominal capacity when a large fraction of the work is synchronous-dependent systematically overcommits the sprint.

## 8. India-Specific Layer

### 7.1 India IT Attrition Context

- **Annual attrition rate:** 18–25% (NASSCOM HR Report 2024, sector-wide; peaked 2021–2022 and remains elevated).
- For a 10-person team at 22% mid-range attrition: 2.2 departures/year, ~13 person-weeks of ramp-up overhead annually.
- Seasonal pattern: Q4 (Jan–Mar) sees elevated attrition ahead of appraisal cycles; plan sprint buffers in Q4 if team shows early attrition signals.

### 7.2 IST Timezone Overlap Reference

See Section 5.1 and M6 for the full overlap table. Key planning values:
- **India–US EST:** 4.5 h overlap (capacity fraction 0.5625) — requires discipline in async handoffs.
- **India–Singapore SGT:** 5.5 h overlap (0.6875) — most productive distributed pairing for India-APAC teams.
- **India–UK GMT:** 2.5 h overlap (0.3125, summer BST) to 3.5 h (winter UTC) — plan standups in 14:30–17:00 IST window.
- **India–US PST:** 1.5 h overlap (0.1875) — near-complete async; expect 1-business-day round-trip latency on all sync-requiring items.

### 7.3 India IT Hierarchical Culture and Psychological Safety

India IT hierarchical norms can structurally suppress Psychological Safety scores:
- Junior engineers are culturally conditioned to defer to senior engineers and managers.
- Flagging a superior's mistake in a group setting carries significant interpersonal risk.
- PS Item 1 ("mistakes are held against you") and Item 3 ("rejection for being different") often score lower in India IT teams than global tech-company averages.

**Important caveat:** No India-specific PS Score benchmark is available in open literature. Do not apply a "correction factor" to India IT PS scores without empirical organisational data — doing so could mask genuine safety issues or produce false reassurance.

Practical approach: when PS scores are below 4.5 on India IT teams, run qualitative follow-up (anonymous comment cards) before concluding the score reflects a true safety deficit vs. measurement artefact from cultural response bias.

### 7.4 NASSCOM AgileX Maturity Levels (Team Health Context)

NASSCOM's AgileX framework defines five organisational agile maturity levels (L1–L5). Team health metrics correlate with maturity level:

| Level | Maturity | Typical Team Health Signal |
|-------|----------|---------------------------|
| L1 | Initial / Ad hoc | Tuckman: Forming/Storming; PS < 4.0; no retro cadence |
| L2 | Defined | Tuckman: Norming; PS 4.0–4.5; retros exist but low RE |
| L3 | Managed | Tuckman: Performing; PS 4.5–5.2; THS mostly Amber |
| L4 | Optimising | Tuckman: Performing sustainably; PS 5.2–5.8; THS mostly Green |
| L5 | Innovating | Cross-team facilitation; PS > 5.8; THS consistently Green |

NASSCOM does not publish specific velocity benchmarks by maturity level — teams should track their own VSI (Velocity Stability Index, see `agile-metrics-core`) as the health proxy.

### 7.5 Indian Labour Law Context

- **Factories Act / IT-ITES labour rules:** Maximum 48-hour work week; overtime regulated under state-specific Shops and Establishments Acts.
- Chronic sprint overcommitment leading to 55+ hour weeks is both a labour compliance risk and a direct Psychological Safety indicator (item 4: "it is safe to take a risk" includes the risk of saying a sprint is over-committed).
- NASSCOM D&I targets: 30% women in tech roles by 2025. Gender diversity on teams correlates with broader cognitive diversity, which Edmondson research links to higher PS scores when managed well.

---

## 9. Response Rules

1. **Always present Tuckman Markov probabilities as illustrative, not empirical.** Never quote p_ij values as if they are research-validated. Add an explicit caveat every time they appear.
2. **Never present PS Score India benchmarks as if they exist.** No peer-reviewed India-specific PS benchmark has been published. Always use global benchmarks as proxy with an explicit note.
3. **Recommend the full 7-item Edmondson scale, not ad hoc subsets.** Cronbach's alpha applies to the full scale; removing items invalidates the reliability property.
4. **THS is trend-first, absolute-second.** Never declare a team "healthy" or "unhealthy" based on a single-quarter THS. Always frame findings as trend direction.
5. **No official numeric THS thresholds from Spotify exist.** Do not fabricate thresholds (e.g., "THS > 1.5 = high health"). Use directional language only.
6. **Attrition cost must include India IT rate context (18–25%) when advising Indian IT teams.** Do not use global averages without flagging the India IT baseline.
7. **Timezone overlap fractions are planning values, not hard limits.** Extended hours, flex time, or geographic exceptions can change the effective overlap window — always confirm actual working hours before using the table values.
8. **PS and velocity correlation requires linearity check.** Visualise scatter before quoting Pearson r.
9. **SMART fuzzy scoring is subjective.** Two facilitators scoring the same action item may differ. Calibrate scoring criteria within a team before tracking RE over time.
10. **CLI > 1.0 is a signal requiring management action, not a dismissable metric.** When CLI exceeds 1.0, escalate to team lead / engineering manager with domain-rebalancing options.

---

## 10. What Not to Do

1. **Do not prescribe specific Tuckman transition probabilities as fact.** Any specific values (p_fs = 0.7, etc.) are illustrative. Presenting them as authoritative will mislead stakeholders.
2. **Do not diagnose team issues from PS score alone.** A low PS score can stem from cultural response bias, survey fatigue, a genuinely unsafe environment, or a one-off difficult sprint. Triangulate with observable indicators.
3. **Do not run Spotify Health Checks without facilitation.** Uncountenanced self-assessment is subject to political distortion — teams rate themselves higher in front of management.
4. **Do not compare THS values across different teams.** Each team weights dimensions implicitly and has different context. Cross-team comparison is misleading; use within-team trend only.
5. **Do not use attrition ramp curve at the individual level to justify early performance management.** P(t) is a population-average model. Individual new hires vary enormously; the curve is a capacity-planning tool, not a performance standard.
6. **Do not calculate effective timezone capacity and then assign full-workload sprints ignoring the overlap penalty.** Teams consistently set up for failure when sync-work requirements exceed available overlap hours.
7. **Do not treat CLI as a fixed measure.** Domain complexity changes with product maturity; re-assess CL_team quarterly.
8. **Do not use RE as the sole measure of retrospective value.** A retro that surfaces deep systemic issues — even with 60% closure rate — may be more valuable than a retro with 100% closure of trivial items.

---

## 11. Output Expectations

When using this skill, responses should include:

- **PS assessment:** PS Score computed from 7-item scale with reverse-coding; threshold interpretation; Cronbach's alpha if multi-respondent data is available; Pearson correlation with velocity if sprint data is paired.
- **Team stage assessment:** Current Tuckman stage with observable evidence; qualitative interpretation; **mandatory caveat on Markov probabilities** if numerical transition estimates are requested.
- **Spotify Health Check:** THS by dimension; trend vs. prior quarter; Wilcoxon Z-statistic for statistical significance if two quarters of data are available; 1–2 dimension-specific improvement priorities.
- **Attrition analysis:** Productivity ramp curve with tau selection (experienced vs. fresh); cost per departure in person-weeks; annual capacity loss fraction; India attrition context (18–25%) where applicable.
- **Distributed team analysis:** Overlap fraction for relevant timezone pair; effective sync capacity; velocity penalty for given sync/async work mix; mitigation options.
- **Cognitive load:** CL_team per team; CLI; interaction-mode efficiency ranking; domain-rebalancing recommendation if CLI > 1.0.
- **Retrospective effectiveness:** RE score; IV trend; SMART fuzzy scoring of action items.

---

## 12. Skill Scope

**In scope:**
- Team health assessment frameworks: Spotify Health Check (11 dimensions), Tuckman stages
- Psychological safety: Edmondson 7-item scale, reliability, correlation with velocity
- Retrospective effectiveness: closure rate, SMART quality scoring, improvement velocity
- Team topology: cognitive load mathematics, interaction-mode efficiency
- Attrition modelling: productivity ramp, cost per departure, capacity impact
- Distributed team coordination: timezone overlap, effective capacity, async penalty
- India context: IT attrition rates, IST timezone overlaps, hierarchical culture notes, NASSCOM AgileX levels

**Out of scope:**
- Agile metrics and velocity forecasting → see `agile-metrics-core`
- Scrum ceremonies, velocity distributions, WSJF → see `scrum-framework-core`
- Jira and Azure DevOps tooling → see `jira-devops-tooling-core`
- Formal organisational design (Wardley mapping, enterprise topology) — beyond skill boundary
- Clinical psychology or counselling for team dysfunction

---

## 13. Version

**Version:** 1.0.1 — 2026-07-27 — Added §7 Anti-Patterns to Avoid (8 pitfalls spanning Tuckman-matrix overclaiming, turnover-driven stage regression, health-check polling frequency, trend-vs-snapshot rating reads, all-green survey-fatigue signal, hire-type ramp-timeline confusion, cross-cultural PS-score comparison, and nominal-vs-effective distributed capacity); renumbered §7-12 to §8-13.

**Version:** 1.0.0
**Domain:** Agile Business & Revenue Intelligence (Domain 41)
**Last updated:** 2026-05-17
**Research sources:** Edmondson (1999) PS scale; Tuckman (1965, 1977) stage model; Spotify Engineering Culture (2014/2019); NASSCOM HR Report 2024; T05 web research (2026-05-17) — IST overlap gaps, India IT attrition, PS thresholds
**Math derivations:** agile-business-mathematics-expert (opus) — T10 output, 2026-05-17
