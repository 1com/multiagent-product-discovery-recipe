"""Evaluation figure: quality against cost, one dot per brief.

Scatter plots can carry at most three hues before some pairs become hard to tell apart,
so the five conditions use two hues (blue = single prompt, orange = agents), two fills
(hollow = without the improvement, filled = with it) and three shapes (circle = no critic,
diamond = single prompt with the critic, square = agents), plus direct labels.
"""

from __future__ import annotations

import pandas as pd
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from discovery_chef.eda.charts import (
    BASELINE,
    GRID,
    INK,
    INK_SECONDARY,
    MUTED,
    SURFACE,
    _new_figure,
)
from discovery_chef.eval.collect import CONDITION_LABELS, CONDITIONS

BLUE, ORANGE = "#2a78d6", "#eb6834"  # categorical slots 1 and 2 of the validated palette
CONDITION_STYLE = {  # condition: (hue, marker, filled)
    "naive": (BLUE, "o", False),
    "informed": (BLUE, "o", True),
    "informed_critic": (BLUE, "D", True),
    "agents_draft": (ORANGE, "s", False),
    "agents": (ORANGE, "s", True),
}


def quality_vs_cost(scores: pd.DataFrame) -> Figure:
    data = scores.dropna(subset=["quality_index"])
    fig = _new_figure(
        9, 5.6, "Quality per brief against what it cost",
        "Small marks are single briefs; large marks are condition means. Cost axis is "
        "logarithmic.",
    )
    ax = fig.add_subplot()
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(BASELINE)
    ax.grid(color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, labelcolor=INK_SECONDARY, length=0)

    for condition in CONDITIONS:
        group = data[data["condition"] == condition]
        if group.empty:
            continue
        hue, marker, filled = CONDITION_STYLE[condition]
        face = hue if filled else SURFACE
        ax.scatter(group["cost_usd"], group["quality_index"], s=40, marker=marker,
                   facecolor=face, edgecolor=hue, linewidth=1.5, alpha=0.7, zorder=2)
        mean_cost, mean_quality = group["cost_usd"].mean(), group["quality_index"].mean()
        ax.scatter([mean_cost], [mean_quality], s=150, marker=marker, facecolor=face,
                   edgecolor=hue, linewidth=2.5, zorder=3, label=CONDITION_LABELS[condition])
        ax.annotate(CONDITION_LABELS[condition], (mean_cost, mean_quality),
                    xytext=(11, -4), textcoords="offset points", color=INK_SECONDARY,
                    fontsize=9)

    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:g}"))
    ax.set_xlabel("Cost per brief (USD, list price)", color=INK_SECONDARY)
    ax.set_ylabel("Quality index (0-1)", color=INK_SECONDARY)
    ax.set_ylim(max(0.0, data["quality_index"].min() - 0.1),
                min(1.0, data["quality_index"].max() + 0.08))
    ax.legend(loc="lower right", frameon=False, labelcolor=INK, fontsize=9)
    return fig
