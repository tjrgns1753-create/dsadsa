"""실리콘 물성 해석식: 밴드갭, 진성 캐리어 농도, 내장 전위, 공핍층 폭, SRH 생성 전류 상한.

단위 예외: 반도체 관례와 DEVSIM에 맞춰 농도는 cm^-3, 길이는 cm, 전류밀도는 A/cm²다. 온도는 °C로 받는다.
물성 상수 출처: Sze & Ng, Physics of Semiconductor Devices 3판 (기억에 의존, 원문 미확인).
"""
import math

from memdev.units import K_B_EV, Q, celsius_to_kelvin

EPS_SI = 11.7 * 8.8541878128e-14  # 실리콘 유전율 [F/cm]
NC_300 = 2.86e19  # 전도대 유효 상태 밀도, 300 K [cm^-3]
NV_300 = 3.10e19  # 가전자대 유효 상태 밀도, 300 K [cm^-3]
EG0, ALPHA, BETA = 1.17, 4.73e-4, 636.0  # Varshni 밴드갭 계수 [eV, eV/K, K]


def _require_positive(**kwargs) -> None:
    for name, value in kwargs.items():
        if value <= 0:
            raise ValueError(f"{name} must be positive, got {value}")


def bandgap_ev(temp_c: float) -> float:
    t = celsius_to_kelvin(temp_c)
    return EG0 - ALPHA * t * t / (t + BETA)


def ni_silicon(temp_c: float) -> float:
    t = celsius_to_kelvin(temp_c)
    nc_nv = NC_300 * NV_300 * (t / 300.0) ** 3
    return math.sqrt(nc_nv) * math.exp(-bandgap_ev(temp_c) / (2 * K_B_EV * t))


def built_in_potential(temp_c: float, na: float, nd: float) -> float:
    _require_positive(na=na, nd=nd)
    ni = ni_silicon(temp_c)
    return K_B_EV * celsius_to_kelvin(temp_c) * math.log(na * nd / ni**2)


def depletion_width_cm(temp_c: float, na: float, nd: float, reverse_v: float) -> float:
    if reverse_v < 0:
        raise ValueError(f"reverse_v must be >= 0 (순방향 미지원), got {reverse_v}")
    vbi = built_in_potential(temp_c, na, nd)
    return math.sqrt(2 * EPS_SI * (vbi + reverse_v) / Q * (1 / na + 1 / nd))


def generation_bound(temp_c: float, na: float, nd: float, tau: float, reverse_v: float) -> float:
    """공핍층 전체에서 최대 생성률 ni/(2τ)를 가정한 SRH 생성 전류밀도 상한 [A/cm²]."""
    _require_positive(tau=tau)
    return Q * ni_silicon(temp_c) * depletion_width_cm(temp_c, na, nd, reverse_v) / (2 * tau)
