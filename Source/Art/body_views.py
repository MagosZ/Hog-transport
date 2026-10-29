"""The Hog's three views, VVE-style (Graphic_Vehicle): Body_north, Body_south and Body_east (west mirrors east), each
with a paint mask (Body_northm ...: red = hull, green = cockpit armour and the wing stripe, blue = wings). Painted
areas are drawn in greys so the vehicle's colours tint them; glass, copper fans, lights and dark machinery keep
their own colours.

Every feature sits inside the grid cells of the part it shows (components.py, DESIGN.md): columns A-D port to
starboard, rows 1-7 nose to tail. The wings also run one cell past the footprint on each side (art only, no
hitbox), so the views are 6 cells wide: drawSize (6,7).
"""
import math

from PIL import Image, ImageDraw

PX = 128                  # pixels per cell, as VVE's vehicles
SS = 2                    # supersampling, for smooth edges
W, L = 6, 7               # drawSize: footprint 4x7 plus a wing cell each side
FOOT_X = 1.0              # the footprint's port edge in the north view (columns A-D = x 1-5)

OUTLINE = (34, 34, 38)
GLASS = (70, 140, 190)
GLASS_HI = (170, 215, 240)
COPPER = (178, 118, 66)
COPPER_DARK = (110, 70, 40)
METAL = (92, 94, 100)
METAL_DARK = (58, 60, 64)
LIGHT = (255, 186, 80)
CAP = (205, 165, 60)

HULL, ARMOUR, WING = (255, 0, 0), (0, 255, 0), (0, 0, 255)   # mask channels


class View:
    """One view: the picture and its mask, drawn in cell units."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w * PX * SS, h * PX * SS), (0, 0, 0, 0))
        self.mask = Image.new("RGB", (w * PX * SS, h * PX * SS), (0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.m = ImageDraw.Draw(self.mask)
        self.under = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        self.u = ImageDraw.Draw(self.under)

    def p(self, x, y):
        return round(x * PX * SS), round(y * PX * SS)

    def pts(self, points):
        return [self.p(x, y) for x, y in points]

    def width(self, cells_):
        return max(1, round(cells_ * PX * SS))

    def plate(self, points, grey, mask=None, bevel=0.05):
        """A flat facet with a lit edge facing up/left and a shaded edge facing down/right."""
        self.d.polygon(self.pts(points), fill=(grey, grey, grey, 255))
        n = len(points)
        cx = sum(x for x, _ in points) / n
        cy = sum(y for _, y in points) / n
        for i in range(n):
            (x0, y0), (x1, y1) = points[i], points[(i + 1) % n]
            mx, my = (x0 + x1) / 2 - cx, (y0 + y1) / 2 - cy      # outward-ish direction of this edge
            lit = (-mx - my) > 0
            g = min(255, grey + 45) if lit else max(0, grey - 55)
            inset = [(x0 + (cx - x0) * bevel, y0 + (cy - y0) * bevel), (x1 + (cx - x1) * bevel, y1 + (cy - y1) * bevel)]
            self.d.line(self.pts(inset), fill=(g, g, g, 255), width=self.width(0.035))
        self.d.polygon(self.pts(points), outline=OUTLINE + (255,), width=self.width(0.022))
        if mask:
            self.m.polygon(self.pts(points), fill=mask)

    def fill(self, points, colour, mask=None, outline=True):
        self.d.polygon(self.pts(points), fill=colour + (255,),
                       outline=(OUTLINE + (255,)) if outline else None, width=self.width(0.02))
        if mask:
            self.m.polygon(self.pts(points), fill=mask)
        elif mask is None:
            self.m.polygon(self.pts(points), fill=(0, 0, 0))     # unpainted: keeps its own colour

    def ellipse(self, x0, y0, x1, y1, colour, outline=True, mask=None, width=0.025):
        self.d.ellipse([self.p(x0, y0), self.p(x1, y1)], fill=colour + (255,),
                       outline=(OUTLINE + (255,)) if outline else None, width=self.width(width))
        self.m.ellipse([self.p(x0, y0), self.p(x1, y1)], fill=mask or (0, 0, 0))

    def line(self, points, colour, w=0.02):
        self.d.line(self.pts(points), fill=colour + (255,), width=self.width(w))

    def rivets(self, points, r=0.025):
        for x, y in points:
            self.d.ellipse([self.p(x - r, y - r), self.p(x + r, y + r)], fill=(90, 90, 96, 255))

    def done(self):
        """Skids show faintly through the body; downsample to the shipped size."""
        faint = self.under.copy()
        faint.putalpha(self.under.getchannel("A").point(lambda a: 120 if a else 0))
        img = Image.alpha_composite(self.img, faint)
        size = (self.w * PX, self.h * PX)
        return img.resize(size, Image.LANCZOS), self.mask.resize(size, Image.NEAREST)


def north():
    """Top-down, nose up."""
    v = View(W, L)
    a, b, c, d = FOOT_X, FOOT_X + 1, FOOT_X + 2, FOOT_X + 3      # left edges of columns A-D
    right = FOOT_X + 4

    # Skids, underneath: front skid B2-C2 (crossbar and two runners), rear skids A4-A5 / D4-D5.
    skid = (20, 20, 24, 255)
    for x in (b + 0.15, c + 0.65):
        v.u.rectangle([v.p(x, 1.12), v.p(x + 0.2, 1.88)], fill=skid)
    v.u.rectangle([v.p(b + 0.15, 1.42), v.p(c + 0.85, 1.58)], fill=skid)
    for x in (a + 0.4, d + 0.4):
        v.u.rectangle([v.p(x, 3.08), v.p(x + 0.2, 4.92)], fill=skid)

    # Wings: rows 2-6 of columns A / D, and one cell further out (art only). Swept leading edge, angled tip.
    for root, tip, out in ((b - 0.12, 0.08, -1), (d + 0.12, W - 0.08, 1)):
        wing = [(root, 1.12), (tip, 2.35), (tip, 5.2), (tip - out * 0.45, 5.95), (root, 5.95)]
        v.plate(wing, 168, WING)
        # Green stripe near the trailing edge, as on the kit.
        stripe = [(root, 4.72), (tip, 4.72), (tip, 4.98), (root, 4.98)]
        v.plate(stripe, 190, ARMOUR, bevel=0.02)
        for y in (2.9, 3.6, 4.3):
            v.line([(root, y), (tip, y + 0.02)], (128, 128, 128), 0.012)
        lx = tip - out * 0.2
        v.ellipse(lx - 0.07, 5.08, lx + 0.07, 5.22, LIGHT, outline=False)

    # Hull: body over columns B-C (a little wider), the rear section full width (row 7).
    hull = [(b + 0.05, 0.95), (d - 0.05, 0.95), (d + 0.15, 1.2), (d + 0.15, 6.0), (right - 0.05, 6.05),
            (right - 0.05, 6.95), (a + 0.05, 6.95), (a + 0.05, 6.05), (b - 0.15, 6.0), (b - 0.15, 1.2)]
    v.plate(hull, 196, HULL)
    # Facets: a raised spine down the middle, sloping sides.
    v.plate([(b + 0.4, 1.05), (d - 0.4, 1.05), (d - 0.4, 5.95), (b + 0.4, 5.95)], 214, HULL, bevel=0.01)
    for x in (b - 0.1, d - 0.35):
        v.plate([(x, 1.25), (x + 0.45, 1.1), (x + 0.45, 5.95), (x, 5.95)], 172, HULL, bevel=0.01)
    v.rivets([(b - 0.05, y) for y in (1.5, 2.5, 3.5, 4.5, 5.5)] + [(d + 0.05, y) for y in (1.5, 2.5, 3.5, 4.5, 5.5)])

    # Cockpit B1-C1: faceted armoured box (green), canopy glass at the front.
    v.plate([(b + 0.25, 0.04), (d - 0.25, 0.04), (d - 0.04, 0.3), (d - 0.04, 1.0), (b + 0.04, 1.0), (b + 0.04, 0.3)],
            186, ARMOUR)
    v.fill([(b + 0.35, 0.14), (d - 0.35, 0.14), (d - 0.18, 0.34), (d - 0.18, 0.6), (b + 0.18, 0.6), (b + 0.18, 0.34)],
           GLASS)
    v.line([(b + 0.45, 0.22), (b + 0.85, 0.22)], GLASS_HI, 0.03)
    v.line([(c, 0.14), (c, 0.6)], OUTLINE, 0.02)

    # Roof: cabin hatch B2-C2, fuel tank bay B3-C4, pump and servo grille B5-C5.
    v.plate([(b + 0.3, 1.25), (d - 0.3, 1.25), (d - 0.3, 1.8), (b + 0.3, 1.8)], 205, HULL, bevel=0.03)
    v.plate([(b + 0.2, 2.15), (d - 0.2, 2.15), (d - 0.2, 3.85), (b + 0.2, 3.85)], 205, HULL, bevel=0.02)
    v.line([(b + 0.2, 3.0), (d - 0.2, 3.0)], (150, 150, 150), 0.015)
    for y in (4.2, 4.4, 4.6, 4.8):
        v.line([(b + 0.3, y), (d - 0.3, y)], METAL_DARK, 0.03)

    # Fuel intake B6-C6: refuelling hatch with its cap.
    v.fill([(b + 0.4, 5.15), (d - 0.4, 5.15), (d - 0.4, 5.85), (b + 0.4, 5.85)], METAL)
    v.ellipse(c - 0.2, 5.3, c + 0.2, 5.7, CAP)

    # Rear door, row 7: hinge line and two leaves.
    v.line([(a + 0.1, 6.12), (right - 0.1, 6.12)], OUTLINE, 0.03)
    v.line([(c, 6.15), (c, 6.9)], OUTLINE, 0.025)
    for x in (a + 0.4, right - 0.4):
        v.fill([(x - 0.12, 6.4), (x + 0.12, 6.4), (x + 0.12, 6.65), (x - 0.12, 6.65)], METAL)

    # Turbofans A3-A5 / D3-D5: nacelles on the hull's shoulders, copper fan at the front, exhaust ring behind.
    for x0 in (a + 0.06, d + 0.04):
        x1 = x0 + 0.9
        v.fill([(x0, 2.45), (x1, 2.45), (x1, 4.85), (x0 + 0.1, 4.95), (x0, 4.85)], METAL)
        v.plate([(x0 + 0.15, 2.5), (x1 - 0.15, 2.5), (x1 - 0.15, 4.85), (x0 + 0.15, 4.85)], 120, None, bevel=0.02)
        for y in (3.4, 3.75, 4.1, 4.45):
            v.line([(x0 + 0.08, y), (x1 - 0.08, y)], METAL_DARK, 0.03)
        v.ellipse(x0, 2.05, x1, 2.95, COPPER, width=0.035)
        v.ellipse(x0 + 0.12, 2.17, x1 - 0.12, 2.83, COPPER_DARK, outline=False)
        cx, cy = (x0 + x1) / 2, 2.5
        for k in range(8):
            ang = k * math.pi / 4
            v.line([(cx, cy), (cx + 0.33 * math.cos(ang), cy + 0.33 * math.sin(ang))], COPPER, 0.03)
        v.ellipse(cx - 0.1, cy - 0.1, cx + 0.1, cy + 0.1, OUTLINE, outline=False)
        v.ellipse(x0 + 0.2, 4.7, x1 - 0.2, 4.98, METAL_DARK)
    return v.done()


def south():
    """Nose toward the viewer: the north view turned round, with the cockpit's front face and lights showing."""
    img, mask = north()
    img, mask = img.rotate(180), mask.rotate(180)
    v = View(W, L)
    v.img.paste(img.resize(v.img.size, Image.LANCZOS))
    v.mask.paste(mask.resize(v.mask.size, Image.NEAREST))
    b, d = FOOT_X + 1, FOOT_X + 3
    # Front face of the cockpit box (now at the bottom, row 1 = y 6-7), windscreen and headlights.
    v.plate([(b + 0.05, 6.35), (d - 0.05, 6.35), (d - 0.2, 6.97), (b + 0.2, 6.97)], 176, ARMOUR)
    for x0, x1 in ((b + 0.25, b + 0.95), (b + 1.05, d - 0.25)):
        v.fill([(x0, 6.45), (x1, 6.45), (x1 - 0.06, 6.75), (x0 + 0.06, 6.75)], GLASS)
        v.line([(x0 + 0.08, 6.5), (x0 + 0.35, 6.5)], GLASS_HI, 0.025)
    for x in (b + 0.35, d - 0.35):
        v.ellipse(x - 0.07, 6.82, x + 0.07, 6.94, LIGHT, outline=False)
    return v.done()


def east():
    """Side view, nose right. Row r spans x 7-r to 8-r; the far side (and its wing) is hidden."""
    v = View(L, W)
    col = lambda row: L - row          # left edge of a row in this view

    ground, belly, top = 5.3, 4.3, 2.05

    # Skids: front skid row 2, rear skid rows 4-5: struts and runners below the belly.
    skid = (28, 28, 32)
    for x0, x1 in ((col(2) + 0.2, col(2) + 0.8), (col(5) + 0.15, col(4) + 0.85)):
        v.fill([(x0, ground - 0.12), (x1, ground - 0.12), (x1 + 0.08, ground), (x0 - 0.08, ground)], skid)
        for x in (x0 + 0.1, x1 - 0.18):
            v.fill([(x, belly), (x + 0.08, belly), (x + 0.08, ground - 0.12), (x, ground - 0.12)], skid)

    # Hull side, rows 2-7, with a lit upper chamfer and a shaded lower one.
    v.plate([(col(7) + 0.05, top + 0.25), (col(2) + 1.0, top), (col(2) + 1.0, belly), (col(7) + 0.05, belly - 0.15)],
            190, HULL)
    v.plate([(col(7) + 0.05, top + 0.25), (col(2) + 1.0, top), (col(2) + 1.0, top + 0.35), (col(7) + 0.05, top + 0.55)],
            222, HULL, bevel=0.02)
    v.plate([(col(7) + 0.05, belly - 0.45), (col(2) + 1.0, belly - 0.35), (col(2) + 1.0, belly),
             (col(7) + 0.05, belly - 0.15)], 150, HULL, bevel=0.02)
    # Cabin portholes (rows 2-3) and panel seams.
    for x in (col(2) + 0.35, col(3) + 0.55):
        v.ellipse(x - 0.12, 2.62, x + 0.12, 2.86, GLASS)
    for row in (3, 4, 5, 6):
        v.line([(col(row) + 1.0, top + 0.05), (col(row) + 1.0, belly - 0.05)], (150, 150, 150), 0.012)
    # Rear door, row 7: hinge and seam at the tail.
    v.line([(col(7) + 0.12, top + 0.4), (col(7) + 0.12, belly - 0.25)], OUTLINE, 0.03)
    v.fill([(col(7) + 0.3, 3.0), (col(7) + 0.55, 3.0), (col(7) + 0.55, 3.3), (col(7) + 0.3, 3.3)], METAL)
    # Fuel intake, row 6: hatch on the top.
    roof = lambda x: top + 0.25 - 0.25 * (x - col(7) - 0.05) / (col(2) + 0.95 - col(7))   # sloped hull top
    x0, x1 = col(6) + 0.3, col(6) + 0.7
    v.fill([(x0, roof(x0) - 0.12), (x1, roof(x1) - 0.12), (x1, roof(x1) + 0.02), (x0, roof(x0) + 0.02)], CAP)

    # Cockpit, row 1: armoured box with a sloped nose and side windows.
    v.plate([(col(1), top + 0.1), (col(1) + 0.55, top + 0.15), (col(1) + 0.98, top + 0.85), (col(1) + 0.98, belly - 0.35),
             (col(1) + 0.7, belly - 0.05), (col(1), belly - 0.05)], 184, ARMOUR)
    v.fill([(col(1) + 0.12, top + 0.32), (col(1) + 0.5, top + 0.35), (col(1) + 0.82, top + 0.9),
            (col(1) + 0.12, top + 0.9)], GLASS)
    v.line([(col(1) + 0.2, top + 0.42), (col(1) + 0.45, top + 0.44)], GLASS_HI, 0.025)
    v.ellipse(col(1) + 0.85, belly - 0.32, col(1) + 0.97, belly - 0.2, LIGHT, outline=False)

    # Near wing, rows 2-6: an angled plate at mid-height, its outer cell reaching toward the viewer.
    wing = [(col(6) + 0.05, 3.45), (col(2) + 0.9, 3.05), (col(2) + 0.75, 3.75), (col(6) + 0.2, 4.0)]
    v.plate(wing, 160, WING)
    v.plate([(col(6) + 0.1, 3.72), (col(5) + 0.9, 3.6), (col(5) + 0.88, 3.74), (col(6) + 0.12, 3.86)], 186, ARMOUR,
            bevel=0.02)
    v.ellipse(col(6) + 0.18, 3.83, col(6) + 0.32, 3.97, LIGHT, outline=False)

    # Turbofan nacelle, rows 3-5, on the upper hull: copper intake at the front, ribs, exhaust at the back.
    x0, x1 = col(5) + 0.05, col(3) + 0.95
    v.fill([(x0, 1.3), (x1 - 0.2, 1.25), (x1, 1.45), (x1, 2.25), (x1 - 0.2, 2.4), (x0, 2.35)], METAL)
    v.plate([(x0 + 0.1, 1.4), (x1 - 0.25, 1.36), (x1 - 0.25, 1.62), (x0 + 0.1, 1.66)], 128, None, bevel=0.02)
    for x in (x0 + 0.6, x0 + 1.1, x0 + 1.6, x0 + 2.1):
        v.line([(x, 1.32), (x, 2.36)], METAL_DARK, 0.03)
    v.ellipse(x1 - 0.18, 1.22, x1 + 0.08, 2.48, COPPER, width=0.03)
    v.ellipse(x0 - 0.06, 1.42, x0 + 0.1, 2.22, METAL_DARK)
    v.fill([(x0 + 0.8, 2.36), (x0 + 1.4, 2.36), (x0 + 1.3, top + 0.02), (x0 + 0.9, top + 0.02)], METAL_DARK)  # pylon
    return v.done()


def shadow(north_img):
    alpha = north_img.getchannel("A").point(lambda a: 140 if a > 20 else 0)
    out = Image.new("RGBA", north_img.size, (0, 0, 0, 0))
    out.putalpha(alpha)
    return out


def grid_overlay(img, view):
    """Check image (not shipped): the grid names over a view."""
    out = img.copy()
    dr = ImageDraw.Draw(out)
    red = (255, 0, 0, 255)
    if view == "north":
        for i in range(5):
            x = round((FOOT_X + i) * PX)
            dr.line([(x, 0), (x, L * PX)], fill=red, width=2)
        for j in range(8):
            dr.line([(round(FOOT_X * PX), j * PX), (round((FOOT_X + 4) * PX), j * PX)], fill=red, width=2)
        for i in range(4):
            for j in range(7):
                dr.text((round((FOOT_X + i) * PX) + 4, j * PX + 4), f"{'ABCD'[i]}{j + 1}", fill=red)
    else:   # east: rows run right to left
        for j in range(8):
            dr.line([(j * PX, 0), (j * PX, W * PX)], fill=red, width=2)
        for row in range(1, 8):
            dr.text(((L - row) * PX + 4, 4), f"row {row}", fill=red)
    return out
