"""Phase 4: validate the synthetic daily kt generator against the historical
record. See docs/project_plan.md §7.3.

Tests (Markov generator and the i.i.d. ablation, each vs. history):
  * KS test on monthly-mean kt (proxy for monthly energy yield), per season
  * monthly mean bias, Jan–Dec
  * ACF of daily kt, lags 1–10
  * run-length distribution of cloudy spells (consecutive days in the two
    lowest states)

Run from the project root:  python3 -m src.validate_generator [n_reps]
Writes results/generator_validation.txt and results/generator_validation.png
"""
import sys
from pathlib import Path

import numpy as np
from scipy.stats import ks_2samp

from .estimate_tpm import DRY_MONTHS, load_kt
from .markov import KT_EDGES, day_months, sample_kt, simulate_daily_states

ROOT = Path(__file__).resolve().parents[1]
CLOUDY_MAX_STATE = 1   # states 0–1 count as "cloudy"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def historical():
    """Historical daily kt as (n_years, 365), dropping Feb 29."""
    import csv
    with (ROOT / "data" / "raw" / "nasa_power_daily_batac.csv").open() as f:
        rows = [r for r in csv.DictReader(f) if r["date"][5:] != "02-29"]
    kt = np.array([float(r["ALLSKY_KT"]) for r in rows])
    return kt.reshape(-1, 365)


def synthetic(n_reps, seed, iid, resolution, persist=True):
    rng = np.random.default_rng(seed)
    states = simulate_daily_states(rng, n_reps, iid=iid, resolution=resolution)
    return sample_kt(rng, states, resolution, persist=persist and not iid)


def monthly_means(kt):
    months = day_months(kt.shape[1])
    return np.stack([kt[:, months == m].mean(1) for m in range(1, 13)], axis=1)


def acf(kt, max_lag=10):
    x = kt - kt.mean(1, keepdims=True)
    var = (x * x).mean()
    return np.array([(x[:, :-k] * x[:, k:]).mean() / var for k in range(1, max_lag + 1)])


def run_lengths(kt):
    cloudy = np.digitize(kt, KT_EDGES) - 1 <= CLOUDY_MAX_STATE
    runs = []
    for row in cloudy:
        padded = np.r_[False, row, False].astype(int)
        d = np.diff(padded)
        runs.extend((np.flatnonzero(d == -1) - np.flatnonzero(d == 1)).tolist())
    return np.array(runs)


def run_hist(runs, max_len=10):
    h = np.bincount(np.minimum(runs, max_len), minlength=max_len + 1)[1:]
    return h / h.sum()


def main(n_reps=2000, seed=4):
    hist = historical()
    gens = {"mk_mon": synthetic(n_reps, seed, False, "month"),
            "mk_nop": synthetic(n_reps, seed, False, "month", persist=False),
            "mk_sea": synthetic(n_reps, seed, False, "season"),
            "iid": synthetic(n_reps, seed, True, "month")}
    lines = [f"Historical: {hist.shape[0]} years (Batac, NASA POWER). "
             f"Synthetic: {n_reps} years each.\n"]

    mm_h = monthly_means(hist)
    dry = np.array([m + 1 in DRY_MONTHS for m in range(12)])
    lines.append("KS test, monthly-mean kt (stat, p):")
    for name, kt in gens.items():
        mm = monthly_means(kt)
        for season, sel in [("dry", dry), ("wet", ~dry)]:
            r = ks_2samp(mm_h[:, sel].ravel(), mm[:, sel].ravel())
            lines.append(f"  {name:6} {season}: D={r.statistic:.3f}  p={r.pvalue:.3g}")

    lines.append("\nMonthly mean kt bias vs history (%):  mk_mon / mk_sea")
    mm_mon = monthly_means(gens["mk_mon"]).mean(0)
    mm_sea = monthly_means(gens["mk_sea"]).mean(0)
    for m in range(12):
        h = mm_h[:, m].mean()
        lines.append(f"  {MONTHS[m]} hist {h:.3f}  {100 * (mm_mon[m] / h - 1):+5.1f}%  "
                     f"{100 * (mm_sea[m] / h - 1):+5.1f}%")

    lines.append("\nStd of monthly-mean kt (inter-month variability):")
    lines.append(f"  history {mm_h.std(0).mean():.4f}  " + "  ".join(
        f"{n} {monthly_means(k).std(0).mean():.4f}" for n, k in gens.items()))

    a_h = acf(hist)
    lines.append("\nACF of daily kt, lags 1–5:")
    lines.append("  history " + " ".join(f"{v:.3f}" for v in a_h[:5]))
    for n, k in gens.items():
        lines.append(f"  {n:7} " + " ".join(f"{v:.3f}" for v in acf(k)[:5]))

    lines.append("\nCloudy-spell run lengths (states 0–1):")
    r_h = run_lengths(hist)
    lines.append(f"  history mean {r_h.mean():.2f} d, P95 {np.quantile(r_h, .95):.0f} d, "
                 f"max {r_h.max()} d")
    for n, k in gens.items():
        r = run_lengths(k)
        ks = ks_2samp(r_h, r)
        lines.append(f"  {n:7} mean {r.mean():.2f} d, P95 {np.quantile(r, .95):.0f} d, "
                     f"max {r.max()} d | KS D={ks.statistic:.3f} p={ks.pvalue:.3g}")

    text = "\n".join(lines)
    print(text)
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "generator_validation.txt").write_text(text + "\n")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n(matplotlib not installed — skipping figure)")
        return
    fig, ax = plt.subplots(1, 3, figsize=(14, 4))
    styles = {"history": dict(color="black", lw=2), "mk_mon": dict(color="#1f77b4"),
              "mk_sea": dict(color="#2ca02c", ls=":"),
              "mk_nop": dict(color="#9467bd", ls="-."), "iid": dict(color="#d62728", ls="--")}
    series = {"history": hist, **gens}
    for n, k in series.items():
        ax[0].plot(range(1, 13), monthly_means(k).mean(0), label=n, **styles[n])
        ax[1].plot(range(1, 11), acf(k), label=n, **styles[n])
        ax[2].plot(range(1, 11), run_hist(run_lengths(k)), marker="o", label=n, **styles[n])
    ax[0].set(title="Monthly mean kt", xlabel="Month", xticks=range(1, 13))
    ax[1].set(title="ACF of daily kt", xlabel="Lag (days)")
    ax[2].set(title="Cloudy-spell length distribution", xlabel="Run length (days, 10 = 10+)",
              yscale="log")
    for a in ax:
        a.legend()
    fig.tight_layout()
    fig.savefig(out / "generator_validation.png", dpi=150)
    print(f"\nWrote {out / 'generator_validation.png'}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2000)
