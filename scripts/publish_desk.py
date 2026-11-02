"""Publish the verified desk into the legacy GitHub Pages root at own5-desk/.

The repository already hosts other sessions' dashboards from main @ /. This
additive subdirectory preserves those sites while making this desk publicly
available without changing shared Pages settings.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
TARGET = ROOT / "own5-desk"

if not (DIST / "index.html").exists():
    raise SystemExit("dist/index.html missing; run npm run desk:build first")
if TARGET.exists():
    shutil.rmtree(TARGET)
shutil.copytree(DIST, TARGET)
(TARGET / ".nojekyll").touch()
print(f"Published verified desk to {TARGET.relative_to(ROOT)}/")
