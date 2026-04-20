#!/usr/bin/env python3
"""Generate §3.4 stacked bar chart for docs/model-configuration-analysis.md.

Run from repo root:
    python scripts/generate_stacked_bar.py

Outputs: docs/images/stacked_bar_failure_counts.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "images"

CONFIGS = ["SS", "SW", "WS", "WW"]

# Failed observations per config per assertion type (from §3.4 table)
CATEGORIES = [
    "Normal faith (n=16)",
    "Sentiment (n=16)",
    "Conflicting (n=10)",
    "Adv faith (n=6)",
    "Adv robust (n=6)",
    "Calib (n=12)",
]

DATA = {
    #                        SS   SW   WS   WW
    "Normal faith (n=16)":  [0,   1,   4,   3],
    "Sentiment (n=16)":     [3,   3,   6,   6],
    "Conflicting (n=10)":   [0,   0,   9,   9],
    "Adv faith (n=6)":      [0,   4,   3,   9],
    "Adv robust (n=6)":     [0,   0,   6,   6],
    "Calib (n=12)":         [6,   9,   6,   9],
}

COLORS = ["#4e9a8a", "#e07b39", "#c94040", "#5b7ec2", "#8e5bb5", "#aaaaaa"]
TOTALS = [9, 17, 34, 42]


def main() -> None:
    """Render and save the §3.4 stacked bar chart."""
    x = np.arange(len(CONFIGS))
    bar_width = 0.5

    fig, ax = plt.subplots(figsize=(5, 4))

    bottoms = np.zeros(len(CONFIGS))
    for cat, color in zip(CATEGORIES, COLORS):
        values = np.array(DATA[cat], dtype=float)
        ax.bar(x, values, bar_width, bottom=bottoms, label=cat, color=color)
        bottoms += values

    # Total labels above each bar
    for xi, total in zip(x, TOTALS):
        ax.text(xi, total + 0.5, str(total), ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(CONFIGS, fontsize=9, fontweight="bold")
    ax.set_ylabel("Failed observations", fontsize=8)
    ax.set_ylim(0, 50)
    ax.set_title("Failure counts by config and assertion type\n(per-observation, 3 runs)", fontsize=8)

    ax.legend(
        loc="upper left",
        fontsize=7,
        framealpha=0.85,
        edgecolor="none",
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", labelsize=7)

    plt.tight_layout()
    out_path = OUT_DIR / "stacked_bar_failure_counts.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    main()
