#!/usr/bin/env python3
"""Audit numeric claims in docs/model-configuration-analysis.md against
reports/aggregated.json.

Loads the per-case × per-config × per-run aggregated scores and dumps the
raw data used by the analysis doc: medians, ranges, instability flags,
sentiment/conflict labels, adversarial results, calibration pass/fail
counts, and summary rows. Run this whenever the analysis doc is edited
to cross-check numeric cells against canonical data.

Usage:
    python scripts/model_doc_audit.py
"""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGG = json.loads((ROOT / "reports/aggregated.json").read_text())
DATA = json.loads((ROOT / "data/test_dataset.json").read_text())["test_cases"]
CONFIGS = ["SS", "SW", "WS", "WW"]
THRESHOLD = 0.70


def median(xs):
    return statistics.median(xs)


def fmt_num(x):
    return f"{x:.2f}"


def case_meta():
    out = {}
    for case in DATA:
        out[case["id"]] = case
    return out


META = case_meta()
NORMAL = [
    c["id"]
    for c in DATA
    if not c.get("is_adversarial") and not c.get("is_judge_calibration")
]
ADVERSARIAL = [c["id"] for c in DATA if c.get("is_adversarial")]
CALIBRATION = [c["id"] for c in DATA if c.get("is_judge_calibration")]
SENTIMENT_CASES = [c["id"] for c in DATA if "expected_sentiment" in c]
CONFLICT_CASES = [c["id"] for c in DATA if "expected_conflicting" in c]


def entry(case_id, config):
    runs = AGG[case_id][config]
    scores = [r["score"] for r in runs]
    sentiments = [r.get("sentiment") for r in runs]
    conflicting = [r.get("conflicting") for r in runs]
    results = [r.get("result") for r in runs]
    robustness = [r.get("robustness") for r in runs]
    return {
        "scores": scores,
        "median": median(scores),
        "min": min(scores),
        "max": max(scores),
        "unstable": max(scores) - min(scores) > 0.2,
        "passes": sum(s >= THRESHOLD for s in scores),
        "fails": sum(s < THRESHOLD for s in scores),
        "robust_passes": sum(r == "PASS" for r in results),
        "robust_fails": sum(r == "FAIL" for r in results),
        "robustness_passes": sum(r == "PASS" for r in robustness),
        "robustness_fails": sum(r == "FAIL" for r in robustness),
        "sentiments": sentiments,
        "conflicting": conflicting,
        "results": results,
        "robustness": robustness,
    }


def print_table(title, cases):
    print(f"\n## {title}")
    for case_id in cases:
        row = [case_id]
        for cfg in CONFIGS:
            e = entry(case_id, cfg)
            star = "*" if e["unstable"] else ""
            row.append(
                f"{fmt_num(e['median'])} [{fmt_num(e['min'])}-{fmt_num(e['max'])}]{star}"
            )
        print(" | ".join(row))


def print_sentiment():
    print("\n## Sentiment accuracy")
    for cfg in CONFIGS:
        correct = 0
        wrong = 0
        for case_id in SENTIMENT_CASES:
            expected = META[case_id]["expected_sentiment"]
            vals = entry(case_id, cfg)["sentiments"]
            correct += sum(v == expected for v in vals)
            wrong += sum(v != expected for v in vals)
        print(cfg, correct, wrong, f"{100 * correct / (correct + wrong):.1f}%")
    print("\nPer-case labels")
    for case_id in SENTIMENT_CASES:
        expected = META[case_id]["expected_sentiment"]
        print(case_id, "expected", expected)
        for cfg in CONFIGS:
            print(" ", cfg, entry(case_id, cfg)["sentiments"])


def print_conflicting():
    print("\n## Conflicting accuracy")
    for cfg in CONFIGS:
        correct = 0
        wrong = 0
        for case_id in CONFLICT_CASES:
            expected = META[case_id]["expected_conflicting"]
            vals = entry(case_id, cfg)["conflicting"]
            correct += sum(v == expected for v in vals)
            wrong += sum(v != expected for v in vals)
        print(cfg, correct, wrong)
    print("\nPer-case flags")
    for case_id in CONFLICT_CASES:
        expected = META[case_id]["expected_conflicting"]
        print(case_id, "expected", expected)
        for cfg in CONFIGS:
            print(" ", cfg, entry(case_id, cfg)["conflicting"])


def print_adversarial():
    print("\n## Adversarial")
    for case_id in ADVERSARIAL:
        print(case_id)
        for cfg in CONFIGS:
            e = entry(case_id, cfg)
            print(
                " ",
                cfg,
                e["scores"],
                "median",
                fmt_num(e["median"]),
                "faith_result",
                e["results"],
                "robustness",
                e["robustness"],
                "unstable",
                e["unstable"],
            )


def print_calibration():
    print("\n## Calibration")
    for case_id in CALIBRATION:
        expected = META[case_id]["expected_faithfulness_pass"]
        print(case_id, "expected", expected)
        for cfg in CONFIGS:
            e = entry(case_id, cfg)
            print(
                " ",
                cfg,
                e["scores"],
                "median",
                fmt_num(e["median"]),
                "passes",
                e["passes"],
                "fails",
                e["fails"],
                "unstable",
                e["unstable"],
            )


def print_failure_counts():
    print("\n## Failure counts")
    for cfg in CONFIGS:
        normal_faith = sum(entry(c, cfg)["fails"] for c in NORMAL)
        sentiment = sum(
            sum(v != META[c]["expected_sentiment"] for v in entry(c, cfg)["sentiments"])
            for c in SENTIMENT_CASES
        )
        conflicting = sum(
            sum(v != META[c]["expected_conflicting"] for v in entry(c, cfg)["conflicting"])
            for c in CONFLICT_CASES
        )
        adv_faith = sum(entry(c, cfg)["fails"] for c in ADVERSARIAL)
        adv_robust = sum(entry(c, cfg)["robustness_fails"] for c in ADVERSARIAL)
        calib = sum(
            (
                entry(c, cfg)["fails"]
                if META[c]["expected_faithfulness_pass"]
                else entry(c, cfg)["passes"]
            )
            for c in CALIBRATION
        )
        total = normal_faith + sentiment + conflicting + adv_faith + adv_robust + calib
        print(cfg, normal_faith, sentiment, conflicting, adv_faith, adv_robust, calib, total)


def print_ss_sub1():
    print("\n## SS normal/adversarial medians below 1.00")
    for case_id in NORMAL + ADVERSARIAL:
        med = entry(case_id, "SS")["median"]
        if med < 1.0:
            print(case_id, fmt_num(med), entry(case_id, "SS")["scores"])


def print_unstable():
    print("\n## Unstable entries")
    for case_id in NORMAL + ADVERSARIAL + CALIBRATION:
        for cfg in CONFIGS:
            e = entry(case_id, cfg)
            if e["unstable"]:
                print(case_id, cfg, f"{fmt_num(e['min'])}-{fmt_num(e['max'])}", e["scores"])


def print_summary_rows():
    print("\n## Summary rows")
    for cases, name in [(NORMAL, "normal"), (ADVERSARIAL, "adversarial"), (CALIBRATION, "calibration")]:
        print(name)
        for cfg in CONFIGS:
            meds = [entry(c, cfg)["median"] for c in cases]
            print(
                " ",
                cfg,
                "median_of_medians",
                fmt_num(median(meds)),
                "min_of_medians",
                fmt_num(min(meds)),
                "passes",
                sum(entry(c, cfg)["passes"] for c in cases),
                "fails",
                sum(entry(c, cfg)["fails"] for c in cases),
            )


if __name__ == "__main__":
    print("normal", NORMAL)
    print("adversarial", ADVERSARIAL)
    print("calibration", CALIBRATION)
    print_table("Normal faithfulness", NORMAL)
    print_sentiment()
    print_conflicting()
    print_adversarial()
    print_calibration()
    print_failure_counts()
    print_ss_sub1()
    print_unstable()
    print_summary_rows()
