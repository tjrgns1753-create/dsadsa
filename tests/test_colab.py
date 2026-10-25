import os

from memdev.colab import DEVSIM_MATH_LIBS, setup


def test_setup_without_install_reports_status_and_is_idempotent():
    a = setup(install=False)
    b = setup(install=False)
    assert set(a) == {"ngspice", "devsim", "korean_font"}
    assert a == b
    assert all(isinstance(v, bool) for v in a.values())
    assert os.environ["DEVSIM_MATH_LIBS"] == DEVSIM_MATH_LIBS
