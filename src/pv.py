"""Layer 1b: irradiance → AC energy, plus the shared ambient temperature series.
See docs/project_plan.md §4.6.

PLACEHOLDER: PVWatts-style model on horizontal GHI. Replace with the pvlib
chain (Erbs decomposition, Hay–Davies transposition, Faiman temperature).
"""
from .temperature import simulate_ambient  # noqa: F401  (re-exported)

GAMMA = -0.004     # power temperature coefficient (1/°C)
NOCT = 45.0        # °C
DERATE = 0.86      # inverter, soiling, wiring, mismatch, availability


def ac_energy_per_kwp(ghi, tamb):
    """AC kWh per hour per kWp installed."""
    tcell = tamb + ghi * (NOCT - 20) / 800
    return (ghi / 1000) * (1 + GAMMA * (tcell - 25)) * DERATE
