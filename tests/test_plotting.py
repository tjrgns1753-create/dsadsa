import warnings

import matplotlib
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from memdev.plotting import plain_log_ticks, setup_korean_font, sim_label  # noqa: E402


def test_korean_text_renders_without_missing_glyphs():
    font = setup_korean_font()
    if font is None:
        pytest.skip("no Korean font installed")
    fig, ax = plt.subplots()
    ax.set_xscale("log")
    ax.plot([1e-3, 1e3], [1, 2])
    plain_log_ticks(ax.xaxis)
    ax.set_title("셀 전압 감쇠 " + sim_label("dram_baseline"))
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        fig.canvas.draw()
    plt.close(fig)
    assert not [x for x in w if "missing from" in str(x.message) or "glyph" in str(x.message)]


def test_sim_label_mentions_simulation_and_set():
    s = sim_label("dram_baseline")
    assert "시뮬레이션" in s and "dram_baseline" in s
