#!/usr/bin/env python3
"""Check that every local reference resolves on disk and over HTTP."""
import http.client
import re
import subprocess
import sys
import time
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8753
html = (ROOT / "index.html").read_text()
js = (ROOT / "static/js/main.js").read_text()
failures = []

# --- well-formedness / tag balance -----------------------------------------
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


class Checker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.ids = set()
        self.anchors = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            if a["id"] in self.ids:
                self.errors.append(f"duplicate id: {a['id']}")
            self.ids.add(a["id"])
        href = a.get("href", "")
        if href.startswith("#"):
            self.anchors.append(href[1:])
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"stray </{tag}>")
        elif self.stack[-1][0] != tag:
            self.errors.append(f"expected </{self.stack[-1][0]}> from line "
                               f"{self.stack[-1][1][0]}, got </{tag}> at {self.getpos()[0]}")
        else:
            self.stack.pop()


checker = Checker()
checker.feed(html)
failures += checker.errors
failures += [f"unclosed <{t}> at line {p[0]}" for t, p in checker.stack]
for anchor in sorted(set(checker.anchors)):
    if anchor and anchor not in checker.ids:
        failures.append(f"internal href #{anchor} has no matching id")

# --- local references resolve on disk --------------------------------------
refs = set(re.findall(r'(?:src|href|poster|content)="((?:static|tools)/[^"]+)"', html))
refs |= {m + ".mp4" for m in []}
for slug in re.findall(r"slug:'([^']+)'", js):
    refs.add(f"static/videos/web/tasks/{slug}.mp4")
    refs.add(f"static/videos/web/tasks/{slug}_poster.jpg?v=x")
for ref in sorted(refs):
    path = ROOT / ref.split("?", 1)[0]
    if not path.is_file():
        failures.append(f"missing on disk: {ref}")

# --- bolded terms survived the abstract rewrite ----------------------------
abstract = re.search(r'id="abstract".*?</section>', html, re.S).group(0)
for term in ["<strong>continual vision-to-touch learning</strong>",
             "without tactile\n        midtraining</strong>",
             "<strong>DexTacWAM</strong>",
             "<strong>70.6</strong>", "<strong>38.0</strong>",
             "<strong>74.7 to 26.6</strong>", "<strong>89.4%</strong>",
             "<strong>2.26× faster training</strong>",
             "0.5&nbsp;dB of matched",
             "finger- and pose-aware tactile compressor</strong>"]:
    if term not in abstract:
        failures.append(f"abstract lost expected markup: {term!r}")
for banned in ["tactile adapter", "DexVTAM", "\\dextacwam", "\\methodname", "$"]:
    if banned in abstract:
        failures.append(f"abstract contains banned token: {banned!r}")

# --- HTTP ------------------------------------------------------------------
server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
                          cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    time.sleep(1.5)
    urls = ["/", "/index.html", "/static/css/style.css?v=20260916-7",
            "/static/js/main.js?v=20260916-9"]
    urls += ["/" + r for r in sorted(refs) if not r.endswith(".mp4")]
    urls += ["/static/videos/web/tasks/tongs.mp4", "/static/videos/web/wm_prediction_4col.mp4"]
    for url in urls:
        conn = http.client.HTTPConnection("127.0.0.1", PORT, timeout=30)
        conn.request("GET", url.replace("?v=x", "?v=20260916-2"))
        resp = conn.getresponse()
        body = resp.read()
        status = resp.status
        conn.close()
        print(f"  {status} {len(body):>9} B  {url}")
        if status != 200 or not body:
            failures.append(f"HTTP {status} for {url}")
finally:
    server.terminate()
    server.wait()

print()
if failures:
    print("FAILURES:")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print(f"OK: {len(refs)} local refs resolve, {len(checker.ids)} ids, "
      f"{len(set(checker.anchors))} internal anchors, HTML balanced.")
