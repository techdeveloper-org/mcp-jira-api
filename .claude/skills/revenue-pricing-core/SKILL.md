---
name: revenue-pricing-core
description: "Provides pricing strategy mathematics including price elasticity modeling, Van Westendorp Price Sensitivity Meter, SaaS ARR/MRR/NRR/NDR/GRR cohort analysis, freemium Bayesian conversion, and cohort LTV discounted cash flow. Use when designing pricing tiers, analyzing revenue retention, computing expansion revenue, optimizing freemium funnels, or forecasting ARR from cohort data. Keywords: price elasticity demand curve, Van Westendorp pricing, SaaS ARR MRR NRR NDR GRR metrics, freemium Bayesian conversion rate, cohort LTV DCF, revenue retention analysis, India GST SaaS pricing."
allowed-tools: Read,Glob,Grep
user-invocable: true
---


<!-- generated-by: claude-global-library/tools/project_sync -->
<!-- source: skills/revenue-pricing-core/SKILL.md -- edit the library, then re-run sync_project.py -->

# revenue-pricing-core

## Description

Provides mathematical foundations for SaaS revenue and pricing decisions. Covers price elasticity and demand curve optimization, the Van Westendorp Price Sensitivity Meter with four-curve empirical CDF analysis, SaaS cohort revenue mechanics (NRR, GRR, NDR), freemium Bayesian conversion estimation, cohort LTV via discounted cash flow, and India-specific pricing adjustment (GST SAC 998314, PPP localization via profit-maximization). Use when designing pricing tiers, analyzing revenue retention, computing expansion revenue, optimizing freemium funnels, forecasting ARR from cohort data, or calibrating India market pricing.

---

## 1. SaaS Revenue Metrics

### 1.1 MRR and ARR Definitions

**Monthly Recurring Revenue (MRR):** The normalized, predictable monthly revenue from all active subscriptions.

```
MRR = sum of monthly contract values across all active customers
ARR = MRR * 12
```

Do not include one-time setup fees, professional services, or usage overages in MRR unless fully contracted on a recurring basis.

**MRR Waterfall (five-component decomposition):**

```
MRR_end = MRR_start
        + New_MRR           (from new customers)
        + Expansion_MRR     (upsells, seat adds, tier upgrades)
        - Contraction_MRR   (downgrades, seat reductions)
        - Churned_MRR       (cancelled subscriptions)
```

### 1.2 Net Revenue Retention (NRR / NDR)

NRR measures how much revenue a cohort of existing customers generates relative to what they paid at the start of the period.

```
NRR = (MRR_start + Expansion_MRR - Contraction_MRR - Churned_MRR)
      / MRR_start * 100%
```

NRR > 100% indicates expansion revenue outpaces churn and contraction — the existing base grows without new acquisitions.

**Benchmarks (confirmed from T06 Search 2, 2024):**

| Segment | NRR Benchmark |
|---|---|
| Venture-backed SaaS median | 106% |
| Broader SaaS market median | ~110% |
| Enterprise SaaS | 115–125% |
| SMB SaaS | 90–105% |
| Top-decile (best-in-class) | > 130% |

India SaaS NRR: 108–115% (NASSCOM/SaaSBOOMi estimates, training fallback — verify with SaaSBOOMi 2024 report).

### 1.3 Gross Revenue Retention (GRR)

GRR excludes expansion revenue entirely. It captures pure downside retention.

```
GRR = (MRR_start - Contraction_MRR - Churned_MRR)
      / MRR_start * 100%
```

GRR is bounded at 100% by definition — expansion is structurally excluded.

**Benchmarks (confirmed from T06 Search 2, 2024):**

| Segment | GRR Benchmark |
|---|---|
| Median all SaaS | 90% |
| "Good" | 85–95% |
| "Great" / best-in-class | ≥ 95% |
| Enterprise SaaS | 90–97% |
| Mid-market | 85–92% |
| SMB SaaS | 75–85% |

India SaaS GRR: 88–93% (training fallback — verify with SaaSBOOMi 2024 report).

**Critical rule:** Always present NRR and GRR together. NRR alone hides whether growth comes from genuine expansion or masking contraction. GRR alone ignores the expansion flywheel that justifies premium valuations. See Response Rules §9.1.

---

## 2. Unit Economics Framework

### 2.1 Customer Acquisition Cost (CAC)

```
CAC = Total_Sales_and_Marketing_Spend_period / New_Customers_Acquired_period
```

Denominator: count only net new customers, not expansions or reactivations. Numerator: include fully-loaded S&M salaries, commissions, ad spend, events, and tools. Specify the time window (monthly, quarterly, annual).

**Blended vs channel-specific CAC:**

```
Blended_CAC = Total_S&M / Total_new_customers

CAC_PLG = PLG_S&M_spend / PLG_new_customers
CAC_SLG = SLG_S&M_spend / SLG_new_customers
```

**CAC Payback Period benchmarks (T06 Search 2, 2024):**

| Segment | CAC Payback |
|---|---|
| Median 2024 | 18 months (increased from 14 months in 2023) |
| PLG / high gross margin | < 12 months |
| Average SaaS range | 20–30 months |

### 2.2 Customer Lifetime Value (LTV)

**Simple LTV (no discounting):**

```
LTV_simple = ARPU * Gross_Margin / Monthly_Churn_Rate
```

**DCF LTV (present-value adjusted):**

```
LTV_DCF = ARPU * GM * (1 - ch) / (ch + r/12)
```

where `ch` = monthly churn rate, `r` = annual discount rate, `GM` = gross margin fraction.

Derivation: geometric series with ratio `x = (1-ch)/(1+r/12)`, producing the closed form above. See M5 for full derivation.

### 2.3 LTV:CAC Ratio

```
LTV_to_CAC = LTV_DCF / CAC
```

**Benchmarks (T06 Search 2, 2024):**

| Level | LTV:CAC |
|---|---|
| Median | 3.2:1 |
| Healthy minimum threshold | 3:1 |
| Top-quartile | > 4:1 (with CAC payback < 12 months) |
| Under-investing in growth signal | > 5:1 (flag — see Response Rules §9.2) |

**Sensitivity (most important lever):**

```
d(LTV_DCF)/d(ch) = -(ARPU * GM) / ch^2
```

Churn is the highest-leverage variable: a 1 percentage-point reduction in monthly churn has outsized LTV impact, especially at low base churn rates.

### 2.4 Magic Number (GTM Efficiency)

```
Magic_Number = Net_New_ARR_Q / S&M_Spend_{Q-1}
```

Healthy: > 0.75. Efficient growth signal: > 1.0. (Training knowledge — cite OpenView/SaaS Capital benchmarks; not independently confirmed by web search.)

---

## 3. Pricing Strategy Models

### 3.1 Value-Based Pricing

Price is anchored to the quantified economic value delivered to the customer, not to cost or competitor prices.

```
Price_value_based = Customer_Willingness_To_Pay (WTP)
WTP = Baseline_reference_price + Economic_value_added - Differentiation_costs
```

Economic Value to Customer (EVC) model:
```
EVC = Next_best_alternative_price + Value_of_differentiation
```

The price floor is `MC` (marginal cost); the price ceiling is `EVC`. Optimal price captures a share of `EVC - MC` that reflects competitive dynamics and switching costs.

### 3.2 Cost-Plus Pricing

```
Price_cost_plus = (Variable_Cost + Fixed_Cost_per_unit) * (1 + Target_Margin)
```

Cost-plus is rarely optimal for SaaS (marginal cost near zero) but serves as a price floor sanity check.

### 3.3 Competitive Pricing

```
Price_competitive = Competitor_reference_price + delta_premium
delta_premium reflects brand, switching cost, feature differentiation
```

Benchmark via Van Westendorp (§3.4) to test whether delta_premium aligns with WTP.

### 3.4 Van Westendorp Price Sensitivity Meter (PSM)

Survey instrument with four price questions:

1. **TC ("Too Cheap"):** "At what price would you consider this product too cheap to trust the quality?"
2. **C ("Cheap/Bargain"):** "At what price would you consider this product a bargain — good value for money?"
3. **E ("Expensive"):** "At what price would you begin to find this product getting expensive?"
4. **TE ("Too Expensive"):** "At what price would this product be so expensive you would not consider buying it?"

Construct four empirical CDFs from n survey responses (n ≥ 100 for stable curves; n ≥ 200 preferred).

**Four Key Intersections:**

```
OPP (Optimal Price Point): F_TC(p) = F_TE(p)
    Balance of "too cheap to trust" rejection and "too expensive" rejection.

IDP (Indifference Price Point): F_C(p) = F_E(p)
    Where equal fractions find the price cheap and expensive.

PMC (Point of Marginal Cheapness): 1 - F_TC(p) = F_E(p)
    Lower bound of the Acceptable Price Range.

PME (Point of Marginal Expensiveness): F_C(p) = 1 - F_TE(p)
    Upper bound of the Acceptable Price Range.
```

**Acceptable Price Range:** [PMC, PME].

Intersections are found via linear interpolation between adjacent observed price points — see M2 for the exact algorithm and bootstrap CI procedure.

**OPP is not the revenue-maximizing price.** It is the psychologically optimal price minimizing combined rejection from both ends. Multiply by expected demand to identify revenue-optimal point within the acceptable range.

### 3.5 Price Elasticity of Demand

```
PED = (dQ/dP) * (P/Q) = (ΔQ/Q) / (ΔP/P)
```

|PED| > 1: elastic (quantity responds strongly to price change).
|PED| < 1: inelastic (quantity insensitive).
|PED| = 1: unit elastic.

**Profit-maximizing price (Lerner Condition):**

```
P* = MC / (1 + 1/epsilon) = MC * |epsilon| / (|epsilon| - 1)
Markup over MC: m = 1 / (|epsilon| - 1)
```

See M1 for full derivation from first principles. SaaS typical PED range: -1.5 to -2.5 (moderately elastic); highly differentiated products may reach -1.2 to -1.5.

---

## 4. Cohort Revenue Analysis

### 4.1 Cohort Retention Curves

Define cohort c by acquisition month. Track revenue survival:

```
R_{c, t} = R_{c, c} * (1 - ch)^{t-c} * (1 + exp_rate)^{t-c}
```

where `R_{c,c}` = initial cohort MRR at acquisition, `ch` = monthly gross churn rate, `exp_rate` = monthly expansion rate, `t-c` = cohort age in months.

**Cohort revenue matrix** (rows = cohorts, columns = months since acquisition):

```
       Age 0    Age 1    Age 2    Age 3   ...
C1:    100K     97K      95K      94K
C2:    120K     116K     114K
C3:    90K      88K
...
```

Total ARR at month t = sum over all cohorts still active.

### 4.2 Revenue Decay and Negative Churn

For NRR < 100% (net decay): revenue from a cohort shrinks over time.
For NRR > 100% (negative churn / net expansion): revenue from a cohort grows over time.

**Steady-state ARR (assuming constant monthly new ARR = N and monthly NRR factor = NRR_m):**

```
If NRR_m < 1: ARR_steady = N / (1 - NRR_m)
If NRR_m > 1: ARR grows without bound (expansion flywheel)
```

### 4.3 Cohort LTV by Acquisition Period

Compute discounted LTV for each acquisition cohort separately — costs and ARPU vary by channel and time. Compare early cohorts (often lower ARPU, higher churn) versus recent cohorts (better onboarding, higher LTV). Full DCF derivation in M5.

---

## 5. Revenue Forecasting

### 5.1 Bottom-Up ARR Forecasting

```
ARR_t = ARR_{t-1}
      + New_ARR_t
      + Expansion_ARR_t
      - Contraction_ARR_t
      - Churn_ARR_t
```

Build each component from separate drivers:
- `New_ARR_t` = pipeline × win_rate × ACV
- `Expansion_ARR_t` = NRR-driven from existing ARR base
- `Churn_ARR_t` = Gross_Churn_Rate × ARR_{t-1}

### 5.2 Expansion Revenue Modeling

Expansion MRR = f(seat growth, usage tiers, cross-sell, upsell). Model as:

```
Expansion_rate = Expansion_MRR / MRR_beginning_period
```

Typical B2B SaaS expansion rate: 5–15%/quarter in healthy expanding products. Combine with gross churn to derive NRR:

```
NRR_monthly = 1 + Expansion_rate_monthly - Gross_Churn_rate_monthly
```

### 5.3 Churn Forecasting

**Logo (customer) churn vs revenue churn:** Revenue churn is more important for revenue forecasting.

```
Revenue_Churn_Rate = Churned_MRR / Beginning_MRR
Logo_Churn_Rate = Churned_Customers / Beginning_Customer_Count
```

These can diverge: losing small customers gives high logo churn but low revenue churn; losing enterprise accounts gives low logo churn but high revenue churn.

**Survival curve approach:**

```
Survival(t) = (1 - ch)^t    [constant monthly churn]
```

Fit ch from historical cohort data using maximum likelihood:

```
ch_hat = 1 - (Revenue_remaining_after_T_months / Revenue_initial)^{1/T}
```

---

## 6. Deep Mathematical Foundations

### M1: Price Elasticity and Demand Curve

**Foundation:** Microeconomics (no shared foundation required).

**Price Elasticity of Demand (PED):**

```
PED = (dQ/dP) * (P/Q) = (ΔQ/Q) / (ΔP/P)
```

PED < 0 for normal goods.
- |PED| > 1: elastic (price-sensitive buyers).
- |PED| = 1: unit elastic.
- |PED| < 1: inelastic (price-insensitive buyers).

**Log-Linear (Constant-Elasticity) Demand:**

Specify Q = A * P^epsilon. Then:

```
dQ/dP = epsilon * A * P^{epsilon-1}
PED = epsilon * A * P^{epsilon-1} * P / (A * P^epsilon) = epsilon
```

So elasticity equals the exponent — it is constant along the entire demand curve. In log form: ln(Q) = ln(A) + epsilon * ln(P). Fit with linear regression on log-log data.

**Linear Demand:** Q = a - b*P.

```
PED = -b * (P/Q) = -b*P / (a - b*P)
```

PED varies with P along a linear curve. PED = -1 at P = a/(2b) (midpoint of the demand curve).

**Profit-Maximizing Price (Lerner Condition):**

Profit π = P*Q - MC*Q = (P - MC)*Q. Taking dπ/dP = 0:

```
dπ/dP = Q + (P - MC) * dQ/dP = 0
Divide by Q: 1 + (P - MC)/P * (P * dQ/dP / Q) = 1 + (P - MC)/P * epsilon = 0
=> (P - MC)/P = -1/epsilon = 1/|epsilon|    (since epsilon < 0)
=> P* = MC / (1 + 1/epsilon) = MC * |epsilon| / (|epsilon| - 1)
```

Markup over MC:

```
m = (P* - MC)/MC = 1/(|epsilon| - 1)
```

For |epsilon| = 2: markup = 100% (price = 2× MC).
For |epsilon| = 5: markup = 25% (commodity-like).

**Iso-Profit Curves:**

In (P, Q) space, constant profit π₀ defines:

```
Q = π₀ / (P - MC)
```

These are hyperbolas. The demand curve Q(P) intersects iso-profit curves; the highest attainable iso-profit curve touched by the demand curve gives the optimal price-quantity pair.

**Cross-Price Elasticity:**

```
epsilon_xy = (dQ_x / dP_y) * (P_y / Q_x)
```

epsilon_xy > 0: substitutes (raising P_y increases demand for x).
epsilon_xy < 0: complements (raising P_y reduces demand for x).

**Worked Example:** SaaS product with MC = $30/user/month. Estimated constant elasticity epsilon = -1.8 (|epsilon| = 1.8), Q = 10,000 * P^{-1.8}.

```
P* = 30 * 1.8 / (1.8 - 1) = 30 * 2.25 = $67.50/month
Markup = 1/(1.8-1) = 1.25 = 125%
```

If elasticity shifts to -3.0 (more competitive market): P* = 30 * 3/2 = $45. Markup compressed to 50%.

**Practitioner Interpretation:** Estimate epsilon from controlled price tests, conjoint analysis, or industry benchmarks. SaaS PED typically -1.5 to -2.5. Highly differentiated products: -1.2 to -1.5 (stronger pricing power). Apply Lerner formula directly for first-pass optimal price.

**Boundary Conditions:** |epsilon| ≤ 1 (perfectly inelastic) — Lerner formula gives unbounded markup. Real markets have substitutes that eventually bound elasticity. Negative cross-price elasticity in SaaS: bundled features may cannibalize standalone purchases.

---

### M2: Van Westendorp Price Sensitivity Meter — 4-Curve Analysis

**Foundation:** F3 (Monte Carlo bootstrap / empirical CDF).

**Van Westendorp Survey:** Four price questions to n respondents (n ≥ 100):

- TC: "At what price would this product be too cheap to trust the quality?"
- C: "At what price is this product a bargain — good value?"
- E: "At what price is this product getting expensive?"
- TE: "At what price is this product so expensive you would not consider it?"

**Empirical CDFs (Step Functions):**

For each price question, sort responses ascending. Compute empirical CDFs:

- F_TC(p) = fraction of respondents whose TC threshold ≤ p
- F_C(p) = fraction whose C threshold ≤ p
- F_E(p) = fraction whose E threshold ≤ p
- F_TE(p) = fraction whose TE threshold ≤ p

These are empirical step functions — they are not smooth. Intersection between two step functions requires linear interpolation.

**Linear Interpolation Algorithm for Intersection:**

```python
def find_intersection(F1_values, F2_values, prices_sorted):
    """
    F1_values, F2_values: step-function CDF values at prices_sorted.
    Returns interpolated price where F1(p) = F2(p).
    """
    for i in range(len(prices_sorted) - 1):
        p1 = prices_sorted[i]
        p2 = prices_sorted[i+1]
        diff_at_p1 = F1_values[i] - F2_values[i]
        diff_at_p2 = F1_values[i+1] - F2_values[i+1]
        if diff_at_p1 * diff_at_p2 <= 0:    # sign change -> intersection in interval
            # Linear interpolation fraction t in [0, 1]
            t = diff_at_p1 / (diff_at_p1 - diff_at_p2)
            p_intersect = p1 + t * (p2 - p1)
            return p_intersect
    return None
```

Equivalently, the interpolated intersection price:

```
p_intersect = p1 + (p2 - p1) * (F2(p1) - F1(p1)) / ((F1(p2) - F1(p1)) - (F2(p2) - F2(p1)))
```

**Four Key Intersections:**

```
OPP (Optimal Price Point):
    F_TC(p) = F_TE(p)
    Balance of quality-doubt rejection and too-expensive rejection.

IDP (Indifference Price Point):
    F_C(p) = F_E(p)
    Equal fraction finds price cheap as finds it expensive.

PMC (Point of Marginal Cheapness):
    1 - F_TC(p) = F_E(p)
    Lower limit of Acceptable Price Range.

PME (Point of Marginal Expensiveness):
    F_C(p) = 1 - F_TE(p)
    Upper limit of Acceptable Price Range.
```

**Acceptable Price Range:** [PMC, PME].

**Bootstrap CI for OPP (B = 1,000 — T06 confirmed):**

```
For b = 1 to B = 1,000:
    1. Resample n respondents with replacement from the original sample.
    2. Recompute F_TC*, F_C*, F_E*, F_TE* from the resample.
    3. Find OPP*_b using the linear interpolation algorithm above.
Sort OPP*_1, ..., OPP*_B ascending.
95% CI = [OPP*_{floor(0.025 * B)}, OPP*_{ceil(0.975 * B)}]
```

**Rule:** Always report OPP with its bootstrap confidence interval. A reported OPP without CI is statistically incomplete. See Response Rules §9.3.

**Worked Example (India enterprise SaaS):** 100 respondents surveyed. Prices (Rs/year):
[3,000, 5,000, 8,000, 12,000, 18,000, 25,000].

Observed CDFs:
```
F_TC: [0.10, 0.25, 0.45, 0.70, 0.90, 0.95]
F_TE: [0.95, 0.85, 0.65, 0.40, 0.15, 0.05]
```

OPP: find where F_TC(p) = F_TE(p).
At p=8,000: F_TC = 0.45, F_TE = 0.65. Diff = -0.20 (F_TE > F_TC).
At p=12,000: F_TC = 0.70, F_TE = 0.40. Diff = +0.30 (F_TC > F_TE).

Sign change between Rs 8,000 and Rs 12,000. Interpolate:

```
t = (-0.20) / ((-0.20) - 0.30) = -0.20 / -0.50 = 0.40
p_OPP = 8,000 + 0.40 * (12,000 - 8,000) = 8,000 + 1,600 = Rs 9,600/year
```

Bootstrap (B=1,000) typically yields 95% CI of approximately [Rs 8,200, Rs 11,000].

**Practitioner Interpretation:** Survey 100–200 prospective buyers in each target segment. Ask prices in INR for India surveys (exclude $ responses or normalize). Report OPP, acceptable range [PMC, PME], and bootstrap CI. Wide CI signals more survey data needed.

**Boundary Conditions:** Survey design biases (anchoring, ordering effects) affect CDFs. Use ladder order: C → E → TC → TE to minimize anchoring. Step functions may not cross for poorly calibrated price scales — extend the tested price range. Minimum 100 respondents for stable empirical CDFs; 200+ for stable bootstrap CI.

**India Regulatory Values:** None directly applicable. Ask survey prices in INR. Apply GST adjustment (M6) to convert OPP to customer-inclusive price.

---

### M3: SaaS ARR/MRR Cohort Mathematics — NRR, NDR, GRR

**Foundation:** F1 (Geometric series / DCF).

**MRR Waterfall:**

```
MRR_end = MRR_start + New_MRR + Expansion_MRR - Contraction_MRR - Churn_MRR
```

**Net Revenue Retention (NRR / NDR):**

Considering only existing customers (no new MRR):

```
NRR = (MRR_start + Expansion - Contraction - Churn) / MRR_start * 100%
```

NRR > 100% means existing-customer revenue grows — expansion outpaces churn.

**Gross Revenue Retention (GRR):**

```
GRR = (MRR_start - Contraction - Churn) / MRR_start * 100%
```

GRR ≤ 100% always (expansion excluded). GRR captures pure retention.

**Steady-State ARR via Geometric Series:**

Assume constant monthly new ARR = N and monthly NRR factor = NRR_m (e.g., 1.01 ≈ 1% monthly expansion net of churn = ~12% annual NRR).

ARR at time t (contribution from all prior cohorts):

```
ARR(t) = N * sum_{k=0}^{t} NRR_m^k
```

If NRR_m < 1 (net monthly contraction):

```
ARR(t) -> N * 1/(1 - NRR_m)    as t -> infinity    [geometric series converges]
```

If NRR_m > 1 (net monthly expansion): ARR grows without bound — no finite steady state; this is the expansion flywheel.

**Cohort Revenue Matrix:**

R_{c,t} = revenue from cohort c at calendar month t:

```
R_{c,t} = R_{c,c} * (1 - ch)^{t-c} * (1 + exp_rate)^{t-c}
```

Total ARR at month t:

```
ARR(t) = sum_{c=0}^{t} R_{c,t}
```

**Formula summary:**

```
NRR = (MRR_start + Exp - Contr - Churn) / MRR_start * 100%
GRR = (MRR_start - Contr - Churn) / MRR_start * 100%
Steady-state ARR (NRR_m < 1) = N / (1 - NRR_m)
Cohort matrix: R_{c,t} = R_{c,c} * (1-ch)^{t-c} * (1+exp_rate)^{t-c}
```

**Worked Example:** MRR_start = $100K. Monthly: New = $15K, Expansion = $5K, Contraction = $2K, Churn = $3K.

```
MRR_end = 100 + 15 + 5 - 2 - 3 = $115K.
NRR = (100 + 5 - 2 - 3) / 100 = 100/100 = 100%.
GRR = (100 - 2 - 3) / 100 = 95%.
```

If sustained monthly NRR_m = 1.005 (0.5% monthly net expansion ≈ 6% annualized), steady-state ARR:

```
ARR_steady = $15K / (1 - 1.005) — undefined (growing, no steady state)
```

Steady state only exists when NRR_m < 1. At NRR_m = 0.99: ARR_steady = $15K / 0.01 = $1.5M/month = $18M ARR.

**Practitioner Interpretation:** Track NRR and GRR monthly. NRR > 110% → expansion flywheel. NRR < 90% → revenue leakage. Separate contraction from churn: contraction is often a pricing or expansion-motion gap; churn is a retention/product gap.

**India Regulatory Values (benchmarks from T06 Search 2, confirmed 2024):**

NRR: Venture-backed SaaS median 106%. Broader SaaS ~110%. Enterprise 115–125%. SMB 90–105%. Top-decile > 130%.
GRR: Median 90%. Enterprise 90–97%. Mid-market 85–92%. SMB 75–85%.
India-specific: NRR 108–115%, GRR 88–93% (training fallback; verify with SaaSBOOMi 2024).

---

### M4: Freemium Bayesian Conversion Rate Estimation

**Foundation:** Beta-Binomial conjugacy, F3 (Monte Carlo for A/B test).

**Conversion Rate Modeling:**

theta = probability that a free user converts to paid within a given period (e.g., 30 days).

**Prior:** theta ~ Beta(alpha_0, beta_0). Encode industry belief:

```
Typical 3% conversion: Beta(3, 97)     [mean = 3/100 = 3%, informative prior]
Uninformative prior: Beta(1, 1)         [uniform — no prior belief]
Strong prior on 5%: Beta(50, 950)       [tight prior; small data barely moves it]
```

Industry benchmark (T06 Search 2 confirmed): typical freemium-to-paid rate = 2–5%; PLG-optimized products = 3–7%.

**Likelihood:** Given n free users observed, k converted:

```
L(theta) = C(n, k) * theta^k * (1 - theta)^{n-k}
```

**Posterior (Beta-Binomial conjugacy):**

```
theta | data ~ Beta(alpha_0 + k, beta_0 + n - k)
E[theta | data] = (alpha_0 + k) / (alpha_0 + beta_0 + n)
```

Posterior mean is a weighted average of prior mean and observed rate, with weights proportional to prior strength and data volume.

**HDI (Highest Density Interval) — Credible Interval:**

For Beta(a, b), the 95% HDI is [theta_L, theta_U] satisfying:
- pdf(theta_L) = pdf(theta_U) (equal-density endpoints).
- P(theta_L ≤ theta ≤ theta_U | data) = 0.95.

For symmetric posteriors: HDI ≈ equal-tail credible interval. For asymmetric posteriors: HDI is narrower and skewed toward the mode. Computed numerically via binary search on the Beta density.

**A/B Test: P(theta_B > theta_A) via Monte Carlo:**

Two variants A and B with posteriors Beta(a_A, b_A) and Beta(a_B, b_B):

```
For i = 1 to N (N = 10,000):
    sample theta_A_i ~ Beta(a_A, b_A)
    sample theta_B_i ~ Beta(a_B, b_B)
    record indicator I(theta_B_i > theta_A_i)
P(theta_B > theta_A) = (1/N) * sum_i I(theta_B_i > theta_A_i)
```

Decision threshold: P(B > A) > 0.95 → variant B is confidently superior. P(B > A) < 0.85 → collect more data.

**Formula summary:**

```
Prior: Beta(alpha_0, beta_0)
Posterior: Beta(alpha_0 + k, beta_0 + n - k)
Posterior mean = (alpha_0 + k) / (alpha_0 + beta_0 + n)
A/B test: P(theta_B > theta_A) via Monte Carlo (N = 10,000)
```

**Worked Example:**

Prior: Beta(3, 97) encoding 3% industry expectation.

Week 1: 1,000 free users, 25 converted.
Posterior: Beta(3+25, 97+975) = Beta(28, 1072).
Posterior mean = 28/1100 = 2.55%.

After 4 weeks: 4,000 users total, 100 converted.
Posterior: Beta(103, 3997). Posterior mean = 103/4100 = 2.51%.
95% HDI ≈ [2.07%, 3.02%] (large n, tight interval).

A/B test: Control (A): 50 conversions of 2,000. Variant B: 65 of 2,000.
Posterior_A = Beta(53, 2047). Mean = 2.52%.
Posterior_B = Beta(68, 2032). Mean = 3.24%.
P(B > A) ≈ 0.93 — below 0.95 threshold; collect more data before calling the winner.

**Boundary Conditions:** Beta with alpha = 0 or beta = 0 is degenerate. Use Jeffreys prior Beta(0.5, 0.5) as a non-informative alternative. Strong prior with very small data: posterior dominated by prior — verify prior is well-motivated (e.g., from a prior product launch, not a guess).

**India Regulatory Values:** Prior Beta(3, 97) for 3% base conversion reflects confirmed T06 Search 2 industry rate. Typical 2–5% (T06 confirmed). PLG-optimized 3–7% (T06 confirmed).

---

### M5: Cohort LTV Discounted Cash Flow and CAC Payback Period

**Foundation:** F1 (Geometric series), F4 (Payback period).

**Cohort LTV via DCF:**

For a cohort acquired at t=0, paying monthly ARPU with monthly gross churn ch and annual discount rate r:

```
LTV_DCF = sum_{t=1}^{infinity} ARPU * GM * (1-ch)^t / (1 + r/12)^t
```

Define x = (1-ch)/(1+r/12). This is a geometric series with ratio x. For |x| < 1 (i.e., ch + r/12 > 0, always true for positive churn and positive discount rate):

```
LTV_DCF = ARPU * GM * x / (1 - x)
```

**Algebraic simplification:**

1 - x = 1 - (1-ch)/(1+r/12) = [(1+r/12) - (1-ch)]/(1+r/12) = (ch + r/12)/(1+r/12).

Hence x/(1-x) = (1-ch)/(ch + r/12).

**Closed form:**

```
LTV_DCF = ARPU * GM * (1-ch) / (ch + r/12)
```

**CAC Payback Period T* (Closed-Form Derivation):**

Find smallest T such that cumulative discounted gross profit ≥ CAC:

```
sum_{t=1}^{T*} ARPU * GM * (1-ch)^t / (1+r/12)^t >= CAC
```

Using the finite geometric series sum:

```
ARPU * GM * x * (1 - x^{T*}) / (1 - x) >= CAC
1 - x^{T*} >= CAC * (1 - x) / (ARPU * GM * x)
x^{T*} <= 1 - CAC * (1 - x) / (ARPU * GM * x)
T* * ln(x) <= ln(1 - CAC*(1-x)/(ARPU*GM*x))
```

Since x < 1, ln(x) < 0 — inequality flips when dividing:

```
T* = ceil( ln(1 - CAC*(1-x)/(ARPU*GM*x)) / ln(x) )
```

**Feasibility condition:** Requires CAC*(1-x)/(ARPU*GM*x) < 1, equivalently CAC < LTV_DCF. If CAC ≥ LTV_DCF, payback never occurs — business model is structurally broken.

**LTV:CAC Ratio:**

```
LTV_to_CAC = LTV_DCF / CAC    [healthy: >= 3:1]
```

**Benchmarks (T06 Search 2, 2024):**

| Metric | Benchmark |
|---|---|
| CAC payback median 2024 | 18 months |
| PLG / high gross margin | < 12 months |
| LTV:CAC median | 3.2:1 |
| LTV:CAC healthy minimum | 3:1 |
| LTV:CAC top-quartile | > 4:1 (with payback < 12 months) |

**Worked Example:** ARPU = $100/month, GM = 80%, ch = 2%/month, r = 12%/year, CAC = $1,500.

```
x = (1 - 0.02)/(1 + 0.01) = 0.98/1.01 = 0.9703
1 - x = 0.0297
LTV_DCF = 100 * 0.8 * 0.98 / (0.02 + 0.01) = 78.4 / 0.03 = $2,613
LTV:CAC = 2,613 / 1,500 = 1.74  -- below 3x, concerning

Payback:
CAC*(1-x)/(ARPU*GM*x) = 1,500 * 0.0297 / (100*0.8*0.9703) = 44.55 / 77.62 = 0.574
1 - 0.574 = 0.426
T* = ceil(ln(0.426)/ln(0.9703)) = ceil(-0.853/-0.030) = ceil(28.4) = 29 months
```

With CAC reduced to $500: LTV:CAC = 2,613/500 = 5.2. T* = ceil(ln(1 - 500*0.0297/77.62)/ln(0.9703)) = ceil(7.1) = 8 months. Excellent.

**Sensitivity (churn is primary lever):**

```
d(LTV_DCF)/d(ch) = -(ARPU * GM) / ch^2
```

At ch = 2%: d(LTV)/d(ch) = -(80) / 0.0004 = -$200,000 per 1% increase in monthly churn. Reducing monthly churn from 2% to 1% roughly doubles LTV.

**Practitioner Interpretation:** LTV:CAC < 3 → reduce CAC (sales efficiency) or grow LTV (reduce churn, upsell). T* > 18 months is concerning for venture-backed SaaS (median is 18 months, not a target). Stress-test: compute T* with CAC + 50% and LTV - 30% for worst-case scenario planning.

**India Regulatory Values:** CAC payback median 18 months (T06 confirmed 2024). LTV:CAC median 3.2:1 (T06 confirmed). Healthy minimum 3:1 (T06 confirmed). Top-quartile > 4:1 (T06 confirmed). PLG/high-GM payback < 12 months (T06 confirmed).

---

### M6: India GST Pricing Adjustment and PPP-Based Localization

**Foundation:** Microeconomics (Lerner condition from M1), tax arithmetic.

**GST on SaaS (SAC 998314 — IT Consulting and Support Services):**

```
Cross-state (IGST):   18% IGST
Intra-state:          9% CGST + 9% SGST (= 18% total)
Exports:              Zero-rated
```

**Price conversion (inclusive ↔ exclusive of GST):**

```
P_excl_GST = P_incl_GST / 1.18
GST_payable = P_incl_GST - P_excl_GST = P_incl_GST * (0.18/1.18) = P_incl_GST * 0.1525
```

B2B buyers in India can claim Input Tax Credit (ITC) on GST paid — net cost to B2B buyer = P_excl_GST. B2C buyers cannot claim ITC — they bear full P_incl_GST.

GST export refund: software exports are zero-rated. Claim refund via Form RFD-01 on the GSTN portal. Refund processing typical 60–90 days.

**PPP Adjustment (World Bank ICP 2024 — T06 confirmed):**

```
India_price_PPP = Global_price * 0.29
```

The PPP factor 0.29 means $1 USD buys in India what approximately $0.29 buys in the US at market exchange rates — Indian price levels are ~29% of US levels. In practice, India SaaS vendors price at 0.25–0.35× US list (T06 confirmed).

**Optimal India Discount via Profit-Maximization (CRITICAL — revenue-maximization gives degenerate results):**

Define:
- P_US = US list price.
- P_IN = P_US * (1 - delta) = India price, where delta is the discount fraction.
- Q_IN(P_IN) = A * P_IN^epsilon (log-linear constant elasticity demand).
- MC_IN = marginal cost to serve India customer (typically lower than MC_US due to lower support costs).

**Why revenue-maximization fails:**

Revenue R_IN = Q_IN * P_IN = A * P_US^{1+epsilon} * (1-delta)^{1+epsilon}.

For elastic demand (epsilon < -1, so 1+epsilon < 0): R_IN is decreasing in delta → revenue maximized at delta = 0 (no discount). For inelastic demand: revenue maximized at delta → 1 (infinite discount). Both are corner solutions — **degenerate**.

**Profit-maximization (CORRECT approach):**

```
π(delta) = Q_IN * (P_IN - MC_IN) = A*(P_US*(1-delta))^epsilon * (P_US*(1-delta) - MC_IN)
```

First-order condition dπ/d(delta) = 0:

```
dπ/d(delta) = -A * P_US * (P_US*(1-delta))^{epsilon-1}
              * [(epsilon + 1)*P_US*(1-delta) - epsilon*MC_IN] = 0
```

Setting the bracket to zero (leading factors are nonzero):

```
(epsilon + 1)*P_US*(1-delta) = epsilon * MC_IN
P_US*(1-delta) = epsilon * MC_IN / (epsilon + 1) = MC_IN * |epsilon| / (|epsilon| - 1)
```

**Lerner-Optimal India Price:**

```
P_IN* = MC_IN * |epsilon| / (|epsilon| - 1)
```

This is exactly the Lerner formula from M1, applied at the India marginal cost basis.

**Optimal Discount:**

```
delta* = 1 - P_IN* / P_US = 1 - MC_IN * |epsilon| / ((|epsilon| - 1) * P_US)
```

**Consistency check with PPP:** If MC_IN ≈ 0.5 * MC_US and US price is already Lerner-optimal (P_US = MC_US * |epsilon|/(|epsilon|-1)):

```
delta* = 1 - (0.5 * MC_US * |epsilon|/(|epsilon|-1)) / (MC_US * |epsilon|/(|epsilon|-1))
       = 1 - 0.5 = 0.50 (50% India discount)
```

With MC_IN ≈ 0.6 * MC_US → delta* ≈ 40%. Consistent with observed India vendor practice of 25–35% off US list (higher MC_IN estimate → smaller discount), T06 confirmed.

**Formula summary:**

```
P_excl_GST = P_incl_GST / 1.18                  [SAC 998314 GST]
P_India_PPP = Global_price * 0.29                [World Bank ICP 2024]
P_IN_optimal = MC_IN * |epsilon| / (|epsilon| - 1)   [Lerner at India MC]
delta* = 1 - P_IN_optimal / P_US                 [profit-optimal discount]
```

**Worked Example:** US SaaS $300/month. India MC_IN = $50 (lower support cost). India |epsilon| = 2.5 (more price-sensitive than US).

```
P_IN* = 50 * 2.5/1.5 = $83.33/month
delta* = 1 - 83.33/300 = 0.722 = 72% discount
P_IN in INR = $83.33 * 84 = Rs 7,000/month
Ratio to US = 83.33/300 = 27.8% ≈ 29% PPP factor — consistent
```

GST on Rs 7,000: customer pays Rs 7,000 * 1.18 = Rs 8,260 inclusive (B2C) or Rs 7,000 + ITC (B2B).

**Practitioner Interpretation:** Optimal India price = Lerner price at India marginal cost basis. Lower India MC → lower India price. Validate against PPP factor: P_IN*/P_US should be in range 0.25–0.35 for typical India SaaS. If model gives a ratio outside this range, re-examine MC_IN estimate. GST 18% adds to the invoice price; ensure enterprise customers understand the ITC recovery path.

**Boundary Conditions:** |epsilon| ≤ 1 (inelastic): Lerner formula gives zero or negative denominator — undefined. Real India markets have substitutes; minimum |epsilon| ≈ 1.2 is a practical floor. MC_IN must be positive — subsidies break the formula. Revenue-maximization must never be used for India PPP pricing — see above.

**India Regulatory Values:**
- GST SAC 998314: 18% IGST cross-state; 9% CGST + 9% SGST intra-state (T06 confirmed).
- Exports zero-rated; refund via RFD-01 (T06 confirmed).
- India PPP factor: ~0.29× US prices (World Bank ICP 2024, T06 confirmed).
- India vendor discount practice: 0.25–0.35× US list (T06 confirmed).
- RBI Transfer Pricing: Section 92 Income Tax Act arm's-length pricing; APA (Advance Pricing Agreement) process for related-party transactions.

---

## 7. Anti-Patterns to Avoid

- **Presenting NRR without GRR alongside it (or vice versa)**: per §1.3's critical rule, NRR alone hides whether growth comes from genuine expansion or is masking underlying contraction, while GRR alone ignores the expansion flywheel that justifies premium valuations — the two metrics answer different questions and neither substitutes for the other.
- **Including one-time setup fees, professional services, or unguaranteed usage overages in MRR**: per §1.1, MRR is specifically the normalized, predictable monthly revenue from active subscriptions — folding in non-recurring or variable revenue inflates MRR with amounts that won't reliably repeat, corrupting every downstream metric (ARR, NRR, LTV) computed from it.
- **Treating an LTV:CAC ratio above 5:1 as purely a positive signal**: per §2.3's benchmark table, a ratio this high is explicitly flagged as a potential under-investing-in-growth signal, not an unambiguous win — it suggests the company could be spending more on acquisition to capture market faster rather than banking excess unit-economics headroom.
- **Using simple (undiscounted) LTV for high-stakes capital-allocation or long-payback-period decisions**: per §2.2, `LTV_simple = ARPU * GM / ch` ignores the time value of money entirely — for decisions where payback period or discount rate meaningfully affects the answer, the DCF-adjusted `LTV_DCF = ARPU * GM * (1-ch) / (ch + r/12)` is the version that actually reflects present value.
- **Conflating logo churn with revenue churn when forecasting or reporting churn health**: per §5.3, these can diverge sharply — losing many small customers produces high logo churn but low revenue churn, while losing a few enterprise accounts produces the opposite; revenue churn is the more important figure for revenue forecasting specifically, and reporting logo churn as if it captures the same information overstates or understates the actual revenue impact.
- **Treating the Van Westendorp Optimal Price Point (OPP) as the revenue-maximizing price**: per §3.4's explicit note, OPP is the psychologically optimal price that minimizes combined rejection from both "too cheap" and "too expensive" ends — it must be multiplied by expected demand at each candidate price within the Acceptable Price Range to actually identify the revenue-optimal point, not read directly off the survey intersection.
- **Defaulting to cost-plus pricing as the primary SaaS pricing methodology**: per §3.2, cost-plus is rarely optimal for SaaS specifically because marginal cost is near zero — it serves only as a price-floor sanity check, and setting the actual price this way abandons the value captured between marginal cost and economic value to customer (§3.1) that value-based pricing is built to capture.
- **Citing the Magic Number thresholds (>0.75 healthy, >1.0 efficient) as independently confirmed benchmarks**: per §2.4, this figure is explicitly training knowledge requiring citation to OpenView/SaaS Capital for external use, not a web-search-confirmed number like the NRR/GRR/CAC-payback benchmarks elsewhere in this skill — presenting it with the same confidence level as the confirmed figures misrepresents its evidentiary basis.

## 8. India-Specific Layer

### 7.1 GST Framework for SaaS Pricing

**SAC Code 998314** covers "Information technology (IT) consulting and support services." All SaaS and cloud software subscriptions fall under this SAC.

Tax rates:
- Cross-state B2B or B2C transactions: **18% IGST** (Integrated GST).
- Intra-state transactions: **9% CGST + 9% SGST** (combined 18%).
- Software exports to foreign clients: **Zero-rated** (no GST liability).

**Invoice requirements:**
- B2B invoices must show GSTIN of both parties and apply correct CGST/SGST (intra-state) or IGST (inter-state).
- Subscription invoices on a recurring basis each constitute a separate taxable supply.
- GST payment due by 20th of the following month.

**ITC (Input Tax Credit):** B2B buyers can claim full ITC on GST paid on SaaS subscriptions, provided the SAC code is correctly declared and the supplier is GSTIN-registered. Net GST cost to B2B customer = zero (recovered via ITC).

**Export refund process (RFD-01):** Software exported to foreign clients → zero-rated supply. File Form RFD-01 on GSTN portal. Refund credited to bank within 60–90 days. Maintain FIRC (Foreign Inward Remittance Certificate) from bank as documentary evidence.

### 7.2 India SaaS Pricing Norms

**Enterprise SaaS (India domestic):**
- Typical ARR range: Rs 25–75 lakhs per customer (NASSCOM SaaS Survey 2024, training fallback).
- Per-seat pricing: Rs 800–5,000/user/month depending on product category.
- Pricing often quoted excluding GST; enterprise contracts explicitly state "plus GST as applicable."

**SMB SaaS (India domestic):**
- Typical ARR range: Rs 2–8 lakhs per customer.
- Per-seat pricing: Rs 100–800/user/month.

**India vs global price point comparison:**
- India list price typically 25–35% of US list (World Bank PPP 0.29×, confirmed T06 Search 2).
- India enterprise discounts common: 30–50% off list (in addition to the India list already being PPP-adjusted).
- Do not use USD pricing for India market — quote in INR to eliminate FX risk objection.

### 7.3 RBI Transfer Pricing (Related-Party Transactions)

Under Section 92 of the Income Tax Act 1961, transactions between related parties (Indian subsidiary and foreign parent) must be priced at arm's length.

**Transfer pricing methods:**
- TNMM (Transactional Net Margin Method): most commonly used for service companies.
- CUP (Comparable Uncontrolled Price): used for direct product/service comparisons.
- RPSM (Residual Profit Split Method): for intangible-heavy transactions.

**Advance Pricing Agreement (APA):**
- Bilateral APA with foreign tax authorities: locks in transfer pricing methodology for 5 years.
- Reduces penalty exposure under Section 271(1)(c) (up to 300% of tax shortfall).

Apply M6 profit-maximization formula when deriving India prices that also must satisfy TNMM comparability test. If P_IN* < P25 of comparables, adjust upward to P25 to maintain arm's-length compliance.

### 7.4 India CAC Differences from Global Benchmarks

- India enterprise sales cycle: 4–9 months for deals > Rs 25 lakhs TCV (training fallback).
- India CAC for enterprise: lower absolute cost in USD but as % of ACV often higher than US (smaller ACVs in India).
- India inside sales / SDR fully-loaded cost: Rs 8–18 lakhs/year (vs $80–150K in US).
- India field sales (Tier-1 cities): Rs 18–35 lakhs/year fully-loaded.
- India digital acquisition (performance marketing): CPL (cost per lead) Rs 2,000–15,000 depending on category.

**Implication for LTV:CAC calculation in India:** Use INR-denominated ARPU and CAC. Do not apply USD LTV:CAC benchmarks directly to INR-priced products without adjusting for Indian ARPU levels.

### 7.5 India NRR/GRR Expectations

India-specific benchmarks (NASSCOM/SaaSBOOMi estimates — training fallback; verify with SaaSBOOMi 2024 survey):

- Median NRR: 108–115% (higher than global median 106% for venture SaaS, due to expansion motion in seat-based products).
- Median GRR: 88–93% (slightly below global enterprise due to higher SMB mix in India domestic market).
- Churn pressure source: budget cycles in India (April–March fiscal year), decision-maker turnover, and price renegotiations at contract renewal.

### 7.6 DPIIT Startup Pricing Considerations (Section 80-IAC)

DPIIT-recognized startups qualifying under Section 80-IAC enjoy 100% profit deduction for 3 consecutive years out of first 10. This affects DCF LTV modeling:

```
Effective_tax_rate = 0% during elected years (vs 25.168% normally)
LTV_DCF_post_tax = LTV_DCF * (1 - tax_rate)
```

During the tax holiday, post-tax LTV is identical to pre-tax LTV. This materially improves the NPV of the business during early growth years. Model LTV:CAC with zero tax rate during 80-IAC years; switch to 25.168% effective rate thereafter.

---

## 9. Response Rules

### 9.1 Always Present NRR AND GRR Together

NRR without GRR is incomplete and misleading. NRR can exceed 100% even with severe gross churn if expansion is high enough. GRR without NRR hides the expansion flywheel. Always report both numbers simultaneously with their respective benchmarks.

```
REQUIRED reporting pattern:
  NRR: [value]% (benchmark: venture-SaaS median 106%; enterprise 115-125%)
  GRR: [value]% (benchmark: median 90%; enterprise 90-97%; best-in-class ≥95%)
```

### 9.2 Flag LTV:CAC > 5 as Potential Under-Investment

LTV:CAC > 5:1 can indicate under-investment in growth rather than exceptional efficiency. If the addressable market is large and competitors are investing aggressively, a company with LTV:CAC = 6 may be leaving ARR on the table. Flag this to the user and ask: "Is the growth rate in line with market opportunity? Are you CAC-constrained or market-constrained?"

### 9.3 Report Van Westendorp OPP with Bootstrap CI

Always accompany OPP with its 95% bootstrap CI (B=1,000 resamples). An OPP without CI is statistically incomplete. A wide CI (>30% relative width) signals the sample size is insufficient; recommend n ≥ 200.

### 9.4 Distinguish India GST-Inclusive vs GST-Exclusive Pricing

When presenting India prices, always specify whether the amount is GST-inclusive or GST-exclusive. Enterprise B2B customers care about GST-exclusive price (they recover ITC); B2C and small businesses care about GST-inclusive price (their out-of-pocket cost).

### 9.5 Use Monthly Churn Rates Consistently

Do not mix monthly and annual churn rates in the same model. LTV_DCF uses monthly churn (ch) and monthly discount (r/12). Always verify units before computing. Converting: annual churn A_ch corresponds to monthly ch = 1 - (1 - A_ch)^{1/12}.

### 9.6 CAC Payback 18 Months is a Median, Not a Target

The 18-month CAC payback confirmed for 2024 is the industry median. For a given business, optimal payback depends on market growth rate, competitive dynamics, and available capital. In rapidly growing markets with large opportunities, accepting 24-month payback to grow faster may be rational. Do not present 18 months as a universal ceiling.

### 9.7 Confirm Price Survey Language and Currency for India

Van Westendorp surveys for India must be administered in INR. Responses in USD or vague descriptions should be excluded or normalized. Ask prices as round-number INR amounts within a plausible range for the product category (e.g., Rs 1,000–Rs 1,00,000 for enterprise SaaS per year).

---

## 10. What Not to Do

- **Do not use revenue-maximization pricing for India market without a profit constraint.** Revenue-maximization with constant elasticity demand produces degenerate corner solutions (either no discount or 100% discount). Always use profit-maximization via the Lerner formula at India MC basis (M6).
- **Do not present Van Westendorp OPP without bootstrap confidence interval.** A single OPP number without CI conveys false precision. Always run B=1,000 bootstrap resamples.
- **Do not mix monthly and annual churn in the same LTV calculation.** Use monthly throughout and clearly label units.
- **Do not apply USD-denominated LTV:CAC benchmarks to INR-priced products without PPP adjustment.** India ARPU is fundamentally lower; the ratio calculation must use consistent currency.
- **Do not report NRR alone.** Always pair with GRR to give a complete picture of retention health.
- **Do not use cost-plus pricing as the primary pricing methodology for SaaS.** With near-zero marginal cost for additional users, cost-plus severely underprices the product. Use value-based pricing (EVC model) or elasticity-based Lerner pricing as primary methods.
- **Do not assume CAC payback ≤ 18 months is always achievable.** Enterprise SaaS with long sales cycles may structurally require 24–30 month payback. The goal is LTV:CAC ≥ 3:1 with a clear path to payback within the fundraising horizon.
- **Do not conflate logo churn and revenue churn.** They can diverge significantly. Revenue forecasting requires revenue churn, not logo churn.
- **Do not apply India NRR/GRR benchmarks (108–115% NRR, 88–93% GRR) as confirmed.** These are training fallback values. Cite the SaaSBOOMi 2024 survey for verification.
- **Do not omit the IGST vs CGST/SGST distinction.** Cross-state invoices use IGST (single line); intra-state invoices split into CGST and SGST. The wrong GST type invalidates ITC for the buyer and creates compliance risk.

---

## 11. Output Expectations

**Pricing Analysis Output:**
- Demand curve with estimated elasticity epsilon (with confidence interval from regression).
- Profit-maximizing price P* via Lerner condition.
- Iso-profit curve overlay showing sensitivity to volume assumptions.
- India PPP-adjusted price (P_IN*) with GST-inclusive and exclusive versions.

**Van Westendorp Output:**
- Four CDFs plotted (or described) over the tested price range.
- Four intersection points: OPP, IDP, PMC, PME.
- Acceptable price range [PMC, PME].
- Bootstrap 95% CI for OPP (B = 1,000).
- Recommendation: recommended price point, rationale relative to OPP and competitive pricing.

**Revenue Retention Output:**
- NRR and GRR side-by-side with segment benchmark comparison.
- MRR waterfall (new / expansion / contraction / churn) for the analysis period.
- Steady-state ARR projection given current NRR and new ARR run rate.
- Cohort revenue matrix (top 3–5 acquisition cohorts).

**Freemium Funnel Output:**
- Prior specification with justification.
- Posterior mean and 95% HDI after observed data.
- A/B test P(B > A) with recommendation (go / wait / inconclusive).
- Required sample size to reach P(B > A) > 0.95 (if not yet achieved).

**LTV/CAC Output:**
- LTV_DCF with all input assumptions listed (ARPU, GM, ch, r).
- CAC payback T* in months with feasibility check.
- LTV:CAC ratio with benchmark comparison.
- Sensitivity table: LTV:CAC at ±25% ARPU, ±25% churn, ±25% CAC.

---

## 12. Skill Scope

**In scope:**
- SaaS revenue metrics: MRR, ARR, NRR, GRR, NDR, expansion MRR, churn MRR.
- Price elasticity modeling, demand curve estimation, Lerner-optimal pricing.
- Van Westendorp Price Sensitivity Meter: four curves, four intersections, bootstrap CI.
- Cohort revenue analysis: cohort matrix, decay curves, steady-state ARR.
- Freemium Bayesian conversion: Beta-Binomial posterior, HDI, A/B test.
- Cohort LTV DCF: closed-form formula, CAC payback exact derivation, LTV:CAC.
- India GST SAC 998314 pricing, PPP localization via profit-maximization, RBI transfer pricing.
- India pricing norms and NRR/GRR benchmarks.

**Out of scope:**
- Sales pipeline CRM mechanics → see `sales-pipeline-core`.
- Market sizing (TAM/SAM/SOM) and Bass diffusion → see `market-expansion-core`.
- India government tender scoring and DPIIT/GeM regulations → see `india-bd-core`.
- PLG/SLG go-to-market motion economics → see `market-expansion-core`.
- SaaS financial modeling beyond unit economics (P&L, balance sheet) → see `fintech-mathematics-expert`.

---

## 13. Version

**Version:** 1.0.1 — 2026-07-27 — Added §7 Anti-Patterns to Avoid (8 pitfalls spanning NRR/GRR presentation, MRR contamination, LTV:CAC over-investment misreading, simple-vs-DCF LTV misuse, logo-vs-revenue churn conflation, Van Westendorp OPP misinterpretation, cost-plus SaaS pricing, and Magic Number sourcing); renumbered §8-12 to §9-13.

**Version:** 1.0.0
**Domain:** Agile Business & Revenue Intelligence (Domain 41)
**Math Master:** `agile-business-mathematics-expert` (opus) — delegate all derivations requiring optimization proofs, distribution fitting, or numerical methods.
**Research Sources:** T06 (BD research, web-confirmed benchmarks); T08 (synthesis); T10 (M1–M6 verbatim derivations from opus math expert).
**Last Updated:** 2026-05-17
