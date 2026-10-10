"""Per-household analysis from a user's own electricity bills.

The user enters monthly kWh (and optionally the ₱ amount) from their INEC
bills. The model is calibrated to that household, then every PV size is
simulated under common random numbers and a recommendation is printed.

Calibration:
  * Load: the simulated hourly load is rescaled month by month so its mean
    monthly kWh equals the user's billed kWh. The hourly shape and the
    temperature/solar coupling of the load model are kept.
  * Tariff: if ₱ amounts are given, all per-kWh rates are scaled so the
    model's all-in ₱/kWh matches the user's bills.
  * One bill only (--month): the other 11 months follow the model's own
    seasonal pattern (temperature-driven fans/aircon), scaled so the billed
    month matches. Less certain than 12 real months — see the printed note.

Examples (run from the project root):
  python3 -m src.household --kwh 180 170 200 230 260 250 220 210 205 200 190 185 \
                           --pesos 2300 2180 2560 2950 3330 3200 2820 2690 2620 2560 2430 2370
  python3 -m src.household --kwh 220 --pesos 2650 --month 9   # ONE bill (September)
  python3 -m src.household --kwh 220 --reps 1000 --budget 200000
"""
import argparse

import numpy as np

from .markov import day_months
from .optimization import CAPEX_PER_KWP, LAMBDA, SIZES_KWP, annualized_capex
from .simulation import bills_for_size, cvar, generate_scenarios
from .tariff import EFFECTIVE, FIXED_PER_MONTH, VAT, effective_rate

MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def expand12(values, name):
    if values is None:
        return None
    if len(values) == 1:
        return np.repeat(float(values[0]), 12)
    if len(values) == 12:
        return np.asarray(values, float)
    raise SystemExit(f"--{name}: give 1 value or 12 values (Jan–Dec), got {len(values)}")


def calibrate_load(load, kwh12):
    """Scale each month of `load` (n_reps, 365, 24) to the user's monthly kWh."""
    months = day_months(load.shape[1])
    out = load.copy()
    for m in range(12):
        days = months == m + 1
        model_mean = load[:, days].sum((1, 2)).mean()
        out[:, days] *= kwh12[m] / model_mean
    return out


def household_inputs(load, kwh_vals, pesos_vals, month=None):
    """Return (kwh12, tariff scale) from 1 or 12 bills.

    One bill with `month`: kWh for other months from the model's seasonal
    shape. One bill without `month`: repeated flat (not recommended).
    """
    if len(kwh_vals) == 1 and month:
        months = day_months(load.shape[1])
        model = np.array([load[:, months == m + 1].sum((1, 2)).mean() for m in range(12)])
        kwh = model * (kwh_vals[0] / model[month - 1])
    else:
        kwh = expand12(kwh_vals, "kwh")
    scale = 1.0
    if pesos_vals:
        billed_kwh = np.asarray(kwh_vals, float)
        n = len(pesos_vals)
        rate = (sum(pesos_vals) - n * FIXED_PER_MONTH * (1 + VAT)) / billed_kwh.sum()
        scale = rate / effective_rate()
    return kwh, scale


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kwh", type=float, nargs="+", required=True,
                    help="billed kWh per month (1 value or 12 values Jan–Dec)")
    ap.add_argument("--pesos", type=float, nargs="+",
                    help="billed ₱ per month, same count as --kwh (optional)")
    ap.add_argument("--reps", type=int, default=2000, help="Monte Carlo years")
    ap.add_argument("--budget", type=float, help="max capital ₱ for the PV system")
    ap.add_argument("--max-kwp", type=float, help="roof / net-metering limit in kWp")
    ap.add_argument("--aircon", action="store_true",
                    help="household runs a 1 hp aircon at night (shapes the hourly profile)")
    ap.add_argument("--offset", choices=["bill", "generation"], default="bill",
                    help="which charges net-metering credits may offset")
    ap.add_argument("--month", type=int, choices=range(1, 13), metavar="1-12",
                    help="with a single bill: which month it is (1=Jan … 12=Dec)")
    a = ap.parse_args()
    if a.pesos and len(a.pesos) != len(a.kwh):
        raise SystemExit("--pesos needs the same number of values as --kwh")

    pv1, load = generate_scenarios(a.reps, aircon=a.aircon)
    kwh, scale = household_inputs(load, a.kwh, a.pesos, a.month)
    pesos = expand12(a.pesos, "pesos") if a.pesos and len(a.pesos) == 12 else None
    if a.pesos:
        print(f"Your all-in rate: ₱{scale * effective_rate():.2f}/kWh "
              f"(model default ₱{effective_rate():.2f}/kWh → rates scaled ×{scale:.3f})")
    else:
        print(f"No ₱ amounts given; using model tariff ₱{effective_rate():.2f}/kWh")
    if len(a.kwh) == 1:
        if a.month:
            print(f"ONE bill ({MONTHS[a.month - 1]}): other months estimated from the model's "
                  "seasonal pattern:\n  " + "  ".join(f"{MONTHS[m]} {kwh[m]:.0f}" for m in range(12)))
        else:
            print("WARNING: one bill without --month → every month assumed equal; "
                  "add --month for a seasonal estimate")
    load = calibrate_load(load, kwh)
    print(f"Calibrated load: {load.sum((1, 2)).mean():,.0f} kWh/yr "
          f"(your bills: {kwh.sum():,.0f} kWh/yr)")

    sizes = [s for s in SIZES_KWP
             if (a.budget is None or s * CAPEX_PER_KWP <= a.budget)
             and (a.max_kwp is None or s <= a.max_kwp)]

    base = bills_for_size(pv1, load, 0, scale, a.offset)
    print("\nModel check, no solar (mean simulated ₱ vs your bill):")
    print("  " + "  ".join(f"{MONTHS[m]} {base[:, m].mean():,.0f}"
                           + (f"/{pesos[m]:,.0f}" if pesos is not None else "")
                           for m in range(12)))

    rows = []
    for kwp in sizes:
        b = bills_for_size(pv1, load, kwp, scale, a.offset)
        annual = b.sum(1)
        cost = annual + annualized_capex(kwp)
        rows.append(dict(kwp=kwp, mean=annual.mean(), p10=np.quantile(annual, .1),
                         p90=np.quantile(annual, .9), worst=np.quantile(b.max(1), .9),
                         save=base.sum(1).mean() - annual.mean(),
                         cost=cost.mean(), cvar=cvar(cost)))

    print(f"\n{'kWp':>4} {'capex ₱':>9} {'bill/yr':>9} {'P10':>8} {'P90':>8} "
          f"{'worst mo':>8} {'saves/yr':>9} {'payback':>7}")
    for r in rows:
        capex = r["kwp"] * CAPEX_PER_KWP
        pb = f"{capex / r['save']:.1f}y" if r["save"] > 0 else "—"
        print(f"{r['kwp']:>4} {capex:>9,.0f} {r['mean']:>9,.0f} {r['p10']:>8,.0f} "
              f"{r['p90']:>8,.0f} {r['worst']:>8,.0f} {r['save']:>9,.0f} {pb:>7}")

    neutral = min(rows, key=lambda r: r["cost"])
    risk = min(rows, key=lambda r: r["cost"] + LAMBDA * r["cvar"])
    print(f"\nRecommended size (lowest expected cost):        {neutral['kwp']} kWp")
    print(f"Recommended size (also guarding bad years):     {risk['kwp']} kWp")
    print(f"NOTE: tariff = INEC {EFFECTIVE}; net-metering offset = '{a.offset}'; "
          "capex is a placeholder. Verify against a current INEC bill.")


if __name__ == "__main__":
    main()
