
import json

from src.data_quality_report import (
    generate_data_quality_report,
    save_data_quality_report,
)


def test_generate_report_with_all_passed_checks():
    results = [
        {
            "check": "Dataset not empty",
            "status": "PASS",
            "details": "100 rows found",
        },
        {
            "check": "Missing values",
            "status": "PASS",
            "details": "0 missing values found",
        },
    ]

    report = generate_data_quality_report(results)

    assert report["total_checks"] == 2
    assert report["passed"] == 2
    assert report["failed"] == 0
    assert report["pass_percentage"] == 100.0
    assert report["overall_status"] == "PASS"
    assert report["failed_checks"] == []


def test_generate_report_with_failed_checks():
    results = [
        {
            "check": "Dataset not empty",
            "status": "PASS",
            "details": "100 rows found",
        },
        {
            "check": "Missing values",
            "status": "FAIL",
            "details": "5 missing values found",
        },
    ]

    report = generate_data_quality_report(results)

    assert report["total_checks"] == 2
    assert report["passed"] == 1
    assert report["failed"] == 1
    assert report["pass_percentage"] == 50.0
    assert report["overall_status"] == "FAIL"
    assert len(report["failed_checks"]) == 1
    assert report["failed_checks"][0]["check"] == "Missing values"


def test_generate_report_with_empty_results():
    report = generate_data_quality_report([])

    assert report["total_checks"] == 0
    assert report["passed"] == 0
    assert report["failed"] == 0
    assert report["pass_percentage"] == 0.0
    assert report["overall_status"] == "FAIL"


def test_save_report_as_json(tmp_path):
    results = [
        {
            "check": "Dataset not empty",
            "status": "PASS",
            "details": "100 rows found",
        }
    ]

    report = generate_data_quality_report(results)
    output_file = tmp_path / "data_quality_report.json"

    saved_path = save_data_quality_report(
        report, output_file
    )

    assert saved_path.exists()

    with saved_path.open("r", encoding="utf-8") as file:
        saved_report = json.load(file)

    assert saved_report["total_checks"] == 1
    assert saved_report["passed"] == 1
    assert saved_report["overall_status"] == "PASS"
