#!/usr/bin/env python3
"""Deterministic NFL baseline line-originator and evidence/validation engine.

This is a deliberately simple, auditable starting point, not a trained or validated
betting model. It uses only completed official 2026 NFL points through Week 9. It does
not apply numeric injury adjustments because no official, validated player-value to
points conversion is available in this snapshot; injury-adjusted line cells stay blank.
"""
from __future__ import annotations
import csv, json, math
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
AS_OF = "2026-11-12"
NFL_STANDINGS = "https://www.nfl.com/standings/league/2026/REG"
NFL_INJURIES = "https://www.nfl.com/injuries/"
NFL_W10_REPORT = "https://www.nfl.com/news/nfl-week-10-injury-report-2026-season"
NFL_NEWS = "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11"
NFL_PASS = "https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all"
NFL_RUSH = "https://www.nfl.com/stats/team-stats/offense/rushing/2026/reg/all"
NFL_DEF_PASS = "https://www.nfl.com/stats/team-stats/defense/passing/2026/reg/all"
NFL_DEF_RUSH = "https://www.nfl.com/stats/team-stats/defense/rushing/2026/reg/all"
NFL_PLAYER_PASS = "https://www.nfl.com/stats/player-stats/category/passing/2026/reg/all/passingyards/desc"
NFL_PLAYER_RUSH = "https://www.nfl.com/stats/player-stats/category/rushing/2026/reg/all/rushingyards/desc"
NFL_PLAYER_REC = "https://www.nfl.com/stats/player-stats/category/receiving/2026/reg/all/receivingreceptions/desc"


def read_csv(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(name, rows, fields=None):
    if fields is None:
        fields = list(rows[0]) if rows else []
    with (DATA / name).open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
        w.writeheader(); w.writerows(rows)

def fnum(v):
    return float(v) if v not in (None, "") else math.nan

def half(x):
    """Round to the nearest half-point, ties away from zero."""
    return math.copysign(math.floor(abs(x)*2 + 0.5)/2, x)

def fmt(x, places=2):
    if abs(x) < 0.5 * (10 ** (-places)):
        x = 0.0
    return f"{x:.{places}f}"

def p_fmt(p):
    return f"{p:.6g}"

def load_inputs():
    standings={r["team"]:{**r,"wins":int(r["wins"]),"losses":int(r["losses"]),"ties":int(r["ties"]),"points_for":int(r["points_for"]),"points_against":int(r["points_against"])} for r in read_csv("standings_2026_w10.csv")}
    games=[]
    for r in read_csv("games_2026_w1_w9.csv"):
        g=dict(r); g["week"]=int(r["week"]); g["away_points"]=int(r["away_points"]); g["home_points"]=int(r["home_points"]); games.append(g)
    schedule=read_csv("schedule_2026_w10.csv")
    quotes=read_csv("market_quotes_2026_w10.csv")
    injuries=read_csv("injuries_depth_w10.csv")
    stats=read_csv("team_stats_2026_w10.csv")
    return standings,games,schedule,quotes,injuries,stats

def reconcile(standings,games):
    totals={t:{"wins":0,"losses":0,"ties":0,"points_for":0,"points_against":0,"games":0} for t in standings}
    for g in games:
        a,h=g["away_team"],g["home_team"]; ap,hp=g["away_points"],g["home_points"]
        for t,pf,pa in ((a,ap,hp),(h,hp,ap)):
            q=totals[t]; q["games"]+=1; q["points_for"]+=pf; q["points_against"]+=pa
        if ap>hp: totals[a]["wins"]+=1; totals[h]["losses"]+=1
        elif hp>ap: totals[h]["wins"]+=1; totals[a]["losses"]+=1
        else: totals[a]["ties"]+=1; totals[h]["ties"]+=1
    diffs=[]
    for t,off in standings.items():
        got=totals[t]
        for k in ("wins","losses","ties","points_for","points_against"):
            exp=int(off[k])
            if got[k]!=exp: diffs.append({"team":t,"field":k,"got":got[k],"expected":exp})
    weeks=Counter(g["week"] for g in games)
    report={"as_of":AS_OF,"source_url":NFL_STANDINGS,"games":len(games),"teams":len(standings),"week_counts":dict(sorted(weeks.items())),
       "teams_reconciled":len(standings)-len({d["team"] for d in diffs}),"fields_checked_per_team":["W","L","T","PF","PA"],"mismatches":diffs,
       "status":"PASS" if len(games)==136 and len(standings)==32 and not diffs else "FAIL",
       "scope_note":"136 completed 2026 Weeks 1-9 results reconciled exactly to NFL.com standings before Week 10. Each game row links to the official NFL.com game page."}
    (DATA/"game_reconciliation.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return totals,report

# Student-t two-tailed p-values using regularized incomplete beta, standard library only.
def _betacf(a,b,x):
    maxit=200; eps=3e-14; fpmin=1e-300
    qab=a+b; qap=a+1; qam=a-1
    c=1.0; d=1.0-qab*x/qap
    if abs(d)<fpmin: d=fpmin
    d=1.0/d; h=d
    for m in range(1,maxit+1):
        m2=2*m
        aa=m*(b-m)*x/((qam+m2)*(a+m2))
        d=1.0+aa*d
        if abs(d)<fpmin:d=fpmin
        c=1.0+aa/c
        if abs(c)<fpmin:c=fpmin
        d=1.0/d; h*=d*c
        aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2))
        d=1.0+aa*d
        if abs(d)<fpmin:d=fpmin
        c=1.0+aa/c
        if abs(c)<fpmin:c=fpmin
        d=1.0/d; delta=d*c; h*=delta
        if abs(delta-1.0)<eps: break
    return h

def _betai(a,b,x):
    if x<0 or x>1: raise ValueError("beta x outside 0..1")
    if x==0 or x==1:return x
    bt=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log1p(-x))
    if x < (a+1)/(a+b+2): return bt*_betacf(a,b,x)/a
    return 1-bt*_betacf(b,a,1-x)/b

def t_cdf(t,df):
    if df<=0: return math.nan
    x=df/(df+t*t)
    ib=_betai(df/2,0.5,x)
    return 1-0.5*ib if t>=0 else 0.5*ib

def pearson(xs,ys):
    n=len(xs)
    if n<2 or n!=len(ys): return math.nan
    mx=sum(xs)/n; my=sum(ys)/n
    sx=sum((x-mx)**2 for x in xs); sy=sum((y-my)**2 for y in ys)
    if sx==0 or sy==0:return math.nan
    return sum((x-mx)*(y-my) for x,y in zip(xs,ys))/math.sqrt(sx*sy)

def corr_stats(xs,ys):
    n=len(xs); r=pearson(xs,ys)
    if not math.isfinite(r) or n<4:return {"r":"","p":"","ci_low":"","ci_high":"","n":n}
    rc=max(-0.999999999,min(0.999999999,r))
    df=n-2
    t=abs(rc)*math.sqrt(df/(1-rc*rc))
    # Direct beta-tail evaluation avoids cancellation to zero for small p-values.
    p=_betai(df/2,0.5,df/(df+t*t))
    z=math.atanh(rc); se=1/math.sqrt(n-3)
    return {"r":fmt(r,6),"p":p_fmt(p),"ci_low":fmt(math.tanh(z-1.96*se),6),"ci_high":fmt(math.tanh(z+1.96*se),6),"n":n}

def build_walk_forward(games):
    history=defaultdict(lambda:{"games":0,"pf":0,"pa":0})
    rows=[]
    for week in sorted({g["week"] for g in games}):
        week_games=[g for g in games if g["week"]==week]
        if week>1:
            for g in week_games:
                a,h=g["away_team"],g["home_team"]
                ha,hh=history[a],history[h]
                if not ha["games"] or not hh["games"]: raise ValueError(f"no prior-week history for week {week}: {a}/{h}")
                # Symmetric PF/G + opponent PA/G baseline. No explicit HFA or injury modifier.
                away_expected=(ha["pf"]/ha["games"]+hh["pa"]/hh["games"])/2
                home_expected=(hh["pf"]/hh["games"]+ha["pa"]/ha["games"])/2
                pred=home_expected-away_expected; actual=g["home_points"]-g["away_points"]
                rows.append({"week":week,"game_date":g["date"],"away_team":a,"home_team":h,"training_cutoff":"end_of_week_"+str(week-1),
                    "projected_home_margin":fmt(pred,4),"actual_home_margin":actual,"residual_actual_minus_projected":fmt(actual-pred,4),
                    "model_method":"(home PF/G + away PA/G)/2 - (away PF/G + home PA/G)/2; HFA=0; no injuries",
                    "source_url":g["source_url"],"input_standings_source_url":NFL_STANDINGS})
        # Update after all games in week are forecast, avoiding same-week look-ahead.
        for g in week_games:
            a,h=g["away_team"],g["home_team"]
            for t,pf,pa in ((a,g["away_points"],g["home_points"]),(h,g["home_points"],g["away_points"])):
                history[t]["games"]+=1; history[t]["pf"]+=pf; history[t]["pa"]+=pa
    write_csv("walk_forward_2026_w2_w9.csv",rows)
    actual=[float(r["actual_home_margin"]) for r in rows]
    pred=[float(r["projected_home_margin"]) for r in rows]
    rstats=corr_stats(pred,actual)
    summary={"as_of":AS_OF,"n_games":len(rows),"prediction_method":"Pre-week rolling PF/G and PA/G; no same-week data, no HFA, no injury adjustment.",
      "mae_points":fmt(sum(abs(a-p) for a,p in zip(actual,pred))/len(rows),4) if rows else "",
      "mean_error_actual_minus_projected":fmt(sum(a-p for a,p in zip(actual,pred))/len(rows),4) if rows else "",
      "pearson_projected_vs_actual":rstats,"status":"EXPLORATORY_DESCRIPTIVE_ONLY",
      "limitations":"2026 in-sample walk-forward, 120 games, one season; no bookmaker price/closing line, no bet ledger, no clustered confidence interval. It does not establish profitability or skill."}
    (DATA/"walk_forward_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return rows,summary

def make_correlations(standings,totals,wf_rows):
    teams=sorted(standings)
    winpct={t:(standings[t]["wins"]+0.5*standings[t]["ties"])/(standings[t]["wins"]+standings[t]["losses"]+standings[t]["ties"]) for t in teams}
    pfpg={t:standings[t]["points_for"]/(standings[t]["wins"]+standings[t]["losses"]+standings[t]["ties"]) for t in teams}
    papg={t:standings[t]["points_against"]/(standings[t]["wins"]+standings[t]["losses"]+standings[t]["ties"]) for t in teams}
    metrics=[
      ("CORR-01","team PF per game","official win percentage",[pfpg[t] for t in teams],[winpct[t] for t in teams],NFL_STANDINGS,"2026 team-level ecological association; not causal."),
      ("CORR-02","team PA per game","official win percentage",[papg[t] for t in teams],[winpct[t] for t in teams],NFL_STANDINGS,"Higher PA/G may associate negatively; team-level ecological association."),
      ("CORR-03","team net points per game","official win percentage",[pfpg[t]-papg[t] for t in teams],[winpct[t] for t in teams],NFL_STANDINGS,"Same standings inputs; descriptive association, not independent validation."),
      ("CORR-04","pre-week model projected home margin","actual home margin",[float(r["projected_home_margin"]) for r in wf_rows],[float(r["actual_home_margin"]) for r in wf_rows],NFL_STANDINGS,"Walk-forward calculation from official game outcomes; one season, within-season dependence not adjusted."),
    ]
    out=[]
    for cid,xlab,ylab,x,y,url,note in metrics:
        q=corr_stats(x,y)
        out.append({"correlation_id":cid,"metric_x":xlab,"metric_y":ylab,"pearson_r":q["r"],"p_value_two_sided":q["p"],"ci95_low_fisher_z":q["ci_low"],"ci95_high_fisher_z":q["ci_high"],"n":q["n"],"source_url":url,"source_game_results_url":"https://www.nfl.com/schedules/2026/by-week/week-9" if cid=="CORR-04" else "","status":"COMPUTED_DESCRIPTIVE","caveat":note})
    for cid,xlab,ylab,url in [
       ("CORR-05","paired player passing prop outcomes","paired player receiving prop outcomes",NFL_PLAYER_PASS),
       ("CORR-06","paired player rushing prop outcomes","paired player receiving prop outcomes",NFL_PLAYER_RUSH),
       ("CORR-07","same-game prop leg settlement outcomes","joint parlay outcome",NFL_PLAYER_REC),
    ]:
        out.append({"correlation_id":cid,"metric_x":xlab,"metric_y":ylab,"pearson_r":"","p_value_two_sided":"","ci95_low_fisher_z":"","ci95_high_fisher_z":"","n":"","source_url":url,"source_game_results_url":"","status":"NOT_COMPUTABLE_MISSING_PAIRED_GAME_LOGS_AND_SETTLEMENTS","caveat":"No paired official game-level player-prop outcomes, market lines and settlement ledger were archived; blank by policy."})
    write_csv("correlations_2026.csv",out)
    return out

def make_model_lines(standings,schedule,quotes,injuries):
    quote_map=defaultdict(list)
    for q in quotes: quote_map[(q["away_team"],q["home_team"])].append(q)
    exp_counts=defaultdict(lambda:{"offense":0,"defense":0})
    for r in injuries:
        if r["verification_status"].startswith("VERIFIED") and r["actual_week10_participation"]=="":
            if r["side"] in ("offense","defense") and r["published_depth_chain"]:
                # This is only a count of selected listed-depth observations, not a score impact.
                exp_counts[r["team"]][r["side"]]+=1
    rows=[]
    for g in schedule:
        if g["status"]!="SCHEDULED": continue
        a,h=g["away_team"],g["home_team"]
        sa,sh=standings[a],standings[h]
        ga=sa["wins"]+sa["losses"]+sa["ties"]; gh=sh["wins"]+sh["losses"]+sh["ties"]
        away_pts=(sa["points_for"]/ga+sh["points_against"]/gh)/2
        home_pts=(sh["points_for"]/gh+sa["points_against"]/ga)/2
        away_round=half(away_pts); home_round=half(home_pts)
        margin=home_round-away_round
        model_home_spread=-margin; model_total=home_round+away_round
        qq=quote_map[(a,h)]
        if len(qq)!=2: raise ValueError(f"expected two book quotes for {a}@{h}; got {len(qq)}")
        qhome=sum(float(q["home_spread"]) for q in qq)/len(qq)
        qtotal=sum(float(q["total_points"]) for q in qq)/len(qq)
        q_sources=";".join(q["source_url"] for q in qq)
        rows.append({"week":10,"date":g["date"],"kickoff_et":g["kickoff_et"],"away_team":a,"home_team":h,
            "base_away_points":fmt(away_round,1),"base_home_points":fmt(home_round,1),"base_home_margin":fmt(margin,1),"model_home_spread":fmt(model_home_spread,1),"model_total":fmt(model_total,1),
            "injury_adjustment_away_points":"","injury_adjustment_home_points":"","injury_adjusted_home_spread":"","injury_adjusted_total":"",
            "selected_reported_offense_depth_observations_away":exp_counts[a]["offense"],"selected_reported_defense_depth_observations_away":exp_counts[a]["defense"],
            "selected_reported_offense_depth_observations_home":exp_counts[h]["offense"],"selected_reported_defense_depth_observations_home":exp_counts[h]["defense"],
            "market_home_spread_mean_two_books":fmt(qhome,2),"market_total_mean_two_books":fmt(qtotal,2),
            "model_home_margin_minus_market_home_line":fmt(margin+qhome,2),"model_total_minus_market_total":fmt(model_total-qtotal,2),
            "market_quotes":"DraftKings;FanDuel","market_quote_date":AS_OF,"market_quote_exact_time_utc":"","market_quote_timestamp_status":"DATE_ONLY; source page supplied no preserved UTC capture time",
            "line_status":"BASELINE_EXPLORATORY; NOT INJURY_ADJUSTED; NOT A BET RECOMMENDATION",
            "source_url":g["source_url"],"source_standings_url":NFL_STANDINGS,"source_market_urls":q_sources,"source_injury_report_url":NFL_W10_REPORT,
            "limitation":"Numeric injury coefficient and final active/inactive list unavailable; adjusted line blank and FLG-02/FLG-03 apply."})
    write_csv("model_lines_2026_w10.csv",rows)
    return rows

def write_competition_tables():
    strategies=[
      {"strategy_id":"STR-01","name":"Rolling team scoring-differential spread baseline","category":"Single-game spread","hypothesis":"Compare a no-HFA rolling PF/G + opponent PA/G score projection to contemporaneous book spread; register direction and threshold before testing.","signal_fields":"model_home_margin_minus_market_home_line","current_evidence":"2026 Week 10 baseline lines and Week 2-9 walk-forward accuracy are descriptive only.","status":"RESEARCH_ONLY_NOT_VALIDATED","required_missing":"historical timestamped prices, closing prices, complete bet/settlement ledger, prospective holdout","source_url":NFL_STANDINGS,"secondary_source_url":NFL_W10_REPORT},
      {"strategy_id":"STR-02","name":"Rolling offense/defense total baseline","category":"Single-game total","hypothesis":"Compare symmetric team scoring projections to two-book total consensus; calibrate uncertainty before any use.","signal_fields":"model_total_minus_market_total","current_evidence":"Own baseline totals and two-book dated snapshot; no return/CLV evaluation.","status":"RESEARCH_ONLY_NOT_VALIDATED","required_missing":"timestamped total prices, closing prices, settlement ledger, holdout calibration","source_url":NFL_STANDINGS,"secondary_source_url":"https://sportsbook.fanduel.com/navigation/nfl"},
      {"strategy_id":"STR-03","name":"Cross-game parlay probability model","category":"Parlay","hypothesis":"Estimate joint outcome probability from game-level model probabilities and dependence; compare to exact offered parlay price after margin.","signal_fields":"joint_probability; de_vigged_joint_market_probability; net_EV","current_evidence":"No joint outcome probabilities or wager ledger computed.","status":"BLOCKED_MISSING_EVIDENCE","required_missing":"timestamped multi-leg odds, event-level calibrated probabilities, historical joint outcomes, settlement rules","source_url":"https://www.nfl.com/schedules/2026/by-week/week-10","secondary_source_url":"https://sportsbook.fanduel.com/navigation/nfl"},
      {"strategy_id":"STR-04","name":"Same-game parlay dependence model","category":"Same-game parlay","hypothesis":"Estimate conditional same-game leg dependence from paired official game-level outcomes and compare to bookmaker price.","signal_fields":"joint_probability; empirical_phi_or_joint_frequency; de_vigged_price","current_evidence":"Correlation coefficients, joint rates and fair odds intentionally blank.","status":"BLOCKED_MISSING_PAIRED_OUTCOMES","required_missing":"paired player/game logs, exact prop lines and prices, settlement definitions, joint validation sample","source_url":NFL_PLAYER_REC,"secondary_source_url":"https://sportsbook.fanduel.com/navigation/nfl"},
      {"strategy_id":"STR-05","name":"Player-prop combo: passing + receiver production","category":"Player-prop combination","hypothesis":"Test paired QB passing and target receiver receiving outcomes, conditioned on starters, opponent and usage; do not multiply marginal probabilities unless independence is tested.","signal_fields":"player-game passing/receiving paired residuals; exact prop line; joint outcome","current_evidence":"Official 2026 aggregate player leaders pages exist; no canonical paired game-log extract or prop price ledger.","status":"BLOCKED_MISSING_PAIRED_GAME_LOGS","required_missing":"official paired player game logs, as-of starter status, prop price history and settlements","source_url":NFL_PLAYER_PASS,"secondary_source_url":NFL_PLAYER_REC},
      {"strategy_id":"STR-06","name":"Depth-chart-aware availability adjustment","category":"Availability-adjusted spread/total","hypothesis":"Apply a pre-estimated position/player replacement-value coefficient only when a documented starter absence and active replacement are confirmed.","signal_fields":"verified_inactive_starter; confirmed replacement; calibrated delta-EPA/score; uncertainty","current_evidence":"76 selected status/depth observations; no validated conversion from string slot to points.","status":"BLOCKED_UNCALIBRATED_INJURY_COEFFICIENTS","required_missing":"final active list, player-level snaps/production, replacement-level baseline, out-of-sample effect estimate","source_url":NFL_INJURIES,"secondary_source_url":NFL_W10_REPORT},
    ]
    write_csv("strategies_2026.csv",strategies)
    gates=[
      ("G0","Source integrity","All inputs have source URL, capture date, schema and row provenance; reconcile scores/records.","Input files; 32/32 and 136-game reconciliation","PASS"),
      ("G1","Quote timestamp and executable price","Every wager has book, jurisdiction, line, odds, quote time and closing quote from an approved source.","No persistent UTC capture time; no historical quote ledger","BLOCKED"),
      ("G2","Pre-registration and code freeze","Strategy, markets, selection rule, primary endpoint, sample horizon and analysis plan are hashed before outcomes.","No prospectively registered strategy ledger","BLOCKED"),
      ("G3","No look-ahead / chronology","Every feature timestamp precedes market quote; holdout split is time-ordered; same-week outcomes do not leak.","One descriptive walk-forward backtest only; no quote/feature timestamps","BLOCKED"),
      ("G4","Power and independent validation","Holdout sample size is derived from predeclared minimum useful effect, alpha, power and clustering; replicate in later season.","No predeclared effect size or prospective holdout; numeric threshold not invented","BLOCKED"),
      ("G5","Multiplicity and researcher degrees of freedom","Correct family-wise error / FDR over all tested strategies and markets; publish all trials.","No complete registered trial family / results ledger","BLOCKED"),
      ("G6","Probability calibration and joint dependence","Probability calibration passes a preregistered scoring rule; parlays require direct joint outcome/price comparison.","No event-level calibrated probabilities or paired player-prop outcomes","BLOCKED"),
      ("G7","Net returns / closing-line value","Grade all selections at recorded prices, settlement rules and costs; report ROI and CLV with clustered CIs.","No wager ledger, historical prices, fees or closing quotes","BLOCKED"),
      ("G8","Injury and lineup verification","Use final inactive/active list and verified replacement; missing depth or uncalibrated value stays blank.","Weekly static status sample; active list and position-to-points coefficients missing","BLOCKED"),
      ("G9","Luck-adjusted ranking","Rank only if G0-G8 pass; use time-blocked bootstrap or suitable hierarchical model and multiplicity-adjusted uncertainty.","No eligible strategy results; no luck-adjusted scores computed","BLOCKED"),
      ("G10","Competition rewards and governance","Publish eligibility, independent audit, budget source, award values, jurisdiction and payment policy before entry.","No competition charter/budget or funded reward amounts","BLOCKED"),
    ]
    sources=[NFL_STANDINGS,NFL_W10_REPORT,NFL_STANDINGS,"https://www.nfl.com/schedules/2026/by-week/week-10","https://www.nfl.com/news/2026-27-national-football-league-important-dates",NFL_PLAYER_REC,"https://sportsbook.fanduel.com/navigation/nfl",NFL_INJURIES,NFL_W10_REPORT,NFL_STANDINGS,"https://www.nfl.com/standings/league/2026/REG"]
    # row 4 citation above is an official NFL article but not a numerical power standard; policy basis is explicit.
    out=[]
    for i,(gid,name,rule,evidence,status) in enumerate(gates):
        out.append({"gate_id":gid,"gate_name":name,"mandatory_rule":rule,"current_evidence":evidence,"status":status,
          "source_url":sources[i],"policy_note":"Competition rule proposed by this project; not an NFL certification standard."})
    write_csv("validation_gates_2026.csv",out)
    leaderboard=[]
    for s in strategies:
        leaderboard.append({"strategy_id":s["strategy_id"],"strategy_name":s["name"],"category":s["category"],"rank":"","graded_bets":"0","win_rate":"","net_roi":"","risk_adjusted_skill_score":"","luck_adjusted_ci":"","gates_passed":"0/11","status":"NO_QUALIFIED_ENTRY","proposed_reward":"Non-cash recognition / research allocation proposal; amount blank, unfunded and not awarded","source_url":s["source_url"],"strategy_source_url":s.get("secondary_source_url","")})
    write_csv("leaderboard_2026.csv",leaderboard)
    luck=[
      {"item_id":"LUCK-01","metric":"Luck-adjusted strategy score","estimate":"","n":"","method":"Block-bootstrap net return / skill interval over pre-registered time blocks; do not treat bet outcomes as independent when they share a game/week.","status":"NOT_COMPUTABLE_NO_GRADED_BETS","source_url":"https://sportsbook.fanduel.com/navigation/nfl","note":"No settled bet ledger, historical prices or eligible strategy; no performance rank emitted."},
      {"item_id":"LUCK-02","metric":"Required sample size","estimate":"","n":"","method":"Power analysis from a preregistered smallest useful edge, baseline price/break-even rate, alpha, target power and clustering design.","status":"NOT_COMPUTABLE_DESIGN_INPUTS_MISSING","source_url":"https://www.nfl.com/standings/league/2026/REG","note":"Inputs are not supplied by the official standings; no arbitrary minimum sample threshold invented."},
      {"item_id":"LUCK-03","metric":"Reward eligibility","estimate":"","n":"","method":"Award only after all mandatory gates pass and an independent audit confirms a lower uncertainty bound above the preregistered benchmark.","status":"BLOCKED_UNFUNDED_NO_VALIDATED_ENTRANTS","source_url":"https://www.nfl.com/","note":"No funded award amount or payment program verified."},
    ]
    write_csv("luck_skill_2026.csv",luck)

def main():
    standings,games,schedule,quotes,injuries,stats=load_inputs()
    if len(standings)!=32 or len(games)!=136: raise SystemExit("fail: expected 32 standings rows and 136 final games")
    teams=set(standings)
    if set(r["team"] for r in stats)!=teams: raise SystemExit("fail: team stats team set mismatch")
    if len([r for r in schedule if r["status"]=="SCHEDULED"])!=14: raise SystemExit("fail: expected 14 Week 10 games")
    if len(quotes)!=28: raise SystemExit("fail: expected 28 two-book quote rows")
    totals,report=reconcile(standings,games)
    if report["status"]!="PASS": raise SystemExit(json.dumps(report["mismatches"],indent=2))
    wf,wf_summary=build_walk_forward(games)
    corr=make_correlations(standings,totals,wf)
    model=make_model_lines(standings,schedule,quotes,injuries)
    write_competition_tables()
    print(json.dumps({"status":"PASS","game_reconciliation":report["status"],"teams":len(standings),"completed_games":len(games),"week10_lines":len(model),"walk_forward_games":len(wf),"walk_forward_mae":wf_summary["mae_points"],"correlations":len(corr),"selected_injury_rows":len(injuries)},indent=2))

if __name__=="__main__": main()
