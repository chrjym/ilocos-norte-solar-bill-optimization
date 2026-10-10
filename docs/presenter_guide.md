# Presenter Guide

A slide-by-slide guide to the adviser presentation, **"Stochastic Optimization of Household Electricity Bills Under Solar Variability"** (34 slides).

Each slide has four parts:

- **Shows:** what is on the slide.
- **Say:** the main points to explain, in plain words.
- **Key numbers:** figures to remember.
- **If asked:** likely adviser questions, with answers.

Deck link: https://claude.ai/artifact/YEoHBdjqx5wr4AERecPu65 (share it from the deck's Share menu before the meeting).

---

## Suggested split and timing

About 35–40 minutes plus questions. One way to divide it among presenters:

| Part | Slides | Topic | Time |
|---|---|---|---|
| 1 | 1–8 | Introduction, site, data, the bill | 8 min |
| 2 | 9–22 | Models, parameters, variables | 14 min |
| 3 | 23–29 | Results | 10 min |
| 4 | 30–34 | Limitations, conclusion, next steps | 6 min |

---

## The one-minute story

If you remember nothing else:

1. A Batac household pays **₱5,739.45** for **464 kWh** in September 2026 (**₱12.36/kWh**).
2. We simulate **2,000 possible weather years** instead of one average year, because the bill under net metering depends on the *sequence* of sunny and cloudy days.
3. The best rooftop solar size, **without a battery**, is **4.5 kWp**.
4. It cuts the yearly bill from **₱70,225 to ₱18,056 (−74%)**, saving **₱52,170 a year**, with a **3.9-year payback**.
5. Bigger systems barely help, because exported power earns only the generation rate.
6. The main uncertainty is the **net-metering credit rule**, and we have **only one month of bills**.

---

## Part 1: Introduction, site and data

### Slide 1: Title

- **Shows:** project title, presenters, adviser, date, and "4.5 kWp" on the right.
- **Say:** "We sized rooftop solar for one Batac City household and estimated how much it cuts the INEC bill, using simulation instead of an average-year calculation. Our answer is 4.5 kWp."
- **Before presenting:** replace **[Presenters]** and **Adviser: [Name]**.

### Slide 2: Problem statement

- **Shows:** three cards (two prices, unbundled tariff, cloudy spells) and the formula **E[bill] ≠ bill(E[irradiance])**.
- **Say:**
  - Solar used at home saves the full retail rate (₱12.36/kWh). Solar exported to the grid earns only the generation rate (about ₱6.30).
  - The bill has fixed charges, per-kWh lines and taxes, so it does not scale simply.
  - Cloudy days come in runs, especially in the habagat and typhoon season.
  - So the average bill is **not** the bill of an average-weather year. We must simulate the whole range of bills.
- **If asked "what does the formula mean?":** the expected (average) bill is not the same as the bill you get when you plug in average sunlight. The bill is non-linear in the weather.

### Slide 3: Why this matters, and what it is used for

- **Shows:** two lists, "Why it matters" and "What it is used for".
- **Say:**
  - **Why:** rates are high and change monthly; it is easy to buy too many panels; bad-weather months cause high bills; the credit rule is unclear.
  - **Used for:** households (enter one bill, get a size and savings), installers (size from real bills), INEC/ERC/LGUs (evidence that the credit rule matters), and other Ilocos Norte households (the same code works).
- **If asked "who would actually use this?":** mainly a household deciding to buy solar, and the installer advising them. The code takes one or more INEC bills as input.

### Slide 4: Objectives and research questions

- **Shows:** three specific objectives and three research questions (RQ1–RQ3).
- **Say:** read the research questions aloud. They are answered on slides 28 (RQ1), 26 (RQ2) and 29 (RQ3), and summarised on slide 32.
  - **RQ1:** Does ignoring cloud persistence bias the bill?
  - **RQ2:** Does adding a risk term change the best size?
  - **RQ3:** Which uncertain input matters most?

### Slide 5: Study site and scope

- **Shows:** site facts and delimitations.
- **Say:**
  - The site is **Batac City** (18.055°N, 120.566°E), served by INEC.
  - Laoag and Batac fall in the same NASA POWER grid cell, so their downloaded data were identical. We model Batac only.
  - **No battery storage**, by design: the focus is how much PV to install and how much the bill drops.
- **If asked "why no battery?":** it was a scope decision. Batteries add large cost and many more parameters; the question here is PV size only. It is listed as out of scope.

### Slide 6: Data sources

- **Shows:** table of all data: NASA POWER weather (2001–2024), INEC 2020 rate schedule, 2026 reported rate, the household bill, and the assumed hourly usage pattern.
- **Say:**
  - Weather: 8,766 days of satellite data, none missing.
  - Tariff: the 2020 INEC line structure, updated to the 2026 total of ₱11.7246/kWh.
  - Household: one real bill, September 2026.
  - Hourly usage pattern: **assumed typical household**, not surveyed.
- **If asked "where did the 2026 generation rate come from?":** it was not published. We solved it as ₱6.0848/kWh, the value that makes the 2020 line structure add up to the reported 2026 total.

### Slide 7: The household bill, without and with solar

- **Shows:** the real September bill grouped into 9 charge groups, with columns **Now / With PV / Reduced**.
- **Say:**
  - Today: **₱5,740** (bill says ₱5,739.45).
  - With 4.5 kWp: we buy only **303 kWh** instead of 464, and export **372 kWh**.
  - The export credit cancels the **generation charge and its VAT** completely (₱2,925 → ₱0).
  - The other charges drop only because we buy less power.
  - Result: about **₱1,614**, a reduction of **₱4,126 (−72%)**.
- **If asked "why ₱1,614 here but ₱1,512 on slide 27?":** this slide uses the bill's own rates. The model splits the same total rate using INEC's 2020 line structure, which gives ₱1,512. The difference is the tariff split, not the solar.
- **If asked "why does the generation charge go to zero?":** under the generation-only credit rule, export credit can only offset generation charges. 372 kWh exported is worth more than the generation charge on 303 kWh imported, so it is fully covered, and the extra credit carries forward.

### Slide 8: Why only one billing month

- **Shows:** five reasons, plus how the bill is used.
- **Say:**
  - Timing: data collection matched the September billing cycle.
  - The printed slip shows only the current month.
  - Earlier slips were not kept.
  - No online history was available.
  - Thermal paper fades.
  - So September is a **calibration anchor**: it fixes the household's consumption level and real rate; other months come from the model.
- **Also say:** the household reports September 2026 was unusually hot.
- **If asked "is one month enough?":** it is enough to demonstrate the method, which is the usual situation for a first-time solar buyer. It is not enough for a precise annual forecast; see slide 31.

---

## Part 2: The models, parameters and variables

### Slide 9: Methodology overview

- **Shows:** six boxes: Weather → PV output → Load → INEC bill → Monte Carlo → Optimizer, with the code module for each.
- **Say:** "One simulated weather sequence drives both solar supply and household demand. Temperature affects both panel losses and aircon use, so the link between solar and demand comes from the data. Each simulated year ends as twelve monthly bills."

### Slide 10: The models: purpose and importance (1 of 2)

- **Shows:** four cards: Markov chain, PV output, temperature, household load. Each has **Used for** and **Why it matters**.
- **Say:** go card by card.
  - **Markov chain:** generates realistic runs of sunny and cloudy days. It matters because cloudy days cluster.
  - **PV output:** turns sunlight into kWh. Heat reduces output 0.4% per °C.
  - **Temperature:** gives temperature consistent with each day. The same weather drives aircon and panel losses.
  - **Load:** hourly demand from a typical pattern, scaled to the bill. Only hourly netting shows how much solar is used at home vs exported.

### Slide 11: The models: purpose and importance (2 of 2)

- **Shows:** four cards: tariff and net metering, Monte Carlo, optimization, Sobol sensitivity.
- **Say:**
  - **Tariff and net metering:** rebuilds the bill in pesos. Savings depend on which charges solar avoids.
  - **Monte Carlo:** 2,000 simulated years per design, giving average and bad-year bills.
  - **Optimization:** picks the size: 4.5 kWp.
  - **Sobol sensitivity:** tells us what data to collect next.

### Slide 12: Weather model: Markov chain

- **Shows:** two formulas and how a day is generated.
  - **kt = GHI / H₀**: the clearness index, the share of top-of-atmosphere sunlight reaching the ground.
  - **p̂ᵢⱼ = nᵢⱼ / Σⱼ nᵢⱼ**: transition probability, counted from 24 years of data.
- **Say:**
  - kt removes the sun's predictable geometry, so the chain only models the random weather.
  - Daily kt is split into 6 states. For each calendar month, we count how often state i is followed by state j.
  - To simulate: today's state and the month pick a row; we draw tomorrow's state; then a kt value from real days in that state; then split into hours.
  - Tomorrow depends on today, so cloudy spells last as they really do.
- **If asked "what is a Markov chain?":** a random process where the next state depends only on the current state. Here: tomorrow's weather depends only on today's.

### Slide 13: Weather model parameters

- **Shows:** table of fitted parameters.
- **Key numbers:**
  - 6 equal-probability states; edges 0.42, 0.52, 0.58, 0.62, 0.66.
  - 12 transition matrices (one per month).
  - First-order chain: likelihood-ratio test p = 0.50 (dry), 0.64 (wet); BIC also prefers it.
  - Overcast → overcast: 57% wet season, 42% dry.
  - Within-state AR(1) ρ = 0.075; hourly noise σ = 0.15, kt capped at 0.85.
- **If asked "why 6 states?":** 8 and 10 states were tested. They improved persistence only slightly while making each monthly matrix sparser, so 6 was kept.
- **If asked "why per month and not per season?":** the two-season version failed the dry-season validation test and biased monthly means by up to 11% (slide 23).

### Slide 14: PV output model

- **Shows:** the PV equation and a symbol table.
  - **P = kWp · (GHI/1000) · [1 + γ(Tc − 25)] · DERATE**
  - **Tc = Ta + GHI · (NOCT − 20)/800**
- **Key numbers:** γ = −0.004/°C, NOCT = 45 °C, DERATE = 0.86.
- **Say:** output scales with size and sunlight, loses 0.4% per degree of cell temperature above 25 °C, and loses 14% to inverter, soiling, wiring and availability.
- **If asked "what about panel tilt?":** not modelled; we use horizontal irradiance. This is a listed simplification.

### Slide 15: Temperature model

- **Shows:** two regression equations and their parameters.
- **Say:**
  - Daily mean temperature and daily range depend on the month and on whether that day is sunnier or cloudier than usual.
  - The day-to-day leftover follows an AR(1) process (φ = 0.63–0.83), so hot spells persist.
  - Hourly shape: minimum at 06:00, maximum at 14:00.
- **Key numbers:** monthly means within 0.1 °C of NASA; temperature–kt correlation up to +0.64 (May).
- **If asked "why model temperature at all?":** it drives aircon and fan use, and panel losses. Without it, demand and solar would be unrelated.

### Slide 16: Load parameters and calibration

- **Shows:** occupancy and aircon parameters, the calibration formula, and the estimated monthly kWh.
- **Say:**
  - A **typical household usage pattern is assumed** (not surveyed). It sets **when** power is used; the bill sets **how much**.
  - Occupancy: home-active or away, with 0.8 hourly persistence.
  - Aircon runs overnight if it is still ≥ 26.5 °C at 21:00.
  - Calibration: **kWhₘ = modelₘ × 464 / model_Sep**. Each month is scaled so September equals the bill.
- **Key numbers:** 5,677 kWh/yr; January 321 to May 676 kWh; September 464 (real).
- **If asked "where did the appliance data come from?":** it is an assumed typical pattern, not your household's survey. It is needed because solar savings depend on the time of day power is used, and the bill only gives a monthly total.

### Slide 17: Tariff parameters

- **Shows:** model tariff lines (2026, derived), VAT and tax parameters, and the calibrated rate.
- **Key numbers:**
  - Generation ₱6.0848 (solved), transmission ₱1.5476 (reported), all-in ₱11.7246/kWh.
  - VAT 12%, franchise tax 0.866% + 0.5%, fixed metering ₱5/month.
  - Calibration scale ×1.054 → **₱12.36/kWh** (back-test error 5.1%).
- **Say:** "We rebuild the bill line by line. The model's default rate was 5.1% below the real bill, so all rates are scaled by 1.054 to match it."

### Slide 18: Net metering

- **Shows:** three equations and two scenarios.
  - **import_h = max(load_h − PV_h, 0)**, **export_h = max(PV_h − load_h, 0)**
  - **bill_m = rates · Σ import + ₱5 − min(credit, offsettable charges)**
  - **credit_m = generation rate · Σ export + unused credit carried forward**
- **Say:**
  - Netting is hourly: solar first covers the home's use; the rest is exported.
  - Exports earn credit at the generation rate.
  - **"Generation" scenario (main):** credit can only offset generation charges. More conservative.
  - **"Bill" scenario:** credit can offset all variable charges. Upper bound.
- **If asked "which rule does INEC use?":** not yet confirmed. We need one net-metered INEC bill. That is our top remaining task.

### Slide 19: Monte Carlo engine

- **Shows:** common random numbers, seeding, replications, output statistics.
- **Say:**
  - Each design is tested on the **same 2,000 simulated years** (common random numbers), so differences come from the design, not luck.
  - Master seed 20261007, split into separate streams for weather, temperature and load.
- **Statistics to define:**
  - **P10/P90:** 10% of years are below/above this bill.
  - **CVaR95:** average of the worst 5% of outcomes.
  - **P(month > X):** share of months above a bill threshold.
- **If asked "why 2,000?":** the convergence study (slide 24) shows every statistic is within ±1% at that size.

### Slide 20: Optimization

- **Shows:** cost definition, three objectives, parameter table.
  - **C = annual bill + annualized capex**
  - (1) min E[C]; (2) min E[C] + λ·CVaR95[C]; (3) min E[C] s.t. P(bill > X) ≤ α
- **Key numbers:** sizes 0–6 kWp in 0.5 steps; ₱45,000/kWp (placeholder); 8% discount; 20-year life; λ = 0.5; X = ₱1,000; α = 0.05.
- **Say:** "We test 13 sizes × 2 schedules = 26 designs and pick the best under each objective."
- **If asked "is ₱45,000/kWp real?":** it is a placeholder until we get an installer quote. Sensitivity analysis shows cost barely changes the best size.

### Slide 21: Summary of variables

- **Shows:** every variable by type: decision, random, derived, output, calibration.
- **Say:**
  - **Decision** (chosen): PV size and appliance schedule.
  - **Random** (simulated): kt, irradiance, temperature, occupancy, load.
  - **Derived:** hourly PV, import, export.
  - **Output:** monthly bill, annual cost, expected cost, CVaR, exceedance probability.
  - **Calibration** (from the bill): 464 kWh, ₱5,739.45, scale 1.054.
- **Tip:** this slide is the quick reference if the adviser asks "what are your variables?"

### Slide 22: Sensitivity analysis setup

- **Shows:** 8 uncertain inputs with ranges, and the Sobol method.
- **Key numbers:** cost ₱35,000–60,000/kWp; escalation 0–5%/yr; degradation 0.3–0.8%/yr; discount 5–12%; consumption 0.7–1.4×; aircon yes/no; export credit 0.8–1.2×; offset rule bill/generation. N = 512 → 5,120 runs.
- **If asked "what is a Sobol index?":** the share of an output's variance caused by one input. First-order is the input alone; total-order includes its interactions.

---

## Part 3: Results

### Slide 23: Result 1: weather model validation

- **Shows:** validation tests comparing the per-month chain (used), a two-season chain and independent days.
- **Say:** "Only the per-month chain passes every test." Point at:
  - Monthly bias within ±0.7%.
  - Cloudy-spell lengths match (p = 0.76); P95 spell 8 days, same as the record.
  - Independent days fail badly: cloudy spells half as long.
- **Weakness to admit:** lag-1 autocorrelation 0.56 vs 0.64 in the record.

### Slide 24: Result 2: demand and convergence

- **Shows:** temperature and load checks; convergence table.
- **Say:**
  - Temperature matches NASA within 0.1 °C.
  - In an aircon home, aircon is the largest end use (28%), and only 45% of use falls in daylight.
  - Daytime load vs PV correlation is only +0.17, because cooling is mostly at night.
  - At N = 2,000, every statistic is within ±1%; all 10 batches pick the same best size.

### Slide 25: Result 3: annual bill by PV size

- **Shows:** bar chart and table of the mean annual bill from 0 to 6 kWp; 4.5 kWp highlighted.
- **Say:**
  - Each 0.5 kWp saves ₱4,600–9,000/yr up to 4 kWp, then ₱2,500 for the step to 4.5.
  - After 4.5 kWp, each step saves only ₱130–210, because the extra power is exported at the low generation credit.
- **Key numbers:** ₱70,225 (no solar) → ₱18,056 (4.5 kWp); payback 3.9 years; 6 kWp only reaches ₱17,564 with a 5.1-year payback.

### Slide 26: Result 4: recommended design

- **Shows:** **4.5 kWp** with four numbers and the objectives table.
- **Key numbers:** −74%; ₱52,170 saved per year; 3.9-year payback on ₱202,500; +₱1,094/yr from load shifting.
- **Say (RQ2):**
  - Risk-neutral and mean–CVaR both choose 4.5 kWp: **the risk term changes nothing** here.
  - The ₱1,000/month target is **impossible at any size** (P = 0.81 at 4.5 kWp), because night aircon must come from the grid without a battery.
  - Robust range: **3.5–4.5 kWp**, covering a hot September and the other credit rule.

### Slide 27: Result 4b: monthly bill with 4.5 kWp

- **Shows:** each month's bill without and with solar, and the reduction; yearly summary.
- **Say:**
  - Every month drops by about three-quarters.
  - September (the real bill): ₱5,739 → ₱1,512 (model estimate).
  - Biggest peso savings in April and May (₱5,700–6,100/month), the hottest months.
  - PV makes 6,699 kWh/yr: 2,053 used at home, 4,647 exported. About 3,625 kWh is still bought, mostly night aircon.
- **Remember:** only September is a real bill; other months are model estimates.

### Slide 28: Result 5: cloud persistence (RQ1)

- **Shows:** monthly bill statistics with the Markov chain vs independent days, at 1 and 4.5 kWp.
- **Say:**
  - For this household, ignoring cloud persistence changes the bill by **less than 1%**.
  - Why: the bill varies mostly by season (321–676 kWh) and night aircon, not by cloudy runs.
  - Contrast: for a small no-aircon household, the worst 5% of bills were understated by about 6%.
  - Conclusion: persistence matters when solar covers most of a small, daytime-heavy load.
- **If asked "then why use a Markov chain?":** the weather model must be realistic to pass validation (slide 23), and whether persistence matters depends on the household. We could only know it is small here by testing it.

### Slide 29: Result 6: sensitivity (RQ3)

- **Shows:** total-order Sobol indices for three outputs.
- **Key numbers:**
  - Optimal size: consumption 0.45, credit offset rule 0.31, aircon 0.31.
  - 20-year benefit: discount rate 0.40, consumption 0.24, tariff escalation 0.19.
  - First-year bill cut: credit offset rule **0.99**.
- **Say:** "The household sets the size; the credit rule sets the savings. Installed cost and panel degradation barely matter."
- **Caveat to mention:** these runs vary inputs around a generic household, so they rank inputs; they do not size the Batac system.

---

## Part 4: Limitations, conclusion and next steps

### Slide 30: Limitations: model and data

- **Shows:** 9 limitations and their effects.
- **Say:** the most important are:
  - The credit rule is not confirmed, so both rules were run.
  - The tariff is partly derived.
  - The typical usage pattern is assumed.
  - The PV model has no tilt or orientation.
  - The climate is assumed stationary.
  - The installed cost is a placeholder.
- **Tip:** say these confidently. Stating limitations clearly shows you understand the model.

### Slide 31: Limitations: single billing month

- **Shows:** six cards on what one September bill cannot tell us.
- **Say:**
  - Only 1 of 12 months is observed; 5,677 kWh/yr is extrapolated.
  - **Hot September:** if heat inflated the bill by 15%, the year is 4,931 kWh and the size is 3.5–4.0 kWp.
  - The months that drive sizing (March–June) are all estimates.
  - P10/P90 cover weather only, not behaviour.
  - The rate is fixed at September's; no out-of-sample test; one household only.

### Slide 32: Conclusion

- **Shows:** the answers to RQ1–RQ3.
- **Say:**
  - About **4.5 kWp** cuts the bill by about three-quarters.
  - **RQ1:** under 1% for this household; about 6% for a small no-aircon home.
  - **RQ2:** the risk term agrees with the expected-value size.
  - **RQ3:** consumption sets the size; the credit rule sets the bill cut; the discount rate sets the long-run benefit.
  - Recommended range: **3.5–4.5 kWp**.

### Slide 33: Recommendations and remaining work

- **Shows:** remaining work and recommendations.
- **Say:**
  - **Most valuable next step:** one net-metered INEC bill to settle the credit rule.
  - Then: another month of bills (ideally April or May), PAGASA temperatures for September 2026, an installer quote, and bills from 3–5 more households.
  - Recommendations: size from your own bills, run washing and pumping at midday, and INEC/ERC should publish the credit rule plainly.
- **Already done:** the tariff back-test against the September bill (5.1% error).

### Slide 34: Thank you

- **Say:** invite questions.
- **Good questions to ask the adviser:**
  - Is the generation-only credit rule acceptable as the main case?
  - Is one bill plus the hot-September sensitivity enough for the scope?
  - Should we collect the household's real appliance list?

---

## Quick answers to common questions

| Question | Short answer |
|---|---|
| Why simulation instead of an average year? | The bill is non-linear: two prices, fixed charges, cloudy runs. The average bill ≠ the bill of average weather. |
| Why no battery? | Scope decision: the question is PV size and bill reduction. |
| Why only Batac, not Laoag? | Same NASA grid cell; the data were identical. |
| Why one bill? | Only record available (slide 8). Used as a calibration anchor. |
| Is the appliance data real? | No. A typical usage pattern is assumed; only the 464 kWh total is real. |
| Why does the bill not reach zero? | Night aircon must be bought from the grid without a battery. |
| Why not a bigger system? | After 4.5 kWp, extra output is exported at the generation rate only; each 0.5 kWp saves ₱130–210/yr. |
| What is the biggest uncertainty? | The net-metering credit rule (Sobol 0.99 for bill cut). |
| How sure is 4.5 kWp? | 4.5 kWp under our assumptions; 3.5–4.5 kWp across a hot September and the other credit rule. |
| Why does slide 7 say ₱1,614 and slide 27 ₱1,512? | Same solar, different tariff split: the bill's own rates vs the model's 2020 line structure. |

## Where things are in the repository

| To show | File |
|---|---|
| Full write-up | `docs/project_report.md` |
| What every file does | `docs/repository_guide.md` |
| Household result | `.venv/bin/python -m src.household --kwh 464 --pesos 5739.45 --month 9 --aircon --offset generation` |
| Monthly bill table | `results/monthly_bill.csv` |
| Validation figures | `results/generator_validation.png`, `results/load_validation.png`, `results/convergence.png` |
| Size results | `results/optimization.csv`, `results/optimization.png` |
| Sensitivity | `results/sensitivity.txt`, `results/sensitivity.png` |
