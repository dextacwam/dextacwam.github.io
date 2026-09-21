"""Tile one representative frame from every web clip into a single sheet.

Gives a quick visual check that every clip is the task its filename claims
and that tone mapping did not wreck the colors.
"""
import os
import subprocess
import glob

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

FF = imageio_ffmpeg.get_ffmpeg_exe()
WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.join(WEB, "static/videos/web")
OUT = os.path.join(WEB, "tools/contact_sheet.png")

TW, TH = 384, 216      # thumbnail size
BAR = 26               # label bar height
COLS = 4
PAD = 6


def font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/gnu-free/FreeSansBold.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def grab(path):
    """Pull a frame from ~40% into the clip, where the action usually is."""
    tmp = "/tmp/_cs_frame.png"
    dur = subprocess.run(
        [FF, "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    secs = 4.0
    for line in dur.split("\n"):
        if "Duration:" in line:
            h, m, s = line.split("Duration:")[1].split(",")[0].strip().split(":")
            secs = (int(h) * 3600 + int(m) * 60 + float(s)) * 0.4
            break
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", "%.2f" % secs, "-i", path, "-frames:v", "1", tmp],
                   capture_output=True)
    return Image.open(tmp).convert("RGB") if os.path.exists(tmp) else None


def main():
    clips = sorted(glob.glob(os.path.join(ROOT, "**/*.mp4"), recursive=True))
    rows = (len(clips) + COLS - 1) // COLS
    W = COLS * (TW + PAD) + PAD
    H = rows * (TH + BAR + PAD) + PAD
    sheet = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    f = font(15)

    for i, c in enumerate(clips):
        r, col = divmod(i, COLS)
        x = PAD + col * (TW + PAD)
        y = PAD + r * (TH + BAR + PAD)
        im = grab(c)
        if im is not None:
            im = im.resize((TW, TH), Image.LANCZOS)
            sheet.paste(im, (x, y))
        label = os.path.relpath(c, ROOT).replace(".mp4", "")
        mb = os.path.getsize(c) / 1e6
        d.rectangle([x, y + TH, x + TW, y + TH + BAR], fill=(38, 38, 44))
        d.text((x + 6, y + TH + 5), "%s  (%.1fMB)" % (label, mb),
               fill=(235, 235, 240), font=f)
        print("tiled", label)

    sheet.save(OUT)
    print("\nwrote", OUT, sheet.size)


if __name__ == "__main__":
    main()
