#!/usr/bin/env python3
"""Generate §2a faithfulness heatmap for docs/model-configuration-analysis.md.

Run from repo root:
    python scripts/generate_heatmap.py

Outputs: docs/images/heatmap_normal_faithfulness.png
"""

from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np

THRESHOLD = 0.70
OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "images"

CONFIGS = ["SS", "SW", "WS", "WW"]

# Each row: (label, SS, SW, WS, WW, unstable_col_indices)
# Scores are medians across 3 runs.
# unstable = max−min > 0.2 for that cell.
CASES: list[tuple[str, float, float, float, float, set[int]]] = [
    ("positive_baseline",                1.00, 1.00, 1.00, 1.00, set()),
    ("negative_baseline",                0.88, 1.00, 1.00, 1.00, set()),
    ("neutral_baseline",                 1.00, 1.00, 1.00, 1.00, set()),
    ("negative_conflicting_logistics",   1.00, 1.00, 1.00, 1.00, set()),
    ("positive_conflicting_logistics",   1.00, 0.83, 1.00, 1.00, set()),
    ("negative_conflicting_borderline",  0.90, 1.00, 1.00, 1.00, set()),
    ("negative_numeric_shortfall",       1.00, 1.00, 0.80, 1.00, set()),
    ("negative_attribution_multiparty",  1.00, 1.00, 1.00, 0.75, set()),
    ("positive_negation_double",         1.00, 0.80, 1.00, 0.67, {2}),  # WS unstable
    ("negative_negation_rhetorical",     1.00, 1.00, 1.00, 1.00, set()),
    ("negative_distractor_delayed_failure", 1.00, 1.00, 1.00, 1.00, set()),
    ("negative_timeline_shipping",       0.71, 1.00, 1.00, 1.00, set()),
    ("negative_conflicting_noise",       1.00, 1.00, 0.86, 1.00, set()),
    ("positive_conflicting_override",    0.89, 1.00, 1.00, 0.80, set()),
    ("positive_conflicting_conditional", 1.00, 1.00, 1.00, 1.00, {1}),  # SW unstable
    ("negative_sarcasm",                 0.71, 0.75, 0.00, 1.00, {1}),   # SW unstable
]


def main() -> None:
    row_labels = [row[0] for row in CASES]
    scores = np.array([[row[1], row[2], row[3], row[4]] for row in CASES], dtype=float)
    unstable = [row[5] for row in CASES]

    n_rows, n_cols = scores.shape

    norm = mcolors.TwoSlopeNorm(vmin=0.0, vcenter=THRESHOLD, vmax=1.0)
    cmap = plt.get_cmap("RdYlGn")

    fig, ax = plt.subplots(figsize=(5, 8))
    im = ax.imshow(scores, cmap=cmap, norm=norm, aspect="auto")

    cbar = fig.colorbar(im, ax=ax, pad=0.02, fraction=0.046)
    cbar.set_label("Faithfulness score (median)", fontsize=6.5)
    cbar.ax.axhline(y=THRESHOLD, color="#212121", linestyle="--", linewidth=1.5)
    cbar.ax.text(
        -0.1, THRESHOLD, "0.70 ─",
        ha="right", va="center", fontsize=6, color="#212121",
        transform=cbar.ax.transData,
    )

    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(CONFIGS, fontsize=8, fontweight="bold")
    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")

    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(row_labels, fontsize=6)

    # Cell annotations: score, * if unstable, bold if below threshold
    for r, (row_scores, unstable_cols) in enumerate(zip(scores, unstable)):
        for c, score in enumerate(row_scores):
            is_fail = score < THRESHOLD
            label = f"{score:.2f}"
            if c in unstable_cols:
                label += "*"
            bg = cmap(norm(score))
            luminance = 0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2]
            text_color = "white" if luminance < 0.45 else "#111111"
            ax.text(
                c, r, label,
                ha="center", va="center",
                fontsize=6,
                fontweight="bold" if is_fail else "normal",
                color=text_color,
            )

    # Minor grid lines between cells
    ax.set_xticks(np.arange(-0.5, n_cols, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n_rows, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.5)
    ax.tick_params(which="both", length=0)

    ax.set_title(
        "Normal-case faithfulness (median, 3 runs)\n"
        "bold = below 0.70  ·  * = unstable (range > 0.2)",
        fontsize=7,
        pad=14,
    )

    plt.tight_layout()
    out_path = OUT_DIR / "heatmap_normal_faithfulness.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    main()
