import pytest

from memdev.design import Design, save_design
from memdev.widgets import merge_into_current


@pytest.fixture(autouse=True)
def isolated_work(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMDEV_WORK", str(tmp_path / "work"))


def test_saving_keeps_other_overrides():
    save_design(Design(name="a").with_overrides(cs=12e-15))
    d = merge_into_current({"na": 3e17, "tau_srh": 1e-6}, name="b")
    assert d.overrides == {"cs": 12e-15, "na": 3e17}
    save_design(d)
    d2 = merge_into_current({"cs": 10e-15, "cbl": 60e-15}, name="c")
    assert d2.overrides == {"na": 3e17, "cbl": 60e-15}
