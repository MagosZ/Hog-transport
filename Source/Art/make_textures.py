"""Placeholder textures for the Hog shuttle.

Run from anywhere: python make_textures.py [check-image path]
Writes Textures/HogShuttle/: Body and its mask Body_m (the top-down view clipped to the footprint, from body_views.py),
WingTips (the rest of the wings, shown while the engines run), Shadow and BuildIcon (with the full wings),
Transparent, the upgrade icons, and the Autocannon roof turret with its icon.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import body_views

OUT = Path(__file__).resolve().parents[2] / "Textures" / "HogShuttle"

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
    """Upgrade icon: a cockpit computer with a flight-path screen."""
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([16, 20, 112, 96], fill=HULL, outline=OUTLINE, width=4)        # casing
    d.rectangle([26, 30, 102, 78], fill=(20, 40, 30, 255))                     # screen
    d.line([(32, 70), (52, 56), (72, 62), (96, 36)], fill=(90, 220, 120, 255), width=4)  # flight path
    d.ellipse([90, 30, 102, 42], fill=GLOW)                                    # waypoint
    for x in (34, 54, 74, 94):
        d.rectangle([x - 6, 84, x + 6, 90], fill=PANEL)                        # buttons
    d.rectangle([52, 96, 76, 110], fill=HULL_DARK, outline=OUTLINE, width=3)   # mount
    return img


def armour_icon():
    """Upgrade icon: a riveted plasteel plate."""
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    plasteel = (150, 170, 190, 255)
    d.polygon([(64, 10), (112, 30), (104, 92), (64, 118), (24, 92), (16, 30)], fill=plasteel, outline=OUTLINE)
    d.polygon([(64, 22), (100, 37), (94, 86), (64, 106), (34, 86), (28, 37)], outline=HULL_DARK)
    for x, y in ((40, 40), (88, 40), (40, 80), (88, 80), (64, 30), (64, 98)):
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=HULL_DARK)            # rivets
    return img


def cargo_icon():
    """Upgrade icon: two strapped cargo crates."""
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    crate = (170, 130, 80, 255)
    for box in ([14, 54, 70, 110], [58, 22, 114, 78]):
        d.rectangle(box, fill=crate, outline=OUTLINE, width=4)
        x0, y0, x1, y1 = box
        d.line([(x0, y0), (x1, y1)], fill=(120, 90, 50, 255), width=4)          # brace
    d.line([(8, 84), (120, 84)], fill=GLOW, width=6)                            # tie-down strap
    d.line([(64, 14), (64, 118)], fill=GLOW, width=6)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    img, mask = body_views.top()
    body, body_mask, tips = body_views.split_wings(img, mask)
    body.save(OUT / "Body.png")
    body_mask.save(OUT / "Body_m.png")
    tips.save(OUT / "WingTips.png")
    body_views.shadow(img).save(OUT / "Shadow.png")
    img.resize((256, 256), Image.LANCZOS).save(OUT / "BuildIcon.png")
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
    if len(sys.argv) > 2:                       # optional check image of the gun on the body
        body_views.with_gun(img, gun).save(sys.argv[2])
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
