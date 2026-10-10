"""Layer 4: Monte Carlo engine with common random numbers (CRN).
See docs/project_plan.md §7.

Every PV size is evaluated on the *same* sampled weather and load
trajectories, so differences between sizes are not sampling noise.

Run from the project root:  python3 -m src.simulation [n_reps]
"""
import sys
from pathlib import Path

import numpy as np

from .markov import day_months, simulate_ghi
from .load import simulate_load
from .pv import ac_energy_per_kwp, simulate_ambient
from .tariff import monthly_bills

SEED = 20261007
RESULTS = Path(__file__).resolve().parents[1] / "results"


def streams(seed=SEED, batch=0):
    """Seeding scheme for CRN (§10): SeedSequence(seed) → one child per batch
    → independent child streams for weather, temperature and load. Changing
    one sub-model (e.g. the load model or aircon ownership) leaves the other
    streams, and hence the sampled weather, unchanged."""
    batch_seq = np.random.SeedSequence(seed).spawn(batch + 1)[batch]
    w, t, l = batch_seq.spawn(3)
    return np.random.default_rng(w), np.random.default_rng(t), np.random.default_rng(l)


def generate_scenarios(n_reps, seed=SEED, iid=False, aircon=False, batch=0):
    """Sampled weather + load: (pv per kWp, load), each (n_reps, 365, 24) kWh."""
    rng_w, rng_t, rng_l = streams(seed, batch)
    ghi, kt_day = simulate_ghi(rng_w, n_reps, iid=iid)
    tamb = simulate_ambient(rng_t, kt_day)
    load = simulate_load(rng_l, tamb, aircon=aircon)
    return ac_energy_per_kwp(ghi, tamb).astype(np.float32), load.astype(np.float32)


def monthly_flows(pv1, load, kwp):
    """Monthly imported and exported kWh (n_reps, 12) each, hourly netting."""
    net = load - kwp * pv1
    imp_day = np.clip(net, 0, None).sum(axis=2)
    exp_day = np.clip(-net, 0, None).sum(axis=2)
    starts = np.r_[0, np.flatnonzero(np.diff(day_months(net.shape[1]))) + 1]
    return np.add.reduceat(imp_day, starts, axis=1), np.add.reduceat(exp_day, starts, axis=1)


def bills_for_size(pv1, load, kwp, scale=1.0, offset=None):
    """Monthly ₱ bills (n_reps, 12) for a system of `kwp`, hourly netting."""
    return monthly_bills(*monthly_flows(pv1, load, kwp), scale, offset)


def cvar(x, q=0.95):
    return x[x >= np.quantile(x, q)].mean()


def main(n_reps=2000):
    from .optimization import SIZES_KWP, annualized_capex, optimize

    print(f"Generating {n_reps} one-year scenarios (seed {SEED})...")
    pv1, load = generate_scenarios(n_reps)
    print(f"  mean annual load {load.sum((1, 2)).mean():,.0f} kWh, "
          f"yield {pv1.sum((1, 2)).mean():,.0f} kWh/kWp")

    rows = []
    for kwp in SIZES_KWP:
        bills = bills_for_size(pv1, load, kwp)
        annual = bills.sum(1)
        cost = annual + annualized_capex(kwp)
        rows.append(dict(
            kwp=kwp, bill_mean=annual.mean(),
            bill_p10=np.quantile(annual, .1), bill_p50=np.median(annual),
            bill_p90=np.quantile(annual, .9),
            worst_month_p90=np.quantile(bills.max(1), .9),
            cost_mean=cost.mean(), cost_cvar95=cvar(cost)))

    print("\nAnnual bill (₱) and total annual cost = bill + annualized capex")
    hdr = f"{'kWp':>4} {'mean':>9} {'P10':>9} {'P50':>9} {'P90':>9} " \
          f"{'worstMo P90':>11} {'cost mean':>10} {'cost CVaR95':>11}"
    print(hdr)
    for r in rows:
        print(f"{r['kwp']:>4} {r['bill_mean']:>9,.0f} {r['bill_p10']:>9,.0f} "
              f"{r['bill_p50']:>9,.0f} {r['bill_p90']:>9,.0f} "
              f"{r['worst_month_p90']:>11,.0f} {r['cost_mean']:>10,.0f} "
              f"{r['cost_cvar95']:>11,.0f}")

    optimize(rows)

    # Research question 1: what does ignoring cloud persistence do?
    pv_iid, load_iid = generate_scenarios(n_reps, iid=True)
    k = 1.0
    m_mk = bills_for_size(pv1, load, k)
    m_iid = bills_for_size(pv_iid, load_iid, k)
    print(f"\nPersistence ablation at {k} kWp (monthly bills, ₱):")
    for name, b in [("Markov", m_mk), ("i.i.d.", m_iid)]:
        print(f"  {name:7} mean {b.mean():7,.0f}  std {b.std():6,.0f}  "
              f"P90 {np.quantile(b, .9):7,.0f}  CVaR95 {cvar(b.ravel()):7,.0f}")

    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / "size_sweep.csv"
    keys = list(rows[0])
    out.write_text(",".join(keys) + "\n" + "\n".join(
        ",".join(f"{r[k]:.2f}" for k in keys) for r in rows) + "\n")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2000)
