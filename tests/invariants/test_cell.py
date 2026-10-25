import numpy as np
import pytest

from memdev.dram.cell import bitline_signal, cell_voltage, fail_voltage, retention_time

CS, CBL, VDD = 10e-15, 50e-15, 1.1


def test_charge_sharing_conserves_charge():
    v = 1.1
    dv = bitline_signal(v, VDD, CS, CBL)
    assert CS * v + CBL * VDD / 2 == pytest.approx((CS + CBL) * (VDD / 2 + dv))


def test_baseline_fail_voltage_and_retention():
    vf = fail_voltage(VDD, CS, CBL, 0.05)
    assert vf == pytest.approx(0.85)
    assert retention_time(VDD, vf, 2.5e-15, CS) == pytest.approx(1.0)


def test_small_cs_makes_cell_unreadable():
    vf = fail_voltage(VDD, 2e-15, CBL, 0.05)
    assert vf >= VDD
    assert retention_time(VDD, vf, 2.5e-15, 2e-15) == 0.0


def test_more_leakage_shorter_retention():
    vf = fail_voltage(VDD, CS, CBL, 0.05)
    assert retention_time(VDD, vf, 5e-15, CS) < retention_time(VDD, vf, 2.5e-15, CS)


def test_cell_voltage_vectorized_and_non_negative():
    t = np.logspace(-3, 3, 50)
    v = cell_voltage(t, VDD, 2.5e-15, CS)
    assert v.shape == t.shape and (v >= 0).all() and (np.diff(v) <= 0).all()


@pytest.mark.parametrize("bad", [0.0, -1e-15])
def test_invalid_inputs_raise(bad):
    with pytest.raises(ValueError):
        retention_time(VDD, 0.85, bad, CS)
    with pytest.raises(ValueError):
        cell_voltage(1.0, VDD, 2.5e-15, bad)
