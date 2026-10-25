"""설계안: 기준 파라미터 세트에서 바꾼 값만 기록하고, 모든 단계(노트북)가 같은 설계안을 쓴다.

설계안 파일은 작업 폴더(work_dir)에 저장한다. Colab에서는 저장소 폴더 밖(/content/memdev_work)을 써서
첫 셀이 저장소를 최신으로 맞출 때 지워지지 않게 한다.
"""
import hashlib
import json
import math
import os
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

from memdev.params import load_params

COLAB_WORK_DIR = "/content/memdev_work"


def work_dir() -> Path:
    if "MEMDEV_WORK" in os.environ:
        path = Path(os.environ["MEMDEV_WORK"])
    elif "google.colab" in sys.modules:
        path = Path(COLAB_WORK_DIR)
    else:
        path = Path.home() / ".memdev"
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass(frozen=True)
class Design:
    name: str
    base: str = "dram_baseline"
    overrides: dict[str, float] = field(default_factory=dict)
    note: str = ""

    def __post_init__(self):
        params = load_params(self.base)
        for key, value in self.overrides.items():
            if key not in params:
                raise ValueError(f"'{key}'는 파라미터 세트 {self.base}에 없는 항목입니다")
            p = params[key]
            if not p.low <= value <= p.high:
                raise ValueError(f"{key}={value:g} {p.unit}는 허용 범위 {p.low:g}~{p.high:g} 밖입니다")

    def with_overrides(self, **changes: float) -> "Design":
        return replace(self, overrides={**self.overrides, **{k: float(v) for k, v in changes.items()}})

    def values(self) -> dict[str, float]:
        return {key: self.overrides.get(key, p.value) for key, p in load_params(self.base).items()}

    def fingerprint(self) -> str:
        """설계 값이 같으면 같은 지문. 이름과 메모는 포함하지 않는다."""
        payload = json.dumps({"base": self.base, "values": self.values()}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:12]


def changes_from_base(values: dict[str, float], base: str = "dram_baseline") -> dict[str, float]:
    """기준값과 다른 값만 고른다. 슬라이더 단위 변환에서 생기는 부동소수점 오차는 같은 값으로 본다."""
    params = load_params(base)
    return {key: float(v) for key, v in values.items()
            if not math.isclose(v, params[key].value, rel_tol=1e-9)}


def _design_path(slot: str) -> Path:
    path = work_dir() / "designs"
    path.mkdir(exist_ok=True)
    return path / f"{slot}.json"


def save_design(design: Design, slot: str = "current") -> Path:
    path = _design_path(slot)
    data = {"name": design.name, "base": design.base, "overrides": design.overrides, "note": design.note}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_design(slot: str = "current") -> Design:
    """저장된 설계안을 불러온다. 없으면 기준 설계안(바꾼 값 없음)을 돌려준다."""
    path = _design_path(slot)
    if not path.exists():
        return Design(name="baseline")
    data = json.loads(path.read_text(encoding="utf-8"))
    return Design(name=data["name"], base=data["base"], overrides=data["overrides"], note=data["note"])


@dataclass(frozen=True)
class DesignRow:
    key: str
    base: float
    current: float
    unit: str
    status: str
    source: str
    changed: bool


def design_table(design: Design) -> list[DesignRow]:
    current = design.values()
    return [DesignRow(key=key, base=p.value, current=current[key], unit=p.unit, status=p.status,
                      source=p.source, changed=key in design.overrides and current[key] != p.value)
            for key, p in load_params(design.base).items()]
