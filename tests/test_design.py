import json

import pytest

from memdev.design import Design, design_table, load_design, save_design, work_dir
from memdev.params import values


@pytest.fixture(autouse=True)
def isolated_work(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMDEV_WORK", str(tmp_path / "work"))


def test_work_dir_respects_env(tmp_path):
    assert work_dir() == tmp_path / "work"
    assert work_dir().is_dir()


def test_default_design_is_baseline():
    d = load_design()
    assert d.overrides == {}
    assert d.values() == values("dram_baseline")


def test_overrides_apply_and_unknown_key_rejected():
    d = Design(name="t").with_overrides(cs=12e-15)
    assert d.values()["cs"] == 12e-15
    assert d.values()["cbl"] == values("dram_baseline")["cbl"]
    with pytest.raises(ValueError):
        Design(name="t", overrides={"no_such_param": 1.0})


def test_override_out_of_range_rejected():
    with pytest.raises(ValueError):
        Design(name="t").with_overrides(cs=1e-12)  # 허용 범위 2~30 fF 밖


def test_save_and_load_roundtrip():
    d = Design(name="my_cell", note="Cs 키움").with_overrides(cs=12e-15, ea=0.7)
    path = save_design(d)
    assert json.loads(path.read_text(encoding="utf-8"))["overrides"]["cs"] == 12e-15
    assert load_design() == d


def test_fingerprint_depends_on_values_not_name():
    a = Design(name="a").with_overrides(cs=12e-15)
    b = Design(name="b").with_overrides(cs=12e-15)
    c = Design(name="a").with_overrides(cs=13e-15)
    assert a.fingerprint() == b.fingerprint() != c.fingerprint()


def test_design_table_marks_changed_rows():
    rows = {r.key: r for r in design_table(Design(name="t").with_overrides(cs=12e-15))}
    assert rows["cs"].changed and not rows["cbl"].changed
    assert rows["cs"].base == 10e-15 and rows["cs"].current == 12e-15
    assert rows["cs"].status == "assumed" and rows["cs"].unit == "F"


def test_changes_from_base_ignores_float_noise():
    from memdev.design import changes_from_base
    got = changes_from_base({"cs": 10 * 1e-15, "cbl": 60e-15, "ea": 0.6})
    assert got == {"cbl": 60e-15}
