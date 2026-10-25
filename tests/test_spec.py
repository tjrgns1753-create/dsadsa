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
