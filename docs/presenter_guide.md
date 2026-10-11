# Presenter Guide

A slide-by-slide guide to the adviser presentation, **"Stochastic Optimization of Household Electricity Bills Under Solar Variability"** (17 slides).

Each slide has four parts:

- **Shows:** what is on the slide.
- **Say:** the main points to explain, in plain words.
- **Key numbers:** figures to remember.
- **If asked:** likely adviser questions, with answers.

Deck link: https://claude.ai/artifact/YEoHBdjqx5wr4AERecPu65 (share it from the deck's Share menu before the meeting).

The deck was trimmed from 34 to 17 slides. Detail that was removed (data sources, PV and temperature models, tariff, net metering, validation, convergence, persistence and sensitivity) is kept under **Backup answers** below, so you can still answer questions on it.

---

## Suggested split and timing

About 20–22 minutes plus questions. One way to divide it among presenters:

| Part | Slides | Topic | Time |
|---|---|---|---|
| 1 | 1–5 | Introduction, scope, the bill | 5 min |
| 2 | 6–10 | The model | 6 min |
| 3 | 11–14 | Results and what the models contributed | 7 min |
| 4 | 15–17 | Limitations, conclusion | 3 min |

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

## Part 1: Introduction, scope and the bill

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
### Slide 3: Objectives and research questions

- **Shows:** three specific objectives and three research questions (RQ1–RQ3).
- **Say:** read the research questions aloud. RQ2 is answered on slide 12; all three are answered on slide 16 (Conclusion).
  - **RQ1:** Does ignoring cloud persistence bias the bill?
  - **RQ2:** Does adding a risk term change the best size?
  - **RQ3:** Which uncertain input matters most?
### Slide 4: Study site and scope

- **Shows:** site facts and delimitations.
- **Say:**
  - The site is **Batac City** (18.055°N, 120.566°E), served by INEC.
  - Laoag and Batac fall in the same NASA POWER grid cell, so their downloaded data were identical. We model Batac only.
  - **No battery storage**, by design: the focus is how much PV to install and how much the bill drops.
- **If asked "why no battery?":** it was a scope decision. Batteries add large cost and many more parameters; the question here is PV size only. It is listed as out of scope.
### Slide 5: The household bill, without and with solar

- **Shows:** the real September bill grouped into 9 charge groups, with columns **Now / With PV / Reduced**.
- **Say:**
  - Today: **₱5,740** (bill says ₱5,739.45).
  - With 4.5 kWp: we buy only **303 kWh** instead of 464, and export **372 kWh**.
  - The export credit cancels the **generation charge and its VAT** completely (₱2,925 → ₱0).
  - The other charges drop only because we buy less power.
  - Result: about **₱1,614**, a reduction of **₱4,126 (−72%)**.
- **If asked "why ₱1,614 here but ₱1,512 on slide 13?":** this slide uses the bill's own rates. The model splits the same total rate using INEC's 2020 line structure, which gives ₱1,512. The difference is the tariff split, not the solar.
- **If asked "why does the generation charge go to zero?":** under the generation-only credit rule, export credit can only offset generation charges. 372 kWh exported is worth more than the generation charge on 303 kWh imported, so it is fully covered, and the extra credit carries forward.
- **If asked "why only one bill?":** it is the only record available (the slip shows only the current month, earlier slips were not kept). September is used as a **calibration anchor**: it fixes the consumption level and real rate; other months come from the model. The household reports September 2026 was unusually hot.

---

## Part 2: The model

### Slide 6: Methodology overview

- **Shows:** six boxes: Weather → PV output → Load → INEC bill → Monte Carlo → Optimizer, with the code module for each.
- **Say:** "One simulated weather sequence drives both solar supply and household demand. Temperature affects both panel losses and aircon use, so the link between solar and demand comes from the data. Each simulated year ends as twelve monthly bills."
### Slide 7: Weather model: Markov chain

- **Shows:** two formulas and how a day is generated.
  - **kt = GHI / H₀**: the clearness index, the share of top-of-atmosphere sunlight reaching the ground.
  - **p̂ᵢⱼ = nᵢⱼ / Σⱼ nᵢⱼ**: transition probability, counted from 24 years of data.
- **Say:**
  - kt removes the sun's predictable geometry, so the chain only models the random weather.
  - Daily kt is split into 6 states. For each calendar month, we count how often state i is followed by state j.
  - To simulate: today's state and the month pick a row; we draw tomorrow's state; then a kt value from real days in that state; then split into hours.
  - Tomorrow depends on today, so cloudy spells last as they really do.
- **If asked "what is a Markov chain?":** a random process where the next state depends only on the current state. Here: tomorrow's weather depends only on today's.
### Slide 8: Load parameters and calibration

- **Shows:** occupancy and aircon parameters, the calibration formula, and the estimated monthly kWh.
- **Say:**
  - A **typical household usage pattern is assumed** (not surveyed). It sets **when** power is used; the bill sets **how much**.
  - Occupancy: home-active or away, with 0.8 hourly persistence.
  - Aircon runs overnight if it is still ≥ 26.5 °C at 21:00.
  - Calibration: **kWhₘ = modelₘ × 464 / model_Sep**. Each month is scaled so September equals the bill.
- **Key numbers:** 5,677 kWh/yr; January 321 to May 676 kWh; September 464 (real).
- **If asked "where did the appliance data come from?":** it is an assumed typical pattern, not your household's survey. It is needed because solar savings depend on the time of day power is used, and the bill only gives a monthly total.
### Slide 9: Monte Carlo engine

- **Shows:** common random numbers, seeding, replications, output statistics.
- **Say:**
  - Each design is tested on the **same 2,000 simulated years** (common random numbers), so differences come from the design, not luck.
  - Master seed 20261007, split into separate streams for weather, temperature and load.
- **Statistics to define:**
  - **P10/P90:** 10% of years are below/above this bill.
  - **CVaR95:** average of the worst 5% of outcomes.
  - **P(month > X):** share of months above a bill threshold.
- **If asked "why 2,000?":** the convergence study  shows every statistic is within ±1% at that size.
### Slide 10: Optimization

- **Shows:** cost definition, three objectives, parameter table.
  - **C = annual bill + annualized capex**
  - (1) min E[C]; (2) min E[C] + λ·CVaR95[C]; (3) min E[C] s.t. P(bill > X) ≤ α
- **Key numbers:** sizes 0–6 kWp in 0.5 steps; ₱45,000/kWp (placeholder); 8% discount; 20-year life; λ = 0.5; X = ₱1,000; α = 0.05.
- **Say:** "We test 13 sizes × 2 schedules = 26 designs and pick the best under each objective."
- **If asked "is ₱45,000/kWp real?":** it is a placeholder until we get an installer quote. Sensitivity analysis shows cost barely changes the best size.
---

## Part 3: Results and what the models contributed

### Slide 11: Result 1: annual bill by PV size

- **Shows:** bar chart and table of the mean annual bill from 0 to 6 kWp; 4.5 kWp highlighted.
- **Say:**
  - Each 0.5 kWp saves ₱4,600–9,000/yr up to 4 kWp, then ₱2,500 for the step to 4.5.
  - After 4.5 kWp, each step saves only ₱130–210, because the extra power is exported at the low generation credit.
- **Key numbers:** ₱70,225 (no solar) → ₱18,056 (4.5 kWp); payback 3.9 years; 6 kWp only reaches ₱17,564 with a 5.1-year payback.
### Slide 12: Result 2: recommended design

- **Shows:** **4.5 kWp** with four numbers and the objectives table.
- **Key numbers:** −74%; ₱52,170 saved per year; 3.9-year payback on ₱202,500; +₱1,094/yr from load shifting.
- **Say (RQ2):**
  - Risk-neutral and mean–CVaR both choose 4.5 kWp: **the risk term changes nothing** here.
  - The ₱1,000/month target is **impossible at any size** (P = 0.81 at 4.5 kWp), because night aircon must come from the grid without a battery.
  - Robust range: **3.5–4.5 kWp**, covering a hot September and the other credit rule.
### Slide 13: Result 3: monthly bill with 4.5 kWp

- **Shows:** each month's bill without and with solar, and the reduction; yearly summary.
- **Say:**
  - Every month drops by about three-quarters.
  - September (the real bill): ₱5,739 → ₱1,512 (model estimate).
  - Biggest peso savings in April and May (₱5,700–6,100/month), the hottest months.
  - PV makes 6,699 kWh/yr: 2,053 used at home, 4,647 exported. About 3,625 kWh is still bought, mostly night aircon.
- **Remember:** only September is a real bill; other months are model estimates.
### Slide 14: What the models contributed

- **Shows:** two cards (Markov chain, Monte Carlo) and a table linking each main finding to the model that made it possible.
- **Say:**
  - **Markov chain = realistic weather.** Learned from 24 years of NASA data, one pattern per month. Cloudy days come in runs (habagat, typhoons), so solar stays low for several days at a time; an average misses this. Simulated cloudy-spell lengths match the record (p = 0.76) and monthly bias is within ±0.7%. Treating days as independent makes spells half as long. The same weather sets solar output and temperature, and temperature drives aircon, so supply and demand are linked through the data.
  - **Monte Carlo = the full range of bills.** Every design runs through the same 2,000 simulated years. Because home-used solar saves ₱12.36/kWh but exports earn only about ₱6.30, the average bill ≠ the bill of an average year; only simulation gets it right. It also gives good and bad years (P10/P90, CVaR95) for risk-adjusted sizing, compares sizes fairly, and is stable within ±1% (all 10 batches pick the same size).
- **Findings it made possible:**
  - 4.5 kWp best (robust 3.5–4.5); bill ₱70,225 → ₱18,056/yr (−74%); 3.9-year payback.
  - Beyond 4.5 kWp, only ₱130–210/yr per extra 0.5 kWp (hourly self-use vs export).
  - ₱1,000/month is impossible at any size (P = 0.81) because aircon runs at night.
  - RQ1: persistence changes this bill by under 1%, about 6% for a small no-aircon home. RQ2: the risk term doesn't change the size.
- **One line to remember:** *"The Markov chain makes the weather realistic, and Monte Carlo turns that weather into the full range of possible bills. Together they show 4.5 kWp is the best size and how confident we can be in the savings."*
- **If asked "why not just use average weather?":** with two prices and cloudy runs, the bill is non-linear in the weather, so an average year gives the wrong average bill and no risk range.

---

## Part 4: Limitations and conclusion

### Slide 15: Limitations: model and data

- **Shows:** 9 limitations and their effects.
- **Say:** the most important are:
  - The credit rule is not confirmed, so both rules were run.
  - The tariff is partly derived.
  - The typical usage pattern is assumed.
  - The PV model has no tilt or orientation.
  - The climate is assumed stationary.
  - The installed cost is a placeholder.
- **Tip:** say these confidently. Stating limitations clearly shows you understand the model.
- **If asked "is one month enough?":** enough to demonstrate the method, not for a precise annual forecast. If heat inflated September by 15%, the year is 4,931 kWh and the size is 3.5–4.0 kWp.

### Slide 16: Conclusion

- **Shows:** the answers to RQ1–RQ3.
- **Say:**
  - About **4.5 kWp** cuts the bill by about three-quarters.
  - **RQ1:** under 1% for this household; about 6% for a small no-aircon home.
  - **RQ2:** the risk term agrees with the expected-value size.
  - **RQ3:** consumption sets the size; the credit rule sets the bill cut; the discount rate sets the long-run benefit.
  - Recommended range: **3.5–4.5 kWp**.
- **Next step to mention:** one net-metered INEC bill to settle the credit rule; then another month of bills (ideally April or May) and an installer quote.

### Slide 17: Thank you

- **Say:** invite questions.
- **Good questions to ask the adviser:**
  - Is the generation-only credit rule acceptable as the main case?
  - Is one bill plus the hot-September sensitivity enough for the scope?
  - Should we collect the household's real appliance list?
---

## Backup answers (slides removed from the deck)

| If asked about | Answer |
|---|---|
| Data sources | NASA POWER daily weather 2001–2024 (8,766 days, none missing); INEC 2020 rate structure updated to the 2026 total ₱11.7246/kWh; one real bill (Sep 2026); hourly usage pattern assumed. |
| 2026 generation rate | Not published; solved as ₱6.0848/kWh so the 2020 line structure adds up to the reported 2026 total. |
| Markov parameters | 6 equal-probability kt states, 12 monthly matrices; first-order chain passes the likelihood-ratio test (p = 0.50 dry, 0.64 wet). 8 and 10 states barely helped. |
| PV model | P = kWp · (GHI/1000) · [1 + γ(Tc − 25)] · DERATE; γ = −0.004/°C, NOCT 45 °C, DERATE 0.86; horizontal, no tilt. |
| Temperature | Regression on month and daily kt, AR(1) residual; within 0.1 °C of NASA. Drives aircon and panel losses. |
| Tariff | Rebuilt line by line; scaled ×1.054 to match the bill → ₱12.36/kWh (back-test error 5.1%). |
| Net metering | Hourly netting; exports credited at the generation rate. Main case: credit offsets generation charges only; upper bound: offsets all variable charges. INEC rule not yet confirmed. |
| Validation | Per-month chain passes every test: monthly bias ±0.7%, cloudy-spell lengths match (p = 0.76). Weakness: lag-1 autocorrelation 0.56 vs 0.64. |
| Why 2,000 runs | Convergence study: every statistic within ±1%; all 10 batches pick the same size. |
| RQ1, cloud persistence | Under 1% effect for this aircon household (seasonal and night load dominate); about 6% for a small no-aircon household. |
| RQ3, sensitivity (Sobol) | Optimal size: consumption 0.45, credit rule 0.31, aircon 0.31. Bill cut: credit rule 0.99. 20-yr benefit: discount rate 0.40. |

## Quick answers to common questions

| Question | Short answer |
|---|---|
| Why simulation instead of an average year? | The bill is non-linear: two prices, fixed charges, cloudy runs. The average bill ≠ the bill of average weather. |
| Why no battery? | Scope decision: the question is PV size and bill reduction. |
| Why only Batac, not Laoag? | Same NASA grid cell; the data were identical. |
| Why one bill? | Only record available (slide 5 notes). Used as a calibration anchor. |
| Is the appliance data real? | No. A typical usage pattern is assumed; only the 464 kWh total is real. |
| Why does the bill not reach zero? | Night aircon must be bought from the grid without a battery. |
| Why not a bigger system? | After 4.5 kWp, extra output is exported at the generation rate only; each 0.5 kWp saves ₱130–210/yr. |
| What is the biggest uncertainty? | The net-metering credit rule (Sobol 0.99 for bill cut). |
| How sure is 4.5 kWp? | 4.5 kWp under our assumptions; 3.5–4.5 kWp across a hot September and the other credit rule. |
| Why does slide 5 say ₱1,614 and slide 13 ₱1,512? | Same solar, different tariff split: the bill's own rates vs the model's 2020 line structure. |

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

