"""Deterministic UI-graphics renderer for the Folks (software tips) channel.

Draws crisp, text-accurate dark-mode tech scenes with PIL so keycap labels,
window titles and menu items are always legible (openjourney/SD1.5 cannot
render text).  Each scene is 1080x960 and designed so the lower third stays
clear for the word-level caption overlay.

Scenes are data-driven: every video variant maps to a list of scene ``spec``
dicts (``type`` + params), so adding a new short only requires a spec list.

Usage:
    python -m app.video.ui_graphics folks <data_dir> <variant>
"""

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

CANVAS = (1080, 960)

# Palette
BG_TOP = (15, 18, 23)
BG_BOTTOM = (18, 28, 36)
PANEL = (26, 35, 50)
PANEL_EDGE = (55, 72, 96)
KEY_FILL = (31, 41, 55)
KEY_EDGE = (60, 75, 95)
KEY_PRESSED = (17, 23, 32)
TEXT = (230, 237, 243)
TEXT_DIM = (120, 136, 153)
CYAN = (34, 211, 238)
RED = (248, 113, 113)
GREEN = (52, 211, 153)
YELLOW = (250, 204, 21)
ORANGE = (251, 146, 60)

COLORS = {
    "red": RED,
    "cyan": CYAN,
    "green": GREEN,
    "yellow": YELLOW,
    "orange": ORANGE,
    "dim": TEXT_DIM,
    "white": TEXT,
    "blue": (96, 165, 250),
}

_FONT_DIR = r"C:\Windows\Fonts"


def _font(size: int, bold: bool = True):
    name = "consolab.ttf" if bold else "consola.ttf"
    return ImageFont.truetype(os.path.join(_FONT_DIR, name), size)


def _bg() -> Image.Image:
    img = Image.new("RGB", CANVAS, BG_TOP)
    d = ImageDraw.Draw(img)
    for y in range(CANVAS[1]):
        t = y / CANVAS[1]
        r = round(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = round(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = round(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        d.line([(0, y), (CANVAS[0], y)], fill=(r, g, b))
    grid = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for x in range(0, CANVAS[0], 72):
        gd.line([(x, 0), (x, CANVAS[1])], fill=(120, 160, 200, 10))
    for y in range(0, CANVAS[1], 72):
        gd.line([(0, y), (CANVAS[0], y)], fill=(120, 160, 200, 10))
    img = Image.alpha_composite(img.convert("RGBA"), grid).convert("RGB")
    return img


def _glow(img, center, radius, color, alpha):
    layer = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse(
        [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
        fill=(*color, alpha),
    )
    layer = layer.filter(ImageFilter.GaussianBlur(radius // 2))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def _rounded(d, box, radius, fill, outline=None, width=1):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _headline(img, text, color):
    d = ImageDraw.Draw(img)
    f = _font(42)
    tw = d.textlength(text, font=f)
    x = (CANVAS[0] - tw) // 2
    y = 36
    d.text((x + 2, y + 2), text, font=f, fill=(0, 0, 0))
    d.text((x, y), text, font=f, fill=color)
    d.line([(CANVAS[0] // 2 - 60, y + 66), (CANVAS[0] // 2 + 60, y + 66)], fill=color, width=3)
    return img


# --------------------------------------------------------------------------
# Keyboard
# --------------------------------------------------------------------------

KEY_LAYOUT = [
    ["Esc", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"],
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "Backspace"],
    ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\"],
    ["Caps", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "Enter"],
    ["Shift", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "Shift"],
    ["Ctrl", "Win", "Alt", "Space", "Alt", "Win", "Menu", "Ctrl"],
]

KEY_W, KEY_H, GAP = 60, 42, 6


def _draw_keyboard(img, top=300, highlights=(), pressed=(), dim=()):
    d = ImageDraw.Draw(img)
    rows = KEY_LAYOUT
    board_w = max(len(r) for r in rows) * (KEY_W + GAP) + GAP
    x0 = (CANVAS[0] - board_w) // 2
    y0 = top

    _rounded(d, (x0 - 26, y0 - 22, x0 + board_w + 26, y0 + len(rows) * (KEY_H + GAP) + 18),
             radius=22, fill=PANEL, outline=PANEL_EDGE, width=2)

    for r_i, row in enumerate(rows):
        row_w = len(row) * (KEY_W + GAP) - GAP
        rx = x0 + (board_w - row_w) // 2
        for k_i, label in enumerate(row):
            kw = KEY_W
            if label in ("Backspace", "Enter", "Shift", "Caps", "Space"):
                kw = KEY_W * 2 + GAP
            if label == "Space":
                kw = KEY_W * 4 + GAP * 3
            x = rx + k_i * (KEY_W + GAP)
            y = y0 + r_i * (KEY_H + GAP)
            key = label.lower()
            box = (x, y, x + kw, y + KEY_H)
            is_pressed = key in pressed
            is_hi = key in highlights
            is_dim = key in dim

            if is_pressed:
                box = (x + 2, y + 3, x + kw + 2, y + KEY_H + 3)
                _rounded(d, (x, y - 3, x + kw, y + KEY_H - 2), radius=8, fill=KEY_PRESSED)
            if is_hi:
                _rounded(d, box, radius=8, fill=(*CYAN, 255), outline=(200, 240, 255), width=2)
            elif is_dim:
                _rounded(d, box, radius=8, fill=KEY_PRESSED, outline=(40, 50, 66), width=1)
            else:
                _rounded(d, box, radius=8, fill=KEY_FILL, outline=KEY_EDGE, width=1)

            label_color = (12, 24, 34) if is_hi else (TEXT if not is_dim else TEXT_DIM)
            f = _font(21)
            fsize = f.getbbox(label)
            lw = (fsize[2] - fsize[0])
            lh = (fsize[3] - fsize[1])
            lx = x + (kw - lw) / 2 - fsize[0]
            ly = y + (KEY_H - lh) / 2 - fsize[1] + (3 if is_pressed else 0)
            d.text((lx, ly), label, font=f, fill=label_color)
    return img


# --------------------------------------------------------------------------
# Windows, menus, dialogs, meters
# --------------------------------------------------------------------------

def _window(img, box, title, rows, highlight_label=None, accent=CYAN,
            columns=("Name", "Status", "CPU", "Memory"), tabs=None, tab_highlight=None):
    d = ImageDraw.Draw(img)
    if not columns:
        columns = ("Name", "Status", "CPU", "Memory")
    x, y, w, h = box
    _rounded(d, (x, y, x + w, y + h), radius=16, fill=PANEL, outline=PANEL_EDGE, width=2)
    _rounded(d, (x + 1, y + 1, x + w - 1, y + 42), radius=15, fill=(34, 46, 64))
    for i, c in enumerate(["#f87171", "#facc15", "#34d399"]):
        d.ellipse([x + 14 + i * 24, y + 14, x + 24 + i * 24, y + 24], fill=c)
    d.text((x + 100, y + 11), title, font=_font(24), fill=TEXT)

    head_y = y + 82
    if tabs:
        ty = y + 52
        tx = x + 14
        tf = _font(20)
        for t in tabs:
            hi = (t == tab_highlight)
            d.text((tx, ty + 6), t, font=tf, fill=accent if hi else TEXT_DIM)
            if hi:
                d.line([(tx, ty + 34), (tx + d.textlength(t, font=tf) + 2, ty + 34)], fill=accent, width=3)
            tx += d.textlength(t, font=tf) + 26
        head_y = y + 104

    col_w = (w - 24) / len(columns)
    for i, cname in enumerate(columns):
        d.text((x + 14 + i * col_w, head_y), cname, font=_font(20), fill=TEXT_DIM)
    for idx, row in enumerate(rows):
        ry = head_y + 30 + idx * 38
        if highlight_label and row[0].lower() == highlight_label.lower():
            _rounded(d, (x + 8, ry - 3, x + w - 8, ry + 30), radius=8, fill=(*accent, 34), outline=accent, width=1)
        for i, val in enumerate(row):
            col = TEXT if not (highlight_label and row[0].lower() == highlight_label.lower()) else accent
            d.text((x + 14 + i * col_w, ry), str(val), font=_font(22), fill=col)
    return img


def _context_menu(img, box, items, highlight=None, accent=RED):
    d = ImageDraw.Draw(img)
    x, y, w, h = box
    _rounded(d, (x, y, x + w, y + h), radius=12, fill=(24, 33, 48), outline=PANEL_EDGE, width=2)
    for i, item in enumerate(items):
        iy = y + 14 + i * 40
        if highlight and item.lower() == highlight.lower():
            _rounded(d, (x + 8, iy - 3, x + w - 8, iy + 30), radius=7, fill=(*accent, 36), outline=accent, width=1)
            d.text((x + 18, iy), item, font=_font(24), fill=accent)
        else:
            d.text((x + 18, iy), item, font=_font(24), fill=TEXT)
    return img


def _progress_bar(d, box, pct, color, label=None):
    x0, y0, x1, y1 = box
    _rounded(d, box, radius=8, fill=(20, 27, 38), outline=PANEL_EDGE, width=1)
    fw = int((x1 - x0) * max(0.0, min(1.0, pct)))
    if fw > 0:
        d.rounded_rectangle((x0 + 2, y0 + 2, x0 + fw, y1 - 2), radius=6, fill=color)
    if label:
        d.text((x0, y1 + 10), label, font=_font(28), fill=color)


def _storage_meter(d, cx, cy, w, pct, color):
    h = 46
    x0, y0 = cx - w // 2, cy - h // 2
    _rounded(d, (x0, y0, x0 + w, y0 + h), radius=12, fill=(20, 27, 38), outline=PANEL_EDGE, width=2)
    fw = int(w * max(0.0, min(1.0, pct)))
    if fw > 0:
        d.rounded_rectangle((x0 + 2, y0 + 2, x0 + fw, y0 + h - 2), radius=10, fill=color)
    f = _font(30)
    txt = f"{int(round(pct * 100))}%"
    tw = d.textlength(txt, font=f)
    d.text((cx - tw / 2, y0 + h + 8), txt, font=f, fill=color)


def _run_dialog(d, box, value, title="Run"):
    x, y, w, h = box
    _rounded(d, box, radius=14, fill=PANEL, outline=PANEL_EDGE, width=2)
    _rounded(d, (x + 1, y + 1, x + w - 1, y + 40), radius=13, fill=(34, 46, 64))
    d.text((x + 14, y + 10), title, font=_font(22), fill=TEXT)
    _rounded(d, (x + 14, y + 58, x + w - 14, y + 100), radius=6, fill=(15, 21, 30), outline=CYAN, width=2)
    d.text((x + 22, y + 62), value, font=_font(24), fill=CYAN)
    d.text((x + 14, y + 118), "OK            Cancel", font=_font(20), fill=TEXT_DIM)


def _explorer(d, box, title, files, selected=()):
    x, y, w, h = box
    _rounded(d, box, radius=14, fill=PANEL, outline=PANEL_EDGE, width=2)
    _rounded(d, (x + 1, y + 1, x + w - 1, y + 40), radius=13, fill=(34, 46, 64))
    for i, c in enumerate(["#f87171", "#facc15", "#34d399"]):
        d.ellipse([x + 14 + i * 24, y + 14, x + 24 + i * 24, y + 24], fill=c)
    d.text((x + 100, y + 11), title, font=_font(22), fill=TEXT)
    for idx, name in enumerate(files):
        ry = y + 52 + idx * 40
        sel = name in selected
        if sel:
            _rounded(d, (x + 10, ry - 2, x + w - 10, ry + 32), radius=7, fill=(*CYAN, 40), outline=CYAN, width=1)
        d.text((x + 20, ry), name, font=_font(22), fill=CYAN if sel else TEXT)


def _trash(d, cx, cy, s=1.0):
    w, h = int(150 * s), int(170 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    _rounded(d, (x0 + 20 * s, y0, x0 + w - 20 * s, y0 + 24 * s), radius=6, fill=PANEL_EDGE)
    d.rectangle([x0, y0 + 24 * s, x0 + w, y0 + h], fill=(52, 66, 88), outline=PANEL_EDGE, width=2)
    for i in range(3):
        d.line([(x0 + 34 * s + i * 40 * s, y0 + 46 * s), (x0 + 34 * s + i * 40 * s, y0 + h - 28 * s)],
               fill=PANEL_EDGE, width=8)


# --------------------------------------------------------------------------
# Icon library
# --------------------------------------------------------------------------

def _ic_clipboard(d, cx, cy, color, s, ok):
    w, h = int(150 * s), int(180 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    _rounded(d, (x0, y0, x0 + w, y0 + h), radius=14, fill=(40, 52, 72), outline=PANEL_EDGE, width=2)
    d.rounded_rectangle((x0 + 40 * s, y0 - 18 * s, x0 + w - 40 * s, y0 + 10 * s),
                        radius=6, fill=(66, 84, 110), outline=PANEL_EDGE, width=2)
    for ly in range(3):
        d.line([(x0 + 24 * s, y0 + 48 * s + ly * 34 * s), (x0 + w - 24 * s, y0 + 48 * s + ly * 34 * s)],
               fill=PANEL_EDGE, width=6)
    if ok is True:
        d.line([(x0 + 36 * s, y0 + 96 * s), (x0 + 68 * s, y0 + 128 * s)], fill=GREEN, width=16)
        d.line([(x0 + 68 * s, y0 + 128 * s), (x0 + 120 * s, y0 + 64 * s)], fill=GREEN, width=16)
    elif ok is False:
        d.line([(x0 + 34 * s, y0 + 44 * s), (x0 + w - 34 * s, y0 + h - 44 * s)], fill=RED, width=14)


def _ic_bookmark(d, cx, cy, color, s, ok):
    w, h = int(130 * s), int(170 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    d.polygon([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (cx, y0 + h - 46 * s), (x0, y0 + h)], fill=color)
    d.line([(x0, y0), (x0 + w, y0)], fill=(255, 220, 170), width=4)


def _ic_lightning(d, cx, cy, color, s, ok):
    pts = [(cx - 34 * s, cy - 70 * s), (cx + 26 * s, cy - 70 * s),
           (cx + 6 * s, cy - 6 * s), (cx + 44 * s, cy - 6 * s),
           (cx - 30 * s, cy + 74 * s), (cx - 12 * s, cy + 8 * s), (cx - 52 * s, cy + 8 * s)]
    d.polygon(pts, fill=color)


def _ic_bell(d, cx, cy, color, s, ok):
    d.ellipse([cx - 26 * s, cy - 26 * s, cx + 26 * s, cy + 26 * s], fill=TEXT_DIM)
    d.polygon([(cx - 30 * s, cy - 8 * s), (cx - 16 * s, cy - 26 * s), (cx + 16 * s, cy - 26 * s),
               (cx + 30 * s, cy - 8 * s)], fill=color)
    d.polygon([(cx - 12 * s, cy + 20 * s), (cx + 12 * s, cy + 20 * s), (cx + 6 * s, cy + 30 * s),
               (cx - 6 * s, cy + 30 * s)], fill=color)


def _ic_trash(d, cx, cy, color, s, ok):
    w, h = int(150 * s), int(170 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    _rounded(d, (x0 + 20 * s, y0, x0 + w - 20 * s, y0 + 24 * s), radius=6, fill=PANEL_EDGE)
    d.rectangle([x0, y0 + 24 * s, x0 + w, y0 + h], fill=color, outline=PANEL_EDGE, width=2)
    for i in range(3):
        d.line([(x0 + 34 * s + i * 40 * s, y0 + 46 * s), (x0 + 34 * s + i * 40 * s, y0 + h - 28 * s)],
               fill=(12, 18, 26), width=8)


def _ic_battery(d, cx, cy, color, s, ok):
    w, h = int(210 * s), int(96 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    _rounded(d, (x0, y0, x0 + w, y0 + h), radius=10, fill=(40, 52, 72), outline=PANEL_EDGE, width=3)
    d.rounded_rectangle((x0 + w + 8 * s, y0 + 24 * s, x0 + w + 28 * s, y0 + h - 24 * s),
                        radius=4, fill=PANEL_EDGE)
    pct = ok if isinstance(ok, (int, float)) else 0.5
    fw = int((w - 16 * s) * max(0.0, min(1.0, pct)))
    if fw > 0:
        d.rounded_rectangle((x0 + 8 * s, y0 + 8 * s, x0 + 8 * s + fw, y0 + h - 8 * s), radius=6, fill=color)


def _ic_wifi(d, cx, cy, color, s, ok):
    w = int(260 * s)
    x0, y0 = cx - w // 2, cy - w // 2
    if ok is False:
        _rounded(d, (x0 - 12, y0 - 12, x0 + w + 12, y0 + w + 12), radius=24, fill=PANEL, outline=RED, width=3)
    for r, width in ((80, 14), (58, 14), (36, 12)):
        d.arc([cx - r * s, cy - r * s, cx + r * s, cy + r * s], 180, 360, fill=color, width=int(width * s))
    d.ellipse([cx - 14 * s, cy - 14 * s, cx + 14 * s, cy + 14 * s], fill=color)
    if ok is False:
        d.line([(x0, y0 + w + 12), (x0 + w, y0 - 12)], fill=RED, width=12)


def _ic_speaker(d, cx, cy, color, s, ok):
    d.polygon([(cx - 34 * s, cy - 34 * s), (cx - 34 * s, cy + 34 * s), (cx + 26 * s, cy + 34 * s),
               (cx + 70 * s, cy + 80 * s), (cx + 70 * s, cy - 80 * s)], fill=color)
    for r, width in ((74, 10), (106, 10)):
        d.arc([cx + 24 * s - r * s, cy - r * s, cx + 24 * s + r * s, cy + r * s],
              -45, 45, fill=color, width=int(width * s))
    if ok is False:
        d.line([(cx - 80 * s, cy - 80 * s), (cx + 110 * s, cy + 90 * s)], fill=RED, width=12)


def _ic_mic(d, cx, cy, color, s, ok):
    w, h = int(72 * s), int(120 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=int(36 * s), fill=color)
    d.line([(cx, y0 + h), (cx, y0 + h + 50 * s)], fill=color, width=int(10 * s))
    d.arc([cx - 70 * s, y0 + h + 10 * s, cx + 70 * s, y0 + h + 120 * s], 0, 180, fill=color, width=int(10 * s))
    if ok is False:
        d.line([(cx - 90 * s, cy - 90 * s), (cx + 90 * s, cy + 90 * s)], fill=RED, width=12)


def _ic_printer(d, cx, cy, color, s, ok):
    w, h = int(220 * s), int(120 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    d.rounded_rectangle((x0, y0, x0 + w, y0 + 70 * s), radius=10, fill=(40, 52, 72), outline=PANEL_EDGE, width=3)
    d.rectangle([x0 + 20 * s, y0 + 30 * s, x0 + w - 20 * s, y0 + 70 * s], fill=color)
    d.rectangle([x0 + 30 * s, y0 + 70 * s, x0 + w - 30 * s, y0 + h], fill=color, outline=PANEL_EDGE, width=3)
    for i in range(2):
        d.line([(x0 + 52 * s + i * 62 * s, y0 + 88 * s), (x0 + 52 * s + i * 62 * s, y0 + 106 * s)],
               fill=(240, 240, 240), width=8)
    if ok is False:
        d.line([(x0 - 20 * s, y0 - 20 * s), (x0 + w + 20 * s, y0 + h + 20 * s)], fill=RED, width=12)


def _ic_search(d, cx, cy, color, s, ok):
    r = int(58 * s)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=int(10 * s))
    d.line([(cx + r * 0.72, cy + r * 0.72), (cx + r * 1.85, cy + r * 1.85)], fill=color, width=int(12 * s))
    if ok is False:
        d.line([(cx - r - 14 * s, cy - r - 14 * s), (cx + r + 14 * s, cy + r + 14 * s)], fill=RED, width=12)


def _ic_folder(d, cx, cy, color, s, ok):
    w, h = int(220 * s), int(150 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    d.polygon([(x0, y0 + 16 * s), (x0 + w * 0.4, y0 + 16 * s), (x0 + w * 0.55, y0 + 44 * s),
               (x0 + w, y0 + 44 * s), (x0 + w, y0 + h), (x0, y0 + h)], fill=color)


def _ic_file(d, cx, cy, color, s, ok):
    w, h = int(150 * s), int(190 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    d.polygon([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)], fill=(52, 66, 88))
    d.polygon([(x0 + w - 50 * s, y0), (x0 + w, y0), (x0 + w, y0 + 50 * s)], fill=PANEL_EDGE)
    for ly in range(3):
        d.line([(x0 + 24 * s, y0 + 72 * s + ly * 30 * s), (x0 + w - 24 * s, y0 + 72 * s + ly * 30 * s)],
               fill=PANEL_EDGE, width=6)
    if ok is False:
        d.line([(x0 + 20 * s, y0 + 24 * s), (x0 + w - 20 * s, y0 + h - 24 * s)], fill=RED, width=14)
    elif ok is True:
        d.line([(x0 + 30 * s, y0 + 100 * s), (x0 + 65 * s, y0 + 135 * s)], fill=GREEN, width=16)
        d.line([(x0 + 65 * s, y0 + 135 * s), (x0 + 120 * s, y0 + 70 * s)], fill=GREEN, width=16)


def _ic_mouse(d, cx, cy, color, s, ok):
    w, h = int(110 * s), int(170 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    _rounded(d, (x0, y0, x0 + w, y0 + h), radius=int(55 * s), fill=(40, 52, 72), outline=PANEL_EDGE, width=3)
    d.line([(cx, y0 + 8 * s), (cx, y0 + 70 * s)], fill=PANEL_EDGE, width=8)
    if ok is False:
        d.line([(x0 - 20 * s, y0 - 20 * s), (x0 + w + 20 * s, y0 + h + 20 * s)], fill=RED, width=12)


def _ic_gear(d, cx, cy, color, s, ok):
    r = int(50 * s)
    for i in range(8):
        a = i * 45 * math.pi / 180
        x1 = cx + int(r * math.cos(a)); y1 = cy + int(r * math.sin(a))
        x2 = cx + int((r + 16 * s) * math.cos(a)); y2 = cy + int((r + 16 * s) * math.sin(a))
        d.line([(x1, y1), (x2, y2)], fill=color, width=int(10 * s))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=int(12 * s))
    d.ellipse([cx - 14 * s, cy - 14 * s, cx + 14 * s, cy + 14 * s], fill=color)


def _ic_shield(d, cx, cy, color, s, ok):
    w, h = int(180 * s), int(210 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    d.polygon([(cx, y0), (x0 + w, y0 + 26 * s), (x0 + w - 14 * s, y0 + h - 40 * s),
               (cx, y0 + h), (x0 + 14 * s, y0 + h - 40 * s), (x0, y0 + 26 * s)], fill=color)
    if ok:
        d.line([(cx - 40 * s, y0 + 110 * s), (cx - 10 * s, y0 + 150 * s)], fill=(10, 18, 26), width=int(14 * s))
        d.line([(cx - 10 * s, y0 + 150 * s), (cx + 45 * s, y0 + 80 * s)], fill=(10, 18, 26), width=int(14 * s))


def _ic_camera(d, cx, cy, color, s, ok):
    w, h = int(220 * s), int(150 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    _rounded(d, (x0, y0, x0 + w, y0 + h), radius=18, fill=(40, 52, 72), outline=PANEL_EDGE, width=3)
    d.polygon([(cx - 46 * s, y0 - 26 * s), (cx - 46 * s, y0), (x0 + 46 * s, y0 + 46 * s),
               (x0 + w - 46 * s, y0 + 46 * s), (cx + 46 * s, y0), (cx + 46 * s, y0 - 26 * s)], fill=color)
    d.ellipse([cx - 34 * s, cy - 34 * s, cx + 34 * s, cy + 34 * s], outline=color, width=int(10 * s))
    if ok is False:
        d.line([(x0, y0), (x0 + w, y0 + h)], fill=RED, width=12)


def _ic_emoji(d, cx, cy, color, s, ok):
    r = int(76 * s)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=int(12 * s))
    d.ellipse([cx - 34 * s, cy - 30 * s, cx - 12 * s, cy - 8 * s], fill=color)
    d.ellipse([cx + 12 * s, cy - 30 * s, cx + 34 * s, cy - 8 * s], fill=color)
    d.arc([cx - 45 * s, cy - 30 * s, cx + 45 * s, cy + 70 * s], 20, 160, fill=color, width=int(10 * s))


def _ic_monitor(d, cx, cy, color, s, ok):
    w, h = int(240 * s), int(150 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    fill = (30, 60, 90) if ok == "blue" else (40, 52, 72)
    _rounded(d, (x0, y0, x0 + w, y0 + h), radius=12, fill=fill, outline=PANEL_EDGE, width=3)
    d.line([(cx, y0 + h), (cx, y0 + h + 40 * s)], fill=PANEL_EDGE, width=10)
    d.line([(cx - 80 * s, y0 + h + 40 * s), (cx + 80 * s, y0 + h + 40 * s)], fill=PANEL_EDGE, width=10)
    if ok == "blue":
        d.text((cx - 90 * s, cy - 24 * s), ":(", font=_font(int(60 * s)), fill=TEXT)


def _ic_rocket(d, cx, cy, color, s, ok):
    w, h = int(120 * s), int(200 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    d.polygon([(cx, y0), (x0 + w, y0 + 70 * s), (cx, y0 + h), (x0, y0 + 70 * s)], fill=color)
    d.ellipse([cx - 16 * s, y0 + 80 * s, cx + 16 * s, y0 + 112 * s], fill=(10, 18, 26))
    d.polygon([(cx - 20 * s, y0 + h), (cx + 20 * s, y0 + h), (cx, y0 + h + 40 * s)], fill=ORANGE)
    d.line([(x0 + 12 * s, y0 + 62 * s), (x0 - 20 * s, y0 + 72 * s)], fill=PANEL_EDGE, width=8)
    d.line([(x0 + w - 12 * s, y0 + 62 * s), (x0 + w + 20 * s, y0 + 72 * s)], fill=PANEL_EDGE, width=8)


def _ic_globe(d, cx, cy, color, s, ok):
    r = int(70 * s)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=int(10 * s))
    d.arc([cx - r, cy - r, cx + r, cy + r], -60, 60, fill=color, width=4)
    d.arc([cx - r, cy - r, cx + r, cy + r], 120, 240, fill=color, width=4)
    d.line([(cx - r, cy), (cx + r, cy)], fill=color, width=4)
    if ok is False:
        d.line([(cx - r - 20 * s, cy - r - 20 * s), (cx + r + 20 * s, cy + r + 20 * s)], fill=RED, width=12)


def _ic_hourglass(d, cx, cy, color, s, ok):
    w, h = int(130 * s), int(190 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    d.line([(x0, y0), (x0 + w, y0)], fill=color, width=int(8 * s))
    d.line([(x0, y0 + h), (x0 + w, y0 + h)], fill=color, width=int(8 * s))
    d.line([(x0, y0), (cx, y0 + h // 2)], fill=color, width=int(8 * s))
    d.line([(x0 + w, y0), (cx, y0 + h // 2)], fill=color, width=int(8 * s))
    d.line([(x0, y0 + h), (cx, y0 + h // 2)], fill=color, width=int(8 * s))
    d.line([(x0 + w, y0 + h), (cx, y0 + h // 2)], fill=color, width=int(8 * s))


def _ic_check_circle(d, cx, cy, color, s, ok):
    r = int(76 * s)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=int(12 * s))
    d.line([(cx - 30 * s, cy + 6 * s), (cx - 8 * s, cy + 30 * s)], fill=color, width=int(16 * s))
    d.line([(cx - 8 * s, cy + 30 * s), (cx + 32 * s, cy - 22 * s)], fill=color, width=int(16 * s))


def _ic_cross_circle(d, cx, cy, color, s, ok):
    r = int(76 * s)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=int(12 * s))
    d.line([(cx - 28 * s, cy - 28 * s), (cx + 28 * s, cy + 28 * s)], fill=color, width=int(14 * s))
    d.line([(cx + 28 * s, cy - 28 * s), (cx - 28 * s, cy + 28 * s)], fill=color, width=int(14 * s))


def _ic_stop(d, cx, cy, color, s, ok):
    r = int(70 * s)
    pts = []
    for i in range(8):
        a = (i * 45 + 22.5) * math.pi / 180
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=color)
    d.rectangle([cx - 28 * s, cy - 28 * s, cx + 28 * s, cy + 28 * s], fill=(12, 18, 26))


def _ic_download(d, cx, cy, color, s, ok):
    w, h = int(120 * s), int(140 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    d.line([(cx, y0), (cx, y0 + h)], fill=color, width=int(14 * s))
    d.polygon([(cx - 40 * s, y0 + h - 70 * s), (cx + 40 * s, y0 + h - 70 * s), (cx, y0 + h)], fill=color)
    d.rectangle([x0, y0 + h, x0 + w, y0 + h + 20 * s], fill=color)


def _ic_text(d, cx, cy, color, s, ok):
    d.text((cx - 74 * s, cy - 74 * s), "Aa", font=_font(int(116 * s)), fill=color)


def _ic_alert(d, cx, cy, color, s, ok):
    w, h = int(200 * s), int(180 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    d.polygon([(cx, y0), (x0 + w, y0 + h), (x0, y0 + h)], fill=color)
    d.line([(cx, y0 + 60 * s), (cx, y0 + 120 * s)], fill=(10, 18, 26), width=int(14 * s))
    d.ellipse([cx - 10 * s, y0 + 138 * s, cx + 10 * s, y0 + 158 * s], fill=(10, 18, 26))


def _ic_bluetooth(d, cx, cy, color, s, ok):
    d.line([(cx - 30 * s, cy - 100 * s), (cx - 30 * s, cy + 100 * s)], fill=color, width=int(10 * s))
    d.line([(cx - 30 * s, cy - 100 * s), (cx + 40 * s, cy - 40 * s), (cx - 30 * s, cy),
            (cx + 40 * s, cy + 40 * s), (cx - 30 * s, cy + 100 * s)], fill=color, width=int(12 * s), joint="curve")


def _ic_harddrive(d, cx, cy, color, s, ok):
    w, h = int(250 * s), int(160 * s)
    x0, y0 = cx - w // 2, cy - h // 2
    _rounded(d, (x0, y0, x0 + w, y0 + h), radius=16, fill=(40, 52, 72), outline=PANEL_EDGE, width=3)
    if isinstance(ok, (int, float)):
        pct = max(0.0, min(1.0, ok))
        fw = int((w - 16 * s) * pct)
        if fw > 0:
            d.rounded_rectangle((x0 + 8 * s, y0 + 8 * s, x0 + 8 * s + fw, y0 + h - 8 * s), radius=10, fill=color)
    else:
        d.ellipse([cx - 30 * s, cy - 14 * s, cx + 30 * s, cy + 14 * s], fill=color)


def _ic_pointer(d, cx, cy, color, s, ok):
    pts = [(cx, cy - 70 * s), (cx, cy + 50 * s), (cx + 34 * s, cy + 20 * s), (cx + 90 * s, cy + 80 * s),
           (cx + 116 * s, cy + 58 * s), (cx + 58 * s, cy - 4 * s), (cx + 78 * s, cy - 14 * s)]
    d.polygon(pts, fill=color)


_ICONS = {
    "clipboard": _ic_clipboard,
    "bookmark": _ic_bookmark,
    "lightning": _ic_lightning,
    "bell": _ic_bell,
    "trash": _ic_trash,
    "battery": _ic_battery,
    "wifi": _ic_wifi,
    "speaker": _ic_speaker,
    "mic": _ic_mic,
    "printer": _ic_printer,
    "search": _ic_search,
    "folder": _ic_folder,
    "file": _ic_file,
    "mouse": _ic_mouse,
    "gear": _ic_gear,
    "shield": _ic_shield,
    "camera": _ic_camera,
    "emoji": _ic_emoji,
    "monitor": _ic_monitor,
    "rocket": _ic_rocket,
    "globe": _ic_globe,
    "hourglass": _ic_hourglass,
    "check_circle": _ic_check_circle,
    "cross_circle": _ic_cross_circle,
    "stop": _ic_stop,
    "download": _ic_download,
    "text": _ic_text,
    "alert": _ic_alert,
    "bluetooth": _ic_bluetooth,
    "harddrive": _ic_harddrive,
    "pointer": _ic_pointer,
}


def _icon(d, cx, cy, name, color, s=1.0, ok=None):
    fn = _ICONS.get(name)
    if fn:
        fn(d, cx, cy, color, s, ok)


# --------------------------------------------------------------------------
# Generic scene builders (dispatch on spec["type"])
# --------------------------------------------------------------------------

def _build_icon(spec):
    img = _bg()
    color = COLORS[spec.get("color", "red")]
    img = _glow(img, (CANVAS[0] // 2, 470), spec.get("glow", 320), color, 40)
    _headline(img, spec["headline"], color)
    d = ImageDraw.Draw(img)
    _icon(d, CANVAS[0] // 2, 470, spec["icon"], color, s=spec.get("s", 1.3), ok=spec.get("ok"))
    sub = spec.get("sub")
    if sub:
        f = _font(28)
        tw = d.textlength(sub, font=f)
        d.text(((CANVAS[0] - tw) / 2, 680), sub, font=f, fill=COLORS[spec.get("sub_color", "dim")])
    return img


def _build_keyboard(spec):
    img = _bg()
    color = COLORS[spec.get("color", "cyan")]
    img = _glow(img, (CANVAS[0] // 2, 480), 300, color, 36)
    _headline(img, spec["headline"], color)
    _draw_keyboard(img, top=320, highlights=spec.get("highlight", ()),
                   pressed=spec.get("pressed", ()), dim=spec.get("dim", ()))
    d = ImageDraw.Draw(img)
    w = spec.get("window")
    if w:
        _window(img, w["box"], w["title"], w["rows"], highlight_label=w.get("highlight"),
                accent=COLORS.get(w.get("accent", "cyan"), CYAN))
    return img


def _build_window(spec):
    img = _bg()
    color = COLORS[spec.get("color", "cyan")]
    _headline(img, spec["headline"], color)
    _window(img, spec.get("box", (120, 220, 960, 760)), spec["title"], spec["rows"],
            highlight_label=spec.get("highlight"),
            accent=COLORS.get(spec.get("accent", "cyan"), CYAN),
            columns=spec.get("columns"), tabs=spec.get("tabs"),
            tab_highlight=spec.get("tab_highlight"))
    return img


def _build_context(spec):
    img = _bg()
    color = COLORS[spec.get("color", "red")]
    img = _glow(img, (720, 470), 240, color, 34)
    _headline(img, spec["headline"], color)
    _window(img, (120, 220, 700, 700), spec["title"], spec["rows"],
            highlight_label=spec.get("highlight"),
            accent=COLORS.get(spec.get("accent", "cyan"), CYAN),
            columns=spec.get("columns"))
    _context_menu(img, (620, 320, 990, 540), spec["menu"],
                  highlight=spec.get("menu_highlight"),
                  accent=COLORS.get(spec.get("menu_accent", "red"), RED))
    return img


def _build_menu(spec):
    img = _bg()
    color = COLORS[spec.get("color", "red")]
    img = _glow(img, (720, 470), 240, color, 34)
    _headline(img, spec["headline"], color)
    d = ImageDraw.Draw(img)
    _context_menu(img, (560, 300, 980, 620), spec["menu"],
                  highlight=spec.get("menu_highlight"),
                  accent=COLORS.get(spec.get("menu_accent", "red"), RED))
    return img


def _build_progress(spec):
    img = _bg()
    color = COLORS[spec.get("color", "red")]
    img = _glow(img, (CANVAS[0] // 2, 470), 320, color, 40)
    _headline(img, spec["headline"], color)
    d = ImageDraw.Draw(img)
    _progress_bar(d, spec.get("box", (240, 430, 840, 480)), spec["pct"], color, label=spec.get("label"))
    y = 560
    for txt, c in spec.get("lines", []):
        d.text((240, y), txt, font=_font(28), fill=COLORS[c])
        y += 44
    return img


def _build_storage(spec):
    img = _bg()
    color = COLORS[spec.get("color", "red")]
    img = _glow(img, (CANVAS[0] // 2, 470), 320, color, 40)
    _headline(img, spec["headline"], color)
    d = ImageDraw.Draw(img)
    _storage_meter(d, CANVAS[0] // 2, 440, 560, spec["pct"], color)
    cap = spec.get("caption")
    if cap:
        d.text((330, 560), cap, font=_font(28), fill=color)
    return img


def _build_run(spec):
    img = _bg()
    color = COLORS[spec.get("color", "cyan")]
    img = _glow(img, (CANVAS[0] // 2, 470), 300, color, 36)
    _headline(img, spec["headline"], color)
    d = ImageDraw.Draw(img)
    _run_dialog(d, spec.get("box", (240, 320, 840, 520)), spec["value"], title=spec.get("title", "Run"))
    return img


def _build_explorer(spec):
    img = _bg()
    color = COLORS[spec.get("color", "red")]
    _headline(img, spec["headline"], color)
    d = ImageDraw.Draw(img)
    files = spec["files"]
    _explorer(d, spec.get("box", (140, 220, 940, 740)), spec.get("title", "Temp - %temp%"),
              files, selected=files if spec.get("selected") else ())
    return img


def _build_panel(spec):
    img = _bg()
    color = COLORS[spec.get("color", "dim")]
    img = _glow(img, (CANVAS[0] // 2, 470), 300, color, 26)
    _headline(img, spec["headline"], color)
    d = ImageDraw.Draw(img)
    box = spec.get("box", (200, 280, 880, 640))
    _rounded(d, box, radius=22, fill=PANEL, outline=color, width=2)
    y = box[1] + 36
    f = _font(spec.get("font", 28))
    for txt, c in spec.get("lines", []):
        d.text((box[0] + 36, y), txt, font=f, fill=COLORS[c])
        y += 46
    return img


def _build_console(spec):
    img = _bg()
    color = COLORS[spec.get("color", "green")]
    img = _glow(img, (CANVAS[0] // 2, 470), 320, color, 34)
    _headline(img, spec["headline"], color)
    d = ImageDraw.Draw(img)
    box = spec.get("box", (140, 300, 940, 620))
    _rounded(d, box, radius=14, fill=(8, 12, 16), outline=PANEL_EDGE, width=2)
    d.text((box[0] + 30, box[1] + 28), "C:\\WINDOWS\\system32\\cmd.exe", font=_font(22), fill=TEXT_DIM)
    d.text((box[0] + 30, box[1] + 92), "> " + spec.get("command", ""), font=_font(30), fill=color)
    ok = spec.get("output")
    if ok:
        d.text((box[0] + 30, box[1] + 152), ok, font=_font(24), fill=TEXT)
    return img


def _build_flicker(spec):
    img = _bg()
    img = _glow(img, (CANVAS[0] // 2, 470), 320, (160, 170, 190), 30)
    _headline(img, spec.get("headline", "SCREEN FLICKERS FOR 1 SECOND"), TEXT)
    d = ImageDraw.Draw(img)
    bands = [(150, 210, 90), (380, 470, 130), (560, 600, 80), (720, 830, 150)]
    for y0, y1, w in bands:
        d.rectangle([(0, y0), (CANVAS[0], y1)], fill=(70, 78, 90))
        for i in range(4):
            yy = y0 + i * 10 + 3
            d.line([(0, yy), (CANVAS[0], yy)], fill=(210, 220, 230), width=w // 14)
    d.polygon([(0, 470), (180, 380), (300, 520), (460, 410), (620, 540), (780, 390),
               (930, 500), (1080, 430), (1080, 620), (0, 660)], fill=(120, 132, 148))
    d.polygon([(0, 470), (180, 380), (300, 520), (460, 410), (620, 540), (780, 390),
               (930, 500), (1080, 430), (1080, 480), (0, 520)], fill=(210, 222, 232))
    return img


def _build_ten_sec(spec):
    img = _bg()
    img = _glow(img, (CANVAS[0] // 2, 470), 300, YELLOW, 40)
    _headline(img, "THE 10-SECOND FIX", YELLOW)
    d = ImageDraw.Draw(img)
    _rounded(d, (300, 300, 780, 560), radius=24, fill=PANEL, outline=YELLOW, width=3)
    _icon(d, CANVAS[0] // 2, 430, "lightning", YELLOW, s=1.0)
    f = _font(64)
    txt = "10s"
    tw = d.textlength(txt, font=f)
    d.text(((CANVAS[0] - tw) / 2, 588), txt, font=f, fill=YELLOW)
    return img


def _build_follow(spec):
    img = _bg()
    img = _glow(img, (CANVAS[0] // 2, 470), 320, ORANGE, 40)
    _headline(img, "SAVE THIS FOR LATER", ORANGE)
    d = ImageDraw.Draw(img)
    _icon(d, CANVAS[0] // 2 - 140, 480, "bookmark", ORANGE, s=1.3)
    _rounded(d, (520, 380, 940, 560), radius=26, fill=PANEL, outline=ORANGE, width=3)
    f = _font(40)
    d.text((600, 420), "FOLLOW", font=f, fill=ORANGE)
    _icon(d, 650, 505, "bell", ORANGE, s=0.9)
    return img


_BUILDERS = {
    "icon": _build_icon,
    "keyboard": _build_keyboard,
    "window": _build_window,
    "context": _build_context,
    "menu": _build_menu,
    "progress": _build_progress,
    "storage": _build_storage,
    "run": _build_run,
    "explorer": _build_explorer,
    "panel": _build_panel,
    "console": _build_console,
    "flicker": _build_flicker,
    "ten_sec": _build_ten_sec,
    "follow": _build_follow,
}


# --------------------------------------------------------------------------
# Scene spec templates (shared)
# --------------------------------------------------------------------------

def _task_manager_rows(*apps):
    rows = []
    for a in apps:
        rows.append([a, "Running", "1.2", "90 MB"])
    return rows


def _app_rows(*apps):
    return [[a, "Enabled"] for a in apps]


# --------------------------------------------------------------------------
# Variants
# --------------------------------------------------------------------------

VARIANTS = {
    "clipboard_fix": [
        {"name": "copy broken", "type": "icon", "headline": "COPY & PASTE STOPPED",
         "color": "red", "icon": "clipboard", "ok": False, "s": 1.4},
        {"name": "ctrl+c", "type": "keyboard", "headline": "PRESS CTRL + C", "color": "cyan",
         "highlight": ["ctrl", "c"]},
        {"name": "ctrl+v", "type": "keyboard", "headline": "CTRL + V ... NOTHING", "color": "dim",
         "highlight": ["ctrl", "v"], "dim": ["c"]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "ctrl+shift+esc", "type": "keyboard", "headline": "CTRL + SHIFT + ESC", "color": "cyan",
         "highlight": ["ctrl", "shift", "esc"],
         "window": {"box": (690, 110, 1045, 340), "title": "Task Manager",
                    "rows": [("Explorer", "Running", "2.1", "180 MB")]}},
        {"name": "find explorer", "type": "window", "headline": "FIND WINDOWS EXPLORER",
         "title": "Task Manager", "highlight": "Windows Explorer",
         "rows": _task_manager_rows("Windows Explorer", "OneDrive", "Spotify", "Steam", "Edge")},
        {"name": "restart", "type": "context", "headline": "RIGHT CLICK  →  RESTART",
         "title": "Task Manager", "highlight": "Windows Explorer",
         "rows": _task_manager_rows("Windows Explorer", "OneDrive"),
         "menu": ["Restore", "Restart", "End task", "Open file location"],
         "menu_highlight": "Restart"},
        {"name": "flicker", "type": "flicker", "headline": "SCREEN FLICKERS FOR 1 SECOND"},
        {"name": "restored", "type": "icon", "headline": "COPY & PASTE IS BACK",
         "color": "green", "icon": "clipboard", "ok": True, "s": 1.4, "sub": "WORKING",
         "sub_color": "green"},
        {"name": "follow", "type": "follow"},
    ],
    "update_stuck": [
        {"name": "update stuck", "type": "icon", "headline": "UPDATE STUCK AT 0%?",
         "color": "red", "icon": "download", "s": 1.3, "sub": "NOTHING IS HAPPENING"},
        {"name": "never moves", "type": "panel", "headline": "IT NEVER MOVES", "color": "dim",
         "lines": [("Windows Update  —  0%", "dim"), ("You wait... and wait.", "white")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "ctrl+shift+esc", "type": "keyboard", "headline": "CTRL + SHIFT + ESC", "color": "cyan",
         "highlight": ["ctrl", "shift", "esc"]},
        {"name": "find update", "type": "window", "headline": "FIND WINDOWS UPDATE",
         "title": "Task Manager", "highlight": "Windows Update",
         "rows": _task_manager_rows("Windows Update", "OneDrive", "Spotify", "Steam", "Edge")},
        {"name": "end task", "type": "context", "headline": "RIGHT CLICK  →  END TASK",
         "title": "Task Manager", "highlight": "Windows Update",
         "rows": _task_manager_rows("Windows Update", "OneDrive"),
         "menu": ["Switch to", "Expand", "End task", "Go to details"],
         "menu_highlight": "End task"},
        {"name": "end task done", "type": "icon", "headline": "END TASK DONE",
         "color": "green", "icon": "check_circle", "s": 1.3, "sub": "Windows Update: STOPPED",
         "sub_color": "red"},
        {"name": "restart update", "type": "progress", "headline": "RESTART THE UPDATE",
         "color": "cyan", "pct": 0.35,
         "lines": [("Settings  →  Update & Security", "white"), ("Click 'Check for updates'", "cyan")]},
        {"name": "downloading", "type": "progress", "headline": "BOOM. DOWNLOADING AGAIN",
         "color": "green", "pct": 0.68, "label": "Downloading...  68%"},
        {"name": "follow", "type": "follow"},
    ],
    "disk_full": [
        {"name": "disk full", "type": "icon", "headline": "DISK ALWAYS FULL?",
         "color": "red", "icon": "harddrive", "ok": 0.95, "s": 1.2, "sub": "95% USED  —  5 GB LEFT"},
        {"name": "cant install", "type": "icon", "headline": "GAMES WON'T INSTALL",
         "color": "dim", "icon": "harddrive", "ok": 0.97, "s": 1.2, "sub": "Not enough disk space"},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "win+r", "type": "keyboard", "headline": "PRESS WIN + R", "color": "cyan",
         "highlight": ["win", "r"]},
        {"name": "type temp", "type": "run", "headline": "TYPE  %temp%  →  ENTER",
         "color": "cyan", "value": "%temp%"},
        {"name": "junk folder", "type": "explorer", "headline": "THE JUNK FOLDER", "color": "red",
         "title": "Temp - %temp%",
         "files": ["   temp_tmp0001.tmp", "   cache_data.bin", "   old_setup.log",
                   "   crash_dump.dmp", "   installer_tmp.exe", "   junk_file.dat"]},
        {"name": "select all", "type": "explorer", "headline": "CTRL + A  →  SELECT ALL", "color": "cyan",
         "title": "Temp - %temp%", "selected": True,
         "files": ["   temp_tmp0001.tmp", "   cache_data.bin", "   old_setup.log",
                   "   crash_dump.dmp", "   installer_tmp.exe", "   junk_file.dat"]},
        {"name": "delete", "type": "panel", "headline": "PRESS DELETE", "color": "orange",
         "lines": [("Select all  →  Delete", "white"), ("Skip files in use", "dim")]},
        {"name": "space freed", "type": "icon", "headline": "GIGABYTES FREED",
         "color": "green", "icon": "harddrive", "ok": 0.35, "s": 1.2, "sub": "INSTANTLY!",
         "sub_color": "green"},
        {"name": "follow", "type": "follow"},
    ],
    "slow_startup": [
        {"name": "slow boot", "type": "icon", "headline": "PC BOOTS SUPER SLOW?",
         "color": "red", "icon": "hourglass", "s": 1.2, "sub": "You wait... and wait."},
        {"name": "auto start", "type": "panel", "headline": "EVERYTHING AUTO-STARTS", "color": "dim",
         "lines": [("Apps launch at boot", "white"), ("All fighting for CPU", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "ctrl+shift+esc", "type": "keyboard", "headline": "CTRL + SHIFT + ESC", "color": "cyan",
         "highlight": ["ctrl", "shift", "esc"]},
        {"name": "startup tab", "type": "window", "headline": "CLICK THE STARTUP TAB",
         "title": "Task Manager", "tabs": ["Processes", "Startup"], "tab_highlight": "Startup",
         "columns": ("Name", "Status"), "rows": _app_rows("OneDrive", "Spotify", "Steam", "Teams", "Edge")},
        {"name": "find junk", "type": "window", "headline": "DISABLE THE JUNK",
         "title": "Task Manager", "tabs": ["Processes", "Startup"], "tab_highlight": "Startup",
         "columns": ("Name", "Status"), "highlight": "OneDrive",
         "rows": _app_rows("OneDrive", "Spotify", "Steam", "Teams", "Edge")},
        {"name": "disable", "type": "context", "headline": "RIGHT CLICK  →  DISABLE",
         "title": "Task Manager", "highlight": "OneDrive",
         "rows": _task_manager_rows("OneDrive", "Spotify"),
         "menu": ["Open", "Open file location", "Search online", "Disable"],
         "menu_highlight": "Disable"},
        {"name": "faster boot", "type": "icon", "headline": "BOOM. FASTER BOOT",
         "color": "green", "icon": "rocket", "s": 1.2, "sub": "Startup cleaned up",
         "sub_color": "green"},
        {"name": "way faster", "type": "panel", "headline": "WAY FASTER BOOT", "color": "green",
         "lines": [("Power on  →  Desktop in seconds", "green")]},
        {"name": "follow", "type": "follow"},
    ],
    "bluetooth_gone": [
        {"name": "bluetooth gone", "type": "icon", "headline": "BLUETOOTH JUST DISAPPEARED?",
         "color": "red", "icon": "bluetooth", "ok": False, "s": 1.2, "sub": "Gone from Settings"},
        {"name": "cant connect", "type": "panel", "headline": "CAN'T CONNECT ANYTHING", "color": "dim",
         "lines": [("Headphones? Nope", "white"), ("Mouse? Nope", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "win+x", "type": "keyboard", "headline": "PRESS WIN + X", "color": "cyan",
         "highlight": ["win", "x"]},
        {"name": "device manager", "type": "window", "headline": "OPEN DEVICE MANAGER",
         "title": "Device Manager", "highlight": "Bluetooth",
         "columns": ("Device", "Status"), "accent": "cyan",
         "rows": [["Audio", "Working"], ["Bluetooth", "Working"], ["Cameras", "Working"],
                  ["Keyboards", "Working"], ["Mice", "Working"]]},
        {"name": "right click bt", "type": "context", "headline": "RIGHT CLICK BLUETOOTH",
         "title": "Device Manager", "highlight": "Bluetooth",
         "columns": ("Device", "Status"),
         "rows": [["Bluetooth", "Working"], ["Keyboards", "Working"], ["Mice", "Working"]],
         "menu": ["Disable device", "Update driver", "Uninstall device"],
         "menu_highlight": "Disable device"},
        {"name": "wait", "type": "panel", "headline": "WAIT 2 SECONDS", "color": "dim",
         "lines": [("Then Enable it again", "white")]},
        {"name": "bt back", "type": "icon", "headline": "BOOM. BLUETOOTH IS BACK",
         "color": "green", "icon": "bluetooth", "s": 1.2, "sub": "Enabled again",
         "sub_color": "green"},
        {"name": "connect again", "type": "panel", "headline": "CONNECT AGAIN", "color": "green",
         "lines": [("It just works now", "green")]},
        {"name": "follow", "type": "follow"},
    ],
    "no_sound": [
        {"name": "no sound", "type": "icon", "headline": "NO SOUND?",
         "color": "red", "icon": "speaker", "ok": False, "s": 1.2, "sub": "Volume is all the way up"},
        {"name": "still nothing", "type": "panel", "headline": "STILL NOTHING", "color": "dim",
         "lines": [("Videos play in silence", "white"), ("Annoying, right?", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "win+r", "type": "keyboard", "headline": "PRESS WIN + R", "color": "cyan",
         "highlight": ["win", "r"]},
        {"name": "services", "type": "run", "headline": "TYPE services.msc", "color": "cyan",
         "value": "services.msc"},
        {"name": "windows audio", "type": "window", "headline": "FIND WINDOWS AUDIO",
         "title": "Services", "highlight": "Windows Audio",
         "columns": ("Name", "Status"), "accent": "cyan",
         "rows": [["Windows Audio", "Running"], ["Windows Firewall", "Running"],
                  ["Print Spooler", "Running"], ["Windows Update", "Manual"],
                  ["Windows Search", "Running"]]},
        {"name": "restart audio", "type": "context", "headline": "RIGHT CLICK  →  RESTART",
         "title": "Services", "highlight": "Windows Audio",
         "columns": ("Name", "Status"),
         "rows": [["Windows Audio", "Running"], ["Windows Firewall", "Running"]],
         "menu": ["Start", "Stop", "Restart", "Properties"],
         "menu_highlight": "Restart"},
        {"name": "wait", "type": "panel", "headline": "WAIT 5 SECONDS", "color": "dim",
         "lines": [("Sound service restarting", "white")]},
        {"name": "sound back", "type": "icon", "headline": "SOUND IS BACK",
         "color": "green", "icon": "speaker", "s": 1.2, "sub": "Music on!",
         "sub_color": "green"},
        {"name": "follow", "type": "follow"},
    ],
    "slow_internet": [
        {"name": "slow internet", "type": "icon", "headline": "INTERNET SUPER SLOW?",
         "color": "red", "icon": "globe", "ok": False, "s": 1.2, "sub": "Pages keep spinning"},
        {"name": "nothing loads", "type": "panel", "headline": "NOTHING LOADS", "color": "dim",
         "lines": [("Websites crawl", "white"), ("Videos buffer forever", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "win+r", "type": "keyboard", "headline": "PRESS WIN + R", "color": "cyan",
         "highlight": ["win", "r"]},
        {"name": "cmd", "type": "run", "headline": "OPEN COMMAND PROMPT", "color": "cyan",
         "value": "cmd", "title": "Run"},
        {"name": "flushdns", "type": "console", "headline": "RUN AS ADMIN", "color": "cyan",
         "command": "ipconfig /flushdns", "output": "Successfully flushed the DNS Resolver Cache"},
        {"name": "dns cleared", "type": "icon", "headline": "DNS CACHE CLEARED",
         "color": "green", "icon": "globe", "s": 1.2, "sub": "Internet feels faster",
         "sub_color": "green"},
        {"name": "instant boost", "type": "panel", "headline": "INSTANT BOOST", "color": "green",
         "lines": [("Websites load fast again", "green")]},
        {"name": "still slow", "type": "panel", "headline": "STILL SLOW?", "color": "dim",
         "lines": [("Restart your router", "white")]},
        {"name": "follow", "type": "follow"},
    ],
    "app_not_responding": [
        {"name": "not responding", "type": "icon", "headline": "APP NOT RESPONDING?",
         "color": "red", "icon": "alert", "s": 1.2, "sub": "It's completely frozen"},
        {"name": "cant close", "type": "panel", "headline": "CAN'T EVEN CLOSE IT", "color": "dim",
         "lines": [("X button does nothing", "white"), ("Full screen lockup", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "ctrl+shift+esc", "type": "keyboard", "headline": "CTRL + SHIFT + ESC", "color": "cyan",
         "highlight": ["ctrl", "shift", "esc"]},
        {"name": "find app", "type": "window", "headline": "FIND THE FROZEN APP",
         "title": "Task Manager", "highlight": "Chrome (Not responding)", "accent": "red",
         "rows": [["Chrome (Not responding)", "Not responding", "5.8", "900 MB"],
                  ["Spotify", "Running", "3.2", "210 MB"],
                  ["Edge", "Running", "2.7", "240 MB"],
                  ["Steam", "Suspended", "0.0", "90 MB"],
                  ["Teams", "Running", "1.9", "180 MB"]]},
        {"name": "end task", "type": "context", "headline": "RIGHT CLICK  →  END TASK",
         "title": "Task Manager", "highlight": "Chrome (Not responding)", "accent": "red",
         "rows": [["Chrome (Not responding)", "Not responding", "5.8", "900 MB"],
                  ["Spotify", "Running", "3.2", "210 MB"]],
         "menu": ["End task", "Go to details"], "menu_highlight": "End task"},
        {"name": "closed", "type": "icon", "headline": "BOOM. CLOSED",
         "color": "green", "icon": "stop", "s": 1.2, "sub": "App force-closed",
         "sub_color": "green"},
        {"name": "you're back", "type": "panel", "headline": "YOU'RE BACK", "color": "green",
         "lines": [("Nothing lost. Just closed", "green")]},
        {"name": "freeze gone", "type": "panel", "headline": "FREEZE GONE", "color": "dim",
         "lines": [("Saves your day", "dim")]},
        {"name": "follow", "type": "follow"},
    ],
    "wrong_default_app": [
        {"name": "wrong app", "type": "icon", "headline": "FILES OPEN IN THE WRONG APP?",
         "color": "red", "icon": "file", "ok": False, "s": 1.2, "sub": "PDFs open in the browser"},
        {"name": "annoying", "type": "panel", "headline": "SO ANNOYING", "color": "dim",
         "lines": [("Images in the wrong editor", "white"), ("Every single time", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "open with", "type": "menu", "headline": "RIGHT CLICK THE FILE",
         "menu": ["Open", "Open with", "Share", "Delete"], "menu_highlight": "Open with"},
        {"name": "choose app", "type": "panel", "headline": "CHOOSE ANOTHER APP", "color": "cyan",
         "lines": [("Pick your favorite app", "white"), ("From the list", "dim")]},
        {"name": "always use", "type": "panel", "headline": "ALWAYS USE THIS APP", "color": "green",
         "lines": [("Tick 'Always use this app'", "green"), ("Then click OK", "dim")]},
        {"name": "fixed", "type": "icon", "headline": "FIXED FOREVER",
         "color": "green", "icon": "file", "ok": True, "s": 1.2, "sub": "Never opens wrong again",
         "sub_color": "green"},
        {"name": "done", "type": "panel", "headline": "DONE!", "color": "green",
         "lines": [("That app is now the default", "green")]},
        {"name": "steal defaults", "type": "panel", "headline": "NEW APPS STEAL DEFAULTS", "color": "dim",
         "lines": [("Re-check after installs", "dim")]},
        {"name": "follow", "type": "follow"},
    ],
    "battery_drain": [
        {"name": "battery drain", "type": "icon", "headline": "BATTERY DRAINS FAST?",
         "color": "red", "icon": "battery", "ok": 0.15, "s": 1.2, "sub": "Full in the morning, dead at lunch"},
        {"name": "dies fast", "type": "panel", "headline": "RUNS OUT TOO QUICKLY", "color": "dim",
         "lines": [("Video calls eat it up", "white"), ("Games even faster", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "win+i", "type": "keyboard", "headline": "PRESS WIN + I", "color": "cyan",
         "highlight": ["win", "i"]},
        {"name": "power settings", "type": "panel", "headline": "SYSTEM  →  POWER & BATTERY", "color": "cyan",
         "lines": [("Open Settings", "white"), ("Power and battery", "cyan")]},
        {"name": "battery saver", "type": "panel", "headline": "TURN ON BATTERY SAVER", "color": "green",
         "lines": [("One toggle", "white"), ("Battery Saver:  ON", "green")]},
        {"name": "lasts longer", "type": "icon", "headline": "LASTS WAY LONGER",
         "color": "green", "icon": "battery", "ok": 1.0, "s": 1.2, "sub": "Big difference",
         "sub_color": "green"},
        {"name": "easy win", "type": "panel", "headline": "EASY WIN", "color": "green",
         "lines": [("Works on any laptop", "green")]},
        {"name": "tip", "type": "panel", "headline": "TIP: LOWER BRIGHTNESS TOO", "color": "dim",
         "lines": [("Saves even more", "dim")]},
        {"name": "follow", "type": "follow"},
    ],
    "mic_not_working": [
        {"name": "mic broken", "type": "icon", "headline": "MIC NOT WORKING?",
         "color": "red", "icon": "mic", "ok": False, "s": 1.2, "sub": "Nobody can hear you"},
        {"name": "calls broken", "type": "panel", "headline": "CALLS ARE BROKEN", "color": "dim",
         "lines": [("Meetings? Silence", "white"), ("Voice notes? Nope", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "win+i", "type": "keyboard", "headline": "PRESS WIN + I", "color": "cyan",
         "highlight": ["win", "i"]},
        {"name": "privacy", "type": "window", "headline": "PRIVACY  →  MICROPHONE",
         "title": "Settings - Privacy", "highlight": "Microphone access: ON",
         "columns": ("Setting", "Value"), "accent": "cyan",
         "rows": [["Microphone access: ON", "ON"], ["Apps allowed: ON", "ON"],
                  ["Desktop apps", "Allowed"], ["Camera access", "ON"]]},
        {"name": "toggle", "type": "panel", "headline": "TOGGLE IT OFF & ON", "color": "cyan",
         "lines": [("Microphone access", "white"), ("Off... then On", "cyan")]},
        {"name": "test mic", "type": "icon", "headline": "TEST YOUR MIC",
         "color": "green", "icon": "mic", "s": 1.2, "sub": "Boom. It works",
         "sub_color": "green"},
        {"name": "works again", "type": "panel", "headline": "WORKS AGAIN", "color": "green",
         "lines": [("You can be heard now", "green")]},
        {"name": "privacy updates", "type": "panel", "headline": "PRIVACY UPDATES DO THIS", "color": "dim",
         "lines": [("Re-check after updates", "dim")]},
        {"name": "follow", "type": "follow"},
    ],
    "printer_not_printing": [
        {"name": "printer stuck", "type": "icon", "headline": "PRINTER NOT PRINTING?",
         "color": "red", "icon": "printer", "ok": False, "s": 1.2, "sub": "Stuck in the queue"},
        {"name": "nothing out", "type": "panel", "headline": "NOTHING COMES OUT", "color": "dim",
         "lines": [("You hit print... nothing", "white"), ("Classic printer", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "win+i", "type": "keyboard", "headline": "PRESS WIN + I", "color": "cyan",
         "highlight": ["win", "i"]},
        {"name": "printers", "type": "panel", "headline": "PRINTERS & SCANNERS", "color": "cyan",
         "lines": [("Open Printers & scanners", "white"), ("Find your printer", "dim")]},
        {"name": "open queue", "type": "panel", "headline": "OPEN PRINT QUEUE", "color": "cyan",
         "lines": [("Click 'Open print queue'", "white"), ("See the stuck jobs", "dim")]},
        {"name": "cancel all", "type": "panel", "headline": "CANCEL ALL DOCUMENTS", "color": "red",
         "lines": [("Click 'Cancel all'", "red"), ("Clears the jam", "dim")]},
        {"name": "prints again", "type": "icon", "headline": "PRINT AGAIN",
         "color": "green", "icon": "printer", "s": 1.2, "sub": "Boom. It prints",
         "sub_color": "green"},
        {"name": "printers jam", "type": "panel", "headline": "PRINTERS LOVE TO JAM", "color": "dim",
         "lines": [("Save this for next time", "dim")]},
        {"name": "follow", "type": "follow"},
    ],
    "desktop_icons_missing": [
        {"name": "icons gone", "type": "icon", "headline": "DESKTOP ICONS MISSING?",
         "color": "red", "icon": "monitor", "s": 1.2, "sub": "Desktop looks empty"},
        {"name": "dont panic", "type": "panel", "headline": "DON'T PANIC", "color": "dim",
         "lines": [("Your files are safe", "white"), ("They're still there", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "right click", "type": "menu", "headline": "RIGHT CLICK THE DESKTOP",
         "menu": ["View", "Sort by", "Refresh", "New"], "menu_highlight": "View"},
        {"name": "view", "type": "menu", "headline": "HOVER OVER VIEW",
         "menu": ["Large icons", "Medium icons", "Small icons", "Auto arrange icons",
                  "Show desktop icons"], "menu_highlight": "Show desktop icons"},
        {"name": "show icons", "type": "panel", "headline": "SHOW DESKTOP ICONS", "color": "green",
         "lines": [("Click the checkbox", "white"), ("That's it", "dim")]},
        {"name": "icons back", "type": "icon", "headline": "ALL YOUR ICONS ARE BACK",
         "color": "green", "icon": "monitor", "s": 1.2, "sub": "Boom",
         "sub_color": "green"},
        {"name": "done", "type": "panel", "headline": "DONE", "color": "green",
         "lines": [("Icons restored", "green")]},
        {"name": "happens often", "type": "panel", "headline": "HAPPENS MORE THAN YOU THINK", "color": "dim",
         "lines": [("Quick fix every time", "dim")]},
        {"name": "follow", "type": "follow"},
    ],
    "cant_delete_file": [
        {"name": "cant delete", "type": "icon", "headline": "CAN'T DELETE A FILE?",
         "color": "red", "icon": "file", "ok": False, "s": 1.2, "sub": "Open in another program"},
        {"name": "windows says no", "type": "panel", "headline": "WINDOWS SAYS NO", "color": "dim",
         "lines": [("File is in use", "white"), ("Delete keeps failing", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "ctrl+shift+esc", "type": "keyboard", "headline": "CTRL + SHIFT + ESC", "color": "cyan",
         "highlight": ["ctrl", "shift", "esc"]},
        {"name": "find app", "type": "window", "headline": "FIND THE APP USING IT",
         "title": "Task Manager", "highlight": "Chrome",
         "rows": _task_manager_rows("Chrome", "Spotify", "Edge", "Steam", "Teams")},
        {"name": "end task", "type": "context", "headline": "RIGHT CLICK  →  END TASK",
         "title": "Task Manager", "highlight": "Chrome",
         "rows": _task_manager_rows("Chrome", "Spotify"),
         "menu": ["End task", "Go to details"], "menu_highlight": "End task"},
        {"name": "delete now", "type": "panel", "headline": "NOW DELETE IT", "color": "cyan",
         "lines": [("Right click  →  Delete", "white"), ("Or press Delete", "dim")]},
        {"name": "gone", "type": "icon", "headline": "BOOM. GONE",
         "color": "green", "icon": "trash", "s": 1.2, "sub": "File deleted",
         "sub_color": "green"},
        {"name": "stubborn files", "type": "panel", "headline": "STUBBORN FILES RETURN", "color": "dim",
         "lines": [("Same fix next time", "dim")]},
        {"name": "follow", "type": "follow"},
    ],
    "search_broken": [
        {"name": "search broken", "type": "icon", "headline": "WINDOWS SEARCH BROKEN?",
         "color": "red", "icon": "search", "ok": False, "s": 1.2, "sub": "Finds absolutely nothing"},
        {"name": "spins", "type": "panel", "headline": "IT JUST SPINS", "color": "dim",
         "lines": [("Type... nothing", "white"), ("Start menu search dead", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "ctrl+shift+esc", "type": "keyboard", "headline": "CTRL + SHIFT + ESC", "color": "cyan",
         "highlight": ["ctrl", "shift", "esc"]},
        {"name": "find search", "type": "window", "headline": "FIND WINDOWS SEARCH",
         "title": "Task Manager", "highlight": "Windows Search",
         "rows": _task_manager_rows("Windows Search", "OneDrive", "Spotify", "Steam", "Edge")},
        {"name": "end task", "type": "context", "headline": "RIGHT CLICK  →  END TASK",
         "title": "Task Manager", "highlight": "Windows Search",
         "rows": _task_manager_rows("Windows Search", "Edge"),
         "menu": ["End task", "Go to details"], "menu_highlight": "End task"},
        {"name": "restarts", "type": "panel", "headline": "IT RESTARTS ITSELF", "color": "cyan",
         "lines": [("Windows brings it back", "white"), ("Automatically", "dim")]},
        {"name": "search works", "type": "icon", "headline": "SEARCH WORKS AGAIN",
         "color": "green", "icon": "search", "s": 1.2, "sub": "Boom",
         "sub_color": "green"},
        {"name": "search breaks", "type": "panel", "headline": "SEARCH BREAKS A LOT", "color": "dim",
         "lines": [("Same fix next time", "dim")]},
        {"name": "follow", "type": "follow"},
    ],
    "text_too_small": [
        {"name": "text small", "type": "icon", "headline": "TEXT TOO SMALL?",
         "color": "red", "icon": "text", "s": 1.1, "sub": "Squinting at your screen"},
        {"name": "hard to read", "type": "panel", "headline": "HARD TO READ", "color": "dim",
         "lines": [("Everything is tiny", "white"), ("Your eyes hurt", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "ctrl scroll", "type": "keyboard", "headline": "HOLD CTRL + SCROLL UP", "color": "cyan",
         "highlight": ["ctrl"]},
        {"name": "browser zoom", "type": "panel", "headline": "ZOOMS IN THE BROWSER", "color": "cyan",
         "lines": [("Works on any page", "white"), ("Ctrl + Scroll up", "cyan")]},
        {"name": "display settings", "type": "panel", "headline": "WHOLE SYSTEM: DISPLAY", "color": "cyan",
         "lines": [("Win + I  →  Display", "white"), ("Scale: bump it up", "dim")]},
        {"name": "scale up", "type": "panel", "headline": "DRAG THE SCALE UP", "color": "green",
         "lines": [("Try 125% or 150%", "white"), ("Applies instantly", "green")]},
        {"name": "bigger text", "type": "icon", "headline": "BIGGER TEXT",
         "color": "green", "icon": "text", "s": 1.1, "sub": "Much easier to read",
         "sub_color": "green"},
        {"name": "new screens", "type": "panel", "headline": "EVERY NEW SCREEN NEEDS THIS", "color": "dim",
         "lines": [("Re-apply per monitor", "dim")]},
        {"name": "follow", "type": "follow"},
    ],
    "emoji_keyboard": [
        {"name": "emoji trick", "type": "icon", "headline": "SECRET EMOJI KEYBOARD?",
         "color": "orange", "icon": "emoji", "s": 1.2, "sub": "Built into Windows"},
        {"name": "no downloads", "type": "panel", "headline": "NO DOWNLOADS NEEDED", "color": "dim",
         "lines": [("No apps, no install", "white"), ("It's already there", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "win dot", "type": "keyboard", "headline": "WIN + PERIOD", "color": "cyan",
         "highlight": ["win", "."]},
        {"name": "panel pops", "type": "panel", "headline": "EMOJI PANEL POPS UP", "color": "cyan",
         "lines": [("Instantly", "white"), ("Browse the whole library", "dim")]},
        {"name": "search emojis", "type": "panel", "headline": "SEARCH EMOJIS TOO", "color": "cyan",
         "lines": [("Type what you need", "white"), ("Like 'laugh'", "dim")]},
        {"name": "emojis everywhere", "type": "icon", "headline": "EMOJIS EVERYWHERE",
         "color": "green", "icon": "emoji", "s": 1.2, "sub": "In any app",
         "sub_color": "green"},
        {"name": "daily", "type": "panel", "headline": "YOU'LL USE THIS DAILY", "color": "green",
         "lines": [("Try it right now", "green")]},
        {"name": "shortcut", "type": "panel", "headline": "SHORTCUT:  WIN + .", "color": "dim",
         "lines": [("Same trick everywhere", "dim")]},
        {"name": "follow", "type": "follow"},
    ],
    "screen_record": [
        {"name": "record", "type": "icon", "headline": "RECORD WITHOUT SOFTWARE?",
         "color": "orange", "icon": "camera", "s": 1.2, "sub": "Windows has it hidden"},
        {"name": "no watermark", "type": "panel", "headline": "NO DOWNLOADS. NO WATERMARK.", "color": "dim",
         "lines": [("No installs", "white"), ("Completely free", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "win alt r", "type": "keyboard", "headline": "WIN + ALT + R", "color": "cyan",
         "highlight": ["win", "alt", "r"]},
        {"name": "recording", "type": "panel", "headline": "RECORDING STARTS NOW", "color": "red",
         "lines": [("A small bar appears", "white"), ("Rec dot: ON", "red")]},
        {"name": "stop", "type": "panel", "headline": "CLICK STOP WHEN DONE", "color": "cyan",
         "lines": [("Hit the stop button", "white"), ("Clip saves itself", "dim")]},
        {"name": "saved", "type": "panel", "headline": "SAVED TO VIDEOS FOLDER", "color": "green",
         "lines": [("Videos folder, automatically", "white"), ("Ready to upload", "green")]},
        {"name": "done", "type": "icon", "headline": "DONE. ZERO COST",
         "color": "green", "icon": "camera", "s": 1.2, "sub": "No software needed",
         "sub_color": "green"},
        {"name": "clips", "type": "panel", "headline": "GREAT FOR CLIPS & BUGS", "color": "dim",
         "lines": [("Share bugs with support", "dim")]},
        {"name": "follow", "type": "follow"},
    ],
    "blue_screen": [
        {"name": "bsod", "type": "icon", "headline": "BLUE SCREEN?",
         "color": "blue", "icon": "monitor", "ok": "blue", "s": 1.1, "sub": "Don't panic",
         "sub_color": "white"},
        {"name": "files fine", "type": "panel", "headline": "YOUR FILES ARE FINE", "color": "dim",
         "lines": [("Usually safe", "white"), ("It's Windows, not your PC", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "win+r", "type": "keyboard", "headline": "WIN + R  →  cmd", "color": "cyan",
         "highlight": ["win", "r"]},
        {"name": "cmd", "type": "run", "headline": "RUN AS ADMIN", "color": "cyan",
         "value": "cmd", "title": "Run"},
        {"name": "sfc", "type": "console", "headline": "CHECK SYSTEM FILES", "color": "cyan",
         "command": "sfc /scannow", "output": "Scanning... repairs broken Windows files"},
        {"name": "scan", "type": "progress", "headline": "LET IT SCAN",
         "color": "cyan", "pct": 0.6, "label": "Verifying  60%"},
        {"name": "fixed", "type": "icon", "headline": "BOOM. FIXED",
         "color": "green", "icon": "shield", "ok": True, "s": 1.2, "sub": "Fewer crashes now",
         "sub_color": "green"},
        {"name": "after crash", "type": "panel", "headline": "WORTH DOING AFTER A CRASH", "color": "dim",
         "lines": [("Runs a full check", "dim")]},
        {"name": "follow", "type": "follow"},
    ],
    "cursor_disappeared": [
        {"name": "cursor gone", "type": "icon", "headline": "CURSOR DISAPPEARED?",
         "color": "red", "icon": "mouse", "ok": False, "s": 1.2, "sub": "Pointer is gone"},
        {"name": "nothing", "type": "panel", "headline": "MOVE THE MOUSE... NOTHING", "color": "dim",
         "lines": [("No pointer anywhere", "white"), ("Blank screen", "dim")]},
        {"name": "10s fix", "type": "ten_sec"},
        {"name": "win+r", "type": "keyboard", "headline": "PRESS WIN + R", "color": "cyan",
         "highlight": ["win", "r"]},
        {"name": "main cpl", "type": "run", "headline": "TYPE main.cpl", "color": "cyan",
         "value": "main.cpl"},
        {"name": "pointer options", "type": "panel", "headline": "POINTER OPTIONS", "color": "cyan",
         "lines": [("Open Mouse Properties", "white"), ("Pointer Options tab", "dim")]},
        {"name": "show location", "type": "panel", "headline": "SHOW LOCATION ON CTRL", "color": "green",
         "lines": [("Tick the checkbox", "white"), ("Show location when I press CTRL", "green")]},
        {"name": "found it", "type": "icon", "headline": "PRESS CTRL NOW",
         "color": "green", "icon": "mouse", "s": 1.2, "sub": "Boom. Found it",
         "sub_color": "green"},
        {"name": "cursors hide", "type": "panel", "headline": "CURSORS LOVE TO HIDE", "color": "dim",
         "lines": [("Now you can find it", "dim")]},
        {"name": "follow", "type": "follow"},
    ],
}


def render_scenes(data_dir: str, variant: str = "clipboard_fix") -> list[str]:
    specs = VARIANTS.get(variant)
    if specs is None:
        raise KeyError(f"unknown ui variant: {variant!r} (have {sorted(VARIANTS)})")
    os.makedirs(data_dir, exist_ok=True)
    out = []
    for i, spec in enumerate(specs):
        builder = _BUILDERS[spec["type"]]
        img = builder(spec)
        path = os.path.join(data_dir, f"scene_{i}.jpg")
        img.save(path, format="JPEG", quality=92)
        out.append(path)
        print(f"[{i}] {spec.get('name', spec['type'])} -> {path}")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("usage: python -m app.video.ui_graphics folks <data_dir> <variant>")
    variant = sys.argv[3] if len(sys.argv) > 3 else "clipboard_fix"
    render_scenes(sys.argv[2], variant)
