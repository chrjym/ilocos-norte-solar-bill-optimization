"""Phase 9: global sensitivity analysis (Sobol indices). See docs/project_plan.md §9.2.

Which uncertain input drives (a) the optimal PV size and (b) the money it saves?

Uncertain inputs (uniform ranges):
  capex_per_kwp        ₱35,000 – 60,000 installed per kWp
  tariff_escalation    0 – 5 %/yr (all per-kWh rates)
  degradation          0.3 – 0.8 %/yr PV output loss
  discount_rate        5 – 12 %/yr
  load_scale           0.7 – 1.4 × the modelled household consumption
  aircon               < 0.5 no aircon, ≥ 0.5 runs a 1 hp aircon at night
  export_credit_mult   0.8 – 1.2 × generation rate (credit-rate uncertainty)
  offset_rule          < 0.5 credit offsets whole bill, ≥ 0.5 generation only

Not varied here: Markov discretization (number of kt states). Its effect is
checked separately in Phase 4 (validate_generator) because each level needs
a refit of the transition matrices.

Outputs, over a 20-year PV life with appliances on the solar schedule:
  opt_kwp        PV size minimising NPV of (capex + bills), 0–6 kWp in 0.5 steps
  npv_benefit    NPV of bill savings − capex at that size (₱)
  bill_cut_pct   first-year bill reduction at that size (%)

Speed: monthly import/export kWh are precomputed once on a grid of
(aircon × load_scale × PV size) on common simulated years, then interpolated,
so each Sobol sample only recomputes bills.

Run from the project root:  python3 -m src.sensitivity [N_base] [reps]
Writes results/sensitivity.txt and results/sensitivity.png
"""
import sys
from pathlib import Path

import numpy as np
from SALib.analyze import sobol
from SALib.sample import sobol as sobol_sample

from .load import shiftable_defaults
from .simulation import generate_scenarios, monthly_flows
from .tariff import monthly_bills

ROOT = Path(__file__).resolve().parents[1]
LIFETIME = 20
CANDIDATES = np.arange(0, 6.01, 0.5)
SCALE_GRID = np.linspace(0.7, 1.4, 8)
SIZE_GRID = np.arange(0, 6.01, 0.25)

PROBLEM = {
    "num_vars": 8,
    "names": ["capex_per_kwp", "tariff_escalation", "degradation", "discount_rate",
              "load_scale", "aircon", "export_credit_mult", "offset_rule"],
    "bounds": [[35_000, 60_000], [0.0, 0.05], [0.003, 0.008], [0.05, 0.12],
               [0.7, 1.4], [0.0, 1.0], [0.8, 1.2], [0.0, 1.0]],
}
OUTPUTS = ["opt_kwp", "npv_benefit", "bill_cut_pct"]


def precompute(reps):
    """imp, exp: (2 aircon, len(SCALE_GRID), len(SIZE_GRID), reps, 12) kWh."""
    shape = (2, len(SCALE_GRID), len(SIZE_GRID), reps, 12)
    imp, exp = np.empty(shape, np.float32), np.empty(shape, np.float32)
    for ac in (0, 1):
        pv1, load = generate_scenarios(reps, aircon=bool(ac))   # same weather for both
        n_days = load.shape[1]
        load = load + (shiftable_defaults(n_days, "solar")
                       - shiftable_defaults(n_days, "default")).astype(np.float32)[None]
        for i, s in enumerate(SCALE_GRID):
            for j, k in enumerate(SIZE_GRID):
                imp[ac, i, j], exp[ac, i, j] = monthly_flows(pv1, s * load, k)
        print(f"  precomputed aircon={bool(ac)}", flush=True)
    return imp, exp


def _interp(grid, x):
    i = np.clip(np.searchsorted(grid, x) - 1, 0, len(grid) - 2)
    w = (x - grid[i]) / (grid[i + 1] - grid[i])
    return i, np.clip(w, 0, 1)


def flows(imp, exp, ac, scale, sizes):
    """Interpolated (len(sizes), reps, 12) import and export kWh."""
    i, wi = _interp(SCALE_GRID, scale)
    j, wj = _interp(SIZE_GRID, np.asarray(sizes))
    def bil(a):
        a0 = a[ac, i] * (1 - wi) + a[ac, i + 1] * wi          # (sizes_grid, reps, 12)
        return (a0[j] * (1 - wj)[:, None, None] + a0[j + 1] * wj[:, None, None])
    return bil(imp), bil(exp)


def model(x, imp, exp):
    capex, esc, deg, r, scale, ac, cmult, off = x
    ac = int(ac >= 0.5)
    offset = "generation" if off >= 0.5 else "bill"
    years = np.arange(LIFETIME)
    disc = (1 + r) ** -(years + 1)
    tariff = (1 + esc) ** years
    reps = imp.shape[3]

    npv_bills, first_year = [], []
    for k in CANDIDATES:
        eff = k * (1 - deg) ** years                     # degraded size each year
        im, ex = flows(imp, exp, ac, scale, eff)          # (years, reps, 12)
        sc = np.repeat(tariff, reps)[:, None]
        bills = monthly_bills(im.reshape(-1, 12), ex.reshape(-1, 12), sc, offset, cmult)
        annual = bills.sum(1).reshape(LIFETIME, reps).mean(1)
        npv_bills.append((annual * disc).sum())
        first_year.append(annual[0])
    npv_bills, first_year = np.array(npv_bills), np.array(first_year)
    total = npv_bills + capex * CANDIDATES
    b = int(np.argmin(total))
    return (CANDIDATES[b], npv_bills[0] - total[b],
            100 * (1 - first_year[b] / first_year[0]))


def main(n_base=512, reps=200):
    print(f"Precomputing energy flows on {reps} common simulated years...")
    imp, exp = precompute(reps)
    X = sobol_sample.sample(PROBLEM, n_base, calc_second_order=False, seed=7)
    print(f"Evaluating {len(X)} Sobol samples...")
    Y = np.array([model(x, imp, exp) for x in X])

    lines = [f"Sobol analysis: N_base={n_base}, {len(X)} model runs, {reps} simulated "
             f"years per run, {LIFETIME}-yr life, solar-hours schedule, no battery\n"]
    for o, name in enumerate(OUTPUTS):
        y = Y[:, o]
        lines.append(f"{name}: mean {y.mean():,.2f}, P5 {np.quantile(y, .05):,.2f}, "
                     f"P95 {np.quantile(y, .95):,.2f}")
        if y.std() == 0:
            lines.append("  (constant — no variance to apportion)\n")
            continue
        si = sobol.analyze(PROBLEM, y, calc_second_order=False, seed=7)
        order = np.argsort(-si["ST"])
        lines.append(f"  {'input':20} {'S1':>6} {'±':>5} {'ST':>6} {'±':>5}")
        for i in order:
            lines.append(f"  {PROBLEM['names'][i]:20} {si['S1'][i]:6.3f} {si['S1_conf'][i]:5.3f} "
                         f"{si['ST'][i]:6.3f} {si['ST_conf'][i]:5.3f}")
        lines.append(f"  sum S1 = {si['S1'].sum():.2f} (1 − sum S1 ≈ share from interactions)\n")
        if o == 0:
            ks, counts = np.unique(y, return_counts=True)
            lines.append("  optimal size distribution: " + ", ".join(
                f"{k:.1f} kWp {100 * c / len(y):.0f}%" for k, c in zip(ks, counts)) + "\n")
        globals().setdefault("_si", {})[name] = si

    text = "\n".join(lines)
    print(text)
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "sensitivity.txt").write_text(text + "\n")
    np.savez(out / "sensitivity_samples.npz", X=X, Y=Y, names=PROBLEM["names"])

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.5))
    yl = np.arange(PROBLEM["num_vars"])
    for o, name in enumerate(OUTPUTS):
        si = _si.get(name) if "_si" in globals() else None
        if si is None:
            continue
        ax[o].barh(yl - 0.2, si["S1"], 0.4, xerr=si["S1_conf"], label="first-order S1")
        ax[o].barh(yl + 0.2, si["ST"], 0.4, xerr=si["ST_conf"], label="total-order ST")
        ax[o].set(yticks=yl, yticklabels=PROBLEM["names"] if o == 0 else [], title=name, xlim=(0, 1))
        ax[o].invert_yaxis()
        ax[o].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "sensitivity.png", dpi=150)
    print(f"Wrote {out / 'sensitivity.png'}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 512,
         int(sys.argv[2]) if len(sys.argv) > 2 else 200)
