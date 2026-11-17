"""Placeholder textures for the Hog shuttle.

Run from anywhere: python make_textures.py [check-image path]
Writes Textures/HogShuttle/: Body and its mask Body_m (the top-down view clipped to the footprint, from body_views.py),
WingTips (the rest of the wings, shown while the engines run), Shadow and BuildIcon (with the full wings),
Transparent, the upgrade icons, and the Autocannon roof turret with its icon; and the Workshop preview,
About/Preview.png.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import body_views

OUT = Path(__file__).resolve().parents[2] / "Textures" / "HogShuttle"
ABOUT = Path(__file__).resolve().parents[2] / "About"

HULL = (120, 124, 130, 255)
HULL_DARK = (82, 86, 92, 255)
PANEL = (150, 154, 160, 255)
WINDOW = (70, 150, 200, 255)
THRUSTER = (60, 62, 66, 255)
GLOW = (255, 170, 60, 255)
OUTLINE = (30, 30, 34, 255)


def toilet_icon():
    """Upgrade icon: a compact chemical toilet in three-quarter view, with its tank of blue chemical, and a jerrycan of
    the chemical beside it. Drawn at 4x and scaled down, so the curves come out smooth."""
    k = 4
    img = Image.new("RGBA", (128 * k, 128 * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def box(x0, y0, x1, y1):
        return [round(x0 * k), round(y0 * k), round(x1 * k), round(y1 * k)]

    def shade(x0, y0, x1, y1, light, dark, radius=0):
        """A rounded block lit from the left: a column-by-column blend from light to dark, then the outline."""
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        steps = max(1, round((x1 - x0) * k))
        for i in range(steps):
            t = i / max(1, steps - 1)
            c = tuple(round(light[j] + (dark[j] - light[j]) * t) for j in range(3)) + (255,)
            ld.line([(round(x0 * k) + i, round(y0 * k)), (round(x0 * k) + i, round(y1 * k))], fill=c)
        maskimg = Image.new("L", img.size, 0)
        ImageDraw.Draw(maskimg).rounded_rectangle(box(x0, y0, x1, y1), radius=round(radius * k), fill=255)
        img.paste(layer, (0, 0), maskimg)
        d.rounded_rectangle(box(x0, y0, x1, y1), radius=round(radius * k), outline=OUTLINE, width=3 * k)

    ceramic, ceramic_dark = (236, 238, 240), (150, 156, 164)
    # Floor shadow.
    d.ellipse(box(14, 104, 104, 118), fill=(0, 0, 0, 70))
    # Cistern, with the chemical gauge and the flush button.
    shade(22, 10, 74, 58, ceramic, ceramic_dark, radius=7)
    d.rounded_rectangle(box(20, 6, 76, 16), radius=4 * k, fill=(214, 218, 222), outline=OUTLINE, width=3 * k)
    d.ellipse(box(42, 8, 54, 13), fill=(120, 126, 134), outline=OUTLINE, width=2 * k)
    d.rounded_rectangle(box(30, 24, 44, 52), radius=3 * k, fill=(40, 46, 54), outline=OUTLINE, width=2 * k)
    d.rounded_rectangle(box(32, 34, 42, 50), radius=2 * k, fill=(60, 150, 210))
    d.line([box(33, 36, 33, 49)[0:2], box(33, 36, 33, 49)[2:4]], fill=(170, 220, 250), width=2 * k)
    for y in (29, 33):
        d.line([box(46, y, 66, y)[0:2], box(46, y, 66, y)[2:4]], fill=(160, 166, 174), width=2 * k)
    # Pedestal.
    d.polygon([(30 * k, 70 * k), (66 * k, 70 * k), (62 * k, 108 * k), (34 * k, 108 * k)], fill=(206, 210, 214),
              outline=OUTLINE, width=3 * k)
    d.polygon([(54 * k, 72 * k), (64 * k, 72 * k), (61 * k, 106 * k), (54 * k, 106 * k)], fill=(170, 176, 184))
    # Bowl and seat, seen from above at an angle: an ellipse ring with blue chemical inside.
    d.ellipse(box(10, 54, 86, 82), fill=(196, 200, 206), outline=OUTLINE, width=3 * k)
    d.ellipse(box(12, 52, 84, 78), fill=(244, 246, 248), outline=OUTLINE, width=3 * k)
    d.ellipse(box(22, 57, 74, 73), fill=(36, 96, 150), outline=OUTLINE, width=2 * k)
    d.ellipse(box(26, 59, 68, 70), fill=(60, 150, 210))
    d.arc(box(30, 60, 58, 68), 200, 300, fill=(190, 230, 250), width=2 * k)
    # Jerrycan of the chemical: green, with a handle and a white drop.
    shade(78, 70, 110, 112, (110, 170, 120), (52, 96, 62), radius=4)
    d.rounded_rectangle(box(84, 62, 104, 72), radius=3 * k, outline=OUTLINE, width=3 * k)
    d.rectangle(box(80, 66, 86, 72), fill=(70, 72, 78), outline=OUTLINE, width=2 * k)
    drop = [(94 * k, 80 * k), (100 * k, 92 * k), (99 * k, 96 * k), (94 * k, 99 * k), (89 * k, 96 * k), (88 * k, 92 * k)]
    d.polygon(drop, fill=(240, 244, 246))
    d.line([(84 * k, 104 * k), (104 * k, 104 * k)], fill=(40, 70, 46), width=2 * k)
    return img.resize((128, 128), Image.LANCZOS)


def flight_computer_icon():
    """Upgrade icon: an angled cockpit flight computer with an orbital trajectory screen, drawn at 4x."""
    k = 4
    img = Image.new("RGBA", (128 * k, 128 * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def box(x0, y0, x1, y1):
        return [round(x0 * k), round(y0 * k), round(x1 * k), round(y1 * k)]

    def shade(x0, y0, x1, y1, light, dark, radius=0):
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        steps = max(1, round((x1 - x0) * k))
        for i in range(steps):
            t = i / max(1, steps - 1)
            c = tuple(round(light[j] + (dark[j] - light[j]) * t) for j in range(3)) + (255,)
            ld.line([(round(x0 * k) + i, round(y0 * k)), (round(x0 * k) + i, round(y1 * k))], fill=c)
        maskimg = Image.new("L", img.size, 0)
        ImageDraw.Draw(maskimg).rounded_rectangle(box(x0, y0, x1, y1), radius=round(radius * k), fill=255)
        img.paste(layer, (0, 0), maskimg)
        d.rounded_rectangle(box(x0, y0, x1, y1), radius=round(radius * k), outline=OUTLINE, width=3 * k)

    # Floor shadow & pedestal mount.
    d.ellipse(box(20, 108, 108, 120), fill=(0, 0, 0, 75))
    d.polygon([(48 * k, 96 * k), (80 * k, 96 * k), (88 * k, 114 * k), (40 * k, 114 * k)],
              fill=(78, 82, 90, 255), outline=OUTLINE, width=3 * k)
    d.line([(50 * k, 101 * k), (78 * k, 101 * k)], fill=(48, 52, 58, 255), width=2 * k)

    # Metallic avionics casing with NW bevel and corner bolts.
    shade(12, 16, 116, 98, (148, 154, 162), (96, 100, 108), radius=7)
    d.line([(17 * k, 19 * k), (111 * k, 19 * k)], fill=(184, 190, 198, 255), width=2 * k)
    d.line([(15 * k, 21 * k), (15 * k, 93 * k)], fill=(176, 182, 190, 255), width=2 * k)
    for bx, by in ((18, 22), (110, 22), (18, 92), (110, 92)):
        d.ellipse(box(bx - 2.2, by - 2.2, bx + 2.2, by + 2.2), fill=(62, 66, 72, 255))

    # Recessed phosphor holo screen with grid, horizon arc, orbital trajectory, and target reticle.
    d.rounded_rectangle(box(22, 25, 106, 79), radius=4 * k, fill=(14, 30, 24, 255), outline=OUTLINE, width=3 * k)
    for gx in range(34, 100, 14):
        d.line([(gx * k, 27 * k), (gx * k, 77 * k)], fill=(26, 60, 44, 255), width=k)
    for gy in range(35, 76, 12):
        d.line([(24 * k, gy * k), (104 * k, gy * k)], fill=(26, 60, 44, 255), width=k)
    # Planet horizon arc in lower-left.
    d.arc(box(6, 52, 74, 118), 265, 358, fill=(68, 168, 118, 255), width=3 * k)
    # Smooth orbital trajectory curve with thrust nodes.
    traj = [(28, 72), (38, 56), (52, 48), (68, 50), (82, 42), (92, 35)]
    d.line([(x * k, y * k) for x, y in traj], fill=(90, 235, 130, 255), width=3 * k)
    for nx, ny in (traj[1], traj[3]):
        d.ellipse(box(nx - 2.5, ny - 2.5, nx + 2.5, ny + 2.5), fill=(190, 255, 210, 255))
    # Glowing orange target reticle.
    tx, ty = 92, 35
    d.ellipse(box(tx - 6.5, ty - 6.5, tx + 6.5, ty + 6.5), outline=(255, 175, 65, 255), width=2 * k)
    d.ellipse(box(tx - 2.8, ty - 2.8, tx + 2.8, ty + 2.8), fill=(255, 190, 80, 255))
    # Telemetry bars on right margin.
    for idx, wbar in enumerate((10, 14, 7)):
        by = 62 + idx * 5
        d.line([((102 - wbar) * k, by * k), (102 * k, by * k)], fill=(86, 200, 136, 255), width=2 * k)

    # Illuminated cockpit bezel buttons along the bottom.
    btn_cols = ((80, 210, 120, 255), (240, 175, 65, 255), (168, 174, 182, 255), (168, 174, 182, 255))
    for i, col in enumerate(btn_cols):
        bx = 27 + i * 20
        d.rounded_rectangle(box(bx, 84, bx + 14, 92), radius=2 * k, fill=col, outline=OUTLINE, width=2 * k)
    return img.resize((128, 128), Image.LANCZOS)


def armour_icon():
    """Upgrade icon: layered plasteel armour shield plates with bevels and hex bolts, drawn at 4x."""
    k = 4
    img = Image.new("RGBA", (128 * k, 128 * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def pt(x, y):
        return (round(x * k), round(y * k))

    # Floor shadow.
    d.ellipse([26 * k, 108 * k, 102 * k, 122 * k], fill=(0, 0, 0, 75))

    outer = [(64, 10), (112, 28), (104, 92), (64, 118), (24, 92), (16, 28)]
    # Gradient fill for main plasteel plate.
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for y in range(10 * k, 119 * k):
        t = (y - 10 * k) / max(1, 108 * k)
        c = (round(185 - 75 * t), round(205 - 76 * t), round(222 - 74 * t), 255)
        ld.line([(16 * k, y), (112 * k, y)], fill=c)
    pmask = Image.new("L", img.size, 0)
    ImageDraw.Draw(pmask).polygon([pt(x, y) for x, y in outer], fill=255)
    img.paste(layer, (0, 0), pmask)

    # Lit NW chamfer & shaded SE chamfer.
    d.line([pt(24, 92), pt(16, 28), pt(64, 10), pt(112, 28)], fill=(216, 230, 244, 255), width=3 * k)
    d.line([pt(112, 28), pt(104, 92), pt(64, 118), pt(24, 92)], fill=(86, 102, 118, 255), width=3 * k)
    d.polygon([pt(x, y) for x, y in outer], outline=OUTLINE, width=3 * k)

    # Overlapping central reinforcement plate with drop shadow.
    inner = [(64, 26), (98, 40), (92, 84), (64, 102), (36, 84), (30, 40)]
    d.polygon([pt(x + 2, y + 3) for x, y in inner], fill=(0, 0, 0, 65))
    d.polygon([pt(x, y) for x, y in inner], fill=(138, 158, 178, 255), outline=OUTLINE, width=2 * k)
    d.line([pt(36, 84), pt(30, 40), pt(64, 26), pt(98, 40)], fill=(192, 210, 226, 255), width=2 * k)
    d.line([(64 * k, 32 * k), (64 * k, 96 * k)], fill=(104, 122, 140, 255), width=2 * k)
    d.line([(65 * k, 32 * k), (65 * k, 96 * k)], fill=(176, 194, 210, 255), width=k)

    # Recessed hex bolts with specular glints.
    for bx, by in ((64, 19), (26, 35), (102, 35), (32, 84), (96, 84), (64, 109)):
        d.ellipse([round((bx - 4) * k), round((by - 4) * k), round((bx + 4) * k), round((by + 4) * k)],
                  fill=(54, 62, 72, 255))
        d.ellipse([round((bx - 2.6) * k), round((by - 2.6) * k), round((bx + 2.6) * k), round((by + 2.6) * k)],
                  fill=(146, 158, 170, 255))
        d.ellipse([round((bx - 1.5) * k), round((by - 1.8) * k), round((bx + 0.2) * k), round((by - 0.1) * k)],
                  fill=(226, 236, 244, 255))
    return img.resize((128, 128), Image.LANCZOS)


def cargo_icon():
    """Upgrade icon: two strapped industrial cargo crates on a metallic pallet, drawn at 4x."""
    k = 4
    img = Image.new("RGBA", (128 * k, 128 * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def box(x0, y0, x1, y1):
        return [round(x0 * k), round(y0 * k), round(x1 * k), round(y1 * k)]

    def crate(x0, y0, x1, y1, light, dark):
        d.rectangle(box(x0 + 3, y0 + 4, x1 + 3, y1 + 4), fill=(0, 0, 0, 70))
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        steps = max(1, round((x1 - x0) * k))
        for i in range(steps):
            t = i / max(1, steps - 1)
            c = tuple(round(light[j] + (dark[j] - light[j]) * t) for j in range(3)) + (255,)
            ld.line([(round(x0 * k) + i, round(y0 * k)), (round(x0 * k) + i, round(y1 * k))], fill=c)
        cmask = Image.new("L", img.size, 0)
        ImageDraw.Draw(cmask).rounded_rectangle(box(x0, y0, x1, y1), radius=3 * k, fill=255)
        img.paste(layer, (0, 0), cmask)
        # Corrugated ribs & diagonal brace.
        d.line([(round((x0 + 4) * k), round((y0 + 4) * k)), (round((x1 - 4) * k), round((y1 - 4) * k))],
               fill=(108, 78, 44, 255), width=3 * k)
        for ry in range(round(y0 + 12), round(y1 - 8), 10):
            d.line([(round((x0 + 6) * k), ry * k), (round((x1 - 6) * k), ry * k)], fill=(116, 84, 48, 255), width=2 * k)
        d.rounded_rectangle(box(x0, y0, x1, y1), radius=3 * k, outline=OUTLINE, width=3 * k)
        # Corner metal brackets.
        for cx, cy in ((x0, y0), (x1 - 8, y0), (x0, y1 - 8), (x1 - 8, y1 - 8)):
            d.rectangle(box(cx, cy, cx + 8, cy + 8), fill=(110, 116, 124, 255), outline=OUTLINE, width=2 * k)

    # Metallic pallet base.
    d.ellipse(box(10, 104, 118, 120), fill=(0, 0, 0, 75))
    d.rounded_rectangle(box(12, 98, 116, 114), radius=3 * k, fill=(104, 110, 118, 255), outline=OUTLINE, width=3 * k)
    for sx in (26, 56, 86):
        d.rectangle(box(sx, 102, sx + 16, 110), fill=(48, 52, 58, 255))

    # Rear upper crate and front lower crate.
    crate(54, 18, 108, 72, (182, 142, 88), (132, 96, 52))
    crate(18, 46, 74, 102, (196, 154, 96), (142, 104, 58))

    # Heavy-duty orange tie-down straps wrapping neatly around the crates + ratchet buckles.
    strap, strap_hi = (232, 146, 42, 255), (255, 196, 104, 255)
    # Horizontal strap across front crate.
    d.rectangle(box(16, 70, 76, 78), fill=strap, outline=OUTLINE, width=2 * k)
    d.line([(18 * k, 72 * k), (74 * k, 72 * k)], fill=strap_hi, width=k)
    # Vertical strap across front crate down to pallet.
    d.rectangle(box(42, 44, 50, 104), fill=strap, outline=OUTLINE, width=2 * k)
    d.line([(44 * k, 46 * k), (44 * k, 102 * k)], fill=strap_hi, width=k)
    # Vertical strap across rear crate.
    d.rectangle(box(78, 16, 86, 74), fill=strap, outline=OUTLINE, width=2 * k)
    d.line([(80 * k, 18 * k), (80 * k, 72 * k)], fill=strap_hi, width=k)
    # Ratchet buckles.
    for bx, by in ((40, 68), (76, 40)):
        d.rounded_rectangle(box(bx, by, bx + 12, by + 12), radius=2 * k,
                            fill=(180, 186, 194, 255), outline=OUTLINE, width=2 * k)
        d.rectangle(box(bx + 3, by + 3, bx + 9, by + 9), fill=(72, 76, 82, 255))
    return img.resize((128, 128), Image.LANCZOS)


def font(name, size):
    """A Windows font if there is one, else Pillow's own."""
    try:
        return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
    except OSError:
        return ImageFont.load_default()


def preview(img, mask, gun):
    """The Workshop preview, About/Preview.png, 1280x720: the Hog in flight, painted in its default colours, wings out and
    the autocannon on the roof, over a dark sky, with its name."""
    w, h = 1280, 720
    out = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(out)
    for y in range(h):                                      # sky: dark slate at the top, a little lighter below
        t = y / h
        d.line([(0, y), (w, y)], fill=(round(20 + 26 * t), round(26 + 28 * t), round(36 + 30 * t), 255))
    import random
    rng = random.Random(7)
    for _ in range(160):                                    # a few faint stars
        x, y, r = rng.randrange(w), rng.randrange(h), rng.choice((1, 1, 1, 2))
        v = rng.randrange(90, 200)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(v, v, v + 20, 255))

    hog = body_views.paint(img, mask)
    hog.alpha_composite(gun, (round(3.5 * body_views.PX - gun.width / 2), round(body_views.GUN_PIVOT_Y * body_views.PX - gun.height / 2)))
    hog = hog.resize((560, 560), Image.LANCZOS).rotate(-22, resample=Image.BICUBIC, expand=True)
    cx, cy = 960, 372
    pos = (cx - hog.width // 2, cy - hog.height // 2)
    shade = Image.new("RGBA", hog.size, (0, 0, 0, 0))
    shade.putalpha(hog.getchannel("A").point(lambda a: 120 if a > 20 else 0).filter(ImageFilter.GaussianBlur(14)))
    out.alpha_composite(shade, (pos[0] + 60, pos[1] + 70))
    out.alpha_composite(hog, pos)

    d = ImageDraw.Draw(out)
    d.text((70, 226), "HOG SHUTTLE", font=font("bahnschrift.ttf", 80), fill=(236, 238, 240, 255))
    d.line([(74, 326), (440, 326)], fill=(86, 160, 104, 255), width=5)
    lines = ["A boxy spacer shuttle that hovers", "like a VTOL, crosses the world map", "and flies to orbit and back."]
    for i, line in enumerate(lines):
        d.text((72, 348 + i * 38), line, font=font("segoeui.ttf", 28), fill=(196, 202, 210, 255))
    d.text((72, 482), "Vehicle Framework  \u00b7  VTOL Vehicle  \u00b7  VVE", font=font("segoeuib.ttf", 22), fill=(150, 196, 160, 255))
    return out.convert("RGB")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    img, mask = body_views.top()
    body, body_mask, tips = body_views.split_wings(img, mask)
    body.save(OUT / "Body.png")
    body_mask.save(OUT / "Body_m.png")
    tips.save(OUT / "WingTips.png")
    body_views.shadow(img).save(OUT / "Shadow.png")
    painted = body_views.paint(img, mask)
    painted.resize((256, 256), Image.LANCZOS).save(OUT / "BuildIcon.png")
    if len(sys.argv) > 1:                       # optional check image with the grid names
        body_views.grid_overlay(img).save(sys.argv[1])
    Image.new("RGBA", (4, 4), (0, 0, 0, 0)).save(OUT / "Transparent.png")
    toilet_icon().save(OUT / "Upgrade_ChemicalToilet.png")
    flight_computer_icon().save(OUT / "Upgrade_FlightComputer.png")
    armour_icon().save(OUT / "Upgrade_PlasteelArmour.png")
    cargo_icon().save(OUT / "Upgrade_CargoOutfit.png")
    gun = body_views.autocannon()
    gun.save(OUT / "Autocannon.png")
    body_views.gun_icon(gun).save(OUT / "Upgrade_Autocannon.png")
    preview(img, mask, gun).save(ABOUT / "Preview.png", optimize=True)
    if len(sys.argv) > 2:                       # optional check image of the gun on the body
        body_views.with_gun(img, gun).save(sys.argv[2])
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
