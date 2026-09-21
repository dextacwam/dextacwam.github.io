#!/usr/bin/env python3
"""Stamp a cache-busting query string onto image and poster references.

GitHub Pages serves images with a long-lived cache policy, so re-rendered
figures keep their old URLs and browsers keep the stale bytes. Bumping VERSION
after replacing any image forces a refetch. Images and posters only; the video
files themselves are left untouched.
"""
import re
import sys
from pathlib import Path

VERSION = "20260916-2"
ROOT = Path(__file__).resolve().parent.parent
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")


def stamp_html(text):
    pattern = re.compile(r'((?:src|href|content)=")(static/[^"?]+)(")')

    def repl(match):
        prefix, path, suffix = match.groups()
        if not path.lower().endswith(IMAGE_SUFFIXES):
            return match.group(0)
        return f"{prefix}{path}?v={VERSION}{suffix}"

    text, n_img = pattern.subn(repl, text)

    poster = re.compile(r'(poster=")(static/[^"?]+)(")')
    text, n_poster = poster.subn(lambda m: f"{m.group(1)}{m.group(2)}?v={VERSION}{m.group(3)}", text)

    # The JS bundle now embeds the version, so its own URL must change too.
    text, n_js = re.subn(r'(static/js/main\.js\?v=)[0-9-]+', r"\g<1>" + VERSION, text)
    return text, n_img, n_poster, n_js


def stamp_js(text):
    # main.js rebuilds the hero poster path per rollout; keep it byte-identical
    # to the markup so the two references share one cache entry.
    text, n = re.subn(
        r"(`static/videos/web/tasks/\$\{rollout\.slug\}_poster\.jpg)`",
        r"\1?v=" + VERSION + "`",
        text,
    )
    return text, n


def main():
    html_path = ROOT / "index.html"
    js_path = ROOT / "static/js/main.js"

    html, n_img, n_poster, n_js = stamp_html(html_path.read_text())
    js, n_js_poster = stamp_js(js_path.read_text())

    html_path.write_text(html)
    js_path.write_text(js)
    print(f"index.html: {n_img} image refs, {n_poster} posters, {n_js} script-tag version bumps")
    print(f"main.js: {n_js_poster} runtime poster path(s)")
    if not (n_img and n_poster and n_js and n_js_poster):
        sys.exit("expected every category to match at least once")


if __name__ == "__main__":
    main()
