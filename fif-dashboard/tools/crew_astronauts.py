#!/usr/bin/env python3
"""Build the crew astronaut sprites from the team's own pixel illustrations.

    python tools/crew_astronauts.py --src "../crew-illustrations"      # writes assets/crew/<id>.png (+ a preview)

Faces are never shown. From each person's own illustration only proportions are measured (full height, head size, shoulder
width); no pixel of the illustration is copied into the sprite. Each astronaut is a pixel-art EVA suit in that crew member's
suit colour (content/characters.json is the one authoritative colour table), with a fully enclosed helmet whose opaque, dark
reflective visor hides the face, trim in the member's accent colour, gloves, boots, a backpack, a chest panel and a name
patch with initials. A very dark suit (Mahmoud Nadeem's black suit) gets a lighter outline and bright trim so it reads on
the dark site.

Identity comes from FILES below (file name -> crew id, matching content/characters.json), never from appearance.
Output per crew member: a sprite sheet of 4 frames (idle, breath, talk, point), FRAME_W x FRAME_H each, transparent.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent.parent
# file name -> crew id (content/characters.json). "Shiref" in the file name is the same person as "Shreif" in the site data.
FILES = {"morgan": "Amr Morgan.jpeg", "adwi": "Khaled Adawi.jpeg", "nadeem": "Mahmoud Nadeem.jpeg",
         "gamal": "Mohammed Gamal.jpeg", "shreif": "Mohammed Shiref.jpeg", "tamer": "Mohammed Tamer.jpeg"}
# head box in the original image (x0, y0, x1, y1): hair top to just below the chin, measured once from each illustration
HEADS = {"morgan": (295, 18, 482, 262), "adwi": (434, 251, 582, 428), "nadeem": (300, 12, 528, 272),
         "gamal": (422, 254, 587, 452), "shreif": (308, 8, 485, 228), "tamer": (408, 263, 612, 492)}
FRAME_W, FRAME_H = 176, 300          # one frame; the figure stands on the bottom edge (ground line FRAME_H - 4)
FIGURE_H = 270                       # every person's full height (hair to soles) maps to this many pixels


def remove_white(im: Image.Image, tol: int = 34) -> Image.Image:
    """Transparent background: flood-fill near-white pixels connected to the crop border (interior whites stay)."""
    a = np.asarray(im.convert("RGB")).astype(int)
    h, w, _ = a.shape
    white = (a.min(axis=2) > 255 - tol) & (np.ptp(a, axis=2) < 26)
    keep = np.ones((h, w), bool)
    stack = [(y, x) for y in range(h) for x in (0, w - 1)] + [(y, x) for x in range(w) for y in (0, h - 1)]
    seen = np.zeros((h, w), bool)
    while stack:
        y, x = stack.pop()
        if seen[y, x] or not white[y, x]: continue
        seen[y, x] = True; keep[y, x] = False
        if y > 0: stack.append((y - 1, x))
        if y < h - 1: stack.append((y + 1, x))
        if x > 0: stack.append((y, x - 1))
        if x < w - 1: stack.append((y, x + 1))
    rgba = np.dstack([a, keep.astype(int) * 255]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def preview_heads(src: Path, out: Path):
    tiles = []
    for cid, f in FILES.items():
        im = Image.open(src / f).convert("RGB").crop(HEADS[cid])
        tiles.append(remove_white(im).resize((im.width // 2, im.height // 2), Image.NEAREST))
    W = sum(t.width for t in tiles) + 20 * (len(tiles) + 1); H = max(t.height for t in tiles) + 40
    sheet = Image.new("RGBA", (W, H), (10, 15, 34, 255)); x = 20
    for t in tiles: sheet.alpha_composite(t, (x, 20)); x += t.width + 20
    sheet.save(out)



# ----------------------------------------------------------------------------------------------- suit and helmet
# shoulder width / full height, measured on each illustration (Mahmoud's raised arm excluded)
BUILD = {"morgan": 0.227, "adwi": 0.288, "nadeem": 0.25, "gamal": 0.295, "shreif": 0.238, "tamer": 0.302}
CHIN_KEEP = {"tamer": 0.70, "nadeem": 0.62}      # width of the chin/beard band kept at the bottom of the head crop
INITIALS = {"morgan": "AM", "adwi": "KA", "nadeem": "MN", "gamal": "MG", "shreif": "MS", "tamer": "MT"}
FONT = {  # 3x5 pixel letters for the name patch
    "A": ["010", "101", "111", "101", "101"], "M": ["101", "111", "111", "101", "101"], "K": ["101", "110", "100", "110", "101"],
    "N": ["101", "111", "111", "111", "101"], "G": ["011", "100", "101", "101", "011"], "S": ["011", "100", "010", "001", "110"],
    "T": ["111", "010", "010", "010", "010"]}
K0 = (10, 15, 34, 255)                     # outline (the site's ink)
METAL, DARK = (120, 128, 148, 255), (52, 58, 78, 255)
VISOR_TOP, VISOR_LOW = (58, 74, 118, 255), (9, 12, 26, 255)   # opaque reflective visor: lit at the top, near black below


def hexrgba(h, a=255):
    h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def palette(suit_hex: str) -> dict:
    """Suit colour -> fill, shade, light, outline. A very dark suit gets a light outline so its silhouette shows."""
    r, g, b, _ = hexrgba(suit_hex)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    mix = lambda t, c: tuple(int(v + (c - v) * t) for v in (r, g, b)) + (255,)
    if lum < 60:
        return {"S": (r, g, b, 255), "H": mix(0.45, 0), "L": mix(0.22, 255), "K": (112, 120, 146, 255)}
    return {"S": (r, g, b, 255), "H": mix(0.28, 0), "L": mix(0.35, 255), "K": K0}


def defringe(im: Image.Image, passes: int = 2) -> Image.Image:
    """Drop light, semi-white edge pixels left by JPEG compression next to the removed background."""
    a = np.asarray(im).copy()
    for _ in range(passes):
        alpha = a[..., 3] > 0
        edge = alpha & ~(np.roll(alpha, 1, 0) & np.roll(alpha, -1, 0) & np.roll(alpha, 1, 1) & np.roll(alpha, -1, 1))
        light = a[..., :3].min(axis=2) > 185
        a[edge & light, 3] = 0
    return Image.fromarray(a, "RGBA")


def head_size(cid: str, scale: float) -> tuple[int, int]:
    """The person's head size at sprite scale, from the measured head box: the closed helmet is built around it."""
    x0, y0, x1, y1 = HEADS[cid]
    return max(30, round((x1 - x0) * scale)), max(34, round((y1 - y0) * scale))


def text_patch(d: ImageDraw.ImageDraw, x: int, y: int, s: str, col):
    for i, ch in enumerate(s):
        for r, row in enumerate(FONT[ch]):
            for c, bit in enumerate(row):
                if bit == "1": d.point((x + i * 4 + c, y + r), fill=col)


def frame(cid: str, head: tuple, pal: dict, accent, pose: str) -> tuple[Image.Image, tuple]:
    """One pose. Returns the frame and the bust box (x, y, size) used for small portraits."""
    img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    ground = FRAME_H - 4; top = ground - FIGURE_H
    cx = FRAME_W // 2
    dy = 1 if pose == "breath" else 0                 # breathing: shoulders and head settle by one pixel
    nod = 1 if pose == "talk" else 0                  # talking: a small nod
    SUIT, SHADE, LIGHT, K = pal["S"], pal["H"], pal["L"], pal["K"]
    hw, hh = head
    head_y = top + dy + nod
    chin = head_y + hh
    sw = max(56, int(BUILD[cid] * FIGURE_H) + 14)    # shoulder width of the (puffy) suit, from the person's own build
    ww = int(sw * 0.84)                               # waist
    collar_y = chin - 5
    sh_y = collar_y + 7
    hip_y = top + int(FIGURE_H * 0.55)
    crotch = hip_y + 10
    boot_h = 15
    leg_w = ww // 2 - 2
    rx, ry = hw // 2 + 8, hh // 2 + 9
    hcx, hcy = cx, head_y + hh // 2 + 1

    # backpack (behind)
    bp_w, bp_h = sw - 6, int((hip_y - sh_y) * 0.8)
    d.rounded_rectangle([cx - bp_w // 2, sh_y - 7, cx + bp_w // 2, sh_y - 7 + bp_h], radius=4, fill=DARK, outline=K)
    d.rectangle([cx - bp_w // 2 + 4, sh_y - 4, cx + bp_w // 2 - 4, sh_y], fill=METAL)
    # legs: a gap between them, knee pads, boots
    for side in (-1, 1):
        lx0 = cx + 2 if side > 0 else cx - 2 - leg_w
        lx1 = lx0 + leg_w
        d.rounded_rectangle([lx0, hip_y - 2, lx1, ground - boot_h + 2], radius=3, fill=SUIT, outline=K)
        d.line([lx0 + 2, crotch, lx0 + 2, ground - boot_h - 2], fill=LIGHT if side < 0 else SHADE)
        knee = (crotch + ground - boot_h) // 2
        d.rounded_rectangle([lx0 + 1, knee - 4, lx1 - 1, knee + 4], radius=2, fill=SHADE, outline=K)
        d.line([lx0 + 1, ground - boot_h - 6, lx1 - 1, ground - boot_h - 6], fill=accent)
        bx0, bx1 = (lx0 - 1, lx1 + 3) if side > 0 else (lx0 - 3, lx1 + 1)
        d.rounded_rectangle([bx0, ground - boot_h, bx1, ground], radius=3, fill=DARK, outline=K)
        d.line([bx0 + 2, ground - 3, bx1 - 2, ground - 3], fill=METAL)
    # torso: wide shoulders tapering to the waist
    t = sh_y - 2 + dy
    d.polygon([(cx - sw // 2, t + 6), (cx - sw // 2 + 6, t), (cx + sw // 2 - 6, t), (cx + sw // 2, t + 6),
               (cx + ww // 2, hip_y + 2), (cx - ww // 2, hip_y + 2)], fill=SUIT, outline=K)
    d.line([cx - sw // 2 + 3, t + 8, cx - ww // 2 + 2, hip_y - 2], fill=LIGHT)
    d.line([cx + sw // 2 - 3, t + 8, cx + ww // 2 - 2, hip_y - 2], fill=SHADE)
    d.rectangle([cx - sw // 2 + 4, t + 24, cx + sw // 2 - 4, t + 27], fill=accent)                 # chest stripe, crew colour
    d.rectangle([cx - ww // 2 + 1, hip_y - 5, cx + ww // 2 - 1, hip_y - 1], fill=METAL, outline=K)   # waist ring
    # chest control panel and name patch
    py = t + 10
    d.rectangle([cx - 8, py, cx + 8, py + 12], fill=DARK, outline=K)
    led = (255, 200, 60, 255) if pose == "talk" else (70, 90, 120, 255)
    for i, col in enumerate([accent, led, (61, 200, 140, 255)]):
        d.rectangle([cx - 5 + i * 4, py + 3, cx - 4 + i * 4, py + 4], fill=col)
    d.rectangle([cx - 5, py + 7, cx + 5, py + 9], fill=METAL)
    nx = cx - sw // 2 + 7
    d.rectangle([nx, py, nx + 10, py + 8], fill=accent, outline=K)
    for i, ch in enumerate(INITIALS[cid]):
        for r, row in enumerate(FONT[ch]):
            for c, bit in enumerate(row):
                if bit == "1": d.point((nx + 1 + i * 4 + c, py + 2 + r), fill=(255, 255, 255, 255))
    # arms with shoulder pads, elbow rings and gloves
    arm_w = 13
    def arm_down(side):
        x0 = cx + sw // 2 - 3 if side > 0 else cx - sw // 2 - arm_w + 3
        d.rounded_rectangle([x0, t + 2, x0 + arm_w, hip_y + 6], radius=6, fill=SUIT, outline=K)
        elbow = (t + hip_y) // 2 + 4
        d.rectangle([x0 + 1, elbow, x0 + arm_w - 1, elbow + 3], fill=SHADE)
        d.rectangle([x0 + 1, hip_y - 2, x0 + arm_w - 1, hip_y + 1], fill=accent)                 # cuff
        d.rounded_rectangle([x0 - 1, hip_y + 2, x0 + arm_w + 1, hip_y + 14], radius=5, fill=LIGHT, outline=K)   # glove
        d.ellipse([x0 - 2, t, x0 + arm_w + 2, t + 12], fill=SUIT, outline=K)                     # shoulder pad
    def arm_point(side):
        x0 = cx + sw // 2 - 4
        y0 = t + 3
        reach = 34
        d.rounded_rectangle([x0, y0, x0 + reach, y0 + arm_w - 1], radius=6, fill=SUIT, outline=K)
        d.rectangle([x0 + reach - 7, y0 + 1, x0 + reach - 4, y0 + arm_w - 2], fill=accent)
        g = x0 + reach - 3
        d.rounded_rectangle([g, y0 - 1, g + 11, y0 + arm_w], radius=5, fill=LIGHT, outline=K)
        d.rounded_rectangle([g + 10, y0 + 3, g + 16, y0 + 7], radius=2, fill=LIGHT, outline=K)    # pointing finger
        d.ellipse([x0 - 4, t, x0 + arm_w, t + 12], fill=SUIT, outline=K)
    arm_down(-1)
    (arm_point if pose == "point" else arm_down)(1)
    # collar ring, then the closed helmet: a shell in the suit colour and an opaque reflective visor (no face)
    d.rounded_rectangle([cx - hw // 2 - 6, collar_y - 1 + dy, cx + hw // 2 + 6, collar_y + 7 + dy], radius=3, fill=METAL, outline=K)
    bbox = [hcx - rx, hcy - ry, hcx + rx, hcy + ry]
    d.ellipse(bbox, fill=SUIT, outline=K, width=1)
    d.arc([bbox[0] + 2, bbox[1] + 2, bbox[2] - 2, bbox[3] - 2], 150, 260, fill=LIGHT, width=2)        # shell highlight
    d.arc([bbox[0] + 2, bbox[1] + 2, bbox[2] - 2, bbox[3] - 2], 330, 60, fill=SHADE, width=2)         # shell shade
    vx0, vx1 = hcx - int(rx * 0.74), hcx + int(rx * 0.74)
    vy0, vy1 = hcy - int(ry * 0.50), hcy + int(ry * 0.50)
    rad = (vy1 - vy0) // 2 - 1
    mask = Image.new("L", (FRAME_W, FRAME_H), 0); ImageDraw.Draw(mask).rounded_rectangle([vx0, vy0, vx1, vy1], radius=rad, fill=255)
    grad = Image.new("RGBA", (FRAME_W, FRAME_H)); gd = ImageDraw.Draw(grad)
    for y in range(vy0, vy1 + 1):                                   # banded, not smooth: it stays pixel art
        t = round(min(1.0, max(0.0, (y - vy0) / max(1, vy1 - vy0))) * 5) / 5
        gd.line([vx0, y, vx1, y], fill=tuple(int(VISOR_TOP[i] + (VISOR_LOW[i] - VISOR_TOP[i]) * t) for i in range(3)) + (255,))
    img.paste(grad, (0, 0), mask)
    d.rounded_rectangle([vx0 - 1, vy0 - 1, vx1 + 1, vy1 + 1], radius=rad + 1, outline=K, width=1)
    d.rounded_rectangle([vx0 - 2, vy0 - 2, vx1 + 2, vy1 + 2], radius=rad + 2, outline=accent, width=1)   # visor frame in the crew trim
    # reflections: a curved band of sky and a bright glint (they cover the face, they do not suggest one)
    d.arc([vx0 + 3, vy0 + 2, vx1 - 3, vy1 + (vy1 - vy0)], 200, 250, fill=(150, 178, 228, 255), width=2)
    d.rectangle([vx0 + 5, vy0 + 4, vx0 + 7, vy0 + 6], fill=(238, 246, 255, 255))
    d.point((vx0 + 9, vy0 + 4), fill=(238, 246, 255, 255))
    d.line([vx1 - 9, vy1 - 4, vx1 - 4, vy1 - 6], fill=accent)
    # side lamp and comm light (lit while talking)
    d.rectangle([bbox[0] + 1, hcy - 3, bbox[0] + 4, hcy + 3], fill=DARK, outline=K)
    d.rectangle([bbox[2] - 4, hcy - 3, bbox[2] - 1, hcy + 3], fill=(255, 200, 60, 255) if pose == "talk" else DARK, outline=K)
    d.rounded_rectangle([cx - hw // 2 - 6, collar_y + 3 + dy, cx + hw // 2 + 6, collar_y + 8 + dy], radius=3, fill=METAL, outline=K)
    ant_x = hcx + rx - 7
    d.line([ant_x, hcy - ry + 5, ant_x + 3, hcy - ry - 4], fill=K)
    d.rectangle([ant_x + 2, hcy - ry - 7, ant_x + 4, hcy - ry - 5], fill=(255, 200, 60, 255) if pose == "talk" else METAL, outline=K)
    side = max(2 * rx + 30, 84)                       # bust: helmet and shoulders, square, for small portraits
    bust = (max(0, hcx - side // 2), max(0, hcy - ry - 9 - nod - dy), side)
    return img, bust


POSES = ["idle", "breath", "talk", "point"]


def build(src: Path, out: Path, chars: dict):
    out.mkdir(parents=True, exist_ok=True)
    meta = {}
    sheets = []
    for cid, f in FILES.items():
        full = Image.open(src / f).convert("RGB")
        a = np.asarray(full).min(axis=2) < 225
        rows = np.where(a.sum(1) > 3)[0]
        scale = FIGURE_H / (rows[-1] - rows[0])
        head = head_size(cid, scale)
        c = chars[cid]
        made = [frame(cid, head, palette(c["suit"]), hexrgba(c["accent"]), p) for p in POSES]
        frames = [m[0] for m in made]; bust = made[0][1]
        sheet = Image.new("RGBA", (FRAME_W * len(frames), FRAME_H), (0, 0, 0, 0))
        for i, fr in enumerate(frames): sheet.alpha_composite(fr, (i * FRAME_W, 0))
        sheet = sheet.quantize(colors=96, method=Image.FASTOCTREE, dither=Image.NONE).convert("RGBA")
        sa = np.asarray(sheet).copy(); sa[..., 3] = np.where(sa[..., 3] > 127, 255, 0); sheet = Image.fromarray(sa, "RGBA")
        sheet.save(out / f"{cid}.png", optimize=True)
        meta[cid] = {"sheet": f"assets/crew/{cid}.png", "frame": [FRAME_W, FRAME_H], "frames": POSES, "source": f"crew-illustrations/{f}",
                     "head_box": HEADS[cid], "scale": round(scale, 4),
                     "bust": list(bust)}
        sheets.append(sheet)
    (out / "crew-sprites.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return sheets


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument("--preview-heads", type=Path)
    ap.add_argument("--out", type=Path, default=HERE / "assets" / "crew")
    ap.add_argument("--preview", type=Path, help="also write a contact sheet on the site's dark background")
    a = ap.parse_args()
    if a.preview_heads: preview_heads(a.src, a.preview_heads); raise SystemExit
    chars = {c["id"]: c for c in json.loads((HERE / "content" / "characters.json").read_text(encoding="utf-8"))["characters"]}
    sheets = build(a.src, a.out, chars)
    if a.preview:
        bg = Image.new("RGBA", (sheets[0].width, FRAME_H * len(sheets)), (5, 8, 20, 255))
        for i, sh in enumerate(sheets): bg.alpha_composite(sh, (0, i * FRAME_H))
        bg.resize((bg.width * 2, bg.height * 2), Image.NEAREST).save(a.preview)
    # record each sheet in content/characters.json (the site reads sprites from there); other fields stay as they are
    cpath = HERE / "content" / "characters.json"
    doc = json.loads(cpath.read_text(encoding="utf-8")); meta = json.loads((a.out / "crew-sprites.json").read_text(encoding="utf-8"))
    for c in doc["characters"]:
        if c["id"] in meta:
            m = meta[c["id"]]
            c["sprite"] = m["sheet"]
            c["sheet"] = {"frame": m["frame"], "bust": m["bust"], "frames": m["frames"], "source": m["source"]}
    cpath.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + chr(10), encoding="utf-8", newline=chr(10))
    print("wrote", ", ".join(f"{c}.png" for c in FILES), "and updated content/characters.json")
