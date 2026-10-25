"""Rendert Folge 2 „Überlebst du das? – Treibsand“ passend zur Stimme in
folgen/folge-02/stimme.mp3.

Aufruf:  python3 video/render_folge02.py
Ergebnis: video/out/folge02-treibsand.mp4
"""
import math
import os

from PIL import Image, ImageDraw

from common import (AMBER, BLUE, FIGURE, GREEN, GREY, RED, ROOT, SAND,
                    SAND_DARK, VIG_GREEN, VIG_RED, W, WHITE, Sfx, arrow_up,
                    build_captions, clamp, compose_frame, draw_choice,
                    draw_comment_prompt, draw_follow_button, draw_option,
                    draw_tomorrow, ease_out, font, paste_vignette, punch, render,
                    rrect, text_c)

DAY = 2
VOICE = os.path.join(ROOT, "folgen", "folge-02", "stimme.mp3")
DUR = 60.3

SENTENCES = [
    (0.00, 1.00, "Du sinkst."),
    (1.14, 3.64, "Und je mehr du kämpfst, desto schneller geht es."),
    (4.12, 6.26, "Du steckst bis zu den Knien im Treibsand."),
    (6.64, 7.27, "Was tust du?"),
    (17.84, 18.33, "Drei."),
    (18.85, 19.43, "Zwei."),
    (20.10, 20.61, "Eins."),
    (21.28, 23.16, "Die meisten wählen A oder B."),
    (23.75, 27.10, "Aber ein Bein auch nur 1 cm pro Sekunde rauszuziehen,"),
    (27.20, 29.81, "braucht so viel Kraft, wie ein Auto anzuheben."),
    (30.36, 31.41, "Richtig ist C."),
    (31.93, 34.40, "Durch langsame Bewegungen fließt Wasser nach,"),
    (34.50, 37.40, "der Sand wird locker, und du kommst Stück für Stück frei."),
    (37.91, 38.92, "Und die gute Nachricht:"),
    (39.28, 41.87, "Treibsand ist etwa doppelt so dicht wie dein Körper."),
    (42.23, 43.79, "Komplett versinken wie im Film?"),
    (44.22, 45.00, "Unmöglich."),
    (45.45, 46.31, "Hättest du's gewusst?"),
    (46.68, 49.20, "Schreib A, B oder C in die Kommentare."),
    (49.76, 51.94, "Und morgen: Ein Bär rennt auf dich zu."),
    (52.34, 54.07, "Dein Instinkt schreit: Lauf!"),
    (54.44, 56.08, "Und genau das ist der Fehler."),
    (56.52, 59.30, "Folg mir – sonst weißt du nicht, was dich rettet."),
]
CAPTIONS = build_captions(SENTENCES, DUR)

OPTIONS = [
    ("A", "Bein mit aller Kraft", "rausziehen"),
    ("B", "Von einem Freund", "rausziehen lassen"),
    ("C", "Ruhig bleiben, Beine", "langsam bewegen"),
]
T_OPT = (7.89, 11.13, 14.11)
T_COUNT = (17.84, 18.85, 20.10)
C_END = T_COUNT[2] + 0.75
T = {"scenario": 4.1, "choice": 6.64, "wrong": 21.28, "right": 30.36,
     "good": 37.91, "end": 45.45, "tomorrow": 49.76}

SURFACE = 1150


# ---------------------------------------------------------------- Treibsand
def _legs(d, cx, fy, wiggle, col, width=20):
    for side in (-1, 1):
        kx = cx + side * 38 + wiggle * side
        d.line((cx + side * 12, fy - 170, kx, fy - 85, kx - side * 4, fy),
               fill=col, width=width, joint="curve")


def draw_sand_figure(img, d, t, depth, arms="calm", wiggle=0.0, water=0.0,
                     cx=W // 2):
    """Figur steckt `depth` Pixel tief im Sand (85 = Knie, 170 = Hüfte).
    Sand im Querschnitt: Beine darin dunkel sichtbar."""
    fy = SURFACE + depth
    col = FIGURE
    d.ellipse((cx - 40, fy - 420, cx + 40, fy - 340), fill=col)
    d.line((cx, fy - 340, cx, fy - 170), fill=col, width=26)
    sy = fy - 310
    if arms == "flail":
        a = math.sin(t * 9)
        ends = [(cx - 120, sy - 90 * a), (cx + 120, sy + 90 * a)]
    elif arms == "up":
        ends = [(cx - 95, sy - 110), (cx + 95, sy - 110)]
    else:
        ends = [(cx - 70, sy + 120), (cx + 70, sy + 120)]
    for ex, ey in ends:
        d.line((cx, sy, ex, ey), fill=col, width=18)
    _legs(d, cx, fy, wiggle, col)
    # Sand mit welliger Oberfläche
    pts = [(0, SURFACE)]
    for x in range(0, W + 1, 30):
        pts.append((x, SURFACE + 8 * math.sin(x / 70 + t * 2)))
    pts += [(W, SURFACE + 200), (0, SURFACE + 200)]
    d.polygon(pts, fill=SAND)
    for i in range(14):
        x = (i * 97 + 40) % W
        y = SURFACE + 30 + (i * 53) % 150
        d.ellipse((x, y, x + 10, y + 10), fill=SAND_DARK)
    # Beine im Querschnitt
    hip = fy - 170
    if hip < SURFACE:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        _legs(ld, cx, fy, wiggle, (90, 62, 30, 255))
        layer = layer.crop((0, SURFACE, W, SURFACE + 200))
        img.paste(layer, (0, SURFACE), layer)
    else:
        d.rectangle((cx - 40, SURFACE + 4, cx + 40, fy), fill=(90, 62, 30))
    if water > 0:  # Wassertropfen fließen an den Beinen nach unten
        for i in range(10):
            ph = (t * 0.9 + i / 10) % 1.0
            side = -1 if i % 2 else 1
            x = cx + side * (60 + (i % 3) * 14)
            y = SURFACE + 10 + ph * (depth - 10)
            r = 9
            col_w = tuple(int(c * water) for c in BLUE)
            d.ellipse((x - r, y - r * 1.4, x + r, y + r), fill=col_w)


def scene_hook(img, d, t):
    pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 1.25)
    paste_vignette(img, VIG_RED, 0.35 + 0.45 * pulse)
    depth = 60 + 110 * ease_out(t / 4.0)
    draw_sand_figure(img, d, t, depth, arms="flail", wiggle=14 * math.sin(t * 11))
    sc = punch(t, 0.0, 0.5)
    text_c(d, (W // 2, 420), "ÜBERLEBST", 120 * sc, stroke=12)
    text_c(d, (W // 2, 560), "DU DAS?", 150 * sc, fill=RED, stroke=12)


def scene_scenario(img, d, t):
    draw_sand_figure(img, d, t, 85, arms="calm")
    a = ease_out((t - 4.6) / 0.4)
    if a > 0:
        d.line((640, SURFACE + 40, 760, SURFACE + 40), fill=WHITE, width=6)
        d.text((780, SURFACE + 40), "Knietief", font=font(52), fill=WHITE,
               anchor="lm", stroke_width=6, stroke_fill=(0, 0, 0))
    text_c(d, (W // 2, 420), "TREIBSAND", 110 * punch(t, T["scenario"]), fill=AMBER)


def scene_choice(img, d, t):
    draw_choice(img, d, t, OPTIONS, T["choice"], T_OPT, T_COUNT)


def draw_car(d, cx, cy, s=1.0):
    col = (120, 128, 140)
    rrect(d, (cx - 170 * s, cy - 40 * s, cx + 170 * s, cy + 50 * s), int(24 * s), col)
    d.polygon([(cx - 100 * s, cy - 40 * s), (cx - 60 * s, cy - 110 * s),
               (cx + 70 * s, cy - 110 * s), (cx + 120 * s, cy - 40 * s)], fill=col)
    d.polygon([(cx - 80 * s, cy - 45 * s), (cx - 52 * s, cy - 98 * s),
               (cx - 5 * s, cy - 98 * s), (cx - 5 * s, cy - 45 * s)], fill=(50, 70, 90))
    d.polygon([(cx + 5 * s, cy - 45 * s), (cx + 5 * s, cy - 98 * s),
               (cx + 62 * s, cy - 98 * s), (cx + 100 * s, cy - 45 * s)], fill=(50, 70, 90))
    for wx in (-100, 100):
        d.ellipse((cx + (wx - 42) * s, cy + 8 * s, cx + (wx + 42) * s, cy + 92 * s),
                  fill=(25, 25, 28))


def scene_wrong(img, d, t):
    if t < 23.75:
        draw_option(d, OPTIONS[0], 0, 0, t, state="wrong")
        draw_option(d, OPTIONS[1], 1, 0, t, state="wrong")
        draw_option(d, OPTIONS[2], 2, 0, t, dim=True)
        text_c(d, (W // 2, 420), "FALSCH!", 130 * punch(t, T["wrong"]), fill=RED)
        return
    text_c(d, (W // 2, 330), "Wie viel Kraft?", 80 * punch(t, 23.75))
    # links: Bein im Sand, Pfeil nach oben
    lx, base = 260, 1030
    d.rectangle((90, base - 20, 430, base + 160), fill=SAND)
    d.line((lx, base - 260, lx, base + 120), fill=FIGURE, width=34)
    d.line((lx, base + 120, lx + 50, base + 130), fill=FIGURE, width=26)
    a = ease_out((t - 24.3) / 0.6)
    arrow_up(d, lx + 110, base - 60, int(260 * a), AMBER, 14)
    if a > 0:
        d.text((lx, base + 220), "1 cm pro Sek.", font=font(46), fill=AMBER,
               anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0))
    if t >= 27.2:
        text_c(d, (W // 2 + 10, 860), "=", 140 * punch(t, 27.2), fill=WHITE)
        b = ease_out((t - 27.2) / 0.6)
        lift = int(110 * b)
        draw_car(d, 800, 990 - lift, 0.95)
        arrow_up(d, 800, 1120, int(120 * b), AMBER, 14)
        d.text((800, base + 220), "Auto anheben", font=font(46), fill=AMBER,
               anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0))


def scene_right(img, d, t):
    paste_vignette(img, VIG_GREEN, 0.55 * (1 - clamp((t - T["right"]) / 0.6)))
    if t < 31.93:
        draw_option(d, OPTIONS[0], 0, 0, t, dim=True)
        draw_option(d, OPTIONS[1], 1, 0, t, dim=True)
        draw_option(d, OPTIONS[2], 2, 0, t, state="right")
        text_c(d, (W // 2, 420), "RICHTIG: C", 110 * punch(t, T["right"]), fill=GREEN)
        return
    rise = ease_out((t - 34.5) / 2.9)
    depth = 85 - 60 * rise
    draw_sand_figure(img, d, t, depth, arms="calm",
                     wiggle=8 * math.sin(t * 4), water=clamp((t - 31.93) / 0.5))
    text_c(d, (W // 2, 360), "Langsam bewegen", 74 * punch(t, 31.93), fill=GREEN)
    if t >= 32.3:
        text_c(d, (W // 2, 480), "Wasser fließt nach", 54,
               fill=BLUE, alpha=ease_out((t - 32.3) / 0.4))
    if t >= 34.5:
        text_c(d, (W // 2, 570), "Sand wird locker", 54, fill=AMBER,
               alpha=ease_out((t - 34.5) / 0.4))


def scene_good(img, d, t):
    if t < 42.23:
        text_c(d, (W // 2, 330), "Die gute Nachricht", 76 * punch(t, T["good"]),
               fill=GREEN)
        if t < 39.28:
            return
        a = ease_out((t - 39.28) / 0.8)
        base = 1250
        for i, (label, val, col, unit) in enumerate(
                (("Treibsand", 2, SAND, "ca. 2 g/cm³"),
                 ("Dein Körper", 1, FIGURE, "ca. 1 g/cm³"))):
            x = 300 + i * 480
            h = int(320 * val * a)
            rrect(d, (x - 110, base - h, x + 110, base), 16, col)
            d.text((x, base + 50), label, font=font(48), fill=WHITE, anchor="mm")
            d.text((x, base - h - 45), unit, font=font(40), fill=GREY, anchor="mm")
        if t >= 40.6:
            text_c(d, (W // 2, 520), "doppelt so dicht", 66 * punch(t, 40.6),
                   fill=AMBER)
        return
    draw_sand_figure(img, d, t, 170, arms="up")
    for x in range(60, W - 60, 50):  # gestrichelte Linie an der Hüfte
        d.line((x, SURFACE - 2, x + 26, SURFACE - 2), fill=GREEN, width=6)
    d.text((W - 70, SURFACE - 40), "max. Hüfte", font=font(46), fill=GREEN,
           anchor="rm", stroke_width=6, stroke_fill=(0, 0, 0))
    text_c(d, (W // 2, 330), "Komplett versinken?", 76 * punch(t, 42.23))
    if t >= 44.22:
        sc = punch(t, 44.22)
        rrect(d, (170, 430, 910, 570), 26, (14, 50, 32), outline=GREEN, width=6)
        text_c(d, (W // 2, 500), "UNMÖGLICH", 88 * sc, fill=GREEN, stroke=0)


def draw_bear(d, cx, gy, s, t):
    bob = 10 * s * abs(math.sin(t * 7))
    gy -= bob
    col, dark = (112, 76, 46), (80, 52, 30)
    for lx in (-150, -70, 60, 130):  # Beine
        sw = 18 * s * math.sin(t * 7 + lx)
        d.rounded_rectangle((cx + (lx - 28) * s + sw, gy - 130 * s,
                             cx + (lx + 28) * s + sw, gy), int(14 * s), fill=dark)
    d.ellipse((cx - 230 * s, gy - 330 * s, cx + 190 * s, gy - 100 * s), fill=col)
    d.ellipse((cx - 120 * s, gy - 380 * s, cx + 80 * s, gy - 220 * s), fill=col)
    hx, hy = cx + 200 * s, gy - 270 * s
    for ex in (-55, 45):
        d.ellipse((hx + (ex - 24) * s, hy - 110 * s, hx + (ex + 24) * s, hy - 62 * s),
                  fill=dark)
    d.ellipse((hx - 95 * s, hy - 90 * s, hx + 95 * s, hy + 90 * s), fill=col)
    d.ellipse((hx + 30 * s, hy - 5 * s, hx + 130 * s, hy + 70 * s), fill=(150, 108, 70))
    d.ellipse((hx + 95 * s, hy + 5 * s, hx + 128 * s, hy + 35 * s), fill=(20, 15, 12))
    d.ellipse((hx + 10 * s, hy - 40 * s, hx + 34 * s, hy - 16 * s), fill=(20, 15, 12))


def scene_end(img, d, t):
    if t < T["tomorrow"]:
        draw_comment_prompt(d, t, T["end"], 46.68, "Hättest du's", "gewusst?")
        return
    draw_tomorrow(d, t, T["tomorrow"], 3, "BÄRENANGRIFF")
    k = ease_out((t - T["tomorrow"]) / 4.0)
    draw_bear(d, W // 2 - 60, 1290, 0.75 + 0.55 * k, t)
    if 52.34 <= t < 56.52:
        text_c(d, (W // 2, 640), "LAUF!", 150 * punch(t, 52.34), fill=RED, stroke=12)
        if t >= 54.44:
            x = ease_out((t - 54.44) / 0.3)
            d.line((300, 690, 300 + 480 * x, 590), fill=WHITE, width=18)
            text_c(d, (W // 2, 760), "FEHLER!", 70 * punch(t, 54.44), fill=AMBER)
    if t >= 56.52:
        paste_vignette(img, VIG_RED, 0.4)
        draw_follow_button(d, t, 56.52, y=640)


SCENES = [
    (0.0, T["scenario"], scene_hook),
    (T["scenario"], T["choice"], scene_scenario),
    (T["choice"], T["wrong"], scene_choice),
    (T["wrong"], T["right"], scene_wrong),
    (T["right"], T["good"], scene_right),
    (T["good"], T["end"], scene_good),
    (T["end"], DUR, scene_end),
]


def frame(t):
    return compose_frame(t, SCENES, DAY, CAPTIONS, DUR)


def make_sfx():
    s = Sfx(DUR)
    s.drone([0, 6.6, C_END, C_END + 0.6, 45, 50, 56, DUR],
            [0.07, 0.08, 0.13, 0.05, 0.04, 0.09, 0.09, 0.0])
    s.heartbeat(0, 6.6, 0.8)
    s.rumble(0, 4.0, 1.5)
    s.heartbeat(8.0, C_END, 0.6, 0.4)
    s.ticks(7.3, C_END)
    for tc in T_COUNT:
        s.beep(tc)
    s.buzzer(C_END, freq=110, length=0.6, amp=0.18)
    for v in T.values():
        s.whoosh(v)
    s.buzzer(T["wrong"])
    s.thud(27.2, 0.6)
    s.chime(T["right"])
    s.soft(44.22, 523.25)
    s.pops(46.68)
    s.rumble(T["tomorrow"], 5.0, 2.5)
    s.heartbeat(T["tomorrow"], 56.5, 0.5, 0.45)
    s.thud(52.34, 0.7)
    s.buzzer(54.44)
    s.soft(56.52)
    return s


if __name__ == "__main__":
    print(render("folge02-treibsand", VOICE, make_sfx(), frame, DUR))
