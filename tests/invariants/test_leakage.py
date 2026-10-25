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


def test_ten_degree_ratio_depends_on_temperature():
    # 문서(01 노트북, 면접 Q&A)에 적은 수치: 25→35°C 약 2.1배, 80→90°C 약 1.7배
    def ratio(t_low):
        return arrhenius_leakage(t_low + 10, 2.5e-15, 85.0, 0.6) / arrhenius_leakage(t_low, 2.5e-15, 85.0, 0.6)
    assert ratio(25.0) == pytest.approx(2.13, rel=0.01)
    assert ratio(25.0) > ratio(80.0)
