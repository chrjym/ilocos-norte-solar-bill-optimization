"""Verification and validation (V&V) tests for the solar bill model.

VERIFICATION — "is the model built right?"  The code does what the equations
in docs/project_plan.md say it does: probabilities sum to 1, energy is
conserved, a bill computed by hand equals the bill computed by the code,
the same seed gives the same answer.

VALIDATION — "is it the right model?"  The model's output agrees with the
real world: 24 years of NASA POWER weather for Batac and the household's
real September 2026 INEC bill (464 kWh, ₱5,739.45); October 2026 (509 kWh,
₱6,295.52) is in data/bills/bills.csv.

Run from the project root:  .venv/bin/python -m pytest tests -v
"""
import numpy as np
import pytest

from src import markov, tariff
from src.household import calibrate_load, household_inputs
from src.markov import day_months, extraterrestrial_hourly, stationary
from src.pv import ac_energy_per_kwp
from src.simulation import bills_for_size, generate_scenarios, monthly_flows
from src.validate_generator import acf, historical, monthly_means, synthetic

N = 200          # Monte Carlo years: enough for the tolerances below, fast to run
SEP_KWH, SEP_PESOS = 464.0, 5739.45
OCT_KWH, OCT_PESOS = 509.0, 6295.52
FIXED = tariff.FIXED_PER_MONTH * (1 + tariff.VAT)


@pytest.fixture(scope="module")
def scenarios():
    return generate_scenarios(N, aircon=True)


# ============================================================================
# VERIFICATION
# ============================================================================

class TestMarkovChain:
    def test_tpm_rows_are_probabilities(self):
        for name, P in markov.TPM.items():
            assert np.all(P >= 0), name
            np.testing.assert_allclose(P.sum(1), 1.0, atol=1e-9, err_msg=str(name))

    def test_stationary_distribution(self):
        for P in markov.TPM.values():
            pi = stationary(P)
            np.testing.assert_allclose(pi @ P, pi, atol=1e-9)   # π P = π
            assert pi.sum() == pytest.approx(1.0)

    def test_states_and_kt_in_range(self):
        rng = np.random.default_rng(0)
        s = markov.simulate_daily_states(rng, 50)
        assert s.shape == (50, 365)
        assert s.min() >= 0 and s.max() < markov.N_STATES
        kt = markov.sample_kt(rng, s)
        assert np.all((kt >= markov.KT_EDGES[s]) & (kt <= markov.KT_EDGES[s + 1]))

    def test_calendar(self):
        assert np.bincount(day_months())[1:].tolist() == \
            [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    def test_no_sun_at_night(self):
        h0 = extraterrestrial_hourly()
        assert np.all(h0[:, [0, 1, 2, 3, 21, 22, 23]] == 0)
        assert np.all(h0[:, 12] > 900)       # noon at 18°N is always high sun


class TestPV:
    def test_hand_calculation(self):
        # GHI 1000 W/m², 30 °C → Tcell = 30 + 1000·25/800 = 61.25 °C
        # AC = 1 kW × (1 − 0.004·36.25) × 0.86 = 0.7353 kWh in that hour
        assert ac_energy_per_kwp(np.array(1000.0), np.array(30.0)) == pytest.approx(0.7353, abs=1e-4)

    def test_zero_irradiance_gives_zero(self):
        assert ac_energy_per_kwp(np.array(0.0), np.array(25.0)) == 0.0

    def test_hotter_panel_produces_less(self):
        assert ac_energy_per_kwp(800.0, 35.0) < ac_energy_per_kwp(800.0, 25.0)


class TestTariff:
    def test_all_in_rate_matches_published_figure(self):
        assert tariff.effective_rate() == pytest.approx(11.7246, abs=1e-6)

    def test_bill_by_hand_no_solar(self):
        b = tariff.monthly_bills(np.full((1, 12), 100.0), np.zeros((1, 12)))
        np.testing.assert_allclose(b, 100 * 11.7246 + FIXED)

    def test_zero_use_pays_only_fixed_charge(self):
        b = tariff.monthly_bills(np.zeros((1, 12)), np.zeros((1, 12)))
        np.testing.assert_allclose(b, FIXED)

    def test_credit_carries_forward_and_never_goes_negative(self):
        imp = np.full((1, 12), 100.0)
        exp = np.zeros((1, 12))
        exp[0, 0] = 1000.0                                   # big export in January only
        b = tariff.monthly_bills(imp, exp, offset="bill")
        credit = 1000 * tariff.EXPORT_CREDIT                 # ≈ ₱5,000+ of credit
        monthly_var = 100 * tariff.effective_rate()
        n_free = int(credit // monthly_var)                  # months fully paid by credit
        np.testing.assert_allclose(b[0, :n_free], FIXED)     # floor = fixed charge
        assert np.all(b >= FIXED - 1e-9)
        # total paid = no-solar total − credit (all credit gets used in the year)
        assert b.sum() == pytest.approx(12 * (monthly_var + FIXED) - credit)

    def test_generation_offset_is_never_cheaper_than_bill_offset(self):
        rng = np.random.default_rng(1)
        imp, exp = rng.uniform(0, 400, (100, 12)), rng.uniform(0, 400, (100, 12))
        # Compared over the year: carried credit can move savings between months
        assert np.all(tariff.monthly_bills(imp, exp, offset="generation").sum(1)
                      >= tariff.monthly_bills(imp, exp, offset="bill").sum(1) - 1e-6)


class TestSimulationEngine:
    def test_energy_balance(self, scenarios):
        # load − PV = import − export, month by month (hourly netting)
        pv1, load = scenarios
        imp, exp = monthly_flows(pv1, load, 3.0)
        m = day_months()
        for k in range(12):
            net = (load[:, m == k + 1] - 3.0 * pv1[:, m == k + 1]).sum((1, 2))
            np.testing.assert_allclose(imp[:, k] - exp[:, k], net, rtol=1e-4, atol=1e-2)

    def test_zero_kwp_has_no_export(self, scenarios):
        imp, exp = monthly_flows(*scenarios, 0.0)
        assert np.all(exp == 0)

    def test_more_solar_never_raises_the_bill(self, scenarios):
        pv1, load = scenarios
        means = [bills_for_size(pv1, load, k).sum(1).mean() for k in (0, 1, 2, 3, 4, 5)]
        # ≥ up to float32 rounding (bill flattens at the fixed charge once credit covers all)
        assert all(a >= b - 0.01 for a, b in zip(means, means[1:]))
        assert means[-1] == pytest.approx(12 * FIXED, abs=0.01)

    def test_same_seed_same_result(self):
        a, b = generate_scenarios(5), generate_scenarios(5)
        np.testing.assert_array_equal(a[0], b[0])
        np.testing.assert_array_equal(a[1], b[1])

    def test_common_random_numbers(self):
        # Aircon changes the load, but must NOT change the sampled weather
        pv_a, _ = generate_scenarios(5, aircon=False)
        pv_b, _ = generate_scenarios(5, aircon=True)
        np.testing.assert_array_equal(pv_a, pv_b)


class TestCalibration:
    def test_one_bill_calibration_hits_the_bill(self, scenarios):
        _, load = scenarios
        kwh12, scale = household_inputs(load, [SEP_KWH], [SEP_PESOS], month=9)
        assert kwh12[8] == pytest.approx(SEP_KWH)
        cal = calibrate_load(load, kwh12)
        sep = cal[:, day_months() == 9].sum((1, 2)).mean()
        assert sep == pytest.approx(SEP_KWH, rel=1e-4)
        # tariff scale makes the model reproduce the ₱ amount exactly
        bill = SEP_KWH * tariff.effective_rate() * scale + FIXED
        assert bill == pytest.approx(SEP_PESOS, abs=0.01)

    def test_two_bill_calibration_hits_both_bills(self, scenarios):
        _, load = scenarios
        kwh12, scale = household_inputs(load, [SEP_KWH, OCT_KWH],
                                        [SEP_PESOS, OCT_PESOS], month=[9, 10])
        cal = calibrate_load(load, kwh12)
        for m, kwh in ((9, SEP_KWH), (10, OCT_KWH)):
            assert cal[:, day_months() == m].sum((1, 2)).mean() == pytest.approx(kwh, rel=1e-4)
        # one tariff scale reproduces the ₱ total of both bills
        bills = (SEP_KWH + OCT_KWH) * tariff.effective_rate() * scale + 2 * FIXED
        assert bills == pytest.approx(SEP_PESOS + OCT_PESOS, abs=0.01)


# ============================================================================
# VALIDATION
# ============================================================================

@pytest.fixture(scope="module")
def kt_hist():
    return historical()


@pytest.fixture(scope="module")
def kt_synth():
    return synthetic(500, seed=4, iid=False, resolution="month")


class TestWeatherValidation:
    """Synthetic years vs 24 real years of Batac (NASA POWER)."""

    def test_monthly_mean_clearness_within_3pct(self, kt_hist, kt_synth):
        h, s = monthly_means(kt_hist).mean(0), monthly_means(kt_synth).mean(0)
        np.testing.assert_allclose(s, h, rtol=0.03)

    def test_day_to_day_persistence(self, kt_hist, kt_synth):
        # lag-1 autocorrelation: history ≈ 0.64; Markov must be close
        assert abs(acf(kt_synth, 1)[0] - acf(kt_hist, 1)[0]) < 0.10

    def test_persistence_test_can_fail(self, kt_hist):
        # Sanity check of the test itself: i.i.d. days (no Markov memory) fail it
        kt_iid = synthetic(500, seed=4, iid=True, resolution="month")
        assert abs(acf(kt_iid, 1)[0] - acf(kt_hist, 1)[0]) > 0.30

    def test_monthly_variability_kept(self, kt_hist, kt_synth):
        sd_h = monthly_means(kt_hist).std(0).mean()
        sd_s = monthly_means(kt_synth).std(0).mean()
        assert sd_s == pytest.approx(sd_h, rel=0.25)


class TestPVValidation:
    def test_annual_yield_is_realistic(self, scenarios):
        # Northern Luzon fixed PV: ~1,300–1,600 kWh/kWp/yr (PVGIS / Global Solar Atlas range)
        y = scenarios[0].sum((1, 2)).mean()
        assert 1300 < y < 1650

    def test_dry_season_beats_wet_season(self, scenarios):
        m = day_months()
        pv = scenarios[0]
        dry = pv[:, np.isin(m, [2, 3, 4])].sum((1, 2)).mean() / 89
        wet = pv[:, np.isin(m, [7, 8, 9])].sum((1, 2)).mean() / 92
        assert dry > wet


class TestBillValidation:
    def test_unscaled_tariff_reproduces_real_bill(self):
        """Back-test: published tariff alone (no calibration) vs the real
        Sep 2026 bill. Accept ≤10% error (current: ≈5.1%)."""
        model = tariff.monthly_bills(np.full((1, 12), SEP_KWH), np.zeros((1, 12)))[0, 8]
        assert abs(model - SEP_PESOS) / SEP_PESOS < 0.10

    def test_simulated_load_is_household_scale(self, scenarios):
        # Uncalibrated aircon household: a few hundred kWh per month
        sep = scenarios[1][:, day_months() == 9].sum((1, 2)).mean()
        assert 150 < sep < 900
