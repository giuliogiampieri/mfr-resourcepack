#!/usr/bin/env python3
"""Barra del mana (#39 nel repository del server): riempimento blu della barra dell'esperienza.

Il server mostra il mana nella barra dell'esperienza (numero = mana, 0-100). Questo script disegna solo il
riempimento (sprite hud/experience_bar_progress, 182x5); lo sfondo della barra resta quello del gioco.
Disegno originale, a righe di colore: riflesso chiaro in alto, corpo blu, ombra in basso, estremi scuri.

Uso: python3 genera_barra_mana.py   → scrive assets/minecraft/textures/gui/sprites/hud/experience_bar_progress.png
"""
import pathlib
from PIL import Image

QUI = pathlib.Path(__file__).resolve().parent
USCITA = QUI / "assets/minecraft/textures/gui/sprites/hud/experience_bar_progress.png"
L, A = 182, 5
BORDO = (16, 44, 112, 255)
RIFLESSO = (150, 214, 255, 255)
CORPO = (46, 128, 236, 255)
OMBRA = (28, 88, 190, 255)

# Il gioco disegna la barra sempre alta 5 pixel: per farla sembrare più spessa il riempimento usa tutte e 5 le righe
# (copre anche il bordo scuro dello sfondo), con riflesso in alto, ombra in basso ed estremi scuri.
img = Image.new("RGBA", (L, A), (0, 0, 0, 0))
for x in range(L):
    for y in range(A):
        if x in (0, L - 1):
            c = BORDO
        elif y == 0:
            c = RIFLESSO
        elif y == A - 1:
            c = OMBRA
        else:
            c = CORPO
        img.putpixel((x, y), c)
USCITA.parent.mkdir(parents=True, exist_ok=True)
img.save(USCITA, optimize=True)
print(f"{USCITA.relative_to(QUI)}: {L}x{A}")
