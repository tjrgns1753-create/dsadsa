"""Colab과 로컬 환경 준비: ngspice, DEVSIM, 한글 폰트.

몇 번을 실행해도 되며, 예외를 던지지 않고 상태만 돌려준다.
"""
import ctypes.util
import os
import shutil
import subprocess
import sys

from memdev.ngspice import has_ngspice
from memdev.plotting import setup_korean_font

DEVSIM_MATH_LIBS = "libopenblas.so.0:liblapack.so.3:libblas.so.3"
DEVSIM_VERSION = "2.11.2"


def _devsim_ok() -> bool:
    # 현재 프로세스가 import 실패로 오염되지 않도록 별도 프로세스에서 확인한다.
    try:
        proc = subprocess.run([sys.executable, "-c", "import devsim"], capture_output=True,
                              timeout=120, env=os.environ.copy())
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def _run_quiet(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, capture_output=True, timeout=900)
    except (OSError, subprocess.TimeoutExpired):
        pass


def _install_missing() -> None:
    apt_packages = []
    if not has_ngspice():
        apt_packages.append("ngspice")
    if ctypes.util.find_library("openblas") is None:
        apt_packages += ["libopenblas0", "liblapack3"]
    if setup_korean_font() is None:
        apt_packages.append("fonts-nanum")
    if apt_packages and shutil.which("apt-get"):
        _run_quiet(["apt-get", "-qq", "update"])
        _run_quiet(["apt-get", "-qq", "install", "-y", *apt_packages])
    if not _devsim_ok():
        _run_quiet([sys.executable, "-m", "pip", "install", "-q", f"devsim=={DEVSIM_VERSION}"])


def setup(install: bool = True) -> dict[str, bool]:
    os.environ["DEVSIM_MATH_LIBS"] = DEVSIM_MATH_LIBS
    if install:
        _install_missing()
    return {
        "ngspice": has_ngspice(),
        "devsim": _devsim_ok(),
        "korean_font": setup_korean_font() is not None,
    }
