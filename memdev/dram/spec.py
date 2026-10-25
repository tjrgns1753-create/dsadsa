"""D1 스펙 정의와 판정. 목표값은 설계 문서 5장 D1의 가정값이다."""
import math
from dataclasses import dataclass, replace

from memdev.dram.cell import bitline_signal, fail_voltage, retention_time
from memdev.dram.leakage import arrhenius_leakage


@dataclass(frozen=True)
class DramSpec:
    retention_min_s: float = 0.064
    retention_temp_c: float = 85.0
    signal_min_v: float = 0.05
    write_pulse_s: float = 10e-9
    write_target_frac: float = 0.95
    temp_range_c: tuple[float, float] = (0.0, 95.0)
    vdd_tolerance: float = 0.05


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    value: float
    limit: float
    margin: float  # value / limit


def _check(name: str, value: float, limit: float) -> CheckResult:
    margin = value / limit if limit else float("inf")
    # 경계값(value == limit)은 통과. 부동소수점 반올림이 판정을 뒤집지 않도록 상대 오차를 허용한다.
    passed = value >= limit or math.isclose(value, limit, rel_tol=1e-9)
    return CheckResult(name=name, passed=passed, value=value, limit=limit, margin=margin)


def check_retention(t_ret_s: float, spec: DramSpec) -> CheckResult:
    return _check("리텐션", t_ret_s, spec.retention_min_s)


def check_signal(dv_v: float, spec: DramSpec) -> CheckResult:
    return _check("읽기 신호", dv_v, spec.signal_min_v)


def spec_table(spec: DramSpec) -> list[tuple[str, str, str]]:
    low, high = spec.temp_range_c
    return [
        ("리텐션",
         f"{spec.retention_temp_c:g}°C에서 {spec.retention_min_s * 1e3:g} ms 이상 (예비 셀 수리 후, 칩 기준)",
         "리프레시 주기 안에 데이터 유지"),
        ("읽기 신호", f"비트라인 신호 ≥ {spec.signal_min_v * 1e3:g} mV",
         "센스앰프가 구분할 수 있는 최소 신호"),
        ("쓰기",
         f"쓰기 펄스 {spec.write_pulse_s * 1e9:g} ns 안에 셀 전압이 목표의 {spec.write_target_frac:.0%} 도달",
         "접근 트랜지스터가 충분히 켜짐"),
        ("동작 조건", f"{low:g}~{high:g}°C, 전원 ±{spec.vdd_tolerance:.0%}", "코너 검증 범위"),
        ("수리 한도", "가정 1000셀 (근거 미확인, D6 민감도)", "수율 판정 기준"),
    ]


@dataclass(frozen=True)
class CellEvaluation:
    v_fail: float
    signal_v: float  # 가득 찬 셀을 읽을 때의 비트라인 신호
    readable: bool  # 가득 찬 셀의 신호가 최소 감지값 이상인가
    retention_now_s: float  # temp_c에서의 리텐션
    retention_spec_s: float  # 스펙 온도에서의 리텐션
    signal: CheckResult
    retention: CheckResult


def evaluate_cell(*, cs: float, cbl: float, vdd: float, sense_min: float, i_ref: float,
                  t_ref_c: float, ea_ev: float, temp_c: float, spec: DramSpec) -> CellEvaluation:
    """셀 설계 하나를 스펙에 대해 판정한다.

    읽기 신호는 주어진 sense_min(센스앰프의 최소 감지값)을 기준으로 판정하고, 읽기 가능 여부도 같은 판정을 쓴다.
    """
    signal_v = float(bitline_signal(vdd, vdd, cs, cbl))
    signal = check_signal(signal_v, replace(spec, signal_min_v=sense_min))
    v_fail = fail_voltage(vdd, cs, cbl, sense_min)

    def ret(t_c: float) -> float:
        if not signal.passed:
            return 0.0
        return retention_time(vdd, v_fail, arrhenius_leakage(t_c, i_ref, t_ref_c, ea_ev), cs)

    retention_spec_s = ret(spec.retention_temp_c)
    return CellEvaluation(v_fail=v_fail, signal_v=signal_v, readable=signal.passed,
                          retention_now_s=ret(temp_c), retention_spec_s=retention_spec_s,
                          signal=signal, retention=check_retention(retention_spec_s, spec))
