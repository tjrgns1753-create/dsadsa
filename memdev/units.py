"""물리 상수와 단위 변환. 내부 단위는 SI, 온도는 API에서 °C."""
import numpy as np

K_B_EV = 8.617333262e-5  # 볼츠만 상수 [eV/K]
Q = 1.602176634e-19  # 기본 전하 [C]


def celsius_to_kelvin(t_c):
    """°C → K. 절대영도 미만이면 ValueError."""
    t_k = np.asarray(t_c, dtype=float) + 273.15
    if np.any(t_k < 0):
        raise ValueError(f"temperature below absolute zero: {t_c} °C")
    return t_k if t_k.ndim else float(t_k)
