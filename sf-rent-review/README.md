# SF Rent Review

An additive static GitHub Pages subsite at `/Own5/sf-rent-review/`. The snapshot is
2026-11-06. This is independent research, not legal advice or a notice to serve.
Unit-specific values are intentionally blank because private owner reports are
not confirmed by official property or lease records. Do not add tenant names,
initials, addresses, private documents or inferred unit values to this repository.

## Maintain and verify

```sh
python3 sf-rent-review/build.py
python3 research/sf-rent-review/build_audit.py
python3 -m unittest discover -s sf-rent-review/tests -v
python3 sf-rent-review/build.py --check
python3 research/sf-rent-review/build_audit.py --check
# After npm ci --ignore-scripts, with the repository root served on port 3000:
node sf-rent-review/tests/browser.cjs
```

Source scopes and review dates are in `data/sources.json`; display content and
stable record IDs are in `data/pages.json`. The build generates eight committed
HTML pages without remote fonts, scripts, analytics, a backend or a form. Every
table row has an official government link; the legal link on a blank is not
verification of the private fact. The research folder contains a row-by-row
audit and source irregularities. Refresh the official sources and update the
snapshot before relying on a rate or procedural rule in the future.
