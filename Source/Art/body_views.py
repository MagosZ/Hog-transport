"""The Hog seen from straight above, nose up: Body.png and its paint mask Body_m.png (red = hull and engine armour,
green = cockpit armour and the wing band, blue = wings). VTOL Vehicle turns this one picture to the aircraft's heading,
as the Hind's single top-down view.

Modelled on the Arvus lighter kit (Warhammer Community and painted-model photos), part by part, as seen from above:
- Cockpit: a green box narrower than the hull, with a thin front window and a larger sloped window behind it, and grey
  sensor pods against its sides. The lenses on those pods face forward, so they don't show.
- Turbofans, nose to tail: two brass intake rings, a short duct, an arched yoke, the coil machinery on a dark core, a
  second yoke, a ribbed neck, then an armoured exhaust with a heat-stained nozzle rim. The fan itself faces forward: hidden.
- Roof: the yokes reach in to a raised plate between the engines; behind it a stepped plate with vents, then a rear hatch.
- Wings: plates standing clear of the hull, with a green band along the outer edge, a white line, a stencil and a caged lamp
  at the leading corner.
- Only upward-facing surfaces show: the rear door and the skids don't.
- Height comes from light (from the top left, north-west) and from shadows cast down and to the right.

Every feature sits on the grid cells of its part (components.py, DESIGN.md) or close by: columns A-D port to starboard,
rows 1-7 nose to tail. The wings run one cell past the footprint on each side (art only, no hitbox), and split_wings() cuts
those parts off into their own texture, shown only while the engines run. The texture is square, drawSize (7,7), like the
Hind's, so it turns cleanly: the 6-cell span sits in the middle.
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
COPPER = (180, 110, 62)
HEAT_BLUE = (74, 82, 150)
GUNMETAL = 96
WHITE_LINE = 238
LAMP_CYAN = (110, 200, 230)
LAMP_RED = (210, 60, 50)
NAV_RED = (225, 55, 45)
NAV_GREEN = (70, 215, 110)

HULL, ARMOUR, WING = (255, 0, 0), (0, 255, 0), (0, 0, 255)   # mask channels
NONE = (0, 0, 0)


class Canvas:
    def __init__(self, cells=SIZE):
        self.cells = cells
        n = cells * PX * SS
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
        size = (self.cells * PX, self.cells * PX)
        return self.img.resize(size, Image.LANCZOS), self.mask.resize(size, Image.NEAREST)


WING_GAP = 0.12           # open air between the hull's side and the wing, as on the kit: they join only at the struts


def wing_outline(side):
    """Port (-1) or starboard (+1) wing: rows 2-6, from just off the hull out to one cell past the footprint."""
    root, tip = (B - 0.15 - WING_GAP, A - 0.95) if side < 0 else (D + 0.15 + WING_GAP, END + 0.95)
    back = tip - side * 0.45
    return [(root, 1.1), (tip, 2.35), (tip, 5.2), (back, 5.95), (root, 5.95)], root, tip


TAIL = 6.96
# The four corner cells stay empty, and the tail's corners are cut, as the kit's rear roof.
HULL_PTS = [(B - 0.15, 1.0), (D + 0.15, 1.0), (D + 0.15, 6.68), (D - 0.1, TAIL), (B + 0.1, TAIL), (B - 0.15, 6.68)]


def turbofan(v, nx):
    """One engine, centred on nx, nose to tail as in the photos."""
    # Soot behind the exhaust, and the shadow on the wing and the roof.
    for k in range(6):
        v.shadow([(nx - 0.32 + k * 0.03, 4.9), (nx + 0.32 - k * 0.03, 4.9), (nx + 0.22, 5.8), (nx - 0.22, 5.8)],
                 0, 0, 0.028 - k * 0.004)
    v.shadow([(nx - 0.45, 2.0), (nx + 0.45, 2.0), (nx + 0.45, 4.9), (nx - 0.45, 4.9)], 0.16, 0.16, 0.42)
    # Armoured exhaust housing, then the heat-stained nozzle rim behind it.
    v.cylinder(nx - 0.31, 4.74, nx + 0.31, 4.92, HEAT_BLUE, NONE)
    v.cylinder(nx - 0.41, 4.18, nx + 0.41, 4.76, 158, HULL)
    for x in (nx - 0.2, nx + 0.2):
        v.line([(x, 4.24), (x, 4.7)], 92, 0.016)
    v.cylinder(nx - 0.41, 4.62, nx + 0.41, 4.68, 112, HULL, outline=False)
    for x in (nx - 0.33, nx + 0.33):
        v.rivet(x, 4.3)
    # Ribbed neck.
    v.cylinder(nx - 0.27, 3.66, nx + 0.27, 4.2, GUNMETAL, NONE)
    for k in range(9):
        y = 3.7 + k * 0.055
        v.cylinder(nx - 0.27, y, nx + 0.27, y + 0.022, 150, NONE, outline=False)
    # Dark core with the coil machinery on top, and side braces.
    v.cylinder(nx - 0.31, 2.72, nx + 0.31, 3.68, 104, NONE)
    v.rect(nx - 0.41, 3.02, nx - 0.31, 3.42, 134, HULL)
    v.rect(nx + 0.31, 3.02, nx + 0.41, 3.42, 112, HULL)
    v.rect(nx - 0.19, 2.92, nx + 0.19, 3.5, 62, NONE)
    for k in range(10):
        y = 2.96 + k * 0.053
        v.line([(nx - 0.16, y), (nx + 0.16, y)], BRASS_DARK if k % 2 else BRASS, 0.016)
    for x in (nx - 0.25, nx + 0.25):
        for y in (2.98, 3.2, 3.42):
            v.dot(x, y, 0.024, 182, None)
    # Duct and the two brass intake rings, the widest part.
    v.cylinder(nx - 0.45, 2.14, nx + 0.45, 2.74, 178, HULL)
    for k in range(7):
        v.rivet(nx - 0.36 + k * 0.12, 2.28)
    v.cylinder(nx - 0.48, 2.05, nx + 0.48, 2.15, BRASS_DARK, NONE)
    v.cylinder(nx - 0.5, 1.95, nx + 0.5, 2.06, BRASS, NONE)


def yoke(v, y, left, right):
    """An arched crossbeam over the engines, lit along its front edge, reaching to the raised plate."""
    pts = [(left, y), (right, y), (right, y + 0.17), (left, y + 0.17)]
    v.shadow(pts, 0.05, 0.08, 0.4)
    v.poly(pts, 170, HULL)
    v.line([(left, y + 0.012), (right, y + 0.012)], 228, 0.014)


def top():
    v = Canvas()

    # 1. Wings (the lowest surfaces): flat plates, a lit leading edge, a dark trailing edge, panel lines and rivets. The
    #    green band runs along the outer edge, with a white line, a stencil and a ring; a caged lamp at the leading corner.
    for side in (-1, 1):
        pts, root, tip = wing_outline(side)
        v.poly(pts, 168, WING)
        for y in (2.95, 3.6, 4.25, 5.0):
            v.groove([(root, y), (tip, y)], 168)
        mid = A if side < 0 else END                                        # a plate seam where the tip folds
        v.groove([(mid, 1.75), (mid, 5.9)], 168)
        for y in (2.75, 3.4, 4.05, 4.8, 5.55):                              # rivet rows along the plate seams
            for k in (1, 2, 4):
                v.rivet(root + (tip - root) * k / 6, y + 0.12)
        # The band: from the wing's edge in to bx, following the leading edge and the rear chamfer.
        bx = tip - side * 0.6
        lead = 1.1 + (bx - root) / (tip - root) * 1.25
        band = [(bx, lead), pts[1], pts[2], pts[3], (bx, 5.95)]
        v.poly(band, 186, ARMOUR, outline=False)
        for y in (2.95, 3.6, 4.25, 5.0):
            v.groove([(bx, y), (tip, y)], 186)

        def stencil(points, width=0.022):
            v.line(points, WHITE_LINE, width)
            v.m.line(v.pts(points), fill=NONE, width=v.w(width))

        stencil([(bx, lead), (bx, 5.95)], 0.04)                             # the white line
        ex = tip - side * 0.3
        for dx in (-0.1, 0, 0.1):                                           # stencil: three arrows, crossed
            stencil([(ex - dx, 3.72), (ex + dx, 4.14)])
        stencil([(ex - 0.1, 4.3), (ex - 0.02, 4.3)], 0.05)
        stencil([(ex + 0.02, 4.3), (ex + 0.1, 4.3)], 0.05)
        v.d.ellipse([v.p(ex - 0.09, 5.2), v.p(ex + 0.09, 5.38)], outline=(44, 56, 48, 255), width=v.w(0.018))
        v.line([pts[0], pts[1]], 212, 0.03)                                 # leading edge catches the light
        v.line([pts[3], pts[4]], 112, 0.035)                                # trailing edge
        # Caged lamp at the leading corner: a dome, so it shows from above.
        lx, ly = ex, 2.62
        v.dot(lx, ly, 0.12, 70, NONE)
        v.dot(lx, ly, 0.092, LAMP_CYAN, NONE)
        v.dot(lx - 0.03, ly - 0.03, 0.03, (225, 250, 255), NONE)
        for a in (0, 60, 120):
            r = math.radians(a)
            v.line([(lx - 0.12 * math.cos(r), ly - 0.12 * math.sin(r)),
                    (lx + 0.12 * math.cos(r), ly + 0.12 * math.sin(r))], 60, 0.012)
        # Struts across the gap to the hull, at the two places the turbofan doesn't bridge it.
        for y in (1.68, 5.3):
            x0, x1 = (root - 0.03, root + WING_GAP + 0.03) if side < 0 else (root - WING_GAP - 0.03, root + 0.03)
            v.rect(x0, y, x1, y + 0.1, 92, NONE)
        # The hinge the wing tip folds on, just inside the footprint's edge, so it stays with the parked body: a long
        # barrel lying lengthwise, cut into knuckles, with a riveted leaf on the wing side. Unpainted.
        bx = A if side < 0 else END - 0.1
        lx = A + 0.1 if side < 0 else END - 0.17
        y0, y1 = 1.85, 5.85
        v.rect(lx, y0, lx + 0.07, y1, 128, NONE, outline=False)
        for k in range(8):
            v.rivet(lx + 0.035, y0 + 0.2 + k * (y1 - y0 - 0.4) / 7)
        v.cylinder(bx, y0, bx + 0.1, y1, 138, NONE)
        for k in range(1, 16):
            y = y0 + k * (y1 - y0) / 16
            v.line([(bx, y), (bx + 0.1, y)], 48, 0.012)

    # 2. Hull (higher): its shadow falls down-right onto the starboard wing, then the hull itself. Roof facets: flat top,
    #    lit west chamfer, shaded east chamfer, lit front edge. One roof to the tail; the rear door below is a vertical
    #    face, so it isn't visible from above.
    v.shadow(HULL_PTS, 0.16, 0.16)
    v.poly(HULL_PTS, 196, HULL)
    v.poly([(B + 0.12, 1.12), (D - 0.12, 1.12), (D - 0.12, 6.6), (D - 0.18, 6.84), (B + 0.18, 6.84), (B + 0.12, 6.6)],
           204, HULL, outline=False)
    v.poly([(B - 0.15, 1.0), (B + 0.12, 1.12), (B + 0.12, 6.6), (B + 0.18, 6.84), (B + 0.1, TAIL), (B - 0.15, 6.68)],
           226, HULL, outline=False)
    v.poly([(D + 0.15, 1.0), (D - 0.12, 1.12), (D - 0.12, 6.6), (D - 0.18, 6.84), (D - 0.1, TAIL), (D + 0.15, 6.68)],
           150, HULL, outline=False)
    v.poly([(B - 0.15, 1.0), (D + 0.15, 1.0), (D - 0.12, 1.12), (B + 0.12, 1.12)], 232, HULL, outline=False)
    v.poly([(B + 0.1, TAIL), (D - 0.1, TAIL), (D - 0.18, 6.84), (B + 0.18, 6.84)], 140, HULL, outline=False)
    for y in (1.6, 5.6, 6.3):
        v.rivet(B - 0.02, y)
        v.rivet(D + 0.02, y)
    # Copper pipes on the hull's shoulders, ahead of the engines.
    for x0 in (B - 0.08, D - 0.02):
        v.cylinder(x0, 1.16, x0 + 0.1, 1.96, COPPER, NONE)
        for y in (1.34, 1.72):
            v.rect(x0 - 0.02, y, x0 + 0.12, y + 0.05, 90, NONE, outline=False)

    # 3. Cockpit, B1-C1: a green armoured box narrower than the hull, with grey sensor pods against its sides. A thin
    #    front window, a larger sloped one behind a thick frame, small lamp domes at the rear corners.
    for px0, px1, shade in ((B + 0.03, B + 0.22, 172), (D - 0.22, D - 0.03, 150)):
        pod = [(px0, 0.34), (px1, 0.34), (px1, 0.82), (px0, 0.82)]
        v.poly(pod, shade, HULL)
        v.line([(px0, 0.35), (px1, 0.35)], 226, 0.012)
        for y in (0.44, 0.58, 0.72):
            v.line([(px0 + 0.03, y), (px1 - 0.03, y)], 96, 0.016)
    ck = [(B + 0.37, 0.04), (D - 0.37, 0.04), (D - 0.2, 0.25), (D - 0.2, 1.02), (B + 0.2, 1.02), (B + 0.2, 0.25)]
    v.poly(ck, 180, ARMOUR)
    v.poly([(B + 0.2, 0.25), (B + 0.33, 0.32), (B + 0.33, 1.02), (B + 0.2, 1.02)], 206, ARMOUR, outline=False)
    v.poly([(D - 0.2, 0.25), (D - 0.33, 0.32), (D - 0.33, 1.02), (D - 0.2, 1.02)], 140, ARMOUR, outline=False)
    v.poly([(B + 0.5, 0.09), (D - 0.5, 0.09), (D - 0.45, 0.2), (B + 0.45, 0.2)], GLASS, NONE)
    v.poly([(B + 0.42, 0.28), (D - 0.42, 0.28), (D - 0.52, 0.64), (B + 0.52, 0.64)], GLASS, NONE)
    v.line([(B + 0.55, 0.34), (C - 0.1, 0.34)], GLASS_HI, 0.022)            # reflection
    v.line([(B + 0.2, 1.02), (D - 0.2, 1.02)], 110, 0.03)                   # step up to the hull roof
    v.rect(C - 0.3, 0.72, C + 0.3, 0.94, 168, ARMOUR)                       # a roof plate behind the window
    for k in range(7):
        v.rivet(C - 0.54 + 0.18 * k, 0.68)
    for x, col in ((B + 0.42, NAV_RED), (D - 0.42, NAV_GREEN)):
        v.dot(x, 0.86, 0.045, col)
        v.dot(x - 0.012, 0.848, 0.014, (255, 240, 230))

    # 4. Roof. Row 2: a raised sensor block with lens domes, its shadow, the cabin hatch. Then the raised plate between
    #    the engines, the stepped plate with vents and the refuelling cap, and the rear hatch with an antenna post.
    box = [(B + 0.3, 1.1), (D - 0.3, 1.1), (D - 0.3, 1.52), (B + 0.3, 1.52)]
    v.shadow(box, 0.07, 0.07, 0.4)
    v.poly(box, 214, HULL)
    v.line([(B + 0.3, 1.1), (D - 0.3, 1.1)], 240, 0.015)
    v.rect(B + 0.4, 1.18, B + 0.85, 1.44, GRILLE, NONE)
    for x in (D - 0.72, D - 0.46):
        v.dot(x, 1.31, 0.095, 80, NONE)
        v.dot(x, 1.31, 0.07, LAMP_CYAN, NONE)
        v.dot(x - 0.022, 1.288, 0.02, (225, 250, 255), NONE)
    v.groove([(B + 0.45, 1.95), (B + 0.45, 1.62), (D - 0.45, 1.62)], 204)   # cabin hatch
    v.line([(D - 0.45, 1.62), (D - 0.45, 1.95), (B + 0.45, 1.95)], 232, 0.012)

    plate = [(C - 0.34, 2.62), (C + 0.34, 2.62), (C + 0.56, 3.02), (C + 0.56, 3.34), (C + 0.34, 3.74), (C - 0.34, 3.74),
             (C - 0.56, 3.34), (C - 0.56, 3.02)]
    v.shadow(plate, 0.07, 0.09, 0.42)
    v.poly(plate, 212, HULL)
    v.line([plate[7], plate[0], plate[1]], 240, 0.014)
    inner = [(C - 0.24, 2.8), (C + 0.24, 2.8), (C + 0.38, 3.06), (C + 0.38, 3.3), (C + 0.24, 3.56), (C - 0.24, 3.56),
             (C - 0.38, 3.3), (C - 0.38, 3.06)]
    v.line(inner + [inner[0]], 150, 0.014)
    for x in (C - 0.16, C + 0.16):                                          # tank fillers
        v.dot(x, 3.18, 0.085, 150, HULL)
        v.groove([(x - 0.06, 3.18), (x + 0.06, 3.18)], 150)

    step = [(C - 0.62, 4.02), (C + 0.62, 4.02), (C + 0.82, 4.36), (C + 0.82, 5.3), (C + 0.56, 5.6), (C - 0.56, 5.6),
            (C - 0.82, 5.3), (C - 0.82, 4.36)]
    v.shadow(step, 0.05, 0.07, 0.36)
    v.poly(step, 210, HULL)
    v.line([step[7], step[0], step[1]], 238, 0.014)
    v.rect(C - 0.34, 4.26, C + 0.34, 4.9, GRILLE, NONE)
    for y in (4.36, 4.5, 4.64, 4.78):
        v.line([(C - 0.3, y), (C + 0.3, y)], 120, 0.02)
    hx = C - 0.32
    v.rect(hx - 0.17, 5.04, hx + 0.17, 5.38, 150, HULL)
    v.dot(hx, 5.21, 0.105, CAP)
    v.dot(hx - 0.035, 5.175, 0.035, (240, 215, 140))
    v.rect(C + 0.14, 5.08, C + 0.5, 5.34, 186, HULL)                        # a small access panel
    v.line([(C + 0.2, 5.21), (C + 0.44, 5.21)], 120, 0.016)

    rear = [(C - 0.62, 5.78), (C + 0.62, 5.78), (C + 0.62, 6.4), (C + 0.38, 6.66), (C - 0.38, 6.66), (C - 0.62, 6.4)]
    v.groove(rear + [rear[0]], 204)
    v.rect(C - 0.14, 6.12, C + 0.14, 6.22, 140, HULL, outline=False)        # hatch handle
    for x, y in ((C - 0.5, 5.9), (C + 0.5, 5.9), (C - 0.5, 6.34), (C + 0.5, 6.34)):
        v.rivet(x, y)
    v.shadow([(C + 0.3, 5.92), (C + 0.34, 5.92), (C + 0.34, 5.96), (C + 0.3, 5.96)], 0.08, 0.08, 0.45)  # antenna post
    v.dot(C + 0.32, 5.94, 0.03, 90, None)

    # 5. Turbofans, half a cell in from their component cells (A3-A5 / D3-D5), over the wing and the roof's edge, with the
    #    two yokes across each engine and in to the raised plate.
    nacelles = (A + 1.0, D)
    for nx in nacelles:
        turbofan(v, nx)
    yoke(v, 2.7, nacelles[0] - 0.46, C - 0.3)
    yoke(v, 2.7, C + 0.3, nacelles[1] + 0.46)
    yoke(v, 3.5, nacelles[0] - 0.46, C - 0.3)
    yoke(v, 3.5, C + 0.3, nacelles[1] + 0.46)
    # The raised plate's edge sits on top of the yokes where they meet it.
    v.poly([(C - 0.3, 2.66), (C + 0.3, 2.66), (C + 0.3, 2.74), (C - 0.3, 2.74)], 212, HULL, outline=False)
    v.poly([(C - 0.3, 3.6), (C + 0.3, 3.6), (C + 0.3, 3.7), (C - 0.3, 3.7)], 212, HULL, outline=False)
    return v.done()


# The Hog's default paint (graphicData in Defs/VehicleDefs/HogShuttle.xml), per mask channel.
DEFAULT_PAINT = ((176, 178, 182), (86, 128, 98), (150, 152, 156))


def paint(img, mask, colours=DEFAULT_PAINT):
    """The view as the game paints it: each pixel times its mask channel's colour, as the CutoutComplexPattern shader."""
    out = img.copy()
    pixels, mask_pixels = out.load(), mask.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = pixels[x, y]
            weights = mask_pixels[x, y]
            total = sum(weights)
            if a and total:
                tint = [sum(w * colour[c] for w, colour in zip(weights, colours)) / total for c in range(3)]
                pixels[x, y] = (round(r * tint[0] / 255), round(g * tint[1] / 255), round(b * tint[2] / 255), a)
    return out


def split_wings(img, mask):
    """Cut the full view at the footprint's edges. Returns the body and its mask, parked exactly 4 cells wide, and
    the wing tips, the parts outside the footprint, which VTOL Vehicle's rotor code fades in when the engines run
    (Defs/VehicleDefs/HogShuttle.xml). Rotor textures take no paint, so the tips are baked in the default colours."""
    left, right = round(A * PX), round(END * PX)
    body, body_mask, tips = img.copy(), mask.copy(), img.copy()
    pixels, mask_pixels, tip_pixels = body.load(), body_mask.load(), tips.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]
            if left <= x < right:
                tip_pixels[x, y] = (0, 0, 0, 0)
                continue
            pixels[x, y] = (0, 0, 0, 0)
            mask_pixels[x, y] = NONE
            weights = mask.getpixel((x, y))
            total = sum(weights)
            if a and total:                                  # as the paint shader: the texture times the colour
                tint = [sum(w * paint[c] for w, paint in zip(weights, DEFAULT_PAINT)) / total for c in range(3)]
                tip_pixels[x, y] = (round(r * tint[0] / 255), round(g * tint[1] / 255), round(b * tint[2] / 255), a)
    # A dark edge where each wing is cut, so the parked body has a clean outline.
    for x in (left, left + 1, right - 2, right - 1):
        for y in range(img.height):
            if pixels[x, y][3] > 128:
                pixels[x, y] = OUTLINE + (255,)
    return body, body_mask, tips


GUN_CELLS = 4             # the turret texture: square, drawSize (4,4), same pixels per cell as the body
GUN_PIVOT_Y = 1.66        # the mount's centre on the body texture: on the roof behind the cockpit, on the centre line
GUN_REACH = 1.48          # muzzle ahead of the pivot; the muzzles stop just short of the nose, over the windscreen


def autocannon():
    """The roof turret from straight above, pointing north. The whole image turns about its centre, so the mounting
    ring, being round, looks fixed to the roof while the head and barrel swing. One barrel: a ribbed cooling jacket, a bare
    tip section and a muzzle brake, with a collar at each end of the jacket. One ammo drum on the head's port side."""
    v = Canvas(GUN_CELLS)
    c = GUN_CELLS / 2
    # A low mounting ring on the roof, under everything.
    v.dot(c, c, 0.37, 58, None)
    v.dot(c, c, 0.335, 92, None)
    # Ammo drum beside the breech, lying lengthwise, with two bands.
    x0 = c - 0.47
    v.cylinder(x0, c - 0.16, x0 + 0.22, c + 0.24, 112)
    for y in (c - 0.09, c + 0.11):
        v.cylinder(x0, y, x0 + 0.22, y + 0.05, (178, 176, 120), outline=False)
    # The barrel.
    tip = c - GUN_REACH
    v.cylinder(c - 0.06, tip + 0.1, c + 0.06, c - 0.3, 104)
    v.cylinder(c - 0.09, c - 0.74, c + 0.09, c - 0.16, 88)
    for k in range(4):
        y = c - 0.7 + k * 0.125
        v.cylinder(c - 0.09, y, c + 0.09, y + 0.045, 132, outline=False)
    v.cylinder(c - 0.085, tip, c + 0.085, tip + 0.11, 76)
    v.dot(c, tip + 0.005, 0.035, 30, None)
    for y in (c - 0.76, c - 0.32):
        v.rect(c - 0.105, y, c + 0.105, y + 0.05, 62)
        v.line([(c - 0.1, y + 0.008), (c + 0.1, y + 0.008)], 140, 0.01)
    # Head: flat top, lit west chamfer, shaded east chamfer, lit front, a feed cover and rivets.
    block = [(c - 0.17, c - 0.26), (c + 0.17, c - 0.26), (c + 0.26, c - 0.14), (c + 0.26, c + 0.3),
             (c - 0.26, c + 0.3), (c - 0.26, c - 0.14)]
    v.poly(block, 86)
    v.poly([(c - 0.26, c - 0.14), (c - 0.19, c - 0.1), (c - 0.19, c + 0.23), (c - 0.26, c + 0.3)], 124, outline=False)
    v.poly([(c + 0.26, c - 0.14), (c + 0.19, c - 0.1), (c + 0.19, c + 0.23), (c + 0.26, c + 0.3)], 56, outline=False)
    v.poly([(c - 0.17, c - 0.26), (c + 0.17, c - 0.26), (c + 0.19, c - 0.1), (c - 0.19, c - 0.1)], 118, outline=False)
    v.rect(c - 0.13, c - 0.04, c + 0.13, c + 0.16, 72)
    v.groove([(c - 0.13, c + 0.16), (c - 0.13, c - 0.04), (c + 0.13, c - 0.04)], 72)
    v.rect(c - 0.05, c + 0.03, c + 0.05, c + 0.08, 128, outline=False)
    for x, y in ((-0.15, 0.23), (0.15, 0.23), (-0.15, -0.09), (0.15, -0.09)):
        v.rivet(c + x, c + y)
    return v.done()[0]


def gun_icon(gun):
    """The gun's Upgrades-tab and gizmo icon: the turret image centred on a 128 px square."""
    shape = gun.crop(gun.getbbox())
    scale = 118 / max(shape.size)
    shape = shape.resize((round(shape.width * scale), round(shape.height * scale)), Image.LANCZOS)
    icon = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    icon.alpha_composite(shape, ((128 - shape.width) // 2, (128 - shape.height) // 2))
    return icon


def with_gun(img, gun):
    """Check image (not shipped): the body with the gun on it, on a canvas with room for the muzzles."""
    out = Image.new("RGBA", (img.width, img.height + 2 * PX), (0, 0, 0, 0))
    out.alpha_composite(img, (0, 2 * PX))
    x = round((C - GUN_CELLS / 2) * PX)
    y = round((GUN_PIVOT_Y - GUN_CELLS / 2) * PX) + 2 * PX
    out.alpha_composite(gun, (x, y))
    return out


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
