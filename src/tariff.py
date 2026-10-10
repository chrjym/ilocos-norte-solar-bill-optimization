"""Layer 3: INEC unbundled residential bill with net-metering settlement.
See docs/project_plan.md §6.

Line-item structure and values: INEC Unbundled Rate Schedule, January 2020
billing (data/raw/tariff/URS-January-2020.pdf, residential column).

Updated to April 2026 (latest public figures found, Daily Tribune 2026-04-09):
  * transmission charge ₱1.5476/kWh (reported);
  * all-in residential rate ₱11.7246/kWh (reported). The generation rate is
    SOLVED so the schedule reproduces this total, because the April 2026
    generation line itself was not published in the source found.
All other lines keep their January 2020 values. VERIFY against a current
INEC bill / URS before using results (§6.3).

Not yet modelled: lifeline discount (only for qualified marginalized
end-users under RA 11552), senior-citizen discount.
"""
import numpy as np

EFFECTIVE = "April 2026 (derived; Jan-2020 structure)"

# ₱/kWh, pre-VAT, residential (URS Jan 2020)
LINES = {
    "generation": 3.7082,
    "transmission": 0.8987,
    "system_loss": 0.4893,
    "distribution_system": 0.4613,
    "supply_system": 0.5376,
    "metering_system": 0.3205,
    "rfsc": 0.2752,
    "lifeline_subsidy": 0.0334,
    "senior_citizen_subsidy": 0.0004,
    "daa_gram": 0.0967,
    "daa_icera": 0.0456,
    "uc_missionary": 0.1544,
    "uc_me_red": 0.0017,
    "uc_environmental": 0.0025,
    "uc_npc_stranded_contract": 0.0543,
    "uc_npc_stranded_debt": 0.0428,
    "fit_all": 0.2226,
}
# ₱/kWh pass-through VAT lines (URS Jan 2020)
VAT_LINES = {
    "generation": 0.5744,
    "transmission": 0.0875,
    "system_loss": 0.0711,
    "daa_gram": 0.0088,
    "daa_icera": 0.0044,
}
METERING_FIXED = 5.00        # ₱/meter/month (retail customer charge)
VAT = 0.12                   # on distribution-group charges
FRANCHISE_TAX = 0.008662 + 0.005   # city (Batac; Laoag rate assumed) + province, on distribution group
DIST_GROUP = ("distribution_system", "supply_system", "metering_system")

# --- update to April 2026 ---------------------------------------------------
_TARGET_ALL_IN = 11.7246
_TRANSMISSION_2026 = 1.5476
VAT_LINES["transmission"] *= _TRANSMISSION_2026 / LINES["transmission"]
LINES["transmission"] = _TRANSMISSION_2026


def _all_in(lines, vat_lines):
    dist = sum(lines[k] for k in DIST_GROUP)
    return sum(lines.values()) + sum(vat_lines.values()) + dist * (VAT + FRANCHISE_TAX)


_gen_vat_ratio = VAT_LINES["generation"] / LINES["generation"]
_gap = _TARGET_ALL_IN - _all_in(LINES, VAT_LINES)
LINES["generation"] += _gap / (1 + _gen_vat_ratio)
VAT_LINES["generation"] = LINES["generation"] * _gen_vat_ratio
# ----------------------------------------------------------------------------

FIXED_PER_MONTH = METERING_FIXED * (1 + VAT + FRANCHISE_TAX) / (1 + VAT)
"""Kept in pre-VAT form so `FIXED_PER_MONTH * (1 + VAT)` is the billed fixed ₱."""

# Net metering (ERC Res. 09 s.2013 / 06 s.2019): exports credited at the DU's
# blended generation cost (INEC's generation rate), applied to the bill,
# excess carried forward.
EXPORT_CREDIT = LINES["generation"]
OFFSET = "bill"   # "bill": credit may offset all variable charges
                  # "generation": credit may offset only generation + its VAT


def effective_rate():
    """All-in ₱/kWh including taxes, excluding the fixed charge."""
    return _all_in(LINES, VAT_LINES)


def generation_rate_all_in():
    return LINES["generation"] + VAT_LINES["generation"]


def monthly_bills(imp_kwh, exp_kwh, scale=1.0, offset=None, credit_mult=1.0):
    """imp/exp: (n_reps, 12) kWh per month. Returns ₱ bills (n_reps, 12).

    Export credits offset the bill; unused credit carries to the next month.
    `scale` multiplies every per-kWh rate (used to calibrate to a user's bills).
    `credit_mult` scales the export credit rate relative to the generation rate.
    """
    offset = offset or OFFSET
    variable = imp_kwh * effective_rate() * scale
    fixed = FIXED_PER_MONTH * (1 + VAT)
    offsettable = variable if offset == "bill" else imp_kwh * generation_rate_all_in() * scale
    credit_new = exp_kwh * EXPORT_CREDIT * scale * credit_mult
    bills = np.empty_like(variable)
    carry = np.zeros(variable.shape[0])
    for m in range(variable.shape[1]):
        avail = carry + credit_new[:, m]
        used = np.minimum(avail, offsettable[:, m])
        bills[:, m] = variable[:, m] + fixed - used
        carry = avail - used
    return bills


if __name__ == "__main__":
    print(f"INEC residential tariff, {EFFECTIVE}")
    for k, v in LINES.items():
        print(f"  {k:28} {v:8.4f}")
    print(f"  generation all-in (export credit basis) {generation_rate_all_in():.4f}")
    print(f"  all-in ₱/kWh {effective_rate():.4f} (target {_TARGET_ALL_IN})")
