"""파라미터 세트 로더. 각 값은 단위, 범위, 출처, 확인 상태를 함께 가진다."""
from dataclasses import dataclass
from importlib import resources

import yaml


@dataclass(frozen=True)
class Param:
    value: float
    unit: str
    low: float
    high: float
    source: str
    status: str  # assumed | unverified | verified


def load_params(name: str) -> dict[str, Param]:
    text = resources.files(__package__).joinpath(f"{name}.yaml").read_text(encoding="utf-8")
    raw = yaml.safe_load(text)
    # PyYAML은 '10e-15'처럼 소수점 없는 지수 표기를 문자열로 읽으므로 float로 변환한다.
    return {
        key: Param(value=float(d["value"]), unit=str(d["unit"]), low=float(d["low"]),
                   high=float(d["high"]), source=str(d["source"]), status=str(d["status"]))
        for key, d in raw.items()
    }


def values(name: str) -> dict[str, float]:
    return {key: p.value for key, p in load_params(name).items()}
