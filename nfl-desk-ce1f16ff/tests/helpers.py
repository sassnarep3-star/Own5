"""Shared test plumbing: put the desk on sys.path without depending on cwd."""
import os
import sys

DESK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if DESK not in sys.path:
    sys.path.insert(0, DESK)
DATA = os.path.join(DESK, "data")
