"""EDA figures. Colours follow the validated reference palette (light mode only: the
figures are static PNGs for the notebook and the presentation)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from discovery_chef.eda.codebook import THEMES_BY_KEY

if TYPE_CHECKING:
    from discovery_chef.eda.profile import EdaProfile

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
BLUE_LIGHT = "#86b6ef"  # sequential step 250
BLUE_DARK = "#1c5cab"  # sequential step 550
ACCENT = "#eb6834"  # categorical slot 2, used for emphasis
WEIGHT_CMAP = LinearSegmentedColormap.from_list("weight", ["#b7d3f6", "#104281"])

KIND_TITLES = {
    "problem": "Problems",
    "requirement": "Requirements on a solution",
    "counter_evidence": "Counter-evidence",
}


HEADER_INCHES = 0.8  # band above the plot reserved for title and subtitle


def _new_figure(width: float, height: float, title: str, subtitle: str) -> Figure:
    fig = Figure(figsize=(width, height), facecolor=SURFACE, layout="constrained")
    fig.get_layout_engine().set(rect=(0, 0, 1, 1 - HEADER_INCHES / height))
    fig.text(0.01, 1 - 0.12 / height, title, ha="left", va="top", color=INK, fontsize=13,
             fontweight="bold")
    fig.text(0.01, 1 - 0.45 / height, subtitle, ha="left", va="top", color=INK_SECONDARY,
             fontsize=9.5)
    return fig


def _style_axes(ax, *, grid_axis: str = "x") -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    ax.tick_params(colors=MUTED, labelcolor=INK_SECONDARY, length=0)
    ax.grid(axis=grid_axis, color=GRID, linewidth=1)
    ax.set_axisbelow(True)


def theme_support_chart(support: pd.DataFrame) -> Figure:
    """Dumbbell per theme: raw interview count vs evidence-weighted support."""
    kinds = [k for k in KIND_TITLES if (support["kind"] == k).any()]
    heights = [int((support["kind"] == k).sum()) for k in kinds]
    fig = _new_figure(
        9, 0.36 * len(support) + 2.2,
        "Theme support shrinks once evidence quality is weighed",
        "Weighted = sum of interview weights (quality x target fit). P06 counts 0; "
        "P07 counts 0.25.",
    )
    axes = fig.subplots(len(kinds), 1, sharex=True, gridspec_kw={"height_ratios": heights})
    for ax, kind in zip(axes, kinds, strict=True):
        df = support[support["kind"] == kind].iloc[::-1]
        y = list(range(len(df)))
        _style_axes(ax)
        for yi, raw, weighted in zip(y, df["raw_interviews"], df["weighted_support"],
                                     strict=True):
            ax.plot([weighted, raw], [yi, yi], color=BASELINE, linewidth=2,
                    solid_capstyle="round", zorder=1)
        ax.scatter(df["raw_interviews"], y, s=70, color=BLUE_LIGHT, edgecolor=SURFACE,
                   linewidth=2, zorder=2, label="Interviews mentioning it (raw count)")
        ax.scatter(df["weighted_support"], y, s=70, color=BLUE_DARK, edgecolor=SURFACE,
                   linewidth=2, zorder=3, label="Evidence-weighted support")
        ax.set_yticks(y, df["label"], fontsize=9)
        ax.set_ylim(-0.7, len(df) - 0.3)
        ax.set_title(KIND_TITLES[kind], loc="left", color=INK, fontsize=10.5, pad=4)
    axes[-1].set_xlim(0, 10.2)
    axes[-1].set_xticks(range(0, 11, 2))
    axes[-1].set_xlabel("Interviews (out of 10)", color=INK_SECONDARY)
    axes[-1].legend(loc="upper right", frameon=False, labelcolor=INK_SECONDARY, fontsize=9)
    return fig


def theme_matrix_chart(profile: EdaProfile) -> Figure:
    """Which interview raises which theme, shaded by that interview's evidence weight."""
    matrix = profile.theme_matrix
    weights = profile.metrics.set_index("interview_id")["evidence_weight"]
    rows: list[str | None] = []  # None = gap row between kinds
    for kind in KIND_TITLES:
        keys = [k for k in matrix.index if THEMES_BY_KEY[k].kind == kind]
        if keys:
            rows += ([None] if rows else []) + keys
    columns = list(matrix.columns)

    fig = _new_figure(
        10, 0.34 * len(rows) + 2.4, "Who raises which theme",
        "Filled cell = the interview mentions the theme; darker = more trustworthy and "
        "closer to the target customer.",
    )
    ax = fig.add_subplot()
    ax.set_facecolor(SURFACE)
    for spine in ax.spines.values():
        spine.set_visible(False)
    gap = 0.06  # surface gap between cells
    for r, key in enumerate(rows):
        if key is None:
            continue
        for c, iid in enumerate(columns):
            if not matrix.loc[key, iid]:
                ax.add_patch(Rectangle((c + gap, r + gap), 1 - 2 * gap, 1 - 2 * gap,
                                       facecolor=SURFACE, edgecolor=GRID, linewidth=0.8))
                continue
            weight = float(weights[iid])
            if weight == 0:
                ax.add_patch(Rectangle((c + gap, r + gap), 1 - 2 * gap, 1 - 2 * gap,
                                       facecolor=GRID, hatch="///", edgecolor=MUTED,
                                       linewidth=0))
            else:
                ax.add_patch(Rectangle((c + gap, r + gap), 1 - 2 * gap, 1 - 2 * gap,
                                       facecolor=WEIGHT_CMAP(weight), linewidth=0))
    ax.set_xlim(0, len(columns))
    ax.set_ylim(len(rows), 0)
    ax.xaxis.tick_top()
    ax.set_xticks([c + 0.5 for c in range(len(columns))],
                  [f"{iid}\n{weights[iid]:.2f}" for iid in columns], fontsize=9)
    ytick_rows = [r for r, key in enumerate(rows) if key is not None]
    ax.set_yticks([r + 0.5 for r in ytick_rows],
                  [THEMES_BY_KEY[rows[r]].label for r in ytick_rows], fontsize=9)
    ax.tick_params(colors=MUTED, labelcolor=INK_SECONDARY, length=0)
    for r, key in enumerate(rows):
        if key is None:
            next_kind = THEMES_BY_KEY[rows[r + 1]].kind
            ax.text(0, r + 0.75, KIND_TITLES[next_kind], color=INK, fontsize=10,
                    fontweight="bold", va="bottom")
    first_kind = THEMES_BY_KEY[rows[0]].kind
    ax.set_title(KIND_TITLES[first_kind], loc="left", color=INK, fontsize=10,
                 fontweight="bold", pad=34)

    colorbar = fig.colorbar(
        _scalar_mappable(), ax=ax, orientation="horizontal", fraction=0.025, pad=0.02,
        aspect=40,
    )
    colorbar.set_label("Interview evidence weight (column header). Hatched = mentioned "
                       "but excluded (P06).", color=INK_SECONDARY, fontsize=9)
    colorbar.ax.tick_params(colors=MUTED, labelcolor=INK_SECONDARY, length=0)
    colorbar.outline.set_visible(False)
    return fig


def _scalar_mappable():
    from matplotlib.cm import ScalarMappable
    from matplotlib.colors import Normalize

    return ScalarMappable(norm=Normalize(0, 1), cmap=WEIGHT_CMAP)


def competitor_freshness_chart(competitors: pd.DataFrame, stale_after_days: int) -> Figure:
    """Days since each competitor row was verified; stale rows emphasised."""
    df = competitors.dropna(subset=["days_since_verified"]).sort_values("days_since_verified")
    n_stale = int((df["freshness"] == "stale").sum())
    fig = _new_figure(
        8.5, 0.42 * len(df) + 1.8,
        f"{n_stale} of {len(df)} competitor rows were last verified over a year ago",
        "competitors.csv, measured against the last interview date.",
    )
    ax = fig.add_subplot()
    _style_axes(ax)
    colors = [ACCENT if f == "stale" else BASELINE for f in df["freshness"]]
    y = list(range(len(df)))
    ax.barh(y, df["days_since_verified"], height=0.55, color=colors)
    for yi, days, freshness in zip(y, df["days_since_verified"], df["freshness"], strict=True):
        label = f"{int(days)} days" + ("  ·  stale" if freshness == "stale" else "")
        ax.text(days + 8, yi, label, va="center", color=INK_SECONDARY, fontsize=9)
    ax.axvline(stale_after_days, color=MUTED, linewidth=1)
    ax.text(stale_after_days + 6, len(df) - 0.45, "1 year", color=MUTED, fontsize=9,
            va="bottom")
    ax.set_yticks(y, df["competitor"], fontsize=9.5)
    ax.set_xlim(0, max(df["days_since_verified"].max() * 1.22, stale_after_days * 1.3))
    ax.set_ylim(-0.6, len(df) - 0.1)
    ax.set_xlabel("Days between last_verified and the research date", color=INK_SECONDARY)
    return fig


def save_all(profile: EdaProfile, out_dir: Path) -> list[Path]:
    from discovery_chef.eda.sources import COMPETITOR_STALE_DAYS

    out_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "theme_support.png": theme_support_chart(profile.theme_support),
        "theme_matrix.png": theme_matrix_chart(profile),
        "competitor_freshness.png": competitor_freshness_chart(profile.competitors,
                                                               COMPETITOR_STALE_DAYS),
    }
    written = []
    for name, fig in figures.items():
        path = out_dir / name
        fig.savefig(path, dpi=150, facecolor=SURFACE, metadata={"Software": None})
        written.append(path)
    return written
