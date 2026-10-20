# Ilocos Norte Solar Bill Optimization

**Stochastic Optimization of Household Monthly Electricity Bills Under Solar Variability: A Markov Chain and Monte Carlo Approach in Ilocos Norte, Philippines**

Under net metering (RA 9513) and unbundled tariffs, a household's monthly bill is a
non-linear, path-dependent function of the irradiance sequence, so
`E[bill] ≠ bill(E[irradiance])`. This project simulates the full bill distribution
with a season-conditioned Markov chain of clearness index and Monte Carlo
replications. It then sizes PV (no battery storage) against a
risk-adjusted objective (mean–CVaR or chance-constrained).

Project report: [`docs/project_report.md`](docs/project_report.md) · Plan: [`docs/project_plan.md`](docs/project_plan.md) · Concept: [`docs/study_concept.md`](docs/study_concept.md) · Repository guide: [`docs/repository_guide.md`](docs/repository_guide.md)  · Presenter guide: [`docs/presenter_guide.md`](docs/presenter_guide.md)

## Pipeline

| Layer | Module | Output |
|---|---|---|
| 1. Solar stochastic model | `src/markov.py`, `src/pv.py` | synthetic hourly GHI → PV power |
| 2. Household demand model | `src/load.py` | synthetic hourly load (temperature-coupled) |
| 3. Billing model | `src/tariff.py` | peso bill from net hourly flows (INEC tariff + net metering) |
| 4. Monte Carlo engine | `src/simulation.py` | distribution of monthly bills (common random numbers) |
| 5. Optimization | `src/optimization.py` | optimal design under risk-neutral vs. risk-adjusted objectives |

## Running

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m src.fetch_nasa_power          # data/raw/nasa_power_daily_*.csv
.venv/bin/python -m src.estimate_tpm batac 6      # data/processed/tpm_batac.npz
.venv/bin/python -m src.validate_generator 2000   # Phase 4 checks → results/
.venv/bin/python -m src.temperature               # fitted temperature–kt coupling
.venv/bin/python -m src.validate_load 500         # Phase 5 checks → results/
.venv/bin/python -m src.tariff                    # print the INEC tariff in use
.venv/bin/python -m src.convergence 5000 500      # Phase 7: convergence, CRN → results/
.venv/bin/python -m src.simulation 2000           # size sweep + persistence ablation
.venv/bin/python -m src.optimization --kwh 220 [--pesos 2600] [--aircon]   # Phase 8
.venv/bin/python -m src.household --kwh 464 509 --pesos 5739.45 6295.52 --month 9 10 --aircon --offset generation   # two bills (Sep + Oct 2026)
.venv/bin/python -m src.monthly --kwh 464 509 --pesos 5739.45 6295.52 --month 9 10 --aircon --kwp 4.5   # monthly bill with vs without solar
.venv/bin/python -m src.persistence --kwh 464 509 --pesos 5739.45 6295.52 --month 9 10 --aircon   # cloud persistence, this household
.venv/bin/python -m src.sensitivity 512 200       # Phase 9: Sobol → results/
.venv/bin/python -m src.backtest                  # Phase 10: data/bills/bills.csv vs model
.venv/bin/python -m pytest tests -v               # verification & validation tests
```

## Household data

Two INEC bills are available: **September 2026, 464 kWh, ₱5,739.45** and **October 2026, 509 kWh,
₱6,295.52** (both ₱12.3574/kWh), stored in `data/bills/bills.csv`. Result (generation-only export credit):
**4.5 kWp**, about ₱55,000/yr saved, ~3.7-year payback; **5.0 kWp** if the worst months also matter
(mean–CVaR). See project report §2.1 and §5.3 for why only two months are used and what that limits.

## Layout

```
data/
  raw/            NASA POWER daily weather (Batac); INEC tariff sources
  processed/      fitted Markov transition matrices
  bills/          household bills (bills.csv) + blank template
  appliances.csv  appliance inventory for the hourly load shape
src/              model code (pipeline above)
results/          figures, tables and run logs
docs/             project report, project plan, study concept, repository and presenter guides
```

## Tooling

Python 3.11+, `numpy`, `scipy`, `matplotlib`, `SALib` (see `requirements.txt`).
