"""Month-by-month bill with and without solar for the calibrated household.

Same calibration as src.household. For each month: billed kWh, bill without
solar, PV output, self-consumed and exported kWh, bill with PV (solar
schedule for shiftable loads) and the reduction. Means over the simulated years.

Run from the project root:
  python3 -m src.monthly --kwh 464 --pesos 5739.45 --month 9 --aircon --kwp 4.5
Writes results/monthly_bill.csv and results/monthly_bill.txt
"""

import argparse
from pathlib import Path

import numpy as np

from .household import calibrate_load, household_inputs
from .load import shiftable_defaults
from .markov import day_months
from .simulation import bills_for_size, generate_scenarios, monthly_flows

RESULTS = Path(__file__).resolve().parents[1] / "results"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--kwh", type=float, nargs="+", required=True)
    p.add_argument("--pesos", type=float, nargs="+")
    p.add_argument("--month", type=int, choices=range(1, 13), metavar="1-12")
    p.add_argument("--aircon", action="store_true")
    p.add_argument("--offset", choices=["bill", "generation"], default="generation")
    p.add_argument("--kwp", type=float, default=4.5)
    p.add_argument("--reps", type=int, default=2000)
    a = p.parse_args()

    pv1, load = generate_scenarios(a.reps, aircon=a.aircon)
    kwh, scale = household_inputs(load, a.kwh, a.pesos, a.month)
    load = calibrate_load(load, kwh)
    n_days = load.shape[1]
    delta = (shiftable_defaults(n_days, "solar") - shiftable_defaults(n_days, "default")).astype(np.float32)
    load_solar = load + delta[None]

    base = bills_for_size(pv1, load, 0, scale, a.offset).mean(0)
    with_pv = bills_for_size(pv1, load_solar, a.kwp, scale, a.offset).mean(0)
    imp, exp = (x.mean(0) for x in monthly_flows(pv1, load_solar, a.kwp))
    starts = np.r_[0, np.flatnonzero(np.diff(day_months(n_days))) + 1]
    use = np.add.reduceat(load_solar.sum(2), starts, axis=1).mean(0)
    pv = use - imp + exp
    self_used = pv - exp

    rows = []
    for m in range(12):
        rows.append((MONTHS[m], use[m], base[m], pv[m], self_used[m], exp[m], imp[m],
                     with_pv[m], base[m] - with_pv[m]))
    tot = [sum(r[i] for r in rows) for i in range(1, 9)]

    hdr = ("month,kwh_used,bill_no_solar,pv_kwh,self_used_kwh,exported_kwh,"
           "imported_kwh,bill_with_solar,reduction")
    csv = [hdr] + [f"{r[0]}," + ",".join(f"{v:.1f}" for v in r[1:]) for r in rows]
    csv.append("Year," + ",".join(f"{v:.1f}" for v in tot))
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "monthly_bill.csv").write_text("\n".join(csv) + "\n")

    lines = [f"{a.kwp} kWp, offset={a.offset}, tariff ×{scale:.3f}, mean of {a.reps} simulated years", "",
             f"{'Mon':4} {'kWh':>5} {'no PV ₱':>8} {'PV kWh':>7} {'self':>5} {'export':>6} "
             f"{'import':>6} {'with PV ₱':>9} {'cut ₱':>7} {'cut':>4}"]
    for r in rows + [("Year", *tot)]:
        lines.append(f"{r[0]:4} {r[1]:>5,.0f} {r[2]:>8,.0f} {r[3]:>7,.0f} {r[4]:>5,.0f} {r[5]:>6,.0f} "
                     f"{r[6]:>6,.0f} {r[7]:>9,.0f} {r[8]:>7,.0f} {r[8] / r[2]:>4.0%}")
    text = "\n".join(lines) + "\n"
    print(text)
    (RESULTS / "monthly_bill.txt").write_text(text)


if __name__ == "__main__":
    main()
