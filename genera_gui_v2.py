#!/usr/bin/env python3
"""Prototipo "GUI v2" (brief del 20/11/2026): fornace, tramoggia e inventario creativo in una variante SEPARATA.

Uso: python3 genera_gui_v2.py <jar del client Minecraft 26.3>

Scrive solo in prototipi/gui-v2/ (stessi percorsi del pacchetto sotto assets/): il pacchetto pubblicato non cambia.
Le texture originali si leggono dal jar del client. Regole del mini design system:
- palette del brief: ossidiana #24121F, bordeaux #421A39, ametista #63335D, oro antico #B48A43, pergamena #F0D49A;
  l'oro chiaro solo sul bordo esterno, sulla casella del risultato e sulla casella sotto il cursore;
- disegno a 4x, ma ogni motivo grande almeno 1 pixel di interfaccia (4 pixel di texture) e i filetti almeno
  mezzo pixel (2 pixel di texture): niente righine fini che sfarfallano (moiré) con la scala 2 o 3;
- sfondo "pietra levigata" a basso contrasto, a blocchi di 1 pixel di interfaccia, mai dietro gli oggetti;
- caselle incassate: filetto d'oro antico attenuato, ombra in alto e a sinistra, luce ametista in basso e a destra,
  superficie uniforme;
- targhette in pergamena con le estremità smussate; il titolo resta dove lo mette il gioco (fornace al centro,
  tramoggia a sinistra): la targhetta è larga quanto la finestra, così vanno bene tutte e due;
- dettagli tematici solo negli spazi vuoti: rame per la fornace (caselle di ingresso e combustibile, freccia e
  fiamma spente), rivetti di ferro brunito per la tramoggia;
  schede della creativa più scure quando non sono attive.
"""
import io
import os
import random
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

QUI = os.path.dirname(os.path.abspath(__file__))
USCITA = os.path.join(QUI, "prototipi", "gui-v2")
CONT = "assets/minecraft/textures/gui/container/"
SPR = "assets/minecraft/textures/gui/sprites/"
S = 4

OSSIDIANA = (36, 18, 31)
BORDEAUX = (66, 26, 57)
AMETISTA = (99, 51, 93)
ORO = (180, 138, 67)
PERGAMENA = (240, 212, 154)
ORO_CHIARO = (226, 190, 118)
ORO_SCURO = (104, 74, 36)
FILETTO = (152, 114, 66)                # oro antico attenuato per le caselle ordinarie
SUPERFICIE = (34, 14, 30)
LUCE_CASELLA = (112, 64, 102)
RAME, BRACE = (150, 88, 52), (196, 104, 44)
FERRO, FERRO_SCURO = (150, 144, 160), (84, 78, 96)

TARGHETTE = {   # (x0, y0, x1, y1) in pixel di interfaccia, come in genera_contenitori.py
    "furnace.png": [(7, 4, 169, 15), (7, 70, 62, 81)],
    "hopper.png": [(7, 4, 169, 15), (7, 37, 62, 48)],
    "creative_inventory/tab_inventory.png": [],
    "creative_inventory/tab_items.png": [(7, 4, 190, 16)],
    "creative_inventory/tab_item_search.png": [(7, 4, 79, 16)],
}


def mix(a, b, t):
    return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))


def pietra(w, h, seme):
    """Sfondo a blocchi di 1 pixel di interfaccia: rumore morbido a basso contrasto (tre toni vicini)."""
    rng = np.random.default_rng(seme)
    grezzo = rng.random((h // 3 + 2, w // 3 + 2))
    liscio = ndimage.zoom(grezzo, 3, order=1)[:h, :w]
    fine = rng.random((h, w)) * .35
    v = liscio * .65 + fine
    toni = np.array([mix(BORDEAUX, OSSIDIANA, .18), BORDEAUX, mix(BORDEAUX, AMETISTA, .10)])
    idx = np.digitize(v, [.30, .78])
    img = toni[idx].astype(np.uint8)
    return np.repeat(np.repeat(img, S, 0), S, 1)


def casella(d, x0, y0, x1, y1, importante=False, filetto=FILETTO):
    """Casella incassata. (x0,y0)-(x1,y1): interno in pixel di interfaccia (estremi esclusi); il filetto sta fuori."""
    X0, Y0, X1, Y1 = (x0 - 1) * S, (y0 - 1) * S, (x1 + 1) * S - 1, (y1 + 1) * S - 1
    d.rectangle([X0, Y0, X1, Y1], fill=ORO if importante else filetto)               # filetto esterno (1/2 px)
    d.rectangle([X0 + 2, Y0 + 2, X1 - 2, Y1 - 2], fill=LUCE_CASELLA)                  # luce in basso a destra
    d.rectangle([X0 + 2, Y0 + 2, X1 - 2, Y0 + 3], fill=OSSIDIANA)                     # ombra in alto
    d.rectangle([X0 + 2, Y0 + 2, X0 + 3, Y1 - 2], fill=OSSIDIANA)                     # ombra a sinistra
    d.rectangle([x0 * S, y0 * S, x1 * S - 1, y1 * S - 1], fill=SUPERFICIE)            # superficie uniforme
    if importante:                                                                   # angoli chiari: area importante
        for cx, cy in ((X0, Y0), (X1 - 3, Y0), (X0, Y1 - 3), (X1 - 3, Y1 - 3)):
            d.rectangle([cx, cy, cx + 3, cy + 3], fill=ORO_CHIARO)


def targhetta(d, x0, y0, x1, y1):
    """Pergamena con le estremità smussate di 1 pixel e filetto d'oro scuro di mezzo pixel."""
    X0, Y0, X1, Y1 = x0 * S, y0 * S, x1 * S - 1, y1 * S - 1
    d.polygon([(X0 + S, Y0), (X1 - S, Y0), (X1, Y0 + S), (X1, Y1 - S), (X1 - S, Y1), (X0 + S, Y1),
               (X0, Y1 - S), (X0, Y0 + S)], fill=ORO_SCURO)
    d.polygon([(X0 + S + 1, Y0 + 2), (X1 - S - 1, Y0 + 2), (X1 - 2, Y0 + S + 1), (X1 - 2, Y1 - S - 1),
               (X1 - S - 1, Y1 - 2), (X0 + S + 1, Y1 - 2), (X0 + 2, Y1 - S - 1), (X0 + 2, Y0 + S + 1)],
              fill=PERGAMENA)
    d.rectangle([X0 + S + 2, Y1 - 3, X1 - S - 2, Y1 - 2], fill=mix(PERGAMENA, ORO, .45))   # ombra sotto il testo


def ornamento_angolo(d, x, y):
    """Piastrina d'oro 5x5 con gemma ametista, appoggiata sulla cornice nell'angolo (zona non cliccabile)."""
    X, Y = x * S, y * S
    d.rectangle([X, Y, X + 5 * S - 1, Y + 5 * S - 1], fill=OSSIDIANA)
    d.rectangle([X + 2, Y + 2, X + 5 * S - 3, Y + 5 * S - 3], fill=ORO)
    d.rectangle([X + 2, Y + 2, X + 5 * S - 3, Y + 3], fill=ORO_CHIARO)
    d.rectangle([X + 2, Y + 2, X + 3, Y + 5 * S - 3], fill=ORO_CHIARO)
    d.polygon([(X + 10, Y + 5), (X + 15, Y + 10), (X + 10, Y + 15), (X + 5, Y + 10)], fill=AMETISTA)
    d.rectangle([X + 9, Y + 7, X + 10, Y + 8], fill=mix(AMETISTA, PERGAMENA, .5))


def analizza(orig):
    a = np.array(orig.convert("RGBA"))
    opaco = a[..., 3] > 0
    grigio = np.where((a[..., 0] == a[..., 1]) & (a[..., 1] == a[..., 2]) & opaco, a[..., 0].astype(int), -1)
    dist = ndimage.distance_transform_cdt(np.pad(opaco, 1), metric="chessboard")[1:-1, 1:-1]
    caselle, irregolari = [], np.zeros(opaco.shape, bool)
    etich, _ = ndimage.label(grigio == 139)
    for i, sl in enumerate(ndimage.find_objects(etich), start=1):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        tocca = (ndimage.binary_dilation(etich == i) & (grigio == 55)).any()
        if (etich[sl] == i).all() and tocca and y1 - y0 >= 8 and x1 - x0 >= 8:
            caselle.append((x0, y0, x1, y1))
        elif tocca:
            irregolari |= etich == i
    return a, opaco, grigio, dist, caselle, irregolari


def ridisegna(orig, rettangoli, tema, seme):
    a, opaco, grigio, dist, caselle, irregolari = analizza(orig)
    h, w = opaco.shape
    big = lambda m: np.repeat(np.repeat(m, S, 0), S, 1)
    out = big(a).copy()                                   # i pixel colorati del gioco restano com'erano
    op4, g4, d4 = big(opaco), big(grigio), big(dist)
    dist4 = ndimage.distance_transform_cdt(np.pad(op4, 1), metric="chessboard")[1:-1, 1:-1]
    sfondo = pietra(w, h, seme)
    fondo = op4 & (g4 == 198)
    out[fondo, :3] = sfondo[fondo]
    out[fondo, 3] = 255
    cornice = op4 & (d4 <= 3) & np.isin(g4, [0, 85, 198, 255])
    # Cornice: filo scuro, oro antico con luce in alto a sinistra e ombra in basso a destra, filo scuro interno.
    yy, xx = np.mgrid[0:h * S, 0:w * S]
    alto_sx = (yy + xx) < (h * S + w * S) / 2
    def colora(m, c):
        out[m, :3] = c
        out[m, 3] = 255
    # 0,5 px scuro | 1,5 px oro antico (luce in alto a sinistra, ombra in basso a destra) | 0,5 px scuro | pietra
    colora(cornice & (dist4 <= 2), OSSIDIANA)
    colora(cornice & (dist4 >= 3) & (dist4 <= 8), ORO)
    colora(cornice & (dist4 >= 3) & (dist4 <= 4) & alto_sx, ORO_CHIARO)
    colora(cornice & (dist4 >= 7) & (dist4 <= 8) & ~alto_sx, ORO_SCURO)
    colora(cornice & (dist4 >= 9) & (dist4 <= 10), OSSIDIANA)
    resto = cornice & (dist4 >= 11)
    out[resto, :3] = sfondo[resto]
    out[resto, 3] = 255
    # Disegni del gioco (frecce, fiamme spente): incisi in ametista, non in oro (l'oro chiaro è per le aree importanti).
    dentro = op4 & ~cornice
    colora(dentro & (g4 == 139) & ~big(irregolari), RAME if tema == "fornace" else AMETISTA)
    colora(dentro & np.isin(g4, [55, 85, 255]) & ~big(irregolari), OSSIDIANA)   # resti di bordi del gioco
    colora(dentro & (g4 == 0), OSSIDIANA)
    colora(big(irregolari), SUPERFICIE)
    img = Image.fromarray(out, "RGBA")
    d = ImageDraw.Draw(img)
    maggiore = max(caselle, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]), default=None)
    for r in caselle:
        rame = tema == "fornace" and r[0] < 80 and r[1] < 70            # ingresso e combustibile della fornace
        casella(d, *r, importante=(r == maggiore and (r[2] - r[0]) > 16), filetto=RAME if rame else FILETTO)
    for r in rettangoli:
        targhetta(d, *r)
    # Ornamenti sugli angoli della cornice (non sull'area interna): solo dove la cornice è un angolo vero.
    ys, xs = np.nonzero(opaco)
    if len(xs) and tema != "creativa":
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        for (x, y) in ((x0, y0), (x1 - 4, y0), (x0, y1 - 4), (x1 - 4, y1 - 4)):
            ornamento_angolo(d, x, y)
    tematici(d, tema, caselle)
    return img


def tematici(d, tema, caselle):
    if tema == "fornace":
        pass                                              # il rame è nei filetti e nelle incisioni (sopra)
    elif tema == "tramoggia":
        # Rivetti di ferro brunito ai lati della fila di caselle (y 20..36) e piastra sotto le caselle.
        for x0 in (18, 145):                                  # piastra di ferro brunito con quattro rivetti
            d.rectangle([x0 * S, 21 * S, (x0 + 13) * S - 1, 35 * S - 1], fill=OSSIDIANA)
            d.rectangle([x0 * S + 2, 21 * S + 2, (x0 + 13) * S - 3, 35 * S - 3], fill=FERRO_SCURO)
            for x in (x0 + 2, x0 + 9):
                for y in (23, 31):
                    d.rectangle([x * S, y * S, x * S + 7, y * S + 7], fill=FERRO)
                    d.rectangle([x * S + 4, y * S + 4, x * S + 7, y * S + 7], fill=FERRO_SCURO)


def scheda(orig, attiva):
    """Schede della creativa a 4x: attiva come il pannello, inattive più scure e con filetto attenuato."""
    a = np.array(orig.convert("RGBA"))
    h, w = a.shape[:2]
    opaco = a[..., 3] > 0
    grigio = np.where((a[..., 0] == a[..., 1]) & (a[..., 1] == a[..., 2]) & opaco, a[..., 0].astype(int), -1)
    big = lambda m: np.repeat(np.repeat(m, S, 0), S, 1)
    op4, g4 = big(opaco), big(grigio)
    dist4 = ndimage.distance_transform_cdt(np.pad(op4, 1), metric="chessboard")[1:-1, 1:-1]
    corpo = BORDEAUX if attiva else mix(BORDEAUX, OSSIDIANA, .45)
    bordo = ORO if attiva else FILETTO
    out = np.zeros((h * S, w * S, 4), np.uint8)
    out[op4, :3] = corpo
    out[..., 3] = np.where(op4, 255, 0)
    out[op4 & (dist4 <= 2), :3] = OSSIDIANA
    out[op4 & (dist4 >= 3) & (dist4 <= 6), :3] = bordo
    if attiva:
        out[op4 & (dist4 >= 3) & (dist4 <= 4), :3] = ORO_CHIARO
    out[op4 & (g4 == 0) & (dist4 > 8), :3] = OSSIDIANA
    return Image.fromarray(out, "RGBA")


def evidenza(orig, alfa):
    """Casella sotto il cursore: stessa forma (nine-slice 24x24), velo di pergamena invece del bianco."""
    a = np.array(orig.convert("RGBA"))
    m = a[..., 3] > 0
    a[m, :3] = PERGAMENA
    a[m, 3] = alfa
    return Image.fromarray(a, "RGBA")


def sovrapposizione(orig, colori):
    """Freccia e fiamma della fornace: il grigio di fondo (198) diventa trasparente, il resto si ricolora."""
    a = np.array(orig.convert("RGBA"))
    g = (a[..., 0] == a[..., 1]) & (a[..., 1] == a[..., 2])
    for valore, colore in colori.items():
        m = g & (a[..., 0] == valore) & (a[..., 3] > 0)
        if colore is None:
            a[m, 3] = 0
        else:
            a[m, :3] = colore
    return Image.fromarray(a, "RGBA")


def scrivi(img, rel):
    p = os.path.join(USCITA, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.save(p, optimize=True)
    print("scritto", os.path.relpath(p, QUI))


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    with zipfile.ZipFile(sys.argv[1]) as jar:
        apri = lambda p: Image.open(io.BytesIO(jar.read(p)))
        temi = {"furnace.png": "fornace", "hopper.png": "tramoggia"}
        for nome, rett in TARGHETTE.items():
            scrivi(ridisegna(apri(CONT + nome), rett, temi.get(nome, "creativa"), seme=len(nome)), CONT + nome)
        for voce in jar.namelist():
            if voce.startswith(SPR + "container/creative_inventory/tab_") and voce.endswith(".png"):
                scrivi(scheda(apri(voce), "_selected_" in voce), voce)
        scrivi(evidenza(apri(SPR + "container/slot_highlight_back.png"), 84), SPR + "container/slot_highlight_back.png")
        scrivi(evidenza(apri(SPR + "container/slot_highlight_front.png"), 30), SPR + "container/slot_highlight_front.png")
        for meta in ("slot_highlight_back.png.mcmeta", "slot_highlight_front.png.mcmeta"):
            p = os.path.join(USCITA, SPR, "container", meta)
            with open(p, "wb") as f:
                f.write(jar.read(SPR + "container/" + meta))
        scrivi(sovrapposizione(apri(SPR + "container/furnace/burn_progress.png"),
                               {198: None, 255: (240, 170, 90), 104: RAME}), SPR + "container/furnace/burn_progress.png")
        scrivi(sovrapposizione(apri(SPR + "container/furnace/lit_progress.png"),
                               {198: None, 139: None}), SPR + "container/furnace/lit_progress.png")


if __name__ == "__main__":
    main()
