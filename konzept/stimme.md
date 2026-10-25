# Sprecherstimme des Kanals

| | |
|---|---|
| Anbieter | ElevenLabs |
| Voice-ID | `SfAtBxtKeIJ5PJmhPaty` |
| Stimme (laut Dateinamen) | Chris Beck – Witty, Energetic and Bright (Zuordnung zur ID noch unbestätigt) |
| Modell | Multilingual v2 oder Turbo/Flash v2.5 (unterstützen `<break time="…" />`) |
| Einstellungen | Stability ca. 40–50 %, Speed 1,0 |
| Export | mp3, ein Durchgang pro Folge |

Für jede Folge dieselbe Stimme verwenden (Wiedererkennung).
Der Text zum Einfügen steht jeweils in `folgen/folge-XX/elevenlabs.txt`.

## Stimmen-Check (ab Folge 4 bei jeder Aufnahme)
`python3 video/check_voice.py <aufnahme.mp3> <originaler_dateiname>`
prüft Stimmnamen im Dateinamen + Tonhöhe/Klangfarbe gegen Folge 2 und 3.
Referenzwerte Chris Beck: Tonhöhe ca. 185–195 Hz, Klangabstand ≤ 0,01.
(Zum Vergleich „Ben“: ca. 135 Hz, Klangabstand ca. 0,1 → würde abgelehnt.)
