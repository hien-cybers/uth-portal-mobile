from __future__ import annotations

import argparse
import csv
import importlib
import json
import os
import re
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from tests.config.test_config import TestConfig


REPO_ROOT = Path(__file__).resolve().parents[1]
TESTCASES_DIR = REPO_ROOT / "tests" / "testcases"
REGISTRY_PATH = TESTCASES_DIR / "test-case-registry.json"
TEST_CASES_DOC = TESTCASES_DIR / "TEST_CASES.md"
REPORT_DIR = REPO_ROOT / "test-results"

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class TestResult:
    id: str
    function: str
    labels: str
    status: str
    duration: float
    actual_result: str
    error: str = ""


def load_registry() -> list[dict[str, Any]]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def load_test_function(target: str) -> Callable[[Path], None]:
    module_name, function_name = target.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, function_name)


def documented_test_case_ids() -> list[str]:
    if not TEST_CASES_DOC.exists():
        return []
    text = TEST_CASES_DOC.read_text(encoding="utf-8")
    return re.findall(r"\|\s*(TC\d{3})\s*\|", text)


def documented_test_steps() -> dict[str, list[str]]:
    if not TEST_CASES_DOC.exists():
        return {}

    steps_by_id: dict[str, list[str]] = {}
    for line in TEST_CASES_DOC.read_text(encoding="utf-8").splitlines():
        if not re.match(r"\|\s*TC\d{3}\s*\|", line):
            continue

        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) < 3:
            continue

        test_id = parts[0]
        steps = [
            re.sub(r"\s+", " ", step.strip())
            for step in re.split(r"<br\s*/?>", parts[2])
            if step.strip()
        ]
        steps_by_id[test_id] = steps
    return steps_by_id


def documented_input_data() -> dict[str, list[str]]:
    if not TEST_CASES_DOC.exists():
        return {}

    inputs_by_id: dict[str, list[str]] = {}
    for line in TEST_CASES_DOC.read_text(encoding="utf-8").splitlines():
        if not re.match(r"\|\s*TC\d{3}\s*\|", line):
            continue

        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) < 4:
            continue

        test_id = parts[0]
        inputs = [
            re.sub(r"\s+", " ", item.strip())
            for item in re.split(r"<br\s*/?>", parts[3])
            if item.strip()
        ]
        inputs_by_id[test_id] = inputs
    return inputs_by_id


def documented_expected_results() -> dict[str, str]:
    if not TEST_CASES_DOC.exists():
        return {}

    expected_by_id: dict[str, str] = {}
    for line in TEST_CASES_DOC.read_text(encoding="utf-8").splitlines():
        if not re.match(r"\|\s*TC\d{3}\s*\|", line):
            continue

        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) < 5:
            continue

        expected_by_id[parts[0]] = re.sub(r"\s+", " ", parts[4].strip())
    return expected_by_id


def documented_labels() -> dict[str, str]:
    if not TEST_CASES_DOC.exists():
        return {}

    labels_by_id: dict[str, str] = {}
    for line in TEST_CASES_DOC.read_text(encoding="utf-8").splitlines():
        if not re.match(r"\|\s*TC\d{3}\s*\|", line):
            continue

        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) < 6:
            continue

        labels_by_id[parts[0]] = re.sub(r"\s+", " ", parts[5].strip())
    return labels_by_id


def validate_registry(registry: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    registry_ids = [item.get("id", "") for item in registry]
    doc_ids = documented_test_case_ids()

    duplicates = sorted({test_id for test_id in registry_ids if registry_ids.count(test_id) > 1})
    if duplicates:
        errors.append(f"Duplicate IDs in registry: {', '.join(duplicates)}")

    doc_duplicates = sorted({test_id for test_id in doc_ids if doc_ids.count(test_id) > 1})
    if doc_duplicates:
        errors.append(f"Duplicate IDs in tests/testcases/TEST_CASES.md: {', '.join(doc_duplicates)}")

    missing_in_registry = sorted(set(doc_ids) - set(registry_ids))
    if missing_in_registry:
        errors.append(f"Documented test cases missing in registry: {', '.join(missing_in_registry)}")

    missing_in_docs = sorted(set(registry_ids) - set(doc_ids))
    if missing_in_docs:
        errors.append(f"Registry test cases missing in tests/testcases/TEST_CASES.md: {', '.join(missing_in_docs)}")

    labels_by_id = documented_labels()

    for item in registry:
        test_id = item.get("id", "<missing>")
        if not item.get("function"):
            errors.append(f"{test_id}: missing function")
        if item.get("automated") is True and not item.get("testTarget"):
            errors.append(f"{test_id}: marked automated without testTarget")
        if item.get("automated") is True and item.get("testTarget"):
            try:
                load_test_function(item["testTarget"])
            except Exception as exc:
                errors.append(f"{test_id}: cannot load {item['testTarget']}: {exc}")
        expected_labels = ", ".join(case_labels_for_tags(item.get("tags", [])))
        documented_label = labels_by_id.get(test_id, "")
        if expected_labels and documented_label != expected_labels:
            errors.append(f"{test_id}: doc Label '{documented_label}' does not match registry '{expected_labels}'")

    if TEST_CASES_DOC.exists():
        for line in TEST_CASES_DOC.read_text(encoding="utf-8").splitlines():
            if re.match(r"\|\s*TC\d{3}\s*\|", line):
                parts = [part.strip() for part in line.strip().strip("|").split("|")]
                if len(parts) >= 5:
                    test_id, function, _steps, _input, expected = parts[:5]
                    if not function:
                        errors.append(f"{test_id}: missing Function in docs")
                    if not expected:
                        errors.append(f"{test_id}: missing Expected Result in docs")
                    if len(parts) < 6 or not parts[5]:
                        errors.append(f"{test_id}: missing Label in docs")
    return errors


def selected_tests(args: argparse.Namespace, registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = registry
    if args.id:
        selected = [item for item in selected if item["id"].lower() == args.id.lower()]
    if args.function:
        selected = [item for item in selected if item["function"].lower() == args.function.lower()]
    if args.tag:
        selected = [item for item in selected if args.tag.lower() in {tag.lower() for tag in item.get("tags", [])}]
    if args.type:
        selected = [item for item in selected if item["type"].lower() == args.type.lower()]
    if not selected:
        raise SystemExit("No test cases matched the selected filters.")
    return selected


def run_one(
    item: dict[str, Any],
    delay_seconds: float = 0.0,
    steps: list[str] | None = None,
    inputs: list[str] | None = None,
    expected_result: str = "",
) -> TestResult:
    print(f"[PROCESSING] {item['id']} - {item['function']}", flush=True)
    case_labels = case_labels_for_tags(item.get("tags", []))
    if case_labels:
        print(f"[CASE] {item['id']} - {', '.join(case_labels)}", flush=True)
    for input_item in inputs or []:
        print(f"[INPUT] {item['id']} - {input_item}", flush=True)
    if expected_result:
        print(f"[EXPECTED] {item['id']} - {expected_result}", flush=True)
    if delay_seconds > 0:
        time.sleep(delay_seconds)

    start = time.perf_counter()
    if not item.get("automated"):
        return TestResult(
            id=item["id"],
            function=item["function"],
            labels=", ".join(case_labels),
            status="SKIPPED",
            duration=0.0,
            actual_result="Test case is not automated.",
        )

    try:
        os.environ["CURRENT_TEST_ID"] = item["id"]
        os.environ["CURRENT_TEST_STEPS"] = json.dumps(steps or [], ensure_ascii=False)
        os.environ["CURRENT_TEST_STEP_INDEX"] = "0"
        fn = load_test_function(item["testTarget"])
        fn(REPO_ROOT)
        return TestResult(
            id=item["id"],
            function=item["function"],
            labels=", ".join(case_labels),
            status="PASS",
            duration=time.perf_counter() - start,
            actual_result="Assertions passed.",
        )
    except AssertionError as exc:
        return TestResult(
            id=item["id"],
            function=item["function"],
            labels=", ".join(case_labels),
            status="FAIL",
            duration=time.perf_counter() - start,
            actual_result="Assertion failed.",
            error=str(exc),
        )
    except Exception:
        return TestResult(
            id=item["id"],
            function=item["function"],
            labels=", ".join(case_labels),
            status="ERROR",
            duration=time.perf_counter() - start,
            actual_result="Unexpected test execution error.",
            error=traceback.format_exc(),
        )


def markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def result_note(result: TestResult) -> str:
    if result.status == "PASS":
        return "Đã kiểm thử tự động (headless) trên code thực tế."
    if result.status == "SKIPPED":
        return "Test case chưa được tự động hóa."
    if result.status == "FAIL":
        return "Cần debug assertion/logic theo Actual Result và Error."
    return "Cần debug lỗi runtime khi chạy test."


def write_debug_report(
    results: list[TestResult],
    steps_by_id: dict[str, list[str]],
    inputs_by_id: dict[str, list[str]],
    expected_by_id: dict[str, str],
) -> None:
    headers = [
        "Test Case ID",
        "Function",
        "Test Steps",
        "Input Data",
        "Expected Result",
        "Actual Result (Kết quả thực tế)",
        "Pass / Fail",
        "Ghi chú",
    ]

    rows: list[list[str]] = []
    for result in results:
        actual = result.actual_result
        if result.error:
            actual = f"{actual}\n\n[Error]\n{result.error}"
        rows.append([
            result.id,
            result.function,
            "\n".join(steps_by_id.get(result.id, [])),
            "\n".join(inputs_by_id.get(result.id, [])),
            expected_by_id.get(result.id, ""),
            actual,
            result.status,
            result_note(result),
        ])

    markdown_lines = [
        "# Debug Test Report",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        markdown_lines.append("| " + " | ".join(markdown_cell(cell) for cell in row) + " |")
    (REPORT_DIR / "latest-debug-report.md").write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")

    with (REPORT_DIR / "latest-debug-report.tsv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file, delimiter="\t", lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(rows)

    with (REPORT_DIR / "latest-debug-report.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(rows)


def write_reports(
    results: list[TestResult],
    steps_by_id: dict[str, list[str]],
    inputs_by_id: dict[str, list[str]],
    expected_by_id: dict[str, str],
) -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    json_rows = [result.__dict__ for result in results]
    (REPORT_DIR / "latest-report.json").write_text(json.dumps(json_rows, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "PASS": sum(1 for item in results if item.status == "PASS"),
        "FAIL": sum(1 for item in results if item.status == "FAIL"),
        "SKIPPED": sum(1 for item in results if item.status == "SKIPPED"),
        "ERROR": sum(1 for item in results if item.status == "ERROR"),
    }
    lines = [
        "# Latest Test Report",
        "",
        f"- PASS: {summary['PASS']}",
        f"- FAIL: {summary['FAIL']}",
        f"- SKIPPED: {summary['SKIPPED']}",
        f"- ERROR: {summary['ERROR']}",
        "",
        "| Test Case ID | Function | Label | Status | Duration | Actual Result | Error |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for result in results:
        error = result.error.replace("\n", "<br>") if result.error else ""
        lines.append(
            f"| {result.id} | {result.function} | {result.labels} | {result.status} | {result.duration:.3f}s | "
            f"{result.actual_result} | {error} |"
        )
    (REPORT_DIR / "latest-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    suite = ET.Element("testsuite", {
        "name": "UTH Portal Mobile",
        "tests": str(len(results)),
        "failures": str(summary["FAIL"]),
        "errors": str(summary["ERROR"]),
        "skipped": str(summary["SKIPPED"]),
    })
    for result in results:
        case = ET.SubElement(suite, "testcase", {
            "classname": result.function,
            "name": result.id,
            "time": f"{result.duration:.3f}",
        })
        properties = ET.SubElement(case, "properties")
        ET.SubElement(properties, "property", {
            "name": "labels",
            "value": result.labels,
        })
        if result.status == "FAIL":
            failure = ET.SubElement(case, "failure", {"message": result.error[:200]})
            failure.text = result.error
        elif result.status == "ERROR":
            error = ET.SubElement(case, "error", {"message": result.error[:200]})
            error.text = result.error
        elif result.status == "SKIPPED":
            ET.SubElement(case, "skipped", {"message": result.actual_result})
    ET.ElementTree(suite).write(REPORT_DIR / "junit-results.xml", encoding="utf-8", xml_declaration=True)
    write_debug_report(results, steps_by_id, inputs_by_id, expected_by_id)


def case_labels_for_tags(tags: list[str]) -> list[str]:
    tag_set = {tag.lower() for tag in tags}
    labels: list[str] = []
    if "positive" in tag_set:
        labels.append("Positive")
    if "negative" in tag_set:
        labels.append("Negative")
    if "boundary" in tag_set:
        labels.append("Boundary")
    if "authorization" in tag_set:
        labels.append("Authorization")
    if "duplicate" in tag_set:
        labels.append("Duplicate")
    return labels


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UTH Portal Mobile test runner")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Run all registered test cases")
    group.add_argument("--id", help="Run one Test Case ID, e.g. TC001")
    group.add_argument("--function", help="Run tests by exact Function name")
    group.add_argument("--tag", help="Run tests by tag")
    group.add_argument("--type", help="Run tests by type, e.g. Integration")
    group.add_argument("--validate", action="store_true", help="Validate docs, registry, and implementations")
    parser.add_argument("--allow-non-test-environment", action="store_true")
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to wait before each test case. Useful for watching UI automation.",
    )
    parser.add_argument(
        "--step-delay",
        type=float,
        default=0.0,
        help="Seconds to wait after UI actions/pump calls inside each test case.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry = load_registry()

    if args.validate:
        errors = validate_registry(registry)
        if errors:
            print("Validation failed:")
            for error in errors:
                print(f"- {error}")
            return 1
        print("Validation passed.")
        return 0

    if not any([args.all, args.id, args.function, args.tag, args.type]):
        args.all = True

    config = TestConfig(allow_non_test_environment=args.allow_non_test_environment)
    config.assert_safe()
    os.environ["UI_STEP_DELAY"] = str(max(args.step_delay, 0.0))

    tests = selected_tests(args, registry)
    steps_by_id = documented_test_steps()
    inputs_by_id = documented_input_data()
    expected_by_id = documented_expected_results()
    results = [
        run_one(
            item,
            args.delay,
            steps_by_id.get(item["id"], []),
            inputs_by_id.get(item["id"], []),
            expected_by_id.get(item["id"], ""),
        )
        for item in tests
    ]
    write_reports(results, steps_by_id, inputs_by_id, expected_by_id)

    for result in results:
        print(f"{result.id} [{result.status}] {result.function} ({result.duration:.3f}s)")
        if result.error:
            print(result.error)

    return 1 if any(result.status in {"FAIL", "ERROR"} for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
