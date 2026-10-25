"""DRAM 1T1C 셀의 기본 물리: 전하 분배, 읽기 실패 전압, 누설에 의한 감쇠, 리텐션.

M1 단계의 단순 모델이다. 누설 전류는 셀 전압과 무관하게 일정하다고 근사한다.
"""
import numpy as np


def _require_positive(**kwargs) -> None:
    for name, value in kwargs.items():
        if np.any(np.asarray(value) <= 0):
            raise ValueError(f"{name} must be positive, got {value}")


def bitline_signal(v_cell, vdd: float, cs: float, cbl: float):
    """읽을 때 비트라인에 나타나는 신호 (Vdd/2로 프리차지된 비트라인과 전하 분배)."""
    _require_positive(cs=cs, cbl=cbl)
    return (np.asarray(v_cell, dtype=float) - vdd / 2) * cs / (cs + cbl)


def fail_voltage(vdd: float, cs: float, cbl: float, sense_min: float) -> float:
    """비트라인 신호가 sense_min이 되는 셀 전압. 이 아래로 떨어지면 '1'을 못 읽는다."""
    _require_positive(cs=cs, cbl=cbl, sense_min=sense_min)
    return vdd / 2 + sense_min * (cs + cbl) / cs


def cell_voltage(t_s, v0: float, i_leak, cs: float):
    """일정 전류 누설 근사에서 시간에 따른 셀 전압. 0 V 아래로는 내려가지 않는다."""
    _require_positive(i_leak=i_leak, cs=cs)
    v = np.maximum(v0 - np.asarray(i_leak) * np.asarray(t_s, dtype=float) / cs, 0.0)
    return v if v.ndim else float(v)


def retention_time(v0: float, v_fail: float, i_leak, cs: float):
    """셀 전압이 v0에서 v_fail까지 떨어지는 시간. v_fail >= v0이면 처음부터 읽을 수 없으므로 0."""
    _require_positive(i_leak=i_leak, cs=cs)
    t = np.where(v_fail >= v0, 0.0, cs * (v0 - v_fail) / np.asarray(i_leak, dtype=float))
    return t if t.ndim else float(t)
