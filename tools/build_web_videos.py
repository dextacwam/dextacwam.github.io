"""Transcode website demo sources into web-ready mp4.

The site currently ships only the Aug 28 deck clips: one per task, plus the
long-horizon prediction. Set INCLUDE_MOV to also transcode the iPhone .MOV
originals sitting untracked in static/videos/demos/ (baseline comparisons,
Bowl generalization, Tongs failure modes). Those are 1080p30 HLG HDR 10-bit
HEVC and need tone mapping or they render washed out.

Everything is written to static/videos/web/ so the raw sources can stay
untracked.
"""
import os
import re
import subprocess
import zipfile

# The .MOV-derived clips are not published right now.
INCLUDE_MOV = False

import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
WEB = "/projects/bekg/haorany7/dex_vtam/DexVTAM_web"
SRC = os.path.join(WEB, "static/videos")
OUT = os.path.join(SRC, "web")
DECK = "/projects/bekg/haorany7/dex_vtam/DexTacWAM Aug 28th.pptx"

# Confirmed by matching each picture's offset to its caption's offset on the
# slide; the left/right pairs are easy to swap by eye, so do not trust the
# filename order.
DECK_CLIPS = {
    "image39.gif": "tasks/cube_place.mp4",
    "image40.gif": "tasks/cube_handover.mp4",
    "image41.gif": "tasks/wipe_whiteboard.mp4",
    "image42.gif": "tasks/tongs.mp4",
    "image43.gif": "tasks/bowl_destack.mp4",
    "image44.gif": "tasks/bottle_cap.mp4",
    "image45.gif": "wm_prediction_4col.mp4",
}

MOV_CLIPS = {
    "demos/DexTacWAM/Tong.MOV": "dextacwam/tongs.mp4",
    "demos/DexTacWAM/Cap.MOV": "dextacwam/bottle_cap.mp4",
    "demos/DexTacWAM/Bowl_Blue.MOV": "dextacwam/bowl_blue.mp4",
    "demos/DexTacWAM/Bowl_Orange.MOV": "dextacwam/bowl_orange.mp4",
    "demos/DexTacWAM/Bowl_Gen_Green.MOV": "generalization/bowl_unseen_green.mp4",
    "demos/DexTacWAM/Bowl_Gen_Purple.MOV": "generalization/bowl_unseen_purple.mp4",
    "demos/DexTacWAM/Bowl_Gen_Yellow.MOV": "generalization/bowl_unseen_yellow.mp4",
    "demos/DexTacWAM/Bowl_Gen_Height_Two.MOV": "generalization/bowl_height_two.mp4",
    "demos/DexTacWAM/Bowl_Gen_Height_Four.MOV": "generalization/bowl_height_four.mp4",
    "demos/DexTacWAM/Tong_failure_slipperry.MOV": "failures/tongs_slip.mp4",
    "demos/DexTacWAM/Tong_failure_stuck.MOV": "failures/tongs_stuck.mp4",
    "demos/PI0.5/Tong_falure.MOV": "baselines/pi05_tongs_failure.mp4",
    "demos/PI0.5/Bowl_success.MOV": "baselines/pi05_bowl_success.mp4",
    "demos/PI0.5/Bowl_failure.MOV": "baselines/pi05_bowl_failure.mp4",
    "demos/PI0.5/Cap_success.MOV": "baselines/pi05_cap_success.mp4",
    "demos/PI0.5/Cap_failure.MOV": "baselines/pi05_cap_failure.mp4",
    "demos/RDP/Tong_success.MOV": "baselines/rdp_tongs_success.mp4",
    "demos/RDP/Tong_failure.MOV": "baselines/rdp_tongs_failure.mp4",
    "demos/RDP/Bowl_Success.MOV": "baselines/rdp_bowl_success.mp4",
    "demos/RDP/Bowl_failure.MOV": "baselines/rdp_bowl_failure.mp4",
    "demos/RDP/Cap_success.MOV": "baselines/rdp_cap_success.mp4",
    "demos/RDP/Cap_failure.MOV": "baselines/rdp_cap_failure.mp4",
}

TONEMAP = (
    "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
    "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,"
)


def is_hdr(path):
    p = subprocess.run([FF, "-hide_banner", "-i", path],
                       capture_output=True, text=True)
    return bool(re.search(r"arib-std-b67|smpte2084", p.stderr))


def encode(src, dst, vf, crf):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    cmd = [FF, "-y", "-hide_banner", "-loglevel", "error", "-i", src,
           "-map", "0:v:0", "-an", "-sn", "-dn",
           "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
           "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
           # Keyframes every ~2s so scrubbing stays responsive.
           "-g", "48", "-movflags", "+faststart", dst]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("  FAILED:", r.stderr.strip()[:300])
        return False
    return True


def poster(src_mp4):
    """First-frame JPEG, shown before load and where autoplay is blocked."""
    dst = src_mp4.rsplit(".", 1)[0] + "_poster.jpg"
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error",
                    "-i", src_mp4, "-frames:v", "1", "-q:v", "4", dst],
                   capture_output=True)
    return dst


def main():
    os.makedirs(OUT, exist_ok=True)
    total_in = total_out = 0

    # Deck GIFs are 256-colour and dithered. A mild denoise strips the dither
    # pattern, which both cleans up the image and stops x264 from spending
    # bits coding noise; a low CRF then keeps us close to the source. Native
    # resolution is kept because upscaling a 640x360 GIF adds nothing.
    z = zipfile.ZipFile(DECK)
    tmp = os.path.join(OUT, "_tmp.gif")
    vf = "hqdn3d=2:2:3:3,scale=trunc(iw/2)*2:trunc(ih/2)*2"
    for name, rel in DECK_CLIPS.items():
        dst = os.path.join(OUT, rel)
        with open(tmp, "wb") as f:
            f.write(z.read("ppt/media/" + name))
        size_in = os.path.getsize(tmp)
        print("[deck] %s -> %s" % (name, rel))
        if encode(tmp, dst, vf, 20):
            poster(dst)
            total_in += size_in
            total_out += os.path.getsize(dst)
    os.remove(tmp)

    for rel_src, rel in (MOV_CLIPS.items() if INCLUDE_MOV else []):
        src = os.path.join(SRC, rel_src)
        if not os.path.exists(src):
            print("[skip] missing", rel_src)
            continue
        dst = os.path.join(OUT, rel)
        vf = "scale=-2:720"
        if is_hdr(src):
            vf = TONEMAP + vf
            tag = "hdr"
        else:
            tag = "sdr"
        print("[%s] %s -> %s" % (tag, rel_src, rel))
        size_in = os.path.getsize(src)
        if encode(src, dst, vf, 27):
            total_in += size_in
            total_out += os.path.getsize(dst)

    print("\nsource %.0f MB -> web %.0f MB (%.1fx smaller)" % (
        total_in / 1e6, total_out / 1e6, total_in / max(total_out, 1)))


if __name__ == "__main__":
    main()
