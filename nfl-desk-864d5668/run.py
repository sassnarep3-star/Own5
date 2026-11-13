#!/usr/bin/env python3
"""Entry point for the Own5 NFL Own-Line Lab pipeline.

Run:  python3 run.py
Writes every derived table to data/, then build_site.py renders the site.
"""
from __future__ import annotations
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import engine
import audit_repo
import build_site


def main():
    summary = engine.main()
    summary["repo_audit"] = audit_repo.main()
    summary["pages"] = build_site.build()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
