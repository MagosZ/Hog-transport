"""Placeholder textures for the Hog shuttle (top-down, nose at the top = north).

Run from anywhere: python make_textures.py
Writes Textures/HogShuttle/{Body,Shadow,BuildIcon,Transparent,Upgrade_ChemicalToilet,Upgrade_FlightComputer,Upgrade_PlasteelArmour,Upgrade_CargoOutfit}.png in the mod folder.
"""
from pathlib import Path

from PIL import Image, ImageDraw

PX = 64                      # pixels per map cell
CANVAS = 8                   # square texture, drawSize (8,8)
BODY_W, BODY_L = 4, 7        # footprint (4,7)
OUT = Path(__file__).resolve().parents[2] / "Textures" / "HogShuttle"

HULL = (120, 124, 130, 255)
HULL_DARK = (82, 86, 92, 255)
PANEL = (150, 154, 160, 255)
WINDOW = (70, 150, 200, 255)
THRUSTER = (60, 62, 66, 255)
GLOW = (255, 170, 60, 255)
OUTLINE = (30, 30, 34, 255)


def cells(x, y):
    return int(x * PX), int(y * PX)


def body_image():
    size = CANVAS * PX
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    left = (CANVAS - BODY_W) / 2
    top = (CANVAS - BODY_L) / 2
    # Grid names (DESIGN.md): columns A-D from `left`, rows 1-7 from `top`; the parts in components.py sit here.

    def c(x, row_y):
        """A point `x` cells from the body's left edge and `row_y` cells down from its nose."""
        return cells(left + x, top + row_y)

    # Wings, swept back, on the sides of rows 2-5 (columns A and D).
    for inner, outer in ((1.0, 0.0), (3.0, 4.0)):
        d.polygon([c(inner, 1.2), c(outer, 2.4), c(outer, 5.0), c(inner, 4.6)], fill=HULL_DARK, outline=OUTLINE)
    # Boxy hull over columns B-C, widening behind the cockpit.
    d.polygon([c(1.0, 0.1), c(3.0, 0.1), c(3.4, 1.0), c(3.4, 6.9), c(0.6, 6.9), c(0.6, 1.0)],
              fill=HULL, outline=OUTLINE)
    # Cockpit box at the front centre (B1-C1), canopy at the nose.
    d.rectangle([c(1.1, 0.2), c(2.9, 1.0)], fill=PANEL, outline=OUTLINE, width=3)
    d.rectangle([c(1.3, 0.3), c(2.7, 0.8)], fill=WINDOW, outline=OUTLINE, width=3)
    # Hull panels over the cargo bay.
    for y in (2.0, 3.0, 4.0, 5.0, 6.0):
        d.line([c(0.7, y), c(3.3, y)], fill=PANEL, width=3)
    # Ducted turbofans on the upper sides (columns A and D, rows 2-5).
    for x in (0.05, BODY_W - 0.95):
        for y in (1.6, 3.4):
            d.ellipse([c(x, y), c(x + 0.9, y + 0.9)], fill=THRUSTER, outline=OUTLINE, width=3)
            d.ellipse([c(x + 0.15, y + 0.15), c(x + 0.75, y + 0.75)], outline=GLOW, width=4)
    # Rear door across row 7, with the fuel intake in its middle.
    d.rectangle([c(0.6, 6.1), c(3.4, 6.9)], fill=HULL_DARK, outline=OUTLINE, width=3)
    d.rectangle([c(1.7, 6.3), c(2.3, 6.7)], fill=(200, 160, 60, 255))
    return img


def shadow_image(body):
    alpha = body.getchannel("A").point(lambda a: 140 if a else 0)
    shadow = Image.new("RGBA", body.size, (0, 0, 0, 0))
    shadow.putalpha(alpha)
    return shadow


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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    body = body_image()
    body.save(OUT / "Body.png")
    shadow_image(body).save(OUT / "Shadow.png")
    body.resize((256, 256), Image.LANCZOS).save(OUT / "BuildIcon.png")
    Image.new("RGBA", (4, 4), (0, 0, 0, 0)).save(OUT / "Transparent.png")
    toilet_icon().save(OUT / "Upgrade_ChemicalToilet.png")
    flight_computer_icon().save(OUT / "Upgrade_FlightComputer.png")
    armour_icon().save(OUT / "Upgrade_PlasteelArmour.png")
    cargo_icon().save(OUT / "Upgrade_CargoOutfit.png")
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
