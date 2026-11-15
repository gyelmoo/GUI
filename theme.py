"""Look and feel: fonts, drawn icons, rounded shapes and decorative images.

Everything visual that is shared by several screens lives here, so the five
screens look like one application. Images are made with Pillow; if Pillow is
missing the app still runs (decorations and icons are simply left out).
"""

import math
import os

from config import BASE_DIR

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageTk
    PIL_OK = True
except ImportError:                      # the app still works, just plainer
    PIL_OK = False

ASSET_DIR = os.path.join(BASE_DIR, "assets")

# ----------------------------------------------------------------------------
# Fonts (Segoe UI / Georgia come with Windows; Tk falls back elsewhere)
# ----------------------------------------------------------------------------
UI = "Segoe UI"
SERIF = "Georgia"


def font(size, *styles):
    return (UI, size, " ".join(styles)) if styles else (UI, size)


F_TITLE = (UI, 24, "bold")
F_GREETING = (SERIF, 24, "bold italic")
F_SUBTITLE = (SERIF, 12, "italic")
F_PAGE_SUB = (UI, 12)
F_H2 = (UI, 13, "bold")
F_LABEL = (UI, 11, "bold")
F_BODY = (UI, 10)
F_SMALL = (UI, 9)
F_BUTTON = (UI, 11, "bold")
F_STAT = (UI, 22, "bold")

_cache = {}


def _key(*parts):
    return "|".join(str(p) for p in parts)


def hex_rgb(colour, alpha=255):
    colour = colour.lstrip("#")
    return tuple(int(colour[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def mix(c1, c2, t):
    """Blend two #rrggbb colours (t=0 -> c1, t=1 -> c2)."""
    a, b = hex_rgb(c1), hex_rgb(c2)
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def photo(pil_image):
    return ImageTk.PhotoImage(pil_image)


# ----------------------------------------------------------------------------
# Decorative pictures from /assets
# ----------------------------------------------------------------------------
def asset_pil(name, width=None, height=None, fade=1.0):
    """The PNG `name` scaled to fit inside width x height (keeps its shape)."""
    path = os.path.join(ASSET_DIR, name + ".png")
    img = Image.open(path).convert("RGBA")
    if width or height:
        w, h = img.size
        scale = min((width or 10 ** 6) / w, (height or 10 ** 6) / h)
        img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    if fade < 1:
        alpha = img.getchannel("A").point(lambda v: int(v * fade))
        img.putalpha(alpha)
    return img


def asset(name, width=None, height=None, fade=1.0, flip=False):
    """Cached Tk image of an asset, or None if it cannot be loaded."""
    if not PIL_OK:
        return None
    k = _key("asset", name, width, height, fade, flip)
    if k not in _cache:
        try:
            img = asset_pil(name, width, height, fade)
            if flip:
                img = ImageOps.mirror(img)
            _cache[k] = photo(img)
        except Exception:
            _cache[k] = None
    return _cache[k]


def long_vine_pil(segments=3, flip=False):
    """A long hanging pothos vine made by joining vine pictures end to end."""
    seg = Image.open(os.path.join(ASSET_DIR, "vine_pothos.png")).convert("RGBA")
    mirror = ImageOps.mirror(seg)
    sw, sh = seg.size
    step = int(sh * 0.82)                 # each piece starts where the last stem ends
    shift = 63                            # lines the stems up (bottom of one = top of next)
    out = Image.new("RGBA", (sw + shift, sh + step * (segments - 1)), (0, 0, 0, 0))
    for i in range(segments):
        piece, x = (seg, 0) if i % 2 == 0 else (mirror, shift)
        out.alpha_composite(piece, (x, step * i))
    out = out.crop(out.getbbox())
    return ImageOps.mirror(out) if flip else out


def long_vine_ratio(segments=3):
    """Width / height of a long vine (used to keep vines inside a space)."""
    k = _key("vine_ratio", segments)
    if k not in _cache:
        img = long_vine_pil(segments)
        _cache[k] = img.width / img.height
    return _cache[k]


def long_vine(height, segments=3, flip=False):
    """Cached Tk image of a long vine scaled to `height` pixels (None without Pillow)."""
    if not PIL_OK:
        return None
    k = _key("vine", int(height), segments, flip)
    if k not in _cache:
        try:
            img = long_vine_pil(segments, flip)
            scale = height / img.height
            _cache[k] = photo(img.resize((max(1, int(img.width * scale)), int(height)),
                                         Image.LANCZOS))
        except Exception:
            _cache[k] = None
    return _cache[k]


def deco_label(parent, name, width=None, height=None, bg=None, fade=1.0, flip=False):
    """A Label showing a decorative picture (empty Label if pictures are unavailable)."""
    import tkinter as tk
    img = asset(name, width, height, fade, flip)
    lbl = tk.Label(parent, bd=0, highlightthickness=0,
                   bg=bg or parent.cget("bg"))
    if img is not None:
        lbl.config(image=img)
        lbl.image = img
    return lbl


# ----------------------------------------------------------------------------
# Rounded shapes
# ----------------------------------------------------------------------------
SS = 3          # supersampling for smooth edges


def rounded_rect_pil(w, h, r, fill, outline=None, width=1, shadow=0, dash=False):
    """Smooth rounded rectangle (RGBA). `shadow` adds a soft shadow below it."""
    W, H = max(2, int(w)), max(2, int(h))
    img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    sh = int(shadow)
    box_h = H - sh
    if sh:
        sh_img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        ImageDraw.Draw(sh_img).rounded_rectangle(
            (sh * SS, sh * 2 * SS, (W - sh) * SS - 1, H * SS - 1),
            radius=r * SS, fill=(60, 80, 60, 38))
        img = sh_img.filter(ImageFilter.GaussianBlur(sh * SS * 0.6))
    d = ImageDraw.Draw(img)
    rect = (0, 0, W * SS - 1, box_h * SS - 1)
    if outline and not dash:
        d.rounded_rectangle(rect, radius=r * SS, fill=hex_rgb(outline))
        inset = width * SS
        d.rounded_rectangle((inset, inset, rect[2] - inset, rect[3] - inset),
                            radius=max(0, (r - width) * SS), fill=hex_rgb(fill))
    else:
        d.rounded_rectangle(rect, radius=r * SS, fill=hex_rgb(fill))
    if outline and dash:
        _dashed_round_rect(d, rect, r * SS, hex_rgb(outline), width * SS)
    return img.resize((W, H), Image.LANCZOS)


def _dashed_round_rect(d, rect, r, colour, width):
    x0, y0, x1, y1 = rect
    pts = []
    steps = 10
    corners = [(x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90),
               (x0 + r, y0 + r, 180)]
    for cx, cy, start in corners:
        for i in range(steps + 1):
            a = math.radians(start + 90 * i / steps)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts.append(pts[0])
    dash, gap, carry, drawing = 9 * SS, 6 * SS, 0.0, True
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = math.hypot(bx - ax, by - ay)
        pos = 0.0
        while pos < seg:
            limit = (dash if drawing else gap) - carry
            step = min(limit, seg - pos)
            if drawing:
                t0, t1 = pos / seg, (pos + step) / seg
                d.line((ax + (bx - ax) * t0, ay + (by - ay) * t0,
                        ax + (bx - ax) * t1, ay + (by - ay) * t1), fill=colour, width=width)
            pos += step
            carry += step
            if carry >= (dash if drawing else gap) - 0.01:
                drawing, carry = not drawing, 0.0


def rounded_rect(w, h, r, fill, outline=None, width=1, shadow=0, dash=False):
    if not PIL_OK:
        return None
    k = _key("rr", int(w), int(h), r, fill, outline, width, shadow, dash)
    if k not in _cache:
        _cache[k] = photo(rounded_rect_pil(w, h, r, fill, outline, width, shadow, dash))
        if len(_cache) > 900:                # resizing creates many sizes - keep it small
            for old in [x for x in list(_cache) if x.startswith("rr|")][:300]:
                _cache.pop(old, None)
    return _cache[k]


def round_photo(path, w, h, radius=12, mtime=None):
    """A user's picture cropped to w x h with rounded corners (cached)."""
    if not PIL_OK:
        return None
    k = _key("photo", path, mtime, w, h, radius)
    if k not in _cache:
        try:
            with Image.open(path) as src:
                img = ImageOps.fit(ImageOps.exif_transpose(src).convert("RGBA"), (w * SS, h * SS),
                                   Image.LANCZOS)
            mask = Image.new("L", (w * SS, h * SS), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, w * SS - 1, h * SS - 1),
                                                   radius=radius * SS, fill=255)
            img.putalpha(mask)
            _cache[k] = photo(img.resize((w, h), Image.LANCZOS))
        except Exception:
            _cache[k] = None
    return _cache[k]


def pil_round_preview(pil_img, w, h, radius=14):
    """Rounded preview of an in-memory (not yet saved) PIL picture."""
    img = ImageOps.fit(pil_img.convert("RGBA"), (w * SS, h * SS), Image.LANCZOS)
    mask = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w * SS - 1, h * SS - 1),
                                           radius=radius * SS, fill=255)
    img.putalpha(mask)
    return photo(img.resize((w, h), Image.LANCZOS))


def donut(size, parts, thickness=0.28, gap_colour=None):
    """Smooth donut chart. parts = [(value, colour), ...]."""
    if not PIL_OK:
        return None
    k = _key("donut", size, parts, thickness)
    if k in _cache:
        return _cache[k]
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    total = sum(v for v, _ in parts)
    if total <= 0:
        d.ellipse((0, 0, S - 1, S - 1), fill=hex_rgb("#e7ece3"))
    else:
        start = -90.0
        for value, colour in parts:
            if value <= 0:
                continue
            extent = 360.0 * value / total
            d.pieslice((0, 0, S - 1, S - 1), start, start + extent, fill=hex_rgb(colour))
            start += extent
    hole = S * thickness
    d.ellipse((hole, hole, S - 1 - hole, S - 1 - hole), fill=(0, 0, 0, 0))
    _cache[k] = photo(img.resize((size, size), Image.LANCZOS))
    return _cache[k]


def ring(size, pct, colour, track):
    """Small progress ring (used on the Completion Rate card)."""
    if not PIL_OK:
        return None
    k = _key("ring", size, pct, colour, track)
    if k not in _cache:
        S = size * SS
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        w = int(S * 0.16)
        d.arc((w // 2, w // 2, S - w // 2, S - w // 2), 0, 360, fill=hex_rgb(track), width=w)
        if pct > 0:
            d.arc((w // 2, w // 2, S - w // 2, S - w // 2), -90, -90 + 3.6 * pct,
                  fill=hex_rgb(colour), width=w)
        _cache[k] = photo(img.resize((size, size), Image.LANCZOS))
    return _cache[k]


# ----------------------------------------------------------------------------
# Icons - drawn on a 24 x 24 grid, so they stay sharp at any size
# ----------------------------------------------------------------------------
def _petal(cx, cy, length, width, angle_deg, n=24):
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = (math.cos(t) + 1) / 2 * length
        y = math.sin(t) * width / 2 * math.sin((math.cos(t) + 1) / 2 * math.pi) ** 0.6
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return pts


def _draw_icon(name, d, k, c, clear):
    def P(x, y):
        return (x * k, y * k)

    def L(points, w=2.2):
        pts = [P(*p) for p in points]
        d.line(pts, fill=c, width=max(1, int(w * k)), joint="curve")
        for p in (pts[0], pts[-1]):              # round line ends
            r = w * k / 2
            d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=c)

    def E(x0, y0, x1, y1, fill=True, w=2.2, col=None):
        if fill:
            d.ellipse((*P(x0, y0), *P(x1, y1)), fill=col or c)
        else:
            d.ellipse((*P(x0, y0), *P(x1, y1)), outline=col or c, width=int(w * k))

    def R(x0, y0, x1, y1, r=2, fill=True, w=2.2, col=None):
        if fill:
            d.rounded_rectangle((*P(x0, y0), *P(x1, y1)), radius=r * k, fill=col or c)
        else:
            d.rounded_rectangle((*P(x0, y0), *P(x1, y1)), radius=r * k, outline=col or c,
                                width=int(w * k))

    def POLY(points, col=None):
        d.polygon([P(*p) for p in points], fill=col or c)

    def ARC(x0, y0, x1, y1, a0, a1, w=2.2):
        d.arc((*P(x0, y0), *P(x1, y1)), a0, a1, fill=c, width=int(w * k))

    if name == "home":
        POLY([(2.5, 11.5), (12, 3), (21.5, 11.5), (19.5, 11.5), (19.5, 21), (4.5, 21),
              (4.5, 11.5)])
        R(9.8, 14, 14.2, 21.2, 1.2, col=clear)
    elif name == "plus":
        L([(12, 4), (12, 20)], 3.2)
        L([(4, 12), (20, 12)], 3.2)
    elif name == "search":
        E(3, 3, 17, 17, fill=False, w=2.6)
        L([(15.2, 15.2), (20.5, 20.5)], 3.2)
    elif name == "chart":
        R(3.5, 12, 8, 21, 1)
        R(9.8, 7, 14.2, 21, 1)
        R(16, 3, 20.5, 21, 1)
    elif name == "logout":
        L([(11, 3.5), (5, 3.5), (5, 20.5), (11, 20.5)], 2.2)
        L([(10, 12), (20.5, 12)], 2.2)
        L([(16.5, 8), (20.5, 12), (16.5, 16)], 2.2)
    elif name == "calendar":
        R(3, 5, 21, 21, 3, fill=False, w=2)
        R(3, 5, 21, 10, 2)
        R(3, 8, 21, 10, 0)
        L([(8, 3), (8, 6.5)], 2.2)
        L([(16, 3), (16, 6.5)], 2.2)
        for x in (6.5, 10.8, 15.1):
            for y in (12.5, 16.5):
                R(x, y, x + 2.6, y + 2.4, 0.6)
    elif name == "bell":
        E(5.5, 3.5, 18.5, 16.5)
        R(5.5, 10, 18.5, 17.5, 0)
        R(3.5, 16, 20.5, 18.5, 1.2)
        E(10, 18.5, 14, 22)
    elif name == "clock":
        E(3, 3, 21, 21, fill=False, w=2.2)
        L([(12, 7), (12, 12.5), (15.5, 14.5)], 2.2)
    elif name == "clipboard":
        R(4.5, 4.5, 19.5, 21.5, 2.5, fill=False, w=2.2)
        R(8.5, 2.5, 15.5, 6.5, 1.5)
        L([(8, 13.5), (11, 16.5), (16.5, 10.5)], 2.4)
    elif name == "alert":
        L([(12, 5), (12, 13.5)], 3.6)
        E(10.1, 16.5, 13.9, 20.3)
    elif name == "pot":
        POLY(_petal(12, 12.5, 9, 5.2, -125), col=c)
        POLY(_petal(12, 12.5, 9, 5.2, -55), col=c)
        R(5, 12, 19, 15, 1.2)
        POLY([(6.3, 15), (17.7, 15), (16.3, 21.5), (7.7, 21.5)])
    elif name == "leaf":
        POLY(_petal(4, 20, 19, 11, -45))
        L([(5, 19), (14.5, 9.5)], 1.4)
        L([(14.5, 9.5), (14.5, 9.5)], 1.4)
        d.line([P(5, 19), P(14, 10)], fill=clear, width=max(1, int(1.2 * k)))
    elif name == "drop":
        pts = [(12, 2.5)]
        for i in range(0, 31):
            a = math.radians(-35 + 250 * i / 30)
            pts.append((12 + 6.5 * math.cos(a), 14.5 + 6.5 * math.sin(a)))
        # order: right side down, bottom, left side up
        pts = [(12, 2.5)] + [(12 + 6.5 * math.cos(math.radians(a)),
                              14.5 + 6.5 * math.sin(math.radians(a)))
                             for a in range(-40, 221, 8)]
        POLY(pts)
        E(8.4, 13, 10.6, 17.5, col=clear)
    elif name == "flask":
        POLY([(9, 3), (15, 3), (15, 9), (20, 19), (18.8, 21), (5.2, 21), (4, 19), (9, 9)])
        POLY([(7.2, 14.5), (16.8, 14.5), (18.6, 18.6), (17.8, 19.6), (6.2, 19.6), (5.4, 18.6)],
             col=clear)
        POLY([(8, 15.5), (16, 15.5), (17.4, 18.6), (6.6, 18.6)])
    elif name == "scissors":
        E(3, 14, 10, 21, fill=False, w=2.2)
        E(14, 14, 21, 21, fill=False, w=2.2)
        L([(8.6, 15.2), (18, 3)], 2.2)
        L([(15.4, 15.2), (6, 3)], 2.2)
    elif name == "sprout":
        L([(12, 21), (12, 11)], 2.2)
        POLY(_petal(12, 12, 9.5, 6, -150))
        POLY(_petal(12, 10.5, 10.5, 6.5, -35))
        R(5, 19.5, 19, 21.8, 1.1)
    elif name == "star":
        pts = []
        for i in range(10):
            r = 9.8 if i % 2 == 0 else 4.3
            a = math.radians(-90 + 36 * i)
            pts.append((12 + r * math.cos(a), 12.8 + r * math.sin(a)))
        POLY(pts)
    elif name == "flag":
        L([(5.5, 3), (5.5, 21.5)], 2.4)
        POLY([(6, 3.5), (19.5, 3.5), (16, 8.5), (19.5, 13.5), (6, 13.5)])
    elif name == "repeat":
        ARC(4, 4, 20, 20, 200, 340, 2.4)
        ARC(4, 4, 20, 20, 20, 160, 2.4)
        POLY([(19.6, 5.2), (20.8, 10.8), (15.4, 9.6)])
        POLY([(4.4, 18.8), (3.2, 13.2), (8.6, 14.4)])
    elif name == "notes":
        R(4.5, 3, 19.5, 21, 2.5, fill=False, w=2.2)
        for y in (8.5, 12.5, 16.5):
            L([(8.5, y), (15.5, y)], 1.8)
    elif name == "camera":
        R(2.5, 7, 21.5, 20, 3)
        R(8, 4.5, 16, 8.5, 1.5)
        E(7.5, 9, 16.5, 18, col=clear)
        E(9.6, 11.1, 14.4, 15.9)
    elif name == "image":
        R(2.5, 4.5, 21.5, 19.5, 2.5, fill=False, w=2)
        POLY([(4.5, 18), (10, 11), (13.5, 15), (16, 12.5), (20, 18)])
        E(14.5, 6.8, 18, 10.3)
    elif name == "trash":
        L([(4, 6.5), (20, 6.5)], 2.2)
        L([(9.5, 6), (9.5, 3.5), (14.5, 3.5), (14.5, 6)], 2)
        L([(6, 7), (7.2, 20.5), (16.8, 20.5), (18, 7)], 2.2)
        L([(10.2, 10.5), (10.2, 17)], 1.8)
        L([(13.8, 10.5), (13.8, 17)], 1.8)
    elif name == "edit":
        POLY([(15.5, 3.5), (20.5, 8.5), (9, 20), (4, 20), (4, 15)])
        POLY([(13.4, 6.6), (17.4, 10.6), (16.2, 11.8), (12.2, 7.8)], col=clear)
    elif name == "check":
        L([(4.5, 12.5), (9.8, 17.8), (19.5, 6.5)], 3)
    elif name == "user":
        E(7.5, 3, 16.5, 12)
        d.chord((*P(3.5, 13.5), *P(20.5, 30)), 180, 360, fill=c)
    elif name == "lock":
        ARC(7, 3, 17, 13, 180, 360, 2.4)
        L([(7, 8), (7, 11)], 2.4)
        L([(17, 8), (17, 11)], 2.4)
        R(4.5, 10.5, 19.5, 21, 2.5)
        E(10.6, 14, 13.4, 16.8, col=clear)
    elif name == "sort":
        L([(4, 6), (14, 6)], 2.2)
        L([(4, 12), (11, 12)], 2.2)
        L([(4, 18), (8, 18)], 2.2)
        L([(18, 4), (18, 20)], 2.2)
        L([(15, 17), (18, 20.3), (21, 17)], 2.2)
    elif name == "dots":
        for y in (5, 12, 19):
            E(10.2, y - 1.8, 13.8, y + 1.8)
    elif name == "trophy":
        R(7, 3, 17, 5, 0.5)
        d.chord((*P(6.5, -4), *P(17.5, 14.5)), 0, 180, fill=c)
        ARC(2.5, 4.5, 9, 12, 90, 270, 1.8)
        ARC(15, 4.5, 21.5, 12, 270, 90, 1.8)
        R(10.7, 13.5, 13.3, 17.5, 0.4)
        R(7.5, 17.5, 16.5, 20.5, 1.2)
    elif name == "bulb":
        E(5, 2.5, 19, 16.5, fill=False, w=2.2)
        L([(9.5, 16), (9.5, 18), (14.5, 18), (14.5, 16)], 2.2)
        L([(10, 21), (14, 21)], 2.2)
        L([(12, 7), (10.5, 10.5), (13.5, 10.5), (12, 14)], 1.6)
    elif name == "close":
        L([(6, 6), (18, 18)], 2.6)
        L([(18, 6), (6, 18)], 2.6)
    elif name == "filter":
        POLY([(3, 4), (21, 4), (14, 12.5), (14, 20), (10, 18), (10, 12.5)])
    elif name == "upload":
        L([(12, 15), (12, 3.5)], 2.4)
        L([(7, 8.5), (12, 3.5), (17, 8.5)], 2.4)
        L([(4, 14.5), (4, 20), (20, 20), (20, 14.5)], 2.4)
    elif name == "list":
        for y in (6, 12, 18):
            E(3, y - 1.5, 6, y + 1.5)
            L([(9, y), (21, y)], 2.2)
    elif name == "pending":
        E(3, 3, 21, 21, fill=False, w=2.2)
        for x in (8, 12, 16):
            E(x - 1.3, 10.7, x + 1.3, 13.3)
    else:                                   # unknown name: small dot
        E(9, 9, 15, 15)


def icon_pil(name, size, colour, clear=(0, 0, 0, 0)):
    S = size * 4
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_icon(name, d, S / 24.0, hex_rgb(colour), clear)
    return img.resize((size, size), Image.LANCZOS)


def icon(name, size=18, colour="#1f4d36"):
    """Cached Tk image of a drawn icon (None if Pillow is missing)."""
    if not PIL_OK:
        return None
    k = _key("icon", name, size, colour)
    if k not in _cache:
        _cache[k] = photo(icon_pil(name, size, colour))
    return _cache[k]


def badge(name, size, circle, colour, scale=0.52):
    """Icon inside a filled circle (stat cards, list rows)."""
    if not PIL_OK:
        return None
    k = _key("badge", name, size, circle, colour, scale)
    if k not in _cache:
        S = size * SS
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(img).ellipse((0, 0, S - 1, S - 1), fill=hex_rgb(circle))
        img = img.resize((size, size), Image.LANCZOS)
        inner = max(6, int(size * scale))
        ic = icon_pil(name, inner, colour, clear=hex_rgb(circle))
        img.alpha_composite(ic, ((size - inner) // 2, (size - inner) // 2))
        _cache[k] = photo(img)
    return _cache[k]


TASK_ICON_NAMES = {"Watering": "drop", "Fertilizing": "flask", "Pruning": "scissors",
                   "Repotting": "pot", "Other": "leaf"}
TASK_ICON_COLOURS = {"Watering": "#3b8fd6", "Fertilizing": "#8a6bb8", "Pruning": "#c56b4a",
                     "Repotting": "#b9793d", "Other": "#4f8a4f"}
PRIORITY_FLAG = {"Urgent": "#d64545", "Overdue": "#8e2a2a", "Routine": "#d9a32e",
                 "Optional": "#5d9d69"}