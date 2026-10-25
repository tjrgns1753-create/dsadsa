"""셀 누설 전류의 온도 의존 (M1 단순 모델).

누설 경로별 분해(서브스레숄드, 접합, GIDL)는 M2~M3에서 DEVSIM 결과와 함께 다룬다.
"""
import numpy as np

from memdev.units import K_B_EV, celsius_to_kelvin


def arrhenius_leakage(temp_c, i_ref: float, t_ref_c: float, ea_ev: float):
    """기준 온도 t_ref_c에서 i_ref인 누설이 활성화 에너지 ea_ev로 온도에 따라 변하는 값."""
    if i_ref <= 0:
        raise ValueError(f"i_ref must be positive, got {i_ref}")
    t, t_ref = celsius_to_kelvin(temp_c), celsius_to_kelvin(t_ref_c)
    i = i_ref * np.exp(-ea_ev / K_B_EV * (1 / np.asarray(t) - 1 / t_ref))
    return i if np.ndim(i) else float(i)
