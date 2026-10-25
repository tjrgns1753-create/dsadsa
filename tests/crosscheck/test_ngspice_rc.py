import math

import pytest

from memdev.ngspice import has_ngspice, parse_meas, run_batch

requires_ngspice = pytest.mark.skipif(not has_ngspice(), reason="ngspice not installed")

RC = """* RC leak
C1 n1 0 10f IC=1.1
R1 n1 0 1e14
.tran 1m 2 UIC
.control
run
meas tran t_fail WHEN v(n1)=0.85 FALL=1
quit
.endc
.end
"""


@requires_ngspice
def test_rc_decay_matches_analytic():
    t = parse_meas(run_batch(RC), "t_fail")
    assert t == pytest.approx(math.log(1.1 / 0.85) * 1.0, rel=0.01)


def test_parse_meas_missing_raises():
    with pytest.raises(KeyError):
        parse_meas("no measurements here", "t_fail")
