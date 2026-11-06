"""Offline integrity, sourcing, privacy and build checks for the static site."""
import importlib.util
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
spec = importlib.util.spec_from_file_location('sf_rent_build', ROOT / 'build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class PageAudit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.references = []
        self.rows = []
        self.current_row = None
        self.in_body = False
        self.in_table = False
        self.forms = 0
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'table':
            self.in_table = True
        if tag == 'tbody' and self.in_table:
            self.in_body = True
        if tag == 'tr' and self.in_body:
            self.current_row = {'id': attrs.get('data-record-id'),
                                'sources': (attrs.get('data-sources') or '').split(),
                                'links': []}
        if tag == 'a' and attrs.get('href'):
            self.references.append(attrs['href'])
            if self.current_row is not None:
                self.current_row['links'].append(attrs['href'])
        if tag in ('link', 'script') and attrs.get('href'):
            self.references.append(attrs['href'])
        if tag in ('img', 'script') and attrs.get('src'):
            self.references.append(attrs['src'])
        if tag == 'form':
            self.forms += 1
        if tag == 'script':
            self.scripts += 1

    def handle_endtag(self, tag):
        if tag == 'tr' and self.current_row is not None:
            self.rows.append(self.current_row)
            self.current_row = None
        if tag == 'tbody':
            self.in_body = False
        if tag == 'table':
            self.in_table = False


def audit_page(path):
    parser = PageAudit()
    parser.feed(path.read_text(encoding='utf-8'))
    parser.close()
    return parser


class EvidenceSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = sorted(ROOT.glob('*.html'))
        cls.audits = {path.name: audit_page(path) for path in cls.files}
        cls.rows_by_id = {row['id']: row for page in build.PAGES.values()
                          for section in page['sections'] for row in section['rows']}

    def test_generator_validation_and_committed_output(self):
        build.validate()
        result = subprocess.run([sys.executable, str(ROOT / 'build.py'), '--check'],
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(set(self.audits), {name + '.html' for name, _ in build.NAV})

    def test_all_table_rows_link_to_registered_official_sources(self):
        seen = set()
        for page, audit in self.audits.items():
            self.assertTrue(audit.rows, page)
            for row in audit.rows:
                self.assertTrue(row['id'], (page, row))
                self.assertNotIn(row['id'], seen, (page, row['id']))
                seen.add(row['id'])
                self.assertTrue(row['sources'], (page, row['id']))
                expected = {build.SOURCES[sid]['url'] for sid in row['sources']}
                self.assertEqual(set(row['links']), expected, (page, row['id']))
                for url in row['links']:
                    parsed = urlsplit(url)
                    self.assertEqual(parsed.scheme, 'https')
                    self.assertIn(parsed.hostname, build.ALLOWED_HOSTS)
        self.assertEqual(seen, set(self.rows_by_id) | set(build.SOURCES))

    def test_all_internal_links_and_fragments_exist(self):
        for name, audit in self.audits.items():
            for ref in audit.references:
                parsed = urlsplit(ref)
                if parsed.scheme or parsed.netloc:
                    continue
                target = (ROOT / name).parent / unquote(parsed.path) if parsed.path else ROOT / name
                if target.is_dir():
                    target /= 'index.html'
                self.assertTrue(target.exists(), (name, ref, target))
                if parsed.fragment:
                    self.assertIn(unquote(parsed.fragment), audit_page(target).ids, (name, ref))

    def test_private_and_unknown_values_remain_blank(self):
        # These stable row IDs identify property-specific facts, not tenant identity.
        for row_id in ('U01','U02','U03','U04','U05','U06','U07','U08'):
            self.assertEqual(self.rows_by_id[row_id]['cells'][1:3], ['', ''], row_id)
        for row_id in ('G01','G02','G03','G04','G05','G06','G07','G08',
                       'G09','G10','G11','G12','G15','R04','N05','F07','P04','P05'):
            self.assertEqual(self.rows_by_id[row_id]['cells'][1], '', row_id)
        self.assertIn('not verified', self.rows_by_id['G02']['cells'][2])
        self.assertIn('not verified', self.rows_by_id['G03']['cells'][2])

    def test_current_and_historical_rates_are_not_confused(self):
        self.assertEqual(self.rows_by_id['R01']['cells'][1], '1.6%')
        self.assertEqual(self.rows_by_id['R02']['cells'][1], '1.4%')
        self.assertEqual(self.rows_by_id['R03']['cells'][1], '1.7%')
        self.assertEqual(self.rows_by_id['R04']['cells'][1], '')
        self.assertIn('inconsistency', self.rows_by_id['G13']['cells'][1])
        self.assertIn('inconsistency', self.rows_by_id['G14']['cells'][1])

    def test_notice_example_is_not_service_ready(self):
        notice = (ROOT / 'notice.html').read_text(encoding='utf-8')
        self.assertIn('NOT READY TO SERVE', notice)
        self.assertIn('cannot itself change rent', notice)
        self.assertIn('independently reviewed before use', notice)

    def test_static_privacy_and_no_external_runtime(self):
        for name, audit in self.audits.items():
            self.assertEqual(audit.forms, 0, name)
            self.assertEqual(audit.scripts, 0, name)
            text = (ROOT / name).read_text(encoding='utf-8').lower()
            self.assertIn('not legal advice', text, name)
            self.assertNotIn('google-analytics', text)
            self.assertNotIn('localhost', text)
            if name != 'sources.html':
                self.assertIn('intentionally blank', text)
        self.assertNotIn('@import', (ROOT / 'assets/style.css').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
