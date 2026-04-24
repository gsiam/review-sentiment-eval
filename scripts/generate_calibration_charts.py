#!/usr/bin/env python3
"""Generate calibration score charts for docs/model-configuration-analysis.md.

Run from repo root:
    python scripts/generate_calibration_charts.py

Outputs two PNG files to docs/images/.
"""

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

THRESHOLD = 0.70
OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "images"

FAITHFUL_LABELS = ["mag-severity", "mag-precision", "scope-condition", "spec-simplification"]

UNFAITHFUL_LABELS = [
    "hallucinated",
    "negation-flip",
    "attribution-swap",
    "number-swap",
    "mag-severity",
    "mag-precision",
    "scope-condition",
    "spec-simplification",
]

# Pooled medians across SS+WS (strong judge, 6 runs) and SW+WW (weak judge, 6 runs).
# Calibration cases use pre-written summaries so the summariser plays no role;
# pooling eliminates the misleading implication that SS/WS differences are summariser-driven.
# Ranges are (min, max) for unstable entries (max−min > 0.2), None for stable ones.
CONFIGS = {
    "strong": {
        "title": "Strong Judge (claude-sonnet-4-6) — pooled median (6 runs)",
        "filename": "calibration_strong_judge.png",
        # spec-simplification: SS [1,1,0.5] + WS [1,0.5,0.5] → sorted [0.5,0.5,0.5,1,1,1] → 0.75
        "faithful_scores": [1.00, 1.00, 1.00, 0.75],
        "faithful_ranges": [None, None, None, (0.50, 1.00)],
        # mag-severity: SS [0,1,1] + WS [0,0,1] → sorted [0,0,0,1,1,1] → 0.50
        "unfaithful_scores": [0.60, 0.00, 0.00, 0.50, 0.50, 1.00, 0.50, 0.50],
        "unfaithful_ranges": [None, None, None, None, (0.00, 1.00), None, None, None],
    },
    "weak": {
        "title": "Weak Judge (ollama/mistral) — pooled median (6 runs)",
        "filename": "calibration_weak_judge.png",
        "faithful_scores": [1.00, 1.00, 1.00, 1.00],
        "faithful_ranges": [None, None, None, None],
        "unfaithful_scores": [0.60, 0.00, 0.00, 0.33, 1.00, 1.00, 1.00, 0.50],
        "unfaithful_ranges": [None, None, None, None, None, None, None, None],
    },
}

GREEN = "#4CAF50"
RED = "#E53935"
NEUTRAL = "#90A4AE"
THRESHOLD_COLOR = "#212121"
RANGE_COLOR = "#F57C00"


def _bar_colors(scores: list[float], is_faithful: bool) -> list[str]:
    if is_faithful:
        return [GREEN if s >= THRESHOLD else RED for s in scores]
    return [GREEN if s < THRESHOLD else RED for s in scores]


def _draw_subplot(
    ax: plt.Axes,
    labels: list[str],
    scores: list[float],
    ranges: list[tuple[float, float] | None],
    is_faithful: bool,
    subtitle: str,
) -> None:
    colors = _bar_colors(scores, is_faithful)
    x = np.arange(len(labels))

    # Background: shade the "correct" region
    if is_faithful:
        ax.axhspan(THRESHOLD, 1.05, alpha=0.08, color="green", zorder=0)
    else:
        ax.axhspan(0, THRESHOLD, alpha=0.08, color="green", zorder=0)

    bars = ax.bar(x, scores, color=colors, width=0.55, zorder=3, edgecolor="white", linewidth=0.5)

    # Error bars for all entries: real range for unstable, zero-height cap for stable
    yerr_lower = [s - r[0] if r else 0.0 for s, r in zip(scores, ranges)]
    yerr_upper = [r[1] - s if r else 0.0 for s, r in zip(scores, ranges)]
    ax.errorbar(
        x,
        scores,
        yerr=[yerr_lower, yerr_upper],
        fmt="none",
        ecolor=RANGE_COLOR,
        elinewidth=2,
        capsize=6,
        capthick=2,
        zorder=5,
    )

    ax.axhline(y=THRESHOLD, color=THRESHOLD_COLOR, linestyle="--", linewidth=1.5, zorder=4)

    ax.set_title(subtitle, fontsize=10, pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=8.5)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Faithfulness Score", fontsize=9)
    ax.yaxis.grid(True, linestyle=":", alpha=0.4, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)

    for bar, score in zip(bars, scores):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.03,
            f"{score:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
            color="#333333",
        )

    # Threshold label on the right edge
    ax.text(
        len(labels) - 0.5 + 0.5,
        THRESHOLD + 0.02,
        "0.70",
        ha="right",
        va="bottom",
        fontsize=8,
        color=THRESHOLD_COLOR,
    )


def generate(config_key: str) -> None:
    cfg = CONFIGS[config_key]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), gridspec_kw={"width_ratios": [1, 2]})
    fig.suptitle(cfg["title"], fontsize=12, fontweight="bold", y=1.02)

    _draw_subplot(
        ax1,
        FAITHFUL_LABELS,
        cfg["faithful_scores"],
        cfg["faithful_ranges"],
        is_faithful=True,
        subtitle="Faithful cases\n(bars should be above threshold)",
    )
    _draw_subplot(
        ax2,
        UNFAITHFUL_LABELS,
        cfg["unfaithful_scores"],
        cfg["unfaithful_ranges"],
        is_faithful=False,
        subtitle="Unfaithful cases\n(bars should be below threshold)",
    )

    legend_handles = [
        mpatches.Patch(color=GREEN, label="Correct judge behaviour"),
        mpatches.Patch(color=RED, label="Judge miss"),
        plt.Line2D([0], [0], color=THRESHOLD_COLOR, linestyle="--", linewidth=1.5, label="Threshold (0.70)"),
        plt.Line2D([0], [0], color=RANGE_COLOR, linewidth=2, label="Min–max range (unstable)"),
    ]
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        ncol=4,
        bbox_to_anchor=(0.5, -0.06),
        fontsize=9,
        frameon=False,
    )

    plt.tight_layout()
    out_path = OUT_DIR / cfg["filename"]
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generate("strong")
    generate("weak")
