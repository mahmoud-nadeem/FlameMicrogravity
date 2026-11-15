#!/usr/bin/env python3
"""Turn a team member's photo into a pixel-art character for the dashboard.

    python tools/pixelate.py photo.jpg --id nadeem [--size 32] [--colors 16] [--crop x,y,w,h]

Use only a photo of a team member who agreed to it (all members are over 18). This is a fixed image
filter (crop, shrink, reduce colours), not an AI image generator, so no AI watermark is involved;
the photo itself is never copied into the site, only the small pixel image.

Writes assets/characters/<id>.png and prints the line to put in content/characters.json. The 'mouth'
box (in pixel units) is darkened while the character talks; adjust it after looking at the result.
Needs Pillow:  pip install pillow
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("photo", type=Path)
    ap.add_argument("--id", required=True, help="character id in content/characters.json (e.g. nadeem)")
    ap.add_argument("--size", type=int, default=32, help="sprite width and height in pixels")
    ap.add_argument("--colors", type=int, default=16, help="number of colours (retro look: 8-24)")
    ap.add_argument("--crop", help="x,y,w,h box around the face in the photo (default: centre square)")
    args = ap.parse_args()

    img = ImageOps.exif_transpose(Image.open(args.photo)).convert("RGB")
    if args.crop:
        x, y, w, h = (int(v) for v in args.crop.split(","))
        img = img.crop((x, y, x + w, y + h))
    else:
        side = min(img.size)
        left, top = (img.width - side) // 2, max(0, (img.height - side) // 3)
        img = img.crop((left, top, left + side, top + side))
    small = img.resize((args.size, args.size), Image.Resampling.BOX)
    small = ImageOps.autocontrast(small, cutoff=1)
    pal = small.quantize(colors=args.colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGBA")

    out = HERE / "assets" / "characters" / f"{args.id}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    pal.save(out)
    s = args.size
    mouth = {"x": round(s * 0.40), "y": round(s * 0.72), "w": round(s * 0.20), "h": max(1, round(s * 0.06))}
    print(f"wrote {out.relative_to(HERE)} ({s}x{s}, {args.colors} colours)")
    print("In content/characters.json, for this character set:")
    print(json.dumps({"sprite": f"assets/characters/{args.id}.png", "mouth": mouth}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
