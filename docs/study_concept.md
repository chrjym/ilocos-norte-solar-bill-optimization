# Stochastic Optimization of Household Monthly Electricity Bills Under Solar Variability: A Markov Chain and Monte Carlo Approach in Ilocos Norte, Philippines

## 1. Overview

This study determines how much solar PV capacity a household should install to achieve the lowest and most reliable monthly electricity bill. Because solar output depends on weather and household demand is uncertain, the study uses stochastic simulation instead of a single average-year calculation.

**Guiding question:** *How much solar should be installed so that the monthly bill is as low as possible, and how confident can we be about that bill?*

## 1A. Study Area: Ilocos Norte

The study is limited to Ilocos Norte, Philippines with Batac City (about 18.06 N, 120.57 E) as the study site.

**Why Ilocos Norte is a good case**

- **Two pronounced seasons.** Ilocos Norte falls under PAGASA Climate Type I, with a dry season (about November to April) and a wet season (about May to October). This justifies separate Markov transition matrices per season.
- **Typhoon and monsoon exposure.** Northern Luzon is frequently affected by typhoons and the southwest monsoon, so multi-day overcast and rainy spells are real risks. This makes the weather-persistence feature of the Markov chain especially relevant. Consider adding a fifth "typhoon/heavy rain" state.
- **Strong renewable context.** The province hosts wind farms (Bangui, Burgos, Pagudpud), a mini-hydro plant, and expanding solar farms (e.g., Currimao), so rooftop solar fits local energy conditions.
- **Volatile and high power rates.** Reported INEC residential rates have swung widely, for example about PHP 17.9/kWh in October 2022 versus about PHP 14.0/kWh in January 2023 (VAT-inclusive), and PHP 14.74/kWh in August 2023 versus PHP 11.00/kWh in October 2023. High and moving rates strengthen the economic case for solar and make the tariff itself an uncertain input.
- **Single distribution utility.** The Ilocos Norte Electric Cooperative (INEC) serves the province, so one tariff and one set of net-metering rules define the bill calculation.

**Study-area implications for the model**

1. Use Ilocos Norte coordinates and elevation for solar geometry and for the NASA POWER or PVGIS data queries.
2. Estimate weather transitions separately for dry and wet seasons, with an optional typhoon state.
3. Treat the generation charge (the largest bill component, reported at roughly 72 to 74 percent of the bill) as a random input, for example with a monthly rate scenario (low, base, high) or a simple Markov or lognormal rate model.
4. Calibrate household load using INEC bills from households in the province.

## 2. Problem Statement

Conventional solar sizing relies on average-year estimates. These hide the risk of prolonged cloudy or rainy periods, which are the months that drive the highest bills. Utility tariffs are also nonlinear (tiered rates, different import and export prices), so the best system size is not obvious and a bigger system is not always cheaper.

## 3. Objectives

### General objective

	To determine the optimal solar PV capacity that minimizes the expected monthly electricity bill and its risk under stochastic weather and load conditions, using Markov chain and Monte Carlo simulation.

### Specific objectives

1. Model daily weather states from historical solar data using a Markov chain, and validate the generator against the observed record.
2. Simulate hourly PV output and household load under those weather states, and compute the monthly bill distribution for each candidate PV size using the INEC tariff and net metering (Monte Carlo).
3. Identify the PV capacity that minimizes the expected bill and a risk measure (95th-percentile bill) within budget limits, and determine which input (weather, load, or tariff) affects the bill most through sensitivity analysis.

## 4. Scope and Delimitations

- One household (or building) on one utility tariff structure
- Decision variable: PV capacity (battery storage and load shifting are extensions)
- Hourly time step, one-month simulation horizon
- Location: Ilocos Norte only, with separate dry and wet season models
- Utility: Ilocos Norte Electric Cooperative (INEC) tariff and its net-metering arrangement

## 5. System Description

A grid-connected household with a rooftop PV system. At each hour, the household consumes energy, the PV system generates energy, and the difference is imported from or exported to the grid.

```
Bill = (Import energy x import rate) - (Export energy x export rate) + Fixed charges

Import(t) = max(0, L(t) - PV(t))
Export(t) = max(0, PV(t) - L(t))
```

## 6. Variables and Parameters

### 6.1 Decision variables

| Symbol | Variable | Typical range |
|---|---|---|
| P_pv | PV capacity (kW) | 1 to roof limit (e.g., 10 kW) |
| E_bat | Battery capacity (kWh), extension | 0 to 15 kWh |
| Load-shift fraction | Share of flexible load moved to daytime, extension | 0 to 30% |

### 6.2 Random variables

| Variable | Description |
|---|---|
| W(t) | Weather state (clear, partly cloudy, overcast, rainy), Markov chain |
| k_t | Clearness index (actual / clear-sky irradiance), drawn per weather state |
| L(t) | Hourly household load (kWh) |
| T(t) | Ambient temperature, affecting PV efficiency and cooling load |
| Tariff changes | Optional year-to-year rate changes |

### 6.3 Model parameters

**Estimated from data**

- Markov transition probabilities p_ij for each season
- Beta distribution parameters (alpha, beta) of k_t for each weather state
- Load model coefficients: baseline, temperature effect, weekday/weekend effect, noise variance

**Fixed technical parameters**

- PV temperature coefficient: about -0.4 %/degree C
- Performance ratio: about 0.75 to 0.85
- Inverter efficiency: about 0.95 to 0.97
- Annual degradation: about 0.5 %/year
- Battery round-trip efficiency, depth of discharge, power limits (if included)

**Fixed economic and tariff parameters**

- Import rate (PHP/kWh), including tiers or time-of-use blocks
- Export or net-metering credit rate (PHP/kWh)
- Fixed monthly charges
- PV installation cost (PHP/kW) and O&M cost
- Discount rate and project lifetime

**Location parameters**

- Latitude, longitude, elevation of the chosen Ilocos Norte site (Batac City, about 18.06 N, 120.57 E)
- PAGASA Type I climate (dry about Nov to Apr, wet about May to Oct)

### 6.4 Simulation settings

- Time step: 1 hour
- Horizon: 1 month per run (12 months for annual comparison)
- Monte Carlo runs: N = 5,000 (range 1,000 to 10,000)
- Random seed fixed for reproducibility

## 7. Methodology

### 7.1 Chosen model

**Core model:** Markov chain weather model driving a Monte Carlo bill simulation.

A Markov chain captures the clustering of cloudy days, which independent daily sampling would miss. Monte Carlo then repeats the month thousands of times and handles the nonlinear tariff without needing a closed-form solution.

### 7.2 Role of each algorithm

| Method | Role |
|---|---|
| Markov chain | Generates realistic sequences of daily weather states |
| Monte Carlo | Simulates thousands of months to build the bill distribution |
| MCMC (optional) | Estimates transition probabilities (Dirichlet priors) and Beta parameters with uncertainty |
| Latin Hypercube sampling | Improves Monte Carlo efficiency |
| Sobol indices | Ranks which uncertain inputs matter most |

### 7.3 Simulation steps

1. **Collect data.** Daily and hourly solar irradiance and temperature from NASA POWER or PVGIS; household bills or load profile; the utility tariff schedule.
2. **Classify days.** Assign each historical day to a weather state using its clearness index k_t.
3. **Estimate the transition matrix.** Count day-to-day transitions separately for the dry and wet seasons.
4. **Generate weather.** For each simulated month, sample a sequence of daily states from the Markov chain.
5. **Generate solar output.** Draw k_t from the state's Beta distribution, then convert to hourly PV output using clear-sky irradiance, P_pv, temperature, and system losses.
6. **Generate load.** Use a baseline hourly profile with weekday/weekend and temperature effects plus random noise.
7. **Compute the bill.** Calculate hourly import and export, then apply the tariff to get the monthly bill.
8. **Repeat.** Run steps 4 to 7 for N simulated months for each candidate P_pv.
9. **Optimize.** Compare designs on expected bill and risk, and select the best feasible size.
10. **Analyze sensitivity.** Vary import rate, export rate, PV cost, load level, and cloudiness.

### 7.4 Pseudocode

```python
for P_pv in candidate_sizes:
    bills = []
    for run in range(N):
        weather = simulate_markov_month(transition_matrix[season])
        pv = generate_pv_output(weather, P_pv, params)
        load = generate_load(weather, params)
        imp = np.maximum(0, load - pv)
        exp = np.maximum(0, pv - load)
        bill = tariff(imp, exp)        # tiers, import/export rates, fixed charge
        bills.append(bill)
    results[P_pv] = {
        "mean": np.mean(bills),
        "p95": np.percentile(bills, 95),
        "std": np.std(bills),
    }
best = min(feasible_designs, key=lambda p: results[p]["mean"] + lam * results[p]["p95"])
```

## 8. Optimization Formulation

```
Minimize    E[Bill(P_pv)] + lambda * Risk(Bill(P_pv))
Subject to  P_pv <= roof limit
            Installation cost <= budget
            Payback period <= target
```

The weight lambda controls the trade-off between a low average bill and a stable bill. Risk can be measured as the 95th-percentile bill or the Conditional Value at Risk (CVaR).

## 9. Output Metrics

- Expected monthly bill and standard deviation
- 95th-percentile (bad-month) bill
- Probability that the bill exceeds a target amount
- Self-consumption ratio and solar fraction
- Monthly savings, payback period, and net present value

## 10. Expected Deliverables

1. Recommended PV capacity for the household and tariff
2. Distribution of monthly bills for each design, for example "the expected bill is X PHP, and in a bad month it will not exceed Y PHP"
3. Financial evaluation of the recommended design
4. Ranking of the most influential uncertain inputs

## 11. Significance

The study shows how weather persistence and repeated simulation change the optimal solar size compared with average-year methods, giving households a risk-aware recommendation. It also demonstrates how Markov chain and Monte Carlo methods apply to a practical electricity problem.

## 12. Data Sources

| Data | Source |
|---|---|
| Solar irradiance, temperature | NASA POWER, PVGIS |
| Household load | Past bills, smart meter, or published load profiles |
| Tariff and net-metering rules | INEC monthly rate advisories and net-metering guidelines (confirm the export credit basis with INEC and the Energy Regulatory Commission, since it may be based on generation cost rather than the full retail rate) |
| Local weather records | PAGASA station data (e.g., Laoag) to cross-check NASA POWER or PVGIS |
| PV and installation costs | Local supplier quotations |

## 13. Possible Extensions

- Add battery storage and dispatch logic
- Add load shifting of flexible appliances
- Use a Hidden Markov Model for weather states
- Use full Bayesian estimation with MCMC
- Include tariff escalation over the project lifetime
- Extend to commercial or institutional buildings
- Compare municipalities within Ilocos Norte (e.g., coastal Pagudpud versus inland Dingras)

## 14. Parameter Table Template

Include a table like this in the paper so every symbol is documented.

| Symbol | Description | Units | Value or range | Source | Role |
|---|---|---|---|---|---|
| P_pv | PV capacity | kW | 1 to 10 | Decision | Decision variable |
| p_ij | Weather transition probability | , | Estimated | NASA POWER data | Estimated parameter |
| PR | Performance ratio | , | 0.75 to 0.85 | Literature | Fixed |
| r_imp | Import rate | PHP/kWh | INEC monthly rate (has varied roughly PHP 11 to 18) | INEC advisories | Fixed or scenario |
| r_exp | Export credit rate | PHP/kWh | Per INEC net-metering terms | INEC / ERC | Fixed or scenario |
