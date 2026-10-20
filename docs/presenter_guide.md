# Presenter Guide

A slide-by-slide guide to the adviser presentation, **"Stochastic Optimization of Household Electricity Bills Under Solar Variability"** (22 slides).

Each slide has four parts:

- **Shows:** what is on the slide.
- **Say:** the main points to explain, in plain words.
- **Key numbers:** figures to remember.
- **If asked:** likely adviser questions, with answers.

Deck link: https://claude.ai/artifact/YEoHBdjqx5wr4AERecPu65 (share it from the deck's Share menu before the meeting).

The deck was trimmed from 34 to 17 slides, then a formula-basis slide (11), two verification and validation slides (18–19) and two bill-with-solar slides (13–14, September and October) were added. Detail that was removed (data sources, PV and temperature models, tariff, net metering, validation, convergence, persistence and sensitivity) is kept under **Backup answers** below, so you can still answer questions on it.

---

## Suggested split and timing

About 25–27 minutes plus questions. One way to divide it among presenters:

| Part | Slides | Topic                                                             | Time  |
| ---- | ------ | ----------------------------------------------------------------- | ----- |
| 1    | 1–5    | Introduction, scope, the bills                                    | 5 min |
| 2    | 6–11   | The model and the basis of its formulas                           | 7 min |
| 3    | 12–19  | Results, the bills with solar, models, verification and validation | 11 min |
| 4    | 20–22  | Limitations, conclusion                                           | 3 min |

---

## The one-minute story

If you remember nothing else:

1. A Batac household pays **₱5,739.45** for **464 kWh** in September 2026 and **₱6,295.52** for **509 kWh** in October 2026 (**₱12.36/kWh**).
2. We simulate **2,000 possible weather years** instead of one average year, because the bill under net metering depends on the *sequence* of sunny and cloudy days.
3. The best rooftop solar size, **without a battery**, is **4.5 kWp**, or **5.0 kWp** if you also want to protect against bad months.
4. 4.5 kWp cuts the yearly bill from **₱76,534 to ₱21,287 (−72%)**, saving **₱55,247 a year**, with a **3.7-year payback**.
5. Bigger systems barely help, because exported power earns only the generation rate.
6. The main uncertainty is the **net-metering credit rule**, and we have **only two months of bills**.

---

## Part 1: Introduction, scope and the bill

### Slide 1: Title

- **Shows:** project title, presenters, adviser, date, and "4.5 kWp" on the right.
- **Say:** "We sized rooftop solar for one Batac City household and estimated how much it cuts the INEC bill, using simulation instead of an average-year calculation. Our answer is 4.5 kWp, or 5.0 kWp for a household that wants to avoid bad months."
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
- **Say:** read the research questions aloud. RQ2 is answered on slide 15; all three are answered on slide 21 (Conclusion).
  - **RQ1:** Does ignoring cloud persistence bias the bill?
  -In real life, cloudy days often come in runs: a rainy week, or a stretch of typhoon weather. If the model treats every day as random and unrelated to the day before, it may guess the electricity bill too low or too high.
  - **RQ2:** Does adding a risk term change the best size?
  -Does the best system size change if we care about bad months as well as the average month?
  -Picking a system just to get the lowest average bill ignores the risk of a really expensive month. Here we add a penalty for that risk and see whether the recommended number of panels changes.
  - **RQ3:** Which uncertain input matters most?
  -Weather, electricity rates, household usage, and panel performance are all uncertain. This question asks which one moves the bill the most, which tells you where to focus.
### Slide 4: Study site and scope
Where the study takes place (Site)

- Location: Batac City, Ilocos Norte. The coordinates (18.055°N, 120.566°E) give the exact spot on the map.
- Weather pattern: PAGASA classes the area as Climate Type I, meaning it has two clear seasons:
  - Dry season, November to April: sunny, so solar panels make more electricity.
  - Wet season, May to October: cloudy and rainy, so the panels make less.
- Electric company: INEC (Ilocos Norte Electric Cooperative). The study uses its rates and its net-metering rules, which set how much you're credited when your panels send extra power to the grid.
- Weather data: The sunlight data comes from NASA, which splits the Earth into grid squares. The study uses the square that covers Batac City.

What the study does not cover (Delimitations)

These are the limits the study sets for itself on purpose:

- Rooftop solar connected to the grid only, with no battery. Extra power goes to the grid instead of being stored.
- A simple way of turning daily sunlight into hourly sunlight. The study uses a basic method rather than TAG, which is more complex.
- A standard, simplified panel model (PVWatts-style). It works from sunlight measured on a flat surface instead of modelling every detail of tilted panels.
- No special discounts. The lifeline discount for low-use households and the senior-citizen discount are left out.
- Household electricity use is based on two bills, September and October 2026. Those two months are used to estimate how much the household uses all year.

### Slide 5: The household bills, September and October 2026

- **Shows:** the two real INEC bills side by side, September (left) and October (right). The top row of each table is the **demand** (kWh used, from the meter readings); below it, 9 charge groups with **₱/kWh** and **Now** (no solar).
- **Say:**
  - **Demand:** September meter 856 → 1,320 = **464 kWh**; October meter 1,320 → 1,829 = **509 kWh**. October used **45 kWh (10%) more**.
  - **Bill:** September **₱5,739.45**, October **₱6,295.52**. Both work out to about **₱12.36/kWh** all-in.
  - Generation is more than half of each bill (₱2,925 and ₱3,285).
  - Some rates changed between the two months: generation went up (₱6.30 → ₱6.45/kWh), ancillary service went down (₱1.17 → ₱1.01), system loss went up (₱0.71 → ₱0.78).
  - **Bottom line of the slide:** each charge = ₱/kWh × demand; total = sum + ₱5 metering ≈ **₱12.3574 × kWh + ₱5**. September: 12.3574 × 464 + 5 = ₱5,738.83; October: 12.3574 × 509 + 5 = ₱6,294.92. The full line-by-line table is in the "how is each total calculated?" answer below.
  - These two bills are the real data the model is calibrated to. What solar does to each bill is shown after the results, on slides 13 and 14.
- **If asked "why does the model need the demand?":** the demand sets how much electricity the simulated household uses. The model scales its seasonal pattern so September and October match 464 and 509 kWh (6,188 kWh a year); see slide 8.
- **If asked "how is each total calculated?":** each charge = its rate × the demand; the ₱5 metering charge is added once. Shortcut: **total ≈ ₱12.3574 × kWh + ₱5**.

  | Charge group | September (464 kWh) | October (509 kWh) |
  |---|---|---|
  | Generation | 6.3031 × 464 = 2,924.64 | 6.4539 × 509 = 3,285.04 |
  | Ancillary service | 1.1683 × 464 = 542.09 | 1.0115 × 509 = 514.85 |
  | Distribution, metering | 1.3194 × 464 + 5.00 = 617.20 | 1.3194 × 509 + 5.00 = 676.57 |
  | VAT (5 lines) | 1.2137 × 464 = 563.16 | 1.1623 × 509 = 591.62 |
  | System loss | 0.7118 × 464 = 330.28 | 0.7782 × 509 = 396.10 |
  | Universal charges | 0.6575 × 464 = 305.08 | 0.6575 × 509 = 334.67 |
  | Transmission | 0.5562 × 464 = 258.08 | 0.5483 × 509 = 279.08 |
  | RFSC capex | 0.4171 × 464 = 193.53 | 0.4171 × 509 = 212.30 |
  | Subsidies | 0.0103 × 464 = 4.78 | 0.0104 × 509 = 5.29 |
  | **Total** | **₱5,738.83** (bill: ₱5,739.45) | **₱6,295.52** (bill: ₱6,295.52) |
  | Shortcut | 12.3574 × 464 + 5 = ₱5,738.83 | 12.3574 × 509 + 5 = ₱6,294.92 |

  The small differences (₱0.62 and ₱0.60) come from INEC rounding each printed line to the centavo; the slide rounds to whole pesos (₱5,740 and ₱6,296).
- **If asked "why only two bills?":** they are the only records available (each slip shows only the current month, and earlier slips were not kept). September and October are **calibration anchors**: they fix the consumption level and real rate, and the other months come from the model. October (509 kWh) used even more than September (464 kWh), so September was not an unusually high month for this household. Full answer below.

#### Full answer: why two bills are used

Use this if the panel presses on the data. The short answer is in the "why only two bills?" note above.

**What the two bills give the simulation**

- **Usage level.** 464 kWh (Sep) + 509 kWh (Oct) = 973 kWh. The model's seasonal pattern is scaled to this total, giving 6,188 kWh/yr; September and October keep their real values.
- **Real price.** Both bills give ₱12.36/kWh all-in. The model's tariff (₱11.72) is 5.1% low, so all rates are raised ×1.054 and both bills are matched exactly.
- **A check of the model.** Hide one bill and predict it from the other: October from September gives 430 kWh vs 509 real (−15%); the mean error both ways is 16.8%.

**Why only two**

1. **They were the only bills available.** The INEC slip shows only the current month, not past months. Older slips were thrown away after payment. The thermal paper fades within months. There was no online usage history, and requesting records from INEC was outside the project's time frame.
2. **They match the data-collection period.** Data were collected in September–October 2026, so these were the two newest complete bills, and the rate is current.
3. **Two are better than one.** The second month balances an unusual first month (October used even more than the "hot" September). It lets the model be tested on a month it did not see. It also confirms the rate is the same on both bills.
4. **The method is built for few bills.** Most households considering solar have only one or two recent bills. The project shows the method still works; the missing months come from the model's seasonal pattern.

**What two bills cannot do (say this honestly)**

- The other 10 months are estimates, not real.
- Both bills are from the rainy season; there is no hot dry-season bill (April–May), when usage is highest.
- Neither bill has solar, so the export-credit rule still cannot be checked.

**One line to say:** *"We used two INEC bills, September and October 2026, because they were the only records available: the bill shows only the current month, and older slips weren't kept. Two bills fix the household's real usage and rate, and they let us test the model on a month it didn't see. The other ten months are estimated by the model."*

**If asked "is two enough?":** enough to show the method works and to size the system, not for an exact yearly forecast. The next step is a dry-season bill, ideally April or May.

---

## Part 2: The model

### Slide 6: Methodology overview

- **Shows:** six boxes: Weather → PV output → Load → INEC bill → Monte Carlo → Optimizer, with the code module for each.
- **Say:** "One simulated weather sequence drives both solar supply and household demand. Temperature affects both panel losses and aircon use, so the link between solar and demand comes from the data. Each simulated year ends as twelve monthly bills."
### Slide 7: Weather model: Markov chain

- **Shows:** two formulas (left) and the four steps of how a day is generated (right).
- **Time:** about 1–1.5 minutes.
- **Say, in order:**
  1. **Why (one sentence):** "To know how much the panels make, we need weather. We can't use an 'average day', because real weather comes in runs: a sunny week, then a cloudy week."
  2. **kt = GHI / H₀ (how clear a day is):** "We turn each day into one number, **kt**, the clearness index. **H₀** is the sunlight at the top of the atmosphere, the most possible. **GHI** is what actually reaches the ground. kt is the **share that gets through**: about 0.7 is a clear sunny day, about 0.2 is a heavy cloudy or rainy day." Dividing by H₀ removes the sun's predictable position, so what is left is **only the weather**.
  3. **p̂ᵢⱼ = nᵢⱼ / Σⱼ nᵢⱼ (learning from the past):** "We sorted every day into **6 weather types**, from very cloudy to very clear. Using 24 years of NASA data for Batac, we **counted** how often each type is followed by each other type. That gives the **chance of tomorrow's weather, given today's**, separately for each month, so July behaves like a rainy month and March like a dry month." Example: if a July day is cloudy, the next day is likely cloudy too; that is how habagat and typhoon spells appear.
  4. **How a day is made (right side):** "(1) Look at today's weather type and the month. (2) **Roll the dice** with the counted chances to pick tomorrow's type. (3) Pick a real kt value from past days of that type and month. (4) Split the day into hours of sunlight. Repeat for 365 days to get one year; we make 2,000 years."
  5. **Key point:** "Because **tomorrow depends on today**, cloudy days come in runs, just like the real record. If each day were picked at random, cloudy spells would be **half as long** as reality."
- **One line to remember:** *"We measure how clear each day is, learn from 24 years how today's weather leads to tomorrow's, and use that to make realistic weather years, with cloudy spells included."*
- **If asked "what is a Markov chain?":** a model where the **next step depends only on the current step**. Here, tomorrow's weather depends only on today's.
- **If asked "is it accurate?":** yes. It matches 24 years of NASA data within 0.8% each month, and cloudy-spell lengths match the record (p = 0.76); see the validation slide (slide 19).
### Slide 8: Household load (Layer 2)

- **Shows:** the goal, three cards (**Who is home**, **Heat drives cooling**, **Bills set the amount**) and one key line. No numbers on the slide.
- **Time:** about 1 minute.
- **Say:**
  - **Goal:** "This layer decides **when** the household uses electricity. Solar only helps in the daytime, but the bill gives only a monthly total, so we need an hour-by-hour picture."
  - **Who is home:** "People are either home and using appliances, or away or asleep. Weekdays and weekends follow different routines."
  - **Heat drives cooling:** "Fans and aircon follow the temperature. Hot nights mean more aircon, and without a battery, solar cannot cover that."
  - **Bills set the amount:** "We scale the pattern so the simulated September and October match the real bills."
- **One line to remember:** *"The model decides when power is used; the bills decide how much."*
- **If asked "is this your real household's pattern?":** no, it is an assumed typical pattern, not a survey. Only the monthly totals come from the real bills.
- **If asked for the details (keep for backup, not on the slide):**
  - Occupancy: home-active or away, 0.8 chance of staying in the same state each hour; home and active about 55–60% of weekday daytime hours and 85% of weekend daytime hours. Bedtime 21:00–23:00, wake 04:00–06:00.
  - Aircon: switched on for the night if it is still at least 26.5 °C at 21:00; runs longer on hotter nights (duty (T − 23)/5, between 0.4 and 1).
  - Shiftable loads (washing, pump, iron) can move to 11:00 on the solar schedule.
  - Calibration: kWhₘ = modelₘ × 973 / (model_Sep + model_Oct), with 973 = 464 + 509 kWh. Result: 6,188 kWh a year, from 350 kWh in January to 736 kWh in May.
### Slide 9: Monte Carlo engine

- **Shows:** three cards (common random numbers, seeding, replications) and a table of the output statistics.
- **Time:** about 1 minute.
- **Main goal:** *to find out what the electricity bill will really be, on average and in bad years, for each solar size, even though the weather is uncertain.* For every size it answers two questions: **"How much will I usually pay?"** and **"How bad can it get?"** With both answers we can pick the size that saves the most and is still safe in bad weather.
- **Main idea:** we don't know next year's weather, so instead of guessing one year we **simulate 2,000 possible years** and look at the whole range of bills. Like rolling dice: one roll tells you little; 2,000 rolls show what usually happens and what can go wrong.
- **Say, card by card:**
  - **Common random numbers:** every solar size is tested on **the same 2,000 weather years**, like runners on the same track. If 4.5 kWp beats 4.0 kWp, it is the better size, not the luckier one.
  - **Seeding:** the random numbers start from a fixed seed (20261007), so **anyone who reruns the model gets the same results**. Weather, temperature and usage have separate streams, so changing one does not disturb the others.
  - **Replications:** we tested up to 5,000 years; results stop changing after about **2,000** (within ±1%), so more would only take longer.
- **Statistics in plain words:**
  - **Mean annual bill:** the average yearly bill over the 2,000 years.
  - **P10 / P90:** a good year and a bad year; 10% of years are cheaper than P10, 10% are dearer than P90.
  - **CVaR95:** the average of the worst 5% of cases: how bad it gets in the worst years.
  - **P(month > X):** the chance a month's bill goes above a limit, e.g. ₱1,000.
- **Why it is needed (if asked "why not one average year?"):**
  1. **Weather differs every year.** One year depends on luck; 2,000 years show what usually happens.
  2. **An average year does not give the average bill.** Solar used at home saves about ₱12.36/kWh, exported solar earns only about ₱6.30. Sunny weeks export at the low price, cloudy weeks buy at the high price, and they don't cancel out evenly. So the average of many bills ≠ the bill of an average-weather year.
  3. **We need the bad cases too.** One average year cannot show the bad years and worst months. Seeing them is why the risk-aware choice is 5.0 kWp instead of 4.5.
- **One line to remember:** *"Monte Carlo tests every solar size on 2,000 possible weather years, so we know the usual bill and the worst case before we choose."*
### Slide 10: Optimization

- **Shows:** the cost formula and three objectives (left), and the parameter table (right).
- **Time:** about 1 minute.
- **Main idea:** test **every possible solar size** and pick the one with the **lowest total cost**. Like shopping: look not only at the price tag (the panels) but also at what you save every month (the bill); the best buy costs least overall.
- **The cost formula: C = annual bill + annualized capex.** Total yearly cost = what you still pay INEC + the yearly share of the solar system's price (the panel price spread over 20 years, like a yearly loan payment). More panels mean a smaller bill but a bigger yearly panel cost; the best size is where the two balance.
- **The three goals:**

  | | Formula | In plain words |
  |---|---|---|
  | (1) | min E[C] | **Lowest average cost:** "save the most money on average." |
  | (2) | min E[C] + λ·CVaR95[C] | **Lowest average cost plus a penalty for bad years:** "save money, but no nasty surprises." |
  | (3) | min E[C] s.t. P(bill > X) ≤ α | **Lowest cost, but the monthly bill must almost never exceed ₱1,000:** "a guaranteed low bill." |

  Results (slide 15): (1) picks **4.5 kWp**; (2) picks **5.0 kWp**, a bit more to protect against bad months; (3) is **impossible** at any size, because night-time aircon always needs grid power without a battery.
- **How we search: 26 designs.** 13 sizes (0, 0.5 … 6 kWp) × 2 schedules (normal habits, or washing, pump and iron moved to 11:00). All 26 are tested on the same 2,000 simulated years and the best is picked for each goal; no guessing.
- **The parameter table in plain words:**

  | Parameter | In plain words |
  |---|---|
  | PV size 0–6 kWp, step 0.5 | The sizes we try |
  | Schedule | Normal habits, or appliances moved to 11:00 |
  | Installed cost ₱45,000/kWp | Panel price (**placeholder** until an installer quote) |
  | Discount rate 8% | Money today is worth more than money later |
  | PV life 20 years | How long the panels last |
  | Risk weight λ = 0.5 | How much goal (2) cares about bad years |
  | Bill threshold ₱1,000 | The "low bill" limit in goal (3) |
  | Risk level α = 0.05 | "Almost never" = at most 5% of months |
  | Export credit: generation only | Exported solar reduces only the generation part of the bill |

- **Say:** "Now we choose the best size. The cost we compare is the **yearly bill plus the yearly share of the panel price**. More panels lower the bill but cost more, so there is a best balance. We use three goals: **lowest average cost**, **lowest cost while avoiding bad years**, and **keeping the bill under ₱1,000 almost every month**. We test **26 designs**, 13 sizes times 2 appliance schedules, on the same 2,000 years, and pick the winner for each goal."
- **One line to remember:** *"We test every size and pick the one with the lowest total cost: bill plus panels, with or without caring about bad years."*
- **If asked "is ₱45,000/kWp real?":** it is a placeholder until we get an installer quote. Sensitivity analysis shows cost barely changes the best size.

### Slide 11: Basis of the formulas

- **Shows:** each formula next to the published source it comes from (report §3.9).
- **Say:** "None of the formulas was invented for this project." The weather chain follows Aguiar et al. (1988), fitted with Anderson & Goodman (1957). Panel output is NREL's PVWatts (Dobos, 2014). The risk measure is CVaR (Rockafellar & Uryasev, 2000). The testing follows Sargent (2013).
- **If asked "why such old sources?":** these are the original papers that define the methods. Recent studies still cite them.

---

## Part 3: Results, what the models contributed, and V&V

### Slide 12: Result 1: annual bill by PV size

- **Shows:** bar chart and table of the mean annual bill from 0 to 6 kWp; 4.5 kWp highlighted.
- **Say:**
  - Each 0.5 kWp saves ₱4,400–9,000/yr up to 4.5 kWp, then ₱1,600 for the step to 5.0.
  - After 5.0 kWp, each step saves only ₱150–175, because the extra power is exported at the low generation credit.
- **Key numbers:** ₱76,534 (no solar) → ₱21,287 (4.5 kWp); payback 3.7 years; 6 kWp only reaches ₱19,351 with a 4.7-year payback.
### Slide 13: The September bill, without and with solar

- **Shows:** the real September bill grouped into 9 charge groups, with columns **₱/kWh / Now / With PV / Reduced**.
- **Say:**
  - Today: **₱5,740** (bill says ₱5,739.45) for 464 kWh.
  - With 4.5 kWp: we buy only **303 kWh** instead of 464, and export **372 kWh**.
  - The export credit cancels the **generation charge and its VAT** completely (₱2,925 → ₱0).
  - The other charges drop only because we buy less power.
  - Result: about **₱1,614**, a reduction of **₱4,126 (−72%)**.
- **If asked "why ₱1,614 here but ₱1,570 on slide 16?":** this slide uses the bill's own rates. The model splits the same total rate using INEC's 2020 line structure, which gives ₱1,570. The difference is the tariff split, not the solar.
- **If asked "why does the generation charge go to zero?":** under the generation-only credit rule, export credit can only offset generation charges and their VAT. 372 kWh exported is worth more than those charges on 303 kWh imported, so they are fully covered, and the extra credit carries forward.

### Slide 14: The October bill, without and with solar

- **Shows:** the same table for the real October bill (reading period 18 Sep–18 Oct 2026), in the same layout as slide 13.
- **Say:**
  - Today: **₱6,296** (bill says ₱6,295.52) for 509 kWh, 45 kWh more than September.
  - With 4.5 kWp: we buy only **330 kWh** instead of 509, and export **349 kWh**.
  - The export credit covers the generation charge and its VAT **except ₱138** (₱3,285 → ₱138), because October buys more and exports less than September.
  - Result: about **₱1,801**, a reduction of **₱4,494 (−71%)**.
- **If asked "why ₱1,801 here but ₱1,851 on slide 16?":** same reason as slide 13: the bill's own rates vs the model's 2020 tariff split.
- **If asked "why is October's VAT lower per kWh?":** the October bill's VAT lines total ₱1.16/kWh vs ₱1.21/kWh in September; both are taken as printed on the bills.
### Slide 15: Result 2: recommended design

- **Shows:** **4.5 kWp** with four numbers and the objectives table.
- **Key numbers:** −72%; ₱55,247 saved per year; 3.7-year payback on ₱202,500; +₱1,282/yr from load shifting.
- **Say (RQ2):**
  - Risk-neutral chooses 4.5 kWp; mean–CVaR chooses **5.0 kWp**: **the risk term adds one step** (0.5 kWp).
  - Why: 5.0 kWp costs about ₱679/yr more on average, but the worst-5% monthly bill drops from ₱3,350 to ₱2,626.
  - The ₱1,000/month target is **impossible at any size** (P = 0.89 at 4.5 kWp), because night aircon must come from the grid without a battery.
  - Recommended range: **4.5–5.0 kWp** (generation-only credit). With a 15% cooler September it is 4.5 kWp under both.
- **If asked "why did RQ2 change?":** with only the September bill, both objectives picked 4.5 kWp. The October bill raised the yearly estimate (5,677 → 6,188 kWh), so the hot months have higher bills and the extra 0.5 kWp is now worth it for a risk-averse household.
### Slide 16: Result 3: monthly bill with 4.5 kWp

- **Shows:** each month's bill without and with solar, and the reduction; yearly summary.
- **Say:**
  - Every month drops by about three-quarters.
  - September (real bill): ₱5,739 → ₱1,570; October (real bill): ₱6,296 → ₱1,851 (model estimates with solar).
  - Biggest peso savings in April and May (₱6,200–6,400/month), the hottest months.
  - PV makes 6,699 kWh/yr: 2,192 used at home, 4,507 exported. About 3,996 kWh is still bought, mostly night aircon.
- **Remember:** only September and October are real bills; other months are model estimates.
### Slide 17: What the models contributed

- **Shows:** two cards (Markov chain, Monte Carlo) and a table linking each main finding to the model that made it possible.
- **Say:**
  - **Markov chain = realistic weather.** Learned from 24 years of NASA data, one pattern per month. Cloudy days come in runs (habagat, typhoons), so solar stays low for several days at a time; an average misses this. Simulated cloudy-spell lengths match the record (p = 0.76) and monthly bias is within ±0.7%. Treating days as independent makes spells half as long. The same weather sets solar output and temperature, and temperature drives aircon, so supply and demand are linked through the data.
  - **Monte Carlo = the full range of bills.** Every design runs through the same 2,000 simulated years. Because home-used solar saves ₱12.36/kWh but exports earn only about ₱6.30, the average bill ≠ the bill of an average year; only simulation gets it right. It also gives good and bad years (P10/P90, CVaR95) for risk-adjusted sizing, compares sizes fairly, and is stable within ±1% (all 10 batches pick the same size).
- **Findings it made possible:**
  - 4.5 kWp best (5.0 if risk-averse); bill ₱76,534 → ₱21,287/yr (−72%); 3.7-year payback.
  - Beyond 5.0 kWp, only ₱150–175/yr per extra 0.5 kWp (hourly self-use vs export).
  - ₱1,000/month is impossible at any size (P = 0.89) because aircon runs at night.
  - RQ1: persistence changes this bill by under 1%, about 6% for a small no-aircon home. RQ2: the risk term adds one step (4.5 → 5.0 kWp).
- **One line to remember:** *"The Markov chain makes the weather realistic, and Monte Carlo turns that weather into the full range of possible bills. Together they show 4.5–5.0 kWp is the best size and how confident we can be in the savings."*
- **If asked "why not just use average weather?":** with two prices and cloudy runs, the bill is non-linear in the weather, so an average year gives the wrong average bill and no risk range.

### Slide 18: Verification: is the model built right?

- **Shows:** table of 20 verification checks by layer (`tests/test_model.py`).
- **Say:**
  - Verification means the code does what the equations say. Each test has a known answer.
  - Examples worked by hand: 100 kWh without solar = 100 × ₱11.7246 + ₱5.67; 1,000 W/m² at 30 °C gives 0.7353 kWh per kWp.
  - Energy balances every month, more PV never raises the bill, and the same seed gives the same result.
  - All 20 pass; run with `.venv/bin/python -m pytest tests -v`.

### Slide 19: Validation: is it the right model?

- **Shows:** model vs real data, with the pass condition for each.
- **Say:**
  - Weather: monthly cloudiness within 0.8% of 24 years of NASA data; persistence 0.565 vs 0.637.
  - The persistence test can fail: independent days score 0.10, so the test means something.
  - PV yield about 1,490 kWh/kWp, typical for Northern Luzon.
  - The published tariff alone is within 5.1% of both real bills (September and October).
  - Seasonal check with the second bill: predicting October from September gives 430 kWh vs 509 real (−15%); the mean error both ways is 16.8%. The model expects October to drop, but this household's use went up.
- **Be honest:** the credit rule is not validated yet (needs a net-metered bill), and the seasonal usage is only roughly right (16.8% error).
- **If asked "verification vs validation?":** verification = built right (code vs equations); validation = right model (output vs reality).

---

## Part 4: Limitations and conclusion

### Slide 20: Limitations: model and data

- **Shows:** 9 limitations and their effects.
- **Say:** the most important are:
  - The credit rule is not confirmed, so both rules were run.
  - The tariff is partly derived.
  - The typical usage pattern is assumed.
  - The PV model has no tilt or orientation.
  - The climate is assumed stationary.
  - The installed cost is a placeholder.
- **Tip:** say these confidently. Stating limitations clearly shows you understand the model.
- **If asked "are two months enough?":** enough to demonstrate the method, not for a precise annual forecast. If heat inflated September by 15%, the year is 5,800 kWh and the size is 4.5 kWp under both objectives.

### Slide 21: Conclusion

- **Shows:** the main answer as the title, three cards answering RQ1–RQ3, and the recommended range in the footer.
- **Time:** about 1–1.5 minutes.
- **1. Main answer (the title):** "Our main answer: **4.5 to 5.0 kWp of rooftop solar, without a battery, cuts this household's electricity bill by about 72 to 74 percent.**" For impact: "That's a yearly bill of about **₱76,500 down to about ₱21,300**, saving around **₱55,000 a year**, with the system paying for itself in under 4 years."
- **2. The three research questions** (read the label, then answer in plain words):
  - **RQ1, does ignoring cloudy spells change the bill?** "**Very little for this household, under 1%.** Most of its bill comes from aircon at night and the hot season, not from a few cloudy days. But for a **small home without aircon**, ignoring cloudy spells would make the worst bills look about **6% better than reality**."
  - **RQ2, does caring about bad months change the best size?** "**Yes, by one step.** For the lowest average cost, 4.5 kWp is best. To also avoid expensive months, **5.0 kWp** is better: it costs about ₱679 more a year, but the worst months drop from about ₱3,350 to ₱2,600. Beyond that, more panels don't help, because the remaining bill is **night-time aircon**, which solar can't cover without a battery."
  - **RQ3, which unknown matters most?** "It depends on the question. **How big a system?** Mostly **how much electricity the household uses**. **How much does the bill drop?** Mostly **INEC's export credit rule**. **How much is it worth over 20 years?** Mostly the **discount rate**, the value of money over time."
- **3. Recommendation (the footer):** "Our recommendation is **4.5 to 5.0 kWp**: 4.5 to save the most on average, or 5.0 for a household that wants to avoid bad months. It is based on the household's **two real INEC bills**, September and October 2026."
- **4. Next steps (if time allows):** a **net-metered bill** to confirm INEC's credit rule, a **dry-season bill** (April or May), and a **real installer quote** for the panels.
- **One line to remember:** *"About 4.5 to 5.0 kWp cuts the bill by three-quarters; cloudy spells barely matter here, caring about bad months adds one step, and household usage and INEC's credit rule matter most."*
- **If asked "why not 6 kWp?":** after 5.0 kWp, extra solar is mostly exported at the low price, so each step saves only about ₱150 a year. Not worth it.
- **If asked "why can't the bill reach zero?":** the aircon runs at night; without a battery, that power always comes from the grid.

### Slide 22: Thank you

- **Say:** invite questions.
- **Good questions to ask the adviser:**
  - Is the generation-only credit rule acceptable as the main case?
  - Are two bills (September and October) enough for the scope?
  - Should we collect the household's real appliance list?
---

## Backup answers (slides removed from the deck)

| If asked about | Answer |
|---|---|
| Data sources | NASA POWER daily weather 2001–2024 (8,766 days, none missing); INEC 2020 rate structure updated to the 2026 total ₱11.7246/kWh; two real bills (Sep and Oct 2026); hourly usage pattern assumed. |
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
| Why two bills? | Only records available (slide 5 notes). Used as calibration anchors. |
| Is the appliance data real? | No. A typical usage pattern is assumed; only the 464 and 509 kWh totals are real. |
| Why does the bill not reach zero? | Night aircon must be bought from the grid without a battery. |
| Why not a bigger system? | After 5.0 kWp, extra output is exported at the generation rate only; each 0.5 kWp saves ₱150–175/yr. |
| What is the biggest uncertainty? | The net-metering credit rule (Sobol 0.99 for bill cut). |
| How sure is 4.5 kWp? | 4.5 kWp expected-cost best, 5.0 kWp risk-averse; 4.5 kWp also if September was 15% heat-inflated. Up to 6 kWp if the credit offsets the whole bill. |
| Why do slides 13/14 say ₱1,614 / ₱1,801 and slide 16 ₱1,570 / ₱1,851? | Same solar, different tariff split: the bill's own rates vs the model's 2020 line structure. |

## Where things are in the repository

| To show | File |
|---|---|
| Full write-up | `docs/project_report.md` |
| What every file does | `docs/repository_guide.md` |
| Household result | `.venv/bin/python -m src.household --kwh 464 509 --pesos 5739.45 6295.52 --month 9 10 --aircon --offset generation` |
| Monthly bill table | `results/monthly_bill.csv` |
| Validation figures | `results/generator_validation.png`, `results/load_validation.png`, `results/convergence.png` |
| Size results | `results/optimization.csv`, `results/optimization.png` |
| Sensitivity | `results/sensitivity.txt`, `results/sensitivity.png` |

