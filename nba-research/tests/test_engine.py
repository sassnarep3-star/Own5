import csv
import hashlib
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import engine as e


class MathTests(unittest.TestCase):
    def test_binomial_tails_match_brute_force(self):
        for n in range(0, 13):
            for p in (0.2, 0.5, 0.8):
                for k in range(-1, n + 2):
                    brute = math.fsum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(max(0,k), n+1))
                    self.assertAlmostEqual(e.binom_sf(k,n,p), brute, places=12)
                    self.assertAlmostEqual(e.binom_cdf(k,n,p), 1-e.binom_sf(k+1,n,p), places=12)

    def test_binomial_edges(self):
        self.assertEqual(e.binom_sf(0,10,0.5),1)
        self.assertEqual(e.binom_sf(11,10,0.5),0)
        self.assertEqual(e.binom_sf(1,10,0),0)
        self.assertEqual(e.binom_sf(10,10,1),1)

    def test_clopper_pearson_edges(self):
        lo,hi=e.clopper_pearson(0,10)
        self.assertEqual(lo,0)
        self.assertAlmostEqual(hi,1-(0.025)**(1/10),places=10)
        lo,hi=e.clopper_pearson(10,10)
        self.assertAlmostEqual(lo,(0.025)**(1/10),places=10)
        self.assertEqual(hi,1)
        with self.assertRaises(ValueError): e.clopper_pearson(11,10)

    def test_exact_power_minimum(self):
        p0=110/210; n=e.minimum_n(p0,0.55,0.05,0.80)
        self.assertGreaterEqual(e.exact_power(n,p0,0.55,0.05),0.80)
        self.assertLess(e.exact_power(n-1,p0,0.55,0.05),0.80)
        self.assertEqual(n,2248)
        self.assertEqual(e.minimum_n(p0,0.55,0.05/8,0.80),4055)

    def test_power_rejects_invalid_inputs(self):
        with self.assertRaises(ValueError): e.minimum_n(0.6,0.5)
        with self.assertRaises(ValueError): e.minimum_n(0.5,0.55,alpha=0)

    def test_american_prices_and_no_vig(self):
        self.assertAlmostEqual(e.american_to_decimal(-110),1+100/110)
        self.assertAlmostEqual(e.american_to_decimal(150),2.5)
        self.assertAlmostEqual(e.american_to_prob(-110),110/210)
        self.assertAlmostEqual(e.american_to_prob(150),0.4)
        q=e.no_vig([-110,-110]); self.assertEqual(q,[0.5,0.5])
        with self.assertRaises(ValueError): e.american_to_decimal(0)
        with self.assertRaises(ValueError): e.no_vig([100,100])

    def test_holm_step_down(self):
        out=e.holm_adjust([0.01,0.04,0.03])
        self.assertAlmostEqual(out[0]['adjusted_p'],0.03)
        self.assertAlmostEqual(out[1]['adjusted_p'],0.06)
        self.assertAlmostEqual(out[2]['adjusted_p'],0.06)
        self.assertEqual([r['reject'] for r in out],[True,False,False])

    def test_pearson(self):
        self.assertAlmostEqual(e.pearson([1,2,3],[2,4,6]),1)
        self.assertAlmostEqual(e.pearson([1,2,3],[6,4,2]),-1)
        self.assertIsNone(e.pearson([1,1,1],[1,2,3]))
        self.assertIsNone(e.pearson([1,2],[1,2]))

    def test_deflated_sharpe_guards_and_monotonicity(self):
        self.assertIsNone(e.deflated_sharpe([0.1]*20,[0,0.1]))
        self.assertIsNone(e.deflated_sharpe([0.0]*40,[0,0.1]))
        self.assertIsNone(e.deflated_sharpe([0.1]*40,[0.1,0.1]))
        rng=__import__('random').Random(7)
        returns=[rng.gauss(0.05,1) for _ in range(200)]
        a=e.deflated_sharpe(returns,[-0.1,0.1])
        b=e.deflated_sharpe(returns,[-0.5,0.5])
        self.assertIsNotNone(a); self.assertIsNotNone(b)
        self.assertGreaterEqual(a,b)
        self.assertTrue(0<=a<=1 and 0<=b<=1)

    def test_cscv_pbo_guards_and_range(self):
        self.assertIsNone(e.cscv_pbo([[0.1,0.2]]*10))
        self.assertIsNone(e.cscv_pbo([[0.1,0.2]]*40,blocks=7))
        rng=__import__('random').Random(11)
        mat=[[rng.gauss(0,1) for _ in range(4)] for _ in range(80)]
        p=e.cscv_pbo(mat,blocks=8)
        self.assertIsNotNone(p); self.assertTrue(0<=p<=1)
        self.assertIsNone(e.cscv_pbo([[1,2]]*40+[[1]]*40))

    def test_bootstrap_deterministic_and_conditional(self):
        rows=e.read_csv('player_games.csv')
        a=e.block_bootstrap_ci(rows,'pts','tpm',reps=50,seed=1)
        b=e.block_bootstrap_ci(rows,'pts','tpm',reps=50,seed=1)
        self.assertEqual(a,b)
        self.assertLess(a[0],a[1])


class SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.names=['team_advanced_2026_27.csv','team_advanced_2025_26.csv','team_traditional_2026_27.csv','standings_2026_27.csv','schedule.csv','injuries.csv','players.csv','player_games.csv','market_snapshot.csv','bets.csv','sources.csv','flags.csv']
        cls.d={n:e.read_csv(n) for n in cls.names}

    def test_all_integrity_checks_pass(self):
        checks=e.verify_inputs(self.d)
        self.assertEqual(len(checks),15)
        self.assertTrue(all(c['status']=='PASS' for c in checks),checks)
        self.assertTrue(all(c['source_url'].startswith('https://') for c in checks))

    def test_tampered_record_fails(self):
        d={k:[dict(r) for r in v] for k,v in self.d.items()}
        d['standings_2026_27.csv'][0]['w']='99'
        checks=e.verify_inputs(d)
        self.assertTrue(any(c['check']=='Current record reconciliation' and c['status']=='FAIL' for c in checks))

    def test_tampered_market_fails(self):
        d={k:[dict(r) for r in v] for k,v in self.d.items()}
        d['market_snapshot.csv'][0]['line']='2.5'
        checks=e.verify_inputs(d)
        self.assertTrue(any(c['check']=='Market pair completeness' and c['status']=='FAIL' for c in checks))

    def test_duplicate_player_game_fails(self):
        d={k:[dict(r) for r in v] for k,v in self.d.items()}
        d['player_games.csv'].append(dict(d['player_games.csv'][0]))
        checks=e.verify_inputs(d)
        self.assertTrue(any(c['check']=='Player log coverage and uniqueness' and c['status']=='FAIL' for c in checks))

    def test_projection_units_and_neutral_baseline(self):
        team={'team_id':'1','team':'A','gp':'82','possessions':'8200','off_rating':'110','def_rating':'110','pace':'100'}
        away={**team,'team_id':'2','team':'B'}
        d={'team_advanced_2026_27.csv':[team,away],'team_advanced_2025_26.csv':[team,away],'schedule.csv':[{'game_id':'g','home_id':'1','away_id':'2'}]}
        lines,ratings,sens=e.project_lines(d)
        self.assertEqual(float(lines[0]['projected_home_points']),110)
        self.assertEqual(float(lines[0]['projected_away_points']),110)
        self.assertEqual(float(lines[0]['fair_total']),220)
        self.assertEqual(float(lines[0]['fair_home_spread']),0)
        self.assertEqual(lines[0]['model_win_probability'],'')
        self.assertEqual(len(sens),3)
        self.assertTrue(all(s['total']=='220.00' for s in sens))

    def test_shrinkage_weight(self):
        lines,ratings,sens=e.project_lines(self.d)
        orl=next(r for r in ratings if r['team_id']=='1610612753')
        self.assertAlmostEqual(float(orl['current_weight']),7/27,places=3)
        self.assertEqual(len(ratings),30)

    def test_market_edge_signs_and_blank_probabilities(self):
        lines,_,_=e.project_lines(self.d)
        comp=e.compare_markets(self.d,lines)
        self.assertEqual(len(comp),12)
        for gid in {r['game_id'] for r in comp}:
            for market in ('spread','total'):
                edges=[float(r['model_edge_points']) for r in comp if r['game_id']==gid and r['market']==market]
                self.assertAlmostEqual(sum(edges),0)
        self.assertTrue(all(r['model_probability']=='' and r['expected_value']=='' for r in comp))
        self.assertTrue(all(r['model_line']=='' and r['model_edge_points']=='' for r in comp if r['market']=='moneyline'))

    def test_prop_joint_counts_reconcile(self):
        rows=e.read_csv('prop_combinations.csv')
        self.assertEqual(len(rows),10)
        for r in rows:
            self.assertLessEqual(int(r['joint_hits']),int(r['n']))
            self.assertAlmostEqual(float(r['joint_probability']),int(r['joint_hits'])/int(r['n']),places=4)
            if float(r['independence_product'])>0:
                self.assertAlmostEqual(float(r['joint_lift']),float(r['joint_probability'])/float(r['independence_product']),places=3)
            self.assertEqual(r['market_probability'],''); self.assertEqual(r['edge'],'')

    def test_centering_reduces_pooled_points_assists_correlation(self):
        rows=e.read_csv('correlations.csv')
        pooled=next(float(r['pearson_r']) for r in rows if r['scope']=='Pooled (descriptive)' and r['x']=='pts' and r['y']=='ast')
        centered=next(float(r['pearson_r']) for r in rows if r['scope']=='Player-centered pooled' and r['x']=='pts' and r['y']=='ast')
        self.assertLess(abs(centered),abs(pooled))
        self.assertLess(abs(centered),0.1)

    def test_empty_ledger_blocks_every_strategy(self):
        with (ROOT/'strategies.json').open() as f: config=json.load(f)
        checks=e.verify_inputs(self.d)
        strategies,gates,board,prereg=e.evaluate_strategies(config,checks,[])
        self.assertEqual(len(strategies),8); self.assertEqual(len(gates),10); self.assertEqual(board,[])
        self.assertTrue(all(s['status']=='BLOCKED' and s['rank']=='' and s['reward']=='' for s in strategies))
        self.assertTrue(all(s['roi']=='' and s['clv']=='' and s['deflated_sharpe']=='' and s['pbo']=='' for s in strategies))
        self.assertEqual([g['gate_id'] for g in gates if g['status']=='PASS'],['G01','G02','G10'])
        self.assertEqual(prereg['sha256'],e.canonical_hash(config))

    def test_failed_integrity_blocks_provenance_gate(self):
        with (ROOT/'strategies.json').open() as f: config=json.load(f)
        checks=[{'status':'FAIL'}]
        strategies,gates,_,_=e.evaluate_strategies(config,checks,[])
        self.assertTrue(all(s['status']=='BLOCKED' for s in strategies))
        self.assertEqual(next(g for g in gates if g['gate_id']=='G01')['status'],'BLOCKED')

    def test_raw_rows_have_official_links_and_unknowns_blank(self):
        official=('https://www.nba.com/','https://official.nba.com/','https://ak-static.cms.nba.com/','https://sportsbook.fanduel.com/')
        for name in ['team_advanced_2026_27.csv','team_advanced_2025_26.csv','team_traditional_2026_27.csv','standings_2026_27.csv','schedule.csv','injuries.csv','players.csv','player_games.csv','market_snapshot.csv']:
            for r in self.d[name]:
                self.assertTrue(r['source_url'].startswith(official),(name,r))
        for r in self.d['market_snapshot.csv']:
            self.assertEqual(r['retrieved_at'],''); self.assertEqual(r['jurisdiction'],''); self.assertEqual(r['ticket_terms_url'],'')
        self.assertEqual(self.d['bets.csv'],[])

    def test_power_table_labels_illustrations(self):
        rows=e.read_csv('power.csv')
        self.assertEqual(len(rows),9)
        self.assertTrue(all('Hypothetical' in r['price_assumption'] or 'Illustration' in r['price_assumption'] for r in rows))
        self.assertTrue(all(r['source_url']==e.NIST_URL for r in rows))


class DeterminismTests(unittest.TestCase):
    def test_build_is_deterministic(self):
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data').glob('*') if p.suffix in ('.csv','.json') and p.name not in ('sources.csv','flags.csv')}
        # Include generated files only; raw inputs are unchanged by build.
        summary=e.build()
        after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data').glob('*') if p.suffix in ('.csv','.json') and p.name not in ('sources.csv','flags.csv')}
        self.assertEqual(before,after)
        self.assertEqual(summary['certified_strategies'],0)
        self.assertEqual(summary['settled_bets'],0)
        self.assertEqual(summary['integrity_passed'],summary['integrity_checks'])


if __name__=='__main__':
    unittest.main()
