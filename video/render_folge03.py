"""Rendert Folge 3 „Überlebst du das? – Bärenangriff“ passend zur Stimme in
folgen/folge-03/stimme.mp3.

Aufruf:  python3 video/render_folge03.py
Ergebnis: video/out/folge03-baer.mp4
"""
import math
import os

from common import (AMBER, FIGURE, GREEN, GREY, RED, ROOT, SAND,
                    VIG_GREEN, VIG_RED, W, WHITE, Sfx, build_captions, clamp,
                    compose_frame, draw_bear, draw_choice, draw_comment_prompt,
                    draw_follow_button, draw_option, draw_tomorrow, ease_out,
                    font, paste_vignette, punch, render, rrect, text_c)

DAY = 3
VOICE = os.path.join(ROOT, "folgen", "folge-03", "stimme.mp3")
DUR = 67.5

SENTENCES = [
    (0.00, 1.35, "Ein Bär rennt auf dich zu."),
    (1.70, 2.85, "Du hast zwei Sekunden."),
    (3.70, 4.87, "Du wanderst in Kanada."),
    (5.30, 7.45, "Plötzlich bricht ein Braunbär aus dem Gebüsch –"),
    (7.80, 8.79, "und stürmt los."),
    (9.21, 9.89, "Was tust du?"),
    (19.67, 20.10, "Drei."),
    (20.55, 21.07, "Zwei."),
    (21.61, 22.07, "Eins."),
    (22.75, 24.09, "Die meisten wählen A."),
    (24.47, 26.75, "Aber Wegrennen kann den Angriff erst auslösen."),
    (27.28, 30.00, "Die US-Nationalparkbehörde sagt ganz klar:"),
    (30.34, 31.37, "Niemals rennen."),
    (31.83, 34.48, "Greift der Braunbär wirklich an, ist C richtig."),
    (34.86, 37.45, "Leg dich flach auf den Bauch, Hände in den Nacken,"),
    (37.50, 38.53, "Rucksack bleibt an,"),
    (38.86, 39.69, "Beine auseinander –"),
    (40.07, 41.38, "damit er dich nicht umdrehen kann."),
    (41.78, 43.71, "Bleib still liegen, bis er weg ist."),
    (44.09, 44.62, "Aber Achtung:"),
    (45.03, 48.12, "Ist es ein Schwarzbär, ist Totstellen genau falsch."),
    (48.42, 49.47, "Dann musst du kämpfen –"),
    (49.88, 51.62, "Schläge auf Gesicht und Schnauze."),
    (52.17, 53.10, "Hättest du's gewusst?"),
    (53.25, 55.97, "Schreib A, B oder C in die Kommentare."),
    (56.40, 56.96, "Und morgen:"),
    (57.42, 58.80, "Das Meer zieht dich raus."),
    (59.13, 61.02, "Du schwimmst mit aller Kraft zum Strand –"),
    (61.33, 62.56, "und kommst trotzdem nicht an."),
    (63.00, 63.55, "Folg mir –"),
    (63.89, 67.00, "sonst kämpfst du gegen einen Gegner, den du nicht besiegen kannst."),
]
CAPTIONS = build_captions(SENTENCES, DUR)

OPTIONS = [
    ("A", "So schnell du kannst", "wegrennen"),
    ("B", "Groß machen und", "zurückschlagen"),
    ("C", "Auf den Bauch legen,", "tot stellen"),
]
T_OPT = (10.55, 13.37, 16.31)
T_COUNT = (19.67, 20.55, 21.61)
C_END = T_COUNT[2] + 0.75
T = {"scenario": 3.6, "choice": 9.15, "wrong": 22.75, "right": 31.83,
     "twist": 44.09, "end": 52.17, "tomorrow": 56.40}

GROUND = 1240
BLACK_BEAR = dict(col=(44, 44, 50), dark=(26, 26, 30), snout=(150, 120, 90))


# ---------------------------------------------------------------- Bausteine
def draw_ground(d):
    d.rectangle((0, GROUND, W, GROUND + 100), fill=(34, 52, 30))
    d.line((0, GROUND, W, GROUND), fill=(60, 88, 50), width=6)


def draw_tree(d, x, h, col=(22, 58, 36)):
    d.rectangle((x - 14, GROUND - 90, x + 14, GROUND), fill=(60, 40, 26))
    for k in range(3):
        y0 = GROUND - 80 - k * h * 0.28
        wdt = 110 - k * 25
        d.polygon([(x - wdt, y0), (x + wdt, y0), (x, y0 - h * 0.45)], fill=col)


def draw_bush(d, cx, t, shake=0.0):
    dx = shake * math.sin(t * 40) * 12
    for ox, oy, r in ((-90, 0, 80), (0, -40, 100), (90, 0, 80)):
        x = cx + ox + dx
        d.ellipse((x - r, GROUND - 60 + oy - r, x + r, GROUND - 60 + oy + r),
                  fill=(36, 80, 40))


def draw_hiker(d, cx, t, run=False, s=1.0, facing=1):
    """Wanderer mit Rucksack, steht oder rennt (Blickrichtung facing)."""
    fy = GROUND
    col = FIGURE
    sw = math.sin(t * 14) if run else 0.0
    lean = 30 * facing if run else 0
    hx, hy = cx + lean * 0.6, fy - 380 * s
    d.ellipse((hx - 38 * s, hy - 38 * s, hx + 38 * s, hy + 38 * s), fill=col)
    sx, sy = cx + lean * 0.4, fy - 330 * s
    hipx, hipy = cx, fy - 170 * s
    rrect(d, (sx - facing * 70 * s - 30 * s, sy - 10 * s,
              sx - facing * 70 * s + 30 * s, sy + 110 * s), int(10 * s), (60, 90, 60))
    d.line((sx, sy, hipx, hipy), fill=col, width=int(24 * s))
    for k in (-1, 1):
        a = sw * k
        d.line((hipx, hipy, hipx + 70 * s * a, fy - 85 * s,
                hipx + 110 * s * a, fy), fill=col, width=int(20 * s), joint="curve")
        d.line((sx, sy + 20 * s, sx - 80 * s * a, sy + 110 * s), fill=col,
               width=int(16 * s))


def draw_lying_topview(d, t, cx=W // 2, top=640, labels=()):
    """Person bäuchlings von oben: Hände im Nacken, Rucksack, Beine gespreizt."""
    col = FIGURE
    d.line((cx - 40, top + 300, cx - 150, top + 560), fill=col, width=34)
    d.line((cx + 40, top + 300, cx + 150, top + 560), fill=col, width=34)
    rrect(d, (cx - 75, top + 70, cx + 75, top + 320), 40, col)
    for k in (-1, 1):  # Arme: Schulter → Ellbogen außen → Hände im Nacken
        d.line((cx + k * 70, top + 90, cx + k * 150, top + 20, cx + k * 18, top + 40),
               fill=col, width=26, joint="curve")
    d.ellipse((cx - 50, top - 40, cx + 50, top + 60), fill=col)
    d.ellipse((cx - 22, top + 28, cx + 22, top + 58), fill=(230, 200, 170))
    rrect(d, (cx - 60, top + 110, cx + 60, top + 280), 18, (60, 90, 60))
    callouts = {
        "nacken": ((cx + 150, top + 20), (cx + 300, top - 60), "Hände in den Nacken"),
        "rucksack": ((cx + 60, top + 200), (cx + 300, top + 200), "Rucksack an"),
        "beine": ((cx + 150, top + 540), (cx + 300, top + 470), "Beine auseinander"),
    }
    for key, t0 in labels:
        if t < t0:
            continue
        (x0, y0), (x1, y1), txt = callouts[key]
        d.line((x0, y0, x1, y1), fill=AMBER, width=5)
        d.text((W - 40, y1 - 34), txt, font=font(44 * punch(t, t0, 0.25)),
               fill=AMBER, anchor="rm", stroke_width=6, stroke_fill=(0, 0, 0))


# ---------------------------------------------------------------- Szenen
def scene_hook(img, d, t):
    pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 1.6)
    paste_vignette(img, VIG_RED, 0.35 + 0.45 * pulse)
    draw_ground(d)
    k = ease_out(t / 3.6)
    draw_bear(d, W // 2 - 80, GROUND, 0.7 + 0.7 * k, t * 1.4)
    sc = punch(t, 0.0, 0.5)
    text_c(d, (W // 2, 400), "ÜBERLEBST", 120 * sc, stroke=12)
    text_c(d, (W // 2, 540), "DU DAS?", 150 * sc, fill=RED, stroke=12)


def scene_scenario(img, d, t):
    for x, h in ((80, 520), (330, 640), (760, 580), (1000, 500)):
        draw_tree(d, x, h)
    draw_ground(d)
    burst = t >= 5.3
    if not burst:
        draw_bush(d, 820, t)
    else:
        k = ease_out((t - 5.3) / 0.6)
        run = clamp((t - 7.8) / 1.0)
        bx = 1000 - 200 * k - 260 * run
        draw_bear(d, bx, GROUND, 0.75, t, walk=t >= 7.8)
        draw_bush(d, 900, t, shake=1 - clamp((t - 5.3) / 0.8))
        d.text((bx + 80, GROUND - 360), "BRAUNBÄR", font=font(50), fill=AMBER,
               anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
        if t >= 7.8:
            paste_vignette(img, VIG_RED, 0.6)
    draw_hiker(d, 260, t, facing=1)
    text_c(d, (W // 2, 330), "KANADA", 90 * punch(t, T["scenario"]), fill=GREEN)


def scene_choice(img, d, t):
    draw_choice(img, d, t, OPTIONS, T["choice"], T_OPT, T_COUNT)


def scene_wrong(img, d, t):
    if t < 24.47:
        draw_option(d, OPTIONS[0], 0, 0, t, state="wrong")
        draw_option(d, OPTIONS[1], 1, 0, t, dim=True)
        draw_option(d, OPTIONS[2], 2, 0, t, dim=True)
        text_c(d, (W // 2, 420), "FALSCH!", 130 * punch(t, T["wrong"]), fill=RED)
        return
    draw_ground(d)
    k = (t - 24.47) / 6.0
    hx = 760 + 120 * k
    draw_hiker(d, hx, t, run=True, facing=1)
    draw_bear(d, hx - 520 + 160 * ease_out(k * 2), GROUND, 0.75, t * 1.3)
    if t < 27.28:
        text_c(d, (W // 2, 360), "Rennen kann den", 66 * punch(t, 24.47))
        text_c(d, (W // 2, 450), "Angriff auslösen", 66 * punch(t, 24.47), fill=RED)
        return
    rrect(d, (130, 300, 950, 470), 26, (22, 40, 30), outline=GREEN, width=5)
    text_c(d, (W // 2, 350), "US-Nationalparkbehörde", 50, fill=GREEN, stroke=0)
    text_c(d, (W // 2, 420), "(National Park Service)", 40, fill=GREY, stroke=0)
    if t >= 30.34:
        rrect(d, (150, 540, 930, 680), 26, RED)
        text_c(d, (W // 2, 610), "NIEMALS RENNEN", 76 * punch(t, 30.34), stroke=0)


def scene_right(img, d, t):
    paste_vignette(img, VIG_GREEN, 0.55 * (1 - clamp((t - T["right"]) / 0.6)))
    if t < 34.86:
        draw_option(d, OPTIONS[0], 0, 0, t, dim=True)
        draw_option(d, OPTIONS[1], 1, 0, t, dim=True)
        draw_option(d, OPTIONS[2], 2, 0, t, state="right")
        text_c(d, (W // 2, 400), "RICHTIG: C", 110 * punch(t, T["right"]), fill=GREEN)
        text_c(d, (W // 2, 520), "bei Braunbär-Angriff", 52, fill=GREY, stroke=0)
        return
    if t < 41.78:
        text_c(d, (W // 2, 330), "So geht's richtig", 72 * punch(t, 34.86), fill=GREEN)
        draw_lying_topview(d, t, labels=(("nacken", 36.2), ("rucksack", 37.5),
                                         ("beine", 38.86)))
        return
    text_c(d, (W // 2, 330), "Still liegen …", 76 * punch(t, 41.78), fill=GREEN)
    draw_ground(d)
    rrect(d, (240, GROUND - 60, 560, GROUND - 10), 24, FIGURE)  # liegende Person
    d.ellipse((190, GROUND - 75, 270, GROUND + 5), fill=FIGURE)
    rrect(d, (300, GROUND - 95, 440, GROUND - 50), 12, (60, 90, 60))
    k = ease_out((t - 42.3) / 1.6)
    draw_bear(d, 700 + 420 * k, GROUND, 0.7, t, walk=k > 0)
    if t >= 42.6:
        text_c(d, (W // 2, 450), "… bis er weg ist", 64, fill=WHITE,
               alpha=ease_out((t - 42.6) / 0.4))


def scene_twist(img, d, t):
    text_c(d, (W // 2, 330), "ACHTUNG!", 110 * punch(t, T["twist"]), fill=AMBER)
    if t < 45.03:
        return
    a = ease_out((t - 45.03) / 0.5)
    for i, (name, kw) in enumerate((("Braunbär", {}), ("Schwarzbär", BLACK_BEAR))):
        cx = 290 + i * 500
        rrect(d, (cx - 230, 480, cx + 230, 1180), 30, (22, 26, 34),
              outline=(60, 66, 78), width=4)
        draw_bear(d, cx - 40, 900, 0.62, t, walk=False, **kw)
        d.text((cx, 980), name, font=font(52), fill=WHITE, anchor="mm")
        ok = i == 0
        if a > 0:
            col = GREEN if ok else RED
            d.text((cx, 1060), "Totstellen", font=font(46), fill=col, anchor="mm")
            mx, my = cx, 1125
            if ok:
                d.line((mx - 30, my, mx - 8, my + 24, mx + 34, my - 26), fill=GREEN,
                       width=12, joint="curve")
            else:
                d.line((mx - 26, my - 26, mx + 26, my + 26), fill=RED, width=12)
                d.line((mx - 26, my + 26, mx + 26, my - 26), fill=RED, width=12)
    if t >= 48.42:
        paste_vignette(img, VIG_RED, 0.5)
        rrect(d, (560, 1200, 1020, 1320), 26, RED)
        text_c(d, (790, 1260), "KÄMPFEN!", 70 * punch(t, 48.42), stroke=0)
    if t >= 49.88:
        for k in range(6):  # Treffer-Strahlen am Schwarzbär-Kopf
            ang = k * math.pi / 3 + t * 2
            x0, y0 = 790 + 60, 720
            d.line((x0 + 60 * math.cos(ang), y0 + 60 * math.sin(ang),
                    x0 + 110 * math.cos(ang), y0 + 110 * math.sin(ang)),
                   fill=AMBER, width=8)
        text_c(d, (W // 2, 430), "Gesicht + Schnauze", 56, fill=AMBER,
               alpha=ease_out((t - 49.88) / 0.3))


def draw_sea(d, t, swim_t):
    """Strand unten, Meer oben; Schwimmer wird von der Strömung rausgezogen."""
    shore = 1250
    d.rectangle((0, 640, W, shore), fill=(16, 52, 92))
    d.rectangle((400, 640, 680, shore), fill=(12, 38, 70))  # Strömungskanal
    for row in range(9):
        y = 680 + row * 64
        for x in range(-60, W + 60, 120):
            ox = (x + t * 60 + row * 40) % (W + 120) - 60
            d.arc((ox, y, ox + 90, y + 30), 200, 340, fill=(90, 150, 210), width=4)
    d.rectangle((0, shore, W, shore + 90), fill=SAND)
    for k in range(3):  # Strömungspfeile
        y = 1150 - ((t * 120 + k * 170) % 500)
        d.polygon([(540, y - 40), (515, y), (565, y)], fill=(70, 120, 180))
    k = ease_out(swim_t / 6.0)
    sy = 1080 - 330 * k
    sc = 1 - 0.4 * k
    stroke = math.sin(t * 8)
    d.ellipse((540 - 30 * sc, sy - 30 * sc, 540 + 30 * sc, sy + 30 * sc), fill=FIGURE)
    d.line((540, sy, 540 - 70 * sc, sy + 50 * sc * stroke), fill=FIGURE, width=int(14 * sc))
    d.line((540, sy, 540 + 70 * sc, sy - 50 * sc * stroke), fill=FIGURE, width=int(14 * sc))


def scene_end(img, d, t):
    if t < T["tomorrow"]:
        draw_comment_prompt(d, t, T["end"], 53.25, "Hättest du's", "gewusst?")
        return
    draw_tomorrow(d, t, T["tomorrow"], 4, "STRÖMUNG")
    draw_sea(d, t, t - 57.42)
    if 59.13 <= t < 61.33:
        text_c(d, (W // 2, 580), "Du schwimmst zum Strand …", 56, fill=WHITE,
               alpha=ease_out((t - 59.13) / 0.3))
    elif 61.33 <= t < 63.0:
        text_c(d, (W // 2, 580), "… und kommst nicht an", 56 * punch(t, 61.33),
               fill=RED)
    if t >= 63.0:
        draw_follow_button(d, t, 63.0, y=570)


SCENES = [
    (0.0, T["scenario"], scene_hook),
    (T["scenario"], T["choice"], scene_scenario),
    (T["choice"], T["wrong"], scene_choice),
    (T["wrong"], T["right"], scene_wrong),
    (T["right"], T["twist"], scene_right),
    (T["twist"], T["end"], scene_twist),
    (T["end"], DUR, scene_end),
]


def frame(t):
    return compose_frame(t, SCENES, DAY, CAPTIONS, DUR)


def make_sfx():
    s = Sfx(DUR)
    s.drone([0, 9, C_END, C_END + 0.6, 52, 56.4, 63, DUR],
            [0.08, 0.09, 0.13, 0.05, 0.04, 0.08, 0.08, 0.0])
    s.heartbeat(0, 9.0, 0.6)
    s.rumble(0, 3.5, 2.0)
    s.rumble(5.3, 0.8, 1.8)
    s.rumble(7.8, 1.4, 2.5)
    s.heartbeat(10.5, C_END, 0.6, 0.4)
    s.ticks(9.9, C_END)
    for tc in T_COUNT:
        s.beep(tc)
    s.buzzer(C_END, freq=110, length=0.6, amp=0.18)
    for v in T.values():
        s.whoosh(v)
    s.buzzer(T["wrong"])
    s.rumble(24.47, 2.5, 1.5)
    s.thud(30.34, 0.6)
    s.chime(T["right"])
    for t0 in (36.2, 37.5, 38.86):
        s.beep(t0, freq=660, amp=0.15)
    s.buzzer(45.6, freq=180, length=0.3, amp=0.1)
    s.thud(48.42, 0.7)
    s.thud(49.88, 0.5)
    s.pops(53.25)
    s.heartbeat(57.4, 62.6, 0.6, 0.35)
    s.buzzer(61.33)
    s.soft(63.0)
    return s


if __name__ == "__main__":
    print(render("folge03-baer", VOICE, make_sfx(), frame, DUR))
