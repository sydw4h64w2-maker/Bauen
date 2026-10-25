"""Erzeugt das TikTok-Profilbild (1080x1080) im Stil der Videos.

Aufruf:  python3 video/render_profilbild.py
Ergebnis: account/profilbild.png und account/profilbild-vorschau.png
"""
import os

from PIL import Image, ImageDraw

from common import AMBER, RED, ROOT, WHITE, font

S = 1080


def main():
    img = Image.new("RGB", (S, S), (10, 12, 18))
    d = ImageDraw.Draw(img)
    c, r = S // 2, 420
    # Countdown-Ring wie in den Videos: grauer Ring, roter Bogen
    d.ellipse((c - r, c - r, c + r, c + r), outline=(60, 66, 78), width=56)
    d.arc((c - r, c - r, c + r, c + r), -90, 180, fill=RED, width=56)
    d.text((c, c - 40), "?", font=font(520), fill=AMBER, anchor="mm")
    d.text((c, c + 270), "A · B · C", font=font(96), fill=WHITE, anchor="mm")
    out = os.path.join(ROOT, "account")
    os.makedirs(out, exist_ok=True)
    img.save(os.path.join(out, "profilbild.png"))
    # Vorschau, wie TikTok es rund und klein zeigt
    small = img.resize((200, 200))
    mask = Image.new("L", (200, 200), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 199, 199), fill=255)
    prev = Image.new("RGB", (240, 240), (255, 255, 255))
    prev.paste(small, (20, 20), mask)
    prev.save(os.path.join(out, "profilbild-vorschau.png"))


if __name__ == "__main__":
    main()
