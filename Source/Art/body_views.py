"""The Hog seen from straight above, nose up: Body.png and its paint mask Body_m.png (red = hull and nacelles,
green = cockpit armour and the wing stripe, blue = wings). VTOL Vehicle turns this one picture to the aircraft's
heading, as the Hind's single top-down view.

What shows from above, and what doesn't:
- Only upward-facing surfaces. Vertical faces (the cockpit's sides, the rear door) don't show: row 7 is plain roof.
- The turbofans face forward, so from above each is a cylinder lying lengthwise: a long nacelle shaded across its
  width, the intake lip as a thin band at the front, the exhaust nozzle's rim at the back. The fan isn't visible.
- The cockpit windscreen slopes back, so it shows as a short, foreshortened band at the front of the cockpit roof.
- The skids are under the hull and the wings: hidden.
- Height comes from light (from the top left, north-west) and from shadows cast down and to the right onto
  whatever lies lower: the hull and the nacelles shade the wings.

Every feature sits inside the grid cells of its part (components.py, DESIGN.md): columns A-D port to starboard,
rows 1-7 nose to tail. The wings run one cell past the footprint on each side (art only, no hitbox), and split_wings() cuts those parts off
into their own texture, shown only while the engines run. The texture is square, drawSize (7,7), like the Hind's, so it
turns cleanly: the 6-cell span sits in the middle.
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


HULL_PTS = [(B - 0.15, 1.0), (D + 0.15, 1.0), (D + 0.15, 6.96), (B - 0.15, 6.96)]   # the four corner cells stay empty


def top():
    v = Canvas()

    # 1. Wings (the lowest surfaces): flat plates, a lit leading edge, a dark trailing edge. On top: panel lines,
    #    rivet rows, the green band with an emblem, a caged landing light near the root, a navigation light at
    #    the tip (red port, green starboard), and soot streaks behind the turbofan exhausts.
    for side in (-1, 1):
        pts, root, tip = wing_outline(side)
        v.poly(pts, 168, WING)
        v.line([pts[0], pts[1]], 212, 0.04)                                 # leading edge catches the light
        v.line([pts[3], pts[4]], 112, 0.035)                                # trailing edge
        for y in (2.95, 3.6, 4.25):
            v.groove([(root, y), (tip, y)], 168)
        mid = A if side < 0 else END                                        # a plate seam where the tip folds
        v.groove([(mid, 1.75), (mid, 5.9)], 168)
        for y in (2.75, 3.4, 4.05):                                         # rivet rows along the plate seams
            for k in (1, 2, 4, 5):                                          # k = 3 would sit on the cut (split_wings)
                v.rivet(root + (tip - root) * k / 6, y + 0.12)
        v.poly([(root, 4.62), (tip, 4.62), (tip, 5.02), (root, 5.02)], 186, ARMOUR, outline=False)
        v.line([(root, 4.62), (tip, 4.62)], 226, 0.012)
        v.line([(root, 5.02), (tip, 5.02)], 120, 0.012)
        ex, ey = mid - side * 0.3, 4.82                                     # emblem: an eight-point star outline, on the
        #                                                                     inner wing, so it shows while parked too
        star = [(ex + (0.16 if k % 2 == 0 else 0.07) * math.cos(k * math.pi / 8),
                 ey + (0.16 if k % 2 == 0 else 0.07) * math.sin(k * math.pi / 8)) for k in range(16)]
        v.d.polygon(v.pts(star), outline=(235, 235, 235, 255), width=v.w(0.016))
        # Caged landing light near the wing root's front (row 2): a dome, so it shows from above.
        lx, ly = root + side * 0.25, 1.62                                  # outboard of the hull, on the wing
        v.dot(lx, ly, 0.11, 70, NONE)
        v.dot(lx, ly, 0.085, LAMP_CYAN, NONE)
        v.dot(lx - 0.03, ly - 0.03, 0.03, (225, 250, 255), NONE)
        for a in (0, 60, 120):
            r = math.radians(a)
            v.line([(lx - 0.11 * math.cos(r), ly - 0.11 * math.sin(r)),
                    (lx + 0.11 * math.cos(r), ly + 0.11 * math.sin(r))], 60, 0.012)
        # Struts across the gap to the hull, at the two places the turbofan doesn't bridge it.
        for y in (1.68, 5.3):
            x0, x1 = (root - 0.03, root + WING_GAP + 0.03) if side < 0 else (root - WING_GAP - 0.03, root + 0.03)
            v.rect(x0, y, x1, y + 0.1, 92, NONE)
        # Navigation light at the tip.
        tx = tip - side * 0.14
        v.dot(tx, 5.12, 0.075, NAV_RED if side < 0 else NAV_GREEN)
        v.dot(tx - 0.02, 5.1, 0.025, (255, 240, 230))
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

    # 2. Hull (higher): its shadow falls down-right onto the starboard wing, then the hull itself.
    v.shadow(HULL_PTS, 0.16, 0.16)
    v.poly(HULL_PTS, 196, HULL)
    # Roof facets: flat top, lit west chamfer, shaded east chamfer, lit front edge.
    # One roof from row 2 to the tail (row 7 is ordinary roof; the rear door below it is a vertical face, so it
    # isn't visible from above).
    v.poly([(B + 0.12, 1.12), (D - 0.12, 1.12), (D - 0.12, 6.84), (B + 0.12, 6.84)], 204, HULL, outline=False)
    v.poly([(B - 0.15, 1.0), (B + 0.12, 1.12), (B + 0.12, 6.84), (B - 0.15, 6.96)], 226, HULL, outline=False)
    v.poly([(D + 0.15, 1.0), (D - 0.12, 1.12), (D - 0.12, 6.84), (D + 0.15, 6.96)], 150, HULL, outline=False)
    v.poly([(B - 0.15, 1.0), (D + 0.15, 1.0), (D - 0.12, 1.12), (B + 0.12, 1.12)], 232, HULL, outline=False)
    v.poly([(B - 0.15, 6.96), (D + 0.15, 6.96), (D - 0.12, 6.84), (B + 0.12, 6.84)], 140, HULL, outline=False)
    for y in (1.6, 2.6, 3.6, 4.6, 5.6, 6.6):
        v.rivet(B - 0.02, y)
        v.rivet(D + 0.02, y)

    # 3. Cockpit, B1-C1: a riveted armoured box, lower than the hull behind it. Roof with chamfers, the sloped
    #    windscreen foreshortened at the front (three panes), a roof hatch, small lamp domes at the rear corners.
    ck = [(B + 0.37, 0.04), (D - 0.37, 0.04), (D - 0.2, 0.25), (D - 0.2, 1.02), (B + 0.2, 1.02), (B + 0.2, 0.25)]
    v.poly(ck, 180, ARMOUR)
    v.poly([(B + 0.2, 0.25), (B + 0.33, 0.32), (B + 0.33, 1.02), (B + 0.2, 1.02)], 206, ARMOUR, outline=False)
    v.poly([(D - 0.2, 0.25), (D - 0.33, 0.32), (D - 0.33, 1.02), (D - 0.2, 1.02)], 140, ARMOUR, outline=False)
    v.poly([(B + 0.44, 0.1), (D - 0.44, 0.1), (D - 0.38, 0.42), (B + 0.38, 0.42)], GLASS, NONE)
    v.line([(B + 0.78, 0.1), (B + 0.74, 0.42)], OUTLINE, 0.03)             # windscreen frames: three panes
    v.line([(D - 0.78, 0.1), (D - 0.74, 0.42)], OUTLINE, 0.03)
    v.line([(B + 0.5, 0.17), (B + 0.7, 0.17)], GLASS_HI, 0.022)            # reflection
    v.line([(B + 0.2, 1.02), (D - 0.2, 1.02)], 110, 0.03)                    # step up to the hull roof
    v.rect(C - 0.25, 0.55, C + 0.25, 0.9, 168, ARMOUR)                      # roof escape hatch
    v.groove([(C - 0.25, 0.9), (C - 0.25, 0.55), (C + 0.25, 0.55)], 168)
    for k in range(9):
        v.rivet(B + 0.28 + 0.18 * k, 0.47)
    for x, col in ((B + 0.42, NAV_RED), (D - 0.42, NAV_GREEN)):
        v.dot(x, 0.88, 0.05, col)
        v.dot(x - 0.012, 0.868, 0.015, (255, 240, 230))

    # 4. Roof details.
    #    Row 2: a raised sensor housing just behind the cockpit (its roof, a dome sensor on top, its shadow), then
    #    the cabin hatch. Rows 3-4: the fuel tank bay (two filler plates). Row 5: vent grille. Row 6: the
    #    refuelling cap at the front of B6, roof vents behind it in B6 and C6. Rows 6-7: the dorsal fin on the
    #    centre line, seen edge-on from above.
    box = [(B + 0.3, 1.1), (D - 0.3, 1.1), (D - 0.3, 1.52), (B + 0.3, 1.52)]
    v.shadow(box, 0.07, 0.07, 0.4)
    v.poly(box, 214, HULL)
    v.line([(B + 0.3, 1.1), (D - 0.3, 1.1)], 240, 0.015)
    v.rect(B + 0.4, 1.18, B + 0.85, 1.44, GRILLE, NONE)
    v.dot(D - 0.55, 1.31, 0.1, 80, NONE)
    v.dot(D - 0.55, 1.31, 0.075, LAMP_RED, NONE)
    v.dot(D - 0.575, 1.285, 0.022, (255, 220, 210), NONE)
    v.groove([(B + 0.35, 1.95), (B + 0.35, 1.62), (D - 0.35, 1.62)], 204)   # cabin hatch
    v.line([(D - 0.35, 1.62), (D - 0.35, 1.95), (B + 0.35, 1.95)], 232, 0.012)
    v.rect(C - 0.12, 1.74, C + 0.12, 1.83, 140, HULL, outline=False)       # hatch handle
    for x0, x1 in ((B + 0.48, C - 0.06), (C + 0.06, D - 0.48)):           # tank bay: two filler plates
        v.groove([(x0, 3.85), (x0, 2.15), (x1, 2.15)], 204)
        v.line([(x1, 2.15), (x1, 3.85), (x0, 3.85)], 232, 0.012)
        for y in (2.25, 3.75):
            v.rivet(x0 + 0.08, y)
            v.rivet(x1 - 0.08, y)
        cx = (x0 + x1) / 2
        v.dot(cx, 3.0, 0.1, 150, HULL)
        v.groove([(cx - 0.07, 3.0), (cx + 0.07, 3.0)], 150)
    v.rect(B + 0.48, 4.15, D - 0.48, 4.85, GRILLE, NONE)
    for y in (4.25, 4.4, 4.55, 4.7):
        v.line([(B + 0.52, y), (D - 0.52, y)], 120, 0.02)
    hx = B + 0.45
    v.rect(hx - 0.22, 5.1, hx + 0.22, 5.46, 150, HULL)
    v.groove([(hx - 0.22, 5.46), (hx - 0.22, 5.1), (hx + 0.22, 5.1)], 150)
    v.dot(hx, 5.28, 0.12, CAP)
    v.dot(hx - 0.04, 5.24, 0.04, (240, 215, 140))
    for y in (5.58, 5.78):                                                  # roof vents, B6 and C6
        v.rect(B + 0.2, y, C - 0.18, y + 0.1, GRILLE, NONE)
        v.rect(C + 0.18, y, D - 0.2, y + 0.1, GRILLE, NONE)
    fin = [(C - 0.05, 5.1), (C + 0.05, 5.1), (C + 0.05, 6.9), (C - 0.05, 6.9)]
    v.shadow(fin, 0.22, 0.22, 0.45)
    v.poly(fin, 200, ARMOUR)
    v.line([(C - 0.05, 5.1), (C - 0.05, 6.9)], 236, 0.012)

    # 5. Turbofans, rows 3-5: cylinders lying lengthwise on the hull's shoulders, half a cell in from their component
    #    cells (A3-A5 / D3-D5), so each sits half on the wing and half on the roof. Soot behind the exhaust, then the
    #    shadow (onto the wing and the roof), then the nacelle: intake lip at the front, mounting straps, a fuel line
    #    along the top, the rib bands of the machinery housing, the exhaust rim at the back.
    for x0 in (A + 0.6, D - 0.4):
        x1 = x0 + 0.8
        nx = (x0 + x1) / 2
        for k in range(6):
            v.shadow([(nx - 0.32 + k * 0.03, 4.9), (nx + 0.32 - k * 0.03, 4.9), (nx + 0.22, 5.9), (nx - 0.22, 5.9)],
                     0, 0, 0.07 - k * 0.01)
        v.shadow([(x0, 2.1), (x1, 2.1), (x1, 4.9), (x0, 4.9)], 0.18, 0.18, 0.45)
        v.cylinder(x0, 2.2, x1, 4.78, 186, HULL)
        v.cylinder(x0 - 0.02, 2.08, x1 + 0.02, 2.24, BRASS, NONE)            # intake lip, the widest part
        v.line([(x0, 2.24), (x1, 2.24)], BRASS_DARK, 0.018)
        for y in (2.75, 3.25):                                              # mounting straps
            v.cylinder(x0, y, x1, y + 0.06, 120, HULL, outline=False)
        px = x0 + 0.28
        v.cylinder(px, 2.3, px + 0.07, 3.5, COPPER, NONE)                  # fuel line along the top
        for y in (3.55, 3.8, 4.05, 4.3, 4.55):                              # rib bands round the housing
            v.cylinder(x0, y, x1, y + 0.08, 150, HULL, outline=False)
            v.cylinder(x0, y, x1, y + 0.02, 215, HULL, outline=False)        # lit upper rim of each rib
        v.cylinder(x0 + 0.08, 4.78, x1 - 0.08, 4.9, HEAT, NONE)             # exhaust nozzle rim
    return v.done()


# The Hog's default paint (graphicData in Defs/VehicleDefs/HogShuttle.xml), per mask channel.
DEFAULT_PAINT = ((176, 178, 182), (86, 128, 98), (150, 152, 156))


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
GUN_BARREL_X = 0.085      # barrel centres either side of the centre line: touching, as twin-linked guns are
GUN_REACH = 1.48          # muzzle ahead of the pivot; the muzzles stop just short of the nose, over the windscreen


def twin_autocannon():
    """The roof-mounted twin autocannon from straight above, pointing north; the pivot is the image's centre.
    After VFE Security's double autocannon: one breech block, an ammo drum on each side, and two barrels bound
    together side by side. Each barrel is a cylinder lying lengthwise; straps across both show they are one gun.
    Own drawing, no pixels from that mod."""
    v = Canvas(GUN_CELLS)
    c = GUN_CELLS / 2
    # A low mounting ring on the roof, under everything.
    v.dot(c, c + 0.02, 0.37, 58, None)
    v.dot(c - 0.01, c + 0.01, 0.335, 92, None)
    # Ammo drums either side of the breech, lying lengthwise, with two bands each.
    for x0 in (c - 0.47, c + 0.25):
        v.cylinder(x0, c - 0.16, x0 + 0.22, c + 0.24, 112)
        for y in (c - 0.09, c + 0.11):
            v.cylinder(x0, y, x0 + 0.22, y + 0.05, (178, 176, 120), outline=False)
    # Two barrels, touching: a short, thick ribbed cooling jacket, then a bare tip section, then the muzzle brake.
    tip = c - GUN_REACH
    for sign in (-1, 1):
        x = c + sign * GUN_BARREL_X
        v.cylinder(x - 0.05, tip + 0.1, x + 0.05, c - 0.3, 104)
        v.cylinder(x - 0.075, c - 0.74, x + 0.075, c - 0.16, 88)
        for k in range(4):
            y = c - 0.7 + k * 0.125
            v.cylinder(x - 0.075, y, x + 0.075, y + 0.045, 132, outline=False)
        v.cylinder(x - 0.07, tip, x + 0.07, tip + 0.11, 76)
        v.dot(x, tip + 0.005, 0.03, 30, None)
    # Straps binding the barrels into one gun.
    for y in (c - 0.76, c - 0.32):
        v.rect(c - GUN_BARREL_X - 0.085, y, c + GUN_BARREL_X + 0.085, y + 0.05, 62)
        v.line([(c - GUN_BARREL_X - 0.08, y + 0.008), (c + GUN_BARREL_X + 0.08, y + 0.008)], 140, 0.01)
    # Breech block: flat top, lit west chamfer, shaded east chamfer, lit front, a feed cover and rivets.
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
