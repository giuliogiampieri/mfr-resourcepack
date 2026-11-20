#!/usr/bin/env python3
"""Prototipo "GUI v3": due varianti complete da confrontare (richiesta del 20/11/2026, ore 12:15).

Uso: python3 genera_gui_v3.py <jar del client Minecraft 26.3>
Scrive solo in prototipi/gui-v3-A/ e prototipi/gui-v3-B/: il pacchetto pubblicato non cambia.

Caselle, oggetti, posizioni e dimensioni sono IDENTICI nelle due varianti (stesse funzioni di genera_gui_v2.py);
cambiano solo intestazioni, sfondo e decorazioni della cornice. Il testo resta dove lo mette Minecraft (fornace:
titolo centrato da codice; tramoggia, baule, creativa: a sinistra; banco da lavoro: x = 29).

A "Cartiglio": targhetta in pergamena con estremità arrotolate, larga quanto il titolo standard in italiano
  (misurato con il font del gioco) + margini; sfondo "velluto": vignettatura e retinatura a 1 pixel di interfaccia;
  filigrane d'oro e gemme agli angoli. Un nome personalizzato più lungo esce dalla targhetta.
B "Architrave": intestazione integrata nella cornice (lamina d'oro con pomoli alle estremità, larga quanto la
  finestra: ci stanno anche i nomi lunghi); per "Inventario" una linguetta della stessa lamina su un binario sottile
  che divide la finestra; sfondo in pietra con intarsio a losanghe appena percettibile; cornice a doppio filo con
  rivetti.
"""
import io
import os
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import genera_gui_v2 as v2
from genera_gui_v2 import (S, OSSIDIANA, BORDEAUX, AMETISTA, ORO, PERGAMENA, ORO_CHIARO, ORO_SCURO, FILETTO, RAME,
                           mix, casella, analizza, evidenza, sovrapposizione, scheda)

QUI = os.path.dirname(os.path.abspath(__file__))
CONT, SPR = v2.CONT, v2.SPR
MARGINE = 6                                   # spazio fra testo e bordo della targhetta, per lato

# Schermate: dimensione, titolo standard (testo, x oppure "centro", y) ed etichetta "Inventario" (x, y), in pixel
# di interfaccia della texture. Il baule è disegnato in due pezzi: l'etichetta sta a y 128 della texture.
GUI = {
    "furnace.png": dict(dim=(176, 166), titolo=("Fornace", "centro", 6), inv=(8, 72), tema="fornace"),
    "hopper.png": dict(dim=(176, 133), titolo=("Tramoggia", 8, 6), inv=(8, 39), tema="tramoggia"),
    "generic_54.png": dict(dim=(176, 222), titolo=("Baule", 8, 6), inv=(8, 128), tema="baule"),
    "crafting_table.png": dict(dim=(176, 166), titolo=("Fabbricazione", 29, 6), inv=(8, 72), tema="banco"),
    "creative_inventory/tab_inventory.png": dict(dim=(195, 136), titolo=None, inv=None, tema="creativa"),
    "creative_inventory/tab_items.png": dict(dim=(195, 136), titolo=("Blocchi da costruzione", 8, 6), inv=None,
                                             tema="creativa"),
}


def larghezze_font(jar):
    img = Image.open(io.BytesIO(jar.read("assets/minecraft/textures/font/ascii.png"))).convert("RGBA")
    w = {}
    for c in range(32, 127):
        cella = img.crop(((c % 16) * 8, (c // 16) * 8, (c % 16) * 8 + 8, (c // 16) * 8 + 8))
        bb = cella.getchannel("A").getbbox()
        w[chr(c)] = 4 if chr(c) == " " else (bb[2] if bb else 0) + 1
    return lambda testo: sum(w.get(ch, 6) for ch in testo) - 1


# ---------------------------------------------------------------- sfondi

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def velluto(w, h):
    """A: vignettatura morbida (centro più caldo, bordi più scuri) resa a 5 toni con retinatura ordinata 4x4,
    un pixel di interfaccia per punto: profondità senza righe e senza sfarfallio."""
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = (w - 1) / 2, (h - 1) / 2.6
    r = np.sqrt(((xx - cx) / (w * .62)) ** 2 + ((yy - cy) / (h * .70)) ** 2)
    v = np.clip(1.15 - r, 0, 1)                                   # 1 al centro, 0 ai bordi
    toni = np.array([mix(BORDEAUX, OSSIDIANA, .42), mix(BORDEAUX, OSSIDIANA, .22), BORDEAUX,
                     mix(BORDEAUX, AMETISTA, .10), mix(BORDEAUX, AMETISTA, .18)])
    livello = np.clip((v * 4 + BAYER[yy % 4, xx % 4] - .5).round().astype(int), 0, 4)
    img = toni[livello].astype(np.uint8)
    return np.repeat(np.repeat(img, S, 0), S, 1)


def pietra_intarsiata(w, h):
    """B: pietra a basso contrasto (come v2, più scura) con un intarsio a losanghe di 1 pixel, passo 12."""
    base = v2.pietra(w, h, 7)[::S, ::S].astype(int)
    base = (base * .9 + np.array(OSSIDIANA) * .1).astype(int)
    yy, xx = np.mgrid[0:h, 0:w]
    losanga = ((xx + yy) % 12 == 0) | ((xx - yy) % 12 == 0)
    base[losanga] = (base[losanga] * .88 + np.array(AMETISTA) * .12).astype(int)
    nodo = ((xx + yy) % 12 == 0) & ((xx - yy) % 12 == 0)
    base[nodo] = np.array(mix(BORDEAUX, ORO, .16))
    return np.repeat(np.repeat(base.astype(np.uint8), S, 0), S, 1)


# ---------------------------------------------------------------- cornici e decorazioni

def colora(out, m, c):
    out[m, :3] = c
    out[m, 3] = 255


def cornice_base(out, cornice, dist4, alto_sx, sfondo):
    colora(out, cornice & (dist4 <= 2), OSSIDIANA)
    colora(out, cornice & (dist4 >= 3) & (dist4 <= 8), ORO)
    colora(out, cornice & (dist4 >= 3) & (dist4 <= 4) & alto_sx, ORO_CHIARO)
    colora(out, cornice & (dist4 >= 7) & (dist4 <= 8) & ~alto_sx, ORO_SCURO)
    colora(out, cornice & (dist4 >= 9) & (dist4 <= 10), OSSIDIANA)
    resto = cornice & (dist4 >= 11)
    out[resto, :3] = sfondo[resto]


def cornice_doppia(out, cornice, dist4, alto_sx, sfondo):
    """B: filo d'oro sottile esterno, scanalatura scura, filo d'oro pieno interno."""
    colora(out, cornice & (dist4 <= 1), OSSIDIANA)
    colora(out, cornice & (dist4 >= 2) & (dist4 <= 3), ORO_CHIARO if True else ORO)
    colora(out, cornice & (dist4 >= 4) & (dist4 <= 5), OSSIDIANA)
    colora(out, cornice & (dist4 >= 6) & (dist4 <= 10), ORO)
    colora(out, cornice & (dist4 >= 6) & (dist4 <= 7) & alto_sx, ORO_CHIARO)
    colora(out, cornice & (dist4 >= 9) & (dist4 <= 10) & ~alto_sx, ORO_SCURO)
    resto = cornice & (dist4 >= 11)
    out[resto, :3] = sfondo[resto]


def ombra_interna(out, dentro, dist4):
    """Profondità: 2 pixel di interfaccia più scuri lungo il bordo interno della cornice."""
    for d0, t in ((11, .45), (13, .30), (15, .16), (17, .08)):
        m = dentro & (dist4 >= d0) & (dist4 <= d0 + 1)
        out[m, :3] = (out[m, :3] * (1 - t) + np.array(OSSIDIANA) * t).astype(np.uint8)


def filigrana(d, x, y, sx, sy):
    """A: filigrana d'oro all'angolo (x, y) verso l'interno (sx, sy = ±1): due bracci sulla cornice, un ricciolo
    e una gemma ametista. Resta entro 2 pixel dal bordo interno della cornice: non tocca caselle né testo."""
    P = lambda gx, gy: (x * S + gx * 2 * sx, y * S + gy * 2 * sy)          # passo di mezzo pixel
    def punto(gx, gy, c, n=1):
        x0, y0 = P(gx, gy)
        d.rectangle([min(x0, x0 + sx * (2 * n - 1)), min(y0, y0 + sy * (2 * n - 1)),
                     max(x0, x0 + sx * (2 * n - 1)), max(y0, y0 + sy * (2 * n - 1))], fill=c)
    for i in range(0, 24):                                             # bracci lungo i due lati (12 px)
        punto(i, 0, ORO_CHIARO if i < 14 else ORO); punto(0, i, ORO_CHIARO if i < 14 else ORO)
        punto(i, 1, ORO if i > 2 else ORO_CHIARO); punto(1, i, ORO if i > 2 else ORO_CHIARO)
        punto(i, 2, OSSIDIANA if i > 5 else ORO); punto(2, i, OSSIDIANA if i > 5 else ORO)
    for gx, gy in ((24, 1), (25, 2), (25, 3), (24, 4), (23, 4), (22, 3)):  # riccioli in fondo ai bracci
        punto(gx, gy, ORO_CHIARO); punto(gy, gx, ORO_CHIARO)
    for gx in range(1, 6):                                             # gemma a rombo sull'angolo
        for gy in range(1, 6):
            if abs(gx - 3) + abs(gy - 3) <= 2:
                punto(gx, gy, AMETISTA if abs(gx - 3) + abs(gy - 3) <= 1 else OSSIDIANA)
    punto(2, 2, mix(AMETISTA, PERGAMENA, .55))


def rivetto(d, x, y):
    X, Y = x * S, y * S
    d.ellipse([X, Y, X + 7, Y + 7], fill=ORO_SCURO)
    d.ellipse([X + 1, Y + 1, X + 5, Y + 5], fill=ORO)
    d.rectangle([X + 2, Y + 2, X + 3, Y + 3], fill=ORO_CHIARO)


# ---------------------------------------------------------------- intestazioni

def cartiglio(d, x0, y0, x1, y1):
    """A: pergamena con le estremità arrotolate (rotoli di 2 pixel) e filetto d'oro scuro."""
    X0, Y0, X1, Y1 = x0 * S, y0 * S, x1 * S - 1, y1 * S - 1
    R = 2 * S
    d.rectangle([X0 + R // 2, Y0, X1 - R // 2, Y1], fill=ORO_SCURO)
    d.rectangle([X0 + R // 2, Y0 + 2, X1 - R // 2, Y1 - 2], fill=PERGAMENA)
    d.rectangle([X0 + R // 2, Y1 - 3, X1 - R // 2, Y1 - 2], fill=mix(PERGAMENA, ORO, .5))
    for lato in (0, 1):                                                 # rotoli alle due estremità
        rx = X0 if lato == 0 else X1 - R + 1
        d.rounded_rectangle([rx, Y0 - 2, rx + R - 1, Y1 + 2], radius=3, fill=ORO_SCURO)
        d.rounded_rectangle([rx + 2, Y0, rx + R - 3, Y1], radius=2, fill=mix(PERGAMENA, ORO, .35))
        d.rectangle([rx + 3, Y0 + 2, rx + 3, Y1 - 2], fill=PERGAMENA)          # luce sul rotolo


def architrave(d, x0, y0, x1, y1, pomoli=True):
    """B: lamina d'oro chiaro integrata nella cornice: filo scuro, binari d'oro sopra e sotto, campo chiaro,
    pomoli alle estremità. Il testo grigio del gioco resta leggibile sul campo chiaro."""
    X0, Y0, X1, Y1 = x0 * S, y0 * S, x1 * S - 1, y1 * S - 1
    campo = mix(PERGAMENA, ORO, .42)
    d.rectangle([X0, Y0, X1, Y1], fill=OSSIDIANA)
    d.rectangle([X0, Y0 + 2, X1, Y1 - 2], fill=ORO)
    d.rectangle([X0, Y0 + 2, X1, Y0 + 3], fill=ORO_CHIARO)
    d.rectangle([X0, Y1 - 3, X1, Y1 - 2], fill=ORO_SCURO)
    d.rectangle([X0 + 2, Y0 + 6, X1 - 2, Y1 - 6], fill=campo)
    d.rectangle([X0 + 2, Y0 + 6, X1 - 2, Y0 + 7], fill=PERGAMENA)
    if pomoli:
        for px in (X0 - 2, X1 - 4 * S + 3):
            cy = (Y0 + Y1) // 2
            d.ellipse([px, cy - 9, px + 4 * S - 1, cy + 8], fill=OSSIDIANA)
            d.ellipse([px + 2, cy - 7, px + 4 * S - 3, cy + 6], fill=ORO)
            d.ellipse([px + 4, cy - 5, px + 8, cy - 1], fill=ORO_CHIARO)


def binario(d, x0, y, x1):
    """B: binario d'oro di 1 pixel con filo scuro sotto, che separa contenitore e inventario."""
    d.rectangle([x0 * S, y * S, x1 * S - 1, y * S + 3], fill=ORO)
    d.rectangle([x0 * S, y * S, x1 * S - 1, y * S + 1], fill=ORO_CHIARO)
    d.rectangle([x0 * S, y * S + 4, x1 * S - 1, y * S + 5], fill=OSSIDIANA)


# ---------------------------------------------------------------- composizione

def ridisegna(orig, meta, variante, misura):
    a, opaco, grigio, dist, caselle, irregolari = analizza(orig)
    h, w = opaco.shape
    big = lambda m: np.repeat(np.repeat(m, S, 0), S, 1)
    out = big(a).copy()
    op4, g4, d4 = big(opaco), big(grigio), big(dist)
    dist4 = ndimage.distance_transform_cdt(np.pad(op4, 1), metric="chessboard")[1:-1, 1:-1]
    sfondo = velluto(w, h) if variante == "A" else pietra_intarsiata(w, h)
    fondo = op4 & (g4 == 198)
    out[fondo, :3] = sfondo[fondo]
    out[fondo, 3] = 255
    cornice = op4 & (d4 <= 3) & np.isin(g4, [0, 85, 198, 255])
    yy, xx = np.mgrid[0:h * S, 0:w * S]
    alto_sx = (yy + xx) < (h * S + w * S) / 2
    (cornice_base if variante == "A" else cornice_doppia)(out, cornice, dist4, alto_sx, sfondo)
    dentro = op4 & ~cornice
    ombra_interna(out, dentro & fondo, dist4)
    colora(out, dentro & (g4 == 139) & ~big(irregolari), RAME if meta["tema"] == "fornace" else AMETISTA)
    colora(out, dentro & np.isin(g4, [55, 85, 255]) & ~big(irregolari), OSSIDIANA)
    colora(out, dentro & (g4 == 0), OSSIDIANA)
    colora(out, big(irregolari), v2.SUPERFICIE)
    img = Image.fromarray(out, "RGBA")
    d = ImageDraw.Draw(img)
    maggiore = max(caselle, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]), default=None)
    for r in caselle:                                                  # caselle: IDENTICHE nelle due varianti
        rame = meta["tema"] == "fornace" and r[0] < 80 and r[1] < 70
        casella(d, *r, importante=(r == maggiore and (r[2] - r[0]) > 16), filetto=RAME if rame else FILETTO)
    ys, xs = np.nonzero(opaco)
    X0, X1, Y1 = xs.min(), xs.max() + 1, ys.max() + 1
    finestra_alta = meta["dim"][1] if meta["tema"] != "baule" else 222
    if meta["titolo"]:
        testo, tx, ty = meta["titolo"]
        larg = misura(testo)
        if variante == "A":
            if tx == "centro":
                lt = max(66, larg + 2 * MARGINE + 6)
                x0 = (meta["dim"][0] - lt) // 2
                cartiglio(d, x0, ty - 2, x0 + lt, ty + 9)
            else:
                cartiglio(d, max(4, tx - MARGINE - 2), ty - 2, tx + larg + MARGINE + 2, ty + 9)
        else:
            architrave(d, 2, ty - 3, meta["dim"][0] - 2, ty + 9)
    if meta["inv"]:
        ix, iy = meta["inv"]
        fine = ix + misura("Inventario") + MARGINE
        if variante == "A":
            cartiglio(d, max(4, ix - MARGINE - 2), iy - 2, fine + 2, iy + 9)
        else:
            binario(d, 3, iy + 8, meta["dim"][0] - 3)                    # divisione sottile a tutta larghezza
            architrave(d, 3, iy - 2, fine, iy + 9, pomoli=False)        # linguetta della stessa lamina
    if meta["tema"] != "creativa":
        if variante == "A":
            for (x, y, sx, sy) in ((X0, 0, 1, 1), (X1, 0, -1, 1), (X0, finestra_alta, 1, -1), (X1, finestra_alta, -1, -1)):
                filigrana(d, x, y, sx, sy)
        else:
            for (x, y) in ((1, finestra_alta - 3), (X1 - 3, finestra_alta - 3)):
                rivetto(d, x, y)
    v2.tematici(d, meta["tema"], caselle)
    return img


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    with zipfile.ZipFile(sys.argv[1]) as jar:
        misura = larghezze_font(jar)
        apri = lambda p: Image.open(io.BytesIO(jar.read(p)))
        for variante in ("A", "B"):
            base = os.path.join(QUI, "prototipi", f"gui-v3-{variante}")
            def scrivi(img, rel):
                p = os.path.join(base, rel)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                img.save(p, optimize=True)
            for nome, meta in GUI.items():
                scrivi(ridisegna(apri(CONT + nome), meta, variante, misura), CONT + nome)
            # Immagini in comune (identiche nelle due varianti): schede, casella sotto il cursore, fiamma e freccia.
            for voce in jar.namelist():
                if voce.startswith(SPR + "container/creative_inventory/tab_") and voce.endswith(".png"):
                    scrivi(scheda(apri(voce), "_selected_" in voce), voce)
            scrivi(evidenza(apri(SPR + "container/slot_highlight_back.png"), 84), SPR + "container/slot_highlight_back.png")
            scrivi(evidenza(apri(SPR + "container/slot_highlight_front.png"), 30), SPR + "container/slot_highlight_front.png")
            scrivi(sovrapposizione(apri(SPR + "container/furnace/burn_progress.png"),
                                   {198: None, 255: (240, 170, 90), 104: RAME}), SPR + "container/furnace/burn_progress.png")
            scrivi(sovrapposizione(apri(SPR + "container/furnace/lit_progress.png"), {198: None, 139: None}),
                   SPR + "container/furnace/lit_progress.png")
            print("variante", variante, "scritta in", os.path.relpath(base, QUI))


if __name__ == "__main__":
    main()
