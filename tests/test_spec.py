import pytest

from memdev.dram.spec import DramSpec, check_retention, check_signal, spec_table

S = DramSpec()


def test_retention_pass_with_margin():
    r = check_retention(1.0, S)
    assert r.passed and r.margin == pytest.approx(1.0 / 0.064)


def test_retention_fail_and_zero_retention():
    assert not check_retention(0.05, S).passed
    assert not check_retention(0.0, S).passed


def test_signal_check():
    assert check_signal(0.0917, S).passed
    assert not check_signal(0.03, S).passed


def test_spec_table_has_five_rows_in_korean():
    rows = spec_table(S)
    assert [r[0] for r in rows] == ["리텐션", "읽기 신호", "쓰기", "동작 조건", "수리 한도"]


from memdev.dram.spec import evaluate_cell  # noqa: E402

BASE = dict(cs=10e-15, cbl=50e-15, vdd=1.1, sense_min=0.05, i_ref=2.5e-15, t_ref_c=85.0,
            ea_ev=0.6, temp_c=85.0, spec=S)


def test_evaluate_cell_baseline_passes():
    ev = evaluate_cell(**BASE)
    assert ev.readable and ev.signal.passed and ev.retention.passed
    assert ev.retention_spec_s == pytest.approx(1.0)


def test_evaluate_cell_small_cs_unreadable():
    ev = evaluate_cell(**{**BASE, "cs": 2e-15})
    assert not ev.readable and not ev.signal.passed
    assert ev.retention_now_s == 0.0 and not ev.retention.passed


@pytest.mark.parametrize("cs_fF", [2, 3, 4, 5, 6])
def test_readability_and_signal_verdict_agree_at_boundary(cs_fF):
    # Cbl = 10*Cs이면 가득 찬 셀의 신호가 정확히 50 mV (최소 감지값과 같음)
    ev = evaluate_cell(**{**BASE, "cs": cs_fF * 1e-15, "cbl": 10 * cs_fF * 1e-15})
    assert ev.readable == ev.signal.passed
    assert ev.readable


def test_signal_judged_against_slider_sense_min():
    ev = evaluate_cell(**{**BASE, "sense_min": 0.1})
    assert not ev.readable and not ev.signal.passed
