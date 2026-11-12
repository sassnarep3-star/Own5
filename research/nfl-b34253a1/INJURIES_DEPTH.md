# Week 10 injury and depth-chart evidence

**Snapshot date:** 2026-11-12. **Injury-source timing:** midweek report/news snapshot before most Week 10 games; it is not a complete final inactives/participation record.

## Scope and results

- `injuries_depth_w10.csv` has **76 selected rows across 17 teams**. It is a deficiency/review list, not an exhaustive 32-team injury table. A team/player absent from it is not inferred healthy.
- The selected statuses comprise 63 DNP, 7 OUT, 2 NAMED STARTER, 1 QUESTIONABLE, 1 LP, 1 INJURED RESERVE, and 1 DNP/week-to-week observation. A practice DNP/LP is not equivalent to a final game designation.
- A published chart chain and `deepest_listed_string_slot` report the retrieved order only. A numbered listing is not proof a backup will be active or take snaps. Blank chart chain/position stays blank; actual Week 10 participation and confirmed replacement fields remain unfilled.
- The team-chart source register now has **32/32 club sites**. The 28 scheduled Week 10 teams use the previously checked chart pages; CHI, DEN, PHI, and TB were on bye. Those four chart URLs are now documented but do not create Week 10 injury rows or line adjustments.
- Houston's chart was image-only in the retrieved page, leaving its string assignments unverified. Two selected rows explicitly retain `DEPTH_ORDER_UNVERIFIED_IMAGE_ONLY`; nine chart-chain fields remain blank.

## Bye-team chart check completed

| Team | Week 10 status | Page note | Usage in this release |
|---|---|---|---|
| CHI | Bye | Club page states chart as of 2026-10-31. | Source coverage only; no Week 10 injury signal. |
| DEN | Bye | Current official club page did not display a chart update date in retrieved text; separate archive page is explicitly labelled unofficial and dated 2026-09-22. | Current page URL recorded; no Week 10 injury signal. |
| PHI | Bye | Club page explicitly labels the chart unofficial and compiled by the communications department; no update date shown. | Source coverage only; no Week 10 injury signal. |
| TB | Bye | Current club page did not display a chart update date in retrieved text. | Source coverage only; no Week 10 injury signal. |

All four links, the other 28 chart links, capture date, Week 10 status, and caveats are in `depth_chart_coverage_2026_w10.csv` and `sources_registry.csv`.

## Key limitations

1. The injury index can update during the week. Midweek DNP, LP, IR, OUT, or QUESTIONABLE text does not necessarily identify a final active/inactive player or the replacement who plays.
2. Club pages can call charts unofficial; the chart may be stale or omit a depth position. The source has no authoritative player-value conversion.
3. Nine selected rows have blank published depth chains, and some charts have blank slots. The blank is retained rather than populated from a third-party chart.
4. `actual_week10_participation` and `expected_starter_after_report` are blank; neither status nor string order is translated to points.
5. The 76-row subset is selected for observed injury/depth cascades in the fetched sources. It does not prove all other teams/players were healthy.

The injury-adjustment fields on all 14 Week 10 model rows are blank. See the [injury page](../../nfl-b34253a1/injuries.html), [`injuries_depth_w10.csv`](../../nfl-b34253a1/data/injuries_depth_w10.csv), and [flagged review](FLAGGED.md).
