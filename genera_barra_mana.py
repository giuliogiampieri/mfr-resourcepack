#!/usr/bin/env python3
"""Barra del mana (#39 nel repository del server): la barra dell'esperienza disegnata come una fiala di vetro.

Il server mostra il mana nella barra dell'esperienza (senza numero). Il gioco la disegna sempre 182x5 pixel con due
sprite: lo sfondo (la fiala vuota) e, sopra, il riempimento tagliato a destra secondo il mana (il liquido).
Disegno originale (richieste del proprietario del 22/11/2026): estremi arrotondati, bordi chiari semitrasparenti
come il vetro, liquido sfumato da blu a viola (variante A) con il riflesso del vetro in alto.

Uso: python3 genera_barra_mana.py
  → assets/minecraft/textures/gui/sprites/hud/experience_bar_background.png (fiala vuota)
  → assets/minecraft/textures/gui/sprites/hud/experience_bar_progress.png   (liquido)
"""
import pathlib
from PIL import Image

QUI = pathlib.Path(__file__).resolve().parent
CARTELLA = QUI / "assets/minecraft/textures/gui/sprites/hud"
L, A = 182, 5
# Sfumatura da sinistra a destra, scelta dal proprietario il 22/11/2026 (variante A): blu -> viola.
INIZIO = (40, 110, 235)
FINE = (150, 70, 240)
VETRO_ALTO = (215, 230, 255)
VETRO_BASSO = (140, 160, 205)
VETRO_LATO = (175, 195, 235)


def misto(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def scuro(c, f):
    return tuple(int(v * f) for v in c)


def chiaro(c, f):
    return tuple(int(v + (255 - v) * f) for v in c)


def dentro(x, y):
    """Estremi arrotondati: i quattro angoli restano trasparenti."""
    return not (x in (0, L - 1) and y in (0, A - 1))


def fiala_vuota():
    im = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    for x in range(L):
        for y in range(A):
            if not dentro(x, y):
                continue
            if y == 0:
                c, a = VETRO_ALTO, 190
            elif y == A - 1:
                c, a = VETRO_BASSO, 190
            elif x in (0, L - 1):
                c, a = VETRO_LATO, 190
            elif y == 1:
                c, a = (60, 66, 92), 205        # riflesso tenue sul vetro vuoto
            else:
                c, a = (22, 26, 44), 205        # interno scuro della fiala
            im.putpixel((x, y), c + (a,))
    return im


def liquido():
    im = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    for x in range(L):
        base = misto(INIZIO, FINE, x / (L - 1))
        for y in range(A):
            if not dentro(x, y):
                continue
            if y == 0:
                c, a = misto(VETRO_ALTO, base, 0.35), 230            # vetro colorato dal liquido
            elif y == A - 1:
                c, a = misto(VETRO_BASSO, scuro(base, 0.55), 0.6), 230
            elif x in (0, L - 1):
                c, a = misto(VETRO_LATO, scuro(base, 0.6), 0.5), 230
            elif y == 1:
                c, a = chiaro(base, 0.38), 255                       # riflesso del vetro sul liquido
            elif y == A - 2:
                c, a = scuro(base, 0.85), 255
            else:
                c, a = base, 255
            im.putpixel((x, y), c + (a,))
    for x in range(3, 14):                                           # lampo di luce vicino all'estremo sinistro
        r, g, b, a = im.getpixel((x, 1))
        t = max(0.0, 1 - abs(x - 8) / 6)
        im.putpixel((x, 1), chiaro((r, g, b), 0.35 * t) + (a,))
    return im


CARTELLA.mkdir(parents=True, exist_ok=True)
for nome, img in (("experience_bar_background.png", fiala_vuota()), ("experience_bar_progress.png", liquido())):
    img.save(CARTELLA / nome, optimize=True)
    print(f"{(CARTELLA / nome).relative_to(QUI)}: {L}x{A}")
