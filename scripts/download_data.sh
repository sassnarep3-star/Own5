#!/usr/bin/env bash
# Downloads pinned input datasets via api.github.com (release CDN is not reachable from this sandbox).
# Pins (commit SHA at fetch time):
#   spreadspoke @ 1d309cb7f8f58a9eceb36293979dbcb1af70db94 (tobycrabtree/spreadspoke, master)
#   pbp         @ 352c9c9b0bce0ffa8ce85681cf9ed50c0398f462 (brianfoshee/nfl-play-by-play-data, master)
set -e
RAW=data/raw; mkdir -p "$RAW" /tmp/pbp
for y in 2002 2003 2004 2005 2006 2007 2008 2009 2010 2011 2012; do
  f="/tmp/pbp/${y}_nfl_pbp_data.csv"
  if [ ! -s "$f" ]; then
    curl -s --max-time 300 -H "Accept: application/vnd.github.raw" \
      "https://api.github.com/repos/brianfoshee/nfl-play-by-play-data/contents/${y}_nfl_pbp_data.csv" -o "$f"
    echo "fetched $y $(stat -c%s "$f") bytes"
  fi
done
echo DONE
