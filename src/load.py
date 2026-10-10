"""Layer 2: bottom-up household load model. See docs/project_plan.md §5.

  * Appliance inventory: data/appliances.csv (ratings, duty, classification
    fixed / occupancy / cooking / thermostatic / shiftable, §5.3).
  * Occupancy: hourly Markov chain over {away, home-active} during waking
    hours, with a stochastic sleep window (§5.1 option 2).
  * Thermostatic loads (fans, aircon) and refrigerator duty depend on the
    same ambient temperature series that drives PV cell temperature, so
    solar–load correlation emerges structurally (§5.2).
  * Shiftable loads (washing, pumping, ironing) are returned separately with
    their default start hours; Layer 5 can move them within
    [earliest_hour, latest_hour].

ASSUMPTIONS: ratings and usage are representative engineering values, not
surveyed. Replace with metered/surveyed Ilocos Norte data (§5.1 option 1).
Monthly totals can be calibrated to a household's bills (src/household.py).
"""
import csv
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
HOURS = np.arange(24)


def load_inventory(path=ROOT / "data" / "appliances.csv"):
    with Path(path).open() as f:
        rows = list(csv.DictReader(f))
    num = lambda v: float(v) if v not in ("", None) else None
    return {r["name"]: {k: (num(v) if k not in ("name", "class", "notes") else v)
                        for k, v in r.items()} for r in rows}


INVENTORY = load_inventory()

# Probability of being home and active, by hour, when awake.
P_ACTIVE_WEEKDAY = np.array([.9, .9, .9, .9, .9, .95, .95, .9, .6, .55, .55, .6,
                             .7, .6, .55, .55, .7, .9, .95, .95, .95, .95, .9, .9])
P_ACTIVE_WEEKEND = np.where((HOURS >= 8) & (HOURS < 17), .85, P_ACTIVE_WEEKDAY)
OCC_PERSIST = 0.8     # P(keep previous active/away state) each hour
AC_ON_T = 26.5        # °C at 21:00 above which an aircon owner runs it overnight


def _weekday(n_days):
    """Day of week, 0 = Monday. 2026-01-01 is a Thursday (3)."""
    return (np.arange(n_days) + 3) % 7


def simulate_occupancy(rng, n_reps, n_days):
    """Returns (active, asleep) boolean arrays (n_reps, n_days, 24)."""
    wd = _weekday(n_days)
    target = np.where((wd >= 5)[:, None], P_ACTIVE_WEEKEND[None], P_ACTIVE_WEEKDAY[None])
    flat = target.ravel()
    T = n_days * 24
    u_keep, u_draw = rng.random((n_reps, T)), rng.random((n_reps, T))
    active = np.empty((n_reps, T), bool)
    active[:, 0] = u_draw[:, 0] < flat[0]
    for t in range(1, T):
        fresh = u_draw[:, t] < flat[t]
        active[:, t] = np.where(u_keep[:, t] < OCC_PERSIST, active[:, t - 1], fresh)
    active = active.reshape(n_reps, n_days, 24)

    bed = rng.integers(21, 24, size=(n_reps, n_days, 1))   # 21:00–23:00
    wake = rng.integers(4, 7, size=(n_reps, n_days, 1))    # 04:00–06:00
    h = HOURS[None, None, :]
    asleep = (h >= bed) | (h < wake)
    return active & ~asleep, asleep


def _thermostatic(tamb, active, asleep, aircon):
    fan = INVENTORY["electric_fan"]
    fans_awake = np.clip(np.floor((tamb - 25) / 2), 0, fan["count"])
    fans_sleep = np.where(tamb > 28, 2, np.where(tamb > 25, 1, 0))
    fans = np.where(active, fans_awake, np.where(asleep, fans_sleep, 0))
    e_fan = fans * fan["rated_w"] / 1000

    if not aircon:
        return e_fan, np.zeros_like(tamb)
    ac = INVENTORY["aircon_inverter_1hp"]
    h = HOURS[None, None, :]
    # Nightly decision: if it is still >= AC_ON_T at 21:00, run it all night
    # (21:00–05:00 while asleep). The 05:00 hours belong to the previous night.
    warm_evening = tamb[:, :, 21:22] >= AC_ON_T
    prev = np.concatenate([warm_evening[:, :1], warm_evening[:, :-1]], axis=1)
    on = np.where(h >= 21, warm_evening, np.where(h < 5, prev, False))
    night = asleep & on
    duty = np.clip((tamb - 23) / 5, 0.4, 1.0)
    e_ac = np.where(night, duty * ac["rated_w"] / 1000, 0.0)
    return np.where(night, 0.0, e_fan), e_ac   # fans off while aircon runs


SOLAR_HOUR = 11   # hour of highest mean PV output (results/load_validation.png)


def shiftable_defaults(n_days, policy="default"):
    """Shiftable energy (n_days, 24) kWh, identical across replications.

    policy "default": each appliance at its usual `default_hour`.
    policy "solar":   moved to SOLAR_HOUR, clipped to the appliance's allowed
                      [earliest_hour, latest_hour] window (comfort limit, §8.3).
    """
    wd = _weekday(n_days)
    out = np.zeros((n_days, 24))
    days = {"washing_machine": np.isin(wd, [2, 5, 6]),
            "water_pump": np.ones(n_days, bool),
            "flat_iron": wd == 6}
    for name, on in days.items():
        a = INVENTORY[name]
        hour = a["default_hour"] if policy == "default" else np.clip(
            SOLAR_HOUR, a["earliest_hour"], a["latest_hour"])
        out[on, int(hour)] += a["kwh_per_use"]
    return out


def simulate_load(rng, tamb, aircon=False, components=False):
    """Hourly load in kWh, shape (n_reps, n_days, 24).

    aircon: whether the household owns the 1 hp inverter aircon.
    components=True also returns {end_use: mean kWh/yr per replication}.
    """
    n_reps, n_days, _ = tamb.shape
    active, asleep = simulate_occupancy(rng, n_reps, n_days)
    h = HOURS[None, None, :]
    dark = (h < 6) | (h >= 18)
    inv = INVENTORY

    ref = inv["refrigerator"]["kwh_per_use"] / 24 * (1 + 0.03 * (tamb - 27))
    standby = np.full(tamb.shape, inv["standby_router_chargers"]["rated_w"] / 1000)
    led = inv["led_lighting"]
    light = (np.where(active & dark, 0.6 * led["count"] * led["rated_w"], 0.0)
             + np.where(asleep, inv["night_light"]["rated_w"], 0.0)) / 1000
    tv_p = np.where((h >= 18) & (h < 22), 0.8, 0.3)
    tv = (active & (rng.random(tamb.shape) < tv_p)) * inv["television"]["rated_w"] / 1000
    meals = np.zeros(24)
    meals[[5, 10, 17]] = [0.9, 0.7, 0.9]
    rice = (rng.random(tamb.shape) < meals[None, None, :]) * inv["rice_cooker"]["kwh_per_use"]
    fans, ac = _thermostatic(tamb, active, asleep, aircon)
    shift = np.broadcast_to(shiftable_defaults(n_days)[None], tamb.shape)

    parts = dict(refrigerator=ref, standby=standby, lighting=light, television=tv,
                 rice_cooker=rice, fans=fans, aircon=ac, shiftable=shift)
    total = sum(parts.values())
    if components:
        return total, {k: float(np.asarray(v).sum((1, 2)).mean()) for k, v in parts.items()}
    return total
