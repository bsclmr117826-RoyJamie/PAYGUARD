"""Charts for the dashboard. Pure Python: no Django, no database (section 5.3 of the design).

Each chart has a *_figure builder (used by tests) and a *_chart renderer that returns PNG bytes.
Figures are built with matplotlib's Figure class, never pyplot, so they are safe under a web server.
"""
import io

from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low"]
SEVERITY_COLORS = {"Critical": "#B3261E", "High": "#E8590C", "Medium": "#E2A400", "Low": "#3C8DAD"}
INK, MUTED, GRID, ACCENT = "#1F2A37", "#6B7686", "#E3E7ED", "#1F5F8B"
SIZE = (6.4, 3.6)      # inches; with dpi 100 the image is 640 by 360 pixels
DPI = 100


def _new_axes(title):
    fig = Figure(figsize=SIZE, dpi=DPI, layout="tight")
    ax = fig.subplots()
    ax.set_title(title, fontsize=11, color=INK, loc="left")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    ax.set_axisbelow(True)
    return fig, ax


def _no_data(fig, ax):
    ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center", va="center", color=MUTED, fontsize=12)


def _label_bars(ax, bars, values):
    for bar, value in zip(bars, values):
        ax.annotate(str(value), (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha="center", va="bottom", fontsize=9, color=INK, xytext=(0, 2), textcoords="offset points")


def _bars(title, counts, colors=None):
    fig, ax = _new_axes(title)
    labels = list(counts.keys())
    values = [int(counts[k]) for k in labels]
    if not labels:
        ax.set_xticks([])
        ax.set_yticks([])
        _no_data(fig, ax)
        return fig
    bars = ax.bar(labels, values, color=[(colors or {}).get(k, ACCENT) for k in labels], width=0.6)
    ax.set_ylim(0, max(values + [1]) * 1.2)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    _label_bars(ax, bars, values)
    if sum(values) == 0:
        _no_data(fig, ax)
    return fig


def severity_figure(counts: dict) -> Figure:
    ordered = {k: counts[k] for k in SEVERITY_ORDER if k in counts}
    ordered.update({k: v for k, v in counts.items() if k not in ordered})
    return _bars("Findings by severity", ordered, SEVERITY_COLORS)


def pillar_figure(counts: dict) -> Figure:
    fig = _bars("Findings by SITF pillar", dict(counts))
    for label in fig.axes[0].get_xticklabels():
        label.set_fontsize(8)
    return fig


def trend_figure(points: list) -> Figure:
    fig, ax = _new_axes("Risk score over time")
    if not points:
        ax.set_xticks([])
        ax.set_yticks([])
        _no_data(fig, ax)
        return fig
    scores = [int(p["score"]) for p in points]
    xs = list(range(len(points)))
    ax.plot(xs, scores, color=ACCENT, marker="o", linewidth=2)
    ax.set_xticks(xs)
    ax.set_xticklabels([p["date"] for p in points], rotation=30, ha="right")
    ax.set_ylim(0, 100)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    for x, score in zip(xs, scores):
        ax.annotate(str(score), (x, score), ha="center", va="bottom", fontsize=9, color=INK,
                    xytext=(0, 5), textcoords="offset points")
    return fig


def top_rules_figure(items: list) -> Figure:
    fig, ax = _new_axes("Most frequent rules (latest scan)")
    if not items:
        ax.set_xticks([])
        ax.set_yticks([])
        _no_data(fig, ax)
        return fig
    codes = [str(code) for code, _ in items][::-1]
    values = [int(n) for _, n in items][::-1]
    bars = ax.barh(codes, values, color=ACCENT, height=0.6)
    ax.set_xlim(0, max(values + [1]) * 1.2)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    for bar, value in zip(bars, values):
        ax.annotate(str(value), (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                    ha="left", va="center", fontsize=9, color=INK, xytext=(3, 0), textcoords="offset points")
    return fig


def _png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, facecolor="white")
    return buf.getvalue()


def severity_chart(counts: dict) -> bytes:
    return _png(severity_figure(counts))


def pillar_chart(counts: dict) -> bytes:
    return _png(pillar_figure(counts))


def trend_chart(points: list) -> bytes:
    return _png(trend_figure(points))


def top_rules_chart(items: list) -> bytes:
    return _png(top_rules_figure(items))
