"""Phase 5 checks: temperature generator vs NASA POWER, and load model
diagnostics (end-use breakdown, seasonality, solar–load dependence).

Run from the project root:  python3 -m src.validate_load [n_reps]
Writes results/load_validation.txt and results/load_validation.png
"""
import csv
import sys
from pathlib import Path

import numpy as np

from .load import simulate_load
from .markov import day_months, simulate_ghi
from .pv import ac_energy_per_kwp
from .temperature import simulate_ambient

ROOT = Path(__file__).resolve().parents[1]
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def nasa_daily():
    with (ROOT / "data" / "raw" / "nasa_power_daily_batac.csv").open() as f:
        rows = [r for r in csv.DictReader(f) if r["date"][5:] != "02-29"]
    col = lambda k: np.array([float(r[k]) for r in rows]).reshape(-1, 365)
    return col("ALLSKY_KT"), col("T2M"), col("T2M_MAX"), col("T2M_MIN")


def by_month(x):
    m = day_months(x.shape[1])
    return np.array([x[:, m == k].mean() for k in range(1, 13)])


def main(n_reps=500, seed=11):
    rng = np.random.default_rng(seed)
    ghi, kt = simulate_ghi(rng, n_reps)
    tamb = simulate_ambient(rng, kt)
    pv1 = ac_energy_per_kwp(ghi, tamb)
    lines = []

    # --- temperature vs history ------------------------------------------
    kt_h, t_h, tx_h, tn_h = nasa_daily()
    t_s, tx_s, tn_s = tamb.mean(2), tamb.max(2), tamb.min(2)
    lines.append("Temperature, monthly means — NASA / synthetic (°C):")
    lines.append("       Tmean        Tmax         DTR      corr(Tmean,kt)")
    for m in range(12):
        sh = day_months(365) == m + 1
        ch = np.corrcoef(t_h[:, sh].ravel(), kt_h[:, sh].ravel())[0, 1]
        cs = np.corrcoef(t_s[:, sh].ravel(), kt[:, sh].ravel())[0, 1]
        lines.append(
            f"  {MONTHS[m]}  {by_month(t_h)[m]:4.1f}/{by_month(t_s)[m]:4.1f}  "
            f"{by_month(tx_h)[m]:4.1f}/{by_month(tx_s)[m]:4.1f}  "
            f"{by_month(tx_h - tn_h)[m]:4.1f}/{by_month(tx_s - tn_s)[m]:4.1f}  "
            f"{ch:+.2f}/{cs:+.2f}")
    sd_h = (t_h - by_month(t_h)[day_months(365) - 1]).std()
    sd_s = (t_s - by_month(t_s)[day_months(365) - 1]).std()
    lines.append(f"  daily Tmean anomaly std: NASA {sd_h:.2f}  synthetic {sd_s:.2f}")

    # --- load ------------------------------------------------------------
    fig_data = {}
    for aircon in (False, True):
        load, parts = simulate_load(rng, tamb, aircon=aircon, components=True)
        tag = "with aircon" if aircon else "no aircon"
        annual = load.sum((1, 2))
        lines.append(f"\nLoad, {tag}: {annual.mean():,.0f} kWh/yr "
                     f"(P10 {np.quantile(annual, .1):,.0f}, P90 {np.quantile(annual, .9):,.0f}); "
                     f"{annual.mean() / 12:,.0f} kWh/month avg")
        lines.append("  end use: " + ", ".join(
            f"{k} {v:,.0f} ({100 * v / annual.mean():.0f}%)" for k, v in parts.items() if v > 0))
        monthly = np.array([load[:, day_months(365) == m + 1].sum((1, 2)).mean()
                            for m in range(12)])
        lines.append("  kWh/month: " + " ".join(f"{MONTHS[m]} {monthly[m]:.0f}" for m in range(12)))
        day = (np.arange(24) >= 6) & (np.arange(24) < 18)
        lines.append(f"  share of load 06–18h: {100 * load[:, :, day].sum() / load.sum():.0f}%")
        # solar–load dependence, daytime hours, daily totals within month
        dl = load[:, :, day].sum(2)
        dp = pv1[:, :, day].sum(2)
        r = np.mean([np.corrcoef(dl[:, day_months(365) == m + 1].ravel(),
                                 dp[:, day_months(365) == m + 1].ravel())[0, 1]
                     for m in range(12)])
        lines.append(f"  corr(daytime load, PV) within month, daily: {r:+.2f}")
        fig_data[tag] = (load.mean((0, 1)), monthly)

    text = "\n".join(lines)
    print(text)
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "load_validation.txt").write_text(text + "\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(14, 4))
    ax[0].plot(range(1, 13), by_month(t_h), "k-", lw=2, label="NASA Tmean")
    ax[0].plot(range(1, 13), by_month(t_s), "C0--", label="synthetic Tmean")
    ax[0].plot(range(1, 13), by_month(tx_h), "k:", label="NASA Tmax")
    ax[0].plot(range(1, 13), by_month(tx_s), "C0:", label="synthetic Tmax")
    ax[0].set(title="Ambient temperature", xlabel="Month", ylabel="°C", xticks=range(1, 13))
    ax[0].legend(fontsize=8)
    for tag, (hourly, monthly) in fig_data.items():
        ax[1].plot(range(24), hourly, label=tag)
        ax[2].plot(range(1, 13), monthly, marker="o", label=tag)
    ax[1].plot(range(24), pv1.mean((0, 1)), "k--", label="PV per kWp")
    ax[1].set(title="Mean hourly profile", xlabel="Hour", ylabel="kWh")
    ax[2].set(title="Monthly consumption", xlabel="Month", ylabel="kWh", xticks=range(1, 13))
    ax[1].legend(fontsize=8)
    ax[2].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "load_validation.png", dpi=150)
    print(f"\nWrote {out / 'load_validation.png'}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 500)
