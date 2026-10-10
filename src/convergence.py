"""Phase 7: Monte Carlo convergence study and CRN effectiveness.
See docs/project_plan.md §7.1–7.2.

Scenarios are generated in reproducible batches (src.simulation.streams), so
N can grow without holding every hourly array in memory, and any batch can be
regenerated exactly.

Reports, per PV size:
  * running mean annual bill with 95% CI vs N (convergence plot)
  * CVaR95 of annual cost with bootstrap CI at checkpoints
  * N required for the 95% CI half-width to fall below a tolerance
  * CRN variance reduction for size comparisons: Var(A−B) under common
    random numbers vs Var(A)+Var(B) under independent streams

Run from the project root:  python3 -m src.convergence [n_total] [batch]
Writes results/convergence.txt and results/convergence.png
"""
import sys
from pathlib import Path

import numpy as np

from .optimization import annualized_capex
from .simulation import bills_for_size, cvar, generate_scenarios

ROOT = Path(__file__).resolve().parents[1]
SIZES = [0, 1, 2, 3]
TOL_MEAN = 0.005    # 95% CI half-width ≤ 0.5% of the mean annual bill
TOL_CVAR = 0.01     # bootstrap 95% CI half-width ≤ 1% of CVaR95


def simulate(n_total, batch_size):
    """Annual bill (n_total, len(SIZES)) and worst-month bill, batch by batch."""
    annual, worst = [], []
    for b in range(int(np.ceil(n_total / batch_size))):
        n = min(batch_size, n_total - b * batch_size)
        pv1, load = generate_scenarios(n, batch=b)
        bills = [bills_for_size(pv1, load, k) for k in SIZES]
        annual.append(np.stack([x.sum(1) for x in bills], 1))
        worst.append(np.stack([x.max(1) for x in bills], 1))
        print(f"  batch {b + 1}: {sum(len(a) for a in annual)}/{n_total}", flush=True)
    return np.concatenate(annual), np.concatenate(worst)


def bootstrap_ci(x, stat, n_boot=500, seed=0):
    rng = np.random.default_rng(seed)
    s = np.array([stat(x[rng.integers(0, len(x), len(x))]) for _ in range(n_boot)])
    return np.quantile(s, [0.025, 0.975])


def main(n_total=5000, batch_size=500):
    print(f"Simulating {n_total} years in batches of {batch_size}...")
    annual, worst = simulate(n_total, batch_size)
    cost = annual + np.array([annualized_capex(k) for k in SIZES])[None, :]
    n = np.arange(1, n_total + 1)[:, None]
    run_mean = np.cumsum(annual, 0) / n
    run_sd = np.sqrt(np.maximum(np.cumsum(annual ** 2, 0) / n - run_mean ** 2, 0))
    half = 1.96 * run_sd / np.sqrt(n)

    lines = [f"N = {n_total} simulated years (batches of {batch_size}, seed scheme "
             f"SeedSequence → batch → weather/temperature/load)\n",
             "Annual bill: mean, 95% CI half-width at N, N required for ≤"
             f"{100 * TOL_MEAN:.1f}% of mean"]
    for j, k in enumerate(SIZES):
        m, sd = annual[:, j].mean(), annual[:, j].std(ddof=1)
        rel = half[-1, j] / m if m > 0 else 0
        need = int(np.ceil((1.96 * sd / (TOL_MEAN * m)) ** 2)) if m > 0 else 1
        lines.append(f"  {k} kWp: ₱{m:,.0f} ± {half[-1, j]:,.0f} ({100 * rel:.2f}%), "
                     f"sd ₱{sd:,.0f} → N ≥ {need:,}")

    lines.append(f"\nCVaR95 of annual cost (bill + annualized capex), bootstrap 95% CI; "
                 f"target half-width ≤ {100 * TOL_CVAR:.0f}%")
    checkpoints = [n_ for n_ in (500, 1000, 2000, 5000, 10000) if n_ <= n_total]
    cvar_track = {k: [] for k in SIZES}
    for j, k in enumerate(SIZES):
        parts = []
        for c in checkpoints:
            v = cvar(cost[:c, j])
            lo, hi = bootstrap_ci(cost[:c, j], cvar)
            cvar_track[k].append((c, v, lo, hi))
            parts.append(f"N={c}: {v:,.0f} [{lo:,.0f}, {hi:,.0f}] "
                         f"(±{100 * (hi - lo) / 2 / v:.2f}%)")
        lines.append(f"  {k} kWp: " + "; ".join(parts))

    lines.append("\nP90 of the worst monthly bill in a year, bootstrap 95% CI")
    p90 = lambda x: np.quantile(x, 0.9)
    for j, k in enumerate(SIZES[:3]):
        parts = []
        for c in checkpoints:
            v = p90(worst[:c, j])
            lo, hi = bootstrap_ci(worst[:c, j], p90)
            parts.append(f"N={c}: ₱{v:,.0f} [{lo:,.0f}, {hi:,.0f}] (±{100 * (hi - lo) / 2 / max(v, 1):.1f}%)")
        lines.append(f"  {k} kWp: " + "; ".join(parts))

    lines.append("\nCRN effectiveness for size comparisons (annual bill differences):")
    for a, b in [(0, 1), (1, 2), (2, 3)]:
        ia, ib = SIZES.index(a), SIZES.index(b)
        d = annual[:, ia] - annual[:, ib]
        v_crn = d.var(ddof=1)
        v_ind = annual[:, ia].var(ddof=1) + annual[:, ib].var(ddof=1)
        ratio = v_ind / v_crn if v_crn > 0 else np.inf
        lines.append(f"  {a} vs {b} kWp: Δ = ₱{d.mean():,.0f}; SE with CRN ₱{np.sqrt(v_crn / n_total):,.1f}"
                     f", independent ₱{np.sqrt(v_ind / n_total):,.1f} → variance reduced "
                     f"×{ratio:,.1f}")

    lines.append("\nCRN check: optimum ranking (min mean annual cost) by batch:")
    n_b = int(np.ceil(n_total / batch_size))
    winners = [SIZES[int(np.argmin(cost[i * batch_size:(i + 1) * batch_size].mean(0)))]
               for i in range(n_b)]
    lines.append(f"  {winners} → same optimum in {winners.count(max(set(winners), key=winners.count))}"
                 f"/{n_b} batches")

    text = "\n".join(lines)
    print("\n" + text)
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "convergence.txt").write_text(text + "\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    for j, k in enumerate(SIZES[:3]):
        rel = run_mean[:, j] / run_mean[-1, j] - 1 if run_mean[-1, j] > 0 else run_mean[:, j] * 0
        relh = half[:, j] / run_mean[-1, j] if run_mean[-1, j] > 0 else half[:, j] * 0
        ax[0].plot(n[:, 0], 100 * rel, label=f"{k} kWp", color=f"C{j}")
        ax[0].fill_between(n[:, 0], 100 * (rel - relh), 100 * (rel + relh), color=f"C{j}", alpha=.15)
    ax[0].axhline(0, color="k", lw=.5)
    ax[0].set(title="Running mean annual bill (95% CI)", xlabel="N simulated years",
              ylabel="% deviation from final mean", xscale="log", ylim=(-5, 5))
    ax[0].legend()
    for j, k in enumerate(SIZES[:3]):
        c, v, lo, hi = map(np.array, zip(*cvar_track[k]))
        ax[1].errorbar(c, 100 * (v / v[-1] - 1), yerr=[100 * (v - lo) / v[-1], 100 * (hi - v) / v[-1]],
                       marker="o", capsize=3, label=f"{k} kWp", color=f"C{j}")
    ax[1].axhline(0, color="k", lw=.5)
    ax[1].set(title="CVaR95 of annual cost (bootstrap 95% CI)", xlabel="N", xscale="log",
              ylabel="% deviation from final")
    ax[1].legend()
    d = annual[:, 0] - annual[:, 1]
    rm = np.cumsum(d) / n[:, 0]
    se_crn = d.std(ddof=1) / np.sqrt(n[:, 0])
    se_ind = np.sqrt(annual[:, 0].var(ddof=1) + annual[:, 1].var(ddof=1)) / np.sqrt(n[:, 0])
    ax[2].plot(n[:, 0], rm, color="C0", label="Δ bill, 0 vs 1 kWp (running)")
    ax[2].fill_between(n[:, 0], rm - 1.96 * se_crn, rm + 1.96 * se_crn, alpha=.3, label="95% CI, CRN")
    ax[2].fill_between(n[:, 0], rm - 1.96 * se_ind, rm + 1.96 * se_ind, alpha=.15, color="C3",
                       label="95% CI, independent streams")
    ax[2].set(title="Savings estimate: CRN vs independent", xlabel="N", xscale="log", ylabel="₱/yr")
    ax[2].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "convergence.png", dpi=150)
    print(f"\nWrote {out / 'convergence.png'}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5000,
         int(sys.argv[2]) if len(sys.argv) > 2 else 500)
