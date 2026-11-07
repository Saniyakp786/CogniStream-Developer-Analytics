
"""CogniStream - Data Quality Summary Report."""

import json
from datetime import datetime, timezone
from pathlib import Path


def generate_data_quality_report(results):
    """Generate a summary report from validation results."""

    total_checks = len(results)

    passed = sum(
        result["status"] == "PASS" for result in results
    )

    failed = sum(
        result["status"] == "FAIL" for result in results
    )

    pass_percentage = (
        round((passed / total_checks) * 100, 2)
        if total_checks > 0 else 0.0
    )

    failed_checks = [
        {
            "check": result["check"],
            "details": result["details"],
        }
        for result in results
        if result["status"] == "FAIL"
    ]

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": (
            "PASS" if total_checks > 0 and failed == 0 else "FAIL"
        ),
        "total_checks": total_checks,
        "passed": passed,
        "failed": failed,
        "pass_percentage": pass_percentage,
        "failed_checks": failed_checks,
    }

    return report


def save_data_quality_report(report, output_path):
    """Save the data quality report as a JSON file."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    return path


def print_data_quality_report(report):
    """Print the data quality summary."""

    print("\nCogniStream - Data Quality Summary")
    print("=" * 45)

    print(f"Overall Status: {report['overall_status']}")
    print(f"Total Checks: {report['total_checks']}")
    print(f"Passed: {report['passed']}")
    print(f"Failed: {report['failed']}")
    print(f"Pass Percentage: {report['pass_percentage']}%")

    if report["failed_checks"]:
        print("\nFailed Validation Details:")

        for item in report["failed_checks"]:
            print(f"- {item['check']}: {item['details']}")
    else:
        print("\nAll validation checks passed!")

    print("=" * 45)
