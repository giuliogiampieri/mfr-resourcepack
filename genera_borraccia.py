#!/usr/bin/env python3
"""Borraccia (#190 nel repository del server): texture dell'oggetto, 32x32, dall'immagine del proprietario del 23/11
(sorgenti/borraccia-sorgente.png, pixel art a blocchi irregolari). Ogni cella della griglia 32x32 prende il colore
mediano dei pixel non di sfondo, se ne copre almeno metà; poi tavolozza di 32 colori per pixel netti.

Uso: python3 genera_borraccia.py   → assets/mfr/textures/item/borraccia.png
"""
import pathlib
import numpy as np
from PIL import Image
QUI = pathlib.Path(__file__).resolve().parent
N = 32
im = np.array(Image.open(QUI / 'sorgenti/borraccia-sorgente.png').convert('RGBA')).astype(int)
rgb, a = im[..., :3], im[..., 3]
fondo = (a < 20) | (rgb > 235).all(-1)
ys, xs = np.nonzero(~fondo)
y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
lato = max(y1 - y0, x1 - x0) * 1.04                      # un filo di margine
cy, cx = (y0 + y1) / 2, (x0 + x1) / 2
out = np.zeros((N, N, 4), np.uint8)
for j in range(N):
    for i in range(N):
        ya, yb = int(cy - lato / 2 + j * lato / N), int(cy - lato / 2 + (j + 1) * lato / N)
        xa, xb = int(cx - lato / 2 + i * lato / N), int(cx - lato / 2 + (i + 1) * lato / N)
        ya, xa = max(ya, 0), max(xa, 0)
        cella = rgb[ya:yb, xa:xb].reshape(-1, 3); f = fondo[ya:yb, xa:xb].reshape(-1)
        if cella.size == 0 or (~f).mean() < 0.5:
            continue
        c = np.median(cella[~f], axis=0)
        out[j, i, :3] = c; out[j, i, 3] = 255
# tavolozza ridotta (16 colori) per pixel netti, come le texture di Minecraft
img = Image.fromarray(out, 'RGBA')
op = out[..., 3] > 0
pal = Image.fromarray(out[..., :3]).quantize(32, method=Image.Quantize.MAXCOVERAGE)
q = np.array(pal.convert('RGB'))
out[op, :3] = q[op]
Image.fromarray(out, 'RGBA').save(QUI / 'assets/mfr/textures/item/borraccia.png', optimize=True)
