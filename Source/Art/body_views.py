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

from PIL import Image, ImageDraw, ImageFilter, ImageFont

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

    def rivets(self, x0, y0, x1, y1, n):
        """A row of n rivets from one point to the other."""
        for k in range(n):
            t = k / max(1, n - 1)
            self.rivet(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)

    def bolt(self, x, y, r=0.034):
        """A bolt head: a dark seat, the head, a glint."""
        self.dot(x, y, r, 52, None)
        self.dot(x, y, r * 0.72, 150, None)
        self.dot(x - r * 0.25, y - r * 0.25, r * 0.3, 226, None)

    def shadow(self, points, dx, dy, strength=0.42):
        """A shadow cast down-right onto what is already drawn (never onto empty ground)."""
        shifted = self.pts([(x + dx, y + dy) for x, y in points])
        pad = self.w(0.12)
        x0 = max(0, min(p[0] for p in shifted) - pad)
        y0 = max(0, min(p[1] for p in shifted) - pad)
        x1 = min(self.img.width, max(p[0] for p in shifted) + pad)
        y1 = min(self.img.height, max(p[1] for p in shifted) + pad)
        if x1 <= x0 or y1 <= y0:
            return
        layer = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(layer).polygon([(px - x0, py - y0) for px, py in shifted], fill=round(255 * strength))
        layer = layer.filter(ImageFilter.GaussianBlur(self.w(0.03)))
        region = self.img.crop((x0, y0, x1, y1))
        layer = Image.composite(layer, Image.new("L", layer.size, 0), region.getchannel("A"))
        black = Image.new("RGBA", layer.size, (0, 0, 0, 255))
        black.putalpha(layer)
        self.img.paste(Image.alpha_composite(region, black), (x0, y0))

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

    def plate(self, points, grey, mask=None, lift=0.05, shade=0.4, bevel=0.028):
        """A raised plate: its shadow, the plate, and bevelled edges, lit where they face the light (north-west)."""
        if lift:
            self.shadow(points, lift, lift, shade)
        self.poly(points, grey, mask, outline=False)
        area = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(points, points[1:] + points[:1]))
        sign = 1 if area > 0 else -1
        base = self.rgb(grey)
        for p, q in zip(points, points[1:] + points[:1]):
            ex, ey = q[0] - p[0], q[1] - p[1]
            length = math.hypot(ex, ey) or 1
            nx, ny = sign * ey / length, -sign * ex / length                # outward normal
            light = -(nx + ny) * 0.707                                       # towards the top left
            col = tuple(max(0, min(255, round(c + 52 * light))) for c in base)
            inset = bevel / 2
            self.line([(p[0] - nx * inset, p[1] - ny * inset), (q[0] - nx * inset, q[1] - ny * inset)], col, bevel)
        self.d.polygon(self.pts(points), outline=OUTLINE + (255,), width=self.w(0.014))

    def box(self, x0, y0, x1, y1, grey, mask=None, **kw):
        self.plate([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], grey, mask, **kw)

    def handle(self, x, y, across=True):
        """A grab handle: a dark bar with a lit top."""
        dx, dy = (0.08, 0.018) if across else (0.018, 0.08)
        self.rect(x - dx, y - dy, x + dx, y + dy, 58, NONE, outline=False)
        self.line([(x - dx, y - dy), (x + dx, y - dy)] if across else [(x - dx, y - dy), (x - dx, y + dy)], 200, 0.01)

    def hatch(self, x0, y0, x1, y1, grey, mask=None, across=True, hinges="n"):
        """An access hatch: a low plate, a seam just inside its edge, a handle and two hinge barrels on one side."""
        self.box(x0, y0, x1, y1, grey, mask, lift=0.025, shade=0.3, bevel=0.02)
        self.groove([(x0 + 0.045, y1 - 0.045), (x0 + 0.045, y0 + 0.045), (x1 - 0.045, y0 + 0.045)], self.rgb(grey)[0])
        self.handle((x0 + x1) / 2, (y0 + y1) / 2 + (0.06 if hinges == "n" else 0), across)
        if hinges == "n":
            for hx in (x0 + (x1 - x0) * 0.25, x0 + (x1 - x0) * 0.75):
                self.rect(hx - 0.05, y0 - 0.015, hx + 0.05, y0 + 0.03, 120, NONE, outline=False)
                self.line([(hx - 0.05, y0 - 0.012), (hx + 0.05, y0 - 0.012)], 214, 0.01)
        elif hinges in "we":
            hx = x0 if hinges == "w" else x1
            for hy in (y0 + (y1 - y0) * 0.25, y0 + (y1 - y0) * 0.75):
                self.rect(hx - 0.02, hy - 0.05, hx + 0.02, hy + 0.05, 120, NONE, outline=False)
                self.line([(hx - 0.018, hy - 0.05), (hx - 0.018, hy + 0.05)], 214, 0.01)

    def vent(self, x0, y0, x1, y1, slats, across=True):
        """A louvred vent: a dark recess, its frame lit on the far sides, and slats that catch the light."""
        self.rect(x0, y0, x1, y1, GRILLE, NONE)
        self.line([(x0, y1), (x1, y1), (x1, y0)], 226, 0.012)
        for k in range(slats):
            t = (k + 0.5) / slats
            if across:
                y = y0 + (y1 - y0) * t
                self.line([(x0 + 0.03, y), (x1 - 0.03, y)], 128, 0.02)
                self.line([(x0 + 0.03, y - 0.012), (x1 - 0.03, y - 0.012)], 176, 0.008)
            else:
                x = x0 + (x1 - x0) * t
                self.line([(x, y0 + 0.03), (x, y1 - 0.03)], 128, 0.02)
                self.line([(x - 0.012, y0 + 0.03), (x - 0.012, y1 - 0.03)], 176, 0.008)

    def cable(self, points, width=0.04, base=58):
        """A hose or cable: dark, with a lit upper side and clamps at its ends."""
        self.line(points, base, width)
        self.line([(x - width * 0.22, y - width * 0.22) for x, y in points], base + 62, width * 0.3)
        for x, y in (points[0], points[-1]):
            self.dot(x, y, width * 0.75, 130, None)

    def coil(self, x0, y0, x1, y1, turns, bright=206):
        """A coil spring lying lengthwise: a dark core with the lit turns across it."""
        self.rect(x0, y0, x1, y1, 46, NONE, outline=False)
        step = (y1 - y0) / turns
        for k in range(turns):
            y = y0 + k * step
            self.line([(x0, y + step * 0.75), (x1, y + step * 0.2)], bright, 0.014)
            self.line([(x0, y + step * 0.95), (x1, y + step * 0.4)], 96, 0.008)

    def text(self, x, y, string, height, angle=0, colour=WHITE_LINE):
        """Stencilled lettering centred on (x, y), turned by `angle` degrees counter-clockwise. Unpainted. Skipped if the
        font isn't there."""
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/bahnschrift.ttf", self.w(height))
        except OSError:
            return
        left, top, right, bottom = font.getbbox(string)
        stamp = Image.new("L", (right - left + 4, bottom - top + 4), 0)
        ImageDraw.Draw(stamp).text((2 - left, 2 - top), string, font=font, fill=255)
        stamp = stamp.rotate(angle, expand=True, resample=Image.BICUBIC)
        px, py = self.p(x, y)
        at = (px - stamp.width // 2, py - stamp.height // 2)
        self.img.paste(Image.new("RGBA", stamp.size, self.rgb(colour) + (255,)), at, stamp)
        self.mask.paste(Image.new("RGB", stamp.size, NONE), at, stamp.point(lambda a: 255 if a > 90 else 0))
        self.d = ImageDraw.Draw(self.img)
        self.m = ImageDraw.Draw(self.mask)

    def done(self):
        size = (self.cells * PX, self.cells * PX)
        return self.img.resize(size, Image.LANCZOS), self.mask.resize(size, Image.NEAREST)


WING_GAP = 0.12           # open air between the hull's side and the wing, as on the kit: they join only at the struts
WING_CORNER = 0.34        # how far in from the tip the front corner is cut


def wing_outline(side):
    """Port (-1) or starboard (+1) wing, as the kit's from above: a slab standing off the hull's side, one cell past the
    footprint. The leading edge runs almost straight out, a little forward, to a cut front corner; the outer edge is
    straight; the trailing edge is one long diagonal, so the wing is a cell longer at the hull than at the tip.
    Returns the outline, the root and tip x, and the leading and trailing edges as functions of x."""
    root, tip = (B - 0.15 - WING_GAP, A - 0.95) if side < 0 else (D + 0.15 + WING_GAP, END + 0.95)
    span = abs(tip - root)
    corner = span - WING_CORNER

    def lead(x):
        u = abs(x - root)
        return 1.52 - 0.2 * u / corner if u <= corner else 1.32 + (u - corner) / WING_CORNER * 0.36

    def trail(x):
        return 5.95 - abs(x - root) / span

    pts = [(root, lead(root)), (root + side * corner, lead(root + side * corner)), (tip, lead(tip)), (tip, trail(tip)),
           (root, trail(root))]
    return pts, root, tip, lead, trail


TAIL = 6.96
# The four corner cells stay empty, and the tail's corners are cut, as the kit's rear roof.
HULL_PTS = [(B - 0.15, 1.0), (D + 0.15, 1.0), (D + 0.15, 6.68), (D - 0.1, TAIL), (B + 0.1, TAIL), (B - 0.15, 6.68)]


def wing(v, side):
    """One wing, the lowest surface: plates with seams and rivets, inspection plates, a flap along the trailing edge, the
    hinge the tip folds on, and the outer panel, turned down a little, with its white line, number, stencil and ring.
    The caged lamp sits in a pod at the front corner."""
    pts, root, tip, lead, trail = wing_outline(side)
    v.poly(pts, 168, WING)

    def within(x, y, margin=0.05):
        return lead(x) + margin < y < trail(x) - margin

    def reach(y):
        """How far out a line across the wing at y can run before it meets the trailing edge."""
        return tip if y < trail(tip) else root + side * (5.95 - y) * abs(tip - root)

    seams = (2.3, 2.95, 3.6, 4.25, 4.9)
    for y in seams:
        v.groove([(root, y), (reach(y + 0.03), y)], 168)
    fold = A if side < 0 else END                                           # a plate seam where the tip folds
    v.groove([(fold, lead(fold) + 0.04), (fold, trail(fold) - 0.04)], 168)
    for y in (2.1, 2.75, 3.4, 4.05, 4.7, 5.3):                              # rivet rows along the plate seams
        for k in (1, 2, 4, 5):
            x = root + (tip - root) * k / 6
            if within(x, y + 0.12, 0.1):
                v.rivet(x, y + 0.12)
    # The flap: a seam a little ahead of the trailing edge, with hinge knuckles along it.
    v.groove([(root, trail(root) - 0.3), (tip, trail(tip) - 0.3)], 168)
    for k in (0.12, 0.3, 0.52, 0.7, 0.9):
        hx = root + (tip - root) * k
        hy = trail(hx) - 0.3
        v.rect(hx - 0.045, hy - 0.03, hx + 0.045, hy + 0.04, 118, NONE, outline=False)
        v.line([(hx - 0.045, hy - 0.025), (hx + 0.045, hy - 0.025)], 216, 0.01)
    # Inspection plates on the strip between the outer panel and the hinge.
    sx = fold - side * 0.34
    for y in (3.06, 4.3):
        v.hatch(min(sx, sx + side * 0.22), y, max(sx, sx + side * 0.22), y + 0.44, 176, WING, across=False, hinges="x")
    # The outer panel: the strip along the outer edge, which turns down, so it's lit on the port side and shaded on
    # the starboard. Green by default.
    bx = tip - side * 0.6
    band = [(bx, lead(bx)), pts[2], pts[3], (bx, trail(bx))]
    if abs(bx - root) < abs(pts[1][0] - root):                              # the panel starts inboard of the cut corner
        band.insert(1, pts[1])
    v.poly(band, 198 if side < 0 else 170, ARMOUR, outline=False)
    for y in seams:
        if y < trail(bx) - 0.05:
            v.groove([(bx, y), (reach(y + 0.03), y)], 186)
    v.groove([(bx, trail(bx) - 0.3), (tip, trail(tip) - 0.3)], 186)

    def stencil(points, width=0.022):
        v.line(points, WHITE_LINE, width)
        v.m.line(v.pts(points), fill=NONE, width=v.w(width))

    stencil([(bx, lead(bx)), (bx, trail(bx))], 0.045)                       # the white line
    v.rivets(bx + side * 0.07, lead(bx) + 0.22, bx + side * 0.07, trail(bx) - 0.42, 14)
    ex = tip - side * 0.3
    v.d.ellipse([v.p(ex - 0.09, 2.38), v.p(ex + 0.09, 2.56)], outline=(44, 56, 48, 255), width=v.w(0.018))
    v.dot(ex, 2.47, 0.03, (44, 56, 48), None)                               # the ring, towards the front as on the kit
    v.text(ex, 3.02, "07", 0.3, angle=-90 * side)                           # the number reads from outboard
    for dx in (-0.1, 0, 0.1):                                               # stencil: three arrows, crossed
        stencil([(ex - dx, 3.5), (ex + dx, 3.9)])
    stencil([(ex - 0.1, 4.06), (ex - 0.02, 4.06)], 0.05)
    stencil([(ex + 0.02, 4.06), (ex + 0.1, 4.06)], 0.05)
    for y in (4.28, 4.36, 4.44):                                            # a block of stencilled lines
        stencil([(ex - 0.12, y), (ex + 0.12 - 0.05 * (y > 4.3), y)], 0.014)
    # Edges: the leading edge and the cut corner catch the light, the trailing edge is in shade.
    v.line([pts[0], pts[1]], 216, 0.034)
    v.line([(pts[0][0], pts[0][1] + 0.04), (pts[1][0], pts[1][1] + 0.04)], 132, 0.012)
    v.line([pts[1], pts[2]], 222 if side < 0 else 186, 0.03)
    v.line([pts[2], pts[3]], 140 if side > 0 else 204, 0.022)               # the outer edge
    v.line([pts[3], pts[4]], 108, 0.035)                                    # the trailing edge
    # The lamp pod at the front corner: a housing that stands a little ahead of the leading edge, and the caged dome.
    lx, ly = pts[1][0] + side * 0.08, pts[1][1] + 0.16
    pod = [(lx + 0.185 * math.cos(math.radians(22.5 + 45 * k)), ly - 0.02 + 0.185 * math.sin(math.radians(22.5 + 45 * k)))
           for k in range(8)]
    v.plate(pod, 150, HULL, lift=0.04, shade=0.35, bevel=0.02)
    v.dot(lx, ly, 0.135, 44, NONE)
    v.dot(lx, ly, 0.12, 84, NONE)
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
        v.line([(x0, y + 0.012), (x1, y + 0.012)], 170, 0.01)
    # The hinge the wing tip folds on, just inside the footprint's edge, so it stays with the parked body: a long
    # barrel lying lengthwise, cut into knuckles, with a riveted leaf on the wing side. Unpainted.
    hx = A if side < 0 else END - 0.1
    leaf = A + 0.1 if side < 0 else END - 0.17
    y0, y1 = lead(fold) + 0.1, trail(fold - side * 0.17) - 0.1
    v.rect(leaf, y0, leaf + 0.07, y1, 128, NONE, outline=False)
    for k in range(8):
        v.rivet(leaf + 0.035, y0 + 0.2 + k * (y1 - y0 - 0.4) / 7)
    v.cylinder(hx, y0, hx + 0.1, y1, 138, NONE)
    for k in range(1, 16):
        y = y0 + k * (y1 - y0) / 16
        v.line([(hx, y), (hx + 0.1, y)], 48, 0.012)


def hull(v):
    """The hull, higher than the wings: its shadow, the roof with chamfered sides and a cut tail, seams, rivet rows, the
    copper pipes on the shoulders, stiffener ribs and the door's hinge at the tail. The rear door below is a vertical
    face, so it isn't visible from above."""
    v.shadow(HULL_PTS, 0.16, 0.16)
    v.poly(HULL_PTS, 196, HULL)
    left, right = B + 0.12, D - 0.12
    v.poly([(left, 1.12), (right, 1.12), (right, 6.6), (D - 0.18, 6.84), (B + 0.18, 6.84), (left, 6.6)], 204, HULL,
           outline=False)
    v.poly([(B - 0.15, 1.0), (left, 1.12), (left, 6.6), (B + 0.18, 6.84), (B + 0.1, TAIL), (B - 0.15, 6.68)], 226, HULL,
           outline=False)
    v.poly([(D + 0.15, 1.0), (right, 1.12), (right, 6.6), (D - 0.18, 6.84), (D - 0.1, TAIL), (D + 0.15, 6.68)], 150, HULL,
           outline=False)
    v.poly([(B - 0.15, 1.0), (D + 0.15, 1.0), (right, 1.12), (left, 1.12)], 232, HULL, outline=False)
    v.poly([(B + 0.1, TAIL), (D - 0.1, TAIL), (D - 0.18, 6.84), (B + 0.18, 6.84)], 140, HULL, outline=False)
    v.line([(left, 1.12), (left, 6.6)], 176, 0.01)                          # the roof's edges
    v.line([(right, 1.12), (right, 6.6)], 120, 0.01)
    for y in (2.04, 4.0, 5.68):                                             # seams across the roof
        v.groove([(left, y), (right, y)], 204)
    for y in (1.56, 5.22, 5.92, 6.42):                                      # and across the chamfers
        v.line([(B - 0.15, y), (left, y)], 170, 0.012)
        v.line([(right, y), (D + 0.15, y)], 104, 0.012)
    v.rivets(left + 0.05, 1.24, left + 0.05, 6.5, 26)
    v.rivets(right - 0.05, 1.24, right - 0.05, 6.5, 26)
    v.rivets(B - 0.04, 1.2, B - 0.04, 6.6, 20)
    v.rivets(D + 0.04, 1.2, D + 0.04, 6.6, 20)
    # Copper pipes on the hull's shoulders, ahead of the engines, each with an elbow down the side.
    for x0, out in ((B - 0.08, -1), (D - 0.02, 1)):
        v.cylinder(x0, 1.16, x0 + 0.1, 1.96, COPPER, NONE)
        v.line([(x0 + 0.05, 1.2), (x0 + 0.05 + out * 0.1, 1.2)], COPPER, 0.07)
        v.dot(x0 + 0.05, 1.2, 0.055, (150, 92, 52), None)
        for y in (1.38, 1.74):
            v.rect(x0 - 0.02, y, x0 + 0.12, y + 0.05, 90, NONE, outline=False)
            v.line([(x0 - 0.02, y + 0.008), (x0 + 0.12, y + 0.008)], 170, 0.008)
    # Stiffener ribs along the rear roof, and the door's hinge across the tail.
    for x in (C - 0.78, C + 0.78):
        v.box(x - 0.04, 5.74, x + 0.04, 6.56, 188, HULL, lift=0.03, shade=0.3, bevel=0.016)
    for k in range(5):
        x = C - 0.6 + k * 0.3
        v.rect(x - 0.1, 6.865, x + 0.1, 6.93, 112, NONE, outline=False)
        v.line([(x - 0.1, 6.87), (x + 0.1, 6.87)], 204, 0.01)
    for x in (B + 0.25, D - 0.25):                                          # tail lamps, domes at the corners
        v.dot(x, 6.72, 0.045, 60, NONE)
        v.dot(x, 6.72, 0.034, NAV_RED, NONE)


def cockpit(v):
    """The cockpit, B1-C1: a green armoured box narrower than the hull, with a grey lip under its nose and sensor pods
    against its sides. A thin front window, a larger sloped canopy in a thick frame with a centre bar, quarter windows on
    the chamfers, a roof hatch and two lamp domes."""
    left, right = B + 0.2, D - 0.2
    v.rect(B + 0.42, 0.0, D - 0.42, 0.08, 150, HULL)                        # the lip under the nose
    v.rect(C - 0.1, 0.0, C + 0.1, 0.07, 70, NONE)
    for px0, px1, shade in ((B + 0.03, B + 0.22, 172), (D - 0.22, D - 0.03, 150)):
        cx = (px0 + px1) / 2                                                # sensor pods: a lens barrel points forward
        v.cylinder(cx - 0.055, 0.2, cx + 0.055, 0.36, 92, NONE)
        v.line([(cx - 0.055, 0.2), (cx + 0.055, 0.2)], LAMP_CYAN, 0.02)
        v.box(px0, 0.34, px1, 0.82, shade, HULL, lift=0.03, shade=0.3, bevel=0.018)
        for y in (0.44, 0.58, 0.72):
            v.line([(px0 + 0.03, y), (px1 - 0.03, y)], 96, 0.016)
        v.bolt(cx, 0.775, 0.022)
    box = [(B + 0.37, 0.04), (D - 0.37, 0.04), (right, 0.25), (right, 1.02), (left, 1.02), (left, 0.25)]
    v.poly(box, 180, ARMOUR)
    v.poly([(left, 0.25), (left + 0.13, 0.32), (left + 0.13, 1.02), (left, 1.02)], 206, ARMOUR, outline=False)
    v.poly([(right, 0.25), (right - 0.13, 0.32), (right - 0.13, 1.02), (right, 1.02)], 140, ARMOUR, outline=False)
    v.poly([(B + 0.37, 0.04), (left, 0.25), (left + 0.13, 0.32), (B + 0.47, 0.1)], 214, ARMOUR, outline=False)
    v.poly([(D - 0.37, 0.04), (right, 0.25), (right - 0.13, 0.32), (D - 0.47, 0.1)], 150, ARMOUR, outline=False)
    # Glass: the thin front window, the canopy, and the quarter windows on the chamfers.
    v.poly([(B + 0.5, 0.09), (D - 0.5, 0.09), (D - 0.45, 0.2), (B + 0.45, 0.2)], GLASS, NONE)
    v.poly([(B + 0.42, 0.28), (D - 0.42, 0.28), (D - 0.52, 0.64), (B + 0.52, 0.64)], GLASS, NONE)
    v.poly([(left + 0.035, 0.36), (left + 0.105, 0.39), (left + 0.105, 0.62), (left + 0.035, 0.62)], (70, 124, 160), NONE)
    v.poly([(right - 0.035, 0.36), (right - 0.105, 0.39), (right - 0.105, 0.62), (right - 0.035, 0.62)], (38, 80, 112), NONE)
    v.poly([(B + 0.44, 0.3), (C - 0.03, 0.3), (C - 0.03, 0.44), (B + 0.48, 0.44)], (86, 144, 180), None, outline=False)
    v.line([(B + 0.55, 0.34), (C - 0.12, 0.34)], GLASS_HI, 0.022)           # reflection
    v.line([(C + 0.1, 0.34), (C + 0.3, 0.34)], GLASS_HI, 0.012)
    frame = (180, 180, 180)
    v.line([(C, 0.09), (C, 0.64)], OUTLINE, 0.07)                           # the centre bar
    v.line([(C, 0.1), (C, 0.63)], frame, 0.04)
    v.m.line(v.pts([(C, 0.1), (C, 0.63)]), fill=ARMOUR, width=v.w(0.04))
    v.line([(B + 0.2, 1.02), (D - 0.2, 1.02)], 110, 0.03)                   # step up to the hull roof
    v.hatch(C - 0.3, 0.73, C + 0.3, 0.95, 172, ARMOUR)                      # the roof hatch
    v.rivets(B + 0.48, 0.24, D - 0.48, 0.24, 8)
    v.rivets(C - 0.54, 0.68, C + 0.54, 0.68, 9)
    for x in (left + 0.2, right - 0.2):
        v.bolt(x, 0.5, 0.024)
    for x, col in ((B + 0.42, NAV_RED), (D - 0.42, NAV_GREEN)):
        v.dot(x, 0.86, 0.055, 52, NONE)
        v.dot(x, 0.86, 0.042, col)
        v.dot(x - 0.012, 0.848, 0.014, (255, 240, 230))


def roof(v):
    """The roof's fittings, front to back: the sensor block with its lens domes and hoses, the cabin hatch, a ribbed
    conduit, the raised plate between the engines with the tank fillers, a second conduit, the stepped plate with its
    vents, refuelling cap and access panel, and the rear hatch with an antenna post."""
    v.box(B + 0.3, 1.1, D - 0.3, 1.52, 214, HULL, lift=0.07)
    v.vent(B + 0.4, 1.18, B + 0.85, 1.44, 5)
    for x in (D - 0.72, D - 0.46):
        v.dot(x, 1.31, 0.1, 60, NONE)
        v.dot(x, 1.31, 0.085, 96, NONE)
        v.dot(x, 1.31, 0.066, LAMP_CYAN, NONE)
        v.dot(x - 0.022, 1.288, 0.02, (225, 250, 255), NONE)
    v.rect(C - 0.12, 1.2, C + 0.02, 1.42, 150, HULL)                        # a junction box
    v.line([(C - 0.09, 1.27), (C - 0.01, 1.27)], 80, 0.012)
    v.line([(C - 0.09, 1.34), (C - 0.01, 1.34)], 80, 0.012)
    for x in (B + 0.36, D - 0.36):
        for y in (1.15, 1.47):
            v.bolt(x, y, 0.02)
    for sx in (-1, 1):                                                      # hoses from the block to the engines
        v.cable([(C + sx * 0.7, 1.46), (C + sx * 0.78, 1.7), (C + sx * 0.76, 1.98)], 0.045)
        v.cable([(C + sx * 0.62, 1.5), (C + sx * 0.64, 1.8), (C + sx * 0.6, 2.0)], 0.03, 74)
    v.hatch(C - 0.5, 1.6, C + 0.5, 1.98, 208, HULL)                         # the cabin hatch

    def conduit(y0, y1):
        v.box(C - 0.2, y0, C + 0.2, y1, 190, HULL, lift=0.04, shade=0.35, bevel=0.018)
        for k in range(int((y1 - y0) / 0.075)):
            y = y0 + 0.04 + k * 0.075
            v.line([(C - 0.18, y), (C + 0.18, y)], 120, 0.014)
            v.line([(C - 0.18, y + 0.014), (C + 0.18, y + 0.014)], 230, 0.008)

    conduit(2.02, 2.66)
    plate = [(C - 0.34, 2.62), (C + 0.34, 2.62), (C + 0.56, 3.02), (C + 0.56, 3.34), (C + 0.34, 3.74), (C - 0.34, 3.74),
             (C - 0.56, 3.34), (C - 0.56, 3.02)]
    v.plate(plate, 212, HULL, lift=0.07)
    inner = [(C - 0.24, 2.8), (C + 0.24, 2.8), (C + 0.38, 3.06), (C + 0.38, 3.3), (C + 0.24, 3.56), (C - 0.24, 3.56),
             (C - 0.38, 3.3), (C - 0.38, 3.06)]
    v.line(inner + [inner[0]], 150, 0.014)
    v.line([(x + 0.012, y + 0.012) for x, y in inner + [inner[0]]], 238, 0.008)
    for x, y in ((C - 0.28, 2.72), (C + 0.28, 2.72), (C - 0.47, 3.18), (C + 0.47, 3.18), (C - 0.28, 3.64), (C + 0.28, 3.64)):
        v.bolt(x, y, 0.026)
    for x in (C - 0.16, C + 0.16):                                          # tank fillers
        v.dot(x, 3.18, 0.105, 70, None)
        v.dot(x, 3.18, 0.09, 162, HULL)
        v.dot(x - 0.02, 3.16, 0.06, 186, HULL)
        v.groove([(x - 0.06, 3.18), (x + 0.06, 3.18)], 150)
        v.groove([(x, 3.12), (x, 3.24)], 150)
    conduit(3.72, 4.06)

    step = [(C - 0.62, 4.02), (C + 0.62, 4.02), (C + 0.82, 4.36), (C + 0.82, 5.3), (C + 0.56, 5.6), (C - 0.56, 5.6),
            (C - 0.82, 5.3), (C - 0.82, 4.36)]
    v.plate(step, 210, HULL, lift=0.05, shade=0.36)
    v.vent(C - 0.34, 4.26, C + 0.34, 4.9, 6)
    for x in (C - 0.4, C + 0.4):
        for y in (4.22, 4.94):
            v.bolt(x, y, 0.02)
    for sx in (-1, 1):                                                      # narrow vents either side
        x = C + sx * 0.6
        v.vent(x - 0.1, 4.46, x + 0.1, 4.86, 4)
    hx = C - 0.32                                                           # the refuelling cap in a warning ring
    v.rect(hx - 0.19, 5.02, hx + 0.19, 5.4, 150, HULL)
    for k in range(12):
        a0, a1 = k * 30, k * 30 + 30
        v.d.pieslice([v.p(hx - 0.155, 5.21 - 0.155), v.p(hx + 0.155, 5.21 + 0.155)], a0, a1,
                     fill=((214, 176, 44) if k % 2 else (40, 40, 44)) + (255,))
    v.m.ellipse([v.p(hx - 0.155, 5.21 - 0.155), v.p(hx + 0.155, 5.21 + 0.155)], fill=NONE)
    v.dot(hx, 5.21, 0.112, 60, None)
    v.dot(hx, 5.21, 0.1, CAP)
    v.dot(hx - 0.035, 5.175, 0.035, (240, 215, 140))
    v.hatch(C + 0.12, 5.06, C + 0.52, 5.36, 190, HULL, hinges="e")          # a small access panel
    v.text(C + 0.32, 5.47, "FUEL", 0.085, colour=70)

    rear = [(C - 0.62, 5.78), (C + 0.62, 5.78), (C + 0.62, 6.4), (C + 0.38, 6.66), (C - 0.38, 6.66), (C - 0.62, 6.4)]
    v.plate(rear, 208, HULL, lift=0.03, shade=0.3, bevel=0.02)
    v.groove([(x * 0.93 + C * 0.07, 6.2 + (y - 6.2) * 0.9) for x, y in rear + [rear[0]]], 204)
    v.handle(C, 6.3)
    for hx in (C - 0.36, C + 0.36):                                         # its hinges at the front edge
        v.rect(hx - 0.07, 5.76, hx + 0.07, 5.82, 116, NONE, outline=False)
        v.line([(hx - 0.07, 5.765), (hx + 0.07, 5.765)], 214, 0.01)
    for x, y in ((C - 0.5, 5.9), (C + 0.5, 5.9), (C - 0.5, 6.34), (C + 0.5, 6.34), (C, 6.56)):
        v.bolt(x, y, 0.022)
    v.shadow([(C + 0.3, 5.96), (C + 0.36, 5.96), (C + 0.36, 6.02), (C + 0.3, 6.02)], 0.1, 0.1, 0.5)   # antenna post
    v.dot(C + 0.33, 5.99, 0.04, 70, None)
    v.dot(C + 0.33, 5.99, 0.024, 190, None)


def turbofan(v, nx):
    """One engine, centred on nx, nose to tail as in the photos: two brass intake rings, the duct, the machinery on a
    dark core (coil banks, a brass coil block, a piston each side), a ribbed neck, the armoured exhaust housing, and
    the heat-stained nozzle with its notched rim. The fan faces forward, so it isn't visible."""
    # Soot behind the exhaust, and the shadow on the wing and the roof.
    for k in range(6):
        v.shadow([(nx - 0.32 + k * 0.03, 5.0), (nx + 0.32 - k * 0.03, 5.0), (nx + 0.22, 5.9), (nx - 0.22, 5.9)],
                 0, 0, 0.03 - k * 0.004)
    v.shadow([(nx - 0.45, 2.0), (nx + 0.45, 2.0), (nx + 0.45, 5.0), (nx - 0.45, 5.0)], 0.16, 0.16, 0.42)
    # The nozzle: steel, then blue, then straw at the hot end, with a notched rim.
    v.cylinder(nx - 0.33, 4.72, nx + 0.33, 4.84, 104, NONE)
    v.cylinder(nx - 0.33, 4.82, nx + 0.33, 4.95, HEAT_BLUE, NONE, outline=False)
    v.cylinder(nx - 0.33, 4.94, nx + 0.33, 5.03, (126, 96, 122), NONE, outline=False)
    v.d.rectangle([v.p(nx - 0.33, 4.72), v.p(nx + 0.33, 5.03)], outline=OUTLINE + (255,), width=v.w(0.018))
    for k in range(-3, 4):
        x = nx + k * 0.09
        v.line([(x, 4.86), (x, 5.0)], (40, 44, 78), 0.01)
    for k in range(-3, 3):                                                  # the notches
        x = nx + (k + 0.5) * 0.105
        v.rect(x - 0.026, 4.985, x + 0.026, 5.035, 26, NONE, outline=False)
    # The armoured exhaust housing: two plates on top, a band, bolts.
    v.cylinder(nx - 0.41, 4.18, nx + 0.41, 4.76, 158, HULL)
    for x0 in (nx - 0.24, nx + 0.04):
        v.rect(x0, 4.27, x0 + 0.2, 4.56, 172, HULL)
        v.line([(x0, 4.27), (x0 + 0.2, 4.27)], 226, 0.01)
        v.bolt(x0 + 0.1, 4.415, 0.022)
    v.cylinder(nx - 0.41, 4.62, nx + 0.41, 4.69, 112, HULL, outline=False)
    v.rivets(nx - 0.34, 4.655, nx + 0.34, 4.655, 8)
    v.rivets(nx - 0.34, 4.23, nx + 0.34, 4.23, 8)
    # Ribbed neck with a clamp.
    v.cylinder(nx - 0.27, 3.66, nx + 0.27, 4.2, GUNMETAL, NONE)
    for k in range(9):
        y = 3.7 + k * 0.055
        v.cylinder(nx - 0.27, y, nx + 0.27, y + 0.022, 150, NONE, outline=False)
    v.cylinder(nx - 0.29, 3.9, nx + 0.29, 3.97, 72, NONE)
    v.bolt(nx + 0.12, 3.935, 0.024)
    # Dark core with the machinery on top.
    v.cylinder(nx - 0.31, 2.72, nx + 0.31, 3.68, 104, NONE)
    for sx in (-1, 1):                                                      # a piston each side
        px = nx + sx * 0.375
        v.cylinder(px - 0.05, 2.98, px + 0.05, 3.46, 176, NONE)
        v.rect(px - 0.06, 3.16, px + 0.06, 3.24, 84, NONE, outline=False)
        v.rect(px - 0.06, 2.96, px + 0.06, 3.02, 64, NONE, outline=False)
        v.rect(px - 0.06, 3.42, px + 0.06, 3.48, 64, NONE, outline=False)
    v.rect(nx - 0.15, 2.92, nx + 0.15, 3.5, 62, NONE)                       # the brass coil block
    for k in range(10):
        y = 2.96 + k * 0.053
        v.line([(nx - 0.13, y), (nx + 0.13, y)], BRASS_DARK if k % 2 else BRASS, 0.016)
    for sx in (-1, 1):                                                      # coil banks either side of it
        x0 = nx + sx * 0.235 - 0.045
        v.coil(x0, 2.92, x0 + 0.09, 3.5, 11)
    # Duct: rivet rows, an access plate, a sight glass.
    v.cylinder(nx - 0.45, 2.14, nx + 0.45, 2.74, 178, HULL)
    v.rivets(nx - 0.36, 2.25, nx + 0.36, 2.25, 7)
    v.rect(nx - 0.14, 2.36, nx + 0.14, 2.58, 190, HULL)
    v.line([(nx - 0.14, 2.36), (nx + 0.14, 2.36)], 238, 0.01)
    for x, y in ((nx - 0.1, 2.4), (nx + 0.1, 2.4), (nx - 0.1, 2.54), (nx + 0.1, 2.54)):
        v.bolt(x, y, 0.018)
    v.dot(nx + 0.29, 2.47, 0.04, 44, NONE)
    v.dot(nx + 0.29, 2.47, 0.028, (232, 168, 60), NONE)
    # The two brass intake rings, the widest part, bolted round.
    v.line([(nx - 0.5, 1.94), (nx + 0.5, 1.94)], 30, 0.02)
    v.cylinder(nx - 0.48, 2.05, nx + 0.48, 2.15, BRASS_DARK, NONE)
    v.cylinder(nx - 0.5, 1.95, nx + 0.5, 2.06, BRASS, NONE)
    for k in range(9):
        v.dot(nx - 0.4 + k * 0.1, 2.005, 0.016, (92, 68, 36), None)


def yoke(v, y, left, right, spine):
    """An arched crossbeam over an engine, reaching in to the raised plate: lit along its front edge, bolted at both
    ends, with a gusset where it meets the plate."""
    v.box(left, y, right, y + 0.17, 172, HULL, lift=0.06, shade=0.4, bevel=0.022)
    mid = (left + right) / 2
    v.line([(left + 0.05, y + 0.085), (right - 0.05, y + 0.085)], 150, 0.012)
    for x in (left + 0.06, mid, right - 0.06):
        v.bolt(x, y + 0.085, 0.026)
    gx = right if spine > 0 else left                                       # the gusset at the plate
    v.poly([(gx, y - 0.05), (gx - spine * 0.14, y), (gx - spine * 0.14, y + 0.17), (gx, y + 0.22)], 186, HULL)


def weather(img, mask, seed=7):
    """Wear, at the final size: grain and blotches in the paint, grime gathered round recesses, streaks running aft,
    bare metal chipped along edges, and a few rust runs. Chips and rust are unpainted, so they keep their colour under
    any paint. The same on every run."""
    import numpy as np

    rng = np.random.default_rng(seed)
    a = np.asarray(img).astype(np.float32)
    m = np.asarray(mask).copy()
    rgb, alpha = a[..., :3], a[..., 3]
    inside = alpha > 200
    h, w = inside.shape
    lum = rgb.mean(axis=2)
    painted = m.any(axis=2) & inside
    metal = inside & (np.abs(rgb[..., 0] - rgb[..., 2]) < 14)               # greys only: glass, lamps and brass stay clean

    def smooth(arr, radius):
        """A Gaussian blur, one axis at a time."""
        taps = max(1, int(radius * 3))
        kernel = np.exp(-0.5 * (np.arange(-taps, taps + 1) / radius) ** 2)
        kernel /= kernel.sum()
        out = arr.astype(np.float32)
        for axis in (0, 1):
            padded = np.pad(out, [(taps, taps) if ax == axis else (0, 0) for ax in (0, 1)], mode="edge")
            out = sum(k * np.take(padded, range(i, i + arr.shape[axis]), axis=axis) for i, k in enumerate(kernel))
        return out

    grain = rng.normal(0, 2.6, (h, w))
    coarse = rng.normal(0, 1, (h // 10 + 1, w // 10 + 1)).astype(np.float32)
    blotch = np.asarray(Image.fromarray(coarse, "F").resize((w, h), Image.BICUBIC)) * 5.0
    streak = np.zeros((h, w), np.float32)
    for _ in range(900):                                                    # streaks run aft (down the image)
        x, y0 = int(rng.integers(0, w)), int(rng.integers(0, h))
        length = int(rng.integers(14, 90))
        y1 = min(h, y0 + length)
        strength = float(rng.uniform(-11, 5))                               # mostly dark, a few light
        streak[y0:y1, x] += strength * np.linspace(1, 0, y1 - y0)
    streak = smooth(streak, 0.7)
    recess = smooth(((lum < 70) & inside).astype(np.float32), 2.0)          # grime round dark recesses
    shade = 1 - 0.1 * np.clip(recess * 1.4, 0, 1) * (lum > 110)
    delta = (grain + blotch + streak) * metal
    rgb = rgb * shade[..., None] + delta[..., None]

    edges = np.asarray(img.convert("L").filter(ImageFilter.FIND_EDGES)).astype(np.float32)
    edge = (edges > 60) & painted & (lum > 110)
    patches = smooth(rng.random((h, w)), 1.6)                               # chips come in small clusters
    chips = edge & (patches > np.quantile(patches[edge], 0.97))
    rgb[chips] = (188 + rng.normal(0, 10, int(chips.sum())))[:, None]
    m[chips] = 0

    ys, xs = np.nonzero(edge)
    rust = np.zeros((h, w), np.float32)
    for i in rng.choice(len(ys), size=min(44, len(ys)), replace=False):     # rust runs aft from seams and rivets
        x, y0 = int(xs[i]), int(ys[i])
        length = int(rng.integers(8, 30))
        y1 = min(h, y0 + length)
        rust[y0:y1, x] = np.maximum(rust[y0:y1, x], float(rng.uniform(0.45, 0.9)) * np.linspace(1, 0, y1 - y0))
    rust = np.clip(smooth(rust, 0.6) * 1.5, 0, 1) * painted
    rgb = rgb * (1 - rust[..., None]) + np.array([132, 78, 46], np.float32) * rust[..., None]
    m[rust > 0.5] = 0

    out = np.dstack([np.clip(rgb, 0, 255), alpha]).astype(np.uint8)
    return Image.fromarray(out, "RGBA"), Image.fromarray(m, "RGB")


def top():
    v = Canvas()
    # 1. Wings (the lowest surfaces).
    for side in (-1, 1):
        wing(v, side)
    # 2. Hull, 3. cockpit, 4. the roof's fittings.
    hull(v)
    cockpit(v)
    roof(v)
    # 5. Turbofans, half a cell in from their component cells (A3-A5 / D3-D5), over the wing and the roof's edge, with the
    #    two yokes across each engine and in to the raised plate.
    nacelles = (A + 1.0, D)
    for nx in nacelles:
        turbofan(v, nx)
    for y in (2.7, 3.5):
        yoke(v, y, nacelles[0] - 0.46, C - 0.3, 1)
        yoke(v, y, C + 0.3, nacelles[1] + 0.46, -1)
    # The raised plate's edge sits on top of the yokes where they meet it.
    v.poly([(C - 0.3, 2.66), (C + 0.3, 2.66), (C + 0.3, 2.74), (C - 0.3, 2.74)], 212, HULL, outline=False)
    v.poly([(C - 0.3, 3.6), (C + 0.3, 3.6), (C + 0.3, 3.7), (C - 0.3, 3.7)], 212, HULL, outline=False)
    return weather(*v.done())


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
