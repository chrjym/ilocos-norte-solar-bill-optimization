"""Phases 2–3: kt state binning, MLE transition matrices per season and month,
and first- vs second-order tests. See docs/project_plan.md §4.2–4.4.

Run from the project root:  python3 -m src.estimate_tpm [site] [n_states]
Reads data/raw/nasa_power_daily_<site>.csv, writes data/processed/tpm_<site>.npz
"""
import csv
import sys
from pathlib import Path

import numpy as np
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parents[1]
DRY_MONTHS = {11, 12, 1, 2, 3, 4}


def load_kt(site):
    """Returns (months, kt) as arrays with NaN for missing days."""
    with (ROOT / "data" / "raw" / f"nasa_power_daily_{site}.csv").open() as f:
        rows = list(csv.DictReader(f))
    months = np.array([int(r["date"][5:7]) for r in rows])
    kt = np.array([float(r["ALLSKY_KT"]) if r["ALLSKY_KT"] else np.nan for r in rows])
    return months, kt


def equal_prob_edges(kt, k):
    """Equal-probability bin edges (§4.2), outer edges fixed at 0 and 1."""
    inner = np.nanquantile(kt, np.linspace(0, 1, k + 1)[1:-1])
    return np.r_[0.0, inner, 1.0]


def transitions(states, mask):
    """(prev, next) pairs where both days are valid and `mask` holds for next."""
    a, b = states[:-1], states[1:]
    ok = (a >= 0) & (b >= 0) & mask[1:]
    return a[ok], b[ok]


def count_matrix(a, b, k):
    n = np.zeros((k, k), int)
    np.add.at(n, (a, b), 1)
    return n


def mle(n):
    rows = n.sum(1, keepdims=True)
    return np.divide(n, rows, out=np.full(n.shape, 1 / n.shape[0]), where=rows > 0)


def loglik(n, p):
    nz = n > 0
    return float((n[nz] * np.log(p[nz])).sum())


def order_test(states, mask, k):
    """Order 1 vs 2: likelihood ratio chi-square, AIC, BIC on the same sample."""
    s0, s1, s2 = states[:-2], states[1:-1], states[2:]
    ok = (s0 >= 0) & (s1 >= 0) & (s2 >= 0) & mask[2:]
    s0, s1, s2 = s0[ok], s1[ok], s2[ok]
    n1 = count_matrix(s1, s2, k)
    n2 = np.zeros((k * k, k), int)
    np.add.at(n2, (s0 * k + s1, s2), 1)
    ll1, ll2 = loglik(n1, mle(n1)), loglik(n2, mle(n2))
    # free parameters: only rows actually observed
    p1 = int((n1.sum(1) > 0).sum()) * (k - 1)
    p2 = int((n2.sum(1) > 0).sum()) * (k - 1)
    lr, df, nobs = 2 * (ll2 - ll1), p2 - p1, len(s2)
    return dict(n=nobs, lr=lr, df=df, p=float(chi2.sf(lr, df)),
                aic1=2 * p1 - 2 * ll1, aic2=2 * p2 - 2 * ll2,
                bic1=p1 * np.log(nobs) - 2 * ll1, bic2=p2 * np.log(nobs) - 2 * ll2)


def main(site="batac", k=6):
    months, kt = load_kt(site)
    edges = equal_prob_edges(kt, k)
    states = np.where(np.isnan(kt), -1, np.clip(np.digitize(kt, edges) - 1, 0, k - 1))
    print(f"{site}: {np.isfinite(kt).sum()} valid days, {k} states")
    print("kt bin edges:", np.round(edges, 3))

    out = dict(edges=edges, kt_hist=kt, month_hist=months)
    dry = np.isin(months, list(DRY_MONTHS))
    for season, mask in [("dry", dry), ("wet", ~dry)]:
        n = count_matrix(*transitions(states, mask), k)
        p = mle(n)
        out[f"counts_{season}"], out[f"tpm_{season}"] = n, p
        print(f"\n{season.upper()} season — counts (rows: from-state)")
        print(n)
        print("TPM:")
        print(np.round(p, 3))
        print("persistence P(i→i):", np.round(np.diag(p), 3))
        sparse = np.flatnonzero(n.sum(1) < 30)
        if sparse.size:
            print(f"  WARNING: sparse rows {sparse.tolist()} (<30 obs) — consider fewer states")
        t = order_test(states, mask, k)
        print(f"Order test: LR={t['lr']:.1f}, df={t['df']}, p={t['p']:.3g} | "
              f"AIC 1st {t['aic1']:.0f} vs 2nd {t['aic2']:.0f} | "
              f"BIC 1st {t['bic1']:.0f} vs 2nd {t['bic2']:.0f}")
        best = "1st" if t["bic1"] <= t["bic2"] else "2nd"
        print(f"  → BIC prefers {best} order")

    for m in range(1, 13):
        n = count_matrix(*transitions(states, months == m), k)
        out[f"counts_m{m:02d}"], out[f"tpm_m{m:02d}"] = n, mle(n)

    path = ROOT / "data" / "processed" / f"tpm_{site}.npz"
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, **out)
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "batac",
         int(sys.argv[2]) if len(sys.argv) > 2 else 6)
