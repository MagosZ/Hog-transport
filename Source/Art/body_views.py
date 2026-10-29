"""The Hog seen from straight above, nose up: Body.png and its paint mask Body_m.png (red = hull and nacelles,
green = cockpit armour and the wing stripe, blue = wings). VTOL Vehicle turns this one picture to the aircraft's
heading, as the Hind's single top-down view.

What shows from above, and what doesn't:
- Only upward-facing surfaces. Vertical faces (the cockpit's sides, the rear door) don't show: row 7 is roof.
- The turbofans face forward, so from above each is a cylinder lying lengthwise: a long nacelle shaded across its
  width, the intake lip as a thin band at the front, the exhaust nozzle's rim at the back. The fan isn't visible.
- The cockpit windscreen slopes back, so it shows as a short, foreshortened band at the front of the cockpit roof.
- The skids are under the hull and the wings: hidden.
- Height comes from light (from the top left, north-west) and from shadows cast down and to the right onto
  whatever lies lower: the hull and the nacelles shade the wings.

Every feature sits inside the grid cells of its part (components.py, DESIGN.md): columns A-D port to starboard,
rows 1-7 nose to tail. The wings run one cell past the footprint on each side (art only, no hitbox). The texture is
square, drawSize (7,7), like the Hind's, so it turns cleanly: the 6-cell span sits in the middle.
"""
import math

from PIL import Image, ImageDraw, ImageFilter

PX = 128                  # pixels per cell, as VVE's vehicles
SS = 2                    # supersampling
SIZE = 7                  # square texture, drawSize (7,7)
A = (SIZE - 4) / 2        # left edge of column A; B, C, D follow at +1, +2, +3
B, C, D, END = A + 1, A + 2, A + 3, A + 4

OUTLINE = (30, 31, 35)
GLASS = (52, 104, 142)
GLASS_HI = (150, 200, 230)
BRASS = (196, 150, 86)
BRASS_DARK = (120, 92, 52)
HEAT = 88
LIGHT = (255, 190, 90)
CAP = (206, 168, 64)
GRILLE = (46, 48, 52)

HULL, ARMOUR, WING = (255, 0, 0), (0, 255, 0), (0, 0, 255)   # mask channels
NONE = (0, 0, 0)


class Canvas:
    def __init__(self):
        n = SIZE * PX * SS
        self.img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        self.mask = Image.new("RGB", (n, n), NONE)
        self.d = ImageDraw.Draw(self.img)
        self.m = ImageDraw.Draw(self.mask)

    @staticmethod
    def p(x, y):
        return round(x * PX * SS), round(y * PX * SS)

    def pts(self, points):
        return [self.p(x, y) for x, y in points]

    @staticmethod
    def w(cells):
        return max(1, round(cells * PX * SS))

    @staticmethod
    def rgb(c):
        return c if isinstance(c, tuple) else (c, c, c)

    def poly(self, points, grey, mask=None, outline=True):
        self.d.polygon(self.pts(points), fill=self.rgb(grey) + (255,))
        if outline:
            self.d.polygon(self.pts(points), outline=OUTLINE + (255,), width=self.w(0.018))
        if mask is not None:
            self.m.polygon(self.pts(points), fill=mask)

    def rect(self, x0, y0, x1, y1, grey, mask=None, outline=True):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], grey, mask, outline)

    def line(self, points, colour, width=0.015):
        self.d.line(self.pts(points), fill=self.rgb(colour) + (255,), width=self.w(width))

    def groove(self, points, base):
        """An engraved panel line: a dark cut with a light lip below and right of it."""
        self.line([(x + 0.012, y + 0.012) for x, y in points], min(255, base + 40), 0.012)
        self.line(points, max(0, base - 70), 0.014)

    def dot(self, x, y, r, colour, mask=NONE):
        box = [self.p(x - r, y - r), self.p(x + r, y + r)]
        self.d.ellipse(box, fill=self.rgb(colour) + (255,))
        if mask is not None:
            self.m.ellipse(box, fill=mask)

    def rivet(self, x, y):
        self.dot(x, y, 0.024, 120, None)
        self.dot(x - 0.008, y - 0.008, 0.012, 215, None)

    def shadow(self, points, dx, dy, strength=0.42):
        """A shadow cast down-right onto what is already drawn (never onto empty ground)."""
        layer = Image.new("L", self.img.size, 0)
        ImageDraw.Draw(layer).polygon(self.pts([(x + dx, y + dy) for x, y in points]), fill=round(255 * strength))
        layer = layer.filter(ImageFilter.GaussianBlur(self.w(0.03)))
        layer = Image.composite(layer, Image.new("L", layer.size, 0), self.img.getchannel("A"))
        black = Image.new("RGBA", self.img.size, (0, 0, 0, 255))
        black.putalpha(layer)
        self.img = Image.alpha_composite(self.img, black)
        self.d = ImageDraw.Draw(self.img)

    def cylinder(self, x0, y0, x1, y1, base, mask=None, outline=True):
        """A cylinder lying north-south, seen from above: lit on the left, a highlight, dark on the right.
        `base` is a grey or an (r, g, b) colour."""
        n = 48
        col = self.rgb(base)
        for i in range(n):
            t = (i + 0.5) / n                                    # 0 = port edge, 1 = starboard edge
            normal = math.acos(1 - 2 * t)                        # surface angle across the cylinder
            light = 0.55 + 0.45 * math.cos(normal - math.radians(60))
            spec = 0.35 * max(0.0, math.cos((t - 0.3) * 9)) ** 8
            g = tuple(min(255, round(ch * light + 255 * spec)) for ch in col)
            xa, xb = x0 + (x1 - x0) * i / n, x0 + (x1 - x0) * (i + 1) / n
            self.d.rectangle([self.p(xa, y0), self.p(xb, y1)], fill=g + (255,))
        if outline:
            self.d.rectangle([self.p(x0, y0), self.p(x1, y1)], outline=OUTLINE + (255,), width=self.w(0.018))
        if mask is not None:
            self.m.rectangle([self.p(x0, y0), self.p(x1, y1)], fill=mask)

    def done(self):
        size = (SIZE * PX, SIZE * PX)
        return self.img.resize(size, Image.LANCZOS), self.mask.resize(size, Image.NEAREST)


def wing_outline(side):
    """Port (-1) or starboard (+1) wing: rows 2-6, from under the hull out to one cell past the footprint."""
    root, tip = (B - 0.05, A - 0.95) if side < 0 else (D + 0.05, END + 0.95)
    back = tip - side * 0.45
    return [(root, 1.1), (tip, 2.35), (tip, 5.2), (back, 5.95), (root, 5.95)], root, tip


HULL_PTS = [(B - 0.15, 1.0), (D + 0.15, 1.0), (D + 0.15, 6.96), (B - 0.15, 6.96)]   # the four corner cells stay empty


def top():
    v = Canvas()

    # 1. Wings (the lowest surfaces): flat plates, a lit leading edge, a dark trailing edge, the green stripe.
    for side in (-1, 1):
        pts, root, tip = wing_outline(side)
        v.poly(pts, 168, WING)
        v.line([pts[0], pts[1]], 212, 0.04)                                 # leading edge catches the light
        v.line([pts[3], pts[4]], 112, 0.035)                                # trailing edge
        v.poly([(root, 4.72), (tip, 4.72), (tip, 4.98), (root, 4.98)], 186, ARMOUR, outline=False)
        for y in (2.95, 3.6, 4.25):
            v.groove([(root, y), (tip, y)], 168)
        v.groove([((root + tip) / 2, 1.75), ((root + tip) / 2, 5.9)], 168)
        lx = tip - side * 0.14
        v.dot(lx, 5.12, 0.07, LIGHT)
        v.dot(lx - 0.02, 5.1, 0.025, (255, 240, 200))

    # 2. Hull (higher): its shadow falls down-right onto the starboard wing, then the hull itself.
    v.shadow(HULL_PTS, 0.16, 0.16)
    v.poly(HULL_PTS, 196, HULL)
    # Roof facets: flat top, lit west chamfer, shaded east chamfer, lit front edge.
    v.poly([(B + 0.12, 1.12), (D - 0.12, 1.12), (D - 0.12, 5.98), (B + 0.12, 5.98)], 204, HULL, outline=False)
    v.poly([(B - 0.15, 1.0), (B + 0.12, 1.12), (B + 0.12, 5.98), (B - 0.15, 6.0)], 226, HULL, outline=False)
    v.poly([(D + 0.15, 1.0), (D - 0.12, 1.12), (D - 0.12, 5.98), (D + 0.15, 6.0)], 150, HULL, outline=False)
    v.poly([(B - 0.15, 1.0), (D + 0.15, 1.0), (D - 0.12, 1.12), (B + 0.12, 1.12)], 232, HULL, outline=False)
    # Rear section, row 7 (B7-C7 only; A7 and D7 are empty), a step lower: only its roof shows. The rear door
    # below it is a vertical face at the tail, so it isn't visible from above.
    v.poly([(B - 0.15, 6.0), (D + 0.15, 6.0), (D + 0.15, 6.96), (B - 0.15, 6.96)], 186, HULL)
    v.poly([(B - 0.15, 6.0), (D + 0.15, 6.0), (D + 0.05, 6.1), (B - 0.05, 6.1)], 214, HULL, outline=False)
    v.poly([(B - 0.15, 6.0), (B - 0.05, 6.1), (B - 0.05, 6.96), (B - 0.15, 6.96)], 226, HULL, outline=False)
    v.poly([(D + 0.15, 6.0), (D + 0.05, 6.1), (D + 0.05, 6.96), (D + 0.15, 6.96)], 150, HULL, outline=False)
    v.groove([(B - 0.15, 6.0), (D + 0.15, 6.0)], 196)
    v.groove([(B + 0.2, 6.5), (D - 0.2, 6.5)], 186)                         # roof panel seam
    for x in (B + 0.15, D - 0.15):
        v.rivet(x, 6.3)
    for y in (1.6, 2.6, 3.6, 4.6, 5.6):
        v.rivet(B - 0.02, y)
        v.rivet(D + 0.02, y)

    # 3. Cockpit, B1-C1: an armoured box, lower than the hull behind it. Roof with chamfers, the sloped
    #    windscreen foreshortened at the front.
    ck = [(B + 0.22, 0.04), (D - 0.22, 0.04), (D - 0.05, 0.25), (D - 0.05, 1.02), (B + 0.05, 1.02), (B + 0.05, 0.25)]
    v.poly(ck, 180, ARMOUR)
    v.poly([(B + 0.05, 0.25), (B + 0.2, 0.32), (B + 0.2, 1.02), (B + 0.05, 1.02)], 206, ARMOUR, outline=False)
    v.poly([(D - 0.05, 0.25), (D - 0.2, 0.32), (D - 0.2, 1.02), (D - 0.05, 1.02)], 140, ARMOUR, outline=False)
    v.poly([(B + 0.3, 0.1), (D - 0.3, 0.1), (D - 0.24, 0.42), (B + 0.24, 0.42)], GLASS, NONE)
    v.line([(C, 0.1), (C, 0.42)], OUTLINE, 0.025)                           # windscreen frame
    v.line([(B + 0.38, 0.17), (B + 0.75, 0.17)], GLASS_HI, 0.022)          # reflection
    v.line([(B + 0.05, 1.02), (D - 0.05, 1.02)], 110, 0.03)                  # step up to the hull roof
    v.dot(C + 0.55, 0.7, 0.05, 90, ARMOUR)                                  # roof vent

    # 4. Roof details: cabin hatch B2-C2, fuel tank bay B3-C4, vent grille B5-C5, fuel intake B6-C6.
    for x0, y0, x1, y1 in ((B + 0.3, 1.28, D - 0.3, 1.82), (B + 0.22, 2.15, D - 0.22, 3.85)):
        v.groove([(x0, y1), (x0, y0), (x1, y0)], 204)
        v.line([(x1, y0), (x1, y1), (x0, y1)], 232, 0.012)                  # inset panel: lit lower-right lip
    v.groove([(B + 0.22, 3.0), (D - 0.22, 3.0)], 204)
    v.rect(B + 0.3, 4.15, D - 0.3, 4.85, GRILLE, NONE)
    for y in (4.25, 4.4, 4.55, 4.7):
        v.line([(B + 0.34, y), (D - 0.34, y)], 120, 0.02)
    v.rect(B + 0.4, 5.15, D - 0.4, 5.85, 150, HULL)
    v.groove([(B + 0.4, 5.85), (B + 0.4, 5.15), (D - 0.4, 5.15)], 150)
    v.dot(C, 5.5, 0.17, CAP)
    v.dot(C - 0.05, 5.45, 0.06, (240, 215, 140))

    # 5. Turbofans, A3-A5 / D3-D5: cylinders lying lengthwise on the hull's shoulders. Shadow first (onto the
    #    wing and the hull side), then the nacelle: intake lip at the front, rib bands, exhaust rim at the back.
    for x0 in (A + 0.1, D + 0.1):
        x1 = x0 + 0.8
        v.shadow([(x0, 2.1), (x1, 2.1), (x1, 4.9), (x0, 4.9)], 0.18, 0.18, 0.45)
        v.cylinder(x0, 2.2, x1, 4.78, 186, HULL)
        v.cylinder(x0 - 0.02, 2.08, x1 + 0.02, 2.24, BRASS, NONE)            # intake lip, the widest part
        v.line([(x0, 2.24), (x1, 2.24)], BRASS_DARK, 0.018)
        for y in (3.55, 3.8, 4.05, 4.3, 4.55):                              # rib bands round the housing
            v.cylinder(x0, y, x1, y + 0.08, 150, HULL, outline=False)
            v.cylinder(x0, y, x1, y + 0.02, 215, HULL, outline=False)        # lit upper rim of each rib
        v.cylinder(x0 + 0.08, 4.78, x1 - 0.08, 4.9, HEAT, NONE)             # exhaust nozzle rim
        v.groove([(x0 + 0.02, 3.0), (x1 - 0.02, 3.0)], 186)
    return v.done()


def shadow(img):
    alpha = img.getchannel("A").point(lambda a: 140 if a > 20 else 0)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.putalpha(alpha)
    return out


def grid_overlay(img):
    """Check image (not shipped): the grid names over the view."""
    out = img.copy()
    dr = ImageDraw.Draw(out)
    red = (255, 0, 0, 255)
    for i in range(5):
        x = round((A + i) * PX)
        dr.line([(x, 0), (x, 7 * PX)], fill=red, width=2)
    for j in range(8):
        dr.line([(round(A * PX), j * PX), (round(END * PX), j * PX)], fill=red, width=2)
    for i in range(4):
        for j in range(7):
            dr.text((round((A + i) * PX) + 4, j * PX + 4), f"{'ABCD'[i]}{j + 1}", fill=red)
    return out
