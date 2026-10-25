"""기준 설계안의 단계 결과를 미리 계산해 memdev/precomputed/에 넣는다.

파라미터 YAML을 바꾸면 기준 설계안의 지문이 바뀌므로 이 스크립트를 다시 실행해야 한다
(tests/devsim/test_d2.py::test_precomputed_baseline_d2_matches_current_params가 확인한다).
"""
from memdev.design import Design
from memdev.dram.d2 import run_d2_sweep
from memdev.results import PRECOMPUTED_DIR, save_result


def main() -> None:
    design = Design(name="baseline")
    folder = PRECOMPUTED_DIR / "D2"
    if folder.exists():
        for old in folder.glob("*.json"):
            old.unlink()
    path = save_result("D2", design, run_d2_sweep(design), root=PRECOMPUTED_DIR)
    print(f"D2 → {path}")


if __name__ == "__main__":
    main()
