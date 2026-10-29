"""Placeholder textures for the Hog shuttle (top-down, nose at the top = north).

Run from anywhere: python make_textures.py
Writes Textures/HogShuttle/{Body,Shadow,BuildIcon,Transparent}.png in the mod folder.
"""
from pathlib import Path

from PIL import Image, ImageDraw

PX = 64                      # pixels per map cell
CANVAS = 8                   # square texture, drawSize (8,8)
BODY_W, BODY_L = 4, 8        # footprint (4,8)
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

    # Wings, folded out: the full 4-cell width over the middle of the body.
    d.rectangle([cells(left, 3.2), cells(left + BODY_W, 5.4)], fill=HULL_DARK, outline=OUTLINE, width=3)
    # Boxy hull, a bit narrower than the wings.
    d.rectangle([cells(left + 0.5, 0.4), cells(left + BODY_W - 0.5, 7.2)], fill=HULL, outline=OUTLINE, width=4)
    # Hull panels.
    for y in (1.8, 3.0, 4.2, 5.4):
        d.line([cells(left + 0.6, y), cells(left + BODY_W - 0.6, y)], fill=PANEL, width=3)
    # Cockpit windows at the nose.
    d.rectangle([cells(left + 1.0, 0.7), cells(left + BODY_W - 1.0, 1.4)], fill=WINDOW, outline=OUTLINE, width=3)
    # Rear thrusters with glow.
    for x in (left + 0.6, left + BODY_W - 1.6):
        d.rectangle([cells(x, 7.0), cells(x + 1.0, 7.6)], fill=THRUSTER, outline=OUTLINE, width=3)
        d.rectangle([cells(x + 0.2, 7.6), cells(x + 0.8, 7.85)], fill=GLOW)
    # Wingtip thrusters for the VTOL hover.
    for x in (left + 0.05, left + BODY_W - 0.55):
        d.ellipse([cells(x, 3.9), cells(x + 0.5, 4.7)], fill=THRUSTER, outline=GLOW, width=4)
    return img


def shadow_image(body):
    alpha = body.getchannel("A").point(lambda a: 140 if a else 0)
    shadow = Image.new("RGBA", body.size, (0, 0, 0, 0))
    shadow.putalpha(alpha)
    return shadow


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    body = body_image()
    body.save(OUT / "Body.png")
    shadow_image(body).save(OUT / "Shadow.png")
    body.resize((256, 256), Image.LANCZOS).save(OUT / "BuildIcon.png")
    Image.new("RGBA", (4, 4), (0, 0, 0, 0)).save(OUT / "Transparent.png")
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
