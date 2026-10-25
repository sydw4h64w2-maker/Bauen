"""Gemeinsame Bausteine für alle Folgen von „Überlebst du das?“.

Eine Folge definiert nur noch ihre Satz-Zeitmarken, Szenen und Effekte und
ruft am Ende render(...) auf.
"""
import math
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(HERE, "out")
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

RED = (232, 44, 60)
GREEN = (46, 204, 113)
WHITE = (245, 245, 245)
GREY = (150, 158, 170)
CARD = (28, 34, 44)
AMBER = (255, 176, 32)
BLUE = (70, 160, 255)
SAND = (176, 132, 72)
SAND_DARK = (140, 100, 52)
FIGURE = (200, 200, 210)

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
def _background():
    y = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array([12, 15, 22]), np.array([4, 5, 8])
    grad = np.broadcast_to(top * (1 - y) + bot * y, (H, W, 3))
    return Image.fromarray(grad.astype(np.uint8), "RGB")


def _vignette(color):
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a = np.clip((r - 0.7) / 0.7, 0, 1) ** 1.5 * 0.85
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = color
    img[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


BG = _background()
VIG_DARK = _vignette((0, 0, 0))
VIG_RED = _vignette(RED)
VIG_GREEN = _vignette(GREEN)


def paste_vignette(img, vig, strength):
    if strength <= 0:
        return
    v = vig.copy()
    v.putalpha(v.getchannel("A").point(lambda a: int(a * clamp(strength))))
    img.paste(v, (0, 0), v)


# ---------------------------------------------------------------- Untertitel
def build_captions(sentences, dur):
    """Teilt jeden Satz in gleich lange Häppchen (ca. 26 Zeichen) und verteilt
    die Satzdauer nach Zeichenzahl."""
    caps = []
    for s, e, sent in sentences:
        n = math.ceil(len(sent) / 26)
        target = len(sent) / n
        chunks, cur = [], []
        for w in sent.split():
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
    for a, b in zip(caps, caps[1:]):
        a[1] = min(b[0], a[1] + 0.6)
    caps[-1][1] = min(dur, caps[-1][1] + 1.0)
    return caps


def draw_caption(d, t, captions):
    for s, e, txt in captions:
        if s <= t < e:
            size = 66
            while font(size).getlength(txt) > 940:
                size -= 2
            text_c(d, (W // 2, 1420), txt, size * punch(t, s, 0.22), stroke=10)
            return


def draw_badge(d, day):
    rrect(d, (60, 150, 360, 230), 20, RED)
    d.text((210, 190), f"TAG {day}/365", font=font(44), fill=WHITE, anchor="mm")


# ---------------------------------------------------------------- Antwortkarten
def draw_option(d, option, i, t_in, t, state=None, dim=False, active=False):
    letter, l1, l2 = option
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


def draw_choice(img, d, t, options, t_start, t_opt, t_count):
    """Szene „Was tust du?“: Karten erscheinen beim Vorlesen, dann 3-2-1."""
    text_c(d, (W // 2, 330), "WAS TUST DU?", 92 * punch(t, t_start), stroke=10)
    for i in range(3):
        nxt = t_opt[i + 1] if i < 2 else t_count[0]
        draw_option(d, options[i], i, t_opt[i], t, active=t_opt[i] <= t < nxt)
    c_end = t_count[2] + 0.75
    if t_count[0] <= t < c_end:
        k = 0 if t < t_count[1] else (1 if t < t_count[2] else 2)
        seg_end = t_count[k + 1] if k < 2 else c_end
        frac = (t - t_count[k]) / (seg_end - t_count[k])
        cx, cy, r = W // 2, 540, 105
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(60, 66, 78), width=14)
        d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * (1 - frac),
              fill=RED, width=14)
        text_c(d, (cx, cy), str(3 - k), 120 * punch(t, t_count[k], 0.3), stroke=0)
    elif t >= c_end:
        text_c(d, (W // 2, 540), "ZEIT UM!", 100 * punch(t, c_end), fill=RED)
        paste_vignette(img, VIG_RED, 1 - clamp((t - c_end) / 0.6))


def draw_comment_prompt(d, t, t0, t_abc, title1, title2):
    text_c(d, (W // 2, 520), title1, 100 * punch(t, t0))
    text_c(d, (W // 2, 640), title2, 120 * punch(t, t0), fill=AMBER)
    if t >= t_abc:
        for i, letter in enumerate("ABC"):
            x = W // 2 - 220 + i * 220
            sc = punch(t, t_abc + i * 0.15)
            r = 75 * sc
            d.ellipse((x - r, 860 - r, x + r, 860 + r), fill=AMBER)
            d.text((x, 860), letter, font=font(90 * sc), fill=(10, 10, 10),
                   anchor="mm")
        text_c(d, (W // 2, 1020), "in die Kommentare", 52, fill=GREY, stroke=0)


def draw_follow_button(d, t, t0, y=600):
    if t < t0:
        return
    pulse = 1 + 0.06 * math.sin((t - t0) * 8)
    bw, bh = 420 * pulse, 120 * pulse
    rrect(d, (W / 2 - bw / 2, y - bh / 2, W / 2 + bw / 2, y + bh / 2), 60, RED)
    text_c(d, (W // 2, y), "FOLGEN", 64 * pulse, stroke=0)


def draw_tomorrow(d, t, t0, day, topic):
    rrect(d, (140, 330, 940, 510), 30, (30, 22, 10), outline=AMBER, width=6)
    text_c(d, (W // 2, 390), f"MORGEN · TAG {day}", 50, fill=AMBER, stroke=0)
    text_c(d, (W // 2, 455), topic, 74 * punch(t, t0), stroke=0)


def arrow_up(d, x, y, ln, col, w):
    d.line((x, y, x, y - ln), fill=col, width=w)
    d.polygon([(x - w * 1.6, y - ln + 4), (x + w * 1.6, y - ln + 4),
               (x, y - ln - w * 2.6)], fill=col)


# ---------------------------------------------------------------- Ton
class Sfx:
    """Einfache synthetische Soundeffekte auf einer Spur."""

    def __init__(self, dur, seed=1):
        self.n = int(dur * SR)
        self.tt = np.arange(self.n) / SR
        self.out = np.zeros(self.n)
        self.rng = np.random.default_rng(seed)

    def add(self, start, sig):
        i = int(start * SR)
        j = min(self.n, i + len(sig))
        if j > i:
            self.out[i:j] += sig[: j - i]

    @staticmethod
    def env(length, attack=0.005, decay=None):
        m = int(length * SR)
        e = np.ones(m)
        a = max(1, int(attack * SR))
        e[:a] = np.linspace(0, 1, a)
        if decay:
            e *= np.exp(-np.arange(m) / (decay * SR))
        return e

    @staticmethod
    def sine(freq, length, amp=1.0):
        x = np.arange(int(length * SR)) / SR
        return amp * np.sin(2 * np.pi * freq * x)

    def drone(self, times, levels):
        lvl = np.interp(self.tt, times, levels)
        lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.2 * self.tt)
        self.out += lvl * lfo * (np.sin(2 * np.pi * 55 * self.tt)
                                 + 0.6 * np.sin(2 * np.pi * 82.4 * self.tt))

    def heartbeat(self, start, end, every, amp=0.55):
        for t0 in np.arange(start, end, every):
            for off, a in ((0, 1.0), (0.22, 0.7)):
                self.add(t0 + off, self.sine(58, 0.25, amp * a)
                         * self.env(0.25, decay=0.06))

    def ticks(self, start, end):
        for t0 in np.arange(start, end, 0.5):
            self.add(t0, self.rng.normal(0, 1, int(0.02 * SR))
                     * self.env(0.02, 0.001, 0.004) * 0.25)

    def beep(self, at, freq=880, amp=0.3):
        self.add(at, self.sine(freq, 0.15, amp) * self.env(0.15, decay=0.08))

    def buzzer(self, at, freq=140, length=0.45, amp=0.16):
        self.add(at, np.sign(self.sine(freq, length)) * amp
                 * self.env(length, decay=length / 2))

    def whoosh(self, at):
        m = int(0.6 * SR)
        noise = np.convolve(self.rng.normal(0, 1, m), np.ones(30) / 30, mode="same")
        self.add(at - 0.35, noise * np.sin(np.linspace(0, np.pi, m)) ** 2 * 0.6)

    def chime(self, at):
        for k, fr in enumerate((523.25, 659.25, 783.99)):
            self.add(at + k * 0.09, self.sine(fr, 0.7, 0.22)
                     * self.env(0.7, decay=0.25))

    def thud(self, at, amp=0.5):
        self.add(at, self.sine(70, 0.5, amp) * self.env(0.5, decay=0.12))

    def pops(self, at):
        for k in range(3):
            self.add(at + k * 0.15, self.sine(660, 0.12, 0.18)
                     * self.env(0.12, decay=0.05))

    def soft(self, at, freq=392):
        self.add(at, self.sine(freq, 0.9, 0.2) * self.env(0.9, decay=0.35))

    def rumble(self, at, length, amp=2.5):
        m = int(length * SR)
        r = np.convolve(self.rng.normal(0, 1, m), np.ones(200) / 200, mode="same")
        self.add(at, r * amp * np.sin(np.linspace(0, np.pi, m)))

    def write(self, path):
        out = self.out / (max(1e-9, np.abs(self.out).max()) / 0.9)
        pcm = (out * 32767).astype(np.int16)
        with wave.open(path, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())


# ---------------------------------------------------------------- Rendern
def compose_frame(t, scenes, day, captions, dur):
    img = BG.copy()
    d = ImageDraw.Draw(img)
    for s, e, fn in scenes:
        if s <= t < e:
            fn(img, d, t)
            break
    img.paste(VIG_DARK, (0, 0), VIG_DARK)
    d = ImageDraw.Draw(img)
    draw_badge(d, day)
    draw_caption(d, t, captions)
    for s, _, _ in scenes[1:]:  # kurze Schwarzblende an Szenenwechseln
        if abs(t - s) < 0.12:
            k = 1 - abs(t - s) / 0.12
            img = Image.blend(img, Image.new("RGB", (W, H)), k * 0.8)
    if t > dur - 0.5:
        img = Image.blend(img, Image.new("RGB", (W, H)), (t - (dur - 0.5)) / 0.5)
    return img


def render(name, voice, sfx, frame_fn, dur):
    """Bilder + Stimme + Effekte (unter der Stimme abgesenkt) zu MP4."""
    os.makedirs(OUT_DIR, exist_ok=True)
    sfx_path = os.path.join(OUT_DIR, f"{name}-sfx.wav")
    mp4 = os.path.join(OUT_DIR, f"{name}.mp4")
    sfx.write(sfx_path)
    af = ("[1:a]aresample=44100,aformat=channel_layouts=stereo,asplit=2[v1][v2];"
          "[2:a]volume=0.5[fx];"
          "[fx][v1]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=350[duck];"
          "[duck][v2]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", voice, "-i", sfx_path,
           "-filter_complex", af, "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
           "-t", str(dur), "-movflags", "+faststart", mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)):
        p.stdin.write(frame_fn(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    os.remove(sfx_path)
    return mp4
