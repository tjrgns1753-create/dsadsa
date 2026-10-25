"""단계 결과 저장과 불러오기. 결과마다 어떤 설계안(지문)으로 계산했는지 기록한다.

불러올 때는 작업 폴더의 결과를 먼저 찾고, 없으면 저장소에 미리 계산해 둔 결과(PRECOMPUTED_DIR)를 찾는다.
현재 설계안과 맞는 결과가 없으면 어느 노트북을 다시 실행해야 하는지 알려 준다.
"""
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from memdev import __version__
from memdev.design import Design, work_dir

PRECOMPUTED_DIR = Path(__file__).parent / "precomputed"

STEP_NOTEBOOK = {
    "D2": "02_devsim_leakage",
    "D3": "03_model_extraction",
    "D4": "04_spice_cell",
    "D5": "05_doe_variation",
    "D6": "05_doe_variation",
    "D7": "06_design_refresh",
}


class ResultMissing(LookupError):
    pass


@dataclass(frozen=True)
class Result:
    step: str
    design_fingerprint: str
    data: dict
    source: str  # "work" | "precomputed"


def _to_json(obj):
    if hasattr(obj, "tolist"):
        return obj.tolist()
    raise TypeError(f"JSON으로 저장할 수 없는 값: {type(obj).__name__}")


def save_result(step: str, design: Design, data: dict, root: Path | None = None) -> Path:
    """결과를 root/step/<지문>.json에 저장한다. root가 없으면 작업 폴더의 results/."""
    folder = (work_dir() / "results" if root is None else Path(root)) / step
    folder.mkdir(parents=True, exist_ok=True)
    record = {
        "step": step,
        "design_name": design.name,
        "design_fingerprint": design.fingerprint(),
        "design_values": design.values(),
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "memdev_version": __version__,
        "data": data,
    }
    path = folder / f"{design.fingerprint()}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=1, default=_to_json), encoding="utf-8")
    return path


def load_result(step: str, design: Design) -> Result:
    name = f"{design.fingerprint()}.json"
    for source, root in (("work", work_dir() / "results"), ("precomputed", PRECOMPUTED_DIR)):
        path = root / step / name
        if path.exists():
            record = json.loads(path.read_text(encoding="utf-8"))
            return Result(step=step, design_fingerprint=record["design_fingerprint"],
                          data=record["data"], source=source)
    notebook = STEP_NOTEBOOK.get(step, step)
    others = [p for root in (work_dir() / "results", PRECOMPUTED_DIR) for p in (root / step).glob("*.json")]
    if others:
        raise ResultMissing(f"{step} 결과가 현재 설계안과 맞지 않습니다. {notebook} 노트북을 다시 실행하세요.")
    raise ResultMissing(f"{step} 결과가 없습니다. {notebook} 노트북을 먼저 실행하세요.")
