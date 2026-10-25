import numpy as np
import pytest

from memdev import results
from memdev.design import Design
from memdev.results import ResultMissing, load_result, save_result


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMDEV_WORK", str(tmp_path / "work"))
    monkeypatch.setattr(results, "PRECOMPUTED_DIR", tmp_path / "precomputed")


def test_save_then_load_same_design():
    d = Design(name="t").with_overrides(cs=12e-15)
    save_result("D2", d, {"v": np.array([1.0, 2.0]), "i": 3e-15})
    r = load_result("D2", d)
    assert r.data == {"v": [1.0, 2.0], "i": 3e-15}
    assert r.design_fingerprint == d.fingerprint() and r.source == "work"


def test_load_after_design_change_reports_stale():
    save_result("D2", Design(name="t"), {"i": 1.0})
    with pytest.raises(ResultMissing) as e:
        load_result("D2", Design(name="t").with_overrides(cs=12e-15))
    assert "현재 설계안과 맞지 않습니다" in str(e.value) and "02_devsim_leakage" in str(e.value)


def test_missing_result_message():
    with pytest.raises(ResultMissing) as e:
        load_result("D2", Design(name="t"))
    assert "02_devsim_leakage" in str(e.value) and "실행" in str(e.value)


def test_precomputed_used_when_no_work_result(tmp_path, monkeypatch):
    d = Design(name="baseline")
    save_result("D2", d, {"i": 1.0})
    src = tmp_path / "work" / "results" / "D2"
    dst = tmp_path / "precomputed" / "D2"
    dst.mkdir(parents=True)
    for f in src.iterdir():
        f.rename(dst / f.name)
    r = load_result("D2", d)
    assert r.source == "precomputed" and r.data == {"i": 1.0}


def test_save_result_to_explicit_root(tmp_path):
    p = save_result("D2", Design(name="t"), {"i": 1.0}, root=tmp_path / "pc")
    assert p.parent == tmp_path / "pc" / "D2"
