#!/usr/bin/env python3
"""news-image-20261123 v2: one image summing up Monday 23 November 2026.

Pure Python 3 standard library only: no network, no wall clock, no
unseeded randomness. Renders a 1024x1024 newspaper front page
("THE WORLD TODAY") with a hand-drawn 5x7 bitmap font and writes it to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).

Run:  python3 main.py        (or MAKEFUN_OUTPUT_DIR=out python3 main.py)
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 234)   # warm newsprint
CARD = (255, 255, 255)
INK = (22, 22, 22)
NAVY = (14, 42, 71)
NAVY2 = (27, 66, 104)
RED = (179, 39, 30)
GREEN = (28, 120, 52)
GREEN_LT = (46, 160, 76)
GOLD = (201, 162, 39)
GOLD_LT = (232, 196, 90)
GREY = (120, 116, 108)
GREY_LT = (205, 200, 188)
BLUE = (37, 99, 168)
ORANGE = (214, 106, 22)
TEAL = (15, 118, 110)
PINK = (206, 92, 138)
SKY = (168, 205, 232)
DARK = (16, 24, 34)

# ---------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is blank.
FONT = {
    'A': ("..#..", ".#.#.", "#...#", "#...#", "#####", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    'a': (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    'b': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    'c': (".....", ".....", ".###.", "#....", "#....", "#....", ".###."),
    'd': ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    'e': (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    'f': ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
    'g': (".....", ".####", "#...#", "#...#", ".####", "....#", ".###."),
    'h': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    'i': ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
    'j': ("...#.", ".....", "..##.", "...#.", "...#.", "#..#.", ".##.."),
    'k': ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    'l': (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'm': (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    'n': (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    'o': (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    'p': (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    'q': (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    'r': (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    's': (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    't': (".#...", ".#...", "#####", ".#...", ".#...", ".#...", "..##."),
    'u': (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    'v': (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'w': (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    'x': (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    'y': (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    'z': (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    '0': (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", ".##.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", ".##.."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    '(': ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    '/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    '%': ("##..#", "#.#.#", "...#.", "..#..", ".#...", "#.#.#", "#..##"),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    '&': (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '*': (".....", ".#.#.", "..#..", ".#.#.", ".....", ".....", "....."),
    '#': (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    '_': (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    '|': ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    '<': ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
    '>': (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
    '[': (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    ']': (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
}

CHAR_W = 6   # advance per glyph (5 + 1 spacing), in font units
CHAR_H = 7


def text_width(s, scale):
    return len(s) * CHAR_W * scale - scale


def draw_text(cv, x, y, s, scale, color):
    """Draw string s with its top-left at (x, y); returns width drawn."""
    cx = x
    for ch in s:
        g = FONT.get(ch)
        if g is None:
            cx += CHAR_W * scale
            continue
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == '#':
                    cv.rect(cx + c * scale, y + r * scale, scale, scale, color)
        cx += CHAR_W * scale
    return cx - x


def wrap_lines(s, max_w, scale):
    """Greedy word wrap; returns list of lines that fit max_w pixels."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_block(cv, x, y, s, max_w, scale, color, leading=None):
    """Draw wrapped text; returns y just below the last line."""
    lh = leading if leading is not None else 7 * scale + 4
    for line in wrap_lines(s, max_w, scale):
        draw_text(cv, x, y, line, scale, color)
        y += lh
    return y


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        r, g, b = bg
        for i in range(0, len(self.px), 3):
            self.px[i] = r
            self.px[i + 1] = g
            self.px[i + 2] = b

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def hline(self, x, y, w, color):
        self.rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.rect(x, y, 1, h, color)

    def frame(self, x, y, w, h, color, t=1):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            self.rect(x - t // 2, y - t // 2, t, t, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, color, t=2):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d <= r * r:
                    self.set(xx, yy, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0:
                    self.set(xx, yy, color)

    def poly(self, pts, color):
        """Scanline fill of a simple polygon (list of (x, y))."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                for x in range(int(xs[j]), int(xs[j + 1]) + 1):
                    self.set(x, y, color)

    def tri(self, a, b, c, color):
        self.poly([a, b, c], color)


# ---------------------------------------------------------------------- PNG
def write_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ------------------------------------------------------------- pictograms
# Each draws a small flat scene inside the box (x, y, w, h).

def pic_ship(cv, x, y, w, h):
    """Russian corvette at Benghazi: hull, mast, sea, drone boat, blast."""
    sea_y = y + int(h * 0.68)
    cv.rect(x, sea_y, w, h - int(h * 0.68), (46, 110, 168))
    cv.rect(x, sea_y, w, 2, (140, 190, 225))
    # hull
    cv.poly([(x + 6, sea_y - 14), (x + w - 8, sea_y - 14),
             (x + w - 18, sea_y - 2), (x + 14, sea_y - 2)], (52, 58, 64))
    cv.rect(x + 14, sea_y - 26, 26, 12, (52, 58, 64))      # superstructure
    cv.vline(x + 46, sea_y - 40, 16, (52, 58, 64))          # mast
    cv.line(x + 46, sea_y - 40, x + 58, sea_y - 30, (52, 58, 64), 2)
    # blast star above the deck
    bx, by = x + w - 22, sea_y - 44
    for dx, dy in [(0, -12), (9, -9), (12, 0), (9, 9), (0, 12),
                   (-9, 9), (-12, 0), (-9, -9)]:
        cv.line(bx, by, bx + dx, by + dy, ORANGE, 3)
    cv.circle(bx, by, 6, GOLD_LT)
    # small drone boat speeding in
    cv.poly([(x + 2, sea_y + 8), (x + 20, sea_y + 8),
             (x + 16, sea_y + 14), (x + 6, sea_y + 14)], (240, 240, 240))
    cv.line(x + 2, sea_y + 8, x + 20, sea_y + 8, INK, 1)


def pic_climate(cv, x, y, w, h):
    """Globe with a thermometer: COP31 climate talks, no deal."""
    cx, cy, r = x + w // 2 - 8, y + h // 2, 24
    cv.circle(cx, cy, r, BLUE)
    cv.ellipse(cx - 9, cy - 8, 8, 5, GREEN)     # land blobs
    cv.ellipse(cx + 8, cy + 6, 9, 6, GREEN)
    cv.ellipse(cx + 6, cy - 12, 5, 4, GREEN)
    cv.ring(cx, cy, r, NAVY, 2)
    # thermometer at right
    tx = x + w - 16
    cv.rect(tx, y + 8, 8, h - 22, (240, 240, 240))
    cv.frame(tx, y + 8, 8, h - 22, INK, 1)
    cv.rect(tx + 1, y + h - 26, 6, 12, RED)
    cv.circle(tx + 4, y + h - 12, 7, RED)
    # red cross over the globe = no deal
    cv.line(cx - 30, cy - 30, cx + 14, cy + 14, RED, 4)
    cv.line(cx - 30, cy + 14, cx + 14, cy - 30, RED, 4)


def pic_kyiv(cv, x, y, w, h):
    """Apartment block hit: broken roofline, dark windows, rubble."""
    bx, by = x + 8, y + 6
    bw, bh = w - 26, h - 26
    cv.rect(bx, by + 14, bw, bh - 14, (122, 116, 104))
    # jagged broken top
    cv.poly([(bx, by + 14), (bx + 12, by + 2), (bx + 24, by + 12),
             (bx + 38, by), (bx + 52, by + 10), (bx + bw, by + 6),
             (bx + bw, by + 14)], (90, 84, 72))
    for r in range(3):
        for c in range(4):
            wx = bx + 6 + c * 15
            wy = by + 22 + r * 16
            cv.rect(wx, wy, 9, 11, (250, 214, 90) if (r + c) % 3 == 0 else DARK)
    # rubble at the base
    cv.tri((bx - 2, by + bh), (bx + 14, by + bh - 12), (bx + 26, by + bh), GREY)
    cv.tri((bx + 22, by + bh), (bx + 36, by + bh - 9), (bx + 48, by + bh), (90, 84, 72))
    # rescue light beam
    cv.line(bx + bw - 4, by + bh, bx + bw + 6, by + 4, GOLD_LT, 2)


def pic_factory(cv, x, y, w, h):
    """Sweets factory: sawtooth roof, chimney, flame, smoke."""
    fx, fy = x + 4, y + 16
    fw = w - 14
    cv.poly([(fx, fy + 26), (fx, fy), (fx + 14, fy + 12), (fx + 28, fy),
             (fx + 42, fy + 12), (fx + 56, fy), (fx + fw, fy + 4),
             (fx + fw, fy + 26)], (96, 92, 84))
    cv.rect(fx, fy + 26, fw, h - fy - 26 + y - y, (150, 142, 128))
    cv.rect(fx + fw - 12, fy - 14, 9, 18, (120, 60, 50))
    # flame
    cv.poly([(fx + 20, fy + 24), (fx + 28, fy - 2), (fx + 34, fy + 10),
             (fx + 40, fy - 6), (fx + 46, fy + 24)], ORANGE)
    cv.poly([(fx + 27, fy + 24), (fx + 32, fy + 8), (fx + 37, fy + 24)], GOLD_LT)
    # smoke puffs
    cv.circle(fx + fw - 8, fy - 22, 5, (200, 196, 188))
    cv.circle(fx + fw - 2, fy - 30, 6, (215, 211, 203))
    # door
    cv.rect(fx + 8, fy + 34, 12, 18, DARK)


def pic_space(cv, x, y, w, h):
    """Mercury with craters, spacecraft, dashed orbit."""
    cx, cy = x + 26, y + h // 2 + 4
    # dashed orbit ellipse (approximated with dots)
    for a in range(0, 360, 12):
        import math
        ox = int(x + w // 2 + 34 * math.cos(math.radians(a)))
        oy = int(y + h // 2 + 16 * math.sin(math.radians(a)))
        cv.rect(ox, oy, 2, 2, GREY)
    cv.circle(cx, cy, 20, (150, 146, 138))     # Mercury
    cv.circle(cx - 7, cy - 6, 4, (120, 116, 108))
    cv.circle(cx + 8, cy + 5, 5, (120, 116, 108))
    cv.circle(cx + 6, cy - 10, 3, (170, 166, 158))
    # spacecraft: body + panels
    sx, sy = x + w - 34, y + 12
    cv.rect(sx, sy, 14, 10, (200, 200, 200))
    cv.frame(sx, sy, 14, 10, INK, 1)
    cv.rect(sx - 12, sy + 2, 11, 6, BLUE)
    cv.rect(sx + 15, sy + 2, 11, 6, BLUE)
    cv.line(sx + 7, sy + 10, sx + 7, sy + 18, GOLD, 2)
    # stars
    for sx2, sy2 in [(x + 6, y + 6), (x + w - 8, y + h - 10), (x + w // 2, y + 4)]:
        cv.rect(sx2, sy2, 2, 2, INK)


def pic_health(cv, x, y, w, h):
    """Hospital cross on a screen with an AI chip."""
    mx, my = x + 6, y + 6
    cv.rect(mx, my, w - 30, h - 20, (240, 244, 248))
    cv.frame(mx, my, w - 30, h - 20, INK, 2)
    # screen trace: a scan arc
    cv.line(mx + 6, my + h - 30, mx + 16, my + 14, TEAL, 2)
    cv.line(mx + 16, my + 14, mx + 26, my + h - 30, TEAL, 2)
    cv.line(mx + 26, my + h - 30, mx + 36, my + 18, TEAL, 2)
    # cross badge
    bx, by = x + w - 26, y + h - 28
    cv.circle(bx, by, 12, RED)
    cv.rect(bx - 2, by - 7, 4, 14, CARD)
    cv.rect(bx - 7, by - 2, 14, 4, CARD)
    # "AI" tag
    draw_text(cv, mx + 4, my + 2, "AI", 1, INK)


def pic_lead_chart(cv, x, y, w, h):
    """Lead art: dark chip, circuit traces, green surge line, +31.5%."""
    cv.rect(x, y, w, h, NAVY)
    # faint circuit traces
    for i in range(5):
        yy = y + 14 + i * 16
        cv.hline(x + 10, yy, w - 20, NAVY2)
        cv.vline(x + 14 + i * 34, y + 10, h - 20, NAVY2)
    # chip
    chx, chy = x + 18, y + h - 92
    cv.rect(chx, chy, 74, 74, DARK)
    cv.frame(chx, chy, 74, 74, GOLD, 2)
    cv.rect(chx + 16, chy + 16, 42, 42, NAVY2)
    cv.frame(chx + 16, chy + 16, 42, 42, GOLD_LT, 1)
    draw_text(cv, chx + 19, chy + 29, "NVDA", 1, GOLD_LT)
    for i in range(4):
        cv.rect(chx + 8 + i * 18, chy - 7, 4, 7, GOLD)
        cv.rect(chx + 8 + i * 18, chy + 74, 4, 7, GOLD)
    # rising chart line
    pts = [(x + 110, y + h - 30), (x + 160, y + h - 52), (x + 205, y + h - 44),
           (x + 255, y + h - 78), (x + 305, y + h - 66), (x + 355, y + h - 108),
           (x + 405, y + h - 96), (x + 428, y + h - 132)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], GREEN_LT, 4)
    # arrow head
    cv.poly([(x + 428, y + h - 132), (x + 414, y + h - 128), (x + 424, y + h - 116)],
            GREEN_LT)
    # big gain figure
    draw_text(cv, x + 118, y + 16, "+31.5%", 4, GREEN_LT)
    draw_text(cv, x + 118, y + 52, "SHARES IN ONE DAY", 1, (220, 224, 230))
    draw_text(cv, x + 18, y + 16, "NVIDIA", 2, (240, 242, 245))
    draw_text(cv, x + 18, y + 34, "NASDAQ +7%", 1, GOLD_LT)


# ------------------------------------------------------------------- layout
MARGIN = 24
COL_W = (W - 2 * MARGIN - 2 * 12) // 3   # 317

CARDS = [
    ("WAR AT SEA - LIBYA", "UKRAINE SINKS RUSSIAN WARSHIP",
     "Seven sea drones sink the corvette Merkury at Benghazi; a Ka-27 "
     "helicopter is lost.", pic_ship, RED),
    ("CLIMATE - ANTALYA", "COP31 ENDS WITH NO DEAL",
     "The longest climate summit ever collapses over fossil fuels - the "
     "first failure since 2009.", pic_climate, TEAL),
    ("UKRAINE - KYIV", "15 KILLED IN STRIKES ON KYIV",
     "Russian bombardment hits homes near Kyiv; rescuers pull a boy of 7 "
     "alive from the rubble.", pic_kyiv, RED),
    ("INDONESIA - WEST JAVA", "24 DEAD IN FACTORY FIRE",
     "A blaze guts a sweets factory in Cikande; about 30 workers are "
     "still missing.", pic_factory, ORANGE),
    ("SPACE - MERCURY", "PROBE REACHES MERCURY",
     "BepiColombo slips into orbit after an eight-year trip, safe "
     "despite a software glitch.", pic_space, BLUE),
    ("HEALTH - ENGLAND", "AI TO READ 700,000 BREAST SCANS",
     "The NHS starts the world's largest AI screening trial to catch "
     "cancer earlier.", pic_health, PINK),
]

BRIEFS = [
    ("MATHS", "AI-assisted Riemann proof claim passes formal Lean checks."),
    ("IRAN", "US sanctions two dozen firms in Iran's shadow banking web."),
    ("FOOTBALL", "UK to host the 2035 Women's World Cup, first since 1966."),
    ("POLAND", "Suspected Russian drone in Polish airspace for 8 minutes."),
    ("SUDAN", "Drones hit homes and a UN building in Khartoum."),
    ("TECH", "States sue SpaceX, X and xAI over Grok sexualised images."),
]


def render():
    cv = Canvas(W, H, PAPER)

    # ---- masthead ------------------------------------------------------
    cv.rect(0, 0, W, 116, NAVY)
    title = "THE WORLD TODAY"
    tw = text_width(title, 6)
    draw_text(cv, (W - tw) // 2, 18, title, 6, (250, 248, 242))
    cv.rect(0, 76, W, 3, GOLD)
    draw_text(cv, MARGIN, 90, "MONDAY 23 NOVEMBER 2026", 2, GOLD_LT)
    right = "ONE DAY - ONE PICTURE"
    draw_text(cv, W - MARGIN - text_width(right, 2), 90, right, 2,
              (220, 224, 230))
    cv.rect(0, 116, W, 4, GOLD)

    # ---- lead story ----------------------------------------------------
    ly, lh = 132, 236
    art_x, art_w = MARGIN, 452
    pic_lead_chart(cv, art_x, ly, art_w, lh)
    tx = art_x + art_w + 20
    tw2 = W - MARGIN - tx
    draw_text(cv, tx, ly + 2, "MARKETS - LEAD STORY", 2, RED)
    cv.rect(tx, ly + 34, tw2, 2, RED)
    draw_text(cv, tx, ly + 46, "HUANG IS BACK", 5, INK)
    y = draw_block(cv, tx, ly + 92,
                   "Chief reinstated after 11 days.",
                   tw2, 2, NAVY, leading=32)
    draw_block(cv, tx, y + 6,
               "Shares rocket 31.5% and the Nasdaq jumps 7% after "
               "Donald Trump says he pressed the board to bring "
               "Jensen Huang back.", tw2, 2, INK, leading=30)

    # ---- story grid: 3 columns x 2 rows --------------------------------
    gy, gh, gap = 384, 188, 12
    for i, (kicker, head, deck, pic, kc) in enumerate(CARDS):
        r, c = divmod(i, 3)
        x = MARGIN + c * (COL_W + gap)
        y0 = gy + r * (gh + gap)
        cv.rect(x, y0, COL_W, gh, CARD)
        cv.frame(x, y0, COL_W, gh, GREY_LT, 1)
        cv.rect(x, y0, COL_W, 4, kc)
        # pictogram top-right
        pic(cv, x + COL_W - 78, y0 + 12, 66, 62)
        draw_text(cv, x + 12, y0 + 12, kicker, 1, kc)
        hy = y0 + 28
        hy = draw_block(cv, x + 12, hy, head, COL_W - 96, 2, INK, leading=28)
        draw_block(cv, x + 12, hy + 4, deck, COL_W - 24, 2, (60, 58, 52),
                   leading=24)

    # ---- briefs band -----------------------------------------------------
    by = gy + 2 * gh + gap + 14   # 786
    cv.rect(MARGIN, by, W - 2 * MARGIN, 3, NAVY)
    draw_text(cv, MARGIN, by + 10, "AROUND THE WORLD - IN BRIEF", 2, NAVY)
    draw_text(cv, W - MARGIN - text_width("23 NOV 2026", 1), by + 12,
              "23 NOV 2026", 1, GREY)
    bw = (W - 2 * MARGIN - 16) // 2
    bh = 40
    for i, (kick, text) in enumerate(BRIEFS):
        r, c = divmod(i, 2)
        x = MARGIN + c * (bw + 16)
        yy = by + 38 + r * (bh + 4)
        draw_text(cv, x, yy, kick + ": ", 2, RED)
        kx = x + text_width(kick + ": ", 2)
        draw_block(cv, kx, yy, text, bw - (kx - x), 2, INK, leading=19)

    # ---- footer ----------------------------------------------------------
    fy = by + 38 + 3 * (bh + 4) + 10   # ~946
    cv.rect(MARGIN, fy, W - 2 * MARGIN, 2, GREY_LT)
    draw_text(cv, MARGIN, fy + 10,
              "SOURCES: REUTERS - CNN - LE MONDE - ESA - BMJ - US TREASURY - "
              "SKY SPORTS - KYIV POST - SCMP - AL JAZEERA - PHYS.ORG - "
              "THE BRIEF", 1, GREY)
    draw_text(cv, MARGIN, fy + 22,
              "All events of Monday 23 November 2026, as reported. Drawn "
              "entirely in code - no photographs.", 1, GREY)
    draw_text(cv, MARGIN, fy + 34,
              "THE WORLD TODAY - NO. 327 - ONE DAY, ONE PICTURE", 1, GREY)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    cv = render()
    size = write_png(cv, os.path.join(outdir, "entry.png"))
    print("wrote %s/entry.png (%d bytes, %dx%d)"
          % (outdir, size, cv.w, cv.h))


if __name__ == "__main__":
    main()
