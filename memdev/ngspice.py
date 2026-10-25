"""ngspice 배치 실행과 .meas 결과 파싱."""
import os
import re
import shutil
import subprocess
import tempfile


def has_ngspice() -> bool:
    return shutil.which("ngspice") is not None


def run_batch(netlist: str, timeout_s: float = 120) -> str:
    """넷리스트를 배치 모드로 실행하고 stdout을 돌려준다."""
    if not has_ngspice():
        raise RuntimeError("ngspice not found")
    with tempfile.NamedTemporaryFile("w", suffix=".cir", delete=False) as f:
        f.write(netlist)
        path = f.name
    try:
        proc = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True,
                              timeout=timeout_s)
    finally:
        os.unlink(path)
    if proc.returncode != 0:
        raise RuntimeError(f"ngspice failed (exit {proc.returncode}): {proc.stderr.strip()}")
    return proc.stdout


def parse_meas(stdout: str, name: str) -> float:
    match = re.search(rf"^\s*{re.escape(name)}\s*=\s*([-+0-9.eE]+)", stdout, re.MULTILINE)
    if match is None:
        raise KeyError(name)
    return float(match.group(1))
