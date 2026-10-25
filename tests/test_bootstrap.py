"""노트북 첫 셀의 저장소 동기화(_sync_repo)가 재실행·강제 푸시·로컬 수정에도 멈추지 않는지 확인한다."""
import ast
import os
import subprocess
from pathlib import Path

import pytest

SOURCES = sorted(Path(__file__).resolve().parents[1].joinpath("notebooks", "src").glob("*.py"))
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "init.defaultBranch=work"]


def _load_sync(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_sync_repo")
    ns = {"os": os, "subprocess": subprocess}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(path), "exec"), ns)
    return ns["_sync_repo"], ast.unparse(fn)


def _git(*args, cwd):
    subprocess.run([*GIT, *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def upstream(tmp_path):
    bare, work = tmp_path / "origin.git", tmp_path / "work"
    _git("init", "-q", "--bare", str(bare), cwd=tmp_path)
    _git("init", "-q", str(work), cwd=tmp_path)
    (work / "a.txt").write_text("1")
    _git("add", "a.txt", cwd=work)
    _git("commit", "-q", "-m", "one", cwd=work)
    _git("push", "-q", f"file://{bare}", "HEAD:work", cwd=work)
    return bare, work


def test_every_notebook_defines_the_same_sync_function():
    bodies = {_load_sync(p)[1] for p in SOURCES}
    assert len(SOURCES) >= 2 and len(bodies) == 1


@pytest.mark.parametrize("src", SOURCES, ids=lambda p: p.name)
def test_resync_survives_force_push_and_local_edit(src, upstream, tmp_path):
    sync, _ = _load_sync(src)
    bare, work = upstream
    dest = tmp_path / "clone"
    sync(str(dest), f"file://{bare}", "work")
    assert (dest / "a.txt").read_text() == "1"

    sync(str(dest), f"file://{bare}", "work")  # 그대로 재실행

    (work / "a.txt").write_text("2")
    _git("commit", "-q", "--amend", "-a", "-m", "amended", cwd=work)
    _git("push", "-q", "--force", f"file://{bare}", "HEAD:work", cwd=work)
    (dest / "a.txt").write_text("local edit")

    sync(str(dest), f"file://{bare}", "work")
    assert (dest / "a.txt").read_text() == "2"
