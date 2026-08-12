---
name: india-bd-core
description: "Provides India-specific business development mathematics including GeM government marketplace scoring, DPIIT Startup India benefit quantification, MSMED Act threshold analysis, government tender QCBS/L1/TOPSIS evaluation, FEMA compliance, and TDS/transfer pricing impact on deal economics. Use when bidding on government tenders, registering on GeM, computing Section 80-IAC NPV benefit, structuring cross-border deals, or analyzing MSME procurement preferences. Keywords: GeM government e-marketplace, DPIIT Startup India registration, MSMED Act thresholds, Section 80-IAC NPV, government tender QCBS L1 evaluation, FEMA cross-border compliance, TDS 194Q B2B transactions."
allowed-tools: Read,Glob,Grep
user-invocable: true
---


<!-- generated-by: claude-global-library/tools/project_sync -->
<!-- source: skills/india-bd-core/SKILL.md -- edit the library, then re-run sync_project.py -->

# india-bd-core

## Description

India-specific business development regulatory and compliance skill covering the full ecosystem of government procurement (GeM), startup tax incentives (DPIIT Section 80-IAC), MSME classification and procurement preferences, multi-criteria government tender evaluation (QCBS, L1, TOPSIS), FEMA cross-border deal compliance, and TDS/GST impact on deal cash flows. All regulatory values are drawn from confirmed research (T06) or training knowledge with explicit flags where verification is recommended.

---

## 1. GeM Procurement Framework

### 1.1 Procurement Threshold Tiers

The Government e-Marketplace (GeM) portal mandates three distinct procurement routes based on purchase value:

| Route | Threshold | Process | Competition Required |
|-------|-----------|---------|----------------------|
| Direct Purchase | Up to Rs 25,000 | Buy directly from available listings | None |
| Push Button Procurement (PBP) | Rs 25,001 to Rs 5,00,000 | Select from available sellers in category | Implicit price comparison |
| Bid/Reverse Auction | Above Rs 25,000 (bids); Rs 10 lakh+ (RA trigger — FLAG: unverified) | Open competitive bidding | Yes |

**Critical rule:** No splitting of requirements is permitted to bring a purchase under PBP threshold. The requirement must be assessed as a whole.

### 1.2 MSME Mandatory Procurement Targets

Government buyers are mandated under the Public Procurement Policy for Micro and Small Enterprises (PPP-MSE) Order 2012:

- **25% of annual procurement** from Micro and Small Enterprises (confirmed, T06 Search 1)
- **4% sub-target** of total procurement reserved for SC/ST-owned MSEs (confirmed, T06 Search 1)
- **3% sub-target** reserved for women Self-Help Group (SHG) / women-owned enterprises (confirmed, T06 Search 1)

These mandates apply to GeM procurement and direct government contracts.

### 1.3 GeM Seller Registration Prerequisites

To sell on GeM, a vendor must complete:

1. **Udyam Registration** (udyamregistration.gov.in) — mandatory for MSMEs claiming preference
2. **GeM seller account** linked to Aadhaar / PAN / GSTIN
3. **OEM panel registration** (if Original Equipment Manufacturer) or **Reseller authorization**
4. **Quality certification** where applicable (BIS, ISI for goods)
5. **DPIIT Startup recognition certificate** for startups

### 1.4 GeM Bid Scoring Model

For custom bids above Rs 25,000, the scoring model for complex IT/services procurement uses QCBS:

```
CS = w_Q * Quality_Score + w_C * Cost_Score
C  = (P_min / P_bid) * 100
```

Where:
- CS = Composite Score
- w_Q = quality weight, typically 0.70 to 0.80 for IT services (GoI standard)
- w_C = cost weight = 1 - w_Q, typically 0.20 to 0.30
- P_min = lowest bid received (L1 price)
- C = Cost Score (100 for L1 bidder, decreasing for higher-priced bids)

Minimum Quality Score to win:

```
T_self = (CS_target - w_C * C_self) / w_Q
```

If aiming to be L1 (P_bid = P_min), C_self = 100:

```
T_self_at_L1 = (CS_target - 100 * w_C) / w_Q
```

---

## 2. DPIIT Startup Recognition and Section 80-IAC Tax Holiday

### 2.1 DPIIT Recognition Criteria

A startup must satisfy ALL of the following to be recognized by the Department for Promotion of Industry and Internal Trade (DPIIT):

| Criterion | Requirement |
|-----------|-------------|
| Incorporation | Private Limited Company, LLP, or Registered Partnership Firm |
| Incorporation date | Between 1 April 2016 and 31 March 2025 (FLAG: window extended periodically — verify latest extension at startupindia.gov.in) |
| Age | Up to 10 years from date of incorporation |
| Annual turnover | Not exceeded Rs 100 crore in any FY since incorporation |
| Innovation / Scalability | Working towards development, deployment, commercialisation of a new product/service/process driven by technology or IP |
| Not formed by splitting | Not formed by splitting or reconstructing an existing business |

Application is via the DPIIT online portal; DPIIT recognition is step 1. Section 80-IAC benefit requires additional approval from the Inter-Ministerial Board (IMB) via Form 1.

### 2.2 Section 80-IAC Tax Holiday Details

Under Section 80-IAC of the Income Tax Act, a DPIIT-recognized startup receives:

- **100% deduction of profits** in each elected year
- Applicable for **3 consecutive years** chosen by the startup out of the **first 10 years** from the year of incorporation
- Entity types eligible: **Private Limited Company and LLP only** (not sole proprietorships or general partnership firms)
- Turnover cap: Annual turnover must not exceed **Rs 100 crore** in any of the elected years

**Effective tax saving:** ~25.168% of profits per year (derived from: 22% base rate + 10% surcharge on base + 4% health and education cess on tax+surcharge = 22% × 1.10 × 1.04 = 25.168%)

### 2.3 Optimal Year Election Strategy

The startup selects which 3 consecutive years (out of the first 10) to claim the deduction. The 8 possible consecutive windows are: (1,2,3), (2,3,4), ..., (8,9,10).

**Decision rule:** Elect the 3 consecutive years with the **highest discounted PBT**. Under a constant growth assumption (PBT growing at rate g, discount rate r):

- If **g < r**: elect **early** (years 1, 2, 3)
- If **g > r**: elect **late** (years 8, 9, 10)
- If **g = r**: indifferent; any window is equally optimal
- Break-even growth rate: **g_be = r** (exactly the discount rate)

High-growth startups (g >> r) gain substantially more NPV by deferring the election to peak-profit years.

---

## 3. MSMED Act Classification and Benefits

### 3.1 Revised MSMED Thresholds (Amendment 2020)

Under the Micro, Small and Medium Enterprises Development (MSMED) Act 2006 as amended in 2020, classification requires **BOTH** investment AND turnover criteria to be satisfied:

| Category | Plant & Machinery Investment | Annual Turnover |
|----------|------------------------------|-----------------|
| **Micro** | Not exceeding Rs 1 crore | Not exceeding Rs 5 crore |
| **Small** | Not exceeding Rs 10 crore | Not exceeding Rs 50 crore |
| **Medium** | Not exceeding Rs 50 crore | Not exceeding Rs 250 crore |

**Source note:** These values are from training knowledge (T06); verification at msme.gov.in is recommended before publishing compliance advice. If only one criterion is met, the entity does not qualify for that category.

**Registration portal:** Udyam Registration Portal (udyamregistration.gov.in) — self-declaration basis; linked to PAN and GSTIN.

### 3.2 Key MSME Benefits

| Benefit | Detail |
|---------|--------|
| Payment cycle protection | Buyers must pay within 45 days; default incurs interest at bank rate + 3× |
| MSME Samadhan | Delayed-payment dispute portal; interest at ~18.75% (3× bank rate) |
| Priority sector lending | Lower interest rate on loans |
| Government procurement preference | 25% mandatory procurement mandate from Micro + Small |
| Credit Guarantee Scheme | Collateral-free loans up to Rs 2 crore |

### 3.3 Strategic Threshold Proximity Analysis

As an MSE approaches the Small-to-Medium threshold (Rs 50 Cr turnover), management must weigh the cost of losing MSE procurement preference against growth above the ceiling. The annual MSE preference benefit to model:

```
Annual_preference_benefit = MSE_pool * current_win_share * (1 - 1/m)
```

where m is the win-rate multiplier from MSE preference (empirical range 1.3 to 1.8, training fallback). If annual preference benefit exceeds the profit from incremental revenue above Rs 50 Cr, capping growth (or corporate restructuring via split) may be rational.

---

## 4. TDS Section 194Q Compliance

### 4.1 Scope and Rate

Section 194Q, effective **1 July 2021**, requires:

| Parameter | Value |
|-----------|-------|
| Who deducts | **Buyer** (deducts TDS at source) |
| Applicable when | Aggregate purchases from a single seller exceed Rs 50 lakh in a financial year |
| TDS rate | **0.1%** on the purchase value **exceeding** the Rs 50 lakh threshold |
| No PAN rate | **5%** on the excess if seller has not furnished PAN |
| Coverage | Goods purchases (B2B) |

**Source note:** Confirmed from training knowledge (T06 Area 8); verify at income-tax.gov.in.

### 4.2 TDS Calculation

```
TDS_amount = 0.001 * max(0, Purchase_value - 5,000,000)
```

(Rs 50 lakh = Rs 50,00,000 = 5,000,000 in rupee notation)

Example: Buyer purchases Rs 80 lakh of goods from Seller A in a FY.
- Threshold: Rs 50 lakh
- Excess: Rs 30 lakh
- TDS: 0.1% × Rs 30 lakh = Rs 3,000

### 4.3 Interaction with TCS Section 206C(1H)

Section 206C(1H) requires the **seller** to collect TCS at 0.1% when receipts from a single buyer exceed Rs 50 lakh. Where **both** provisions apply to the same transaction:

> **Section 194Q prevails.** The buyer deducts TDS; the seller does not additionally collect TCS on the same transaction. They are **mutually exclusive** in application — not additive.

This was clarified by CBDT in its guidance dated 28 June 2021.

### 4.4 SaaS Classification Flag

**CRITICAL FLAG:** Section 194Q applies to "goods." SaaS contracts may be classified as a **service** rather than goods under CBDT interpretation, in which case Section 194J (10% TDS on professional/technical services) could apply instead. This would result in 100× more TDS deduction (10% vs 0.1%). Verify the applicable section with a CA and reference CBDT Circular 2021 before structuring large SaaS contracts.

### 4.5 Cash Flow Impact Model

TDS is locked up as a credit until the seller files an income tax return and receives refund or adjusts against tax liability. The working capital cost:

```
Cost_lockup = TDS_amount * (1 - 1/(1 + r/12)^{t_refund})
```

First-order approximation for small r × t:

```
Cost_lockup ≈ TDS_amount * (r/12) * t_refund
```

where r = annual cost of capital, t_refund = refund cycle in months (typically 6 to 12 months).

**Compliance requirement:** Collect buyer's PAN at contract stage to avoid the 5% no-PAN rate.

---

## 5. FEMA External Commercial Borrowing (ECB) and Export Compliance

### 5.1 ECB Automatic Route Limits

Under FEMA Master Direction on External Commercial Borrowings (RBI):

| Borrower Category | ECB Limit per FY |
|-------------------|-----------------|
| General (any eligible borrower) | USD 750 million (or equivalent) |
| DPIIT-recognized startups | USD 3 million |

**Source note:** Training knowledge (T06 Area 8); verify against latest RBI Master Direction on ECB at rbi.org.in before advising clients.

Key ECB conditions:
- Minimum average maturity: 3 years (general); 1 year for startups
- All-in-cost ceiling: SOFR + 450 bps (indicative for 3–5 year tenor)
- Hedging requirements: advisable; forward hedge cost ~3–4% INR-USD per annum

Effective INR cost model:

```
Effective_INR_cost = (1 + coupon_rate) * (1 + hedge_cost) - 1
```

Example: SOFR 4.5% + 450 bps = 9.0% coupon; hedge cost 3.5%. Effective INR cost = (1.09)(1.035) − 1 = 12.83%/yr.

### 5.2 Export Realization and SOFTEX

Under FEMA, export proceeds must be realized within **12 months** from the date of shipment or service delivery. Failure triggers RBI penalties.

Software/IT services exports exceeding **USD 25,000** per invoice must be filed through the **SOFTEX portal** (STPI or SEZ authority):

```
if export_value > USD 25,000:
    filing = "SOFTEX form required"
else:
    filing = "No SOFTEX filing; normal banking channel"
```

STPI unit registration allows: 100% FDI under automatic route; customs duty exemption on imports; exemption from Service Tax on procurements.

### 5.3 Transfer Pricing — TNMM Method

For related-party international transactions, the Transactional Net Margin Method (TNMM) is the most commonly used method in India:

```
NMI = Operating_Profit / Revenue
```

(Alternatively: Operating Profit / Total Cost for service entities.)

The arm's-length range is the interquartile range of comparables:

```
Arm's-length range = [P25_comparables, P75_comparables]
```

If NMI_tested ∈ [P25, P75]: arm's-length; no adjustment.
If NMI_tested < P25: Transfer Pricing Officer can adjust income to the median (P50).

```
Adjustment = (P50 - NMI_tested) * Revenue_tested
```

Penalty under Section 271(1)(c): up to 300% of tax shortfall from under-reported income. For large related-party transactions, an Advance Pricing Agreement (APA) with CBDT provides certainty.

---

## 6. Government Tender Evaluation Methods

### 6.1 QCBS — Quality-Cum-Cost-Based Selection

Used for consultancy, complex IT, and technical services:

```
CS   = w_Q * Q + w_C * C
C    = (P_min / P_bid) * 100
```

GoI standard weights: w_Q = 0.70–0.80; w_C = 0.20–0.30.

### 6.2 L1 Selection (Lowest Price Wins)

Used for commodity goods and standard catalog items on GeM. Only the bidder offering the lowest evaluated price wins. Price negotiation is permitted only with the L1 vendor.

### 6.3 TOPSIS Multi-Criteria Evaluation

Used for complex tenders with more than 2 evaluation dimensions.

**6-Step TOPSIS Algorithm:**

1. Build decision matrix X (m bids × n criteria)
2. Vector normalize: r_ij = x_ij / sqrt(sum_k x_kj^2)
3. Apply weights: v_ij = w_j × r_ij (sum of w_j = 1)
4. Compute ideal (A+) and anti-ideal (A−):
   - Benefit criterion: v_j+ = max_i(v_ij); v_j− = min_i(v_ij)
   - Cost criterion: v_j+ = min_i(v_ij); v_j− = max_i(v_ij)
5. Euclidean distances: d_i+ = sqrt(sum_j(v_ij − v_j+)^2); d_i− = sqrt(sum_j(v_ij − v_j−)^2)
6. Relative closeness: C_i = d_i− / (d_i+ + d_i−); rank by C_i descending (higher = better)

---

## 7. Deep Mathematical Foundations

### M1: GeM Bid Scoring and Price Competitiveness Mathematics

**Foundation:** Order statistics and QCBS scoring.

**QCBS Composite Score:**

```
CS = w_Q * Q + w_C * C      (w_Q + w_C = 1)
C  = (P_min / P_bid) * 100
```

**Minimum Quality Score to win given competitor intelligence:**

Target CS_target = max(competitor composite scores) + ε.

Solve for own minimum quality score T_self at bid price P_bid:

```
T_self = (CS_target - w_C * C_self) / w_Q
```

where C_self = (P_min / P_bid) × 100 depends on own price relative to the current minimum.

If own bid = L1 (P_bid = P_min → C_self = 100):

```
T_self_at_L1 = (CS_target - 100 * w_C) / w_Q
```

**L1 as First-Order Statistic:**

If n bidders draw prices independently from CDF F(p), the minimum price P_min is the first-order statistic X_(1).

Distribution of L1:

```
F_{L1}(p) = P(X_(1) <= p) = 1 - (1 - F(p))^n
```

Expected L1 for uniform bids U(a, b):

```
E[X_(1)] = a + (b - a) / (n + 1)
```

Derivation: The first-order statistic from U(a,b) has PDF f_(1)(x) = n(b−x)^{n−1}/(b−a)^n. Computing E[X_(1)] = integral_a^b x × f_(1)(x) dx via substitution u = (x−a)/(b−a) yields E[X_(1)] = a + (b−a)/(n+1).

For realistic log-normal bid distributions, use Monte Carlo simulation.

**MSE Preference Win-Rate Multiplier (training fallback):**

```
P_win_MSE = m * P_win_normal      m in [1.3, 1.8]
```

**Worked Example:**

GeM IT services contract. 5 bidders: prices Rs 8L, 9.5L, 10L, 11L, 12L. P_min = Rs 8L. Quality scores: 85, 88, 92, 80, 75. w_Q = 0.70, w_C = 0.30.

Cost scores C: 100, 84.2, 80.0, 72.7, 66.7.

Composite scores CS: [0.70×85+0.30×100, 0.70×88+0.30×84.2, 0.70×92+0.30×80, 0.70×80+0.30×72.7, 0.70×75+0.30×66.7] = [89.5, 86.86, 88.4, 77.81, 72.5].

Winner: Bidder 1 (CS = 89.5). For Bidder 3 to win: needs Q = 93.6 or P_bid = Rs 9L (C rises to 88.9 → CS = 91.07).

**India Regulatory Values:** GeM Direct Rs 25,000 (T06 confirmed); PBP Rs 5,00,000 (T06 confirmed); RA threshold Rs 10 lakh (FLAG — unverified, verify at gem.gov.in); w_Q = 0.70–0.80 (T06 confirmed); MSME mandate 25%; SC/ST 4%; women 3% (T06 confirmed).

---

### M2: Section 80-IAC Tax Holiday NPV Quantification

**Foundation:** NPV (F4 discounted cash flow) and geometric series (F1).

**Effective Tax Rate Composition:**

```
Effective_rate = 22% * (1 + 10%) * (1 + 4%)
               = 22% * 1.10 * 1.04
               = 25.168%
```

(22% base corporate tax; 10% surcharge for income > Rs 1 Cr; 4% health and education cess.)

**Tax Savings in Elected Year t:**

```
Tax_savings_t = PBT_t * 0.25168
```

**NPV of Tax Savings over elected year set S:**

```
NPV_80IAC(S) = sum_{t in S} [ PBT_t * 0.25168 / (1 + r)^t ]
```

where S is a set of 3 **consecutive** years chosen from {1, 2, ..., 10}.

**Consecutive Constraint — 8 Feasible Windows:**

S can be (1,2,3), (2,3,4), ..., (8,9,10). Exactly 8 options.

**Optimal Election — Combinatorial Argmax:**

```
S* = argmax over 8 consecutive 3-year windows of NPV_80IAC(S)
```

**Closed-Form Under Constant Growth PBT_t = PBT_0 * (1+g)^t:**

Let phi = (1+g)/(1+r). Contribution of year t = PBT_0 × 0.25168 × phi^t.

- If g < r (phi < 1): terms decline with t → **S* = {1, 2, 3}** (elect earliest)
- If g > r (phi > 1): terms rise with t → **S* = {8, 9, 10}** (elect latest)
- If g = r (phi = 1): all years equal; any window optimal

**Break-Even Growth Rate Derivation:**

The indifference condition between S = {1,2,3} and S = {8,9,10}:

```
phi + phi^2 + phi^3 = phi^8 + phi^9 + phi^10

phi(1 + phi + phi^2) = phi^8(1 + phi + phi^2)

Dividing both sides by (1 + phi + phi^2) > 0:

phi = phi^8   ⟹   phi^7 = 1   ⟹   phi = 1   ⟹   g = r
```

Therefore: **g_be = r** (exactly the discount rate). The model is bistable around this point.

**Sensitivity:**

```
dNPV/dg = 0.25168 * sum_{t in S} PBT_0 * t * (1+g)^{t-1} / (1+r)^t
```

**Worked Example:**

DPIIT startup. Year-1 PBT (Year 3 of operations) = Rs 5 Cr. Projected PBT sequence over 10 years (Rs Cr): [5, 8, 12, 18, 25, 35, 48, 65, 85, 100]. Growth rate g ≈ 35%/yr. Discount rate r = 14%.

Since g = 35% > r = 14%: S* = {8, 9, 10}.

Tax savings NPV at S* = {8, 9, 10}:
- Year 8: 65 × 0.25168 / 1.14^8 = 16.36 / 2.853 = Rs 5.74 Cr
- Year 9: 85 × 0.25168 / 1.14^9 = 21.39 / 3.252 = Rs 6.58 Cr
- Year 10: 100 × 0.25168 / 1.14^10 = 25.17 / 3.707 = Rs 6.79 Cr

**Total NPV (late election) = Rs 19.11 Cr.**

Compare to early election S* = {1, 2, 3}: NPV = Rs 4.69 Cr.

By electing late, the startup captures **Rs 14.4 Cr more** in present-value tax savings.

**Boundary Conditions:** Election is irrevocable once filed. Turnover in any elected year must not exceed Rs 100 Cr (if it does, that year becomes ineligible). Years with losses (PBT ≤ 0) provide zero benefit — factor in loss-making early years. Incorporation window FLAG (verify extension at startupindia.gov.in).

**India Regulatory Values:** 100% deduction for 3 consecutive years out of first 10 (T06 confirmed, training); effective tax rate 25.168% (T06 confirmed); Rs 100 Cr turnover cap (T06 confirmed, training); incorporation window 1 Apr 2016–31 Mar 2025 (FLAG — verify extension).

---

### M3: MSMED Act Thresholds and Procurement Preference Model

**Foundation:** Bernoulli revenue impact model.

**MSMED 2020 Dual-Criterion Classification:**

BOTH investment AND turnover must satisfy thresholds:

```python
def msmed_classification(investment_cr, turnover_cr):
    if investment_cr <= 1 and turnover_cr <= 5:
        return "Micro"
    elif investment_cr <= 10 and turnover_cr <= 50:
        return "Small"
    elif investment_cr <= 50 and turnover_cr <= 250:
        return "Medium"
    else:
        return "Not MSME"
```

(investment and turnover in Rs crore; "T06 training fallback — verify at msme.gov.in")

**Procurement Preference Win-Rate Multiplier:**

```
P_win_MSE = m * P_win_normal      m in [1.3, 1.8]   (training fallback)
```

MSE-preferred procurement targets: 25% total; 4% SC/ST sub-target; 3% women sub-target.

**Annual MSE Preference Benefit:**

```
Preference_benefit = MSE_pool * win_share * (1 - 1/m)
```

where MSE_pool = total addressable MSE-mandated procurement, win_share = current market share, m = win-rate multiplier.

**Threshold-Crossing Revenue Impact:**

At turnover approaching Rs 50 Cr (Small ceiling), each rupee earned has probability ρ of triggering reclassification. Expected annual benefit loss:

```
E[Revenue_lost] = rho * MSE_pool * win_share * (m - 1)/m
```

**Optimal Growth Decision:**

Grow beyond Rs 50 Cr turnover if and only if:

```
Expected non-MSE revenue gain > Preference_benefit
```

**Worked Example:**

Small MSE: Rs 8 Cr investment, Rs 45 Cr turnover. Wins 4% of Rs 200 Cr MSE-mandated pool = Rs 8 Cr/yr. m = 1.5.

Without preference: would win Rs 8/1.5 = Rs 5.33 Cr/yr. Annual preference value = Rs 2.67 Cr.

If turnover crosses Rs 50 Cr → Small-to-Medium reclassification. (Medium entities may not benefit from the Micro/Small-specific 25% mandate — verify current GoI procurement rules.) Cost of crossing = Rs 2.67 Cr/yr.

Justified growth beyond Rs 50 Cr only if incremental profit from additional revenue > Rs 2.67 Cr/yr.

**India Regulatory Values:** Micro (≤Rs 1Cr, ≤Rs 5Cr), Small (≤Rs 10Cr, ≤Rs 50Cr), Medium (≤Rs 50Cr, ≤Rs 250Cr) (T06 training fallback); 25% MSE mandate; 4% SC/ST; 3% women (T06 confirmed); MSME Samadhan interest ≈18.75% (3× bank rate, T06 training fallback).

---

### M4: Government Tender QCBS, L1, and TOPSIS Evaluation

**Foundation:** Multi-criteria decision analysis (MCDA) — F6.2 in shared foundations.

**QCBS and L1:** As derived in M1.

**TOPSIS — Full 6-Step Derivation:**

Decision matrix X with m alternatives (bids) and n criteria.

**Step 1 — Vector Normalization:**

```
r_{ij} = x_{ij} / sqrt( sum_{k=1}^{m} x_{kj}^2 )
```

Normalization invariance proof: All entries in column j are divided by the same positive constant sqrt(sum_k x_kj^2). Division by a positive constant is a monotone transformation; hence relative ordering within each criterion is preserved.

**Step 2 — Apply Criteria Weights:**

```
v_{ij} = w_j * r_{ij}       (sum_{j} w_j = 1)
```

**Step 3 — Compute Ideal (A+) and Anti-Ideal (A−):**

```
Benefit criterion: v_j+ = max_i(v_{ij});  v_j- = min_i(v_{ij})
Cost criterion:    v_j+ = min_i(v_{ij});  v_j- = max_i(v_{ij})
```

**Step 4 — Euclidean Distances:**

```
d_i+ = sqrt( sum_j (v_{ij} - v_j+)^2 )
d_i- = sqrt( sum_j (v_{ij} - v_j-)^2 )
```

**Step 5 — Relative Closeness:**

```
C_i = d_i- / (d_i+ + d_i-)       C_i in [0, 1]
```

C_i = 1 means bid i is identical to the ideal solution. C_i = 0 means bid i equals the anti-ideal.

**Step 6 — Rank:** Sort bids by C_i descending; highest C_i wins.

**Sensitivity to Weight Perturbation:**

```
dC_i / dw_j = [ d_i+ * (d(d_i-)/dw_j) - d_i- * (d(d_i+)/dw_j) ] / (d_i+ + d_i-)^2
```

If |ΔC_i| is large for small Δw_j (> 10% relative), ranking is unstable and weight assumptions should be challenged.

**Worked Example:**

IT services tender. 4 bidders. Criteria: Cost (cost type, lower better), Experience (benefit), Quality (benefit). Weights: w = (0.3, 0.3, 0.4).

```
Decision matrix:
         Cost   Exp   Quality
Bid 1:   10L,   85,   90
Bid 2:   12L,   92,   88
Bid 3:    9L,   75,   85
Bid 4:   11L,   88,   92
```

Column vector norms: Cost → 21.12; Experience → 170.46; Quality → 177.57.

After normalization and weighting, ideal A+ = (min cost, max exp, max quality) and anti-ideal A−.

Relative closeness (computed): C_1 ≈ 0.65, C_4 ≈ 0.62, C_3 ≈ 0.40, C_2 ≈ 0.30.

Ranking: Bid 1 > Bid 4 > Bid 3 > Bid 2. Despite Bid 2 having highest experience (92), its high cost (Rs 12L) makes it the weakest overall.

**India Regulatory Values:** GoI QCBS w_Q = 0.70–0.80 (T06 confirmed); TOPSIS used in GeM and Defence tenders for complex IT/services procurement.

---

### M5: FEMA Cross-Border Deal Compliance Mathematics

**Foundation:** Distribution quantiles for transfer-pricing comparables.

**Export Realization Deadline:**

```
Compliance check: realized_date - invoice_date <= 365 days
```

If export proceeds not realized within 12 months, RBI penalty applies under FEMA.

**SOFTEX Trigger:**

```
if export_value_USD > 25000:
    filing = "SOFTEX form via STPI/SEZ portal"
else:
    filing = "Normal banking channel; no SOFTEX required"
```

**TNMM Transfer Pricing:**

Tested entity Net Margin Indicator:

```
NMI = Operating_Profit / Revenue
```

Comparables analysis: compute NMI_i for n independent comparable companies. Sort ascending.

Arm's-length range:

```
P25 = NMI at 25th percentile of comparables
P50 = NMI at 50th percentile (median)
P75 = NMI at 75th percentile
```

Decision:

```
if P25 <= NMI_tested <= P75:
    "Arm's length — no adjustment"
elif NMI_tested < P25:
    Adjustment = (P50 - NMI_tested) * Revenue_tested
    Additional_tax = Adjustment * 0.25168
    Potential_penalty = Additional_tax * 3   # Section 271(1)(c) max
elif NMI_tested > P75:
    "No adjustment by TP authority (favourable)"
```

**FEMA ECB All-In Cost Model:**

```
Effective_INR_cost = (1 + coupon_rate) * (1 + hedge_cost) - 1
```

Example: Coupon = SOFR(4.5%) + 450bps = 9.0%; hedge = 3.5%:

```
Effective_INR_cost = 1.09 * 1.035 - 1 = 12.83% per annum
```

Compare to domestic MCLR (~8.5–10.5% for AAA borrowers) to decide ECB vs domestic borrowing.

**Worked Example:**

India subsidiary of US parent. India entity NMI = 5%. Comparables (10 firms): P25 = 8%, P50 = 12%, P75 = 16%.

NMI_tested (5%) < P25 (8%) → adjustment required.

Adjustment = (12% − 5%) × Rs 100 Cr = Rs 7 Cr.

Additional tax = Rs 7 Cr × 25.168% = Rs 1.76 Cr.

Maximum penalty = Rs 1.76 Cr × 3 = Rs 5.28 Cr.

Preventive action: Increase India transfer price so that NMI ≥ 8% (P25 lower bound). Optimal to land near P50 (12%) to minimize scrutiny.

**India Regulatory Values:** Export realization 12 months (FEMA, confirmed); SOFTEX > USD 25,000 (T06 confirmed); ECB startup limit USD 3M/FY (T06 training fallback — verify RBI Master Direction on ECB); Section 271(1)(c) penalty up to 300% (T06 training fallback).

---

### M6: TDS and Indirect Tax Impact on Deal Cash Flows

**Foundation:** NPV of cash flow timing differences (F4).

**TDS Section 194Q Cash Flow Formula:**

```
TDS_amount = 0.001 * max(0, Purchase_value - 5,000,000)
```

(Threshold = Rs 50 lakh = 5,000,000; rate = 0.1% = 0.001)

If no PAN: rate = 5% = 0.05.

**Working Capital Lock-Up Cost:**

Seller's TDS is a receivable (tax credit) that is locked up until return filing. Present-value cost:

```
Cost_lockup = TDS_amount * (1 - 1/(1 + r/12)^{t_refund})
```

First-order Taylor expansion for small r × t:

```
Cost_lockup ≈ TDS_amount * (r/12) * t_refund
```

This makes the cost linear in the refund delay and proportional to the cost of capital.

**GST on B2B SaaS (SAC 998314):**

```
GST_output = Invoice_value * 0.18          (cross-state, 18% IGST)
GST_output = Invoice_value * 0.09          (intra-state CGST portion)
               + Invoice_value * 0.09      (intra-state SGST portion)

GST_input  = Eligible_purchases * GST_rate_on_inputs
Net_GST_payable = max(0, GST_output - GST_input)
```

B2B buyer claims Input Tax Credit (ITC); GST is revenue-neutral for the supply chain. Net GST payable by 20th of next month.

**Software Exports — Zero-Rated:**

```
Export_GST_charged = 0             (zero-rated under IGST Act)
Input_GST_refund   = via RFD-01 portal (GSTN)
Refund_cycle = 60-90 days (typical)
```

Lock-up cost of input GST for exporters:

```
Cost_input_lockup = GST_input * (r/12) * t_refund_gst
```

**Comprehensive Deal Cash Flow Model:**

For a B2B SaaS vendor selling Rs P Cr to an Indian enterprise in FY:

```
Gross_revenue           = P
Less: TDS_194Q          = 0.001 * max(0, P - 0.5)    [Rs Cr; threshold 0.5 Cr = Rs 50L]
Less: GST_collected     = P * 0.18                    (if applicable; collected from buyer)
Plus: ITC_utilized      = Eligible_input_GST
Net_GST_payable         = GST_collected - ITC
Net_cash_collected      = P - TDS_194Q + GST_collected - Net_GST_payable
TDS_lockup_cost         = TDS_194Q * (r/12) * t_refund_tds
```

**Worked Example:**

B2B SaaS vendor: Rs 5 Cr purchase by large enterprise buyer in FY.

TDS 194Q: 0.1% × (Rs 5 Cr − Rs 0.50 Cr) = 0.1% × Rs 4.5 Cr = Rs 45,000.

Lock-up cost (r = 14%/yr, 6-month refund cycle):

```
Cost_lockup = 45,000 * (1 - 1/1.0117^6)
            = 45,000 * (1 - 0.933)
            = 45,000 * 0.067
            = Rs 3,015
```

GST on Rs 5 Cr cross-state invoice: 18% × Rs 5 Cr = Rs 90 lakh charged to buyer.

Vendor input GST on cloud/infra purchases Rs 50 lakh × 18% = Rs 9 lakh ITC.

Net GST payable: Rs 90L − Rs 9L = Rs 81 lakh (cash outflow by 20th of next month; recovered when buyer remits GST-inclusive invoice).

Export scenario: Same Rs 5 Cr to US customer. Invoice zero-rated. Input GST Rs 9 lakh locked up for 60–90 days. Lock-up cost = Rs 9L × (14%/12) × 2.5 months = Rs 26,250.

**Practitioner Interpretation:** Collect buyer PAN at contract signing to avoid 5% TDS rate. For export-heavy vendors, zero-rated treatment on outputs combined with RFD-01 refund makes GST cash-flow manageable. The real cost is the refund delay — model it explicitly in working capital forecasts.

**India Regulatory Values:** TDS 194Q 0.1% on purchases > Rs 50L (T06 confirmed); no-PAN rate 5% (T06 confirmed); effective 1 July 2021 (T06 confirmed); 194Q prevails over 206C(1H) (T06 confirmed); GST SAC 998314 18% IGST cross-state; 9%+9% intra-state (T06 confirmed); exports zero-rated; RFD-01 refund (T06 confirmed).

---

## 8. Anti-Patterns to Avoid

- **Splitting a large procurement requirement into multiple smaller purchases to stay under the GeM PBP threshold**: per §1.1's critical rule, no splitting of requirements is permitted to bring a purchase under the PBP threshold — the requirement must be assessed as a whole, and structuring around the threshold this way is a compliance violation, not a savvy procurement optimization.
- **Assuming a SaaS contract automatically qualifies for Section 194Q's 0.1% TDS rate because the buyer treats it as a goods purchase**: per §4.4's critical flag, CBDT may classify SaaS as a *service*, pulling the transaction under Section 194J's 10% TDS instead — a 100x higher deduction than 194Q — advising or structuring a large SaaS contract on the 194Q assumption without CA verification risks a severe TDS-rate misclassification.
- **Applying both TDS under Section 194Q and TCS under Section 206C(1H) to the same transaction**: per §4.3, CBDT's 28 June 2021 clarification makes these mutually exclusive when both would otherwise apply — 194Q prevails and the seller does not additionally collect TCS; treating them as additive double-charges the transaction and creates a reconciliation problem neither party actually owes.
- **Not collecting the buyer's PAN at contract stage before invoicing under Section 194Q**: per §4.2/§4.5, the no-PAN TDS rate is 5% versus the standard 0.1% — a 50x difference — omitting PAN collection at the contracting stage, not merely at payment time, is what triggers the punitive rate on the full transaction value.
- **Electing the Section 80-IAC 3-year tax holiday window as "always the first 3 years" or "always the last 3 years" without comparing the startup's growth rate to its discount rate**: per §2.3, the optimal election depends entirely on whether `g < r` (elect early) or `g > r` (elect late) — a high-growth startup that defaults to electing years 1-3 out of habit leaves NPV on the table it would have captured by deferring to its peak-profit years.
- **Classifying an enterprise's MSME tier by checking only investment OR only turnover against the threshold table**: per §3.1, MSMED classification requires **both** the investment and turnover criteria to be satisfied for a given category — an enterprise that qualifies as Micro on investment but exceeds the Micro turnover ceiling does not qualify as Micro, and treating either criterion alone as sufficient misclassifies the entity.
- **Growing revenue past the MSE-to-Medium turnover threshold without modeling the lost procurement-preference benefit**: per §3.3, the annual MSE preference benefit can exceed the profit from incremental revenue above the Rs 50 Cr ceiling for businesses with a meaningful GeM/government-procurement pipeline — treating the threshold crossing as a pure growth milestone, without running the `Annual_preference_benefit` comparison, can produce a net-negative outcome the model would have flagged in advance.
- **Treating a transfer-pricing NMI below the P25 comparable benchmark as an automatic, fixed tax liability rather than a starting point for negotiation or an APA**: per §5.3, a below-P25 result lets the Transfer Pricing Officer adjust income to the median (P50), but this is a discretionary adjustment path, not an automatically-finalized penalty — for large related-party transactions, pursuing an Advance Pricing Agreement with CBDT provides certainty the reactive TPO-adjustment path does not.

## 9. India-Specific Layer

### 9.1 NASSCOM and IT/BPM Sector Context

- **NASSCOM IT-BPM export target:** USD 194B by FY2025 (confirmed, T06)
- **India domestic SaaS TAM:** ~USD 6–8B FY2025 (training fallback; verify with NASSCOM SaaS Report 2024)
- **India-origin global SaaS:** ~USD 20–25B (training fallback)
- **NASSCOM DSCI guidelines** govern data protection in IT export contracts; DPDP Act 2023 compliance now mandatory for B2B SaaS
- **NASSCOM registered startups:** DPIIT database shows 115,000+ recognized startups as of 2024 (training fallback)

For IT/BPM sector BD:
- NASSCOM membership provides access to government relationship facilitation, procurement advocacy, and talent pool benchmarks
- NASSCOM AgileX certification signals delivery maturity to enterprise buyers

### 9.2 RBI Payment Aggregator Licensing Impact on SaaS Billing

Under RBI's Payment Aggregator and Payment Gateway Guidelines (March 2020 circular):

- SaaS platforms collecting payments on behalf of merchants require **PA-CB (Cross-Border) license** for international transactions
- Domestic SaaS platforms with subscription billing via payment gateway must ensure the payment aggregator holds **PA license** (RBI, 2023 mandatory deadline)
- Non-compliant billing flows risk transaction blocking; validate payment aggregator's RBI authorization before integrating

Impact on deal structuring: Enterprise customers may require invoice-based payment (Net-30/45) rather than card-based auto-debit; factor this into working capital requirements.

### 9.3 GST Registration and Input Tax Credit for B2B

| Threshold | GST Registration Requirement |
|-----------|------------------------------|
| Annual turnover > Rs 40 lakh (goods) | Mandatory |
| Annual turnover > Rs 20 lakh (services) | Mandatory |
| Annual turnover > Rs 10 lakh (special category states — NE states, Himachal Pradesh) | Mandatory |
| Exports (any value) | Mandatory (to claim zero-rating) |

For B2B SaaS, GST registration is almost always mandatory. B2B buyers need the vendor's GSTIN to claim ITC; an unregistered vendor cannot provide a tax invoice, which makes the purchase unattractive for the buyer (no ITC recovery).

**Key ITC rules:**
- ITC is eligible on purchases used for taxable business supply
- ITC blocked on: motor vehicles (personal use), employee benefits, goods/services for personal consumption
- ITC reconciliation via GSTR-2B (auto-populated from supplier GSTR-1)

### 9.4 State Government Incentive Schemes

| Scheme/Policy | State | Key Benefit |
|---------------|-------|------------|
| Special Economic Zone (SEZ) | Pan-India | Section 10AA: 100% deduction first 5 years; 50% next 5; tax holiday for export-oriented units |
| STPI (Software Technology Parks of India) | Pan-India (66 STPs) | 100% FDI automatic route; duty exemption; SOFTEX facilitation |
| Karnataka IT Policy 2020–25 | Karnataka | Investment subsidy, stamp duty waiver, employment generation subsidy |
| Telangana ICT Policy 2022 | Telangana | 25% capex subsidy up to Rs 1 Cr; power tariff concession |
| Tamil Nadu Electronics Policy 2020 | Tamil Nadu | SGST refund for 5 years; ESI/EPF reimbursement |
| Startup India Seed Fund | Pan-India | Rs 20–50 lakh grant for proof-of-concept; up to Rs 5 Cr via incubators |

**Section 10AA (SEZ) vs Section 80-IAC (Startup) — Key Difference:** Section 10AA applies to units within an SEZ; Section 80-IAC applies to the startup entity as a whole. Both cannot be claimed simultaneously for the same profits. Choose the more beneficial scheme.

### 9.5 Transfer Pricing and Advance Pricing Agreements

For startups with US/EU parent or subsidiary relationships:

- **Advance Pricing Agreement (APA):** File with CBDT under Section 92CC for certainty on transfer price method for 5 years; avoid TNMM disputes
- **Bilateral APA:** Covers both Indian and foreign tax authority; eliminates double-taxation risk
- **Safe Harbour Rules (Section 92CB):** Software development services: if operating margin ≥ 18%, safe harbour applies (no TP scrutiny); reduces compliance cost

---

## 10. Response Rules

1. **Always specify Udyam Registration as a prerequisite** when advising on MSME benefits. Without a valid Udyam certificate, the entity cannot claim procurement preferences, MSME payment protection, or credit-linked benefits — even if it meets the investment/turnover criteria.

2. **Always clarify the buyer vs seller obligation for TDS 194Q.** The buyer deducts TDS; the seller does not voluntarily deposit. Sellers should collect buyer's PAN upfront and confirm whether the buyer's aggregate purchases cross Rs 50 lakh in the FY before invoicing.

3. **Always flag 80-IAC as applicable to Pvt Ltd/LLP only — not proprietorships.** Sole proprietors and general partnerships cannot claim Section 80-IAC regardless of DPIIT recognition status. Direct such clients to alternative incentives (Section 10AA for SEZ units, startup seed fund grants).

4. **State research confidence level explicitly.** For GeM thresholds (Rs 25,000, Rs 5 lakh) cite as confirmed; for MSMED Act thresholds cite as training knowledge with recommendation to verify at msme.gov.in; for ECB startup limit cite as training knowledge with recommendation to verify against latest RBI Master Direction.

5. **For TDS classification questions about SaaS,** always flag the 194Q (0.1% goods) vs 194J (10% services) ambiguity. Do not advise 0.1% without caveat; the difference in cash flow impact is 100×.

6. **Optimal 80-IAC year election requires knowing the discount rate.** Never advise deferring or electing early without computing g vs r explicitly. If the startup's growth rate is not known, provide sensitivity analysis across g ∈ {10%, 20%, 30%} against r = 12–15%.

7. **For TOPSIS or QCBS evaluation,** provide the full scoring computation including competitor scores. Do not report only "you should score X"; show the bidder's position in the competitive landscape.

8. **Transfer pricing advice requires a CA/TP specialist.** This skill provides the TNMM framework; for an actual comparables study, advise the client to engage a transfer-pricing professional. The P25–P75 range from actual CRISIL/Bloomberg databases cannot be computed from this skill alone.

---

## 11. What Not to Do

1. **Do not advise GeM registration without verifying MSME/startup certificate prerequisites.** A vendor without DPIIT recognition cannot access startup-specific GeM features. A vendor without Udyam registration cannot claim MSME set-aside benefits. Recommend completing prerequisites first.

2. **Do not treat TDS 194Q and TCS 206C(1H) as additive.** In transactions where both could apply (buyer's aggregate purchases > Rs 50L AND seller's aggregate receipts > Rs 50L), only 194Q applies. Advising double-deduction creates compliance errors and customer disputes.

3. **Do not advise electing 80-IAC immediately without running the NPV analysis.** For high-growth startups (g >> r), early election is a costly mistake — potentially worth Rs 10+ Cr in foregone NPV. Always compute the g vs r comparison first.

4. **Do not assume MSMED thresholds have not changed.** The MSMED Act was significantly revised in 2020. Future revisions are possible. Always cite "verify at msme.gov.in" when the decision is financially material.

5. **Do not use TOPSIS for procurement decisions with only 2 criteria** — QCBS or L1 is simpler and equally valid. Use TOPSIS only when there are 3 or more criteria with different types (benefit vs cost).

6. **Do not recommend ECB without computing the all-in INR cost** (coupon + hedging). ECB at 9% USD + 3.5% hedge = 12.83% effective INR cost, which may be higher than domestic borrowing rates for well-rated startups.

7. **Do not advise GeM as sole BD channel** for IT services above Rs 50 lakh threshold. GeM is competitive; also cultivate direct ministry relationships, NASSCOM connections, and public sector frameworks (NICSI, NIC empanelment) for larger contracts.

8. **Do not claim Section 10AA (SEZ) and Section 80-IAC simultaneously** for the same profits. These are mutually exclusive; advise the client to model both scenarios and choose the more beneficial one based on projected profits and timelines.

---

## 12. Output Expectations

When applying this skill, outputs should include:

- **GeM Bid Strategy:** Composite score model, minimum quality score threshold, price floor to remain competitive, MSE multiplier impact if applicable
- **80-IAC NPV Analysis:** Tax savings NPV table across all 8 election windows, optimal window identification with g vs r justification, sensitivity analysis across growth rate scenarios
- **MSMED Classification Report:** Investment/turnover verification, category confirmation, procurement preference benefit quantification, threshold proximity warning if applicable
- **TDS Cash Flow Schedule:** TDS amount per transaction, annual lock-up cost, PAN status confirmation requirement, classification flag (194Q vs 194J)
- **FEMA Compliance Checklist:** Export realization deadline tracking, SOFTEX filing triggers, TNMM NMI computation, arm's-length range assessment
- **Tender Evaluation Matrix:** QCBS/TOPSIS scores for self and modeled competitors, minimum improvement required to change ranking
- **Deal Cash Flow Summary:** Gross revenue, TDS, GST output, ITC, net cash inflow, timing of receivables vs payables, working capital gap

All regulatory values must be accompanied by their research confidence level: "confirmed," "training knowledge — verify at [source]," or "flag — unverified."

---

## 13. Skill Scope

**In scope:**
- GeM portal procurement thresholds, scoring models, and MSE preference mathematics
- DPIIT Startup India recognition criteria and Section 80-IAC NPV optimization
- MSMED Act 2020 classification thresholds and procurement preference modeling
- TDS Section 194Q mechanics, cash flow impact, and 194Q vs 206C(1H) interaction
- FEMA ECB limits, export realization rules, SOFTEX triggers
- Transfer pricing TNMM method and arm's-length range computation
- Government tender evaluation: QCBS, L1, TOPSIS multi-criteria scoring
- GST SAC 998314 treatment for B2B SaaS, input tax credit, export zero-rating
- State incentive schemes: SEZ Section 10AA, STPI benefits, Karnataka/Telangana policies

**Out of scope:**
- Actual comparables database analysis for transfer pricing (requires licensed databases: CRISIL, Bloomberg; engage TP specialist)
- Income tax return filing procedures and due dates (covered by ca-suite domain)
- Customs duty and import licensing (separate regulatory domain)
- RBI forex compounding penalty calculations (legal advice territory)
- SEBI regulations for equity fundraising and ESOPs (covered by fintech domain)
- Labor law compliance (PF, ESI, Gratuity) — separate domain

---

## 14. Version

**Version:** 1.0.1 — 2026-07-27 — Added §8 Anti-Patterns to Avoid (8 pitfalls spanning GeM procurement splitting, 194Q/194J SaaS misclassification, 194Q/206C(1H) double-charging, no-PAN TDS exposure, 80-IAC election timing, MSME dual-criteria classification, MSE-threshold growth trade-offs, and transfer-pricing adjustment misunderstanding); renumbered §8-13 to §9-14.

**Version:** 1.0.0
**Domain:** Agile Business & Revenue Intelligence (Domain 41)
**Research basis:** T06 (BD regulatory research, 2026-05-17); T08 synthesis SK8; T10 M1-M6 derivations by agile-business-mathematics-expert (opus)
**Confirmed values:** GeM thresholds (Search 1), MSME mandate targets (Search 1), TDS 194Q mechanics (training), FEMA ECB limits (training), QCBS/TOPSIS formulas (training)
**Flags requiring verification:** GeM RA threshold (Rs 10 lakh — unverified); DPIIT 80-IAC incorporation window end date; MSMED 2020 exact thresholds; ECB startup USD 3M/FY; TDS 194Q vs 194J SaaS classification
**Math master:** agile-business-mathematics-expert (opus) for M1-M6 derivations beyond this skill's scope
