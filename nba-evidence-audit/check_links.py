"""Check filesystem-backed relative links in committed HTML (not remote URLs or fragments)."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parent.parent
class Links(HTMLParser):
    def __init__(self): super().__init__(); self.values=[]
    def handle_starttag(self,tag,attrs):
        self.values.extend(value for key,value in attrs if key in ('href','src') and value)

checked=0
broken=[]
for page in sorted(ROOT.rglob('*.html')):
    if any(part in {'.git','node_modules'} for part in page.relative_to(ROOT).parts): continue
    parser=Links(); parser.feed(page.read_text(encoding='utf-8',errors='replace'))
    for value in parser.values:
        url=urlsplit(value)
        # External links and fragment-only links need separate live/anchor testing.
        if url.scheme or url.netloc or not url.path or url.path.startswith('/') or '{' in url.path:
            continue
        target=page.parent/unquote(url.path)
        if target.is_dir(): target=target/'index.html'
        checked+=1
        if not target.is_file(): broken.append(f'{page.relative_to(ROOT)}: {value}')
print(f'Checked {checked} local relative links; {len(broken)} missing. External URLs, fragments and root-relative links excluded.')
for entry in broken: print(entry)
raise SystemExit(bool(broken))
