#!/usr/bin/env python3
"""Draw Bondoq (بندق), the crew's cat, as pixel-art animation frames.

    python tools/bondoq_sprites.py            # writes assets/bondoq/bondoq.png, bowl.png, bed.png, bondoq.json (+ --preview)

Reference: assets/bondoq/originals/bondoq-1.jpeg and bondoq-2.jpeg (a fluffy cream/golden longhair kitten). The palette is sampled
from those images; the face follows them (large round dark eyes with a light catch, pink nose and inner ears, tufted cheeks,
very fluffy outline, plume tail). The poses are original drawings: the references only show him lying down. The sleeping
cushion copies the dark cushion of bondoq-2. Frames face right; the page mirrors them to walk left.

Animations (bondoq.json "anims", used by assets/js/bondoq.js): each is an optional one-time "intro" (a transition such as
sitting down or settling) followed by a "loop". The walk is a 6-frame diagonal gait (far legs darker) with a body bob, a
swaying tail and a nodding head; STRIDE is how far he travels per cycle, so the page can match speed to the legs.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

HERE = Path(__file__).resolve().parent.parent
W, H = 52, 42                     # one frame; ground line at GY
GY = 39
# sampled from the reference images
HI, LIGHT, BASE, MID, SHADE, DARK = "#f8d3ae", "#f1c69c", "#e6b98f", "#d4a57d", "#c3926b", "#906143"
OUT = "#6e4630"
EYE, EYE_CATCH, IRIS = "#23130f", "#fff6e6", "#5b4a2c"
PINK, PINK_D = "#e9a59b", "#c97f74"
TONGUE = "#e8838a"


class Cat:
    def __init__(self, seed):
        self.img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.img)
        self.rng = random.Random(seed)

    def blob(self, cx, cy, rx, ry, fill=BASE, shade=True, tufts=6, up=True):
        d = self.d
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill)
        if shade:
            d.ellipse([cx - rx + 1, cy - ry + 1, cx + rx - 2, cy - ry // 3], fill=LIGHT)
            d.chord([cx - rx, cy, cx + rx, cy + ry], 20, 160, fill=MID)
        for _ in range(tufts):                        # fluffy fur: little tufts sticking out of the outline
            a = self.rng.uniform(math.pi * (1.05 if up else 0), math.pi * (1.95 if up else 2))
            x, y = cx + math.cos(a) * rx, cy + math.sin(a) * ry
            tx, ty = x + math.cos(a) * 2.2, y + math.sin(a) * 2.2
            d.polygon([(x - 1, y), (x + 1, y), (tx, ty)], fill=fill)

    def leg(self, x, top, bottom, w=3, col=MID):
        self.d.rectangle([x, top, x + w - 1, bottom - 1], fill=col)
        self.d.rectangle([x - 0, bottom - 1, x + w, bottom], fill=HI)          # pale paw

    def tail(self, pts, r=3):
        for i, (x, y) in enumerate(pts):
            rr = r if i < len(pts) - 1 else r + 1                         # plume at the tip
            self.d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=SHADE if i < len(pts) // 2 else BASE)
        x, y = pts[-1]; self.d.ellipse([x - 2, y - 2, x + 1, y + 1], fill=LIGHT)

    def head(self, hx, hy, eyes="open", look=0, tilt=0, mouth=None, ear=0):
        d = self.d
        self.blob(hx, hy, 8, 7, tufts=7)
        # cheek ruff
        d.ellipse([hx - 9, hy, hx - 5, hy + 5], fill=LIGHT); d.ellipse([hx + 5, hy, hx + 9, hy + 5], fill=LIGHT)
        # ears with pink insides (tilt moves them)
        for sx in (-1, 1):
            bx = hx + sx * 5 + tilt
            tip = 11 - (3 if ear and sx < 0 else 0)                  # ear twitch: the far ear flicks back
            tx = bx + sx * 1 - (2 if ear and sx < 0 else 0)
            d.polygon([(bx - 3, hy - 4), (bx + 3, hy - 4), (tx, hy - tip)], fill=BASE)
            d.polygon([(bx - 1, hy - 5), (bx + 1, hy - 5), (tx, hy - tip + 2)], fill=PINK)
        # muzzle
        d.ellipse([hx - 3, hy + 1, hx + 3, hy + 5], fill=HI)
        ex = look
        if eyes == "open":
            for sx in (-3, 2):
                d.rectangle([hx + sx + ex, hy - 2, hx + sx + ex + 2, hy + 1], fill=EYE)
                d.point((hx + sx + ex + 1, hy), fill=IRIS)
                d.point((hx + sx + ex, hy - 2), fill=EYE_CATCH)
        elif eyes == "half":
            for sx in (-3, 2): d.rectangle([hx + sx + ex, hy, hx + sx + ex + 2, hy + 1], fill=EYE)
        else:  # closed: gentle curves
            for sx in (-3, 2): d.line([hx + sx, hy, hx + sx + 1, hy + 1, hx + sx + 2, hy], fill=DARK)
        d.rectangle([hx - 1 + ex // 2, hy + 2, hx + ex // 2, hy + 2], fill=PINK_D)            # nose
        if mouth == "lick": d.rectangle([hx, hy + 4, hx + 1, hy + 5], fill=TONGUE)
        elif mouth == "yawn": d.ellipse([hx - 1, hy + 3, hx + 2, hy + 6], fill=TONGUE)
        elif mouth == "eat": d.rectangle([hx - 1, hy + 4, hx + 1, hy + 4], fill=DARK)

    def outline(self):
        """1 px darker edge around the whole cat, like the brown line art of the references."""
        px = self.img.load(); edge = []
        for y in range(H):
            for x in range(W):
                if px[x, y][3] == 0 and any(0 <= x + dx < W and 0 <= y + dy < H and px[x + dx, y + dy][3] > 0
                                            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    edge.append((x, y))
        for p in edge: self.img.putpixel(p, (0x6e, 0x46, 0x30, 255))
        return self.img


STRIDE = 16                       # sprite pixels travelled per walk cycle (6 frames)


def standing(step=-1, look=0, head_dy=0, eat=False, mouth=None, eyes="open", breathe=0, ear=0, tail=0):
    """step 0-5: one frame of the walk cycle; -1: standing still."""
    c = Cat(11)
    walking = step >= 0
    t = step / 6 * 2 * math.pi if walking else 0
    bob = -1 if walking and step % 3 == 1 else 0                         # the body rises as the legs pass under it
    sw = math.sin(t) * 2.5 if walking else tail                         # tail sways with the gait (or flicks while standing)
    c.tail([(10, 24 + bob), (7, 20 + bob), (6 + sw * 0.5, 15 + bob), (8 + sw, 11 + bob + abs(sw) * 0.3)])
    # legs, far side first and darker: back-far, front-far, back-near, front-near; diagonal pairs move together
    legs = [(14, math.pi, SHADE), (30, 0, SHADE), (17, 0, MID), (33, math.pi, MID)]
    for x, ph, col in legs:
        if walking:
            a = t + ph
            dx, lift = round(2.2 * math.sin(a)), max(0, round(2 * math.cos(a)))   # forward swing is lifted, back push on the ground
        else:
            dx, lift = 0, 0
        c.leg(x + dx, 28 + bob, GY - lift, col=col)
    c.blob(23, 26 + bob - breathe, 13, 8 + breathe, tufts=10)
    c.d.ellipse([30, 22 + bob - breathe, 37, 31 + bob], fill=HI)              # pale chest ruff, as in the reference
    nod = (0, 0, 1, 0, 0, 1)[step] if walking else 0
    hx, hy = (38, 24 + head_dy) if eat else (37, 17 + bob + nod + head_dy - breathe)
    c.head(hx, hy, eyes=eyes, look=look, mouth=mouth, ear=ear)
    return c.outline()


def sitting(look=0, groom=0, eyes="open", tailflick=0, breathe=0, ear=0, half=False):
    c = Cat(23)
    if half:                                                              # on the way down: hips lowering, head still high
        c.tail([(12, 30), (8, 30), (5, 27), (5, 23)])
        c.leg(28, 29, GY, col=SHADE); c.leg(31, 29, GY, col=MID)
        c.leg(15, 31, GY, col=MID)
        c.blob(22, 28, 12, 9, tufts=10)
        c.d.ellipse([29, 21, 36, 30], fill=HI)
        c.head(33, 15, eyes=eyes)
        return c.outline()
    c.tail([(14, 36), (9, 37), (5, 35 - tailflick), (4 - tailflick // 2, 31 - tailflick)])
    c.blob(20, 28 - breathe, 10, 11 + breathe, tufts=10)
    c.leg(23, 30, GY, col=MID); c.leg(27, 30, GY, col=SHADE)          # front legs straight
    c.d.ellipse([12, 31, 21, GY], fill=MID)                               # haunch
    if groom == 3:                                                        # paw wiping over the ear
        hx, hy = 25, 15
        c.head(hx, hy, eyes="closed", ear=1)
        c.d.rectangle([hx + 2, hy - 1, hx + 5, hy + 12], fill=MID, outline=SHADE)
        c.d.ellipse([hx + 1, hy - 6, hx + 7, hy - 1], fill=HI, outline=DARK)
    elif groom == 4:                                                      # paw back down, licking lips
        c.head(24, 15, eyes="half", mouth="lick")
    elif groom:
        hx, hy = 26, 16 + (1 if groom == 2 else 0)
        c.head(hx, hy, eyes="closed", mouth="lick" if groom == 2 else None)
        c.d.rectangle([hx, hy + 7, hx + 3, hy + 14], fill=MID, outline=SHADE)   # foreleg raised...
        c.d.ellipse([hx - 2, hy + 3 + (groom == 2), hx + 4, hy + 8 + (groom == 2)], fill=HI, outline=DARK)   # ...paw at the mouth
    else:
        c.head(24, 14 - breathe, eyes=eyes, look=look, ear=ear)
    return c.outline()


def crouch():
    """Between sitting and lying: front legs sliding forward, body lowering."""
    c = Cat(31)
    c.tail([(10, 34), (6, 34), (4, 31), (5, 27)])
    c.blob(24, 30, 14, 8, tufts=11)
    c.d.ellipse([30, 26, 39, 35], fill=HI)
    c.leg(12, 33, GY, col=SHADE); c.leg(16, 33, GY, col=MID)              # drawn facing left like the lying poses
    c.head(17, 22, eyes="half")
    return c.outline()


def loaf(eyes="open", breathe=0, mouth=None, ear=0):
    """Lying like the reference images: front paws tucked, tail along the side."""
    c = Cat(37)
    c.blob(28, 31 - breathe, 17, 8 + breathe, tufts=12)
    c.d.ellipse([33, 26 - breathe, 44, 37], fill=LIGHT)                     # fluffy haunch, as in the reference
    c.d.ellipse([37, 29, 41, 33], fill=HI)
    c.d.ellipse([8, 33, 20, GY], fill=HI)                                   # tucked front paws
    c.head(13, 25 - (1 if mouth == "yawn" else 0), eyes=eyes, mouth=mouth, ear=ear)
    return c.outline()


def sleeping(breathe=0, ear=0, lift=0):
    c = Cat(41)
    c.blob(27, 31 - breathe, 16, 8 + breathe, tufts=12)
    c.tail([(42, 34), (38, 37), (30, 38), (21, 37)], r=3)                  # tail wrapped around the front
    c.head(14, 29 - lift * 3, eyes="half" if lift else "closed", ear=ear)
    c.d.ellipse([8, 34, 17, GY], fill=HI)
    return c.outline()


def stretching(phase=0):
    c = Cat(53)
    c.tail([(10, 20), (7, 15), (8, 10), (11, 7 - phase)])
    for x in (12, 16): c.leg(x, 24, GY, col=MID)                             # rear legs up and straight
    for x in (34, 38): c.leg(x + phase * 2, 33, GY, col=SHADE)              # front legs reaching forward
    c.d.polygon([(10, 26), (14, 18), (30, 26), (38, 33), (22, 36)], fill=BASE)
    c.blob(20, 24, 10, 6, tufts=8)
    c.blob(31, 31, 9, 5, tufts=6)
    c.head(42 + phase, 30, eyes="closed" if phase else "half", mouth="yawn" if phase == 2 else None)
    return c.outline()


# the lying poses are drawn facing left (like the reference photos); mirror them so every frame faces right
right = ImageOps.mirror


# every distinct frame once, by name; animations refer to them by name (frames may repeat inside a sequence)
CELLS = {
    **{f"walk{i}": standing(i) for i in range(6)},
    "stand": standing(), "stand_breathe": standing(breathe=1), "stand_blink": standing(eyes="closed"), "stand_ear": standing(ear=1, tail=-2),
    "look_l": standing(look=-2), "look_r": standing(look=2), "look_r_ear": standing(look=2, ear=1),
    "halfsit": sitting(half=True), "sit": sitting(), "sit_breathe": sitting(breathe=1), "sit_blink": sitting(eyes="closed"),
    "sit_tail": sitting(tailflick=2), "sit_look_l": sitting(look=-2), "sit_look_r": sitting(look=2, ear=1),
    "groom_paw": sitting(groom=1), "groom_lick": sitting(groom=2), "groom_ear": sitting(groom=3), "groom_done": sitting(groom=4),
    "eat_lower": standing(eat=True, head_dy=0, eyes="half"), "eat0": standing(eat=True, head_dy=2, mouth="eat", eyes="half"),
    "eat1": standing(eat=True, head_dy=4, mouth="eat", eyes="closed"),
    "crouch": right(crouch()), "loaf": right(loaf()), "loaf_breathe": right(loaf(breathe=1)), "loaf_half": right(loaf(eyes="half")),
    "loaf_yawn": right(loaf(eyes="closed", mouth="yawn")),
    "curl0": right(sleeping(0)), "curl1": right(sleeping(1)), "curl_ear": right(sleeping(0, ear=1)), "curl_lift": right(sleeping(0, lift=1)),
    "stretch0": stretching(0), "stretch1": stretching(1), "stretch_yawn": stretching(2),
}
ANIMS = {  # name -> (intro played once, loop)
    "walk": ([], [f"walk{i}" for i in range(6)]),
    "stand": ([], ["stand", "stand", "stand_breathe", "stand_breathe", "stand", "stand", "stand_breathe", "stand_blink", "stand_breathe", "stand", "stand_ear", "stand"]),
    "look": ([], ["stand", "look_l", "look_l", "stand", "look_r", "look_r_ear", "look_r", "stand"]),
    "sit": (["halfsit"], ["sit", "sit_breathe", "sit", "sit_breathe", "sit_look_l", "sit_look_l", "sit", "sit_blink", "sit_breathe", "sit_tail", "sit", "sit_look_r", "sit_look_r", "sit_breathe"]),
    "groom": ([], ["groom_paw", "groom_lick", "groom_paw", "groom_lick", "groom_paw", "groom_lick", "groom_ear", "groom_ear", "groom_done", "sit"]),
    "eat": (["stand", "eat_lower"], ["eat0", "eat1", "eat0", "eat1", "eat0", "eat_lower"]),
    "settle": (["halfsit", "sit", "crouch"], ["loaf", "loaf_breathe"]),
    "loaf": ([], ["loaf", "loaf", "loaf_breathe", "loaf_breathe"]),
    "sleep": ([], ["curl0", "curl0", "curl1", "curl1", "curl0", "curl0", "curl1", "curl1", "curl_ear", "curl0", "curl1", "curl1"]),
    "wake": (["curl_lift", "loaf_half", "loaf_yawn", "loaf_half"], ["loaf"]),
    "stretch": (["crouch", "stretch0", "stretch1", "stretch_yawn", "stretch1", "stretch0"], ["stand"]),
}


def props():
    bowl = Image.new("RGBA", (20, 10), (0, 0, 0, 0)); d = ImageDraw.Draw(bowl)
    d.polygon([(1, 3), (18, 3), (15, 9), (4, 9)], fill="#7d869c", outline="#0a0f22")
    d.line([(2, 4), (17, 4)], fill="#c3c9db")
    d.ellipse([3, 0, 16, 5], fill="#a0703f"); d.point([(6, 1), (9, 2), (12, 1), (14, 2)], fill="#c98a4a")   # kibble
    bed = Image.new("RGBA", (60, 12), (0, 0, 0, 0)); d = ImageDraw.Draw(bed)
    d.rounded_rectangle([0, 2, 59, 11], radius=5, fill="#26283a", outline="#0a0f22")                        # dark cushion (bondoq-2)
    d.rounded_rectangle([3, 3, 56, 6], radius=3, fill="#34374d")
    return bowl, bed


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument("--preview", type=Path); a = ap.parse_args()
    out = HERE / "assets" / "bondoq"; out.mkdir(parents=True, exist_ok=True)
    names = list(CELLS); index = {n: i for i, n in enumerate(names)}
    img = Image.new("RGBA", (W * len(names), H), (0, 0, 0, 0))
    for i, n in enumerate(names): img.alpha_composite(CELLS[n], (i * W, 0))
    img.save(out / "bondoq.png", optimize=True)
    bowl, bed = props(); bowl.save(out / "bowl.png", optimize=True); bed.save(out / "bed.png", optimize=True)
    anims = {k: {"intro": [index[n] for n in i], "loop": [index[n] for n in l]} for k, (i, l) in ANIMS.items()}
    (out / "bondoq.json").write_text(json.dumps({"frame": [W, H], "ground": GY, "stride": STRIDE, "cells": names, "anims": anims,
                                                 "bowl": [20, 10], "bed": [60, 12]}, indent=1), encoding="utf-8", newline="\n")
    if a.preview:
        rows = [(k, [CELLS[n] for n in i + l]) for k, (i, l) in ANIMS.items()]
        cols = max(len(f) for _, f in rows)
        pv = Image.new("RGBA", (W * 3 * cols, H * 3 * len(rows)), (5, 8, 20, 255))
        for r, (n, frs) in enumerate(rows):
            for c, f in enumerate(frs): pv.alpha_composite(f.resize((W * 3, H * 3), Image.NEAREST), (c * W * 3, r * H * 3))
        pv.save(a.preview)
    print("cells", len(names), "sheet", img.size)
    print("ANIMS =", json.dumps(anims, separators=(",", ":")))


if __name__ == "__main__":
    main()
