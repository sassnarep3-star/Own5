"""Serve the built static dashboard for the Arena live preview."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT / "dist"))
server = ThreadingHTTPServer(("0.0.0.0", 8000), handler)
print("Own5 dashboard listening on 0.0.0.0:8000", flush=True)
server.serve_forever()
