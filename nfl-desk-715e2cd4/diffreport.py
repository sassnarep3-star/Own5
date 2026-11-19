"""Weekly 'what changed' snapshot tool.

Freeze the current data tables as data/snapshots/<date>/, then let pipeline.py
render weekly_diff.csv against the most recent *previous* snapshot. On the very
first run there is nothing to compare against, and the report says so.

Usage: python3 diffreport.py [--stamp YYYY-MM-DD] [--freeze]
"""
import os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SNAPS = os.path.join(DATA, "snapshots")
STAMP = "2026-11-19"
KEEP = ("team_ratings.csv", "availability_summary.csv", "correlations.csv",
        "lines_week11.csv", "scorecard.csv", "results_corpus.csv")


def main():
    argv = sys.argv[1:]
    stamp = argv[argv.index("--stamp") + 1] if "--stamp" in argv else STAMP
    freeze = "--freeze" in argv
    if freeze:
        dest = os.path.join(SNAPS, stamp)
        os.makedirs(dest, exist_ok=True)
        for fn in KEEP:
            src = os.path.join(DATA, fn)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(dest, fn))
        print("froze snapshot %s" % stamp)
        return 0
    import subprocess
    subprocess.run([sys.executable, os.path.join(HERE, "pipeline.py")], check=True,
                   stdout=subprocess.DEVNULL)
    print("weekly diff rebuilt from the latest previous snapshot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
