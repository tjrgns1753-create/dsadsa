"""노트북들이 함께 쓰는 설계안 저장 패널.

각 노트북은 자기가 다루는 파라미터만 넘기고, 다른 노트북에서 바꾼 값은 그대로 유지된다.
"""
from collections.abc import Callable

import ipywidgets as w

from memdev.design import Design, changes_from_base, load_design, save_design


def merge_into_current(values: dict[str, float], name: str) -> Design:
    """현재 설계안에 values를 반영한다. values에 없는 키의 바꾼 값은 유지하고, values의 키는
    기준값과 비교해 다시 정한다(기준값으로 돌아간 키는 바꾼 값 목록에서 빠진다)."""
    current = load_design()
    kept = {k: v for k, v in current.overrides.items() if k not in values}
    return Design(name=name, base=current.base, overrides={**kept, **changes_from_base(values)},
                  note=current.note)


def design_save_panel(get_values: Callable[[], dict[str, float]], default_name: str) -> w.VBox:
    name_box = w.Text(value=default_name, description="설계안 이름")
    save_btn = w.Button(description="현재 설계안으로 저장", button_style="primary")
    reset_btn = w.Button(description="기준값으로 되돌리기")
    download_btn = w.Button(description="설계안 파일 내려받기")
    msg = w.Output()

    def on_save(_):
        with msg:
            msg.clear_output()
            design = merge_into_current(get_values(), name=name_box.value.strip() or "my_design")
            path = save_design(design)
            print(f"저장했습니다: {design.name} (바꾼 항목: {list(design.overrides) or '없음'}) → {path}")
            print("다음 노트북은 이 설계안을 씁니다. 이 노트북 위쪽 그래프에 반영하려면 '런타임 → 모두 실행'을 누르세요.")

    def on_reset(_):
        # 이 노트북이 다루는 항목만 기준값으로 돌린다. 다른 노트북에서 바꾼 값은 유지한다.
        with msg:
            msg.clear_output()
            keys = list(get_values())
            current = load_design()
            base = Design(name="baseline", base=current.base).values()
            design = merge_into_current({k: base[k] for k in keys}, name=current.name)
            save_design(design)
            print(f"이 노트북의 항목({', '.join(keys)})을 기준값으로 되돌렸습니다. "
                  f"다른 노트북에서 바꾼 항목은 유지합니다: {list(design.overrides) or '없음'}")
            print("'런타임 → 모두 실행'을 누르면 슬라이더도 기준값으로 돌아갑니다.")

    def on_download(_):
        with msg:
            msg.clear_output()
            path = save_design(load_design())
            try:
                from google.colab import files
                files.download(str(path))
            except ImportError:
                print(f"Colab이 아니므로 파일 위치만 알려 드립니다: {path}")

    save_btn.on_click(on_save)
    reset_btn.on_click(on_reset)
    download_btn.on_click(on_download)
    return w.VBox([w.HBox([name_box, save_btn, reset_btn, download_btn]), msg])
