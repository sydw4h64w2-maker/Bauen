"""Rendert Folge 4 „Überlebst du das? – Strömung“ passend zur Stimme in
folgen/folge-04/stimme.mp3.

Aufruf:  python3 video/render_folge04.py
Ergebnis: video/out/folge04-stroemung.mp4
"""
import math
import os

from common import (AMBER, FIGURE, GREEN, GREY, RED, ROOT, SAND, VIG_GREEN,
                    VIG_RED, W, WHITE, Sfx, arrow_up, build_captions, clamp,
                    compose_frame, draw_choice, draw_comment_prompt,
                    draw_follow_button, draw_option, draw_tomorrow, ease_out,
                    font, paste_vignette, punch, render, rrect, text_c)

DAY = 4
VOICE = os.path.join(ROOT, "folgen", "folge-04", "stimme.mp3")
DUR = 70.8

SENTENCES = [
    (0.00, 1.63, "Du schwimmst mit aller Kraft –"),
    (2.01, 3.78, "und das Ufer wird trotzdem kleiner."),
    (4.29, 6.14, "Eine Strömung zieht dich vom Strand weg."),
    (6.53, 7.37, "Raus aufs Meer."),
    (7.79, 8.36, "Was tust du?"),
    (18.66, 19.12, "Drei."),
    (19.61, 20.14, "Zwei."),
    (20.77, 21.24, "Eins."),
    (21.91, 23.23, "Die meisten wählen A."),
    (23.70, 26.81, "Aber diese Strömung kann schneller sein als ein Olympiaschwimmer."),
    (27.28, 29.00, "Wer dagegen anschwimmt, wird müde –"),
    (29.42, 31.16, "und genau das ist das Gefährliche."),
    (31.74, 32.99, "Richtig ist C."),
    (33.44, 36.74, "Die Strömung zieht dich nicht nach unten, sondern nur nach draußen."),
    (37.17, 39.58, "Schwimm parallel zum Strand, bis du raus bist –"),
    (39.90, 41.05, "dann zurück ans Ufer."),
    (41.50, 42.38, "Schaffst du das nicht:"),
    (42.70, 45.19, "Lass dich treiben, wink und ruf um Hilfe."),
    (45.67, 47.33, "Und siehst du jemanden in der Strömung:"),
    (47.64, 48.88, "Spring nicht hinterher –"),
    (49.27, 50.75, "viele Opfer sind Helfer."),
    (51.18, 53.83, "Wirf ihm etwas, das schwimmt, und hol die Rettungsschwimmer."),
    (54.60, 55.51, "Hättest du's gewusst?"),
    (55.89, 58.69, "Schreib A, B oder C in die Kommentare."),
    (59.20, 59.76, "Und morgen:"),
    (60.25, 61.91, "Dein Auto stürzt in einen See."),
    (62.30, 63.83, "Du hast ungefähr eine Minute."),
    (64.25, 66.99, "Was du in dieser Minute tust, entscheidet alles."),
    (67.33, 67.85, "Folg mir –"),
    (68.16, 70.30, "damit du es weißt, bevor du es brauchst."),
]
CAPTIONS = build_captions(SENTENCES, DUR)

OPTIONS = [
    ("A", "Mit aller Kraft", "zurück zum Ufer"),
    ("B", "Abtauchen, unter der", "Strömung durch"),
    ("C", "Parallel zum", "Strand schwimmen"),
]
T_OPT = (9.10, 12.50, 15.86)
T_COUNT = (18.66, 19.61, 20.77)
C_END = T_COUNT[2] + 0.75
T = {"scenario": 4.2, "choice": 7.75, "wrong": 21.91, "right": 31.74,
     "helper": 45.67, "end": 54.60, "tomorrow": 59.20}

SEA_TOP, SHORE = 640, 1250
CH_L, CH_R = 420, 660  # Strömungskanal (x-Bereich)
WATER, WATER_DARK = (16, 52, 92), (10, 34, 64)


# ---------------------------------------------------------------- Meer (Draufsicht)
def draw_sea(d, t, channel=True, label=False):
    d.rectangle((0, SEA_TOP, W, SHORE), fill=WATER)
    if channel:
        d.rectangle((CH_L, SEA_TOP, CH_R, SHORE), fill=WATER_DARK)
    for row in range(9):
        y = SEA_TOP + 40 + row * 64
        for x in range(-60, W + 60, 120):
            ox = (x + t * 60 + row * 40) % (W + 120) - 60
            if channel and CH_L < ox + 45 < CH_R:
                continue  # im Kanal keine brechenden Wellen
            d.arc((ox, y, ox + 90, y + 30), 200, 340, fill=(90, 150, 210), width=4)
    d.rectangle((0, SHORE, W, SHORE + 90), fill=SAND)
    if channel:
        for k in range(3):
            y = SHORE - 100 - ((t * 140 + k * 190) % 520)
            cx = (CH_L + CH_R) // 2
            d.polygon([(cx, y - 44), (cx - 30, y), (cx + 30, y)], fill=(70, 120, 180))
        if label:
            d.text(((CH_L + CH_R) // 2, SEA_TOP - 40), "STRÖMUNG", font=font(48),
                   fill=AMBER, anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))


def draw_swimmer(d, x, y, t, s=1.0, wave=False):
    stroke = math.sin(t * 8)
    d.ellipse((x - 30 * s, y - 30 * s, x + 30 * s, y + 30 * s), fill=FIGURE)
    if wave:  # winkt mit einem Arm
        d.line((x + 20 * s, y, x + 70 * s, y - 90 * s + 20 * stroke * s),
               fill=FIGURE, width=int(14 * s))
        d.line((x - 20 * s, y, x - 70 * s, y + 20 * s), fill=FIGURE, width=int(14 * s))
        return
    d.line((x, y, x - 70 * s, y + 50 * s * stroke), fill=FIGURE, width=int(14 * s))
    d.line((x, y, x + 70 * s, y - 50 * s * stroke), fill=FIGURE, width=int(14 * s))


def draw_ring_buoy(d, x, y, r=40):
    d.ellipse((x - r, y - r, x + r, y + r), fill=(240, 240, 240))
    for a0 in (0, 90, 180, 270):
        d.pieslice((x - r, y - r, x + r, y + r), a0 + 20, a0 + 70, fill=RED)
    d.ellipse((x - r * 0.5, y - r * 0.5, x + r * 0.5, y + r * 0.5), fill=WATER)


# ---------------------------------------------------------------- Szenen
def scene_hook(img, d, t):
    pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 1.25)
    paste_vignette(img, VIG_RED, 0.3 + 0.4 * pulse)
    draw_sea(d, t)
    k = ease_out(t / 4.2)
    draw_swimmer(d, 540, 1150 - 380 * k, t, 1.1 - 0.4 * k)
    sc = punch(t, 0.0, 0.5)
    text_c(d, (W // 2, 330), "ÜBERLEBST", 120 * sc, stroke=12)
    text_c(d, (W // 2, 470), "DU DAS?", 150 * sc, fill=RED, stroke=12)


def scene_scenario(img, d, t):
    draw_sea(d, t, label=True)
    k = ease_out((t - 4.2) / 3.5)
    draw_swimmer(d, 540, 900 - 200 * k, t, 0.9 - 0.25 * k)
    text_c(d, (W // 2, 360), "RAUS AUFS MEER", 84 * punch(t, 6.53), fill=RED,
           alpha=clamp((t - 6.53) / 0.2))


def scene_choice(img, d, t):
    draw_choice(img, d, t, OPTIONS, T["choice"], T_OPT, T_COUNT)


def scene_wrong(img, d, t):
    if t < 23.70:
        draw_option(d, OPTIONS[0], 0, 0, t, state="wrong")
        draw_option(d, OPTIONS[1], 1, 0, t, dim=True)
        draw_option(d, OPTIONS[2], 2, 0, t, dim=True)
        text_c(d, (W // 2, 420), "FALSCH!", 130 * punch(t, T["wrong"]), fill=RED)
        return
    if t < 27.28:
        text_c(d, (W // 2, 360), "Wer ist schneller?", 76 * punch(t, 23.70))
        for i, (label, val, col, note) in enumerate(
                (("Strömung (Spitze)", 1.0, RED, "bis 2,4 m/s"),
                 ("Olympiaschwimmer", 0.88, AMBER, ""))):
            y = 700 + i * 220
            a = ease_out((t - 24.2 - i * 0.6) / 0.8)
            d.text((100, y), label, font=font(50), fill=WHITE, anchor="lm")
            rrect(d, (100, y + 45, 980, y + 135), 18, (30, 34, 42))
            if a * val * 880 > 36:
                rrect(d, (100, y + 45, 100 + int(880 * val * a), y + 135), 18, col)
            if note:
                d.text((960, y + 90), note, font=font(44), fill=WHITE, anchor="rm",
                       stroke_width=5, stroke_fill=(0, 0, 0))
        return
    draw_sea(d, t)
    draw_swimmer(d, 540, 820 - 60 * ease_out((t - 27.28) / 4), t, 0.8)
    energy = 1 - clamp((t - 27.28) / 3.6)
    rrect(d, (240, 380, 840, 440), 20, (30, 34, 42))
    if energy > 0.05:
        col = GREEN if energy > 0.5 else (AMBER if energy > 0.25 else RED)
        rrect(d, (240, 380, 240 + int(600 * energy), 440), 20, col)
    d.text((W // 2, 340), "Kraft", font=font(48), fill=WHITE, anchor="mm")
    if t >= 29.42:
        paste_vignette(img, VIG_RED, 0.6)
        text_c(d, (W // 2, 530), "ERSCHÖPFUNG", 80 * punch(t, 29.42), fill=RED)


def scene_right(img, d, t):
    paste_vignette(img, VIG_GREEN, 0.55 * (1 - clamp((t - T["right"]) / 0.6)))
    if t < 33.44:
        draw_option(d, OPTIONS[0], 0, 0, t, dim=True)
        draw_option(d, OPTIONS[1], 1, 0, t, dim=True)
        draw_option(d, OPTIONS[2], 2, 0, t, state="right")
        text_c(d, (W // 2, 420), "RICHTIG: C", 110 * punch(t, T["right"]), fill=GREEN)
        return
    if t < 37.17:
        # Seitenansicht: Wasseroberfläche, Pfeil nach unten ✗, nach draußen ✓
        d.rectangle((0, 760, W, 1300), fill=WATER)
        for x in range(0, W, 60):
            d.arc((x, 740, x + 60, 780), 0, 180, fill=(90, 150, 210), width=5)
        draw_swimmer(d, 300, 760, t, 1.0)
        d.line((300, 840, 300, 1120), fill=RED, width=16)
        d.polygon([(270, 1110), (330, 1110), (300, 1170)], fill=RED)
        d.line((250, 960, 350, 1060), fill=WHITE, width=12)
        d.line((250, 1060, 350, 960), fill=WHITE, width=12)
        if t >= 35.0:
            a = ease_out((t - 35.0) / 0.5)
            d.line((400, 900, 400 + 480 * a, 900), fill=GREEN, width=16)
            if a > 0.9:
                d.polygon([(880, 870), (880, 930), (940, 900)], fill=GREEN)
            d.text((660, 980), "nur nach draußen", font=font(48), fill=GREEN,
                   anchor="mm")
        text_c(d, (W // 2, 360), "Nicht nach unten!", 76 * punch(t, 33.44))
        return
    draw_sea(d, t)
    if t < 41.50:
        side = ease_out((t - 37.17) / 2.2)
        back = ease_out((t - 39.90) / 1.2)
        x = 540 + 380 * side
        y = 820 + 300 * back
        d.line((540, 820, x, 820), fill=GREEN, width=6)
        draw_swimmer(d, x, y, t, 0.8)
        text_c(d, (W // 2, 360), "Parallel zum Strand", 76 * punch(t, 37.17),
               fill=GREEN)
        if t >= 39.90:
            text_c(d, (W // 2, 470), "dann zurück ans Ufer", 56, fill=WHITE,
                   alpha=ease_out((t - 39.90) / 0.3))
        return
    draw_swimmer(d, 540, 820 + 10 * math.sin(t * 2), t, 0.9, wave=True)
    text_c(d, (W // 2, 360), "Plan B", 80 * punch(t, 41.50), fill=AMBER)
    if t >= 42.70:
        text_c(d, (W // 2, 470), "treiben · winken · rufen", 60 * punch(t, 42.70))


def draw_person_beach(d, x, t, lean=0.0):
    fy = SHORE + 60
    d.ellipse((x - 30 + lean * 40, fy - 300, x + 30 + lean * 40, fy - 240), fill=FIGURE)
    d.line((x + lean * 40, fy - 240, x, fy - 120), fill=FIGURE, width=20)
    d.line((x, fy - 120, x - 30, fy), fill=FIGURE, width=16)
    d.line((x, fy - 120, x + 30, fy), fill=FIGURE, width=16)
    d.line((x + lean * 30, fy - 210, x + 80, fy - 260 - 40 * lean), fill=FIGURE, width=14)


def scene_helper(img, d, t):
    draw_sea(d, t)
    draw_swimmer(d, 540, 760, t, 0.75, wave=True)
    text_c(d, (W // 2, 360), "ACHTUNG!", 100 * punch(t, T["helper"]), fill=AMBER)
    if t < 51.18:
        draw_person_beach(d, 820, t, lean=0.6 if t >= 47.64 else 0.0)
        if t >= 47.64:
            rrect(d, (170, 440, 910, 560), 26, RED)
            text_c(d, (W // 2, 500), "NICHT HINTERHER!", 66 * punch(t, 47.64), stroke=0)
        if t >= 49.27:
            text_c(d, (W // 2, 610), "Viele Opfer sind Helfer", 54, fill=WHITE,
                   alpha=ease_out((t - 49.27) / 0.3))
        return
    draw_person_beach(d, 820, t)
    k = ease_out((t - 51.18) / 1.0)
    bx = 820 + (600 - 820) * k
    by = SHORE - 20 - (SHORE - 20 - 800) * k - 160 * math.sin(math.pi * k)
    draw_ring_buoy(d, bx, by)
    text_c(d, (W // 2, 470), "Etwas, das schwimmt", 60 * punch(t, 51.18), fill=GREEN)
    if t >= 52.6:
        rrect(d, (220, 520, 860, 610), 22, (60, 20, 26))
        text_c(d, (W // 2, 565), "+ Rettungsschwimmer holen", 46, stroke=0,
               alpha=ease_out((t - 52.6) / 0.3))


def draw_car_sinking(d, t, t0):
    k = ease_out((t - t0) / 8.0)
    surface = 900
    d.rectangle((0, surface, W, 1330), fill=WATER)
    cx, cy = W // 2, surface - 60 + 260 * k
    ang = -0.25 * k
    col = (120, 128, 140)

    def rot(x, y):
        return (cx + x * math.cos(ang) - y * math.sin(ang),
                cy + x * math.sin(ang) + y * math.cos(ang))
    body = [rot(x, y) for x, y in ((-200, -40), (200, -40), (200, 50), (-200, 50))]
    cabin = [rot(x, y) for x, y in ((-110, -40), (-70, -120), (90, -120), (140, -40))]
    d.polygon(body, fill=col)
    d.polygon(cabin, fill=(50, 70, 90))
    # Wasser vorn (halbtransparent wirkt über erneutes Zeichnen der Oberfläche)
    for x in range(0, W, 60):
        d.arc((x, surface - 20, x + 60, surface + 20), 0, 180, fill=(90, 150, 210), width=5)
    for i in range(5):  # Luftblasen
        by = surface + 40 + ((t * 120 + i * 70) % 300)
        bx = cx - 80 + i * 40
        d.ellipse((bx - 8, 1330 - by + surface - 40, bx + 8, 1330 - by + surface - 24),
                  outline=(150, 200, 240), width=3)


def scene_end(img, d, t):
    if t < T["tomorrow"]:
        draw_comment_prompt(d, t, T["end"], 55.89, "Hättest du's", "gewusst?")
        return
    draw_tomorrow(d, t, T["tomorrow"], 5, "AUTO IM WASSER")
    draw_car_sinking(d, t, 60.25)
    if 62.30 <= t < 67.33:
        remain = max(0, 60 - int(t - 62.30))
        rrect(d, (330, 560, 750, 700), 30, (40, 12, 16), outline=RED, width=6)
        text_c(d, (W // 2, 630), f"0:{remain:02d}" if remain < 60 else "1:00",
               90 * punch(t, 62.30), fill=RED, stroke=0)
        if t >= 64.25:
            paste_vignette(img, VIG_RED, 0.5)
    if t >= 67.33:
        draw_follow_button(d, t, 67.33, y=630)


SCENES = [
    (0.0, T["scenario"], scene_hook),
    (T["scenario"], T["choice"], scene_scenario),
    (T["choice"], T["wrong"], scene_choice),
    (T["wrong"], T["right"], scene_wrong),
    (T["right"], T["helper"], scene_right),
    (T["helper"], T["end"], scene_helper),
    (T["end"], DUR, scene_end),
]


def frame(t):
    return compose_frame(t, SCENES, DAY, CAPTIONS, DUR)


def make_sfx():
    s = Sfx(DUR)
    s.drone([0, 7.7, C_END, C_END + 0.6, 54.6, 59.2, 67, DUR],
            [0.08, 0.09, 0.13, 0.05, 0.04, 0.09, 0.09, 0.0])
    s.heartbeat(0, 7.7, 0.75)
    s.rumble(0, 7.5, 1.0)
    s.heartbeat(9.5, C_END, 0.6, 0.4)
    s.ticks(8.4, C_END)
    for tc in T_COUNT:
        s.beep(tc)
    s.buzzer(C_END, freq=110, length=0.6, amp=0.18)
    for v in T.values():
        s.whoosh(v)
    s.buzzer(T["wrong"])
    s.heartbeat(27.3, 31.2, 0.45, 0.45)
    s.thud(29.42, 0.6)
    s.chime(T["right"])
    s.soft(37.17, 523.25)
    s.buzzer(47.64, freq=180, length=0.3, amp=0.12)
    s.soft(51.18, 659.25)
    s.pops(55.89)
    s.rumble(60.25, 3.0, 2.0)
    for k in range(5):
        s.ticks(62.3 + k, 62.3 + k + 0.1)
    s.thud(64.25, 0.6)
    s.soft(67.33)
    return s


if __name__ == "__main__":
    print(render("folge04-stroemung", VOICE, make_sfx(), frame, DUR))
