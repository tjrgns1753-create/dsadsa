"""그래프 공통 설정: 한글 폰트, 시뮬레이션 표시, 로그 눈금."""
import logging

from matplotlib import font_manager, rcParams
from matplotlib.ticker import FuncFormatter

KOREAN_FONTS = ["NanumGothic", "WenQuanYi Zen Hei", "Noto Sans CJK KR"]
_FONT_PATH_HINTS = ("nanum", "wqy", "wenquanyi", "noto")


def _installed_font_names() -> set[str]:
    return {f.name for f in font_manager.fontManager.ttflist}


def _register_system_fonts() -> None:
    """matplotlib 캐시 이후 설치된 폰트(예: Colab에서 apt로 설치한 나눔고딕)를 등록한다."""
    for path in font_manager.findSystemFonts():
        if any(hint in path.lower() for hint in _FONT_PATH_HINTS):
            try:
                font_manager.fontManager.addfont(path)
            except (OSError, RuntimeError):
                continue


def setup_korean_font() -> str | None:
    """설치된 한글 폰트를 기본 폰트로 설정하고 그 이름을 돌려준다. 없으면 None."""
    names = _installed_font_names()
    font = next((f for f in KOREAN_FONTS if f in names), None)
    if font is None:
        _register_system_fonts()
        names = _installed_font_names()
        font = next((f for f in KOREAN_FONTS if f in names), None)
    if font is None:
        return None
    rcParams["font.family"] = font
    # 일부 한글 폰트는 굵기 정보가 'normal'과 맞지 않아 findfont 경고가 반복된다. 글리프 누락 경고는
    # warnings 모듈로 나오므로 이 설정과 무관하게 계속 보인다.
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    rcParams["axes.unicode_minus"] = False
    rcParams["mathtext.fontset"] = "dejavusans"
    return font


def sim_label(param_set: str) -> str:
    return f"시뮬레이션 · 파라미터: {param_set} · 수치는 가정"


def plain_log_ticks(axis) -> None:
    """로그 축 눈금을 10^x 대신 0.001, 1, 100처럼 표시한다 (수학 글꼴 마이너스 깨짐 방지)."""
    axis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}"))
