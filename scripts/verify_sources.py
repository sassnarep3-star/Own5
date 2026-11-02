#!/usr/bin/env python3
"""Check the pinned official game file locally or against the GitHub API.

Player-log values were manually checked against NFL.com; this script deliberately
never claims that the player transcriptions have been live-verified.
"""
from __future__ import annotations
import argparse
import base64
import csv
import hashlib
import io
import json
import urllib.request
from analyze import GAME_PATH, GAME_SHA256, REVISION, parse_games, parse_players

API = f"https://api.github.com/repos/nfl-football-ops/Big-Data-Bowl/contents/Data/games.csv?ref={REVISION}"
GIT_BLOB = "3835c453e8c37342394267c384948b7d88fe55f1"


def verify_online():
    request = urllib.request.Request(API, headers={"User-Agent": "Own5-research-verifier", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    upstream = base64.b64decode(payload["content"])
    if payload["sha"] != GIT_BLOB or hashlib.sha256(upstream).hexdigest() != GAME_SHA256:
        raise ValueError("Pinned NFL source hash mismatch")
    local = GAME_PATH.read_bytes()
    local_rows = list(csv.reader(io.StringIO(local.decode("utf-8"), newline="")))
    source_rows = list(csv.reader(io.StringIO(upstream.decode("utf-8"), newline="")))
    if local != upstream or local_rows != source_rows:
        raise ValueError("Local game data differs from pinned official NFL source")
    print(f"Online: all {len(local_rows) - 1} game rows match pinned NFL source byte-for-byte and field-by-field.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true", help="compare every game row to pinned NFL GitHub data")
    args = parser.parse_args()
    games = parse_games()
    players = parse_players()
    print(f"Local: official game SHA-256 matches; {len(games)} games, {len(players)} player transcriptions, {sum(p['paired'] for p in players)} paired.")
    print("Player log checks are manual, not a live online verification by this script.")
    if args.online:
        verify_online()


if __name__ == "__main__":
    main()
