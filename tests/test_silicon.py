import pytest

from memdev.params import values
from memdev.silicon import (bandgap_ev, built_in_potential, depletion_width_cm, generation_bound,
                            ni_silicon)


def test_bandgap_room_temperature():
    assert bandgap_ev(26.85) == pytest.approx(1.1245, abs=2e-3)


def test_ni_room_temperature_near_1e10_and_rises():
    assert ni_silicon(26.85) == pytest.approx(1.0e10, rel=0.10)
    assert ni_silicon(85.0) > 20 * ni_silicon(26.85)


def test_built_in_and_depletion_width():
    vbi = built_in_potential(26.85, 1e17, 1e19)
    assert 0.9 < vbi < 1.05
    w0 = depletion_width_cm(26.85, 1e17, 1e19, 0.0)
    assert 0.08e-4 < w0 < 0.15e-4
    assert depletion_width_cm(26.85, 1e17, 1e19, 1.0) > w0


def test_generation_bound_scales_inverse_tau():
    a = generation_bound(85.0, 1e17, 1e19, 1e-6, 1.0)
    assert generation_bound(85.0, 1e17, 1e19, 1e-7, 1.0) == pytest.approx(10 * a)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        depletion_width_cm(25.0, 1e17, 1e19, -0.1)
    with pytest.raises(ValueError):
        generation_bound(25.0, 1e17, 1e19, 0.0, 1.0)


def test_junction_params_present():
    v = values("dram_baseline")
    assert (v["na"], v["nd"], v["tau_srh"], v["j_area"]) == (1e17, 1e19, 1e-6, 1e-11)
