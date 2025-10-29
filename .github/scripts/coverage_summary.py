"""Parse coverage.xml and append a concise summary to GITHUB_STEP_SUMMARY.

File: .github/scripts/coverage_summary.py
"""

import os
from pathlib import Path

import defusedxml.ElementTree as ET  # noqa: N817


def safe_int(value: str | None) -> int:
    """Convert string to int safely, returning 0 on fail."""
    try:
        return int(value) if value else 0
    except ValueError:
        return 0


def get_coverage_summary() -> str | None:
    """Parse a coverage.xml file and return a formatted summary."""
    cov = Path("coverage.xml")
    if not cov.exists():
        print("coverage.xml not found; nothing to summarize.")
        return None

    try:
        tree = ET.parse(cov)
        root = tree.getroot()
        if root is None:
            print("Error: coverage.xml has no root element.")
            return None

        # Safely extract coverage values (default to zero if missing)
        lines_valid = safe_int(root.get("lines-valid"))
        lines_covered = safe_int(root.get("lines-covered"))
        branches_valid = safe_int(root.get("branches-valid"))
        branches_covered = safe_int(root.get("branches-covered"))

        # Compute percentages safely
        pct = (100.0 * lines_covered / lines_valid) if lines_valid else 0.0
        bpct = (100.0 * branches_covered / branches_valid) if branches_valid else 0.0

        return f"""### Coverage Summary
- Lines: **{lines_covered}/{lines_valid}** ({pct:.1f}%)
- Branches: **{branches_covered}/{branches_valid}** ({bpct:.1f}%)
"""
    except (ET.ParseError, ValueError) as e:
        print(f"Error parsing coverage.xml: {e}")
        return None


def main() -> None:
    """Run the script."""
    summary = get_coverage_summary()
    if not summary:
        return

    out = os.environ.get("GITHUB_STEP_SUMMARY")

    # Append if GitHub provides a summary file; otherwise print to stdout
    if out:
        with Path(out).open("a", encoding="utf-8") as f:
            f.write(summary)
    else:
        print(summary)


if __name__ == "__main__":
    main()
