"""Research question 1 on the calibrated household: what does ignoring
day-to-day cloud persistence do to the bill distribution?

Same household calibration as src.household (one bill + month, or 12 bills).
Markov scenarios vs i.i.d.-day scenarios, both calibrated to the same monthly
kWh, compared at several PV sizes.

Run from the project root:
  python3 -m src.persistence --kwh 464 --pesos 5739.45 --month 9 --aircon --offset generation
Writes results/persistence.txt
"""

import argparse
from pathlib import Path

import numpy as np

from .household import calibrate_load, household_inputs
from .simulation import bills_for_size, cvar, generate_scenarios

RESULTS = Path(__file__).resolve().parents[1] / "results"


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--kwh", type=float, nargs="+", required=True)
    p.add_argument("--pesos", type=float, nargs="+")
    p.add_argument("--month", type=int, choices=range(1, 13), metavar="1-12")
    p.add_argument("--aircon", action="store_true")
    p.add_argument("--offset", choices=["bill", "generation"], default="generation")
    p.add_argument("--reps", type=int, default=2000)
    p.add_argument("--sizes", type=float, nargs="+", default=[1.0, 2.0, 3.0, 4.5])
    a = p.parse_args()

    pv_mk, load_mk = generate_scenarios(a.reps, aircon=a.aircon)
    pv_iid, load_iid = generate_scenarios(a.reps, iid=True, aircon=a.aircon)
    kwh, scale = household_inputs(load_mk, a.kwh, a.pesos, a.month)
    load_mk, load_iid = calibrate_load(load_mk, kwh), calibrate_load(load_iid, kwh)

    lines = [f"Household: {kwh.sum():,.0f} kWh/yr, aircon={a.aircon}, offset={a.offset}, "
             f"tariff ×{scale:.3f}, N={a.reps} simulated years per generator", ""]
    for kwp in a.sizes:
        lines.append(f"{kwp} kWp")
        stats = {}
        for name, pv, load in [("Markov", pv_mk, load_mk), ("i.i.d.", pv_iid, load_iid)]:
            b = bills_for_size(pv, load, kwp, scale, a.offset)
            m = b.ravel()
            stats[name] = (m.mean(), m.std(), np.quantile(m, .9), cvar(m), b.sum(1).mean())
            lines.append(f"  {name:7} monthly mean {stats[name][0]:7,.0f}  std {stats[name][1]:6,.0f}  "
                         f"P90 {stats[name][2]:7,.0f}  CVaR95 {stats[name][3]:7,.0f}  "
                         f"annual mean {stats[name][4]:8,.0f}")
        mk, iid = stats["Markov"], stats["i.i.d."]
        lines.append(f"  i.i.d. vs Markov: mean {iid[0] / mk[0] - 1:+.1%}, std {iid[1] / mk[1] - 1:+.1%}, "
                     f"CVaR95 {iid[3] / mk[3] - 1:+.1%}")
    text = "\n".join(lines) + "\n"
    print(text)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "persistence.txt").write_text(text)


if __name__ == "__main__":
    main()
