"""Phase 10: back-test the model against real INEC bills. See docs/project_plan.md §9.1.

Input: data/bills/bills.csv (copy data/bills/bills_template.csv), one row per bill:
  household_id   any label
  year, month    billing month (month 1–12)
  kwh            kWh billed (for net-metered homes: energy imported)
  pesos          total amount due ₱
  aircon         1 if the household runs an aircon, else 0
  pv_kwp         installed PV size, 0 if no solar
  import_kwh, export_kwh   net-metered homes only (both shown on the bill)

Tests:
  A. Tariff test — every bill: model bill from its kWh vs the real ₱.
     Works with a single bill and no solar. Tests the billing layer (Layer 3).
  B. Net-metering test — bills with export_kwh: model bill under both credit
     rules ("bill" vs "generation"); the closer one shows how INEC applies it.
  C. Seasonal test — households with ≥ 2 bills: calibrate to one bill, predict
     the kWh of the other months from the model's seasonal pattern.

Reports absolute percentage errors and MAPE.

Run from the project root:  python3 -m src.backtest [path/to/bills.csv]
Writes results/backtest.txt
"""
import csv
import sys
from pathlib import Path

import numpy as np

from .tariff import EFFECTIVE, monthly_bills

ROOT = Path(__file__).resolve().parents[1]
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def read_bills(path):
    num = lambda v: float(v) if v not in ("", None) else None
    with Path(path).open() as f:
        rows = [{k: (v if k == "household_id" else num(v)) for k, v in r.items()}
                for r in csv.DictReader(f) if r.get("household_id")]
    for r in rows:
        r["month"], r["year"] = int(r["month"]), int(r["year"] or 0)
        r["aircon"] = bool(r["aircon"])
        r["pv_kwp"] = r["pv_kwp"] or 0.0
    return rows


def model_bill(imp_kwh, exp_kwh=0.0, offset="bill"):
    return float(monthly_bills(np.array([[imp_kwh]]), np.array([[exp_kwh]]), offset=offset)[0, 0])


def ape(pred, actual):
    return 100 * abs(pred - actual) / actual


def main(path=ROOT / "data" / "bills" / "bills.csv"):
    path = Path(path)
    if not path.exists():
        raise SystemExit(f"{path} not found — copy data/bills/bills_template.csv to "
                         f"data/bills/bills.csv and enter your bills")
    rows = read_bills(path)
    lines = [f"Back-test on {len(rows)} bills from {len({r['household_id'] for r in rows})} "
             f"household(s); tariff: INEC {EFFECTIVE}\n"]

    # A. tariff test ---------------------------------------------------------
    lines.append("A. Tariff test (no-solar bills): model ₱ from billed kWh vs real ₱")
    errs = []
    for r in rows:
        if r["pv_kwp"] > 0 or r["pesos"] is None:
            continue
        pred = model_bill(r["kwh"])
        e = ape(pred, r["pesos"])
        errs.append(e)
        lines.append(f"  {r['household_id']:14} {MONTHS[r['month'] - 1]} {r['year']}: "
                     f"{r['kwh']:6.0f} kWh  real ₱{r['pesos']:8,.2f}  model ₱{pred:8,.2f}  "
                     f"error {e:4.1f}%  (real all-in ₱{r['pesos'] / r['kwh']:.2f}/kWh)")
    lines.append(f"  MAPE {np.mean(errs):.1f}% over {len(errs)} bills" if errs
                 else "  (no no-solar bills with ₱)")

    # B. net-metering test ---------------------------------------------------
    nm = [r for r in rows if r["export_kwh"] is not None and r["pesos"] is not None]
    lines.append("\nB. Net-metering test: which credit rule matches the real bill?")
    if not nm:
        lines.append("  (no net-metered bills — needs import_kwh and export_kwh)")
    for rule in ("bill", "generation"):
        e = [ape(model_bill(r["import_kwh"] or r["kwh"], r["export_kwh"], rule), r["pesos"])
             for r in nm]
        if e:
            lines.append(f"  credit offsets '{rule}': MAPE {np.mean(e):.1f}%")
    for r in nm:
        b1 = model_bill(r["import_kwh"] or r["kwh"], r["export_kwh"], "bill")
        b2 = model_bill(r["import_kwh"] or r["kwh"], r["export_kwh"], "generation")
        lines.append(f"  {r['household_id']:14} {MONTHS[r['month'] - 1]}: real ₱{r['pesos']:,.2f}  "
                     f"'bill' ₱{b1:,.2f}  'generation' ₱{b2:,.2f}")
    lines.append("  NOTE: the model starts each test month with no carried-over credit; "
                 "bills showing a credit balance from earlier months are not comparable yet.")

    # C. seasonal test -------------------------------------------------------
    lines.append("\nC. Seasonal test: calibrate to one bill, predict other months' kWh")
    homes = {}
    for r in rows:
        if r["pv_kwp"] == 0:
            homes.setdefault(r["household_id"], []).append(r)
    multi = {h: b for h, b in homes.items() if len({x["month"] for x in b}) >= 2}
    if not multi:
        lines.append("  (needs a household with bills from ≥ 2 different months)")
    else:
        from .markov import day_months
        from .simulation import generate_scenarios
        shape = {}
        for ac in {b[0]["aircon"] for b in multi.values()}:
            _, load = generate_scenarios(300, aircon=ac)
            m = day_months(load.shape[1])
            shape[ac] = np.array([load[:, m == k + 1].sum((1, 2)).mean() for k in range(12)])
        all_e = []
        for h, bills in multi.items():
            s = shape[bills[0]["aircon"]]
            for ref in bills:            # leave-one-in: calibrate on each bill in turn
                for tgt in bills:
                    if tgt is ref:
                        continue
                    pred = s[tgt["month"] - 1] * ref["kwh"] / s[ref["month"] - 1]
                    all_e.append(ape(pred, tgt["kwh"]))
            lines.append(f"  {h}: {len(bills)} bills, mean error {np.mean(all_e[-len(bills) * (len(bills) - 1):]):.1f}%")
        lines.append(f"  MAPE {np.mean(all_e):.1f}% over {len(all_e)} predictions")

    text = "\n".join(lines)
    print(text)
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "backtest.txt").write_text(text + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:])
