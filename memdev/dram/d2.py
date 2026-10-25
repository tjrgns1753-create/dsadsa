"""D2 스윕: 설계안의 접합 파라미터로 온도×바이어스, 도핑·수명 민감도를 계산하고 활성화 에너지를 맞춘다."""
from collections.abc import Sequence

import numpy as np

from memdev.design import Design
from memdev.dram.devsim_junction import simulate_junction
from memdev.units import K_B_EV, celsius_to_kelvin

D2_TEMPS_C = (0.0, 25.0, 45.0, 65.0, 85.0, 95.0)
D2_BIASES_V = (0.0, 0.25, 0.5, 0.75, 1.0, 1.1, 1.25, 1.5)
D2_REF = {"temp_c": 85.0, "bias_v": 1.1}
NA_SWEEP = (1e16, 3e16, 1e17, 3e17, 1e18)
TAU_SWEEP = (1e-9, 1e-8, 1e-7, 1e-6, 1e-5)
EA_FIT_MIN_C = 65.0


def fit_activation_energy(temps_c: Sequence[float], j: Sequence[float]) -> float:
    """ln J 대 1/(kT) 직선의 기울기 부호를 바꾼 값 [eV]."""
    x = 1.0 / (K_B_EV * np.asarray(celsius_to_kelvin(np.asarray(temps_c, dtype=float))))
    slope = np.polyfit(x, np.log(np.asarray(j, dtype=float)), 1)[0]
    return float(-slope)


def run_d2_sweep(design: Design, temps_c: Sequence[float] = D2_TEMPS_C,
                 biases_v: Sequence[float] = D2_BIASES_V, na_sweep: Sequence[float] = NA_SWEEP,
                 tau_sweep: Sequence[float] = TAU_SWEEP) -> dict:
    temps_c, biases_v = [float(t) for t in temps_c], [float(v) for v in biases_v]
    if D2_REF["temp_c"] not in temps_c or D2_REF["bias_v"] not in biases_v:
        raise ValueError(f"기준 조건 {D2_REF}이 스윕에 포함돼야 합니다")
    p = design.values()
    junction = dict(na=p["na"], nd=p["nd"], tau=p["tau_srh"])

    runs = [simulate_junction(temp_c=t, biases_v=biases_v, **junction) for t in temps_c]
    i_t, i_v = temps_c.index(D2_REF["temp_c"]), biases_v.index(D2_REF["bias_v"])

    hot = [(t, r.j_total[i_v]) for t, r in zip(temps_c, runs) if t >= EA_FIT_MIN_C]
    if len(hot) < 2:
        raise ValueError(f"활성화 에너지 맞춤에 {EA_FIT_MIN_C:g}°C 이상 온도가 2개 이상 필요합니다")

    def ref_point(**override) -> float:
        args = {**junction, **override}
        return simulate_junction(temp_c=D2_REF["temp_c"], biases_v=[D2_REF["bias_v"]], **args).j_total[0]

    return {
        "temps_c": temps_c,
        "biases_v": biases_v,
        "j_total": [r.j_total for r in runs],
        "j_gen": [r.j_gen for r in runs],
        "j_diff": [r.j_diff for r in runs],
        "na_sweep": {"na": list(na_sweep), "j_total": [ref_point(na=na) for na in na_sweep]},
        "tau_sweep": {"tau": list(tau_sweep), "j_total": [ref_point(tau=tau) for tau in tau_sweep]},
        "ea_ev": fit_activation_energy([t for t, _ in hot], [j for _, j in hot]),
        "cell_leak_a": runs[i_t].j_total[i_v] * p["j_area"],
        "ref": dict(D2_REF),
        "params": {"na": p["na"], "nd": p["nd"], "tau_srh": p["tau_srh"], "j_area": p["j_area"]},
    }
