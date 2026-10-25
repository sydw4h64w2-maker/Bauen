"""Prüft, ob eine neue ElevenLabs-Aufnahme zur Kanal-Stimme passt.

Aufruf:  python3 video/check_voice.py <neue_aufnahme.mp3> [<originaler_dateiname>]

Vergleicht
1. den Stimmnamen im ElevenLabs-Dateinamen mit VOICE_NAME,
2. Tonhöhe und Klangfarbe mit den Referenzfolgen (REFERENCES).
"""
import os
import sys

import librosa
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICE_NAME = "Chris Beck"
REFERENCES = ["folgen/folge-02/stimme.mp3", "folgen/folge-03/stimme.mp3"]
MAX_PITCH_DIFF = 0.12   # 12 % Abweichung der mittleren Tonhöhe
MAX_TIMBRE_DIST = 0.03  # Abstand der MFCC-Klangprofile (gleiche Stimme ≈ 0.005)


def profile(path):
    y, sr = librosa.load(path, sr=16000, duration=40)
    f0, voiced, _ = librosa.pyin(y, fmin=60, fmax=300, sr=sr)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)[1:]
    v = mfcc.mean(axis=1)
    return float(np.median(f0[voiced])), v / np.linalg.norm(v)


def main():
    path = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(path)
    ok = True
    if VOICE_NAME.replace(" ", "_") in name or VOICE_NAME in name:
        print(f"Dateiname: {VOICE_NAME} ✓")
    elif "_-_" in name:
        print(f"Dateiname: andere Stimme ✗ ({name})")
        ok = False
    else:
        print("Dateiname: kein Stimmname enthalten – nur Klangvergleich")
    pitch, timbre = profile(path)
    for ref in REFERENCES:
        rp, rt = profile(os.path.join(ROOT, ref))
        dp = abs(pitch - rp) / rp
        dt = 1 - float(np.dot(timbre, rt))
        good = dp <= MAX_PITCH_DIFF and dt <= MAX_TIMBRE_DIST
        ok &= good
        print(f"vs. {ref}: Tonhöhe {pitch:.0f} vs. {rp:.0f} Hz ({dp:.0%}), "
              f"Klangabstand {dt:.3f} {'✓' if good else '✗'}")
    print("ERGEBNIS:", "passt ✓" if ok else "PASST NICHT ✗")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
