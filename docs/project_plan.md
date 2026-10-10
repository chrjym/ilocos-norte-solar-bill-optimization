# Project Plan

## Stochastic Optimization of Household Monthly Electricity Bills Under Solar Variability: A Markov Chain and Monte Carlo Approach in Ilocos Norte, Philippines

---

## 1. Problem Statement and Rationale

A household's monthly electricity bill under rooftop solar is a **path-dependent, non-linear function** of the solar irradiance sequence. Three structural features make this true:

1. **Net metering under RA 9513** nets exports over a billing period and credits them at the generation charge, not the full retail rate. Self-consumed kWh and exported kWh therefore have different monetary value.
2. **Unbundled Philippine residential tariffs** contain block structures, lifeline subsidies, and per-kWh riders that do not scale linearly with consumption.
3. **Cloudy spells cluster** — consecutive overcast days in the habagat/typhoon season are correlated, not independent events.

The consequence is that `E[bill] ≠ bill(E[irradiance])`. A deterministic sizing calculation using average monthly irradiance will systematically misestimate both the expected bill and, more importantly, the tail of the bill distribution.

**This justifies the two methodological choices in the title:**

- **Monte Carlo** — because no closed-form expression for the bill distribution exists.
- **Markov chain** (rather than i.i.d. sampling) — because independent draws of daily irradiance would destroy the persistence structure of cloudy spells and understate worst-case monthly bills, which is precisely what drives battery sizing and risk exposure.

---

## 2. Research Objectives

**General objective.** Develop and validate a stochastic simulation–optimization framework that minimizes the expected and risk-adjusted monthly electricity bill of a residential household in Ilocos Norte under solar resource uncertainty.

**Specific objectives.**

1. Construct and statistically validate a month-conditioned Markov chain generator of daily and hourly clearness index for Ilocos Norte, including its seasonal regime shift, and quantify the bias from ignoring day-to-day persistence.
2. Implement a Monte Carlo engine that propagates irradiance uncertainty, a temperature-coupled household demand model, and the reconstructed INEC unbundled tariff and net-metering rules through to the peso-denominated monthly bill distribution.
3. Optimize PV capacity and shiftable-load scheduling (no battery storage) against risk-neutral and risk-adjusted objectives, quantify parameter sensitivity, and validate against real household bills.

**Research questions.**

- How much does ignoring day-to-day persistence in cloudiness bias the estimated monthly bill distribution?
- What is the optimal PV size when the objective includes a risk term, versus when it minimizes expected cost alone?
- Which uncertain input contributes most variance to the bill — irradiance, load, or tariff escalation?

---

## 3. System Architecture

The model is a five-layer pipeline. Each layer is independently testable.

```
Layer 1  Solar stochastic model   →  synthetic hourly GHI sequences
Layer 2  Household demand model   →  synthetic hourly load sequences
Layer 3  Billing model            →  peso bill from net hourly energy flows
Layer 4  Monte Carlo engine       →  distribution of monthly bills
Layer 5  Optimization layer       →  optimal design + operating policy
```

---

## 4. Layer 1 — Solar Stochastic Model (Markov Chain)

### 4.1 Work in clearness index, not raw irradiance

Transform to the clearness index `kt = GHI / H₀`, where `H₀` is extraterrestrial radiation computed for the site latitude. This removes the deterministic seasonal and diurnal trend so the Markov chain models *only* the stochastic residual. Modeling raw GHI directly would force the chain to learn the sun's geometry, which is known exactly.

### 4.2 State discretization

Discretize `kt` into 5–10 states:

| State | Label | Approx. kt range |
|---|---|---|
| 1 | Heavily overcast | 0.00 – 0.15 |
| 2 | Overcast | 0.15 – 0.30 |
| 3 | Cloudy | 0.30 – 0.45 |
| 4 | Partly cloudy | 0.45 – 0.60 |
| 5 | Mostly clear | 0.60 – 0.72 |
| 6 | Clear | 0.72 – 1.00 |

Bin edges are to be finalized from the empirical distribution (equal-probability binning is generally preferable to equal-width). **Treat the number of states as a sensitivity parameter**, not a fixed assumption.

### 4.3 Non-homogeneous transition matrices

Estimate **separate transition probability matrices (TPMs) per month or per season**:

- **Dry season:** November – April
- **Wet / habagat–typhoon season:** May – October

A single pooled TPM would smear two genuinely different persistence regimes together. This non-homogeneity is a defensible methodological contribution in its own right and should be shown explicitly, e.g. by comparing persistence probabilities `P(overcast → overcast)` across seasons.

Estimate entries by maximum likelihood: `p̂ᵢⱼ = nᵢⱼ / Σⱼ nᵢⱼ`. Report cell counts; collapse states if any row is sparsely populated.

### 4.4 Order selection and testing

- Test first- vs. second-order dependence using **AIC and BIC**.
- Run a **chi-square test of the Markov property** (test of order 1 against order 2).
- Report the test result rather than assuming first-order. First-order is usually sufficient at daily resolution and keeps the state space tractable, but the claim must be evidenced.

### 4.5 Daily-to-hourly disaggregation

Hourly resolution is required — it is what distinguishes self-consumed from exported energy, which is the single largest driver of bill savings under Philippine net metering.

Two options:

- **(a)** Run the chain directly at hourly timesteps.
- **(b)** Run it at daily resolution and disaggregate using the **Aguiar–Collares-Pereira TAG** approach, where the sampled daily `kt` state selects an hourly transition matrix.

Option (b) is recommended as the default: more stable estimation, lower data demands, well-established in the literature.

### 4.6 Irradiance-to-power conversion

Chain of physical models, all available in `pvlib-python`:

1. `kt` → GHI (via extraterrestrial radiation at site latitude).
2. GHI → DNI/DHI decomposition (Erbs or DISC).
3. → Plane-of-array irradiance via **Hay–Davies** or **Perez** transposition.
4. → Cell temperature via **NOCT** or **Faiman** model.
5. → DC power via single-diode or PVWatts model.
6. → AC power via inverter efficiency curve.
7. Apply soiling, wiring, mismatch, and availability losses.

Using `pvlib` rather than a hand-rolled conversion is both faster and more defensible under examination.

### 4.7 Data sources

| Source | Use | Notes |
|---|---|---|
| **NASA POWER** | Primary — long hourly record, free, by coordinate | Baseline; satellite-derived |
| **CAMS Radiation Service** | Preferred if accessible | Higher fidelity |
| **Himawari-8 derived products** | Preferred if accessible | Good regional coverage |
| **PAGASA Laoag station** | Ground truth for bias correction | Request early — lead time |

Target site: **Batac City** (the household's location). Laoag City falls in the same NASA POWER grid cell, so it is not modelled separately. Apply bias correction against the PAGASA Laoag station, the nearest ground record, where available.

---

## 5. Layer 2 — Household Demand Model

Load must **not** be treated as deterministic. The bill is driven by the *joint* behavior of supply and demand, and the dependence between them is material.

### 5.1 Data strategy (descending order of rigor)

1. **Best — metered data.** Smart-plug or submeter logs from actual Ilocos Norte households, even a handful over a few months. Highest credibility.
2. **Good — bottom-up appliance model.** An occupancy Markov chain drives appliance switching probabilities. Electric fan and air-conditioning load made **temperature-dependent**.
3. **Fallback — bootstrap resampling** of representative published profiles, with the limitation stated explicitly in the write-up.

### 5.2 Modeling the solar–load dependence

**This is the most consequential modeling decision in Layer 2.** Hot afternoons correlate with high irradiance, which produces favorable self-consumption that an independence assumption would miss entirely. Treating solar and load as independent is the most common error in this class of study.

Implement by making cooling load a function of the same ambient temperature series that drives the PV cell temperature model, so the correlation emerges structurally rather than being imposed.

### 5.3 Appliance inventory

Build a representative Ilocos Norte household appliance set with ratings, typical duty cycles, and classification:

- **Fixed** — refrigerator, lighting, standby loads.
- **Thermostatic** — air conditioning, electric fan (temperature-driven).
- **Shiftable** — laundry, water pumping, water heating, e-trike/EV charging if relevant.

The shiftable set defines the scheduling decision variables in Layer 5.

---

## 6. Layer 3 — Billing Model

**This layer is where most studies in this area are weak, and where this one can be strong.** Reconstruct the bill line by line rather than applying a single ₱/kWh figure.

### 6.1 Bill components to model

- Generation charge
- Transmission charge
- System loss charge
- Distribution, supply, and metering charges
- Subsidies and FIT-All
- Universal charges
- Lifeline rate discount / subsidy, where applicable
- Senior citizen discount, where applicable
- VAT

Use the current **INEC** (Ilocos Norte Electric Cooperative) unbundled rate schedule, cross-checked against the **ERC**-approved structure.

### 6.2 Net metering settlement

Model it as the utility actually applies it:

- Exports credited at the **blended generation cost**, not the full retail rate.
- Credits **carried forward** across billing periods.
- Netting period applied per actual utility practice.
- Observe the net-metering **capacity ceiling** (feeds into Layer 5 constraints).

### 6.3 Verification requirement

**Verify all rates and net-metering rules against current ERC/NEA filings and against the researcher's own actual bills before finalizing.** These change over time. Document the effective date of the rate schedule used, and treat tariff escalation as an uncertain parameter in the sensitivity analysis.

---

## 7. Layer 4 — Monte Carlo Engine

### 7.1 Replication count

Run **5,000–10,000 replications** of 12-month trajectories (or 20–25 year trajectories if computing NPV).

Do **not** pick a round number arbitrarily. Determine N empirically from the standard error of the mean monthly bill and **include a convergence plot** in the results chapter.

### 7.2 Variance reduction

| Technique | Status | Purpose |
|---|---|---|
| **Common random numbers (CRN)** | **Essential** | When comparing a 3 kWp against a 5 kWp system, both must face identical sampled weather and load sequences. Without CRN the comparison is contaminated by sampling noise and small differences become unresolvable. |
| **Latin hypercube sampling** | Recommended | Tightens confidence intervals on parameter-space sampling |
| **Antithetic variates** | Recommended | Further variance reduction at negligible cost |

CRN is non-negotiable. It is the difference between a comparison that resolves the optimum and one that does not.

### 7.3 Generator validation

Validate the synthetic sequences **before** trusting any downstream result:

- **Kolmogorov–Smirnov test** on synthetic vs. historical monthly energy yield distributions.
- **Autocorrelation function** comparison.
- **Persistence / run-length statistics** — distribution of consecutive cloudy days. *A chain that reproduces the mean but not the run-length distribution will mis-size the battery.*
- **Monthly mean bias** by month.
- Seasonal distribution comparison (dry vs. wet).

---

## 8. Layer 5 — Optimization

### 8.1 Decision variables

- PV array size (kWp)
- Inverter rating (kW)
- ~~Battery energy capacity (kWh) and power rating (kW)~~ — **excluded from scope (2026-10-07): the study focuses on PV size and bill reduction**
- Scheduling policy parameters for shiftable loads

### 8.2 Objective function

A pure expected-value objective is the weaker contribution. **Use a risk-adjusted objective** — this is what makes "stochastic optimization" meaningful rather than decorative, and it reflects how an actual household experiences a bill.

Two acceptable formulations:

**(a) Mean–CVaR:**

```
min  E[bill] + λ · CVaR₉₅[bill]
```

**(b) Chance-constrained:**

```
min  E[bill]
s.t. P(monthly bill > ₱X) ≤ α
```

Report results under both the risk-neutral and risk-adjusted objectives to show how the optimal design shifts. That contrast is itself a result.

### 8.3 Constraints

- Capital budget ceiling
- Usable roof area and orientation
- Net-metering capacity ceiling (regulatory)
- Battery state-of-charge bounds and cycle limits
- User comfort limits on load shifting (latest acceptable finish time per shiftable appliance)

### 8.4 Solution method

**Option A — Two-stage stochastic program (preferred if dispatch is linear).**

- First stage: sizing decisions (here-and-now).
- Second stage: hourly dispatch (recourse).
- Solve by **Sample Average Approximation (SAA)** using **Pyomo** with **CBC** or **Gurobi**.
- Report the **optimality gap across independent SAA batches** — this is the standard credibility check.

**Option B — Simulation–optimization (preferred if dispatch rules are non-linear or the design space is small).**

- Grid search, differential evolution, or PSO over the design space.
- Each candidate evaluated by the Monte Carlo engine **under common random numbers**.
- Simpler to implement and entirely defensible.

Choose based on whether the dispatch logic linearizes cleanly. Document the choice and its justification.

---

## 9. Validation and Sensitivity Analysis

### 9.1 Back-testing

Compare model output against **real bills from at least a few households**, both with and without existing PV installations. Report mean absolute percentage error on monthly bills.

### 9.2 Global sensitivity analysis

Use **Sobol indices** — these are stronger than one-at-a-time tornado charts because they capture interaction effects. Vary:

- Tariff escalation rate
- Panel degradation rate
- Discount rate
- Markov state discretization (number of states, bin edges)
- Load model assumptions
- Battery cost (if included)

Reporting first-order and total-order Sobol indices directly answers the research question about which uncertainty dominates.

### 9.3 Results reporting standard

Report **distributions, not point estimates**:

- P10 / P50 / P90 monthly bill
- Probability of exceeding a threshold bill
- CVaR₉₅
- Full bill distribution histograms by scenario

This is the entire payoff of the stochastic framing. Reporting only means would discard the contribution.

---

## 10. Tooling

| Component | Tool |
|---|---|
| Language | Python 3.11+ |
| PV physical modeling | `pvlib-python` |
| Numerics / arrays | `numpy`, `pandas` |
| Statistics / tests | `scipy`, `statsmodels` |
| Optimization (MILP) | `Pyomo` + CBC or Gurobi |
| Metaheuristics | `scipy.optimize.differential_evolution` or `pymoo` |
| Sensitivity analysis | `SALib` (Sobol) |
| Reproducibility | Seeded RNG, version-pinned environment, version control |

Seed management matters: CRN requires deterministic, reproducible seeding across design candidates. Design the seeding scheme explicitly rather than ad hoc.

---

## 11. Scope Control

**This full stack is ambitious for a single project.** Plan a de-scoping path in advance so it is a considered decision rather than a panic measure.

**If time is tight, cut in this order:**

1. Fix the battery out of the model (sizing PV only).
2. Replace MILP dispatch with rule-based dispatch + metaheuristic outer loop.
3. Keep the Markov chain at daily resolution with TAG disaggregation rather than native hourly.
4. Reduce replication count, with convergence evidence justifying the reduction.

That reduced version is still a genuine, publishable stochastic optimization study.

**Do NOT cut these four — they are what separate this from a deterministic payback calculation with noise sprinkled on top:**

1. Correct line-by-line tariff reconstruction
2. Month-conditioned (non-homogeneous) TPM
3. Common random numbers
4. A risk measure in the objective

---

### Scope decisions (2026-10-08)

Excluded from the model and reported as limitations instead:

- **Battery storage** — the study sizes PV only and measures bill reduction.
- **TAG daily-to-hourly disaggregation (§4.5)** — replaced by daily kt × lognormal hourly noise.
- **pvlib physical PV chain (§4.6)** — replaced by a PVWatts-style model on horizontal GHI with NOCT cell temperature.
- **Lifeline and senior-citizen discounts (§6.1)** — not modelled.

---

## 12. Work Plan

| Phase | Work | Output |
|---|---|---|
| **1** | Data acquisition — NASA POWER download, PAGASA request, INEC rate schedule, own bills | Raw dataset, documented rate schedule |
| **2** | Exploratory analysis — kt computation, seasonal characterization, state binning | Descriptive statistics chapter material |
| **3** | Markov chain — TPM estimation, order testing, generator implementation | Validated solar generator |
| **4** | Generator validation — KS, ACF, run-length, bias tests | Validation chapter section |
| **5** | Demand model — appliance inventory, occupancy chain, temperature coupling | Validated load generator |
| **6** | Billing model — line-by-line reconstruction, net metering settlement | Bill calculator, verified against real bills |
| **7** | Monte Carlo engine — integration, CRN seeding, convergence study | Working simulator, convergence plot |
| **8** | Optimization — formulation, solver setup, solution | Optimal designs under both objectives |
| **9** | Sensitivity — Sobol analysis | Sensitivity chapter section |
| **10** | Back-testing and write-up | Final manuscript |

Phases 3–6 can partially overlap; phases 7–9 are strictly sequential.

---

## 13. Key Risks

| Risk | Mitigation |
|---|---|
| PAGASA ground data unavailable or slow | Proceed on NASA POWER; request early; state bias-correction limitation |
| No access to metered household load data | Fall back to bottom-up appliance model (§5.1 option 2); recruit households early |
| Tariff rules change mid-study | Document effective date; treat escalation as sensitivity parameter |
| MILP does not solve in reasonable time | Switch to Option B simulation–optimization (§8.4) |
| Scope overrun | Execute de-scoping path in §11 |

---

## 14. Expected Contributions

1. A validated, season-conditioned Markov chain solar generator calibrated specifically for Ilocos Norte.
2. Quantification of the bias introduced by ignoring cloud persistence in household PV bill estimation.
3. A correctly reconstructed Philippine residential net-metering bill model usable by subsequent researchers.
4. Demonstration that risk-adjusted sizing differs materially from expected-value sizing for Philippine households.
