"""Layer 5 / Phase 8: how much PV to install, and how much it reduces the bill.
See docs/project_plan.md §8.

SCOPE: no battery storage (project decision). Decision variables:
  * PV size (kWp), on a 0.5 kWp grid
  * shiftable-load schedule: "default" hours vs "solar" (moved into solar
    hours within each appliance's allowed window)

Method: Option B simulation–optimization (§8.4). Every candidate is evaluated
on the same simulated years (common random numbers), N = 2000 per Phase 7.

Objectives (§8.2), on annual cost = annual bill + annualized PV capex:
  (1) risk-neutral        min E[cost]
  (2) mean–CVaR           min E[cost] + λ·CVaR95[cost]
  (3) chance-constrained  min E[cost]  s.t.  P(monthly bill > ₱X) ≤ α

Constraints: capital budget, roof / net-metering kWp ceiling (§8.3).

PLACEHOLDER COSTS: replace CAPEX_PER_KWP with local installed-cost quotes.

Run from the project root:
  python3 -m src.optimization                         # model's default household
  python3 -m src.optimization --kwh 180 170 ... --pesos 2300 ... [--aircon]
      [--threshold 1000 --alpha 0.05 --budget 200000 --max-kwp 5 --offset generation]
Writes results/optimization.csv and results/optimization.png
"""
import argparse
from pathlib import Path

import numpy as np

SIZES_KWP = [float(x) for x in np.arange(0, 6.01, 0.5)]
CAPEX_PER_KWP = 45_000.0   # ₱ installed (PLACEHOLDER)
LIFETIME_YR = 20
DISCOUNT = 0.08
LAMBDA = 0.5               # weight on CVaR95 in the risk-adjusted objective
ROOT = Path(__file__).resolve().parents[1]


def annualized_capex(kwp):
    crf = DISCOUNT / (1 - (1 + DISCOUNT) ** -LIFETIME_YR)
    return kwp * CAPEX_PER_KWP * crf


def optimize(rows):
    """Legacy helper used by src.simulation: rows of per-size summaries."""
    neutral = min(rows, key=lambda r: r["cost_mean"])
    risk = min(rows, key=lambda r: r["cost_mean"] + LAMBDA * r["cost_cvar95"])
    print(f"\nOptimal size, risk-neutral  min E[cost]:                 {neutral['kwp']} kWp")
    print(f"Optimal size, risk-adjusted min E[cost] + {LAMBDA}·CVaR95: {risk['kwp']} kWp")
    return neutral, risk


def evaluate(pv1, load_by_policy, sizes, threshold, scale=1.0, offset=None):
    """Metrics for every (policy, size) on common random numbers."""
    from .simulation import bills_for_size, cvar
    base = bills_for_size(pv1, load_by_policy["default"], 0, scale, offset).sum(1).mean()
    rows = []
    for policy, load in load_by_policy.items():
        for kwp in sizes:
            b = bills_for_size(pv1, load, kwp, scale, offset)
            annual = b.sum(1)
            cost = annual + annualized_capex(kwp)
            capex = kwp * CAPEX_PER_KWP
            save = base - annual.mean()
            rows.append(dict(
                policy=policy, kwp=kwp, capex=capex,
                bill_mean=annual.mean(), bill_p10=np.quantile(annual, .1),
                bill_p90=np.quantile(annual, .9),
                month_p50=np.median(b), month_p90=np.quantile(b, .9), month_cvar95=cvar(b.ravel()),
                p_exceed=float((b > threshold).mean()),
                saving=save, saving_pct=100 * save / base,
                payback=capex / save if kwp > 0 and save > 0 else np.inf,
                cost_mean=cost.mean(), cost_cvar95=cvar(cost)))
    return base, rows


def choose(rows, alpha):
    best = lambda key, pool: min(pool, key=key) if pool else None
    feas = [r for r in rows if r["p_exceed"] <= alpha]
    return {
        "risk-neutral": best(lambda r: r["cost_mean"], rows),
        "mean-CVaR": best(lambda r: r["cost_mean"] + LAMBDA * r["cost_cvar95"], rows),
        "chance-constrained": best(lambda r: r["cost_mean"], feas),
    }


def main():
    from .household import calibrate_load, household_inputs
    from .load import shiftable_defaults
    from .simulation import generate_scenarios

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kwh", type=float, nargs="+", help="billed kWh/month (1 or 12 values)")
    ap.add_argument("--pesos", type=float, nargs="+", help="billed ₱/month (optional)")
    ap.add_argument("--aircon", action="store_true")
    ap.add_argument("--month", type=int, choices=range(1, 13), metavar="1-12",
                    help="with a single bill: which month it is (1=Jan … 12=Dec)")
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--threshold", type=float, default=1000.0, help="₱X for the chance constraint")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--budget", type=float)
    ap.add_argument("--max-kwp", type=float)
    ap.add_argument("--offset", choices=["bill", "generation"], default="bill")
    a = ap.parse_args()

    pv1, load = generate_scenarios(a.reps, aircon=a.aircon)
    scale = 1.0
    if a.kwh:
        kwh, scale = household_inputs(load, a.kwh, a.pesos, a.month)
        load = calibrate_load(load, kwh)
    n_days = load.shape[1]
    delta = (shiftable_defaults(n_days, "solar") - shiftable_defaults(n_days, "default")).astype(np.float32)
    loads = {"default": load, "solar": load + delta[None]}

    sizes = [s for s in SIZES_KWP
             if (a.budget is None or s * CAPEX_PER_KWP <= a.budget)
             and (a.max_kwp is None or s <= a.max_kwp)]
    base, rows = evaluate(pv1, loads, sizes, a.threshold, scale, a.offset)

    print(f"Household: {load.sum((1, 2)).mean():,.0f} kWh/yr, aircon={a.aircon}, "
          f"offset={a.offset}, N={a.reps}")
    print(f"Bill without solar: ₱{base:,.0f}/yr\n")
    print(f"{'sched':7} {'kWp':>4} {'capex':>8} {'bill/yr':>8} {'saves':>8} {'cut':>5} "
          f"{'payback':>7} {'mo P90':>7} {'mo CVaR':>7} {'P(>X)':>6}")
    for r in rows:
        pb = f"{r['payback']:.1f}y" if np.isfinite(r["payback"]) else "—"
        print(f"{r['policy']:7} {r['kwp']:>4.1f} {r['capex']:>8,.0f} {r['bill_mean']:>8,.0f} "
              f"{r['saving']:>8,.0f} {r['saving_pct']:>4.0f}% {pb:>7} {r['month_p90']:>7,.0f} "
              f"{r['month_cvar95']:>7,.0f} {r['p_exceed']:>6.3f}")

    print(f"\nOptimal design (X = ₱{a.threshold:,.0f}/month, α = {a.alpha}, λ = {LAMBDA}):")
    picks = choose(rows, a.alpha)
    for name, r in picks.items():
        if r is None:
            print(f"  {name:19} infeasible within the size range")
            continue
        print(f"  {name:19} {r['kwp']:.1f} kWp, {r['policy']} schedule → bill ₱{r['bill_mean']:,.0f}/yr "
              f"(−{r['saving_pct']:.0f}%, saves ₱{r['saving']:,.0f}/yr), payback "
              f"{r['payback']:.1f} y, P(month > X) {r['p_exceed']:.3f}")
    for kwp in sorted({r["kwp"] for r in picks.values() if r}):
        d = next(r for r in rows if r["policy"] == "default" and r["kwp"] == kwp)
        s = next(r for r in rows if r["policy"] == "solar" and r["kwp"] == kwp)
        print(f"  load shifting at {kwp:.1f} kWp saves an extra ₱{d['bill_mean'] - s['bill_mean']:,.0f}/yr")

    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    keys = list(rows[0])
    (out / "optimization.csv").write_text(",".join(keys) + "\n" + "\n".join(
        ",".join(str(r[k]) if isinstance(r[k], str) else f"{r[k]:.4f}" for k in keys)
        for r in rows) + "\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    for i, pol in enumerate(["default", "solar"]):
        rr = [r for r in rows if r["policy"] == pol]
        k = [r["kwp"] for r in rr]
        ax[0].plot(k, [r["bill_mean"] for r in rr], "o-", color=f"C{i}", label=f"{pol} schedule")
        ax[0].fill_between(k, [r["bill_p10"] for r in rr], [r["bill_p90"] for r in rr],
                           color=f"C{i}", alpha=.15)
        ax[1].plot(k, [r["cost_mean"] for r in rr], "o-", color=f"C{i}", label=f"E[cost], {pol}")
        ax[1].plot(k, [r["cost_mean"] + LAMBDA * r["cost_cvar95"] for r in rr], "--",
                   color=f"C{i}", label=f"E + {LAMBDA}·CVaR95, {pol}")
        ax[2].plot(k, [r["p_exceed"] for r in rr], "o-", color=f"C{i}", label=f"{pol} schedule")
    ax[0].set(title="Annual bill (mean, P10–P90 band)", xlabel="PV size (kWp)", ylabel="₱/yr")
    ax[1].set(title="Annual cost = bill + annualized capex", xlabel="PV size (kWp)", ylabel="₱/yr")
    ax[2].axhline(a.alpha, color="k", ls=":", label=f"α = {a.alpha}")
    ax[2].set(title=f"P(monthly bill > ₱{a.threshold:,.0f})", xlabel="PV size (kWp)")
    for x in ax:
        x.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "optimization.png", dpi=150)
    print(f"\nWrote {out / 'optimization.csv'} and {out / 'optimization.png'}")


if __name__ == "__main__":
    main()
