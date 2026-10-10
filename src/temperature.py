"""Ambient temperature generator, coupled to the solar chain.
See docs/project_plan.md §5.2.

Fitted per calendar month to NASA POWER daily T2M / T2M_MAX / T2M_MIN for
Batac (data/raw/nasa_power_daily_batac.csv):

    Tmean_d = a_m + b_m·(kt_d − k̄t_m) + e_d,   e_d AR(1) with lag-1 φ_m
    DTR_d   = c_m + d_m·(kt_d − k̄t_m) + u_d,   u_d i.i.d. normal, DTR ≥ 1 °C

Hourly shape: minimum at 06:00, maximum at 14:00 (cosine segments).
Because the same daily kt drives PV output and temperature, cooling load and
solar production are correlated structurally, not by assumption.

Limitation: NASA POWER T2M is a ~0.5° grid-cell (MERRA-2) value, typically
cooler than local station records (nearest PAGASA station: Laoag). Bias-correct against PAGASA when
available (§4.7).
"""
import csv
from pathlib import Path

import numpy as np

from .markov import day_months

ROOT = Path(__file__).resolve().parents[1]
_CSV = ROOT / "data" / "raw" / "nasa_power_daily_batac.csv"
T_MIN_HOUR, T_MAX_HOUR = 6, 14


def _fit():
    with _CSV.open() as f:
        rows = list(csv.DictReader(f))
    col = lambda k: np.array([float(r[k]) for r in rows])
    kt, t, tx, tn = col("ALLSKY_KT"), col("T2M"), col("T2M_MAX"), col("T2M_MIN")
    month = np.array([int(r["date"][5:7]) for r in rows])
    p = {k: np.zeros(12) for k in "kt_bar a b phi sd_e c d sd_u".split()}
    for m in range(1, 13):
        s = month == m
        x = kt[s] - kt[s].mean()
        b, a = np.polyfit(x, t[s], 1)
        e = t[s] - (a + b * x)
        phi = np.corrcoef(e[:-1], e[1:])[0, 1]   # month blocks join across years; negligible
        d, c = np.polyfit(x, tx[s] - tn[s], 1)
        u = (tx[s] - tn[s]) - (c + d * x)
        for k, v in dict(kt_bar=kt[s].mean(), a=a, b=b, phi=phi, sd_e=e.std(),
                         c=c, d=d, sd_u=u.std()).items():
            p[k][m - 1] = v
    return p


PARAMS = _fit() if _CSV.exists() else None


def _hour_shape():
    """Fraction of the daily range above Tmin, per hour (0 at 06:00, 1 at 14:00)."""
    h = np.arange(24) + 0.5
    rise = (h >= T_MIN_HOUR) & (h <= T_MAX_HOUR)
    s = np.empty(24)
    s[rise] = 0.5 - 0.5 * np.cos(np.pi * (h[rise] - T_MIN_HOUR) / (T_MAX_HOUR - T_MIN_HOUR))
    fall_len = 24 - (T_MAX_HOUR - T_MIN_HOUR)
    since_max = (h[~rise] - T_MAX_HOUR) % 24
    s[~rise] = 0.5 + 0.5 * np.cos(np.pi * since_max / fall_len)
    return s


SHAPE = _hour_shape()


def simulate_ambient(rng, kt_day):
    """Hourly ambient temperature °C, shape (n_reps, n_days, 24)."""
    if PARAMS is None:
        raise FileNotFoundError(f"{_CSV} missing — run src.fetch_nasa_power")
    n_reps, n_days = kt_day.shape
    mi = day_months(n_days) - 1
    p = {k: v[mi][None, :] for k, v in PARAMS.items()}
    x = kt_day - p["kt_bar"]

    eps = rng.standard_normal((n_reps, n_days))
    e = np.empty((n_reps, n_days))
    e[:, 0] = eps[:, 0] * p["sd_e"][:, 0]
    for d in range(1, n_days):
        phi, sd = p["phi"][0, d], p["sd_e"][0, d]
        e[:, d] = phi * e[:, d - 1] + np.sqrt(1 - phi ** 2) * sd * eps[:, d]

    tmean = p["a"] + p["b"] * x + e
    dtr = np.maximum(p["c"] + p["d"] * x + p["sd_u"] * rng.standard_normal((n_reps, n_days)), 1.0)
    tmin = tmean - dtr * SHAPE.mean()
    return tmin[:, :, None] + dtr[:, :, None] * SHAPE[None, None, :]


if __name__ == "__main__":
    names = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    print("month  Tmean  dT/dkt  phi   sd_e  DTR  dDTR/dkt")
    for m in range(12):
        q = {k: v[m] for k, v in PARAMS.items()}
        print(f"{names[m]:5} {q['a']:6.1f} {q['b']:+7.1f} {q['phi']:5.2f} {q['sd_e']:5.2f} "
              f"{q['c']:4.1f} {q['d']:+8.1f}")
