import os
import subprocess
import sys

import pytest

from memdev.colab import DEVSIM_MATH_LIBS

os.environ.setdefault("DEVSIM_MATH_LIBS", DEVSIM_MATH_LIBS)
HAS_DEVSIM = subprocess.run([sys.executable, "-c", "import devsim"], capture_output=True).returncode == 0
pytestmark = pytest.mark.skipif(not HAS_DEVSIM, reason="devsim not available")

from memdev.design import Design  # noqa: E402
from memdev.dram.d2 import fit_activation_energy, run_d2_sweep  # noqa: E402
from memdev.results import load_result  # noqa: E402


def test_fit_activation_energy_on_synthetic_data():
    import math
    k = 8.617333262e-5
    temps = [25.0, 65.0, 95.0]
    j = [math.exp(-0.7 / (k * (t + 273.15))) for t in temps]
    assert fit_activation_energy(temps, j) == pytest.approx(0.7, rel=1e-6)


def test_small_sweep_shape_and_cell_leak():
    d = run_d2_sweep(Design(name="t"), temps_c=(65.0, 85.0, 95.0), biases_v=(0.0, 1.1),
                     na_sweep=(1e17,), tau_sweep=(1e-6,))
    assert len(d["j_total"]) == 3 and len(d["j_total"][0]) == 2
    assert d["cell_leak_a"] == pytest.approx(d["j_total"][1][1] * 1e-11)
    assert 0.5 < d["ea_ev"] < 1.2


def test_precomputed_baseline_d2_matches_current_params(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMDEV_WORK", str(tmp_path / "work"))
    r = load_result("D2", Design(name="baseline"))
    assert r.source == "precomputed"
