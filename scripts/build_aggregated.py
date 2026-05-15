#!/usr/bin/env python3
"""Build reports/aggregated.json from saved pytest run logs.

Run from repo root:
    python scripts/build_aggregated.py

By default this reads the current three-run matrix logs in reports/, writes
reports/aggregated.json, and orders cases according to data/test_dataset.json.
Every run record has score/result fields; additional fields depend on the
dataset case type.

Examples:
    # Rebuild the canonical aggregate from reports/*-runN.log.
    python3 scripts/build_aggregated.py

    # Validate and print without changing reports/aggregated.json.
    python3 scripts/build_aggregated.py --dry-run

    # Build from a copied log directory, useful before replacing the canonical report.
    python3 scripts/build_aggregated.py --reports-dir /tmp/eval-logs --dry-run

    # Rebuild a two-run diagnostic matrix.
    python3 scripts/build_aggregated.py --expected-runs 2 --output reports/aggregated-2run.json
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = ROOT / "data" / "test_dataset.json"
DEFAULT_REPORTS_DIR = ROOT / "reports"
DEFAULT_OUTPUT = DEFAULT_REPORTS_DIR / "aggregated.json"

CONFIGS = ["SS", "SW", "WS", "WW"]
CONFIG_BY_NAME = {
    "strong-strong": "SS",
    "strong-weak": "SW",
    "weak-strong": "WS",
    "weak-weak": "WW",
}

# Logs before the dataset rename use these pytest ids. Keep this map narrow:
# every value is a current data/test_dataset.json id.
LEGACY_CASE_IDS = {
    "positive_001": "positive_baseline",
    "negative_001": "negative_baseline",
    "neutral_001": "neutral_baseline",
    "negative_conflicting_001": "negative_conflicting_logistics",
    "positive_conflicting_001": "positive_conflicting_logistics",
    "negative_numeric_001": "negative_numeric_shortfall",
    "negative_attribution_001": "negative_attribution_multiparty",
    "positive_negation_001": "positive_negation_double",
    "negative_negation_001": "negative_negation_rhetorical",
    "negative_distractor_001": "negative_distractor_delayed_failure",
    "negative_timeline_001": "negative_timeline_shipping",
    "judge_unfaithful_hallucinated_001": "judge_unfaithful_hallucinated",
    "judge_unfaithful_negation_flip_001": "judge_unfaithful_negation_flip",
    "judge_unfaithful_attribution_swap_001": "judge_unfaithful_attribution_swap",
    "judge_unfaithful_number_swap_001": "judge_unfaithful_number_swap",
}

LOG_NAME_RE = re.compile(
    r"^(?P<config>strong-strong|strong-weak|weak-strong|weak-weak)-run(?P<run>\d+)\.log$"
)
LOGGER = logging.getLogger(__name__)


RunRecord = dict[str, Any]
Aggregated = dict[str, dict[str, list[RunRecord]]]
CaseMeta = dict[str, Any]


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=DEFAULT_REPORTS_DIR,
        help="Directory containing *-runN.log files.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
        help="Dataset JSON used for case ordering and validation.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output JSON path.",
    )
    parser.add_argument(
        "--expected-runs",
        type=int,
        default=3,
        help="Expected number of run logs per config.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the aggregate to stdout instead of writing --output.",
    )
    return parser.parse_args()


def load_cases(dataset_path: Path) -> tuple[list[str], dict[str, CaseMeta]]:
    """Load dataset case ordering and metadata."""
    data = json.loads(dataset_path.read_text())
    cases = data["test_cases"]
    case_ids = [case["id"] for case in cases]
    return case_ids, {case["id"]: case for case in cases}


def discover_logs(reports_dir: Path, expected_runs: int) -> list[tuple[str, int, Path]]:
    """Find and validate the run log matrix.

    Args:
        reports_dir: Directory containing config run logs.
        expected_runs: Required number of sequential runs per config.

    Returns:
        Sorted tuples of config label, run number, and log path.

    Raises:
        FileNotFoundError: No matching run logs were found.
        ValueError: The expected run count is invalid, or the log matrix has
            missing or unexpected run numbers.
    """
    if expected_runs < 1:
        raise ValueError("--expected-runs must be at least 1")

    logs: list[tuple[str, int, Path]] = []
    for path in sorted(reports_dir.glob("*-run*.log")):
        match = LOG_NAME_RE.match(path.name)
        if not match:
            continue
        config = CONFIG_BY_NAME[match.group("config")]
        run = int(match.group("run"))
        logs.append((config, run, path))
    if not logs:
        raise FileNotFoundError(f"No run logs found in {reports_dir}")

    expected = set(range(1, expected_runs + 1))
    errors: list[str] = []
    for config in CONFIGS:
        runs = sorted(run for candidate_config, run, _path in logs if candidate_config == config)
        missing = sorted(expected - set(runs))
        unexpected = sorted(set(runs) - expected)
        if missing:
            errors.append(f"{config} missing run(s): {', '.join(map(str, missing))}")
        if unexpected:
            errors.append(f"{config} has unexpected run(s): {', '.join(map(str, unexpected))}")
    if errors:
        raise ValueError(f"Run log matrix mismatch in {reports_dir}: {'; '.join(errors)}")

    return sorted(logs, key=lambda item: (CONFIGS.index(item[0]), item[1], item[2].name))


def parse_value(raw: str) -> Any:
    """Parse a scalar value from a log field."""
    if raw in {"True", "False"}:
        return raw == "True"
    try:
        return float(raw)
    except ValueError:
        return raw


def canonical_case_id(case_id: str) -> str:
    """Map legacy pytest case IDs to current dataset IDs."""
    return LEGACY_CASE_IDS.get(case_id, case_id)


def parse_result_line(line: str) -> tuple[str, RunRecord] | None:
    """Parse one pytest log result line."""
    if line.startswith("INFO "):
        return None

    parts = [part.strip() for part in line.rstrip().split("|")]
    if len(parts) < 3 or parts[1] not in {"PASS", "FAIL"}:
        return None

    case_id = canonical_case_id(parts[0])
    fields: RunRecord = {}
    for part in parts[2:]:
        if "=" not in part:
            continue
        key, raw_value = part.split("=", 1)
        fields[key] = parse_value(raw_value)

    if "score" in fields:
        fields = {"score": fields.pop("score"), "result": parts[1], **fields}
        return case_id, fields
    if "robustness" in fields:
        # Robustness rows supplement the earlier faithfulness row for the same
        # adversarial case; score/result come from that earlier merge.
        return case_id, fields

    return None


def parse_log(path: Path, known_case_ids: set[str]) -> dict[str, RunRecord]:
    """Parse one run log into case records.

    Args:
        path: Log file path.
        known_case_ids: Canonical dataset case IDs accepted for this aggregate.

    Returns:
        Run records keyed by canonical case ID.

    Raises:
        ValueError: The log contains a result for a case not present in the
            dataset.
    """
    records: dict[str, RunRecord] = {}
    unknown_case_ids: set[str] = set()

    for line in path.read_text().splitlines():
        parsed = parse_result_line(line)
        if parsed is None:
            continue

        case_id, fields = parsed
        if case_id not in known_case_ids:
            unknown_case_ids.add(case_id)
            continue

        record = records.setdefault(case_id, {})
        record.update(fields)

    if unknown_case_ids:
        unknown = ", ".join(sorted(unknown_case_ids))
        raise ValueError(f"{path} contains case ids not present in the dataset: {unknown}")

    return records


def build_aggregate(logs: list[tuple[str, int, Path]], case_ids: list[str]) -> Aggregated:
    """Build the case/config/run aggregate from parsed logs.

    Args:
        logs: Sorted tuples of config label, run number, and log path.
        case_ids: Ordered dataset case IDs to include in the output.

    Returns:
        Aggregated records keyed by case ID and config label.

    Raises:
        ValueError: A log is missing one or more dataset case records.
    """
    known_case_ids = set(case_ids)
    aggregate: Aggregated = {case_id: {config: [] for config in CONFIGS} for case_id in case_ids}

    for config, _run, path in logs:
        run_records = parse_log(path, known_case_ids)
        missing = [case_id for case_id in case_ids if case_id not in run_records]
        if missing:
            missing_list = ", ".join(missing)
            raise ValueError(f"{path} is missing records for: {missing_list}")

        for case_id in case_ids:
            aggregate[case_id][config].append(run_records[case_id])

    return aggregate


def required_fields_for_case(case: CaseMeta) -> set[str]:
    """Determine required run-record fields for a dataset case."""
    fields = {"score", "result"}
    if case.get("is_adversarial"):
        return fields | {"robustness", "baseline_sentiment", "adversarial_sentiment"}
    if case.get("is_judge_calibration"):
        return fields | {"expected_pass", "actual_pass"}
    return fields | {"sentiment", "conflicting"}


def validate_record_values(case_id: str, config: str, index: int, record: RunRecord) -> None:
    """Validate individual run-record field values.

    Args:
        case_id: Dataset case ID for error reporting.
        config: Config label for error reporting.
        index: One-based run index for error reporting.
        record: Run record to validate.

    Raises:
        ValueError: A field has an invalid value or type.
    """
    prefix = f"{case_id}/{config} run {index}"
    if not isinstance(record["score"], int | float):
        raise ValueError(f"{prefix} has non-numeric score: {record['score']!r}")
    if record["result"] not in {"PASS", "FAIL"}:
        raise ValueError(f"{prefix} has invalid result: {record['result']!r}")
    if "robustness" in record and record["robustness"] not in {"PASS", "FAIL"}:
        raise ValueError(f"{prefix} has invalid robustness: {record['robustness']!r}")
    if "sentiment" in record and record["sentiment"] not in {"positive", "negative", "neutral"}:
        raise ValueError(f"{prefix} has invalid sentiment: {record['sentiment']!r}")
    for key in ("baseline_sentiment", "adversarial_sentiment"):
        if key in record and record[key] not in {"positive", "negative", "neutral"}:
            raise ValueError(f"{prefix} has invalid {key}: {record[key]!r}")
    for key in ("conflicting", "expected_pass", "actual_pass"):
        if key in record and not isinstance(record[key], bool):
            raise ValueError(f"{prefix} has non-boolean {key}: {record[key]!r}")


def validate_aggregate(
    aggregate: Aggregated,
    case_meta: dict[str, CaseMeta],
    expected_runs: int,
) -> None:
    """Validate aggregate shape and case-type-specific fields.

    Args:
        aggregate: Aggregated records to validate.
        case_meta: Dataset metadata keyed by case ID.
        expected_runs: Required run count per case/config.

    Raises:
        ValueError: Any case/config has the wrong run count, missing required
            fields, or invalid field values.
    """
    for case_id, by_config in aggregate.items():
        required = required_fields_for_case(case_meta[case_id])
        for config, runs in by_config.items():
            if len(runs) != expected_runs:
                raise ValueError(
                    f"{case_id}/{config} has {len(runs)} run record(s), "
                    f"expected {expected_runs}"
                )
            for index, record in enumerate(runs, start=1):
                missing = required - record.keys()
                if missing:
                    fields = ", ".join(sorted(missing))
                    raise ValueError(f"{case_id}/{config} run {index} missing fields: {fields}")
                validate_record_values(case_id, config, index, record)


def main() -> None:
    """Run the command-line interface."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args()
    case_ids, case_meta = load_cases(args.dataset)
    logs = discover_logs(args.reports_dir, args.expected_runs)
    aggregate = build_aggregate(logs, case_ids)
    validate_aggregate(aggregate, case_meta, args.expected_runs)

    output = json.dumps(aggregate, indent=2)
    if args.dry_run:
        print(output, end="")
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output)
    LOGGER.info("Wrote %s", args.output)


if __name__ == "__main__":
    main()
