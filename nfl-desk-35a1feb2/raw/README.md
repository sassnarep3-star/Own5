# Raw official reads — session 35a1feb2 (2026-11-17)

`official_reads_2026-11-17.txt` is a transcription of what the sandbox web fetcher returned for each URL
named in `../data/manifest.csv`, at the clock time named there.

Provenance, stated plainly:

* These bytes are **this session's transcription of the fetched page text**, not the league's raw HTTP body.
  The SHA-256 in the manifest proves the published tables were not edited after the read; it does **not**
  prove the league served those bytes. Prior sessions logged the same limitation and this one does not
  paper over it.
* `nfl.com` is unreachable from this sandbox by `curl`/`urllib` (`OpenSSL SSL_connect: SSL_ERROR_SYSCALL`),
  so the fetcher is the only read channel here. CI re-reads the same URLs from a GitHub runner for
  **freshness monitoring only**, never to overwrite a published number.
* Nothing here is inferred. Where a page had no value the line says `(blank)` or `NOT READ`.
* `verify.py` re-checks that every published number in the derived tables appears in this transcript, so a
  row cannot quietly gain a value the read did not contain.
