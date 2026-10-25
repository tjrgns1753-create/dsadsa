"""D1 스펙 정의와 판정. 목표값은 설계 문서 5장 D1의 가정값이다."""
from dataclasses import dataclass


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
    return CheckResult(name=name, passed=value >= limit, value=value, limit=limit, margin=margin)


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
