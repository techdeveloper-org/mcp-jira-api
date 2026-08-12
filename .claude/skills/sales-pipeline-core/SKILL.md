---
name: sales-pipeline-core
description: "Provides B2B sales pipeline mathematics including stage conversion modeling, MEDDIC/BANT qualification scoring, customer lifetime value computation, win rate logistic regression, and sales velocity optimization. Use when designing sales pipelines, forecasting revenue, computing deal probabilities, building quota models, or analyzing CRM pipeline health. Keywords: B2B sales pipeline stages, MEDDIC qualification scoring, customer lifetime value formula, win rate logistic regression, sales velocity formula, quota ramp mathematics, deal conversion probability."
allowed-tools: Read,Glob,Grep
user-invocable: true
---


<!-- generated-by: claude-global-library/tools/project_sync -->
<!-- source: skills/sales-pipeline-core/SKILL.md -- edit the library, then re-run sync_project.py -->

# sales-pipeline-core

## Description

Provides mathematical foundations for B2B sales pipeline management including Markov-chain stage conversion modeling, MEDDIC qualification scoring with logistic win-probability, customer lifetime value (CLV) in both geometric series and DCF forms, the four-factor sales velocity formula with elasticity analysis, win-rate logistic regression with Newton-Raphson MLE and Brier Score calibration, and quota ramp modeling with India enterprise deal-cycle lognormal distribution. Covers pipeline hygiene, CRM implementation guidance, Bayesian deal scoring, forecast accuracy, and India-specific seasonal, regulatory, and structural constraints.

---

## 1. Pipeline Funnel Architecture

### 1.1 Stage Definitions

A standard B2B pipeline passes opportunities through ordered stages, each with a conversion rate and expected hold time:

| Stage | Definition | Typical Hold Time | Typical Conversion to Next |
|---|---|---|---|
| Prospect / Lead | Outbound or inbound contact; no qualification yet | 1–2 weeks | 30–50% to MQL |
| MQL (Marketing Qualified Lead) | Marketing-qualified: ICP-fit, showed intent signal | 1–3 weeks | 35–55% to SQL |
| SQL (Sales Qualified Lead) | Sales-accepted: initial pain + budget + authority confirmed | 2–4 weeks | 40–60% to Opportunity |
| Opportunity | Full qualification complete; active pursuit underway | 4–12 weeks | 45–65% to Negotiation |
| Negotiation | Proposal exchanged; legal/commercial negotiation in progress | 2–6 weeks | 60–80% to Closed-Won |
| Closed-Won | Contract signed, PO issued | — | — |
| Closed-Lost | No-decision, competitor, or budget freeze | — | — |

### 1.2 Multi-Stage Bernoulli Conversion Model

Each stage transition is a Bernoulli trial with probability c_i (conversion rate for stage i). The probability of a lead converting to Closed-Won through all stages is:

```
P(Won | Lead) = c_MQL * c_SQL * c_Opp * c_Neg * c_Won_from_Neg
```

For a 5-stage path with c = (0.40, 0.50, 0.55, 0.70):
```
P(Won | Lead) = 0.40 * 0.50 * 0.55 * 0.70 = 0.077 (7.7% end-to-end win rate)
```

### 1.3 Pipeline Value and Coverage Ratio

Stage-weighted pipeline value:
```
Pipeline_Value = sum_i (N_i * ACV_i * c_i_to_won)
```

Where c_i_to_won is the cumulative conversion probability from stage i through to Closed-Won.

Pipeline Coverage Ratio (PCR):
```
PCR = Total_Pipeline_Value / Revenue_Target
```

Healthy threshold: **PCR >= 3.0**. Derivation: at overall win rate w = 33%, expected closed = pipeline * 0.33, so PCR = 1/w = 3. At w = 25%, PCR_min = 4.

### 1.4 Conversion Rate Tracking

Track conversion rates per stage using rolling 90-day cohorts:
```
c_i = Deals_exiting_stage_i_to_stage_{i+1} / Total_deals_entering_stage_i_in_period
```

Exclude deals still in stage (not yet resolved) from denominator to avoid survivor bias. Use 3-month rolling windows; recalibrate quarterly.

---

## 2. Sales Velocity Model

### 2.1 The Four-Factor Formula

Sales Velocity (SV) measures revenue produced per unit time:

```
SV = (N_opp × Win_Rate × ACV) / Sales_Cycle_Days
```

| Factor | Symbol | Definition | Unit |
|---|---|---|---|
| Opportunities | N_opp | Number of active open opportunities | count |
| Win Rate | WR | Fraction of closed deals that are won | decimal [0,1] |
| Average Contract Value | ACV | Mean deal size across closed-won deals | currency |
| Sales Cycle Days | Cycle | Mean days from opportunity creation to close | days |

Units of SV: currency per day. Annualize: SV_annual = SV * 365.

### 2.2 Factor Elasticity

Taking the natural log: ln(SV) = ln(N) + ln(WR) + ln(ACV) - ln(Cycle).

Each factor has unit elasticity: a 10% increase in N, WR, or ACV increases SV by 10%. A 10% reduction in Cycle_Days increases SV by 10%.

Practical lever ranking by cost-effectiveness:
1. **Cycle reduction** (process improvement: qualification speed, legal turnaround): cheapest, often 15–25% achievable.
2. **Win rate improvement** (coaching, competitive intelligence, reference customer program): moderate cost.
3. **ACV increase** (upsell, multi-year contracts, premium packaging): limited by market demand.
4. **Opportunity volume increase** (marketing investment): highest cost per additional opp.

### 2.3 Worked India SaaS Example

Sales team baseline:
- N = 50 open opportunities
- WR = 25%
- ACV = Rs 10,00,000 (Rs 10 lakh)
- Cycle = 90 days

```
SV = (50 * 0.25 * 10,00,000) / 90 = 1,25,00,000 / 90 = Rs 1,38,889/day
Annual run rate = Rs 5.07 Cr
```

Lever analysis (each +10%):
- +10% opportunities (N=55): SV -> Rs 1,52,778/day. +10%.
- +10% win rate (WR=0.275): SV -> Rs 1,52,778/day. +10%.
- +10% ACV (Rs 11L): SV -> Rs 1,52,778/day. +10%.
- -10% cycle (81 days): SV -> Rs 1,54,321/day. +11.1%.

To double SV: achieve ~25% improvement across three levers simultaneously (1.25^3 = 1.95x).

### 2.4 Pipeline Coverage Confidence Interval

When win rate is estimated from n historical deals, PCR target has uncertainty. Bootstrap 95% CI for required PCR:

```
For b = 1 to B = 1,000:
    WR_b = mean(Binomial(n_samples, WR_observed) / n_samples)
    PCR_min_b = 1 / WR_b
PCR_CI = [percentile(PCR_min_b, 2.5%), percentile(PCR_min_b, 97.5%)]
```

Example: WR observed = 25% from n=40 deals. PCR_min 95% CI: [2.4, 5.0]. Use PCR >= P75 of CI as conservative target.

---

## 3. CRM Pipeline Management

### 3.1 Stage Entry and Exit Criteria

Each stage requires explicit entry and exit criteria to prevent subjective inflation:

**SQL Entry Criteria (BANT minimum):**
- B — Budget: confirmed budget range or approved procurement pathway
- A — Authority: economic buyer identified and engaged
- N — Need: specific pain and business impact quantified
- T — Timeline: target go-live date within 12 months

**Opportunity Upgrade Criteria (MEDDIC):**
All 6 MEDDIC components partially populated; see Section 5 for scoring.

**Deal Stuck Rule:** Any deal in the same stage for > 1.5× typical hold time (see Section 1.1) is flagged as stale. Sales manager reviews in weekly pipeline call.

### 3.2 Deal Scoring in CRM

Implement Bayesian deal score as a custom field (0–100 scale, see Section 5). Color code:
- 75–100: Green — high confidence, advance to close plan.
- 50–74: Amber — qualified, needs specific next steps.
- 25–49: Red — at risk, executive sponsor or repricing needed.
- 0–24: Grey — disqualify or return to MQL.

### 3.3 Pipeline Hygiene Rules

1. **No deal enters Opportunity without MEDDIC score >= 40/60** (set threshold per org).
2. **Close date update policy:** Reps may not push close date more than once per quarter without manager approval.
3. **Stale deal policy:** Deals stuck > 1.5× typical hold are auto-marked at risk in CRM dashboard.
4. **ACV consistency:** ACV fields must be populated on entry to Opportunity; quotes must match ACV within 20%.
5. **Activity requirement:** At least one logged activity per 14 days per open deal; zero-activity deals flagged.

### 3.4 Forecast Categories

| Category | CRM Stage | Expected Close % | Used For |
|---|---|---|---|
| Commit | Negotiation | >= 75% | Weekly forecast; reps commit to these |
| Best Case | Opportunity or Negotiation | 40–74% | Upside scenario |
| Pipeline | SQL or Opportunity | 25–39% | Directional only |
| Omitted | Lead or MQL | < 25% | Not included in forecast |

Forecast roll-up: Sum(Deal_Value * Stage_Weight) = Weighted Pipeline Forecast.

---

## 4. Bayesian Deal Scoring

### 4.1 Conceptual Framework

Bayesian deal scoring updates the prior win probability for a deal as new evidence accumulates during the sales cycle.

**Three-Step Process:**

**Step 1 — Set Stage Prior:** Assign prior win probability based on CRM stage:
```
P_prior(stage) = historical_win_rate_from_stage
```
Example: Lead=5%, MQL=12%, SQL=25%, Opportunity=40%, Negotiation=65%.

**Step 2 — Likelihood Update from MEDDIC Score:** Compute MEDDIC (see Section 5.1). Use logistic model to compute likelihood ratio:
```
LR = P(MEDDIC_score | Win) / P(MEDDIC_score | Loss)
```

For the logistic model: LR = exp(beta_1 * MEDDIC_score) where beta_1 is the MEDDIC coefficient from fitted model (typically 0.05–0.15 per point).

**Step 3 — Posterior Win Probability:**
```
P_posterior = P_prior * LR / (P_prior * LR + (1 - P_prior))
```

This is Bayes' theorem applied with likelihood ratio.

### 4.2 CRM Implementation

Map CRM stage to prior probability table (calibrate from 18-month historical win rates). When deal enters a new stage, system auto-applies stage prior. When rep updates MEDDIC fields, system computes LR and updates posterior. Display P_posterior as deal score (0–100).

### 4.3 Worked Example

Deal currently at SQL stage. Stage prior: P_prior = 0.25 (25% win rate from SQL historically).
MEDDIC score submitted: 52/60 (high).
Logistic model: beta_1 = 0.06 per point.
LR = exp(0.06 * 52) = exp(3.12) = 22.6.

```
P_posterior = (0.25 * 22.6) / (0.25 * 22.6 + 0.75) = 5.65 / (5.65 + 0.75) = 5.65 / 6.40 = 0.883
```

Deal score: 88/100 (Green). High MEDDIC overrides the low-stage prior substantially.

---

## 5. MEDDIC Qualification Framework

### 5.1 Six-Dimension Scoring

MEDDIC is the industry-standard qualification framework for B2B enterprise sales:

| Dimension | Full Name | What It Assesses | Score Range |
|---|---|---|---|
| M | Metrics | Quantified business impact: cost savings, revenue uplift, time saved | 0–10 |
| E | Economic Buyer | Identified, engaged, and supportive economic decision-maker | 0–10 |
| D | Decision Criteria | Explicit selection criteria understood; product favorably mapped | 0–10 |
| D | Decision Process | Procurement steps, approval chain, legal review process understood | 0–10 |
| I | Identify Pain | Specific, quantified pain that product addresses | 0–10 |
| C | Champion | Internal advocate with influence, credibility, and motivation | 0–10 |

```
MEDDIC_Score = sum_{k=1}^{6} w_k * s_k        w_k = 1/6 (equal weights default)
MEDDIC_max = 60
```

Custom weights: organizations may weight E (economic buyer) and C (champion) at 1.5× others, normalizing sum to 1.

### 5.2 Score Interpretation

| Score Range | Qualification | Action |
|---|---|---|
| 50–60 | Fully qualified | Advance to close plan; commit resource |
| 35–49 | Partially qualified | Address specific weak dimensions |
| 20–34 | Under-qualified | Discovery calls to fill gaps; do not advance |
| 0–19 | Disqualify | Return to nurture or close-lost |

---

## 6. Quota and Forecast Analytics

### 6.1 Quota Attainment Distribution

Across a sales team, individual quota attainment A_i = Revenue_i / Quota_i is approximately lognormal:
```
A_i ~ LogNormal(mu_A, sigma_A^2)
```

Why lognormal: attainment is multiplicative (each rep's result is product of independent win/loss events), right-skewed (a few top performers far exceed quota), and bounded below at zero.

MLE fit: mu_A = mean(ln(A_i)), sigma_A^2 = var(ln(A_i)).

Median attainment = exp(mu_A). Mean attainment = exp(mu_A + sigma_A^2/2). P(attains quota) = P(A >= 1) = 1 - Phi((0 - mu_A) / sigma_A) = Phi(mu_A / sigma_A).

### 6.2 Pipeline Coverage Ratio Target

The 3x rule: pipeline must be 3× quarterly target to deliver quota at a 33% win rate.

More precisely, given win rate WR and pipeline PCR:
```
Expected_Revenue = PCR * Revenue_Target * WR
Coverage_needed_to_hit_target = 1 / WR
```

At WR = 25%: need PCR = 4×. At WR = 40%: need PCR = 2.5×. Adjust PCR target to rep-level WR.

**When to deviate from 3x:** Increase PCR target to 4–5× when: win rate is historically volatile (CV > 30%), deal sizes vary widely (CV of ACV > 50%), or India Q4 flush risk (all deals may close or fall simultaneously in March).

### 6.3 Forecast Accuracy Metrics

**Mean Absolute Percentage Error (MAPE):**
```
MAPE = (1/n) * sum |Forecast_t - Actual_t| / Actual_t * 100%
```
Target: MAPE < 15% at 30-day-out forecast for mature teams.

**Forecast Bias:** Mean(Forecast - Actual). Positive = over-forecasting; negative = under-forecasting.

**Prediction Interval:** Construct 80% CI for quarterly attainment using lognormal distribution of historical errors.

---

## 7. Deep Mathematical Foundations

### M1: Pipeline Stage Conversion and Funnel — Markov Chain

**State Space:** S = {Lead, MQL, SQL, Opp, Negotiation, Closed-Won, Closed-Lost}. Closed-Won and Closed-Lost are absorbing states.

**Transition Matrix P (7x7):** Each row sums to 1. Typical parameterization (calibrate from CRM data):
```
              Lead   MQL   SQL   Opp   Neg   Won   Lost
Lead       [ 0.50, 0.30, 0.00, 0.00, 0.00, 0.00, 0.20 ]
MQL        [ 0.00, 0.40, 0.35, 0.00, 0.00, 0.00, 0.25 ]
SQL        [ 0.00, 0.00, 0.35, 0.40, 0.00, 0.00, 0.25 ]
Opp        [ 0.00, 0.00, 0.00, 0.30, 0.45, 0.00, 0.25 ]
Negotiation[ 0.00, 0.00, 0.00, 0.00, 0.20, 0.60, 0.20 ]
Closed-Won [ 0.00, 0.00, 0.00, 0.00, 0.00, 1.00, 0.00 ]
Closed-Lost[ 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 1.00 ]
```

Self-loops (diagonal) represent staying in the same stage over one time-step (weekly cycle). Off-diagonal entries represent progression or loss.

**Q-Matrix (Transient Sub-Block, 5x5):**
```
Q = first 5 rows and columns of P (transient states: Lead, MQL, SQL, Opp, Negotiation)
```

**R-Matrix (Transient to Absorbing, 5x2):**
```
R = columns Won, Lost from rows Lead, MQL, SQL, Opp, Negotiation of P
```

**Fundamental Matrix:**
```
N = (I - Q)^{-1}
```
N_{ij} = expected number of periods spent in transient state j starting from transient state i before absorption.

**Absorption Probabilities:**
```
B = N * R
B_{i, Won} = probability of being absorbed into Closed-Won starting at state i
```

**Expected Revenue from Stage i with deal value v:**
```
E[Rev | start at i] = v * B_{i, Won}
```

**Pipeline Coverage Ratio:**
```
PCR = V / T
```
where V = total pipeline value, T = quarterly revenue target.

**Healthy threshold:** PCR >= 3.0 (T06 confirmed).

**Derivation:** At overall win rate w, expected closed = V * w. For expected closed = T: PCR = 1/w. At w = 33%: PCR = 3.0. At w = 25%: PCR = 4.0.

**Worked Example:** Deal worth Rs 1,00,00,000 (Rs 1 Cr) at SQL stage.

Using the transition matrix above: B_{SQL, Won} ≈ 0.30 (computed from N*R).

```
E[Rev | SQL] = 1,00,00,000 * 0.30 = Rs 30,00,000
```

For a sales rep with quarterly quota Rs 1 Cr: PCR = total pipeline / Rs 1 Cr. At PCR = 3, expect Rs 30L from SQL-stage deals at 30% absorption probability. PCR = 3–4 minimum.

**Calibration:** Estimate Q from CRM snapshots (quarterly stage transitions). Clean stale deals before fitting. Semi-Markov extension needed if deal-age influences transition probability (deals stuck > 6 months have lower win rate than fresh deals).

**India Values:** India enterprise B2B win rate: 20–35% IT services; 15–25% SMB SaaS (T06 training fallback). PCR mapping: w=0.25 → PCR_min=4; w=0.33 → PCR_min=3.

---

### M2: MEDDIC Qualification Score and Deal Win Probability

**MEDDIC Composite Score:**
```
MEDDIC = sum_{k=1}^{6} w_k * s_k          s_k in [0, 10]; w_k normalized to sum 1
```

**Logistic Model for Win Probability:**

Predictors: MEDDIC score, deal_size (log-scaled), cycle_days.
```
P(win | x) = sigma(beta_0 + beta_1 * MEDDIC + beta_2 * ln(deal_size) + beta_3 * cycle_days)
sigma(z) = 1 / (1 + e^{-z})
```

**MLE via Newton-Raphson (from M5 full derivation):**
```
grad l = X^T (y - p)
H = -X^T W X          W = diag(p_i * (1 - p_i))
beta^{k+1} = beta^k + (X^T W X)^{-1} X^T (y - p)
```

**ROC Curve and F1-Optimal Threshold:**

For decision threshold tau in [0,1]:
```
TPR(tau) = #{p_i >= tau, y_i = 1} / #{y_i = 1}       (sensitivity)
FPR(tau) = #{p_i >= tau, y_i = 0} / #{y_i = 0}       (1 - specificity)
Precision(tau) = #{p_i >= tau, y_i = 1} / #{p_i >= tau}
Recall(tau) = TPR(tau)
F1(tau) = 2 * Precision(tau) * Recall(tau) / (Precision(tau) + Recall(tau))
tau* = argmax F1(tau)     (grid search on [0, 1] step 0.01)
```

**Brier Score for Calibration:**
```
BS = (1/n) * sum (p_i - y_i)^2          BS in [0, 1]; < 0.25 is informative
```

If BS > 0.20: recalibrate via Platt scaling: p_calibrated = sigma(a * p_raw + b) (fit a, b on held-out set).

**Worked Example:** Logistic trained on 1,000 historical deals. Converged beta = (-3.2, 0.32, 0.18, -0.005) (coefficients for intercept, MEDDIC, ln(deal_size), cycle_days).

Coefficient interpretation:
- beta_MEDDIC = 0.32: each +1 MEDDIC point increases log-odds by 0.32 (odds ratio e^0.32 = 1.38, +38% per point).
- beta_cycle = -0.005: each additional day in pipeline reduces log-odds by 0.005 (deals get colder).

Prediction: MEDDIC=30, deal_size=Rs 50L, cycle_days=120:
```
log_odds = -3.2 + 0.32*30 + 0.18*ln(50,00,000) - 0.005*120
         = -3.2 + 9.6 + 0.18*15.42 - 0.6
         = -3.2 + 9.6 + 2.78 - 0.6 = 8.58
P(win) = sigma(8.58) ~ 0.9998
```

Note: beta_1 = 0.32 is illustrative; practical fits on B2B data typically yield beta_1 in [0.05, 0.15]. F1-optimal threshold typically tau* in [0.3, 0.5].

**Boundary Conditions:** Class imbalance (win rate << 50%): use weighted MLE or SMOTE oversampling. Multicollinearity (MEDDIC correlated with cycle_days): use L2 ridge regularization.

---

### M3: Customer Lifetime Value — Geometric Series and DCF Forms

**Setup:** Customer paying ARPU per month, gross margin GM, monthly churn ch (probability of cancellation per month), annual discount rate r.

Per-month margin contribution: m = ARPU * GM.

**Infinite-Horizon CLV (No Discount):**

Geometric series with ratio (1-ch):
```
CLV_inf_no_disc = m * sum_{t=0}^{inf} (1-ch)^t = m / ch        (geometric series limit, |1-ch| < 1)
```

**Infinite-Horizon CLV (With Monthly Discount r/12):**
```
CLV_DCF = m * sum_{t=1}^{inf} (1-ch)^t / (1 + r/12)^t
        = m * x / (1 - x)           where x = (1-ch) / (1 + r/12)
```

Algebraic simplification of (1-x):
```
1 - x = 1 - (1-ch)/(1+r/12) = (1+r/12 - 1 + ch) / (1+r/12) = (ch + r/12) / (1+r/12)
x / (1-x) = (1-ch) / (ch + r/12)
```

Therefore:
```
CLV_DCF = m * (1-ch) / (ch + r/12)
```

**Finite-Horizon CLV (T months):**
```
CLV_T = m * sum_{t=1}^{T} (1-ch)^t / (1+r/12)^t
      = m * x * (1 - x^T) / (1 - x)          where x = (1-ch) / (1+r/12)
```

**Sensitivity Analysis:**

Differentiate CLV_inf_no_disc with respect to ch:
```
dCLV / d_ch = -m / ch^2
```

Reducing churn from 5% to 4% (20% relative reduction) increases CLV by factor (1/0.04)/(1/0.05) = 25/20 = 1.25x (+25%). The quadratic denominator means small churn reductions have outsized CLV impact.

With discount:
```
d CLV_DCF / d_ch = -m * (1 + (1-ch)/(ch+r/12)) / (ch + r/12)
```

For ch=3%, r=12%: d CLV_DCF / d_ch ≈ -m * 25.25 / 0.04. At m=Rs 4,000/mo, dropping ch by 1 pp increases CLV by ≈ Rs 4,000 * 25.25 * 0.01 = Rs 1,010.

**Formulas:**
```
CLV_inf_no_disc = m / ch
CLV_DCF = m * (1-ch) / (ch + r/12)
CLV_T = m * x * (1-x^T) / (1-x)          where x = (1-ch) / (1+r/12)
dCLV/dch = -m / ch^2                      (no-discount form)
```

**Worked Example:** ARPU = Rs 5,000/mo, GM = 80%, m = Rs 4,000/mo. Monthly churn ch = 0.03. Discount r = 12%/yr.

```
CLV_DCF = 4,000 * 0.97 / (0.03 + 0.01) = 4,000 * 0.97 / 0.04 = Rs 97,000
```

If churn drops to 0.02:
```
CLV_DCF_new = 4,000 * 0.98 / (0.02 + 0.01) = Rs 1,30,667     (+35%)
```

Finite 36-month horizon: x = 0.97/1.01 = 0.9604. x^36 = 0.234.
```
CLV_36 = 4,000 * 0.9604 * (1 - 0.234) / (1 - 0.9604) = Rs 74,328
```

**Practitioner Interpretation:** Churn reduction is the single highest-leverage CLV lever. Use infinite-horizon DCF for going-concern SaaS. Use finite-horizon for time-bounded enterprise contracts (e.g., 24-month locked terms). For enterprise annual contracts, substitute ch_annual for monthly ch and r (annual) for r/12.

**India Values:** India SaaS NRR 108–115% implies net negative churn at cohort level (expansion > gross churn). This means CLV must account for expansion ARPU: replace ARPU with ARPU * NRR_monthly in CLV formula for expansion-eligible customers.

---

### M4: Sales Velocity Formula and Pipeline Optimization

**Sales Velocity (SV):**
```
SV = (N_opp * WR * ACV) / Cycle_days             (units: revenue per day)
Annual run rate = SV * 365
```

**Multiplicative Logarithmic Decomposition:**
```
ln(SV) = ln(N) + ln(WR) + ln(ACV) - ln(Cycle)
```

**Unit Elasticity of Each Factor:**
```
d_ln(SV) / d_ln(N)     = +1
d_ln(SV) / d_ln(WR)    = +1
d_ln(SV) / d_ln(ACV)   = +1
d_ln(SV) / d_ln(Cycle) = -1
```

**Partial Derivatives (Absolute Sensitivity):**
```
d SV / d N     = (WR * ACV) / Cycle
d SV / d WR    = (N * ACV) / Cycle
d SV / d ACV   = (N * WR) / Cycle
d SV / d Cycle = -(N * WR * ACV) / Cycle^2
```

The negative sign for Cycle means reducing cycle days increases SV. The quadratic denominator means cycle improvement has compounding effect at shorter cycle lengths.

**Optimization Strategy:**

All factors have equal unit elasticity, so the highest-leverage factor is the one with the lowest cost per 10% improvement:

1. Cycle_days: process improvement (faster qualification, legal templates). Often 15–25% reduction achievable.
2. Win_Rate: enablement investment (competitive battlecards, reference customers). 5–10% improvement per quarter realistic.
3. ACV: upsell/cross-sell program, premium tiers. Limited by buyer budget.
4. N_opp: marketing/SDR investment. Highest per-opp cost.

**Formula Summary:**
```
SV = (N * WR * ACV) / Cycle
Annual_SV = SV * 365
d_ln(SV) / d_ln(x_i) = +1 for N, WR, ACV; -1 for Cycle
```

**Worked Example (India SaaS):**

Baseline: N=50, WR=25%, ACV=Rs 10L, Cycle=90 days.
```
SV = (50 * 0.25 * 10,00,000) / 90 = Rs 1,38,889/day
Annual = Rs 5.07 Cr
```

Targeting 2× annual SV to reach Rs 10.14 Cr: achieve 25% improvement on 3 factors simultaneously:
```
SV_new = (62.5 * 0.3125 * 12.5L) / 90 = Rs 2,71,701/day
Annual = Rs 9.92 Cr                              (~2x achieved)
```

India context: average deal cycle for >$1M TCV (>Rs 8 Cr) = 6–9 months vs global 3–9 months. Factor this into Cycle denominator. SMB SaaS India: 60–90 day cycle typical.

---

### M5: Win Rate Logistic Regression — MLE and Calibration

**Full Logistic Model:**
```
P(win | x) = sigma(beta_0 + beta_1 * deal_size + beta_2 * MEDDIC + beta_3 * competitor_strength + beta_4 * cycle_days + beta_5 * industry_indicator)
sigma(z) = 1 / (1 + e^{-z})
```

**Log-Likelihood:**
```
l(beta) = sum_{i=1}^{n} [y_i * ln(sigma(x_i^T beta)) + (1-y_i) * ln(1 - sigma(x_i^T beta))]
        = sum_{i=1}^{n} [y_i * x_i^T beta - ln(1 + e^{x_i^T beta})]
```

**Score (Gradient):**
```
nabla l = X^T (y - p)          where p_i = sigma(x_i^T beta)
```

**Hessian:**
```
H = -X^T W X                   where W = diag(p_i * (1 - p_i))
```

**Newton-Raphson MLE Update:**
```
beta^{k+1} = beta^k - H^{-1} nabla l
           = beta^k + (X^T W X)^{-1} X^T (y - p)
```

Iterate until ||beta^{k+1} - beta^k|| < 1e-6. Typically converges in 10–20 iterations. Equivalent to IRLS (Iteratively Reweighted Least Squares).

**McFadden Pseudo-R^2:**
```
R^2_McFadden = 1 - l_fitted / l_null
l_null = n * [y_bar * ln(y_bar) + (1-y_bar) * ln(1-y_bar)]          y_bar = mean(y)
```

Interpretation: R^2 = 0 means model no better than intercept-only. R^2 = 0.2–0.4 = good logistic fit (not equivalent to OLS R^2).

**Brier Score:**
```
BS = (1/n) * sum (p_i - y_i)^2          range [0, 1]; < 0.25 is informative; 0 = perfect
```

Murphy Decomposition:
```
BS = reliability - resolution + uncertainty
```
- Reliability: average squared deviation between predicted probability and actual frequency within probability bins. Lower = better.
- Resolution: variance of predicted probabilities. Higher = better.
- Uncertainty: y_bar * (1-y_bar). Irreducible term.

**Platt Scaling Recalibration:** When raw logistic is overconfident or underconfident, fit:
```
p_calibrated = sigma(a * p_raw + b)
```
Re-running logistic on (p_raw as feature, y as label) on a held-out calibration set.

**Formula Summary:**
```
beta_MLE = argmax l(beta)             (Newton-Raphson, ~15 iterations)
R^2_McFadden = 1 - l_fit / l_null
BS = mean((p_i - y_i)^2)
p_calibrated = sigma(a * p_raw + b)   (Platt scaling)
```

**Worked Example:** 500 deals, 30% win rate (y_bar = 0.30).

```
l_null = 500 * (0.3 * ln(0.3) + 0.7 * ln(0.7))
       = 500 * (0.3*(-1.204) + 0.7*(-0.357))
       = 500 * (-0.611) = -305.5
```

Converged model: l_fitted = -240.2.
```
R^2_McFadden = 1 - 240.2/305.5 = 0.214        (good fit)
```

Fitted beta = (-2.5, 1e-6 deal_size, 0.04 MEDDIC, -0.10 competitor_strength, -0.003 cycle_days, 0.30 BFSI_indicator).

Deal prediction: deal_size=Rs 50L, MEDDIC=45, comp_str=3, cycle=90, BFSI=1:
```
log_odds = -2.5 + 5.0 + 1.8 - 0.3 - 0.27 + 0.30 = 4.03
P(win) = sigma(4.03) = 0.982                   (high-confidence deal)
```

BS on test set: 0.18 (good calibration).

**Practitioner Interpretation:** Re-fit model quarterly with rolling 18-month window. Monitor BS — if it rises > 0.05 from baseline, recalibrate via Platt or isotonic regression. Use predicted P(win) for weighted pipeline forecast: Forecast = sum(Deal_Value_i * P_win_i).

**Boundary Conditions:** Quasi-separation (predictor perfectly separates classes): MLE diverges; add L2 regularization (ridge logistic). Small samples (n < 50): cross-validation essential. Class imbalance: stratified sampling or class weights.

---

### M6: Quota Ramp Model and India Enterprise Deal Cycle

**India Enterprise Deal Cycle (LogNormal Distribution):**

Deal cycle time T ~ LogNormal(mu_T, sigma_T^2). Justification: cycle time is positive, right-skewed (long tail for complex deals), and arises from multiplicative stage delays (each stage delay multiplies with others), satisfying conditions for lognormal.

T06 confirmed: India enterprise deal cycle median 6–9 months for >$1M TCV (>Rs 8 Cr).

**Calibration from Percentile Data:**

Given median = 7 months and 90th percentile = 12 months:
```
median = exp(mu_T) = 7    →    mu_T = ln(7) = 1.946
P90 = exp(mu_T + 1.282 * sigma_T) = 12
→ sigma_T = (ln(12) - ln(7)) / 1.282 = (2.485 - 1.946) / 1.282 = 0.420
```

Mean deal cycle:
```
E[T] = exp(mu_T + sigma_T^2 / 2) = exp(1.946 + 0.088) = exp(2.034) = 7.65 months
```

**Probability of Closing in Quarter Q:**

A deal started at time t_0 has cycle T ~ LogNormal(mu_T, sigma_T). Quarter Q has calendar boundaries [Q_start, Q_end] (in months from today):
```
P(closes in Q | started at t_0)
    = P(Q_start - t_0 <= T <= Q_end - t_0)
    = Phi((ln(Q_end - t_0) - mu_T) / sigma_T) - Phi((ln(Q_start - t_0) - mu_T) / sigma_T)
```

where Phi is the standard normal CDF.

**Quota Ramp Model:**

New account executive (AE) ramp by quarter: [0.25, 0.50, 0.75, 1.00].

Expected quarterly revenue:
```
E[Rev_q] = ramp_q * full_annual_quota / 4
```

Year-1 total expected revenue:
```
E[Year_1] = sum_q ramp_q * (Q/4) = (0.25 + 0.50 + 0.75 + 1.00) / 4 * Q = 0.625 * Q
```

A newly hired AE delivers only **62.5% of full quota** in year 1.

**Formula Summary:**
```
T ~ LogNormal(mu_T, sigma_T^2)
mu_T = ln(median_cycle); sigma_T = (ln(P90) - mu_T) / 1.282
P(closes in [a,b] | t_0) = Phi((ln(b-t_0)-mu_T)/sigma_T) - Phi((ln(a-t_0)-mu_T)/sigma_T)
Year-1 ramp expected = 0.625 * full_quota
E[Rev_q] = ramp_q * Q / 4
```

**Worked Example:**

Deal started 1 month ago (t_0 = -1 month from today). Distribution: mu_T=1.946, sigma_T=0.420. Quarter runs months [3, 6] from today.

```
Q_start - t_0 = 3 - (-1) = 4 months.   Q_end - t_0 = 6 - (-1) = 7 months.
z_low = (ln(4) - 1.946) / 0.420 = (1.386 - 1.946) / 0.420 = -1.333    →  Phi(-1.333) = 0.091
z_high = (ln(7) - 1.946) / 0.420 = (1.946 - 1.946) / 0.420 = 0         →  Phi(0) = 0.500
P(closes in Q) = 0.500 - 0.091 = 0.409  (40.9% probability)
```

For a rep in Q2 of ramp (ramp_2 = 0.50) with annual quota Rs 4 Cr:
```
E[Q2_revenue] = 0.50 * Rs 4 Cr / 4 = Rs 50,00,000
```

**Practitioner Interpretation:** Use lognormal cycle CDF for deal-level probability estimates in forecast roll-up. Use quota ramp for headcount planning — a 20-rep team hired at start of year delivers only ~12.5 rep-equivalents in year 1. India-specific: GeM tenders have deterministic 30-day procurement window (not lognormal). Factor separately.

**Boundary Conditions:** Open deals exhibit recency bias (only closed deals contribute to cycle time estimate). Use survival analysis (Kaplan-Meier) for unbiased cycle estimation including censored open deals. Startup AEs often have steeper ramp (0.10/0.30/0.60/1.00) than mature-org AEs (0.25/0.50/0.75/1.00).

---

## 8. Anti-Patterns to Avoid

- **Including deals still open (unresolved) in a stage's conversion-rate denominator**: per §1.4, the denominator must exclude deals still in stage — counting them introduces survivor bias, since an open deal hasn't yet had the chance to convert or fail, and mixing it into a completed-cohort conversion rate systematically distorts the measured rate.
- **Applying the flat "3x pipeline coverage" rule regardless of the team's actual win rate**: per §6.2, `PCR_needed = 1/WR` — a team winning at 25% needs 4x coverage, one winning at 40% needs only 2.5x; using the generic 3x figure for either team either under-resources the pipeline (at 25% WR) or wastes qualification effort chasing unnecessary coverage (at 40% WR).
- **Using the flat 3x-5x PCR target without widening it when win rate is volatile or deal sizes vary widely**: per §6.2's explicit deviation rule, PCR target should rise to 4-5x when win-rate CV exceeds 30% or ACV CV exceeds 50% (or during India's March Q4-flush risk window) — applying a fixed target through periods of high variance understates the coverage actually needed to reliably hit the number.
- **Letting reps repeatedly push a deal's close date instead of flagging it under the stale-deal rule**: per §3.1/§3.3, a deal stuck in the same stage beyond 1.5x its typical hold time is supposed to be auto-flagged at-risk and reviewed in the weekly pipeline call — allowing repeated close-date pushes without manager approval (violating the stated once-per-quarter policy) is exactly the workaround this hygiene rule exists to prevent.
- **Advancing a deal into the Opportunity stage without meeting the MEDDIC gate, or allowing ACV to diverge from the actual quote by more than 20%**: per §3.3's pipeline hygiene rules, both are explicit, numeric entry gates (MEDDIC ≥ 40/60, ACV-to-quote match within 20%) — treating them as guidelines rather than hard gates lets under-qualified or inconsistently-priced deals inflate pipeline value figures that feed directly into the coverage-ratio and forecast calculations.
- **Reporting a deal's raw CRM-stage prior win probability as its current score after MEDDIC evidence has been collected**: per §4.1's worked example, the whole point of the Bayesian update is that a high MEDDIC score can substantially override a low stage prior (25% prior → 88% posterior in the worked example) — continuing to cite the unadjusted stage prior once qualification evidence exists discards the more informative posterior the model was built to produce.
- **Assuming quota attainment is normally distributed when constructing forecast confidence intervals**: per §6.1, attainment is modeled as lognormal specifically because it is multiplicative, right-skewed, and bounded below at zero — fitting a normal distribution to this data misestimates both the tail risk (underestimating how far top performers exceed quota) and the probability mass near zero.
- **Expecting a single Sales Velocity lever (opportunities, win rate, ACV, or cycle time) to double SV on its own**: per §2.2/§2.3, each factor has unit elasticity — a 10% improvement in any one factor yields roughly a 10% SV improvement, not more — doubling SV requires compounding improvement across multiple levers simultaneously (the worked example needs ~25% improvement across three levers, since `1.25³ ≈ 1.95x`), not a single outsized push on one lever alone.

## 9. India-Specific Layer

### 8.1 India Fiscal Calendar and B2B Seasonality

India's fiscal year ends March 31 (FY = April 1 to March 31). This creates a pronounced Q4 (January–March) buying surge as:
- Government and PSU procurement must be exhausted by March 31 budget closure.
- Enterprise software buyers use up capital budgets before fiscal year end.
- Procurement approvals that were on hold accelerate to close within the fiscal year.

**Pipeline building implication:** Start Q4-target pipeline building in September–October (Q2 of Indian fiscal). A 6-month India enterprise cycle started in October yields a March close probability of ~40% (using lognormal model above). Starting in December shortens the window to 3 months with < 20% probability.

**Festival Blackout Periods (India):**

| Period | Festival | Impact |
|---|---|---|
| October (variable) | Diwali (5-day festival) | Deal velocity drops ~50%; executive unavailability; avoid new discovery |
| March (variable) | Holi (2-day) | Minor disruption; March urgency usually overrides |
| August 15 | Independence Day | Government procurement halts |
| October 2 | Gandhi Jayanti | Government offices closed |
| Navratri (Sep–Oct, 9 days) | Regional significance (Gujarat, Maharashtra) | Key decision-makers may be unavailable |

**Plan:** Do not schedule procurement board meetings or contract signing during Diwali week. Do not schedule executive reviews during major festival dates. Pipeline commitments made in October (post-Diwali) are more reliable than pre-Diwali.

### 8.2 GeM (Government e-Marketplace) Procurement

GeM is mandatory for central government procurement above Rs 25,000. Win rates and deal cycles differ significantly from private sector:

| Procurement Type | Trigger Value | Process | Typical Cycle | Win Rate Dynamics |
|---|---|---|---|---|
| Direct Purchase | Up to Rs 25,000 | No competition; agency buys directly | 1–7 days | 100% if listed on GeM |
| Push Button Procurement (PBP) | Rs 25,001 – Rs 5,00,000 | No RA required; L1 price wins | 1–4 weeks | Price-based; lowest wins |
| Bid / RA Process | Above Rs 5,00,000 | Competitive bid; RA for further negotiation | 30–90 days | Quality + price scored |
| Custom Bid | Large/complex requirements | Technical + financial evaluation | 60–180 days | QCBS-style scoring |

**MSME preference on GeM:** 25% of all government procurement must come from Micro and Small Enterprises (MSEs). 4% sub-target for SC/ST-owned MSEs; 3% sub-target for women-led enterprises. MSME-registered sellers receive preferential treatment in tied bidding scenarios.

**Win-rate multiplier for MSME-registered B2B SaaS sellers on GeM:** 1.3–1.8× higher win rate vs non-MSME in comparable bids (due to mandate compliance pressure on procurement officers).

### 8.3 CAC Payback — India SaaS Benchmarks

CAC payback is the number of months required to recover customer acquisition cost from gross margin:
```
CAC_payback = CAC / (ARPU_monthly * GM)
```

**Benchmarks (2024, confirmed by T06 Search 2):**

| Metric | Global Median | India SaaS Estimate |
|---|---|---|
| CAC Payback | 18 months (2024 median) | 18–24 months (higher field sales cost) |
| CAC Payback — PLG / high-GM | < 12 months | 12–18 months |
| LTV:CAC ratio | 3.2:1 (median) | 2.5–3.5:1 (lower ACV, higher CAC) |
| Average SaaS CAC payback range | 20–30 months | 24–36 months (enterprise) |

India-specific factors that increase CAC vs global:
1. Higher field sales intensity (most India enterprise deals require on-site demos and in-person presentations).
2. Longer deal cycles (6–18 months vs 3–9 months globally for equivalent TCV).
3. India-specific procurement friction (Udyam registration, GeM onboarding, GST compliance checks).
4. Price sensitivity: average ACV 30–50% lower than comparable US deals, compressing LTV.

### 8.4 India Enterprise Sales Cycle vs Global

| Deal Size | India Cycle Median | Global Cycle Median | India Premium |
|---|---|---|---|
| SMB SaaS (< Rs 5L/yr) | 60–90 days | 30–60 days | 2× |
| Mid-market SaaS (Rs 5L–Rs 50L/yr) | 3–6 months | 2–4 months | 1.5× |
| Enterprise IT (> Rs 1 Cr/yr or > $1M TCV) | 6–18 months | 3–9 months | 1.5–2× |
| Government / PSU | 3–12 months (GeM + RA) | N/A (different process) | — |

**NASSCOM benchmark (training knowledge):** Median 6–9 months for IT services deals > $1M TCV.

### 8.5 TDS Section 194Q — Impact on Deal Closure Timing

Section 194Q (effective 1 July 2021) requires the buyer to deduct TDS at 0.1% on B2B purchases exceeding Rs 50 lakh per FY from a single seller.

**Deal economics impact:**
```
TDS_amount = 0.001 * max(0, Purchase_value - 50,00,000)
```

If PAN not furnished: rate increases to 5%.

If both Section 194Q and Section 206C(1H) apply: Section 194Q prevails.

**Cash flow timing impact:** TDS deducted by buyer is a working capital lock-up for the seller until TDS refund/credit (typically 6–18 month cycle). For deals that push seller above Rs 50L threshold from a single buyer:

```
Cash_lock_up_cost = TDS_amount * r/12 * t_refund_months     (first-order approximation)
```

**Deal timing implication:** Sellers often structure multi-year contracts to keep individual-year transaction below Rs 50L threshold (avoiding 194Q). Alternatively, they structure as services (potentially under Section 194J at 10%) vs goods (194Q at 0.1%). Important: SaaS may be classified as services under 194J — verify contract classification with CA before deal close.

**March 31 fiscal-year interaction:** All FY-year-to-date purchases reset on April 1. Large enterprise buyers near the Rs 50L threshold in March may time their final purchases for April 1 to reset the counter. Sales reps should monitor buyer's FY cumulative purchase from them.

### 8.6 India Enterprise Deal Norms

**Payment terms:** Standard B2B India payment terms are Net-45 to Net-90. Enterprise buyers (listed companies) are legally required to pay within 45 days of invoice under MSMED Act for MSME vendors; 30-day payment obligation for government buyers. In practice, large corporates pay in 60–90 days.

**Impact on CLV discount rate:** Longer payment cycles increase effective discount rate. Adjust CLV_DCF discount rate r upward by 0–2% to reflect working capital cost of delayed payments.

**Contract structure norms:**
- Annual contracts with 30-day notice are standard for India enterprise SaaS.
- Multi-year contracts (2–3 year) with annual billing are increasingly accepted by large enterprises.
- Government contracts: typically 1-year, renewed annually via GeM RA or fresh tender.

---

## 10. Response Rules

1. Always define what pipeline stage a deal is at before computing win probability or expected revenue — stage determines the Markov prior.
2. Use the four-factor Sales Velocity formula explicitly; never report pipeline value alone as a proxy for revenue health.
3. When presenting CLV, always state whether it is infinite-horizon DCF, finite-horizon, or no-discount form — they differ substantially.
4. Present MEDDIC scores with individual dimension scores, not just a composite — a low single dimension (e.g., no Champion) is more actionable than the total score.
5. For India enterprise deals, always apply the India fiscal calendar context: Q4 (Jan–Mar) surge timing, festival blackouts, and March 31 budget-close urgency.
6. State TDS 194Q flag explicitly when deal value from a single buyer may exceed Rs 50L in the FY — this affects cash flow modeling.
7. Pipeline Coverage Ratio must be computed against the specific rep's or team's observed win rate, not a generic 3x default.
8. When win rates are estimated from small samples (n < 30), add bootstrap CI to PCR recommendation.
9. For GeM deals, use the correct scoring model (L1 for catalog, QCBS/TOPSIS for custom bids) — do not apply private-sector win rate assumptions.
10. Always recalibrate logistic win-rate models quarterly; models trained on historical data degrade as market conditions change.

---

## 11. What Not to Do

1. **Do not use pipeline value without stage-weighted probability** — raw pipeline value overstates expected revenue by 3–5×. Always multiply deal value by B_{stage, Won} absorption probability.
2. **Do not apply global CAC benchmarks directly to India market** — India SaaS CAC payback is typically 20–40% longer than global median due to higher field sales intensity and lower ACV. Adjust India benchmarks explicitly.
3. **Do not ignore India Q4 (Jan–Mar) seasonality** — pipelines built for December close that extend into January become Q4 deals with different urgency dynamics. Treat Q4 as a distinct pipeline category.
4. **Do not conflate NRR with win rate** — NRR (Net Revenue Retention, see revenue-pricing-core) measures cohort expansion/churn, not initial-deal win rate. These are separate metrics.
5. **Do not use a single win-rate threshold (e.g., P(win) > 0.5) across all deal types** — the F1-optimal threshold tau* varies by class imbalance, deal mix, and business objective. Calibrate threshold per segment.
6. **Do not commit to quarterly revenue forecast from a single weighted-pipeline number** — use P85/P95 from Monte Carlo or lognormal model for upside/downside scenario framing.
7. **Do not ignore TDS 194Q when modeling India enterprise deal cash flows** — for deals > Rs 50L/FY from a single buyer, TDS lock-up is a real working capital cost.
8. **Do not model India enterprise deal cycles as Normal (symmetric)** — deal cycles are lognormal (right-skewed). Using Normal underestimates tail risk (deals that run 18 months+).
9. **Do not compute Sales Velocity without unit-checking** — N (count), WR (decimal), ACV (currency), Cycle (days) must have consistent units; output is currency/day.
10. **Do not re-use a logistic model trained more than 2 quarters ago without recalibration** — win-rate drivers (competitive landscape, economic conditions, product maturity) shift; Brier Score should be monitored continuously.

---

## 12. Output Expectations

**When asked to design a sales pipeline:**
- Deliver stage definitions with entry/exit BANT/MEDDIC criteria, typical conversion rates, and PCR target calibrated to stated win rate.

**When asked to compute win probability for a deal:**
- Return P(win) from logistic model with MEDDIC inputs, deal size, and cycle days; include current stage Markov prior; flag any weak MEDDIC dimensions.

**When asked for sales velocity analysis:**
- Compute current SV baseline; show all four factors with their partial derivatives; rank improvement levers by cost-effectiveness; provide India-context cycle benchmarks.

**When asked for CLV:**
- Provide both infinite-horizon DCF (CLV_DCF) and finite-horizon (CLV_T) forms; include churn sensitivity (dCLV/dch); flag India-specific payment-term adjustment.

**When asked for forecast:**
- Provide weighted pipeline (deal × P_win sum), stage-weighted pipeline, and lognormal-model in-quarter probability for key deals; give PCR vs target; flag Q4 surge or festival risk if applicable.

**When asked about India-specific BD:**
- Cover fiscal year seasonality, GeM procurement model, TDS 194Q cash flow impact, payment norms, and CAC payback benchmarks vs global.

All numerical outputs should use INR (Rs) for Indian deals and USD for global benchmarks, with explicit conversion at stated exchange rate.

---

## 13. Skill Scope

**In scope:**
- B2B SaaS, IT services, and enterprise software sales pipelines.
- MEDDIC, BANT, SPICED qualification frameworks.
- CRM pipeline analytics (Salesforce, HubSpot, Zoho CRM).
- Quota design, territory planning, and ramp modeling.
- Revenue forecasting: weighted pipeline, Monte Carlo, lognormal deal-cycle models.
- India-specific sales norms: GeM, TDS 194Q, fiscal calendar, MSME preference.
- Customer lifetime value in geometric series and DCF forms.
- Win rate logistic regression and Brier Score calibration.

**Out of scope:**
- Product-led growth (PLG) funnel metrics — see market-expansion-core and revenue-pricing-core.
- Pricing strategy and price elasticity — see revenue-pricing-core.
- Market sizing (TAM/SAM/SOM) — see market-expansion-core.
- India government tender evaluation (QCBS, TOPSIS) — see india-bd-core.
- Sales compensation design (OTE, commission plans) — not covered in this library.
- Consumer (B2C) sales funnels — out of scope; metrics differ fundamentally.

---

## 14. Version

**Version:** 1.0.1 — 2026-07-27 — Added §8 Anti-Patterns to Avoid (8 pitfalls spanning conversion-rate survivor bias, flat PCR-target misuse, close-date-push workarounds, MEDDIC/ACV gate bypassing, stage-prior-vs-posterior confusion, lognormal-vs-normal attainment modeling, and single-lever SV-doubling expectations); renumbered §8-13 to §9-14.

**Version:** 1.0.0
**Domain:** Agile Business & Revenue Intelligence (Domain 41)
**Library version:** v29.2.0
**Date:** 2026-05-17
**Research sources:** T06 (BD research), T08 (synthesis), T10 (M1–M6 derivations); benchmarks confirmed from SaaS Capital/OpenView 2024, NASSCOM IT-BPM data, GeM portal, Income Tax Act Section 194Q.
