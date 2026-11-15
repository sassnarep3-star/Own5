"""One-command deterministic build: consolidate registers, then render the site."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import consolidate  # noqa: E402
import build_site  # noqa: E402


def main() -> int:
    rc = consolidate.main()
    if rc != 0:
        return rc
    build_site.build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
