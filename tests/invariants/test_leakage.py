import numpy as np
import pytest

from memdev.dram.leakage import arrhenius_leakage


def test_reference_point():
    assert arrhenius_leakage(85.0, 2.5e-15, 85.0, 0.6) == pytest.approx(2.5e-15)


def test_increases_with_temperature_vectorized():
    i = arrhenius_leakage(np.array([25.0, 45.0, 65.0, 85.0]), 2.5e-15, 85.0, 0.6)
    assert (np.diff(i) > 0).all()


def test_ten_degree_ratio_matches_spike():
    r = arrhenius_leakage(90.0, 2.5e-15, 85.0, 0.6) / arrhenius_leakage(80.0, 2.5e-15, 85.0, 0.6)
    assert r == pytest.approx(1.72, rel=0.01)


def test_nonpositive_reference_raises():
    with pytest.raises(ValueError):
        arrhenius_leakage(85.0, 0.0, 85.0, 0.6)
