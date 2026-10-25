import numpy as np
import pytest

from memdev.units import K_B_EV, celsius_to_kelvin


def test_celsius_to_kelvin_scalar_and_array():
    assert celsius_to_kelvin(85.0) == pytest.approx(358.15)
    np.testing.assert_allclose(celsius_to_kelvin(np.array([0.0, 100.0])), [273.15, 373.15])


def test_below_absolute_zero_raises():
    with pytest.raises(ValueError):
        celsius_to_kelvin(-300.0)


def test_boltzmann_ev():
    assert K_B_EV == pytest.approx(8.617333262e-5)
