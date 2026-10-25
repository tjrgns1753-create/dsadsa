from memdev.params import load_params, values

REQUIRED = {"cs", "cbl", "vdd", "sense_min", "i_leak_ref", "t_ref_c", "ea",
            "t_refresh", "write_pulse", "repair_limit"}


def test_baseline_has_required_keys():
    assert REQUIRED <= set(load_params("dram_baseline"))


def test_every_param_well_formed():
    for name, p in load_params("dram_baseline").items():
        assert p.status in {"assumed", "unverified", "verified"}, name
        assert p.unit, name
        assert p.source, name
        assert p.low <= p.value <= p.high, name


def test_values_returns_floats():
    v = values("dram_baseline")
    assert v["cs"] == 10e-15 and v["vdd"] == 1.1
