"""Placeholder textures for the Hog shuttle.

Run from anywhere: python make_textures.py [check-image path]
Writes Textures/HogShuttle/: Body and its mask Body_m (the top-down view, from body_views.py), Shadow, BuildIcon,
Transparent and the upgrade icons.
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
    """Upgrade icon: a chemical toilet seen from the side."""
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([30, 14, 62, 66], fill=PANEL, outline=OUTLINE, width=4)        # tank
    d.rectangle([38, 24, 54, 32], fill=(90, 180, 110, 255))                    # chemical gauge
    d.rectangle([40, 62, 64, 112], fill=HULL, outline=OUTLINE, width=4)        # base
    d.ellipse([40, 54, 104, 78], fill=HULL_DARK, outline=OUTLINE, width=4)     # seat
    d.ellipse([52, 60, 92, 72], fill=(60, 110, 160, 255))                      # bowl
    d.rectangle([34, 110, 74, 118], fill=OUTLINE)                              # foot
    return img


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


def door_gun(kind):
    """Placeholder door gun seen from above, barrel pointing north (Vehicle Framework turns it). The pivot is the
    texture's centre. Only used without "VVE - Secondary Weapons", whose own gun art replaces these."""
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    dark, mid, light = (40, 42, 46, 255), (78, 80, 86, 255), (130, 132, 138, 255)
    if kind == "minigun":
        for x in (118, 124, 130, 136):                                   # six-barrel cluster, four visible
            d.rectangle([x - 2, 14, x + 2, 118], fill=dark)
        d.rectangle([112, 40, 144, 48], fill=mid, outline=OUTLINE)     # barrel clamps
        d.rectangle([112, 96, 144, 104], fill=mid, outline=OUTLINE)
        d.rounded_rectangle([108, 112, 148, 176], radius=8, fill=mid, outline=OUTLINE, width=3)   # motor housing
        d.rectangle([120, 176, 136, 200], fill=dark)                    # spade grips
        d.rectangle([104, 196, 152, 204], fill=dark)
    else:
        heavy = kind == "hmg"
        w = 5 if heavy else 3
        d.rectangle([128 - w, 6 if heavy else 18, 128 + w, 130], fill=dark)             # barrel
        if heavy:
            d.rectangle([122, 60, 134, 110], fill=mid, outline=OUTLINE)                # barrel jacket
        d.rectangle([52, 108, 204, 124], fill=light, outline=OUTLINE, width=3)          # gun shield, seen edge-on
        d.rectangle([116, 116, 140, 190], fill=mid, outline=OUTLINE, width=3)           # receiver
        d.rectangle([90, 128, 116, 150], fill=(176, 150, 90, 255), outline=OUTLINE)     # ammo box (left)
        d.rectangle([124, 190, 132, 206], fill=dark)                                    # grip
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    img, mask = body_views.top()
    img.save(OUT / "Body.png")
    mask.save(OUT / "Body_m.png")
    body_views.shadow(img).save(OUT / "Shadow.png")
    img.resize((256, 256), Image.LANCZOS).save(OUT / "BuildIcon.png")
    if len(sys.argv) > 1:                       # optional check image with the grid names
        body_views.grid_overlay(img).save(sys.argv[1])
    Image.new("RGBA", (4, 4), (0, 0, 0, 0)).save(OUT / "Transparent.png")
    toilet_icon().save(OUT / "Upgrade_ChemicalToilet.png")
    flight_computer_icon().save(OUT / "Upgrade_FlightComputer.png")
    armour_icon().save(OUT / "Upgrade_PlasteelArmour.png")
    cargo_icon().save(OUT / "Upgrade_CargoOutfit.png")
    for kind, name in (("mmg", "Gun_MMG"), ("hmg", "Gun_HMG"), ("minigun", "Gun_Minigun")):
        door_gun(kind).save(OUT / f"{name}.png")
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
