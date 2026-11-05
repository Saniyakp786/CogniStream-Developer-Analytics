"""
Copy the cleaned CSV into powerbi/data/ so the Power BI folder is self-contained.

Run from the project root:
    python src/export_powerbi.py
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "cleaned_developer_productivity.csv"
DEST_DIR = ROOT / "powerbi" / "data"
DEST = DEST_DIR / "cleaned_developer_productivity.csv"


def main():
    if not SRC.exists():
        raise SystemExit(
            f"Missing {SRC.name}. Run first:  python src/cleaning.py"
        )
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC, DEST)
    print(f"Copied:\n  {SRC}\n-> {DEST}")
    print(f"Rows ready for Power BI Desktop ({DEST.stat().st_size:,} bytes).")


if __name__ == "__main__":
    main()
