#!/usr/bin/env python3
"""Barra del mana (#39 nel repository del server): riempimento blu-viola della barra dell'esperienza.

Il server mostra il mana nella barra dell'esperienza (numero = mana, 0-100). Questo script disegna solo il
riempimento (sprite hud/experience_bar_progress, 182x5); lo sfondo della barra resta quello del gioco.
Disegno originale: sfumatura blu -> viola, riflesso chiaro in alto, ombra in basso, estremi scuri.

Uso: python3 genera_barra_mana.py   → scrive assets/minecraft/textures/gui/sprites/hud/experience_bar_progress.png
"""
import pathlib
from PIL import Image

QUI = pathlib.Path(__file__).resolve().parent
USCITA = QUI / "assets/minecraft/textures/gui/sprites/hud/experience_bar_progress.png"
L, A = 182, 5
# Sfumatura da sinistra a destra, scelta dal proprietario il 22/11/2026 (variante A): blu -> viola.
# Con poco mana si vede solo la parte sinistra (blu); a mana pieno la barra finisce in viola.
INIZIO = (40, 110, 235)
FINE = (150, 70, 240)


def misto(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def scuro(c, f):
    return tuple(int(v * f) for v in c)


def chiaro(c, f):
    return tuple(int(v + (255 - v) * f) for v in c)


# Il gioco disegna la barra sempre alta 5 pixel: per farla sembrare più spessa il riempimento usa tutte e 5 le righe
# (copre anche il bordo scuro dello sfondo), con riflesso in alto, ombra in basso ed estremi scuri.
img = Image.new("RGBA", (L, A), (0, 0, 0, 0))
for x in range(L):
    base = misto(INIZIO, FINE, x / (L - 1))
    for y in range(A):
        if x in (0, L - 1):
            c = scuro(base, 0.45)
        elif y == 0:
            c = chiaro(base, 0.55)
        elif y == A - 1:
            c = scuro(base, 0.7)
        else:
            c = base
        img.putpixel((x, y), c + (255,))
USCITA.parent.mkdir(parents=True, exist_ok=True)
img.save(USCITA, optimize=True)
print(f"{USCITA.relative_to(QUI)}: {L}x{A}")
