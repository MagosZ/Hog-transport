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

    def shadow(self, points, dx, dy, strength=0.42, blur=0.03):
        """A shadow cast down-right onto what is already drawn (never onto empty ground)."""
        shifted = self.pts([(x + dx, y + dy) for x, y in points])
        pad = self.w(max(0.12, blur * 4))
        x0 = max(0, min(p[0] for p in shifted) - pad)
        y0 = max(0, min(p[1] for p in shifted) - pad)
        x1 = min(self.img.width, max(p[0] for p in shifted) + pad)
        y1 = min(self.img.height, max(p[1] for p in shifted) + pad)
        if x1 <= x0 or y1 <= y0:
            return
        layer = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(layer).polygon([(px - x0, py - y0) for px, py in shifted], fill=round(255 * strength))
        layer = layer.filter(ImageFilter.GaussianBlur(self.w(blur)))
        region = self.img.crop((x0, y0, x1, y1))
        layer = Image.composite(layer, Image.new("L", layer.size, 0), region.getchannel("A"))
        black = Image.new("RGBA", layer.size, (0, 0, 0, 255))
        black.putalpha(layer)
        self.img.paste(Image.alpha_composite(region, black), (x0, y0))
        self.d = ImageDraw.Draw(self.img)

    def glow(self, x, y, r, colour, alpha=95):
        """A soft radial glow on the image only (never touches the paint mask)."""
        import numpy as np

        cx, cy = self.p(x, y)
        rad = max(4, self.w(r))
        pad = rad + max(4, self.w(r * 0.6))
        x0 = max(0, cx - pad)
        y0 = max(0, cy - pad)
        x1 = min(self.img.width, cx + pad)
        y1 = min(self.img.height, cy + pad)
        if x1 <= x0 or y1 <= y0:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1]
        dist = np.hypot(xx - cx, yy - cy) / max(1.0, float(rad))
        falloff = np.clip(1.0 - dist, 0.0, 1.0) ** 2.2
        col = self.rgb(colour)
        overlay = np.zeros((y1 - y0, x1 - x0, 4), dtype=np.uint8)
        overlay[..., 0] = col[0]
        overlay[..., 1] = col[1]
        overlay[..., 2] = col[2]
        overlay[..., 3] = np.clip(falloff * alpha, 0, 255).astype(np.uint8)
        region = self.img.crop((x0, y0, x1, y1))
        self.img.paste(Image.alpha_composite(region, Image.fromarray(overlay, "RGBA")), (x0, y0))
        self.d = ImageDraw.Draw(self.img)

    def shaded_poly(self, points, c_nw, c_se, mask=None, outline=True, outline_width=0.018):
        """Fill a polygon with a smooth NW-to-SE directional gradient for 3D volume."""
        import numpy as np

        px_pts = self.pts(points)
        xs = [p[0] for p in px_pts]
        ys = [p[1] for p in px_pts]
        x0 = max(0, min(xs) - 2)
        y0 = max(0, min(ys) - 2)
        x1 = min(self.img.width, max(xs) + 3)
        y1 = min(self.img.height, max(ys) + 3)
        if x1 <= x0 or y1 <= y0:
            return
        poly_mask = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(poly_mask).polygon([(px - x0, py - y0) for px, py in px_pts], fill=255)
        yy, xx = np.mgrid[0:(y1 - y0), 0:(x1 - x0)]
        t = ((xx / max(1, x1 - x0 - 1)) + (yy / max(1, y1 - y0 - 1))) * 0.5
        nw = np.array(self.rgb(c_nw), dtype=np.float32)
        se = np.array(self.rgb(c_se), dtype=np.float32)
        grad = (nw[None, None, :] * (1.0 - t[..., None]) + se[None, None, :] * t[..., None])
        arr = np.zeros((y1 - y0, x1 - x0, 4), dtype=np.uint8)
        arr[..., :3] = np.clip(grad, 0, 255).astype(np.uint8)
        arr[..., 3] = np.asarray(poly_mask)
        region = self.img.crop((x0, y0, x1, y1))
        self.img.paste(Image.alpha_composite(region, Image.fromarray(arr, "RGBA")), (x0, y0))
        self.d = ImageDraw.Draw(self.img)
        if outline:
            self.d.polygon(px_pts, outline=OUTLINE + (255,), width=self.w(outline_width))
        if mask is not None:
            self.m.polygon(px_pts, fill=mask)

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

    def plate(self, points, grey, mask=None, lift=0.05, shade=0.4, bevel=0.028, ao=0.22):
        """A raised plate: contact AO + cast shadow, shaded plate face, and bevelled edges lit from NW."""
        if lift:
            if ao:
                self.shadow(points, 0, 0, ao, blur=0.045)
            self.shadow(points, lift, lift, shade)
        base = self.rgb(grey)
        c_nw = tuple(min(255, c + 8) for c in base)
        c_se = tuple(max(0, c - 10) for c in base)
        self.shaded_poly(points, c_nw, c_se, mask, outline=False)
        area = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(points, points[1:] + points[:1]))
        sign = 1 if area > 0 else -1
        for p, q in zip(points, points[1:] + points[:1]):
            ex, ey = q[0] - p[0], q[1] - p[1]
            length = math.hypot(ex, ey) or 1
            nx, ny = sign * ey / length, -sign * ex / length                # outward normal
            light = -(nx + ny) * 0.707                                       # towards the top left
            col = tuple(max(0, min(255, round(c + 52 * light))) for c in base)
            inset = bevel / 2
            self.line([(p[0] - nx * inset, p[1] - ny * inset), (q[0] - nx * inset, q[1] - ny * inset)], col, bevel)
        self.d.polygon(self.pts(points), outline=OUTLINE + (255,), width=self.w(0.016))

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


WING_GAP = 0.46           # open gap between the hull side (2.34 / 4.66) and the wing inner edge (1.88 / 5.12)
WING_CORNER = 0.24        # small front-outer corner clip for the lamp pod


def wing_outline(side):
    """Port (-1) or starboard (+1) wing, filling the outer strip of A2-A7 / D2-D7 out to the canvas edge:
    - Front: inner edge starts at (0.00, 1.42) along x = 1.88 / 5.12 and angles in a triangle up to (u_band, 0.62)
      at the white line, then runs flat across the green band to (corner, 0.62) and bevels to (span, 0.86).
    - Back: flat across the grey wing (0.00..u_band) at y = 6.88, then angled diagonally from (u_band, 6.88)
      to (span, 6.20) across the green outer panel."""
    root, tip = (B - 0.16 - WING_GAP, 0.02) if side < 0 else (D + 0.16 + WING_GAP, SIZE - 0.02)
    span = abs(tip - root)
    corner = span - WING_CORNER
    u_band = span - 0.88

    front_profile = [
        (0.00, 1.42),
        (u_band, 0.62),
        (corner, 0.62),
        (span, 0.86),
    ]
    rear_profile = [
        (0.00, 6.88),
        (u_band, 6.88),
        (span, 6.20),
    ]

    def interp(profile, u):
        u = max(0.0, min(span, u))
        for (u0, y0), (u1, y1) in zip(profile, profile[1:]):
            if u <= u1 and u1 > u0:
                t = (u - u0) / (u1 - u0)
                return y0 + (y1 - y0) * t
        return profile[-1][1]

    def lead(x):
        return interp(front_profile, abs(x - root))

    def trail(x):
        return interp(rear_profile, abs(x - root))

    pts = (
        [(root + side * u, y) for u, y in front_profile]
        + [(root + side * u, y) for u, y in reversed(rear_profile)]
    )
    return pts, root, tip, lead, trail


TAIL = 6.96
# The four corner cells stay empty; the forward hull steps in to cradle the cockpit and the sides reach y = 6.88.
HULL_PTS = [
    (B + 0.16, 0.88), (D - 0.16, 0.88),
    (D + 0.16, 1.08), (D + 0.16, 6.88),
    (D - 0.08, TAIL), (B + 0.08, TAIL),
    (B - 0.16, 6.88), (B - 0.16, 1.08),
]


def wing(v, side):
    """One wing, the lowest surface: detached from the hull by WING_GAP with two thin struts, extended open front dent,
    full-length rear trailing edge meeting the tail of the body, raised inner root pad, inspection hatches, trailing-edge
    flap with hinge actuators, the wing-fold barrel hinge, downturned outer end-plate with white line, number, double
    rings and stencils, and a corner lamp housing."""
    pts, root, tip, lead, trail = wing_outline(side)
    span = abs(tip - root)
    corner = span - WING_CORNER
    u_fold = abs((A if side < 0 else END) - root)

    # Aft connecting strut across the detached wing gap between the hull side and the wing inner edge.
    for y in (5.85,):
        sx0, sx1 = (root - 0.02, root + WING_GAP + 0.04) if side < 0 else (root - WING_GAP - 0.04, root + 0.02)
        v.rect(sx0, y, sx1, y + 0.09, 96, NONE)
        v.line([(sx0, y + 0.012), (sx1, y + 0.012)], 174, 0.01)

    v.shaded_poly(pts, 176, 156, WING)

    def within(x, y, margin=0.05):
        return lead(x) + margin < y < trail(x) - margin

    def span_u(y, u_min=0.0, margin=0.05, flap_margin=0.33):
        """Return (u0, u1) distances from root along a horizontal line at y inside the wing and ahead of the flap."""
        steps = 160
        inside = []
        for k in range(steps + 1):
            u = u_min + (span - u_min) * k / steps
            x = root + side * u
            if lead(x) + margin < y < trail(x) - flap_margin:
                inside.append(u)
        return (inside[0], inside[-1]) if inside and inside[-1] > inside[0] + 0.04 else None

    seams = (0.92, 1.56, 2.20, 2.84, 3.48, 4.12, 4.76, 5.40, 6.00)
    for y in seams:
        rng = span_u(y)
        if rng:
            v.groove([(root + side * rng[0], y), (root + side * rng[1], y)], 166)
    fold = A if side < 0 else END                                           # a plate seam where the tip folds
    v.groove([(fold, lead(fold) + 0.04), (fold, trail(fold) - 0.04)], 166)
    for y in (0.68, 1.32, 1.96, 2.60, 3.24, 3.88, 4.52, 5.16, 5.80):        # rivet rows along the plate seams
        for k in (1, 2, 4, 5):
            x = root + (tip - root) * k / 6
            if within(x, y + 0.08, 0.10) and y + 0.08 < trail(x) - 0.34:
                v.rivet(x, y + 0.08)

    # The flap: a seam a little ahead of the trailing edge, with chordwise ribs and hinge knuckles along it.
    bx = tip - side * 0.88
    v.groove([(root, 6.88 - 0.30), (bx, 6.88 - 0.30), (tip, 6.20 - 0.30)], 162)
    for k in range(1, 15):
        fx = root + (tip - root) * k / 15
        fy = trail(fx)
        v.line([(fx, fy - 0.27), (fx, fy - 0.05)], 138, 0.01)
    for k in (0.12, 0.30, 0.50, 0.70, 0.88):
        hx = root + (tip - root) * k
        hy = trail(hx) - 0.3
        v.rect(hx - 0.048, hy - 0.032, hx + 0.048, hy + 0.042, 118, NONE, outline=False)
        v.line([(hx - 0.048, hy - 0.026), (hx + 0.048, hy - 0.026)], 216, 0.01)
    # Inspection plates on the outer grey strip between the hinge and the white line.
    sx = fold + side * 0.20
    for y in (2.92, 4.20, 5.48):
        v.hatch(min(sx, sx + side * 0.20), y, max(sx, sx + side * 0.20), y + 0.38, 176, WING, across=False, hinges="x")
    # The outer panel: the strip along the outer edge, which turns down, so it's lit on the port side and shaded on
    # the starboard. Green by default.
    p_corner_front = (root + side * corner, 0.62)
    p_tip_front = (tip, 0.86)
    p_tip_rear = (tip, 6.20)
    band = [(bx, lead(bx)), p_corner_front, p_tip_front, p_tip_rear, (bx, trail(bx))]
    v.shaded_poly(band, 206 if side < 0 else 178, 184 if side < 0 else 158, ARMOUR, outline=False)
    u_band = abs(bx - root)
    for y in seams:
        rng = span_u(y, u_min=u_band)
        if rng:
            v.groove([(root + side * rng[0], y), (root + side * rng[1], y)], 182)
    v.groove([(bx, 6.88 - 0.3), (tip, 6.20 - 0.3)], 182)

    def stencil(points, width=0.022):
        v.line(points, WHITE_LINE, width)
        v.m.line(v.pts(points), fill=NONE, width=v.w(width))

    stencil([(bx, lead(bx) + 0.02), (bx, trail(bx) - 0.02)], 0.045)         # the white line
    v.rivets(bx + side * 0.07, lead(bx) + 0.18, bx + side * 0.07, trail(bx) - 0.38, 19)
    ex = tip - side * 0.43
    for rx, ry in ((ex - side * 0.14, 1.12), (ex + side * 0.04, 1.32)):     # twin circular markings towards the front
        v.d.ellipse([v.p(rx - 0.075, ry - 0.075), v.p(rx + 0.075, ry + 0.075)],
                    outline=(44, 56, 48, 255), width=v.w(0.016))
        v.dot(rx, ry, 0.026, (44, 56, 48), None)
    v.text(ex, 2.86, "07", 0.28, angle=-90 * side)                          # the number reads from outboard
    for dx in (-0.09, 0, 0.09):                                             # stencil: three arrows, crossed
        stencil([(ex - dx, 3.46), (ex + dx, 3.90)])
    stencil([(ex - 0.1, 4.12), (ex - 0.02, 4.12)], 0.05)
    stencil([(ex + 0.02, 4.12), (ex + 0.1, 4.12)], 0.05)
    for y in (4.36, 4.45, 4.54):                                            # a block of stencilled lines
        stencil([(ex - 0.11, y), (ex + 0.11 - 0.045 * (y > 4.40), y)], 0.014)
    # Inset edge bevels inside the wing outline, then a crisp dark exterior outline around the whole wing.
    v.line([(pts[6][0] + side * 0.022, pts[6][1] - 0.02), (pts[0][0] + side * 0.022, pts[0][1] + 0.02)],
           136 if side < 0 else 214, 0.02)                                    # inner edge facing hull gap
    v.line([(pts[0][0], pts[0][1] + 0.024), (pts[1][0], pts[1][1] + 0.024)],
           176 if side < 0 else 228, 0.024)                                   # triangular tip slope
    v.line([(pts[1][0], pts[1][1] + 0.024), (pts[2][0], pts[2][1] + 0.024)],
           222, 0.026)
    v.line([(pts[2][0], pts[2][1] + 0.056), (pts[1][0], pts[1][1] + 0.056)], 132, 0.012)
    v.line([(pts[2][0], pts[2][1] + 0.022), (pts[3][0] - side * 0.02, pts[3][1] + 0.022)],
           232 if side < 0 else 178, 0.024)
    v.line([(pts[3][0] - side * 0.022, pts[3][1] + 0.02), (pts[4][0] - side * 0.022, pts[4][1] - 0.02)],
           140 if side > 0 else 204, 0.02)                                   # the outer edge
    v.line([(pts[4][0] - side * 0.015, pts[4][1] - 0.024), (pts[5][0], pts[5][1] - 0.024),
            (pts[6][0], pts[6][1] - 0.024)], 108, 0.026)                      # the trailing edge
    v.d.polygon(v.pts(pts), outline=OUTLINE + (255,), width=v.w(0.022))
    # Integrated armoured lamp housing tucked into the clipped front-outer wing corner.
    lx = (p_corner_front[0] + p_tip_front[0]) / 2 - side * 0.03
    ly = (p_corner_front[1] + p_tip_front[1]) / 2 + 0.04
    pod = [(lx + 0.145 * math.cos(math.radians(22.5 + 45 * k)), ly + 0.145 * math.sin(math.radians(22.5 + 45 * k)))
           for k in range(8)]
    v.plate(pod, 150, HULL, lift=0.035, shade=0.35, bevel=0.018)
    v.dot(lx, ly, 0.105, 44, NONE)
    v.dot(lx, ly, 0.092, 84, NONE)
    v.glow(lx, ly, 0.135, LAMP_CYAN, alpha=85)
    v.dot(lx, ly, 0.072, LAMP_CYAN, NONE)
    v.dot(lx - 0.024, ly - 0.024, 0.024, (225, 250, 255), NONE)
    for a in (0, 60, 120):
        r = math.radians(a)
        v.line([(lx - 0.095 * math.cos(r), ly - 0.095 * math.sin(r)),
                (lx + 0.095 * math.cos(r), ly + 0.095 * math.sin(r))], 60, 0.011)
    # The hinge the wing tip folds on, just inside the footprint's edge, so it stays with the parked body: a long
    # barrel lying lengthwise, cut into knuckles, with a riveted leaf on the wing side and latch brackets. Unpainted.
    hx = A if side < 0 else END - 0.1
    leaf = A + 0.1 if side < 0 else END - 0.17
    y0_hx = lead(fold - side * 0.10) + 0.06
    y0_leaf = lead(fold - side * 0.17) + 0.06
    y1 = 6.78
    v.shadow([(hx, y0_hx), (hx + 0.1, y0_hx), (hx + 0.1, y1), (hx, y1)], 0.03, 0.03, 0.35)
    v.rect(leaf, y0_leaf, leaf + 0.07, y1, 128, NONE, outline=False)
    for k in range(12):
        v.rivet(leaf + 0.035, y0_leaf + 0.16 + k * (y1 - y0_leaf - 0.32) / 11)
    v.cylinder(hx, y0_hx, hx + 0.1, y1, 138, NONE)
    for k in range(1, 17):
        y = y0_hx + k * (y1 - y0_hx) / 17
        v.line([(hx, y), (hx + 0.1, y)], 48, 0.012)
    for k in range(5):
        ly_lat = y0_leaf + 0.30 + k * (y1 - y0_leaf - 0.60) / 4
        bx0 = hx - 0.02 if side < 0 else leaf - 0.01
        bx1 = leaf + 0.08 if side < 0 else hx + 0.12
        v.rect(bx0, ly_lat - 0.035, bx1, ly_lat + 0.035, 108, NONE)
        v.line([(bx0 + 0.01, ly_lat - 0.022), (bx1 - 0.01, ly_lat - 0.022)], 188, 0.008)


def hull(v):
    """The hull, higher than the wings: its shadow, the roof with wide chamfered sides, a stepped forward glacis collar
    cradling the cockpit, external side buttress ribs, seams, rivet rows, the copper pipes on the shoulders, stiffener
    ribs and the door's hinge at the tail."""
    v.shadow(HULL_PTS, 0.07, 0.07)
    v.poly(HULL_PTS, 196, HULL)
    left, right = B + 0.14, D - 0.14
    v.shaded_poly([(left, 1.12), (right, 1.12), (right, 6.74), (D - 0.16, 6.90), (B + 0.16, 6.90), (left, 6.74)],
                  212, 194, HULL, outline=False)
    v.shaded_poly([(B - 0.16, 1.08), (left, 1.12), (left, 6.74), (B + 0.16, 6.90), (B + 0.08, TAIL), (B - 0.16, 6.88)],
                  234, 214, HULL, outline=False)
    v.shaded_poly([(D + 0.16, 1.08), (right, 1.12), (right, 6.74), (D - 0.16, 6.90), (D - 0.08, TAIL), (D + 0.16, 6.88)],
                  160, 140, HULL, outline=False)
    v.poly([(B + 0.16, 0.88), (D - 0.16, 0.88), (D + 0.16, 1.08), (right, 1.12), (left, 1.12), (B - 0.16, 1.08)],
           232, HULL, outline=False)
    v.poly([(B + 0.08, TAIL), (D - 0.08, TAIL), (D - 0.16, 6.90), (B + 0.16, 6.90)], 140, HULL, outline=False)
    v.line([(left, 1.12), (left, 6.74)], 176, 0.01)                          # the roof's edges
    v.line([(right, 1.12), (right, 6.74)], 120, 0.01)
    for y in (2.04, 4.0, 5.68):                                             # seams across the roof
        v.groove([(left, y), (right, y)], 204)
    for y in (1.56, 5.22, 5.92, 6.42):                                      # and across the chamfers
        v.line([(B - 0.16, y), (left, y)], 170, 0.012)
        v.line([(right, y), (D + 0.16, y)], 104, 0.012)
    # Recessed armoured side-bumper pads along the outer chamfer strips at rows 2 and 6.
    for x0, x1, g in ((B - 0.14, left - 0.04, 186), (right + 0.04, D + 0.14, 134)):
        for y0, y1 in ((1.62, 1.92), (5.32, 5.62)):
            v.rect(x0, y0, x1, y1, g, HULL)
            v.groove([(x0 + 0.025, y1 - 0.03), (x0 + 0.025, y0 + 0.03), (x1 - 0.025, y0 + 0.03)], g)
    # External armoured side buttress ribs along the rear hull chamfers behind the turbofans.
    for y in (5.06, 5.72, 6.24):
        v.box(B - 0.16, y, left - 0.02, y + 0.11, 206, HULL, lift=0.02, shade=0.28, bevel=0.014)
        v.box(right + 0.02, y, D + 0.16, y + 0.11, 148, HULL, lift=0.02, shade=0.28, bevel=0.014)
    v.rivets(left + 0.05, 1.24, left + 0.05, 6.5, 26)
    v.rivets(right - 0.05, 1.24, right - 0.05, 6.5, 26)
    v.rivets(B - 0.04, 1.2, B - 0.04, 6.6, 20)
    v.rivets(D + 0.04, 1.2, D + 0.04, 6.6, 20)
    # Copper pipes on the hull's shoulders, ahead of the engines, with socket rings, union nuts, and cast shadows.
    for x0, out in ((B - 0.14, -1), (D + 0.04, 1)):
        v.shadow([(x0, 1.16), (x0 + 0.1, 1.16), (x0 + 0.1, 1.96), (x0, 1.96)], 0.03, 0.03, 0.32)
        v.dot(x0 + 0.05 + out * 0.08, 1.2, 0.055, 52, NONE)
        v.cylinder(x0, 1.16, x0 + 0.1, 1.96, COPPER, NONE)
        v.line([(x0 + 0.05, 1.2), (x0 + 0.05 + out * 0.1, 1.2)], COPPER, 0.07)
        v.dot(x0 + 0.05, 1.2, 0.055, (150, 92, 52), None)
        v.rect(x0 - 0.01, 1.54, x0 + 0.11, 1.61, BRASS, NONE)
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
        v.glow(x, 6.72, 0.08, NAV_RED, 80)
        v.dot(x, 6.72, 0.045, 60, NONE)
        v.dot(x, 6.72, 0.034, NAV_RED, NONE)
    v.d.polygon(v.pts(HULL_PTS), outline=OUTLINE + (255,), width=v.w(0.018))


def cockpit(v):
    """The cockpit, B1-C1: a green armoured box narrower than the hull, with a grey lip under its nose and sensor pods
    against its sides. A thin front window, a larger sloped canopy in a thick frame with a centre bar, quarter windows on
    the chamfers, a roof hatch and two lamp domes."""
    left, right = B + 0.2, D - 0.2
    box = [(B + 0.37, 0.04), (D - 0.37, 0.04), (right, 0.25), (right, 1.02), (left, 1.02), (left, 0.25)]
    v.shadow(box, 0.06, 0.08, 0.42)
    v.rect(B + 0.42, 0.0, D - 0.42, 0.08, 150, HULL)                        # the lip under the nose
    v.rect(C - 0.1, 0.0, C + 0.1, 0.07, 70, NONE)
    for px0, px1, shade in ((B + 0.03, B + 0.22, 172), (D - 0.22, D - 0.03, 150)):
        cx = (px0 + px1) / 2                                                # sensor pods: a lens barrel points forward
        v.cylinder(cx - 0.055, 0.2, cx + 0.055, 0.36, 92, NONE)
        v.glow(cx, 0.2, 0.08, LAMP_CYAN, 70)
        v.line([(cx - 0.055, 0.2), (cx + 0.055, 0.2)], LAMP_CYAN, 0.022)
        v.box(px0, 0.34, px1, 0.82, shade, HULL, lift=0.03, shade=0.3, bevel=0.018)
        for y in (0.44, 0.58, 0.72):
            v.line([(px0 + 0.03, y), (px1 - 0.03, y)], 96, 0.016)
        v.bolt(cx, 0.775, 0.022)
    v.shaded_poly(box, 194, 168, ARMOUR)
    v.shaded_poly([(left, 0.25), (left + 0.13, 0.32), (left + 0.13, 1.02), (left, 1.02)], 212, 194, ARMOUR, outline=False)
    v.shaded_poly([(right, 0.25), (right - 0.13, 0.32), (right - 0.13, 1.02), (right, 1.02)], 148, 130, ARMOUR, outline=False)
    v.poly([(B + 0.37, 0.04), (left, 0.25), (left + 0.13, 0.32), (B + 0.47, 0.1)], 216, ARMOUR, outline=False)
    v.poly([(D - 0.37, 0.04), (right, 0.25), (right - 0.13, 0.32), (D - 0.47, 0.1)], 150, ARMOUR, outline=False)
    # Armoured brow plate above the front windscreen, and multi-layered canopy glass.
    v.poly([(B + 0.47, 0.06), (D - 0.47, 0.06), (D - 0.49, 0.095), (B + 0.49, 0.095)], 206, ARMOUR, outline=False)
    v.poly([(B + 0.5, 0.09), (D - 0.5, 0.09), (D - 0.45, 0.2), (B + 0.45, 0.2)], (32, 68, 96), NONE)
    v.shaded_poly([(B + 0.51, 0.105), (D - 0.51, 0.105), (D - 0.465, 0.185), (B + 0.465, 0.185)],
                  (78, 142, 184), (44, 92, 128), NONE, outline=False)
    canopy = [(B + 0.42, 0.28), (D - 0.42, 0.28), (D - 0.52, 0.64), (B + 0.52, 0.64)]
    v.poly(canopy, (32, 68, 96), NONE)
    v.shaded_poly([(B + 0.44, 0.3), (D - 0.44, 0.3), (D - 0.53, 0.62), (B + 0.53, 0.62)],
                  (78, 142, 184), (44, 94, 130), NONE, outline=False)
    v.line([(B + 0.54, 0.605), (D - 0.54, 0.605)], (120, 178, 206), 0.014)     # subtle dash reflection strip
    v.poly([(left + 0.035, 0.36), (left + 0.105, 0.39), (left + 0.105, 0.62), (left + 0.035, 0.62)], (74, 130, 168), NONE)
    v.poly([(right - 0.035, 0.36), (right - 0.105, 0.39), (right - 0.105, 0.62), (right - 0.035, 0.62)], (38, 80, 112), NONE)
    v.poly([(B + 0.44, 0.3), (D - 0.44, 0.3), (D - 0.48, 0.44), (B + 0.48, 0.44)], (92, 152, 188), None, outline=False)
    v.line([(B + 0.54, 0.335), (C - 0.11, 0.335)], GLASS_HI, 0.022)         # specular reflection bands
    v.line([(B + 0.52, 0.385), (C - 0.26, 0.385)], (124, 178, 210), 0.01)
    v.line([(C + 0.1, 0.34), (C + 0.3, 0.34)], GLASS_HI, 0.012)
    v.rect(left + 0.13, 0.28, B + 0.36, 0.64, 184, ARMOUR, outline=False)   # heavy armoured cheek frames
    v.rect(D - 0.36, 0.28, right - 0.13, 0.64, 152, ARMOUR, outline=False)
    v.line([(B + 0.2, 1.02), (D - 0.2, 1.02)], 110, 0.03)                   # step up to the hull roof
    v.hatch(C - 0.3, 0.73, C + 0.3, 0.95, 172, ARMOUR)                      # the roof hatch
    v.rivets(B + 0.48, 0.24, D - 0.48, 0.24, 8)
    v.rivets(C - 0.54, 0.68, C + 0.54, 0.68, 9)
    for x in (left + 0.2, right - 0.2):
        v.bolt(x, 0.5, 0.024)
    for x, col in ((B + 0.42, NAV_RED), (D - 0.42, NAV_GREEN)):
        v.glow(x, 0.86, 0.085, col, 85)
        v.dot(x, 0.86, 0.055, 52, NONE)
        v.dot(x, 0.86, 0.042, col)
        v.dot(x - 0.012, 0.848, 0.014, (255, 240, 230))
    v.d.polygon(v.pts(box), outline=OUTLINE + (255,), width=v.w(0.018))


def roof(v):
    """The roof's fittings, front to back: the sensor block with its lens domes and hoses, the cabin hatch, a ribbed
    conduit, a second conduit, the stepped plate with its vents, refuelling cap and access panel, and the rear hatch
    with an antenna post. (The central octagonal fuel plate is drawn by fuel_plate() over the engine yokes.)"""
    v.box(B + 0.3, 1.1, D - 0.3, 1.52, 214, HULL, lift=0.07)
    v.vent(B + 0.4, 1.18, B + 0.85, 1.44, 5)
    for x in (D - 0.72, D - 0.46):
        v.dot(x, 1.31, 0.11, 44, NONE)
        v.dot(x, 1.31, 0.095, 92, NONE)
        v.glow(x, 1.31, 0.11, LAMP_CYAN, 75)
        v.dot(x, 1.31, 0.068, LAMP_CYAN, NONE)
        v.dot(x - 0.022, 1.288, 0.02, (225, 250, 255), NONE)
    v.rect(C - 0.12, 1.2, C + 0.02, 1.42, 150, HULL)                        # a junction box
    v.line([(C - 0.09, 1.27), (C - 0.01, 1.27)], 80, 0.012)
    v.line([(C - 0.09, 1.34), (C - 0.01, 1.34)], 80, 0.012)
    for x in (B + 0.36, D - 0.36):
        for y in (1.15, 1.47):
            v.bolt(x, y, 0.02)
    for sx in (-1, 1):                                                      # hoses from the block to the engines
        h1 = [(C + sx * 0.7, 1.46), (C + sx * 0.78, 1.7), (C + sx * 0.76, 1.98)]
        h2 = [(C + sx * 0.62, 1.5), (C + sx * 0.64, 1.8), (C + sx * 0.6, 2.0)]
        v.shadow([(x, y) for x, y in h1] + [(x + 0.04, y) for x, y in reversed(h1)], 0.02, 0.02, 0.25, blur=0.015)
        v.cable(h1, 0.045)
        v.cable(h2, 0.03, 74)
    v.hatch(C - 0.5, 1.6, C + 0.5, 1.98, 208, HULL)                         # the cabin hatch

    def conduit(y0, y1):
        v.box(C - 0.2, y0, C + 0.2, y1, 190, HULL, lift=0.04, shade=0.35, bevel=0.018)
        for k in range(int((y1 - y0) / 0.075)):
            y = y0 + 0.04 + k * 0.075
            v.line([(C - 0.18, y), (C + 0.18, y)], 120, 0.014)
            v.line([(C - 0.18, y + 0.014), (C + 0.18, y + 0.014)], 230, 0.008)

    conduit(2.02, 2.66)
    conduit(3.72, 4.06)

    step = [(C - 0.48, 4.02), (C + 0.48, 4.02), (C + 0.58, 4.30), (C + 0.58, 5.34), (C + 0.48, 5.6), (C - 0.48, 5.6),
            (C - 0.58, 5.34), (C - 0.58, 4.30)]
    v.plate(step, 210, HULL, lift=0.05, shade=0.36)
    v.vent(C - 0.30, 4.26, C + 0.30, 4.9, 6)
    for x in (C - 0.35, C + 0.35):
        for y in (4.22, 4.94):
            v.bolt(x, y, 0.02)
    for sx in (-1, 1):                                                      # narrow vents either side
        x = C + sx * 0.45
        v.vent(x - 0.06, 4.46, x + 0.06, 4.86, 4)
    hx = C - 0.32                                                           # the refuelling cap in a warning ring
    v.rect(hx - 0.19, 5.02, hx + 0.19, 5.4, 150, HULL)
    for k in range(12):
        a0, a1 = k * 30, k * 30 + 30
        v.d.pieslice([v.p(hx - 0.155, 5.21 - 0.155), v.p(hx + 0.155, 5.21 + 0.155)], a0, a1,
                     fill=((214, 176, 44) if k % 2 else (40, 40, 44)) + (255,))
    v.m.ellipse([v.p(hx - 0.155, 5.21 - 0.155), v.p(hx + 0.155, 5.21 + 0.155)], fill=NONE)
    v.d.ellipse([v.p(hx - 0.155, 5.21 - 0.155), v.p(hx + 0.155, 5.21 + 0.155)], outline=OUTLINE + (255,), width=v.w(0.012))
    v.dot(hx, 5.21, 0.116, 48, NONE)
    v.dot(hx, 5.21, 0.104, 136, NONE)
    v.dot(hx, 5.21, 0.09, CAP, NONE)
    v.dot(hx - 0.03, 5.18, 0.03, (240, 215, 140), NONE)
    # Recessed pressure gauge dial beside the access panel.
    v.dot(C + 0.32, 4.98, 0.062, 54, NONE)
    v.dot(C + 0.32, 4.98, 0.048, 224, NONE)
    v.line([(C + 0.32, 4.98), (C + 0.348, 4.95)], (205, 60, 50), 0.01)
    v.dot(C + 0.32, 4.98, 0.012, 50, NONE)
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


def fuel_plate(v):
    """The raised eight-sided plate between the engines with the twin tank fillers, drawn over the yokes."""
    plate = [(C - 0.34, 2.62), (C + 0.34, 2.62), (C + 0.56, 3.02), (C + 0.56, 3.34), (C + 0.34, 3.74), (C - 0.34, 3.74),
             (C - 0.56, 3.34), (C - 0.56, 3.02)]
    v.plate(plate, 212, HULL, lift=0.07)
    inner = [(C - 0.24, 2.8), (C + 0.24, 2.8), (C + 0.38, 3.06), (C + 0.38, 3.3), (C + 0.24, 3.56), (C - 0.24, 3.56),
             (C - 0.38, 3.3), (C - 0.38, 3.06)]
    v.line(inner + [inner[0]], 150, 0.014)
    v.line([(x + 0.012, y + 0.012) for x, y in inner + [inner[0]]], 238, 0.008)
    for x, y in ((C - 0.28, 2.72), (C + 0.28, 2.72), (C - 0.47, 3.18), (C + 0.47, 3.18), (C - 0.28, 3.64), (C + 0.28, 3.64)):
        v.bolt(x, y, 0.026)
    for x in (C - 0.16, C + 0.16):                                          # tank fillers in recessed wells
        v.dot(x, 3.18, 0.125, 52, NONE)
        v.dot(x, 3.18, 0.105, 86, NONE)
        v.dot(x, 3.18, 0.088, 166, HULL)
        v.dot(x - 0.02, 3.16, 0.058, 192, HULL)
        v.groove([(x - 0.056, 3.18), (x + 0.056, 3.18)], 150)
        v.groove([(x, 3.124), (x, 3.236)], 150)
        for k in range(6):
            a = math.radians(k * 60)
            v.dot(x + 0.112 * math.cos(a), 3.18 + 0.112 * math.sin(a), 0.011, 210, None)


def turbofan(v, nx):
    """One engine, centred on nx, expanded by 20% widthwise, nose to tail: two brass intake rings, the duct, the
    machinery on a dark core (coil banks, a brass coil block, a piston each side), a ribbed neck, the armoured exhaust
    housing, and the heat-stained petal nozzle with its notched rim. The fan faces forward, so it isn't visible."""
    # Feathered soot plume behind the exhaust, and the engine shadow on the wing and roof.
    for k in range(8):
        v.shadow([(nx - 0.43 + k * 0.030, 5.01), (nx + 0.43 - k * 0.030, 5.01),
                  (nx + 0.31 - k * 0.018, 6.08 - k * 0.06), (nx - 0.31 + k * 0.018, 6.08 - k * 0.06)],
                 0, 0, 0.026 - k * 0.0028, blur=0.05)
    v.shadow([(nx - 0.49, 1.95), (nx + 0.49, 1.95), (nx + 0.49, 5.05), (nx - 0.49, 5.05)], 0.08, 0.12, 0.42)
    # Heat-stained petal nozzle: smooth 10-slice metallic heat-tint gradient, 6 overlapping petals, and notched rim.
    heat_stops = [
        (0.0, (112, 114, 120)),
        (0.28, (168, 138, 96)),
        (0.55, (132, 92, 138)),
        (0.82, (68, 82, 152)),
        (1.0, (42, 44, 52)),
    ]

    def heat_col(t):
        for (t0, c0), (t1, c1) in zip(heat_stops, heat_stops[1:]):
            if t <= t1:
                u = (t - t0) / max(1e-6, t1 - t0)
                return tuple(round(c0[i] + (c1[i] - c0[i]) * u) for i in range(3))
        return heat_stops[-1][1]

    slices = 10
    for s in range(slices):
        ya = 4.72 + (5.06 - 4.72) * s / slices
        yb = 4.72 + (5.06 - 4.72) * (s + 1) / slices
        v.cylinder(nx - 0.372, ya, nx + 0.372, yb, heat_col((s + 0.5) / slices), NONE, outline=False)
    for k in range(6):
        px0 = nx - 0.372 + k * (0.744 / 6)
        px1 = px0 + (0.744 / 6)
        pmid = (px0 + px1) / 2
        v.line([(pmid - 0.018, 4.76), (pmid - 0.018, 5.02)], (160, 156, 178), 0.014)
        if k > 0:
            v.line([(px0, 4.74), (px0, 5.05)], (28, 30, 44), 0.014)
        v.rect(pmid - 0.026, 5.01, pmid + 0.026, 5.07, 24, NONE, outline=False)
    v.d.rectangle([v.p(nx - 0.372, 4.72), v.p(nx + 0.372, 5.06)], outline=OUTLINE + (255,), width=v.w(0.018))
    # The armoured exhaust housing: inspection plates, recessed cooling louvres, a band, and bolts.
    v.cylinder(nx - 0.468, 4.18, nx + 0.468, 4.76, 158, HULL)
    v.shadow([(nx - 0.456, 4.18), (nx + 0.456, 4.18), (nx + 0.456, 4.24), (nx - 0.456, 4.24)], 0, 0.01, 0.28, blur=0.018)
    for x0 in (nx - 0.264, nx + 0.048):
        v.rect(x0, 4.27, x0 + 0.216, 4.56, 172, HULL)
        v.line([(x0, 4.27), (x0 + 0.216, 4.27)], 226, 0.01)
        v.bolt(x0 + 0.108, 4.415, 0.024)
    for sx in (-1, 1):
        lx0 = nx + sx * 0.348 - 0.048
        for ky in range(4):
            y = 4.31 + ky * 0.06
            v.line([(lx0, y), (lx0 + 0.096, y)], 48, 0.014)
            v.line([(lx0, y + 0.013), (lx0 + 0.096, y + 0.013)], 200, 0.007)
    v.cylinder(nx - 0.468, 4.62, nx + 0.468, 4.69, 112, HULL, outline=False)
    v.rivets(nx - 0.396, 4.655, nx + 0.396, 4.655, 9)
    v.rivets(nx - 0.396, 4.23, nx + 0.396, 4.23, 9)
    # Ribbed neck with a clamp.
    v.cylinder(nx - 0.324, 3.66, nx + 0.324, 4.2, GUNMETAL, NONE)
    for k in range(9):
        y = 3.7 + k * 0.055
        v.cylinder(nx - 0.324, y, nx + 0.324, y + 0.022, 150, NONE, outline=False)
    v.cylinder(nx - 0.348, 3.9, nx + 0.348, 3.97, 72, NONE)
    v.bolt(nx + 0.144, 3.935, 0.026)
    # Dark core bay with interior overhang shadows and 3D brass coil block.
    v.cylinder(nx - 0.372, 2.72, nx + 0.372, 3.68, 104, NONE)
    v.shadow([(nx - 0.36, 2.72), (nx + 0.36, 2.72), (nx + 0.36, 2.84), (nx - 0.36, 2.84)], 0, 0, 0.38, blur=0.02)
    v.shadow([(nx - 0.36, 3.52), (nx + 0.36, 3.52), (nx + 0.36, 3.68), (nx - 0.36, 3.68)], 0, 0, 0.32, blur=0.02)
    for sx in (-1, 1):                                                      # a piston each side
        px = nx + sx * 0.426
        v.cylinder(px - 0.06, 2.98, px + 0.06, 3.46, 176, NONE)
        v.rect(px - 0.072, 3.16, px + 0.072, 3.24, 84, NONE, outline=False)
        v.rect(px - 0.072, 2.96, px + 0.072, 3.02, 64, NONE, outline=False)
        v.rect(px - 0.072, 3.42, px + 0.072, 3.48, 64, NONE, outline=False)
    v.cylinder(nx - 0.18, 2.90, nx + 0.18, 3.52, 56, NONE)                  # 3D shaded brass coil block
    for k in range(12):
        y = 2.94 + k * 0.049
        v.cylinder(nx - 0.162, y, nx + 0.162, y + 0.024, BRASS if k % 2 == 0 else BRASS_DARK, NONE, outline=False)
    for sx in (-1, 1):                                                      # longitudinal busbars & coil banks
        v.rect(nx + sx * 0.18 - 0.022, 2.9, nx + sx * 0.18 + 0.022, 3.52, 134, NONE)
        x0 = nx + sx * 0.282 - 0.054
        v.coil(x0, 2.92, x0 + 0.108, 3.5, 11)
    # Duct: cast shadow from rear intake ring, longitudinal cowling seams & bolts, access plate, and glowing sight glass.
    v.cylinder(nx - 0.492, 2.12, nx + 0.492, 2.74, 178, HULL)
    v.shadow([(nx - 0.492, 2.12), (nx + 0.492, 2.12), (nx + 0.492, 2.18), (nx - 0.492, 2.18)], 0, 0, 0.34, blur=0.015)
    for sx in (-1, 1):
        v.groove([(nx + sx * 0.264, 2.14), (nx + sx * 0.264, 2.72)], 178)
        v.rivets(nx + sx * 0.384, 2.24, nx + sx * 0.384, 2.66, 4)
    v.rivets(nx - 0.396, 2.23, nx + 0.396, 2.23, 8)
    v.rect(nx - 0.156, 2.36, nx + 0.156, 2.58, 190, HULL)
    v.line([(nx - 0.156, 2.36), (nx + 0.156, 2.36)], 238, 0.01)
    for x, y in ((nx - 0.108, 2.4), (nx + 0.108, 2.4), (nx - 0.108, 2.54), (nx + 0.108, 2.54)):
        v.bolt(x, y, 0.020)
    v.dot(nx + 0.324, 2.47, 0.053, 40, NONE)
    v.glow(nx + 0.324, 2.47, 0.069, (240, 175, 65), alpha=75)
    v.dot(nx + 0.324, 2.47, 0.035, (240, 175, 65), NONE)
    v.dot(nx + 0.312, 2.458, 0.014, (255, 235, 170), NONE)
    # Recessed dark intake throat lip and the two brass intake rings, bolted round.
    v.cylinder(nx - 0.504, 1.88, nx + 0.504, 1.94, 32, NONE)
    v.cylinder(nx - 0.516, 2.03, nx + 0.516, 2.13, BRASS_DARK, NONE)
    v.cylinder(nx - 0.528, 1.93, nx + 0.528, 2.04, BRASS, NONE)
    for k in range(10):
        v.dot(nx - 0.432 + k * 0.096, 1.985, 0.017, (92, 68, 36), None)


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
    """Wear, at the final size: grain and blotches in the paint, ambient occlusion & grime round recesses, streaks running aft,
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
    dark_lines = ((lum < 65) & inside).astype(np.float32)
    recess_tight = smooth(dark_lines, 1.5)
    recess_broad = smooth(dark_lines, 4.5)
    ao = np.clip(recess_tight * 1.1 + recess_broad * 0.75, 0, 1)
    shade = (1.0 - 0.12 * ao * (lum > 100)) + 0.03 * (1.0 - np.clip(recess_broad * 1.8, 0, 1)) * (lum > 140) * metal
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
    # 5. Turbofans, moved 0.2 cells inside so their outer edges meet the filled wing strip at x = 1.88 / 5.12.
    nacelles = (A + 0.91, END - 0.91)
    for nx in nacelles:
        turbofan(v, nx)
    for y in (2.7, 3.5):
        yoke(v, y, nacelles[0] - 0.55, C - 0.3, 1)
        yoke(v, y, C + 0.3, nacelles[1] + 0.55, -1)
    fuel_plate(v)
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
    ring, being round, looks fixed to the roof while the head and barrel swing. One barrel: a recoil recuperator,
    a slotted cooling jacket, a fluted mid-barrel and a double-baffle muzzle brake. One ammo drum on the port side
    with a feed chute."""
    v = Canvas(GUN_CELLS)
    c = GUN_CELLS / 2
    # A bolted turret ring base on the roof, under everything.
    v.dot(c, c, 0.38, 42, None)
    v.dot(c, c, 0.35, 102, None)
    v.dot(c, c, 0.27, 56, None)
    for k in range(12):
        a = math.radians(k * 30)
        v.dot(c + 0.315 * math.cos(a), c + 0.315 * math.sin(a), 0.015, 178, None)
    # Cast shadow from the head and ammo drum onto the mounting ring.
    block = [(c - 0.17, c - 0.26), (c + 0.17, c - 0.26), (c + 0.26, c - 0.14), (c + 0.26, c + 0.3),
             (c - 0.26, c + 0.3), (c - 0.26, c - 0.14)]
    v.shadow(block, 0.045, 0.045, 0.45, blur=0.02)
    v.shadow([(c - 0.49, c - 0.16), (c - 0.27, c - 0.16), (c - 0.27, c + 0.24), (c - 0.49, c + 0.24)],
             0.04, 0.04, 0.4, blur=0.02)
    # Ammo drum beside the breech, lying lengthwise, with a feed-chute neck, end-cap rims and ammo-belt bands.
    x0 = c - 0.49
    v.rect(c - 0.32, c - 0.08, c - 0.22, c + 0.14, 72)
    v.line([(c - 0.31, c - 0.04), (c - 0.23, c - 0.04)], (178, 176, 120), 0.02)
    v.line([(c - 0.31, c + 0.02), (c - 0.23, c + 0.02)], (178, 176, 120), 0.02)
    v.line([(c - 0.31, c + 0.08), (c - 0.23, c + 0.08)], (178, 176, 120), 0.02)
    v.cylinder(x0, c - 0.16, x0 + 0.22, c + 0.24, 114)
    v.cylinder(x0 - 0.01, c - 0.18, x0 + 0.23, c - 0.14, 72)
    v.cylinder(x0 - 0.01, c + 0.22, x0 + 0.23, c + 0.26, 72)
    for y in (c - 0.09, c + 0.11):
        v.cylinder(x0, y, x0 + 0.22, y + 0.05, (186, 176, 110), outline=False)
    # The barrel: fluted mid-barrel, slotted cooling jacket, recoil recuperator housing, and double-baffle muzzle brake.
    tip = c - GUN_REACH
    v.cylinder(c - 0.058, tip + 0.13, c + 0.058, c - 0.3, 108)
    for fx in (c - 0.022, c + 0.022):                                       # fluted barrel ribs
        v.line([(fx, tip + 0.16), (fx, c - 0.78)], 56, 0.012)
    v.cylinder(c - 0.092, c - 0.74, c + 0.092, c - 0.18, 90)                # cooling jacket
    for k in range(5):
        y = c - 0.69 + k * 0.102
        v.cylinder(c - 0.092, y, c + 0.092, y + 0.036, 134, outline=False)
        v.dot(c - 0.042, y + 0.055, 0.016, 36, None)
        v.dot(c + 0.042, y + 0.055, 0.016, 36, None)
    v.cylinder(c - 0.11, c - 0.34, c + 0.11, c - 0.18, 76)                  # recoil recuperator housing
    v.line([(c - 0.11, c - 0.34), (c + 0.11, c - 0.34)], 150, 0.01)
    v.cylinder(c - 0.09, tip, c + 0.09, tip + 0.13, 82)                     # double-baffle muzzle brake
    for y_baffle in (tip + 0.035, tip + 0.082):
        v.rect(c - 0.1, y_baffle, c - 0.06, y_baffle + 0.024, 30, NONE, outline=False)
        v.rect(c + 0.06, y_baffle, c + 0.1, y_baffle + 0.024, 30, NONE, outline=False)
    v.line([(c - 0.088, tip + 0.006), (c + 0.088, tip + 0.006)], 140, 0.008)
    v.dot(c, tip + 0.008, 0.035, 26, None)
    for y in (c - 0.76, c - 0.36):
        v.rect(c - 0.108, y, c + 0.108, y + 0.045, 62)
        v.line([(c - 0.1, y + 0.008), (c + 0.1, y + 0.008)], 146, 0.01)
    # Head: flat top with NW shading, lit west chamfer, shaded east chamfer, lit front, a feed cover and bolts.
    v.shaded_poly(block, 98, 74)
    v.poly([(c - 0.26, c - 0.14), (c - 0.19, c - 0.1), (c - 0.19, c + 0.23), (c - 0.26, c + 0.3)], 130, outline=False)
    v.poly([(c + 0.26, c - 0.14), (c + 0.19, c - 0.1), (c + 0.19, c + 0.23), (c + 0.26, c + 0.3)], 54, outline=False)
    v.poly([(c - 0.17, c - 0.26), (c + 0.17, c - 0.26), (c + 0.19, c - 0.1), (c - 0.19, c - 0.1)], 122, outline=False)
    v.rect(c - 0.13, c - 0.04, c + 0.13, c + 0.16, 72)
    v.groove([(c - 0.13, c + 0.16), (c - 0.13, c - 0.04), (c + 0.13, c - 0.04)], 72)
    v.rect(c - 0.05, c + 0.03, c + 0.05, c + 0.08, 128, outline=False)
    for x, y in ((-0.15, 0.23), (0.15, 0.23), (-0.15, -0.09), (0.15, -0.09)):
        v.bolt(c + x, c + y, 0.022)
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
