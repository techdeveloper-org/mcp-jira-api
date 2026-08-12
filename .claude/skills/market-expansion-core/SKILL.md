---
name: market-expansion-core
description: "Provides market sizing mathematics (TAM/SAM/SOM), go-to-market motion modeling (PLG/SLG/CLG), Bass diffusion S-curve analysis, competitive concentration metrics, and partnership NPV computation. Use when sizing new markets, designing GTM strategies, forecasting product adoption curves, evaluating competitive landscape concentration, or modeling partnership economics. Keywords: TAM SAM SOM market sizing, Bass diffusion S-curve, PLG SLG GTM motion, Herfindahl-Hirschman Index competitive concentration, partnership NPV, CAC LTV ratio optimization, NASSCOM India IT export market."
allowed-tools: Read,Glob,Grep
user-invocable: true
---


<!-- generated-by: claude-global-library/tools/project_sync -->
<!-- source: skills/market-expansion-core/SKILL.md -- edit the library, then re-run sync_project.py -->

# market-expansion-core

## Description

This skill provides the mathematical foundations for market expansion strategy — from quantifying how large a market is, to modelling how products diffuse through it, to assessing competitive structure and partnership economics. It covers top-down and bottom-up TAM/SAM/SOM sizing with Monte Carlo confidence intervals, Bass diffusion ODE derivation and non-linear parameter fitting, PLG/SLG/CLG unit economics with Magic Number optimization, Herfindahl-Hirschman competitive concentration, and partnership NPV with sensitivity analysis. India-specific content covers NASSCOM IT-BPM market data, Tier-2 city expansion economics, PPP-adjusted sizing, and GeM/DPIIT context.

---

## 1. TAM/SAM/SOM Market Sizing

### 1.1 Definitions

| Level | Meaning | Typical Use |
|-------|---------|-------------|
| TAM (Total Addressable Market) | Revenue opportunity if 100% market share globally | Investor narrative, market thesis |
| SAM (Serviceable Addressable Market) | Portion TAM your product and geography can serve | Realistic competitive set |
| SOM (Serviceable Obtainable Market) | Realistic share you can win in 3-5 years | Go-to-market planning, quota setting |

### 1.2 Top-Down Sizing

Begin with a macro market figure from an industry report and multiply by a relevance fraction:

```
TAM_top_down = total_market_revenue * relevance_fraction
```

Example: Global HR software market $30B; India share 3%; India TAM = $900M.

Strengths: fast, cited; weaknesses: relevance fraction is arbitrary, over-counts adjacent segments.

### 1.3 Bottom-Up Sizing

Count addressable buyers and multiply by unit economics:

```
TAM_bottom_up = N_addressable_buyers * ARPU
```

Example: 50,000 mid-large Indian enterprises in HR function; ARPU Rs 6,00,000/yr; TAM = Rs 3,000 Cr.

Strengths: grounded in real buyer counts; weaknesses: requires accurate segment census.

### 1.4 Hybrid Validation

Run both methods. If top-down and bottom-up agree within 30%, the estimate is credible. If they diverge by more than 2x, investigate the gap before presenting to investors.

### 1.5 SAM and SOM Derivation

```
SAM = TAM * geographic_fit * product_fit

SOM = SAM * achievable_market_share
```

- `geographic_fit`: fraction of TAM reachable given language, regulation, and distribution presence.
- `product_fit`: fraction of SAM where your product matches the primary use case.
- `achievable_market_share`: 1-5% for new entrants in mature markets; up to 20% for disruptive products in emerging segments.

### 1.6 Churn-Adjusted Reachable Market

Gross TAM is a stock; churn converts it into a flow problem. Annual churn rate `ch` erodes the installed base:

```
Net_reachable_market_yr_n = SOM * (1 - ch)^n
```

Over a 5-year horizon with 15% annual churn, reachable market degrades to (0.85)^5 = 44% of year-0 SOM. This means winning new logos is required merely to maintain position, not grow. Incorporate this into revenue forecasts by adding a gross-new-logo acquisition requirement:

```
Required_new_logos_yr_n = SOM_target - SOM_current * (1 - ch)
```

Always present churn-adjusted SOM alongside gross SOM when building multi-year market models.

### 1.7 Regression-Based Validation

For products with historical revenue data, regress observed revenue against market size proxies (industry GDP, headcount, digital penetration index) to calibrate the TAM multiple:

```
Revenue = alpha + beta * MarketProxy + epsilon
beta_hat = Cov(Revenue, Proxy) / Var(Proxy)
```

If beta_hat * current Proxy diverges from bottom-up TAM by more than 50%, revisit the proxy.

---

## 2. Bass Diffusion Model

### 2.1 The Core ODE

The Bass model describes cumulative adoption N(t) of an innovation through a differential equation:

```
dN/dt = [p + q * N(t)/M] * [M - N(t)]
```

- `p` = innovation coefficient: rate at which non-adopters adopt independently of existing adopters (mass media, cold outreach).
- `q` = imitation coefficient: rate at which non-adopters adopt because of contact with adopters (word-of-mouth, virality).
- `M` = market potential: total eventual adopters.
- `N(t)` = cumulative adopters at time t.

**Interpretation of the hazard function:** For a non-adopter at time t, the hazard rate of adoption is `p + q*N(t)/M`. At t=0, hazard = p (no adopters yet). As N grows, the social influence term q*N(t)/M amplifies adoption.

### 2.2 Confirmed Empirical Parameter Ranges

Research-confirmed ranges for software/SaaS (T06 Search 3, literature confirmed):

| Parameter | Typical Range | Literature Average | Segment Notes |
|-----------|--------------|-------------------|---------------|
| p (innovation) | 0.01 – 0.03 | 0.035 | B2B enterprise: 0.003–0.015; PLG/consumer: 0.01–0.030 |
| q (imitation) | 0.20 – 0.40 | 0.390 | B2B enterprise: 0.15–0.30; PLG/viral: 0.25–0.45 |

**Always state p and q as calibration ranges, not fixed constants.** Every product requires NLS fitting to its own adoption data. Use the above ranges as initialization bounds and sanity checks only.

India-specific calibration: mobile internet and SaaS adoption in India shows q values near the upper range (0.35–0.45) due to high social network density and referral-driven B2B sales. Use `p = 0.02, q = 0.40` as India B2B SaaS central estimate before fitting.

### 2.3 Closed-Form Solution

Solving the separable ODE by partial fractions yields:

```
N(t) = M * (1 - e^{-(p+q)t}) / (1 + (q/p) * e^{-(p+q)t})
```

Verification:
- At t = 0: numerator = 0, so N(0) = 0. Correct.
- As t → ∞: exponential terms → 0, so N(∞) = M. Correct.
- Derivative at t = 0: dN/dt = p * M. Correct (only innovation term active).

### 2.4 Peak Adoption Time (Inflection Point of S-Curve)

The sales rate dN/dt peaks when d²N/dt² = 0. Let z = e^{-(p+q)t}:

```
d^2N/dt^2 = 0  =>  z = p/q
=> e^{-(p+q)t*} = p/q
=> t* = ln(q/p) / (p+q)
```

At peak:

```
dN/dt |_{t*} = M * (p+q)^2 / (4q)
```

Cumulative adoption at peak:

```
N(t*) = M * (q - p) / (2q) = (M/2) * (1 - p/q)
```

For typical India SaaS (p = 0.02, q = 0.40): N(t*)/M = (1 - 0.05)/2 = 0.475. About 47.5% of the market has adopted when sales rate peaks.

**Logistic growth special case:** When p → 0, the Bass model reduces to the logistic growth equation:

```
dN/dt = q * (N/M) * (M - N)
```

with inflection at N = M/2 (exactly half the market). This is derived by setting d²N/dt² = 0 in the logistic equation, which yields N = M/2. For pure word-of-mouth products, the logistic model applies.

### 2.5 NLS Parameter Fitting via Gauss-Newton

Non-linear least squares (NLS) is required because the Bass closed form is non-linear in p, q, M. OLS on the linearized form introduces bias and should not be used.

**Algorithm:**

```
Initialize: beta^0 = (p_0, q_0, M_0) = (0.01, 0.30, 2 * max(N_observed))

Repeat:
  1. Compute residuals: r_i = N_obs(t_i) - N(t_i; beta^k)  for i = 1..n_obs
  2. Compute Jacobian J (n_obs x 3):
       J_{i,1} = -(dN/dp) evaluated at (beta^k, t_i)
       J_{i,2} = -(dN/dq) evaluated at (beta^k, t_i)
       J_{i,3} = -(dN/dM) = -(N/M)
  3. Solve normal equations: (J^T J) * delta = -J^T r
  4. Update: beta^{k+1} = beta^k + delta
  5. Stop when ||delta|| < 1e-6

Validate: p > 0, q > 0, M > max(N_observed)
Report: R^2 = 1 - SS_res/SS_tot, RMSE
```

The negative sign in J_{i,j} arises because residual r_i = N_obs - N_model, so ∂r_i/∂beta_j = -∂N/∂beta_j.

Minimum data: T ≥ 3 observed time periods. With T = 3, M is weakly identified — fix M to TAM estimate if fewer than 5 periods available.

### 2.6 Analytical Jacobian for Gauss-Newton

Let f(t) = 1 - e^{-(p+q)t}, g(t) = 1 + (q/p) * e^{-(p+q)t}, N(t) = M * f/g.

**Partial with respect to M:**

```
dN/dM = f/g = N/M
```

**Partial with respect to p:**

df/dp = t * e^{-(p+q)t}

dg/dp = (-q/p^2) * e^{-(p+q)t} + (q/p) * t * e^{-(p+q)t} = (q * e^{-(p+q)t} / p) * (t - 1/p)

```
dN/dp = M * (df/dp * g - f * dg/dp) / g^2
      = M * e^{-(p+q)t} * [t * (1 + (q/p)*e^{-(p+q)t}) - (1-e^{-(p+q)t}) * (q/p) * (t - 1/p)] / [1 + (q/p)*e^{-(p+q)t}]^2
```

**Partial with respect to q:**

df/dq = t * e^{-(p+q)t}   (same form as df/dp)

dg/dq = (1/p) * e^{-(p+q)t} + (q/p) * t * e^{-(p+q)t} = (e^{-(p+q)t}/p) * (1 + q*t)

```
dN/dq = M * (df/dq * g - f * dg/dq) / g^2
      = M * e^{-(p+q)t} * [t * (1 + (q/p)*e^{-(p+q)t}) - (1-e^{-(p+q)t}) * (1/p) * (1 + q*t)] / [1 + (q/p)*e^{-(p+q)t}]^2
```

These three analytical partials form the columns of J required for each Gauss-Newton iteration. Assembling them numerically avoids finite-difference approximation errors.

---

## 3. Market Penetration Dynamics (Logistic Growth)

### 3.1 Logistic Growth Equation

When adoption is driven purely by imitation (p ≈ 0), the Bass model simplifies to:

```
dN/dt = r * N(t) * (1 - N(t)/M)
```

where r = q is the imitation/growth rate. This is the standard logistic equation.

### 3.2 Closed-Form Solution

```
N(t) = M / (1 + ((M - N_0)/N_0) * e^{-r*t})
```

where N_0 = N(0) = initial adopter count.

### 3.3 Inflection Point Derivation

Differentiate twice and set d²N/dt² = 0:

```
d^2N/dt^2 = r * (dN/dt) * (1 - 2N/M) = 0
```

This equals zero when N = M/2 (since dN/dt ≠ 0 before saturation). The inflection point occurs at exactly half the market potential — the point of fastest adoption.

### 3.4 Saturation Analysis

Market share trajectory:

```
s(t) = N(t)/M = 1 / (1 + c_0 * e^{-r*t})    where c_0 = (M - N_0)/N_0
```

Market share approaches 1 asymptotically. Saturation threshold 90% reached at:

```
t_90 = ln(9 * c_0) / r
```

For India SaaS (r = 0.40, c_0 = 100 corresponding to 1% initial penetration): t_90 = ln(900)/0.40 = 6.9/0.40 = 17.2 periods.

---

## 4. Competitive Analysis Framework

### 4.1 Herfindahl-Hirschman Index (HHI)

The HHI measures market concentration across all firms:

```
HHI = sum_i s_i^2 * 10,000
```

where s_i is the decimal market share of firm i (s_i ∈ [0, 1], Σs_i = 1).

**Derivation:** HHI is defined as the probability that two randomly selected purchase occasions go to the same firm. If a customer chooses firm i with probability s_i, then P(same firm) = Σs_i² = HHI/10,000. A higher HHI means greater concentration.

**Interpretation thresholds (T06 confirmed):**

| HHI Value | Market Structure |
|-----------|-----------------|
| < 1,500 | Competitive (e.g., cloud infrastructure, SaaS productivity) |
| 1,500 – 2,500 | Moderately concentrated (e.g., India CRM: ~2,200-2,700) |
| ≥ 2,500 | Highly concentrated / oligopoly |

**Worked Example:** India CRM market with 5 firms, shares: [0.35, 0.25, 0.20, 0.12, 0.08].

```
HHI = (0.35^2 + 0.25^2 + 0.20^2 + 0.12^2 + 0.08^2) * 10,000
    = (0.1225 + 0.0625 + 0.04 + 0.0144 + 0.0064) * 10,000
    = 0.2458 * 10,000 = 2,458   [moderately concentrated]
```

### 4.2 Cournot N-Firm Symmetric Nash Equilibrium

Under linear inverse demand P = a - bQ (where Q = Σq_i), each firm maximizes profit:

```
pi_i = q_i * (P - MC_i) = q_i * (a - b*Q - MC_i)
```

First-order condition (symmetric firms with identical MC):

```
d_pi_i / d_q_i = a - b*(Q + q_i) - MC = 0
=> q* = (a - MC) / ((n+1) * b)
=> Q* = n * (a - MC) / ((n+1) * b)
=> P* = (a + n*MC) / (n+1)
```

### 4.3 Lerner Index

The Lerner Index measures market power (markup over MC):

```
L = (P* - MC) / P* = 1 / (n * |epsilon|)
```

where epsilon = price elasticity of demand (|epsilon| > 0). Derivation: substitute P* into (P-MC)/P and simplify using the demand elasticity at equilibrium.

**Interpretation:** Low n (few competitors) or low |epsilon| (inelastic demand) produces high Lerner Index (high margins).

### 4.4 Entrant Price Premium Sustainability

A new entrant facing Bertrand undercutting threats can sustain a price premium only up to:

```
Delta_P / P <= 1 / (|epsilon| * n * (n+1))
```

This bounds the maximum differentiation premium before incumbents undercut and capture the market.

### 4.5 Porter's Five Forces Quantification

Five Forces provides a qualitative framework; quantify each dimension with a proxy score (0-10):

| Force | High Score Indicates | Proxy Metric |
|-------|---------------------|-------------|
| Supplier power | Few suppliers, switching costs high | Supplier HHI, switching cost as % COGS |
| Buyer power | Concentrated buyers, low switching cost | Buyer HHI, churn rate |
| Threat of new entry | Low barriers | 1 / (CAC ratio + regulatory score) |
| Threat of substitutes | Many alternatives | Substitute product count * cross-price elasticity |
| Rivalry intensity | HHI in competitive range | (10,000 - HHI) / 10,000 |

Composite score = 0.2 * sum(Force_i). Score > 6.5 = structurally attractive market.

---

## 5. PLG/SLG/CLG Unit Economics and Blended GTM

### 5.1 GTM Motion Definitions

| Motion | Description | Typical CAC | Typical ARPU |
|--------|-------------|-------------|-------------|
| PLG (Product-Led Growth) | Product is primary acquisition channel; self-serve | Low ($100–$500) | Low ($20–$100/mo) |
| SLG (Sales-Led Growth) | Sales-assisted acquisition; demos and outbound | High ($3,000–$20,000) | High ($200–$3,000/mo) |
| CLG (Community-Led Growth) | Community, events, user groups drive acquisition | Medium | Medium |

### 5.2 CAC per Motion

```
CAC_motion = S&M_spend_motion / N_customers_won_motion
```

### 5.3 LTV per Motion

Using the constant-churn DCF closed form (see Deep Mathematical Foundations M3):

```
LTV_motion = ARPU_motion * GM / (ch_motion + r/12)
```

Target LTV:CAC ≥ 3:1 for any motion. PLG typically achieves LTV:CAC 5–8:1 due to low CAC. SLG LTV:CAC 2–4:1 depending on segment.

### 5.4 Magic Number

The Magic Number measures S&M efficiency:

```
MN_Q = Delta_Net_New_ARR_Q / S&M_spend_{Q-1}
```

**Thresholds (T06 training fallback; cite OpenView/SaaS Capital for external use):**
- MN > 1.0: highly efficient growth; recoup S&M in < 12 months.
- MN 0.75–1.0: healthy growth; payback 12–16 months.
- MN 0.5–0.75: marginal; investigate churn or conversion.
- MN < 0.5: inefficient; reduce S&M or fix product/market fit.

### 5.5 Optimal PLG/SLG Split

Minimize blended CAC subject to a revenue target R_target:

```
min  blended_CAC = (CAC_PLG * n_PLG + CAC_SLG * n_SLG) / (n_PLG + n_SLG)
s.t. n_PLG * conv_PLG + n_SLG * conv_SLG >= R_target / ARPU
     n_PLG, n_SLG >= 0
```

KKT optimality condition: at an interior optimum, the cost per acquired customer must equalize across motions:

```
CAC_PLG / conv_PLG = CAC_SLG / conv_SLG
```

**Decision rule:** If CAC_PLG/conv_PLG < CAC_SLG/conv_SLG, shift incremental spend to PLG until ratios equalize. If PLG conversion capacity is saturated, accept higher blended CAC from SLG.

---

## 6. Churn-Adjusted Market Sizing

### 6.1 The Churn Erosion Problem

Gross TAM/SOM figures assume a static buyer pool. In subscription businesses, annual churn ch reduces the effective reachable market each year:

```
Net_reachable_pool_t = initial_pool * (1 - ch)^t
```

### 6.2 Long-Run Addressable Market

The true long-run addressable market under constant churn, with N_new new-logo acquisitions per period, converges to a steady state:

```
N_steady_state = N_new / ch
```

Derivation: at steady state, N_ss = N_ss * (1-ch) + N_new → N_ss * ch = N_new → N_ss = N_new/ch.

**Example:** If annual churn = 15% and you sign 150 new logos/year, steady-state installed base = 150/0.15 = 1,000 customers.

### 6.3 Compound Churn Effect on Revenue

Revenue at time t given ARR_0 and annual net revenue retention NRR:

```
ARR_t = ARR_0 * NRR^t
```

For NRR > 1.0 (expansion outpaces churn), ARR grows without limit (subject to TAM cap). For NRR < 1.0, revenue decays.

Steady-state ARR from continuous new-logo additions at rate A_new/yr:

```
ARR_steady = A_new / (1 - NRR_monthly)    [monthly periods]
```

### 6.4 Gross TAM vs Net-Retention-Adjusted Reachable Market

- **Gross TAM:** all potential buyers, ignoring churn.
- **Net-retention-adjusted reachable market:** accounts for the fact that retaining a customer is cheaper than winning a new one. If NRR > 1.0, existing customers compound — the effective reachable market is larger than gross TAM would suggest.

Present both in market analysis. Investors with portfolio SaaS experience will expect churn-adjusted figures.

---

## 7. Deep Mathematical Foundations

### M1: TAM/SAM/SOM Market Sizing Mathematics

**Foundation:** Monte Carlo simulation (triangular distributions).

**Bottom-up TAM:**
```
TAM = N_addressable_buyers * ARPU
```

**SAM:**
```
SAM = TAM * geographic_fit * product_fit
```

**SOM:**
```
SOM = SAM * achievable_market_share
```

**Monte Carlo Confidence Interval for SOM:**

Each input is uncertain. Model using triangular distributions Tri(min, mode, max):

```
For trial = 1 to B = 10,000:
    TAM_b = sample Tri(TAM_low, TAM_mode, TAM_high)
    geo_b  = sample Tri(geo_low, geo_mode, geo_high)
    prod_b = sample Tri(prod_low, prod_mode, prod_high)
    share_b = sample Tri(share_low, share_mode, share_high)
    SOM_b = TAM_b * geo_b * prod_b * share_b
sort SOM_b
Report P5, P50, P95 percentile SOM.
```

Triangular CDF for inverse sampling (draw u ~ Uniform(0,1)):

```
For Tri(a, c, b):
  F(x) = (x-a)^2 / ((b-a)*(c-a))    for a <= x <= c
  F(x) = 1 - (b-x)^2 / ((b-a)*(b-c)) for c < x <= b
```

Invert: if u < (c-a)/(b-a), x = a + sqrt(u*(b-a)*(c-a)), else x = b - sqrt((1-u)*(b-a)*(b-c)).

**Worked Example:** India B2B SaaS HR-tech.

Bottom-up:
- N = 50,000 mid-large Indian enterprises; ARPU = Rs 6,00,000/yr.
- TAM = Rs 3,000 Cr.

geographic_fit = 0.70; product_fit = 0.50; SAM = Rs 1,050 Cr.
share = 0.03 (3% Year-3 target); SOM = Rs 31.5 Cr.

Monte Carlo: TAM ~ Tri(2500, 3000, 3500), geo ~ Tri(0.6, 0.7, 0.8), prod ~ Tri(0.4, 0.5, 0.6), share ~ Tri(0.02, 0.03, 0.04). With B=10,000:
- SOM P5 = Rs 15.3 Cr.
- SOM P50 = Rs 31.0 Cr.
- SOM P95 = Rs 54.2 Cr.

Wide P5–P95 range (3.5× ratio) reflects compounded uncertainty. If P95 SOM < target revenue, the market is too small. If P5 SOM > breakeven, expansion is low-risk.

---

### M2: Bass Diffusion Model — ODE Derivation and NLS Fitting [CRITICAL_GAP #2 RESOLVED]

**Foundation:** geometric series (closed form integration), Gauss-Newton (Newton-style updates).

**Bass ODE:**
```
dN/dt = [p + q * N(t)/M] * [M - N(t)]
```

- p = innovation coefficient (external influence / mass media).
- q = imitation coefficient (word-of-mouth, social proof).
- M = market potential.
- N(t) = cumulative adopters at time t.

**Hazard interpretation:** For a non-adopter at time t, the instantaneous probability of adoption = p + q*N(t)/M. At t=0, hazard = p (only innovators). As N grows, the social amplification term q*N/M accelerates adoption.

**Closed-Form Solution (Derivation from Separable ODE):**

Rearrange:
```
dN / ((p + qN/M)(M-N)) = dt
```

Apply partial fractions. The standard Bass integration yields:

```
N(t) = M * (1 - e^{-(p+q)t}) / (1 + (q/p) * e^{-(p+q)t})
```

**Verification:** N(0) = M*(1-1)/(1+q/p) = 0 ✓. N(∞) = M*(1-0)/(1+0) = M ✓.

**Peak Adoption Time (Inflection of S-Curve):**

Set d²N/dt² = 0. Let z = e^{-(p+q)t}:

```
d^2N/dt^2 = 0  =>  z = p/q
=> e^{-(p+q)t*} = p/q
=> t* = ln(q/p) / (p+q)
```

**Peak Sales Rate:**
```
dN/dt |_{t*} = M * (p+q)^2 / (4q)
```

**Cumulative Adoption at Peak:**
```
N(t*) = M * (q-p) / (2q)  =  (M/2) * (1 - p/q)
```

For (p, q) = (0.03, 0.38): N(t*)/M = (1 - 0.079)/2 = 0.46 (46% adopted by peak).

**NLS Fitting via Gauss-Newton — Analytical Jacobian (THE CRITICAL DERIVATION):**

Residual: r_i(beta) = N_obs(t_i) - N(t_i; p, q, M). Parameter vector beta = (p, q, M).

Gauss-Newton update:
```
beta^{k+1} = beta^k + (J^T J)^{-1} J^T r
```

where J_{ij} = -(dN/d_beta_j) evaluated at (beta^k, t_i) [negative because r = N_obs - N_model].

**Partial with respect to M (trivial):**
```
dN/dM = f/g = N/M     where f = 1-e^{-(p+q)t},  g = 1 + (q/p)*e^{-(p+q)t}
```

**Partial with respect to p:**

Let u = -(p+q)t.

df/dp = -e^u * (du/dp) = -e^u * (-t) = t * e^u

dg/dp = (-q/p^2)*e^u + (q/p)*t*e^u = (q*e^u/p)*(t - 1/p)

```
dN/dp = M * (df/dp * g - f * dg/dp) / g^2

      = M * e^{-(p+q)t} * [t*(1 + (q/p)*e^{-(p+q)t}) - (1-e^{-(p+q)t})*(q/p)*(t - 1/p)]
        / [1 + (q/p)*e^{-(p+q)t}]^2
```

**Partial with respect to q:**

df/dq = t * e^u  (same form)

dg/dq = (1/p)*e^u + (q/p)*t*e^u = (e^u/p)*(1 + q*t)

```
dN/dq = M * (df/dq * g - f * dg/dq) / g^2

      = M * e^{-(p+q)t} * [t*(1 + (q/p)*e^{-(p+q)t}) - (1-e^{-(p+q)t})*(1/p)*(1 + q*t)]
        / [1 + (q/p)*e^{-(p+q)t}]^2
```

**Full Gauss-Newton Algorithm:**
```
Initialize: beta^0 = (p_0, q_0, M_0) = (0.01, 0.30, 2 * max(N_obs))  [T06 confirmed]

Repeat until ||delta|| < 1e-6:
  1. Compute r_i = N_obs(t_i) - N(t_i; beta^k)  for i=1..n
  2. Assemble Jacobian J (n x 3):
       J_{i,1} = -(dN/dp) at (beta^k, t_i)
       J_{i,2} = -(dN/dq) at (beta^k, t_i)
       J_{i,3} = -(N/M)
  3. Solve (J^T J) delta = J^T r
  4. beta^{k+1} = beta^k + delta

Validate: p > 0, q > 0, M > max(N_obs)
Report: R^2, RMSE
```

**Worked Example:** Software adoption, 6 quarters: N_obs = [50, 150, 350, 600, 850, 980].

Initialize beta^0 = (0.01, 0.30, 1960) where 1960 = 2*980.
After ~8-10 Gauss-Newton iterations, converges to beta ≈ (0.012, 0.45, 1100).

t* = ln(0.45/0.012)/(0.012+0.45) = ln(37.5)/0.462 = 3.624/0.462 = 7.84 quarters.
Peak rate = 1100 * 0.462^2 / (4 * 0.45) = 1100 * 0.213 / 1.80 ≈ 130 adoptions/quarter.

---

### M3: PLG/SLG/CLG Unit Economics and Magic Number Optimization

**Foundation:** geometric series (F1), CLV from SK7/M5.

**CAC by GTM Motion:**
```
CAC_motion = S&M_spend_motion / N_won_motion
```

**LTV by Motion:**
```
LTV_motion = ARPU_motion * GM / (ch_motion + r/12)
```

**Magic Number:**
```
MN_Q = Delta_Net_New_ARR_Q / S&M_spend_{Q-1}
```
MN > 0.75 = healthy; MN > 1.0 = highly efficient (T06 training fallback).

**Constrained Optimization for Optimal PLG/SLG Split:**

Minimize blended CAC subject to revenue target R_target:

```
min  blended_CAC = (CAC_PLG * n_PLG + CAC_SLG * n_SLG) / (n_PLG + n_SLG)
s.t. n_PLG * conv_PLG + n_SLG * conv_SLG >= R_target / ARPU
     n_PLG, n_SLG >= 0
```

**Lagrangian:**
```
L = blended_CAC + lambda * (R_target/ARPU - sum_m n_m * conv_m)
```

**KKT optimality condition (interior solution):**
```
d_blended_CAC / d_n_PLG = lambda * conv_PLG
d_blended_CAC / d_n_SLG = lambda * conv_SLG
=> CAC_PLG / conv_PLG = CAC_SLG / conv_SLG = lambda
```

Allocate spend to equalize cost-per-won-deal across motions. If CAC_PLG/conv_PLG < CAC_SLG/conv_SLG, shift incremental spend toward PLG until ratios equalize or PLG capacity is exhausted.

**Worked Example:** SaaS startup, two motions:
- PLG: CAC = Rs 8,000; conv = 5%; ARPU = Rs 2,500/mo; GM = 75%; ch = 2%/mo; r = 14%/yr.
- SLG: CAC = Rs 4,00,000; conv = 25%; ARPU = Rs 25,000/mo.

LTV_PLG = 2500 * 0.75 / 0.03 = Rs 62,500. LTV:CAC = 62,500/8,000 = 7.8.
LTV_SLG = 25000 * 0.75 / 0.03 = Rs 6,25,000. LTV:CAC = 6,25,000/4,00,000 = 1.56.

Cost per won customer: PLG = 8000/0.05 = Rs 1,60,000. SLG = 4,00,000/0.25 = Rs 16,00,000.

PLG is 10x more capital-efficient per acquired customer. Decision: maximize PLG investment until conv capacity saturates (TAM of free-tier self-serve exhausted).

---

### M4: Herfindahl-Hirschman Index and Cournot Competitive Equilibrium

**Foundation:** game theory.

**HHI:**
```
HHI = sum_i s_i^2 * 10,000    where s_i = decimal market share
```

**Thresholds:** < 1,500 competitive; 1,500–2,500 moderate; ≥ 2,500 highly concentrated.

**Cournot N-Firm Symmetric Equilibrium (linear demand P = a - bQ):**

Profit: pi_i = q_i * (a - b*Q - MC). FOC: a - b*(Q+q_i) - MC = 0.

Symmetric Nash equilibrium:
```
q* = (a - MC) / ((n+1) * b)
Q* = n * (a - MC) / ((n+1) * b)
P* = (a + n*MC) / (n+1)
```

As n → ∞: P* → MC (perfect competition). As n = 1: P* = (a + MC)/2 (monopoly, profit-maximizing).

**Lerner Index:**
```
L = (P* - MC) / P* = 1 / (n * |epsilon|)
```

**Sustainable Entrant Price Premium:**
```
Delta_P / P <= 1 / (|epsilon| * n * (n+1))
```

**Worked Example:** India CRM — 5 firms, shares [0.35, 0.25, 0.20, 0.12, 0.08]:

HHI = (0.1225 + 0.0625 + 0.04 + 0.0144 + 0.0064) * 10,000 = 2,458. Moderately concentrated.

Cournot with n=5, a=200, b=0.001, MC=50:
- q* = 150 / (6 * 0.001) = 25,000 units.
- Q* = 125,000 units. P* = (200 + 250)/6 = 75.
- |epsilon| = P/(bQ) = 75/125 = 0.60.
- Lerner: L = 1/(5 * 0.60) = 0.333 (33% markup).
- Entrant premium: 1/(0.60 * 5 * 6) = 5.6%.

---

### M5: Partnership and Channel NPV Model

**Foundation:** NPV (F4), geometric series (F1).

**Cash Flow Structure:**
```
CF_t = Partner_Sourced_ARR_t * Rev_Share_to_us - Support_Cost_t - Onboarding_Cost_t
NPV = sum_{t=1}^{T} CF_t / (1+r)^t - I_0
```

Year-0 outflow I_0 = upfront integration + sales enablement.

**Discounted Payback Period:**
```
T_payback = min T  such that  sum_{t=1}^{T} CF_t / (1+r)^t >= I_0
```

**Partner Tier Rev-Share (T06 training fallback):**
- Reseller: 20–30% of deal value.
- Referral/Influencer: 10–15% of first-year ARR.
- OEM/White-label: 50–60% of end-customer revenue.

**Tornado Sensitivity Analysis:** Vary each input by ±20%; rank inputs by |ΔNPV|. This identifies the highest-leverage negotiation lever.

**Worked Example:** Reseller partnership, India:

I_0 = Rs 50 lakh. WACC r = 14% (India mid-cap tech, T06 training fallback).
- CF_1 = ARR_1 * 0.75 - support = 1 Cr * 0.75 - 5L = Rs 70L.
- CF_2 = 2 Cr * 0.75 - 10L = Rs 1.40 Cr.
- CF_3 = 3 Cr * 0.75 - 15L = Rs 2.10 Cr.

NPV = -50 + 70/1.14 + 140/1.14^2 + 210/1.14^3
    = -50 + 61.4 + 107.7 + 141.7 = Rs 260.8 lakh = Rs 2.61 Cr.

T_payback: cumulative discounted CF after Year 1 = Rs 61.4L > Rs 50L. Payback = 50/61.4 = 0.81 years.

Tornado: ARR growth assumption has the highest ΔNPV swing (~Rs 1.5 Cr at ±20%). Rev-share swing: ~Rs 75L. Support cost: minor (~Rs 15L). Negotiate on ARR commitment, not rev-share.

---

### M6: Tier-2 City Expansion Economics and India GTM

**Foundation:** NPV (F4), DCF (F1).

**Tier-2 NPV:**
```
NPV_T2 = sum_{t=1}^{T} [Penetration_t * SAM_T2 * ARPU * GM - CAC_T2_t - OpEx_T2_t] / (1+r)^t - I_0
```

**Tier-2 Market Sizing (T06 training fallback):**
```
SAM_T2 = 2.3 * SAM_T1    [India Tier-2 city SAM uplift by 2027]
CAC_T2 = 0.4 * CAC_T1    [lower competition, lower digital ad cost]
OpEx_T2 = 0.4 * OpEx_T1  [lower field sales cost]
```

**Breakeven Penetration p*:**

Solve NPV_T2(p*) = 0. With constant penetration p* per year and horizon T:

```
p* = (I_0 + sum_t (CAC_T2 + OpEx_T2)/(1+r)^t) / (SAM_T2 * ARPU * GM * sum_t 1/(1+r)^t)
```

Sensitivity: dp*/d(CAC_T2) = 1/(SAM_T2 * ARPU * GM). A Rs 1 lakh reduction in total CAC lowers required penetration by 1/(SAM_T2*ARPU*GM) percentage points.

**Worked Example:** SaaS expanding from Bengaluru Tier-1 to Pune/Coimbatore Tier-2:

- SAM_T1 = Rs 100 Cr; SAM_T2 = Rs 230 Cr.
- ARPU = Rs 2 lakh/buyer/yr; GM = 70%.
- CAC_T2 = Rs 20,000; OpEx per customer = Rs 8,000/yr.
- 11,500 addressable buyers in Tier-2; 1% penetration Year 1 = 115 customers.
- Revenue = 115 * Rs 2L = Rs 2.3 Cr.
- CAC outflow = 115 * 20K = Rs 23L; OpEx = 115 * 8K = Rs 9.2L.
- CF_1 = 2.3 Cr * 0.70 - 23L - 9.2L = 1.61 Cr - 32.2L = Rs 1.29 Cr.
- I_0 = Rs 30 lakh; r = 14%.

NPV positive at low penetration (<0.5%) — Tier-2 is capital-efficient. Breakeven penetration p* ≈ 0.5% (very low, confirming attractiveness).

---

## 8. Anti-Patterns to Avoid

- **Fitting the Bass diffusion model with ordinary least squares on the linearized form instead of non-linear least squares**: per §2.5, OLS on the linearized form introduces bias precisely because the closed-form Bass equation is non-linear in `p`, `q`, `M` — Gauss-Newton NLS with the analytical Jacobian (§2.6) is required, not a shortcut that happens to run faster.
- **Treating the literature-average Bass `p`/`q` values as fixed constants applicable to any product**: per §2.2, these are explicitly calibration *ranges* and initialization bounds, not universal parameters — every product requires its own NLS fit to its own adoption data; using the India B2B SaaS central estimate (`p=0.02, q=0.40`) as a final answer instead of a starting point skips the fitting step the model depends on for accuracy.
- **Running Bass-model NLS fitting with fewer than 3 observed time periods, or leaving `M` free to fit with fewer than 5 periods**: per §2.5, `T ≥ 3` is the stated minimum for the fit to be meaningful at all, and with `T < 5`, `M` is weakly identified — the model requires fixing `M` to an independent TAM estimate in that regime rather than letting all three parameters float on too little data.
- **Presenting gross SOM/TAM figures for a multi-year forecast without the churn-adjusted version alongside it**: per §1.6 and §6.4, churn converts a static market-sizing stock into a flow problem — a 5-year model at 15% annual churn erodes reachable market to 44% of year-0 SOM, and presenting only the gross figure to investors who expect churn-adjusted numbers (§6.4) omits the exact adjustment the skill states they will expect.
- **Accepting a top-down TAM estimate without a bottom-up cross-check, or presenting a top-down/bottom-up estimate that diverges by more than 2x without investigating the gap**: per §1.4's hybrid-validation rule, agreement within 30% is the credibility bar, and a >2x divergence is an explicit signal to investigate before presenting to investors — treating either method alone as sufficient, or presenting a divergent pair without reconciling it, skips the validation step the methodology is built around.
- **Splitting GTM budget across PLG and SLG motions by gut feel or fixed ratio instead of equalizing the cost-per-acquired-customer ratio**: per §5.5's KKT optimality condition, the interior optimum requires `CAC_PLG/conv_PLG = CAC_SLG/conv_SLG` — if one motion's ratio is lower, incremental spend should shift toward it until the ratios equalize (or PLG capacity saturates); allocating budget by an arbitrary split instead of this equalization rule leaves an increasing blended CAC on the table.
- **Citing this skill's SaaS Magic Number thresholds as authoritative industry fact in external-facing material**: per §5.4's explicit note, these thresholds are a training-data fallback — external use should cite OpenView/SaaS Capital directly rather than presenting the cached numbers as a sourced benchmark.
- **Assuming the Bass model's adoption-peak/inflection point always occurs at exactly half the market (`N = M/2`)**: per §2.4, `N = M/2` is specifically the *logistic special case* (`p → 0`, pure word-of-mouth) — the general Bass model's peak occurs at `N(t*)/M = (1 - p/q)/2`, which is below 50% whenever `p > 0` (e.g., ~47.5% for typical India SaaS `p=0.02, q=0.40`); applying the logistic-only 50% figure to a product with a meaningful innovation coefficient misreads where the actual sales-rate peak falls.

## 9. India-Specific Layer

### 8.1 India IT-BPM Market Context

**NASSCOM IT-BPM Export Target:**
- FY2025 target: $194B total IT-BPM exports (T06 confirmed).
- India-origin global SaaS: ~$20–25B (T06 training fallback; verify with NASSCOM SaaS Report 2024).
- India domestic SaaS: ~$6–8B FY2025 (T06 training fallback; verify with NASSCOM SaaS Report 2024).
- India SaaS CAGR: 30–35% (2023–2027) (T06 training fallback).

**Flagged items requiring author verification before publishing:**
- India SaaS TAM ($6–8B domestic): training fallback. Verify at nasscom.in.
- India SaaS CAGR (30–35%): training fallback. Verify with NASSCOM/SaaSBOOMi 2024.

### 8.2 India Bass Diffusion Calibration

India mobile internet penetration (2024) provides the M calibration anchor for consumer-facing products:
- Internet users: ~950 million (estimated 2024).
- Smartphone users: ~750 million.
- Urban internet penetration: ~80%; rural: ~45%.

For B2B SaaS, calibrate M against:
- DPIIT registered startups: 115,000+ (T06 training fallback, 2024).
- Mid-large Indian enterprises (>500 employees): ~50,000–80,000.

India B2B SaaS Bass parameters — use these as starting values for NLS fitting:
- p = 0.015–0.025 (lower than global due to longer enterprise sales cycles).
- q = 0.35–0.45 (higher than global average due to strong referral networks in Indian startup ecosystem).

### 8.3 TAM Sizing with PPP Adjustment

India IT budgets are lower than US in absolute terms but purchasing power parity-adjusted:
```
India_TAM_PPP = Global_TAM * India_GDP_PPP_share
India_price = Global_price * 0.29    [World Bank ICP 2024; T06 confirmed]
```

Typical India enterprise SaaS pricing: 0.25–0.35× US list price. When presenting India TAM in USD, note that revenue per buyer is materially lower than global averages — compensated by volume and CAGR.

### 8.4 Tier-2/Tier-3 City Expansion Mathematics

**Tier classification (India):**
- Tier-1: Mumbai, Delhi NCR, Bengaluru, Hyderabad, Chennai, Pune.
- Tier-2: Ahmedabad, Chandigarh, Jaipur, Lucknow, Coimbatore, Indore, Kochi (~35 cities).
- Tier-3: Smaller cities with emerging digital adoption (~300+ cities).

**Key economics (T06 training fallback; verify against latest India startup ecosystem reports):**

| Metric | Tier-1 | Tier-2 | Tier-3 |
|--------|--------|--------|--------|
| SAM multiplier (vs Tier-1) | 1.0x | 2.3x | 1.5x |
| CAC ratio | 1.0x | 0.4x | 0.3x |
| Field sales cost | 1.0x | 0.4x | 0.25x |
| Digital adoption velocity | High | Medium | Low-Medium |

### 8.5 GeM (Government e-Marketplace) Market Sizing

GeM is India's government procurement portal for all central and state PSUs:
- Procurement value: GeM crossed Rs 4 lakh crore cumulative GMV (2024; verify at gem.gov.in).
- Direct Purchase limit: Rs 25,000 (confirmed, T06 Search 1).
- Push Button Procurement (PBP): up to Rs 5 lakh.
- Above Rs 25,000: bid process required.

For SaaS/tech product companies targeting government: GeM is the primary channel. Model a separate SOM for government segment using GeM TAM, not commercial TAM.

### 8.6 NASSCOM India IT Industry Data for Market Sizing

Key NASSCOM metrics useful for bottom-up sizing:
- India IT/BPM workforce: ~5.4 million employees (NASSCOM 2024; verify).
- Digital services growth: 23–25% CAGR.
- India as % of global IT services outsourcing: ~55%.
- GCC (Global Capability Centres) in India: 1,600+ (verify at nasscom.in).

### 8.7 DPIIT Startup Density for PLG TAM Calibration

India's startup ecosystem provides a viral channel for PLG products:
- DPIIT-recognized startups: 115,000+ (T06 training fallback, 2024; verify at startupindia.gov.in).
- State density: Karnataka, Maharashtra, Delhi NCR account for ~60% of startups.
- Stage distribution: ~70% seed/early stage (addressable for low-ARPU PLG); ~30% growth/late stage (addressable for SLG/enterprise).

India PLG localization insight: Hindi/regional language UI increases conversion rates 15–25% in Tier-2 markets (T06 training fallback; cite product analytics data when available).

### 8.8 RBI Payment Aggregator Regulations for GTM Pricing

Products with embedded payments must account for RBI PA-CB (Payment Aggregator Cross-Border) license requirements:
- Domestic payment aggregators: PA license from RBI mandatory.
- Cross-border payments (import): PA-CB license required from 2024.
- This affects freemium-to-paid conversion funnel if self-serve checkout uses international payment rails.

GTM implication: factor 3–6 months for payment infrastructure compliance into India go-live timeline.

---

## 10. Response Rules

1. **Always state Bass p and q as calibration ranges, not fixed constants.** Every product requires NLS fitting to its own data. Report confirmed ranges (p: 0.01–0.03, q: 0.20–0.40 for software/SaaS) as initialization bounds and sanity checks.

2. **Always distinguish TAM, SAM, and SOM clearly.** Never present TAM as achievable revenue. Always clarify which level you are quoting and what assumptions drive it.

3. **Flag training fallback data explicitly.** India SaaS TAM, India CAGR, Tier-2 SAM multiplier, and WACC are training fallbacks. State them as estimates and direct readers to verify against NASSCOM/SaaSBOOMi/RBI sources.

4. **Use Monte Carlo for SOM estimates.** Never present a single-point SOM without a confidence range. P5/P50/P95 is the minimum presentation standard.

5. **Distinguish gross TAM from churn-adjusted reachable market** whenever the product is a subscription with measurable churn > 10% annually.

6. **Confirm p/q initialization values from T06 Search 3:** p_0 = 0.01, q_0 = 0.30, M_0 = 2 * max(N_obs). Always validate post-fit: p > 0, q > 0, M > max(N_obs).

7. **For HHI interpretation:** always quote the three-zone classification (<1,500 competitive; 1,500–2,500 moderate; ≥2,500 concentrated).

8. **For partnership NPV:** always include a tornado sensitivity chart identifying the top three value drivers. ARR growth assumption typically dominates.

9. **For India GTM:** always distinguish Tier-1, Tier-2, and government (GeM) segments separately. They have different TAM, CAC, and adoption velocity profiles.

10. **Magic Number threshold caveat:** MN > 0.75 is training fallback. For published reports, cite OpenView Partners or SaaS Capital benchmark surveys.

---

## 11. What Not to Do

- **Do not use global Bass p/q parameters without India calibration.** Global averages (p=0.035, q=0.390) apply to consumer durables. India B2B SaaS adoption dynamics differ — fit to your own data or use India-specific priors.

- **Do not present TAM as achievable revenue.** TAM is a market ceiling, not a revenue forecast. SOM at 3–5% Year-3 is an aggressive target; build up from unit economics.

- **Do not apply OLS to fit the Bass model.** The Bass closed form is non-linear in p, q, M. OLS on the linearized transformation introduces bias. Always use NLS (Gauss-Newton or Levenberg-Marquardt).

- **Do not ignore churn when computing market sizing for subscription businesses.** Gross TAM overstates the effective revenue opportunity if churn is high.

- **Do not quote India TAM in USD without noting PPP adjustment.** Revenue per enterprise buyer in India is 0.25–0.35× US; total market in USD is not directly comparable to US or European SaaS benchmarks.

- **Do not use a single-point HHI to conclude market attractiveness.** Combine HHI with Lerner Index and competitive entry cost (CAC, regulatory barriers) for a complete picture.

- **Do not conflate NRR with market growth.** NRR > 100% means existing customers expand; it does not imply new logo market is growing. Both dimensions are required for full market assessment.

- **Do not use the logistic model for products with significant mass-media or PLG marketing.** Use full Bass model with p > 0 for products with both innovator and imitator effects.

- **Do not present Bass t* as the forecast date for market maturity.** t* is the peak of the sales rate (new adopters/period); the market continues to grow after t* but decelerates. Saturation (~N = 0.9M) occurs much later.

- **Do not omit GeM in government-facing market sizing.** GoI and PSU procurement is a distinct and large market segment in India; model it separately from commercial B2B.

---

## 12. Output Expectations

A market expansion analysis using this skill should deliver:

1. **TAM/SAM/SOM Table:** Three-row table with methodology (top-down / bottom-up / hybrid), assumption, central estimate (Rs and USD), and data source flag (confirmed / training fallback).

2. **Monte Carlo SOM:** P5/P50/P95 range with assumptions documented (triangular distribution parameters for each input).

3. **Bass Diffusion Forecast (if adoption time-series data available):** Fitted p, q, M with R², RMSE; S-curve chart through horizon; t* (peak adoption quarter); P50 cumulative adoption at Year 3 and Year 5.

4. **HHI Competitive Snapshot:** HHI score with zone classification; top-3 firm shares; Lerner Index; entrant price premium bound.

5. **GTM Motion Economics:** CAC/LTV/LTV:CAC for each motion (PLG/SLG); Magic Number; optimal spend split.

6. **Partnership NPV (if applicable):** Central NPV, discounted payback, tornado chart.

7. **India Market Summary:** Separate Tier-1/Tier-2/Government SOM estimates; Bass India calibration priors; PPP-adjusted revenue per customer vs global benchmark.

---

## 13. Skill Scope

**In scope:**
- TAM/SAM/SOM sizing (top-down, bottom-up, hybrid, Monte Carlo CI).
- Bass diffusion model (ODE, closed form, NLS fitting, Jacobian).
- Logistic growth and saturation analysis.
- Herfindahl-Hirschman Index and Cournot Nash equilibrium.
- PLG/SLG/CLG unit economics, Magic Number, optimal spend split.
- Partnership NPV and channel economics.
- Tier-2 city expansion model and India GTM.
- Churn-adjusted market sizing.

**Out of scope:**
- Pricing strategy (price elasticity, Van Westendorp) → `revenue-pricing-core`.
- Individual deal win probability or pipeline stage conversion → `sales-pipeline-core`.
- India government tender evaluation (QCBS, TOPSIS) → `india-bd-core`.
- Agile delivery metrics or sprint forecasting → `agile-metrics-core`.
- Advanced stochastic demand models (Bayesian hierarchical, non-parametric Bass extensions) → delegate to `agile-business-mathematics-expert`.

---

## Version

1.0.1 — 2026-07-27 — Added §8 Anti-Patterns to Avoid (8 pitfalls spanning OLS-vs-NLS Bass fitting, fixed-parameter misuse, small-sample fitting constraints, gross-vs-churn-adjusted SOM presentation, TAM cross-validation, PLG/SLG budget-split KKT rule, Magic Number sourcing, and Bass-vs-logistic inflection-point confusion); renumbered §9-12 to §10-13.

1.0.0
