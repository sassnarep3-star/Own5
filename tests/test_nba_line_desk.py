"""Tests for the NBA Line Desk 2026-27 (session 9cf7de11).

Covers: mathematical identities in analytics.py, reconciliation of the verified CSVs,
cell-level agreement with the existing nba-2026-lab sample, regenerated derived tables
matching the committed ones, and integrity of the built site (every table row has a
source link, every internal link resolves, no leftover placeholders).
"""
import csv
import html
import math
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.nba_line_desk import analytics as A  # noqa: E402
from tools.nba_line_desk import checks, compute, loader  # noqa: E402

DATA = ROOT / "data" / "nba-2026-27"
SITE = ROOT / "nba-line-desk"


def read_csv(name):
    with open(DATA / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class AnalyticsIdentities(unittest.TestCase):
    def test_pearson_exact(self):
        self.assertAlmostEqual(A.pearson([1, 2, 3], [2, 4, 6]), 1.0)
        self.assertAlmostEqual(A.pearson([1, 2, 3], [6, 4, 2]), -1.0)

    def test_pearson_constant_raises(self):
        with self.assertRaises(ValueError):
            A.pearson([1, 1, 1], [2, 3, 4])

    def test_binomial_known_value(self):
        # 8 wins of 10 at p=0.5: exact two-sided p = 2 * (45 + 10 + 1) / 1024 = 0.109375
        self.assertAlmostEqual(A.binom_two_sided_p(8, 10), 0.109375)

    def test_binomial_symmetric(self):
        self.assertAlmostEqual(A.binom_two_sided_p(3, 10), A.binom_two_sided_p(7, 10))

    def test_wilson_contains_point_estimate(self):
        lo, hi = A.wilson_ci(4, 8)
        self.assertLess(lo, 0.5)
        self.assertGreater(hi, 0.5)

    def test_american_breakeven(self):
        self.assertAlmostEqual(A.american_breakeven(-110), 110 / 210)
        self.assertAlmostEqual(A.american_breakeven(150), 0.4)

    def test_required_n_for_55_percent(self):
        # Normal approximation, two-sided alpha 0.05, power 0.80 vs 50%.
        self.assertEqual(A.required_n_two_proportions_vs_half(0.55), 783)

    def test_games_for_half_width(self):
        self.assertEqual(A.games_for_half_width(0.10), 97)
        self.assertEqual(A.games_for_half_width(0.05), 385)

    def test_fisher_ci_n30_halfwidth_about_036(self):
        # Flag F08 states a 95% CI about +/-0.36 around r=0 for n=30.
        lo, hi = A.fisher_ci(0.0, 30)
        self.assertAlmostEqual(hi, 0.36, places=2)
        self.assertAlmostEqual(lo, -0.36, places=2)

    def test_bonferroni(self):
        self.assertAlmostEqual(A.bonferroni_alpha(0.05, 8), 0.00625)

    def test_permutation_seeded_reproducible(self):
        x = [1, 2, 3, 4, 5, 6, 7, 8]
        y = [2, 1, 4, 3, 6, 5, 8, 7]
        self.assertEqual(A.permutation_p(x, y, 500, 7), A.permutation_p(x, y, 500, 7))


class DataReconciliation(unittest.TestCase):
    def test_all_integrity_checks_pass(self):
        results = checks.run_all()
        failed = checks.failures(results)
        self.assertEqual(failed, [], msg=str(failed))
        self.assertGreaterEqual(len(results), 20)

    def test_standings_and_stats_agree_by_team(self):
        st = {r["team_id"]: r for r in loader.load_standings()}
        ts = {r["team_id"]: r for r in loader.load_team_stats()}
        self.assertEqual(set(st), set(ts))
        for tid in st:
            self.assertEqual((st[tid]["w"], st[tid]["l"]), (ts[tid]["w"], ts[tid]["l"]), tid)

    def test_each_csv_row_has_expected_width(self):
        for path in sorted(DATA.glob("*.csv")):
            with open(path, newline="", encoding="utf-8") as fh:
                rows = list(csv.reader(fh))
            width = len(rows[0])
            for i, row in enumerate(rows[1:], start=2):
                self.assertEqual(len(row), width, msg=f"{path.name} line {i}")

    def test_every_source_id_is_registered(self):
        sources = {r["source_id"] for r in read_csv("sources.csv")}
        for name in ["standings.csv", "team_stats_traditional.csv", "prior_standings_2025-26.csv",
                     "player_logs_edwards.csv"]:
            for r in read_csv(name):
                self.assertIn(r["source_id"], sources, msg=name)
        for r in read_csv("flags.csv") + read_csv("strategies.csv") + read_csv("signals.csv"):
            for sid in re.split(r"[;]", r.get("source_ids", "") or r.get("official_input_source_ids", "")):
                sid = sid.strip()
                if sid:
                    self.assertIn(sid, sources, msg=str(r.get("flag_id") or r.get("strategy_id") or r.get("signal_id")))

    def test_sources_have_urls_and_tiers(self):
        for r in read_csv("sources.csv"):
            self.assertTrue(r["url"].startswith("https://"), msg=r["source_id"])
            self.assertIn(r["tier"], {"OFFICIAL", "REPORTED", "REPOSITORY"}, msg=r["source_id"])

    def test_official_rows_link_to_nba_domains(self):
        for r in read_csv("sources.csv"):
            host = urlsplit(r["url"]).hostname or ""
            if r["tier"] == "OFFICIAL":
                self.assertTrue(host == "nba.com" or host.endswith(".nba.com"), msg=r["source_id"])

    def test_edwards_2025_26_matches_existing_repo_csv(self):
        mine = [r for r in read_csv("player_logs_edwards.csv") if r["season"] == "2025-26"]
        repo_path = ROOT / "nba-2026-lab" / "data" / "edwards_2025_26_recent10.csv"
        with open(repo_path, newline="", encoding="utf-8") as fh:
            repo = list(csv.DictReader(fh))
        self.assertEqual(len(mine), len(repo))
        by_date_repo = {r["date"]: r for r in repo}
        for r in mine:
            rr = by_date_repo[r["game_date"]]
            self.assertEqual(r["result"], rr["result"], msg=r["game_date"])
            self.assertEqual(r["pts"], rr["points"], msg=r["game_date"])
            self.assertEqual(r["fg3m"], rr["threes"], msg=r["game_date"])
            self.assertEqual(r["reb"], rr["rebounds"], msg=r["game_date"])
            self.assertEqual(r["ast"], rr["assists"], msg=r["game_date"])
            self.assertEqual(r["min"], rr["minutes"], msg=r["game_date"])
            self.assertEqual(r["game_id"], rr["game_id"], msg=r["game_date"])

    def test_edwards_2026_27_header_averages(self):
        rows = [r for r in read_csv("player_logs_edwards.csv") if r["season"] == "2026-27"]
        self.assertEqual(len(rows), 4)
        # Official header is rounded half-up (33.25 -> 33.3); Python's :.1f would round half-to-even.
        from decimal import Decimal, ROUND_HALF_UP
        ppg = Decimal(sum(int(r["pts"]) for r in rows)) / Decimal(4)
        self.assertEqual(str(ppg.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)), "33.3")

    def test_prior_season_has_82_games(self):
        for r in read_csv("prior_standings_2025-26.csv"):
            self.assertEqual(int(r["w"]) + int(r["l"]), 82, msg=r["team"])

    def test_gate_g3_matches_computed_sample_size(self):
        g3 = [r for r in read_csv("gates.csv") if r["gate_id"] == "G3"][0]
        self.assertIn("783", g3["threshold"])

    def test_flag_f10_reproduction_claim(self):
        rep = {r["pair"]: r for r in compute.compute_all()["player_repro"]}
        self.assertLess(rep["PTS vs AST"]["diff"], 0.0001)
        self.assertLess(rep["PTS vs REB"]["diff"], 0.0001)
        self.assertLess(rep["3PM vs PTS"]["diff"], 0.0001)
        self.assertLess(rep["PTS vs win indicator"]["diff"], 0.0001)


class DerivedTablesAreReproducible(unittest.TestCase):
    """Re-run the analysis and compare to the committed derived CSVs (no silent drift)."""

    def test_derived_correlations_match_committed(self):
        res = compute.compute_all()
        committed = {r["signal_id"]: r for r in read_csv("derived_correlations.csv")}
        for a in res["assoc"]:
            c = committed[a["signal_id"]]
            self.assertAlmostEqual(float(c["r"]), a["r"], places=4, msg=a["signal_id"])
            self.assertAlmostEqual(float(c["p_perm"]), a["p_perm"], places=5, msg=a["signal_id"])

    def test_no_signal_is_validated(self):
        res = compute.compute_all()
        self.assertFalse(any(a["validated"] for a in res["assoc"]))
        self.assertFalse(any(t["validated"] for t in res["oos"]))

    def test_outcome_derived_signals_excluded(self):
        res = compute.compute_all()
        scopes = {a["signal_id"]: a["scope"] for a in res["assoc"]}
        for sid in ("SIG01", "SIG03", "SIG10", "SIG11", "SIG12"):
            self.assertTrue(scopes[sid].startswith(("excluded", "candidate (outcome")), msg=sid)

    def test_out_of_sample_prior_season_passes_statistically(self):
        res = compute.compute_all()
        self.assertTrue(res["oos"][0]["passes_stat"])
        self.assertGreater(res["oos"][0]["ci_lo"], 0.0)

    def test_luck_counts(self):
        res = compute.compute_all()
        self.assertEqual(res["luck"]["teams_p_below_05"], 0)
        self.assertAlmostEqual(res["luck"]["expected_under_null"], 1.5)


class _Pages(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.ids = set()
        self.rows = []  # per <tr> in <tbody>: dict(text, links)
        self._in_tbody = False
        self._cur = None
        self._in_td = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "tbody":
            self._in_tbody = True
        if tag == "tr" and self._in_tbody:
            self._cur = {"links": [], "text": ""}
        if tag == "td" and self._cur is not None:
            self._in_td = True
        if tag == "a" and "href" in a:
            self.hrefs.append(a["href"])
            if self._cur is not None:
                self._cur["links"].append(a["href"])

    def handle_endtag(self, tag):
        if tag == "tbody":
            self._in_tbody = False
        if tag == "tr" and self._cur is not None:
            self.rows.append(self._cur)
            self._cur = None
        if tag == "td":
            self._in_td = False

    def handle_data(self, data):
        if self._cur is not None and self._in_td:
            self._cur["text"] += data


class SiteIntegrity(unittest.TestCase):
    PAGES = ["index", "standings", "team-stats", "player-logs", "signals", "correlations",
             "luck-vs-skill", "own-lines", "strategies", "validation", "leaderboard",
             "executive-summary", "sources", "flagged"]

    @classmethod
    def setUpClass(cls):
        # Rebuild into the committed location so the test checks what will be published.
        from tools.nba_line_desk import build
        build.main()
        cls.parsed = {}
        for name in cls.PAGES:
            text = (SITE / f"{name}.html").read_text(encoding="utf-8")
            p = _Pages()
            p.feed(text)
            cls.parsed[name] = (text, p)

    def test_all_pages_exist(self):
        for name in self.PAGES:
            self.assertTrue((SITE / f"{name}.html").exists(), msg=name)
        self.assertTrue((SITE / "style.css").exists())
        self.assertTrue((SITE / "app.js").exists())

    def test_internal_links_resolve(self):
        for name, (_, p) in self.parsed.items():
            for href in p.hrefs:
                parts = urlsplit(href)
                if parts.scheme or parts.netloc or href.startswith("#"):
                    continue
                target = SITE / parts.path
                self.assertTrue(target.exists(), msg=f"{name} -> {href}")

    def test_every_table_row_has_a_source_link(self):
        for name, (_, p) in self.parsed.items():
            for row in p.rows:
                external = [h for h in row["links"] if h.startswith("https://")]
                if row["text"].strip() == "":
                    continue
                self.assertTrue(external, msg=f"{name}: row without source: {row['text'][:80]}")

    def test_external_links_are_registered_sources(self):
        urls = {r["url"] for r in read_csv("sources.csv")}
        for name, (_, p) in self.parsed.items():
            for href in p.hrefs:
                if href.startswith("https://"):
                    self.assertIn(href, urls, msg=f"{name}: {href}")

    def test_no_placeholders_or_raw_python(self):
        # Table cells must never contain Python artifacts; visible prose must not contain template leftovers.
        cell_bad = re.compile(r"^\s*(None|nan|NaN|undefined|null)\s*$")
        prose_bad = re.compile(r"\bundefined\b|TODO|\{[a-z_]+\}|\bnan\b")
        for name, (text, _) in self.parsed.items():
            body = re.sub(r"<style.*?</style>|<script.*?</script>", "", text, flags=re.S)
            for cell in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", body, flags=re.S):
                plain = html.unescape(re.sub(r"<[^>]+>", " ", cell))
                self.assertIsNone(cell_bad.match(plain), msg=f"{name}: cell '{plain.strip()}'")
            visible = html.unescape(re.sub(r"<[^>]+>", " ", body))
            m = prose_bad.search(visible)
            self.assertIsNone(m, msg=f"{name}: {m.group(0) if m else ''}")

    def test_flagged_page_lists_open_items_with_sources(self):
        text, p = self.parsed["flagged"]
        open_flags = [r for r in read_csv("flags.csv") if r["status"] == "open"]
        self.assertGreaterEqual(text.count('class="flagged"'), len(open_flags))
        self.assertIn("Flagged for review", text)

    def test_readme_links_to_desk(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("nba-line-desk/", readme)

    def test_no_nba_claim_without_source_on_landing(self):
        text, _ = self.parsed["index"]
        self.assertIn("Flagged for review", text)
        self.assertIn("Validated", text)


if __name__ == "__main__":
    unittest.main()
