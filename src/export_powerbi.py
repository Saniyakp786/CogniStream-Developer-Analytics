"""
Copy the cleaned CSV into powerbi/data/ so the Power BI folder is self-contained.

Run from the project root:
    python src/export_powerbi.py
"""
import shutil
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
import kpis  # noqa: E402

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

    # Spearman correlation matrix (all sessions) in long format for a Power BI heatmap matrix.
    # It is a fixed snapshot: it does NOT react to Power BI slicers.
    df = kpis.load_clean(SRC)
    corr = kpis.correlation_matrix(df)
    long = corr.reset_index().melt(id_vars="index", var_name="variable_y", value_name="spearman_rho")
    long = long.rename(columns={"index": "variable_x"})
    out = DEST_DIR / "correlation_matrix_spearman.csv"
    long.to_csv(out, index=False)
    print(f"Wrote correlation snapshot: {out} ({len(long)} rows)")


if __name__ == "__main__":
    main()
