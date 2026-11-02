#!/usr/bin/env python3
"""
link_check.py — validates the generated docs/ site.

- Internal links (relative hrefs): target file must exist in docs/.
- Anchors: #fragment must exist as id= in the target page (for same-site links).
- External http(s) links: URL syntax check + dedupe listing. NOTE: this sandbox's
  shell blocks non-GitHub hosts (curl exit35), so external reachability cannot be
  asserted from here; spot verification of representative external links was done
  interactively via page fetches (recorded in COORDINATION.md / verification page).
  Exit code reflects INTERNAL link integrity only.

Run: python3 tools/link_check.py   (add SITE_DIR=docs to check another site dir)
"""
import os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, os.environ.get("SITE_DIR", "line-lab"))

def main():
    files = sorted(f for f in os.listdir(DOCS) if f.endswith(".html"))
    href_re = re.compile(r'href=["\']([^"\']+)["\']')
    id_re = re.compile(r'id=["\']([^"\']+)["\']')
    ids = {}
    links = collections.defaultdict(list)
    ext = collections.Counter()
    for f in files:
        txt = open(os.path.join(DOCS, f)).read()
        ids[f] = set(id_re.findall(txt))
        for h in href_re.findall(txt):
            links[f].append(h)

    errors = []
    for f, hs in links.items():
        for h in hs:
            if h.startswith(("http://", "https://")):
                if " " in h or h.count('"'):
                    errors.append(f"{f}: malformed external URL {h}")
                ext[h] += 1
                continue
            if h.startswith("#"):
                frag = h[1:]
                if frag not in ids[f]:
                    errors.append(f"{f}: missing local anchor #{frag}")
                continue
            target, _, frag = h.partition("#")
            if target.endswith(".html"):
                if target not in files:
                    errors.append(f"{f}: broken internal link -> {target}")
                elif frag and frag not in ids[target]:
                    errors.append(f"{f}: broken anchor -> {target}#{frag}")
            # non-html relative links (none expected)

    print(f"pages: {len(files)}  internal+external links: {sum(len(v) for v in links.values())}  unique external: {len(ext)}")
    if errors:
        print(f"FAIL — {len(errors)} problem(s):")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("PASS — all internal links and anchors resolve.")
    print("External hosts referenced (spot-checked via fetch, not curl):")
    for host, n in sorted(collections.Counter(
            h.split("/")[2] for h in ext).items(), key=lambda kv: -kv[1]):
        print(f"  {host}: {n} links")

if __name__ == "__main__":
    main()
