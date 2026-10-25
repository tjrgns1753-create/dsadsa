import math
import os
import subprocess
import sys

import pytest

from memdev.colab import DEVSIM_MATH_LIBS

os.environ.setdefault("DEVSIM_MATH_LIBS", DEVSIM_MATH_LIBS)
HAS_DEVSIM = subprocess.run([sys.executable, "-c", "import devsim"], capture_output=True).returncode == 0
pytestmark = pytest.mark.skipif(not HAS_DEVSIM, reason="devsim not available")

from memdev.dram.devsim_junction import JunctionSimError, simulate_junction  # noqa: E402
from memdev.silicon import generation_bound  # noqa: E402

BASE = dict(temp_c=85.0, na=1e17, nd=1e19, tau=1e-6)


def test_zero_bias_current_negligible_and_monotonic():
    r = simulate_junction(**BASE, biases_v=[0.0, 0.25, 0.5, 1.0, 1.5])
    assert r.j_total[0] < 1e-6 * r.j_total[-1]
    assert all(b > a for a, b in zip(r.j_total[1:], r.j_total[2:]))


def test_mesh_converged():
    a = simulate_junction(**BASE, biases_v=[1.0], fine_cm=1e-7).j_total[0]
    b = simulate_junction(**BASE, biases_v=[1.0], fine_cm=1e-9).j_total[0]
    assert a == pytest.approx(b, rel=0.01)


def test_generation_below_analytic_bound_and_close_at_high_bias():
    j = simulate_junction(**BASE, biases_v=[1.5]).j_gen[0]
    bound = generation_bound(85.0, 1e17, 1e19, 1e-6, 1.5)
    assert 0.3 * bound < j <= bound


def test_generation_scales_inverse_lifetime():
    a = simulate_junction(**{**BASE, "tau": 1e-6}, biases_v=[1.0]).j_gen[0]
    b = simulate_junction(**{**BASE, "tau": 1e-7}, biases_v=[1.0]).j_gen[0]
    assert b / a == pytest.approx(10, rel=0.05)


def test_activation_energy_between_half_gap_and_gap():
    j65 = simulate_junction(**{**BASE, "temp_c": 65.0}, biases_v=[1.1]).j_total[0]
    j95 = simulate_junction(**{**BASE, "temp_c": 95.0}, biases_v=[1.1]).j_total[0]
    k = 8.617333262e-5
    ea = math.log(j95 / j65) / (1 / (k * 338.15) - 1 / (k * 368.15))
    assert 0.5 < ea < 1.2


@pytest.mark.parametrize("na,nd,temp_c,tau", [(1e16, 1e18, 0.0, 1e-3), (1e18, 1e20, 95.0, 1e-10),
                                              (1e16, 1e20, 95.0, 1e-3), (1e18, 1e18, 0.0, 1e-10)])
def test_repeated_runs_in_one_process(na, nd, temp_c, tau):
    r = simulate_junction(temp_c=temp_c, na=na, nd=nd, tau=tau, biases_v=[0.0, 1.5])
    assert r.j_total[1] > 0


def test_failure_is_wrapped_and_recoverable():
    with pytest.raises(JunctionSimError, match="수렴하지 못했습니다"):
        simulate_junction(**BASE, biases_v=[1.5], max_iterations=1)
    assert simulate_junction(**BASE, biases_v=[1.0]).j_total[0] > 0


def test_forward_bias_rejected():
    with pytest.raises(ValueError):
        simulate_junction(**BASE, biases_v=[-0.1])


def test_no_solver_output_leaks(capfd):
    simulate_junction(**BASE, biases_v=[1.0])
    out, err = capfd.readouterr()
    assert "Iteration" not in out + err and "RelError" not in out + err


def test_reach_through_is_rejected():
    # p 영역 0.5 µm에 NA = 1e16이면 1.5 V에서 공핍층이 단자에 닿는다
    with pytest.raises(ValueError, match="공핍층"):
        simulate_junction(temp_c=85.0, na=1e16, nd=1e19, tau=1e-6, biases_v=[1.5],
                          length_cm=1e-4, xj_cm=0.5e-4)


def test_default_geometry_has_room_for_lowest_doping():
    r = simulate_junction(temp_c=85.0, na=1e16, nd=1e19, tau=1e-6, biases_v=[1.5])
    assert r.j_total[0] > 0
