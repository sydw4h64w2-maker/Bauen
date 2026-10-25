"""Rendert Folge 1 „Überlebst du das? – Fahrstuhl“ (1080x1920, 30 fps) passend
zur ElevenLabs-Stimme in folgen/folge-01/stimme.mp3.

Aufruf:  python3 video/render_folge01.py
Ergebnis: video/out/folge01-fahrstuhl.mp4

Die Satz-Zeitmarken (SENTENCES) wurden per Abgleich mit der Aufnahme ermittelt
und an die Sprechpausen angepasst. Neue Aufnahme → Zeitmarken neu setzen.
"""
import math
import os
import random
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(HERE, "out")
VOICE = os.path.join(ROOT, "folgen", "folge-01", "stimme.mp3")
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

RED = (232, 44, 60)
GREEN = (46, 204, 113)
WHITE = (245, 245, 245)
GREY = (150, 158, 170)
CARD = (28, 34, 44)
AMBER = (255, 176, 32)

# (Start, Ende, Satz) – Sekunden in der Sprachaufnahme
SENTENCES = [
    (0.00, 1.16, "Du hast drei Sekunden."),
    (1.70, 3.80, "Wähl falsch – und es wird gefährlich."),
    (4.43, 5.80, "Du bist allein im Fahrstuhl."),
    (6.00, 7.03, "Zwanzigster Stock."),
    (7.52, 9.21, "Plötzlich … fällt er!"),
    (9.33, 10.00, "Was tust du?"),
    (18.90, 19.32, "Drei."),
    (19.83, 20.33, "Zwei."),
    (20.93, 21.38, "Eins."),
    (22.00, 23.33, "Die meisten wählen A."),
    (23.80, 27.92, "Aus dem 20. Stock schlägst du mit über 100 km/h auf."),
    (28.44, 30.67, "Ein Sprung bremst dich nur um etwa 14 km/h."),
    (31.30, 32.48, "Mythos widerlegt."),
    (32.80, 35.47, "Experten raten zu C: flach hinlegen."),
    (35.85, 40.18, "Der Aufprall verteilt sich dann auf deinen ganzen Körper statt auf Beine und Wirbelsäule."),
    (40.54, 42.30, "Eine Garantie ist das nicht."),
    (42.45, 43.63, "Aber die gute Nachricht:"),
    (43.87, 47.08, "Fahrstühle hängen an mehreren Seilen und haben Fangbremsen."),
    (47.38, 49.86, "Ein echter freier Fall ist extrem selten."),
    (50.41, 51.63, "Hättest du richtig gewählt?"),
    (51.89, 54.69, "Schreib A, B oder C in die Kommentare."),
    (55.19, 57.50, "Und morgen: Du steckst im Treibsand."),
    (57.85, 60.77, "Und je mehr du kämpfst, desto tiefer zieht er dich runter."),
    (61.17, 64.37, "Folg mir – sonst erfährst du nie, wie du da rauskommst."),
]
# Antwortoptionen werden auf den Karten gezeigt, nicht als Untertitel
T_OPT = (10.63, 13.54, 16.12)
T_FALL, T_IMPACT = 7.52, 9.20
T_COUNT = (18.90, 19.83, 20.93)
DUR = 66.0

SCENE_T = {"scenario": 4.3, "choice": 9.3, "wrong": 21.9, "right": 32.7,
           "end": 50.3}

_fonts = {}


def font(size):
    size = max(8, int(size))
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT_BOLD, size)
    return _fonts[size]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def punch(t, start, dur=0.35):
    """Skalierung, die kurz überschießt und auf 1 zurückfällt."""
    x = clamp((t - start) / dur)
    if x >= 1:
        return 1.0
    return 1 + 0.25 * math.sin(x * math.pi) * (1 - x) + (ease_out(x) - 1) * 0.6


def text_c(d, xy, txt, size, fill=WHITE, stroke=8, alpha=1.0):
    if alpha <= 0:
        return
    col = tuple(int(c * alpha) for c in fill)
    d.text(xy, txt, font=font(size), fill=col, anchor="mm", stroke_width=stroke,
           stroke_fill=(0, 0, 0))


def rrect(d, box, r, fill, outline=None, width=0):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


# ---------------------------------------------------------------- Hintergrund
def make_background():
    y = np.linspace(0, 1, H)[:, None, None]
    top = np.array([12, 15, 22])
    bot = np.array([4, 5, 8])
    grad = np.broadcast_to(top * (1 - y) + bot * y, (H, W, 3))
    return Image.fromarray(grad.astype(np.uint8), "RGB")


def make_vignette(color):
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a = np.clip((r - 0.7) / 0.7, 0, 1) ** 1.5 * 0.85
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = color
    img[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


BG = make_background()
VIG_DARK = make_vignette((0, 0, 0))
VIG_RED = make_vignette(RED)
VIG_GREEN = make_vignette(GREEN)


def paste_vignette(img, vig, strength):
    if strength <= 0:
        return
    v = vig.copy()
    v.putalpha(v.getchannel("A").point(lambda a: int(a * strength)))
    img.paste(v, (0, 0), v)


# ---------------------------------------------------------------- Untertitel
def build_captions():
    """Teilt jeden Satz in gleich lange Häppchen (ca. 26 Zeichen) und verteilt
    die Satzdauer nach Zeichenzahl."""
    caps = []
    for s, e, sent in SENTENCES:
        words = sent.split()
        n = math.ceil(len(sent) / 26)
        target = len(sent) / n
        chunks, cur = [], []
        for w in words:
            if cur and len(chunks) < n - 1 and \
                    len(" ".join(cur + [w])) > target + 4:
                chunks.append(" ".join(cur))
                cur = []
            cur.append(w)
        chunks.append(" ".join(cur))
        total = sum(len(c) + 3 for c in chunks)
        t = s
        for c in chunks:
            dt = (e - s) * (len(c) + 3) / total
            caps.append([t, t + dt, c])
            t += dt
    # Untertitel bis kurz vor den nächsten stehen lassen (max. 0,6 s länger)
    for a, b in zip(caps, caps[1:]):
        a[1] = min(b[0], a[1] + 0.6)
    caps[-1][1] = min(DUR, caps[-1][1] + 1.0)
    return caps


CAPTIONS = build_captions()


def draw_caption(d, t):
    for s, e, txt in CAPTIONS:
        if s <= t < e:
            size = 66
            while font(size).getlength(txt) > 940:
                size -= 2
            text_c(d, (W // 2, 1420), txt, size * punch(t, s, 0.22), stroke=10)
            return


def draw_badge(d, t):
    rrect(d, (60, 150, 360, 230), 20, RED)
    d.text((210, 190), "TAG 1/365", font=font(44), fill=WHITE, anchor="mm")


# ---------------------------------------------------------------- Szenen
def scene_hook(img, d, t):
    pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 1.25)
    paste_vignette(img, VIG_RED, 0.35 + 0.45 * pulse)
    sc = punch(t, 0.0, 0.5)
    text_c(d, (W // 2, 760), "ÜBERLEBST", 120 * sc, stroke=12)
    text_c(d, (W // 2, 900), "DU DAS?", 150 * sc, fill=RED, stroke=12)


def draw_elevator(d, cx, cy, floor, shake=(0, 0), flash=0.0):
    cx += shake[0]
    cy += shake[1]
    rrect(d, (cx - 380, cy - 520, cx + 380, cy + 520), 24, (22, 26, 34),
          outline=(55, 62, 74), width=6)
    rrect(d, (cx - 150, cy - 470, cx + 150, cy - 330), 18, (8, 8, 10),
          outline=(80, 80, 90), width=4)
    led = RED if flash <= 0 else (255, 120 + int(100 * flash), 120)
    d.text((cx, cy - 400), f"{floor:02d}", font=font(110), fill=led, anchor="mm")
    col = (120, 128, 140)
    rrect(d, (cx - 300, cy - 290, cx - 6, cy + 470), 10, col)
    rrect(d, (cx + 6, cy - 290, cx + 300, cy + 470), 10, col)
    for k in range(6):
        y = cy - 250 + k * 120
        d.line((cx - 280, y, cx - 26, y), fill=(140, 148, 160), width=3)
        d.line((cx + 26, y, cx + 280, y), fill=(140, 148, 160), width=3)


def scene_scenario(img, d, t):
    lt = t - SCENE_T["scenario"]
    fall_t = t - T_FALL
    fall_len = T_IMPACT - T_FALL
    floor, shake, flash = 20, (0, 0), 0.0
    if fall_t > 0:
        floor = max(0, 20 - int(fall_t / fall_len * 20))
        amp = 6 + 22 * clamp(fall_t / fall_len)
        rnd = random.Random(int(t * FPS))
        shake = (rnd.uniform(-amp, amp), rnd.uniform(-amp, amp))
        flash = 0.5 + 0.5 * math.sin(fall_t * 30)
        rnd2 = random.Random(7)
        for _ in range(26):
            x = rnd2.randrange(40, W - 40)
            speed = rnd2.uniform(1800, 3200)
            y = (rnd2.uniform(0, H) - fall_t * speed) % (H + 400) - 200
            d.line((x, y, x, y + rnd2.uniform(120, 320)), fill=(90, 100, 120),
                   width=4)
    a = ease_out(lt / 0.5)
    draw_elevator(d, W // 2, 820 + int((1 - a) * 80), floor, shake, flash)
    if fall_t > 0:
        paste_vignette(img, VIG_RED, 0.7)
    if t > T_IMPACT:  # Aufprall: Weißblitz
        k = clamp((t - T_IMPACT) / 0.25)
        d.rectangle((0, 0, W, H), fill=(int(255 * (1 - k)),) * 3)


OPTIONS = [
    ("A", "Kurz vor dem Aufprall", "hochspringen"),
    ("B", "An den Wänden", "festhalten"),
    ("C", "Flach auf den", "Boden legen"),
]


def draw_option(d, i, t_in, t, state=None, dim=False, active=False):
    letter, l1, l2 = OPTIONS[i]
    a = ease_out((t - t_in) / 0.35)
    if a <= 0:
        return
    y = 720 + i * 190
    x0 = 90 + int((1 - a) * 300)
    border = {None: AMBER if active else (70, 80, 96), "wrong": RED,
              "right": GREEN}[state]
    fill = CARD if not dim else (18, 21, 27)
    rrect(d, (x0, y, x0 + 900, y + 160), 28, fill, outline=border,
          width=8 if (state or active) else 4)
    circ = {None: AMBER, "wrong": RED, "right": GREEN}[state]
    d.ellipse((x0 + 30, y + 25, x0 + 140, y + 135), fill=circ)
    d.text((x0 + 85, y + 80), letter, font=font(70), fill=(10, 10, 10), anchor="mm")
    tc = WHITE if not dim else (90, 95, 105)
    d.text((x0 + 175, y + 52), l1, font=font(48), fill=tc, anchor="lm")
    d.text((x0 + 175, y + 108), l2, font=font(48), fill=tc, anchor="lm")
    cx, cy = x0 + 820, y + 80
    if state == "wrong":
        d.line((cx - 30, cy - 30, cx + 30, cy + 30), fill=RED, width=12)
        d.line((cx - 30, cy + 30, cx + 30, cy - 30), fill=RED, width=12)
    if state == "right":
        d.line((cx - 34, cy, cx - 8, cy + 28, cx + 38, cy - 30), fill=GREEN,
               width=12, joint="curve")


def scene_choice(img, d, t):
    text_c(d, (W // 2, 330), "WAS TUST DU?", 92 * punch(t, SCENE_T["choice"]),
           stroke=10)
    for i in range(3):
        nxt = T_OPT[i + 1] if i < 2 else T_COUNT[0]
        draw_option(d, i, T_OPT[i], t, active=T_OPT[i] <= t < nxt)
    c0, c_end = T_COUNT[0], T_COUNT[2] + 0.75
    if c0 <= t < c_end:
        k = 0 if t < T_COUNT[1] else (1 if t < T_COUNT[2] else 2)
        n = 3 - k
        seg_end = T_COUNT[k + 1] if k < 2 else c_end
        frac = (t - T_COUNT[k]) / (seg_end - T_COUNT[k])
        cx, cy, r = W // 2, 540, 105
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(60, 66, 78), width=14)
        d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * (1 - frac),
              fill=RED, width=14)
        text_c(d, (cx, cy), str(n), 120 * punch(t, T_COUNT[k], 0.3), stroke=0)
    elif t >= c_end:
        k = clamp((t - c_end) / 0.6)
        text_c(d, (W // 2, 540), "ZEIT UM!", 100 * punch(t, c_end), fill=RED)
        paste_vignette(img, VIG_RED, 1 - k)


def draw_bar(d, y, label, value, vmax, t_in, t, color):
    if t < t_in:
        return
    a = ease_out((t - t_in) / 0.8)
    d.text((100, y), label, font=font(46), fill=WHITE, anchor="lm")
    rrect(d, (100, y + 40, 980, y + 120), 18, (30, 34, 42))
    wbar = int(880 * value / vmax * a)
    if wbar > 36:
        rrect(d, (100, y + 40, 100 + wbar, y + 120), 18, color)
    d.text((960, y + 80), f"ca. {int(value * a)} km/h", font=font(44),
           fill=WHITE, anchor="rm", stroke_width=5, stroke_fill=(0, 0, 0))


def scene_wrong(img, d, t):
    t0 = SCENE_T["wrong"]
    draw_option(d, 0, 0, t, state="wrong")
    if t < 23.8:
        draw_option(d, 1, 0, t, dim=True)
        draw_option(d, 2, 0, t, dim=True)
        text_c(d, (W // 2, 400), "FALSCH!", 130 * punch(t, t0), fill=RED)
        return
    text_c(d, (W // 2, 400), "Aufprallgeschwindigkeit", 64, stroke=8)
    draw_bar(d, 950, "Ohne Sprung", 108, 120, 25.2, t, RED)
    draw_bar(d, 1110, "Mit perfektem Sprung", 94, 120, 28.44, t, AMBER)
    if t >= 31.3:
        rrect(d, (200, 540, 880, 660), 24, RED)
        text_c(d, (W // 2, 600), "WIDERLEGT", 80 * punch(t, 31.3), stroke=0)


def draw_person_lying(d, cx, cy, s=1.0, col=WHITE):
    d.ellipse((cx - 230 * s, cy - 40 * s, cx - 150 * s, cy + 40 * s), fill=col)
    d.line((cx - 150 * s, cy, cx + 110 * s, cy), fill=col, width=int(26 * s))
    d.line((cx + 110 * s, cy, cx + 230 * s, cy - 14 * s), fill=col, width=int(22 * s))
    d.line((cx + 110 * s, cy, cx + 230 * s, cy + 14 * s), fill=col, width=int(22 * s))
    d.line((cx - 100 * s, cy, cx - 30 * s, cy + 30 * s), fill=col, width=int(18 * s))


def draw_person_standing(d, cx, cy, col=WHITE):
    d.ellipse((cx - 38, cy - 240, cx + 38, cy - 164), fill=col)
    d.line((cx, cy - 164, cx, cy - 20), fill=col, width=24)
    d.line((cx, cy - 20, cx - 40, cy + 90), fill=col, width=20)
    d.line((cx, cy - 20, cx + 40, cy + 90), fill=col, width=20)
    d.line((cx, cy - 130, cx - 60, cy - 50), fill=col, width=16)
    d.line((cx, cy - 130, cx + 60, cy - 50), fill=col, width=16)


def arrow_up(d, x, y, ln, col, w):
    d.line((x, y, x, y - ln), fill=col, width=w)
    d.polygon([(x - w * 1.6, y - ln + 4), (x + w * 1.6, y - ln + 4),
               (x, y - ln - w * 2.6)], fill=col)


def scene_right(img, d, t):
    t0 = SCENE_T["right"]
    paste_vignette(img, VIG_GREEN, 0.55 * (1 - clamp((t - t0) / 0.6)))
    if t < 35.85:
        draw_option(d, 0, 0, t, dim=True)
        draw_option(d, 1, 0, t, dim=True)
        draw_option(d, 2, 0, t, state="right")
        text_c(d, (W // 2, 400), "RICHTIG: C", 110 * punch(t, t0), fill=GREEN)
        return
    if t < 42.45:
        text_c(d, (W // 2, 330), "Wo trifft dich der Aufprall?", 56)
        draw_person_standing(d, 280, 900, col=(200, 200, 210))
        d.line((140, 1000, 420, 1000), fill=GREY, width=8)
        arrow_up(d, 280, 1180, 150, RED, 22)
        d.text((280, 1250), "Beine +", font=font(42), fill=RED, anchor="mm")
        d.text((280, 1300), "Wirbelsäule", font=font(42), fill=RED, anchor="mm")
        if t >= 37.0:
            a = ease_out((t - 37.0) / 0.5)
            draw_person_lying(d, 790, 960, 0.85, col=(200, 200, 210))
            d.line((560, 1000, 1020, 1000), fill=GREY, width=8)
            for i in range(6):
                arrow_up(d, 620 + i * 66, 1150, int(110 * a), GREEN, 10)
            d.text((790, 1250), "verteilt auf", font=font(42), fill=GREEN, anchor="mm")
            d.text((790, 1300), "ganzen Körper", font=font(42), fill=GREEN, anchor="mm")
        d.line((W // 2, 650, W // 2, 1320), fill=(50, 56, 66), width=4)
        if t >= 40.54:
            rrect(d, (240, 520, 840, 610), 20, (60, 20, 26))
            text_c(d, (W // 2, 565), "Keine Garantie", 54, fill=WHITE, stroke=0,
                   alpha=ease_out((t - 40.54) / 0.3))
        return
    text_c(d, (W // 2, 330), "Die gute Nachricht", 72 * punch(t, 42.45), fill=GREEN)
    cx, top = W // 2, 470
    n_cables = 1 + min(3, int(max(0, t - 43.87) / 0.5))
    for i in range(n_cables):
        x = cx - 90 + i * 60
        d.line((x, top, x, 760), fill=(170, 176, 190), width=8)
    rrect(d, (cx - 230, 760, cx + 230, 1180), 20, (110, 118, 130))
    d.rectangle((cx - 4, 800, cx + 4, 1180), fill=(80, 86, 96))
    if t >= 45.6:
        for side in (-1, 1):
            bx = cx + side * 262
            rrect(d, (bx - 30, 900, bx + 30, 1040), 10, AMBER)
    d.text((cx, 1240), "Mehrere Seile · Fangbremsen", font=font(48), fill=WHITE,
           anchor="mm")
    if t >= 47.38:
        rrect(d, (120, 560, 960, 700), 26, (14, 50, 32), outline=GREEN, width=5)
        text_c(d, (W // 2, 630), "Freier Fall: extrem selten", 56 * punch(t, 47.38),
               stroke=0)


def draw_sand(d, t, t0):
    """Treibsand-Teaser: Figur sinkt langsam ein, Sand wellt sich."""
    k = ease_out((t - t0) / 6.0)
    base = 1180
    head_y = 860 + int(220 * k)
    col = (200, 200, 210)
    cx = W // 2
    d.ellipse((cx - 40, head_y - 40, cx + 40, head_y + 40), fill=col)
    d.line((cx, head_y + 40, cx, head_y + 220), fill=col, width=24)
    wave = math.sin(t * 6) * 18
    d.line((cx, head_y + 90, cx - 90, head_y + 20 + wave), fill=col, width=16)
    d.line((cx, head_y + 90, cx + 90, head_y + 20 - wave), fill=col, width=16)
    pts = [(0, base)]
    for x in range(0, W + 1, 30):
        pts.append((x, base + 10 * math.sin(x / 70 + t * 2)))
    pts += [(W, 1330), (0, 1330)]
    d.polygon(pts, fill=(176, 132, 72))
    for x in range(40, W, 90):
        d.ellipse((x, base + 50, x + 10, base + 60), fill=(140, 100, 52))


def scene_end(img, d, t):
    t0 = SCENE_T["end"]
    if t < 55.19:
        text_c(d, (W // 2, 520), "Hättest du", 100 * punch(t, t0))
        text_c(d, (W // 2, 640), "überlebt?", 120 * punch(t, t0), fill=AMBER)
        if t >= 51.89:
            for i, letter in enumerate("ABC"):
                x = W // 2 - 220 + i * 220
                sc = punch(t, 51.89 + i * 0.15)
                r = 75 * sc
                d.ellipse((x - r, 860 - r, x + r, 860 + r), fill=AMBER)
                d.text((x, 860), letter, font=font(90 * sc), fill=(10, 10, 10),
                       anchor="mm")
            text_c(d, (W // 2, 1020), "in die Kommentare", 52,
                   fill=GREY, stroke=0)
        return
    rrect(d, (140, 330, 940, 510), 30, (30, 22, 10), outline=AMBER, width=6)
    text_c(d, (W // 2, 390), "MORGEN · TAG 2", 50, fill=AMBER, stroke=0)
    text_c(d, (W // 2, 455), "TREIBSAND", 74 * punch(t, 55.19), stroke=0)
    draw_sand(d, t, 55.19)
    if t >= 61.17:
        pulse = 1 + 0.06 * math.sin((t - 61.17) * 8)
        bw, bh = 420 * pulse, 120 * pulse
        rrect(d, (W / 2 - bw / 2, 600 - bh / 2, W / 2 + bw / 2, 600 + bh / 2), 60, RED)
        text_c(d, (W // 2, 600), "FOLGEN", 64 * pulse, stroke=0)


SCENES = [
    (0.0, SCENE_T["scenario"], scene_hook),
    (SCENE_T["scenario"], SCENE_T["choice"], scene_scenario),
    (SCENE_T["choice"], SCENE_T["wrong"], scene_choice),
    (SCENE_T["wrong"], SCENE_T["right"], scene_wrong),
    (SCENE_T["right"], SCENE_T["end"], scene_right),
    (SCENE_T["end"], DUR, scene_end),
]


def render_frame(t):
    img = BG.copy()
    d = ImageDraw.Draw(img)
    for s, e, fn in SCENES:
        if s <= t < e:
            fn(img, d, t)
            break
    img.paste(VIG_DARK, (0, 0), VIG_DARK)
    d = ImageDraw.Draw(img)
    draw_badge(d, t)
    draw_caption(d, t)
    for s, _, fn in SCENES[2:]:  # kurze Schwarzblende (nicht nach dem Aufprall)
        if abs(t - s) < 0.12:
            k = 1 - abs(t - s) / 0.12
            img = Image.blend(img, Image.new("RGB", (W, H)), k * 0.8)
    if t > DUR - 0.5:
        img = Image.blend(img, Image.new("RGB", (W, H)), (t - (DUR - 0.5)) / 0.5)
    return img


# ---------------------------------------------------------------- Effekte
SR = 44100


def synth_sfx(path):
    n = int(DUR * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    rng = np.random.default_rng(1)

    def add(start, sig):
        i = int(start * SR)
        j = min(n, i + len(sig))
        out[i:j] += sig[: j - i]

    def env(length, attack=0.005, decay=None):
        m = int(length * SR)
        e = np.ones(m)
        a = max(1, int(attack * SR))
        e[:a] = np.linspace(0, 1, a)
        if decay:
            e *= np.exp(-np.arange(m) / (decay * SR))
        return e

    def sine(freq, length, amp=1.0):
        x = np.arange(int(length * SR)) / SR
        return amp * np.sin(2 * np.pi * freq * x)

    c_end = T_COUNT[2] + 0.75
    lvl = np.interp(tt, [0, 9, c_end, c_end + 0.6, 50, 55, 64, DUR],
                    [0.05, 0.08, 0.13, 0.05, 0.04, 0.07, 0.07, 0.0])
    lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.2 * tt)
    out += lvl * lfo * (np.sin(2 * np.pi * 55 * tt) + 0.6 * np.sin(2 * np.pi * 82.4 * tt))

    def beat(at, amp=0.55):
        for off, a in ((0, 1.0), (0.22, 0.7)):
            add(at + off, sine(58, 0.25, amp * a) * env(0.25, decay=0.06))
    for t0 in np.arange(0.0, T_FALL, 0.8):
        beat(t0)
    for t0 in np.arange(10.4, c_end, 0.6):
        beat(t0, 0.4)
    for t0 in np.arange(55.2, 61.0, 0.9):
        beat(t0, 0.35)

    for t0 in np.arange(10.0, c_end, 0.5):  # Ticken
        add(t0, rng.normal(0, 1, int(0.02 * SR)) * env(0.02, 0.001, 0.004) * 0.25)
    for tc in T_COUNT:
        add(tc, sine(880, 0.15, 0.3) * env(0.15, decay=0.08))
    add(c_end, (np.sign(sine(110, 0.6)) * 0.18) * env(0.6, decay=0.3))

    for s in list(SCENE_T.values()) + [55.19]:  # Whoosh
        m = int(0.6 * SR)
        noise = np.convolve(rng.normal(0, 1, m), np.ones(30) / 30, mode="same")
        add(s - 0.35, noise * np.sin(np.linspace(0, np.pi, m)) ** 2 * 0.6)

    m = int((T_IMPACT - T_FALL + 0.05) * SR)  # Fall + Aufprall
    f = np.linspace(420, 70, m)
    sweep = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.18
    rumble = np.convolve(rng.normal(0, 1, m), np.ones(200) / 200, mode="same") * 2.5
    add(T_FALL, (sweep + rumble) * np.linspace(0.3, 1, m))
    boom = sine(45, 1.2, 0.9) * env(1.2, decay=0.25)
    boom += rng.normal(0, 1, len(boom)) * env(1.2, decay=0.05) * 0.5
    add(T_IMPACT, boom)

    add(SCENE_T["wrong"], (np.sign(sine(140, 0.45)) * 0.16) * env(0.45, decay=0.2))
    for k, fr in enumerate((523.25, 659.25, 783.99)):
        add(SCENE_T["right"] + k * 0.09, sine(fr, 0.7, 0.22) * env(0.7, decay=0.25))
    add(31.3, sine(70, 0.5, 0.5) * env(0.5, decay=0.12))
    for k in range(3):
        add(51.89 + k * 0.15, sine(660, 0.12, 0.18) * env(0.12, decay=0.05))
    add(61.17, sine(392, 0.9, 0.2) * env(0.9, decay=0.35))

    out /= max(1e-9, np.abs(out).max()) / 0.9
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sfx = os.path.join(OUT_DIR, "folge01-sfx.wav")
    mp4 = os.path.join(OUT_DIR, "folge01-fahrstuhl.mp4")
    synth_sfx(sfx)
    # Effekte werden unter der Stimme automatisch leiser (Ducking),
    # danach Lautheit auf ca. -14 LUFS (üblich für Social Media)
    af = ("[1:a]aresample=44100,aformat=channel_layouts=stereo,asplit=2[v1][v2];"
          "[2:a]volume=0.5[fx];"
          "[fx][v1]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=350[duck];"
          "[duck][v2]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", VOICE, "-i", sfx,
           "-filter_complex", af, "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
           "-t", str(DUR), "-movflags", "+faststart", mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        p.stdin.write(render_frame(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    os.remove(sfx)
    print(mp4)


if __name__ == "__main__":
    main()
