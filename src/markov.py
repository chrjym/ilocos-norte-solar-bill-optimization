"""Layer 1: season-conditioned Markov chain of daily clearness index (kt) states,
with disaggregation to hourly. See docs/project_plan.md §4.

PLACEHOLDER: the transition matrices below are illustrative, not estimated.
Replace them with MLE estimates from NASA POWER data (§4.3).
"""
from pathlib import Path

import numpy as np

LAT_DEG = 18.055  # Batac City

# kt bin edges for the 6 states in §4.2 (top capped at a realistic 0.80)
KT_EDGES = np.array([0.00, 0.15, 0.30, 0.45, 0.60, 0.72, 0.80])
N_STATES = len(KT_EDGES) - 1

DRY_MONTHS = {11, 12, 1, 2, 3, 4}

# "month": one TPM per calendar month (default, chosen by generator validation,
# see src/validate_generator.py); "season": dry/wet pooled TPMs.
RESOLUTION = "month"


def _regime(month, resolution):
    if resolution == "month":
        return month
    return "dry" if month in DRY_MONTHS else "wet"


def _tpm(stay, target):
    """Persistence-weighted TPM: stay in the current state w.p. `stay`,
    otherwise jump according to the `target` distribution."""
    target = np.asarray(target, float) / np.sum(target)
    return stay * np.eye(N_STATES) + (1 - stay) * np.tile(target, (N_STATES, 1))


# Placeholder: dry season mostly clear; wet season cloudier and more persistent.
TPM = {
    "dry": _tpm(0.45, [0.02, 0.04, 0.09, 0.20, 0.35, 0.30]),
    "wet": _tpm(0.60, [0.12, 0.18, 0.22, 0.22, 0.17, 0.09]),
}

# Use estimated TPMs and bin edges when src.estimate_tpm has been run.
_FITTED = Path(__file__).resolve().parents[1] / "data" / "processed" / "tpm_batac.npz"
if _FITTED.exists():
    _f = np.load(_FITTED)
    KT_EDGES = _f["edges"]
    N_STATES = len(KT_EDGES) - 1
    TPM = {"dry": _f["tpm_dry"], "wet": _f["tpm_wet"]}
    TPM.update({m: _f[f"tpm_m{m:02d}"] for m in range(1, 13)})
    _KT_HIST, _MONTH_HIST = _f["kt_hist"], _f["month_hist"]
    print(f"[markov] using fitted TPMs from {_FITTED.name}")
else:
    _KT_HIST = None
    print("[markov] WARNING: using placeholder TPMs (run src.estimate_tpm)")


def stationary(P):
    w, v = np.linalg.eig(P.T)
    pi = np.real(v[:, np.argmin(np.abs(w - 1))])
    return pi / pi.sum()


def day_months(n_days=365):
    """Calendar month (1-12) of each day of a non-leap year."""
    lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return np.repeat(np.arange(1, 13), lengths)[:n_days]


def simulate_daily_states(rng, n_reps, n_days=365, iid=False, resolution=None):
    """Daily kt states, shape (n_reps, n_days).

    iid=True draws each day independently from the season's stationary
    distribution: the 'no persistence' ablation for research question 1.
    """
    resolution = resolution or RESOLUTION
    if resolution == "month" and 1 not in TPM:
        resolution = "season"   # placeholder TPMs have no monthly matrices
    months = day_months(n_days)
    cums = {s: np.cumsum(P, axis=1) for s, P in TPM.items()}
    pis = {s: np.cumsum(stationary(P)) for s, P in TPM.items()}
    states = np.empty((n_reps, n_days), dtype=np.int8)
    state = (rng.random(n_reps)[:, None] > pis[_regime(months[0], resolution)]).sum(1)
    for d in range(n_days):
        season = _regime(months[d], resolution)
        u = rng.random(n_reps)
        if iid:
            state = (u[:, None] > pis[season]).sum(1)
        else:
            state = (u[:, None] > cums[season][state]).sum(1)
        states[:, d] = np.minimum(state, N_STATES - 1)
    return states


def in_bin_rho(resolution=None):
    """Lag-1 correlation of the historical normal-score position of kt within
    its (regime, state) pool: the persistence the state sequence alone misses."""
    from scipy.stats import norm
    resolution = resolution or RESOLUTION
    hist_reg = np.array([_regime(m, resolution) for m in _MONTH_HIST])
    hist_state = np.clip(np.digitize(_KT_HIST, KT_EDGES) - 1, 0, N_STATES - 1)
    z = np.empty_like(_KT_HIST)
    for reg in set(hist_reg.tolist()):
        for s in range(N_STATES):
            sel = (hist_reg == reg) & (hist_state == s)
            ranks = _KT_HIST[sel].argsort().argsort()
            z[sel] = norm.ppf((ranks + 0.5) / sel.sum())
    return float(np.corrcoef(z[:-1], z[1:])[0, 1])


def _ar1_uniforms(rng, shape, rho):
    """Uniforms whose normal scores follow a stationary AR(1) along axis 1."""
    from scipy.stats import norm
    eps = rng.standard_normal(shape)
    z = np.empty(shape)
    z[:, 0] = eps[:, 0]
    s = np.sqrt(1 - rho ** 2)
    for d in range(1, shape[1]):
        z[:, d] = rho * z[:, d - 1] + s * eps[:, d]
    return norm.cdf(z)


def sample_kt(rng, states, resolution=None, persist=True):
    """Daily kt for each state. With fitted data, draws from the historical kt
    values observed in that state and regime (empirical in-bin distribution).
    With persist=True the position within the bin follows an AR(1) process
    (rho fitted by `in_bin_rho`), restoring multi-day autocorrelation.
    Without fitted data: uniform within the bin."""
    lo, hi = KT_EDGES[states], KT_EDGES[states + 1]
    if _KT_HIST is None:
        return lo + (hi - lo) * rng.random(states.shape)
    resolution = resolution or RESOLUTION
    u = (_ar1_uniforms(rng, states.shape, in_bin_rho(resolution)) if persist
         else rng.random(states.shape))
    kt = np.empty(states.shape)
    day_reg = np.array([_regime(m, resolution) for m in day_months(states.shape[1])])
    hist_reg = np.array([_regime(m, resolution) for m in _MONTH_HIST])
    hist_state = np.clip(np.digitize(_KT_HIST, KT_EDGES) - 1, 0, N_STATES - 1)
    for reg in set(day_reg.tolist()):
        for s in range(N_STATES):
            pool = np.sort(_KT_HIST[(hist_reg == reg) & (hist_state == s)])
            sel = (states == s) & (day_reg == reg)[None, :]
            if sel.any():
                kt[sel] = pool[(u[sel] * len(pool)).astype(int)]
    return kt


def extraterrestrial_hourly(n_days=365, lat_deg=LAT_DEG):
    """Extraterrestrial horizontal irradiance H0 (W/m²), shape (n_days, 24)."""
    d = np.arange(1, n_days + 1)[:, None]
    h = np.arange(24)[None, :] + 0.5
    phi = np.radians(lat_deg)
    delta = np.radians(23.45) * np.sin(2 * np.pi * (284 + d) / 365)
    omega = np.radians(15 * (h - 12))
    cosz = np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.cos(omega)
    e0 = 1 + 0.033 * np.cos(2 * np.pi * d / 365)
    return 1361 * e0 * np.clip(cosz, 0, None)


def simulate_ghi(rng, n_reps, n_days=365, iid=False):
    """Returns (ghi W/m² (n_reps, n_days, 24), daily kt (n_reps, n_days)).

    Hourly disaggregation is a simplified stand-in for TAG (§4.5): hourly kt
    = daily kt × lognormal noise. Replace with Aguiar–Collares-Pereira TAG.
    """
    states = simulate_daily_states(rng, n_reps, n_days, iid)
    kt_day = sample_kt(rng, states)
    noise = rng.lognormal(0.0, 0.15, size=(n_reps, n_days, 24))
    kt_hour = np.clip(kt_day[:, :, None] * noise, 0, 0.85)
    return kt_hour * extraterrestrial_hourly(n_days)[None], kt_day
