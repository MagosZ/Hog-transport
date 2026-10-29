"""Placeholder textures for the Hog shuttle (top-down, nose at the top = north).

Run from anywhere: python make_textures.py
Writes Textures/HogShuttle/{Body,Shadow,BuildIcon,Transparent,Upgrade_ChemicalToilet,Upgrade_FlightComputer,Upgrade_PlasteelArmour,Upgrade_CargoOutfit}.png in the mod folder.
"""
import sys
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
    """Top-down, nose up. Every feature is drawn inside the grid cells of the part it shows (components.py)."""
    size = CANVAS * PX
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    under = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    left = (CANVAS - BODY_W) / 2
    top = (CANVAS - BODY_L) / 2
    # Grid names (DESIGN.md): column A is x 0-1, B 1-2, C 2-3, D 3-4; row r is y r-1 to r (from the nose).

    def c(x, y):
        """A point `x` cells from the body's port edge and `y` cells back from its nose."""
        return cells(left + x, top + y)

    # Skids (underneath; drawn see-through so they read through the hull). Front skid B2-C2: a crossbar with
    # two runners. Rear skids A4-A5 / D4-D5: runners outboard of the turbofans.
    u = ImageDraw.Draw(under)
    skid = (20, 20, 24, 255)
    u.rectangle([c(1.15, 1.15), c(1.35, 1.85)], fill=skid)
    u.rectangle([c(2.65, 1.15), c(2.85, 1.85)], fill=skid)
    u.rectangle([c(1.15, 1.42), c(2.85, 1.58)], fill=skid)
    for x in (0.06, 3.74):
        u.rectangle([c(x, 3.1), c(x + 0.2, 4.9)], fill=skid)
        u.rectangle([c(x - 0.02, 3.05), c(x + 0.22, 3.2)], fill=skid)
        u.rectangle([c(x - 0.02, 4.8), c(x + 0.22, 4.95)], fill=skid)

    # Wings A2-A6 / D2-D6: flat angular plates, swept, with a light on each tip.
    for root, tip in ((1.0, 0.0), (3.0, 4.0)):
        d.polygon([c(root, 1.05), c(tip, 2.0), c(tip, 5.4), c((root + tip) / 2, 5.95), c(root, 5.95)],
                  fill=HULL_DARK, outline=OUTLINE)
        d.ellipse([c(tip - 0.18 if tip else 0.04, 5.15), c(tip - 0.04 if tip else 0.18, 5.29)], fill=GLOW)

    # Hull: the body over columns B-C, the rear section full width (row 7, the rear door).
    d.polygon([c(1.0, 0.95), c(3.0, 0.95), c(3.15, 1.2), c(3.15, 6.0), c(3.95, 6.05), c(3.95, 6.95),
               c(0.05, 6.95), c(0.05, 6.05), c(0.85, 6.0), c(0.85, 1.2)], fill=HULL, outline=OUTLINE)
    # Cockpit B1-C1: a faceted armoured box, canopy at the front.
    d.polygon([c(1.25, 0.05), c(2.75, 0.05), c(2.95, 0.3), c(2.95, 1.0), c(1.05, 1.0), c(1.05, 0.3)],
              fill=PANEL, outline=OUTLINE)
    d.polygon([c(1.35, 0.15), c(2.65, 0.15), c(2.8, 0.35), c(2.8, 0.6), c(1.2, 0.6), c(1.2, 0.35)],
              fill=WINDOW, outline=OUTLINE)
    # Roof panels: cabin hatch (B2-C2), fuel tank bay (B3-C4), pumps and servos (B5-C5).
    d.rectangle([c(1.3, 1.25), c(2.7, 1.8)], outline=PANEL, width=3)
    d.rectangle([c(1.2, 2.15), c(2.8, 3.85)], outline=PANEL, width=3)
    d.line([c(1.2, 3.0), c(2.8, 3.0)], fill=PANEL, width=2)
    for y in (4.25, 4.5, 4.75):
        d.line([c(1.3, y), c(2.7, y)], fill=PANEL, width=2)
    # Fuel intake B6-C6: refuelling hatch with its cap.
    d.rectangle([c(1.4, 5.15), c(2.6, 5.85)], fill=HULL_DARK, outline=OUTLINE, width=3)
    d.ellipse([c(1.8, 5.3), c(2.2, 5.7)], fill=(200, 160, 60, 255), outline=OUTLINE)
    # Rear door across row 7: hinge line and the two door leaves.
    d.line([c(0.1, 6.12), c(3.9, 6.12)], fill=OUTLINE, width=4)
    d.line([c(2.0, 6.15), c(2.0, 6.9)], fill=OUTLINE, width=3)
    for x in (0.4, 3.6):
        d.rectangle([c(x - 0.12, 6.4), c(x + 0.12, 6.65)], fill=PANEL, outline=OUTLINE)

    # Turbofans A3-A5 / D3-D5: long nacelles on the hull's shoulders, fan intake at the front, ribbed housing.
    for x0 in (0.06, 3.04):   # inside columns A and D
        x1 = x0 + 0.9
        d.rounded_rectangle([c(x0, 2.35), c(x1, 4.95)], radius=int(0.2 * PX), fill=THRUSTER, outline=OUTLINE,
                            width=3)
        for y in (3.4, 3.8, 4.2, 4.6):
            d.line([c(x0 + 0.1, y), c(x1 - 0.1, y)], fill=HULL_DARK, width=3)
        d.ellipse([c(x0, 2.05), c(x1, 3.0)], fill=(176, 120, 70, 255), outline=OUTLINE, width=4)   # copper fan
        d.ellipse([c(x0 + 0.3, 2.35), c(x1 - 0.3, 2.7)], fill=OUTLINE)

    # Skids show faintly through everything above them.
    faint = under.copy()
    faint.putalpha(under.getchannel("A").point(lambda a: 110 if a else 0))
    return Image.alpha_composite(img, faint)


def grid_overlay(body):
    """Check image (not shipped): the grid names drawn over the body."""
    img = body.copy()
    d = ImageDraw.Draw(img)
    left = (CANVAS - BODY_W) / 2
    top = (CANVAS - BODY_L) / 2
    for i in range(BODY_W + 1):
        d.line([cells(left + i, top), cells(left + i, top + BODY_L)], fill=(255, 0, 0, 255), width=2)
    for j in range(BODY_L + 1):
        d.line([cells(left, top + j), cells(left + BODY_W, top + j)], fill=(255, 0, 0, 255), width=2)
    for i in range(BODY_W):
        for j in range(BODY_L):
            d.text(cells(left + i + 0.05, top + j + 0.05), f"{'ABCD'[i]}{j + 1}", fill=(255, 0, 0, 255))
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
    if len(sys.argv) > 1:
        grid_overlay(body).save(sys.argv[1])   # optional check image path
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
