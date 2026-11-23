#!/usr/bin/env python3
"""Variante B2 (approvata dal proprietario il 20/11/2026, resa ufficiale alle 13:22) su TUTTE le interfacce dei
contenitori. Sostituisce genera_contenitori.py (stile precedente a righine).

Uso: python3 genera_gui_b2.py <jar del client Minecraft 26.3>
     python3 genera_titoli_centrati.py <jar> <it_it.json del gioco> .
     python3 genera_schermata.py            (Banco Magico e sportello, anch'essi in B2)
     python3 costruisci.py
Scrive in assets/ del pacchetto.

Stesso disegno di genera_gui_v3.py (variante B2): pietra intarsiata, cornice a doppio filo con rivetti, caselle
incassate, fascia sottile a tutta larghezza dietro le scritte. Per ogni schermata le scritte stanno dove le mette il
gioco (posizioni lette dal codice del client 26.3): la fascia si allarga a destra e a sinistra finché trova solo
sfondo, così non copre mai caselle o disegni. Lo script si ferma se una scritta cadrebbe su qualcosa che non è sfondo.
"""
import io
import os
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import genera_gui_v2 as v2
import genera_gui_v3 as v3
from genera_gui_v2 import S, OSSIDIANA, BORDEAUX, AMETISTA, ORO, ORO_CHIARO, ORO_SCURO, FILETTO, RAME, casella, analizza

QUI = os.path.dirname(os.path.abspath(__file__))
BASE = QUI
CONT, SPR = v2.CONT, v2.SPR
CENTRO = "centro"

# Scritte di ogni schermata: (x, y) in pixel della texture; x = "centro" se il gioco la centra (larghezza della
# finestra). Valori di AbstractContainerScreen (titolo 8,6; "Inventario" 8, altezza-94) e delle sottoclassi.
SCHERMATE = {
    "generic_54.png": dict(scritte=[(8, 6), (8, 128)], tema="baule"),
    "shulker_box.png": dict(scritte=[(8, 6), (8, 73)]),
    "dispenser.png": dict(scritte=[(CENTRO, 6), (8, 72)]),
    "crafter.png": dict(scritte=[(CENTRO, 6), (8, 72)]),
    "hopper.png": dict(scritte=[(8, 6), (8, 39)], tema="tramoggia"),
    "furnace.png": dict(scritte=[(CENTRO, 6), (8, 72)], tema="fornace"),
    "blast_furnace.png": dict(scritte=[(CENTRO, 6), (8, 72)], tema="fornace"),
    "smoker.png": dict(scritte=[(CENTRO, 6), (8, 72)], tema="fornace"),
    "crafting_table.png": dict(scritte=[(29, 6), (8, 72)], tema="banco"),
    # Inventario: il gioco scrive "Fabbricazione" a (97, 6) (titolo di AbstractContainerScreen, y = 6; prima qui 8 per
    # errore: il testo sporgeva sopra la fascia). Fascia stretta e centrata sul testo italiano (69 px, x 97..165)
    # invece che allargata fino al riquadro del personaggio (richiesta del proprietario del 23/11).
    "inventory.png": dict(scritte=[(97, 6)], fasce=[(93, 170)]),
    "brewing_stand.png": dict(scritte=[(CENTRO, 6), (8, 72)]),
    "enchanting_table.png": dict(scritte=[(8, 6), (8, 72)]),
    "anvil.png": dict(scritte=[(60, 6), (8, 72)]),
    "grindstone.png": dict(scritte=[(8, 6), (8, 72)]),
    "smithing.png": dict(scritte=[(44, 15), (8, 72)]),
    "stonecutter.png": dict(scritte=[(8, 5), (8, 72)]),
    "loom.png": dict(scritte=[(8, 4), (8, 72)]),
    "cartography_table.png": dict(scritte=[(8, 4), (8, 72)]),
    "horse.png": dict(scritte=[(8, 6), (8, 72)]),
    "nautilus.png": dict(scritte=[(8, 6), (8, 72)]),
    "villager.png": dict(scritte=[(5, 6), (CENTRO, 6), (107, 72)]),
    "beacon.png": dict(scritte=[]),                       # scritte chiare del gioco: nessuna fascia
    "creative_inventory/tab_inventory.png": dict(scritte=[], tema="creativa"),
    "creative_inventory/tab_items.png": dict(scritte=[(8, 6)], tema="creativa"),
    "creative_inventory/tab_item_search.png": dict(scritte=[(8, 6)], tema="creativa"),
}

SOVRAPPOSTE = tuple(f"container/{n}" for n in (
    "furnace/burn_progress.png", "furnace/lit_progress.png", "blast_furnace/burn_progress.png",
    "blast_furnace/lit_progress.png", "smoker/burn_progress.png", "smoker/lit_progress.png",
    "brewing_stand/brew_progress.png", "brewing_stand/bubbles.png", "anvil/error.png", "cartography_table/error.png",
    "grindstone/error.png", "smithing/error.png", "villager/out_of_stock.png", "villager/trade_arrow.png",
    "villager/trade_arrow_out_of_stock.png"))
RICOLORATE = tuple(f"container/{n}" for n in (
    "loom/scroller.png", "stonecutter/scroller.png", "villager/scroller.png", "crafter/disabled_slot.png",
    "creative_inventory/scroller.png", "creative_inventory/scroller_disabled.png"))
GRIGI_SOPRA = {198: None, 255: ORO_CHIARO, 139: ORO_SCURO, 104: ORO, 85: ORO_SCURO, 55: OSSIDIANA, 0: OSSIDIANA}
GRIGI_RICOLORA = {198: BORDEAUX, 255: ORO_CHIARO, 139: AMETISTA, 104: ORO, 85: ORO_SCURO, 55: OSSIDIANA,
                  0: OSSIDIANA}
INVISIBILI = ("recipe_book/button.png", "recipe_book/button_highlighted.png")


def estensione(grigio, dist, x_testo, larg, ty, nome):
    """Colonne [x0, x1) della fascia: le righe ty-2..ty+8 devono essere solo sfondo (grigio 198, non cornice).
    Restituisce anche se c'è posto per l'ombra sotto (riga ty+9)."""
    h, w = grigio.shape
    righe = slice(ty, min(h, ty + 9))
    libera = ((grigio[righe] == 198) & (dist[righe] > 3)).all(axis=0)
    a, b = int(x_testo), int(x_testo + larg)
    if not libera[a:b].all():
        sys.exit(f"{nome}: la scritta a ({x_testo}, {ty}) cadrebbe su qualcosa che non è sfondo")
    while a > 0 and libera[a - 1]:
        a -= 1
    while b < w and libera[b]:
        b += 1
    sotto = ty + 9 < h and ((grigio[ty + 9, a:b] == 198) & (dist[ty + 9, a:b] > 3)).all()
    # Sopra: sfondo, oppure cornice (titoli a y 4-5 di telaio, cartografia e tagliapietre: la fascia si salda al filo
    # interno). Se c'è altro (caselle del cavallo subito sopra "Inventario"), filetti superiori omessi.
    sp = grigio[max(0, ty - 2):ty, a:b]
    sopra = bool((((sp == 198) | (dist[max(0, ty - 2):ty, a:b] <= 3))).all())
    return a, b, sotto, sopra


def fascia(d, x0, x1, ty, tutta, sotto, sopra, fondo_img):
    """Fascia B2; senza posto sotto (casella subito dopo la scritta) si omettono capello e ombra inferiori,
    ripristinando lo sfondo già disegnato."""
    X0, X1 = x0 * S, x1 * S
    salva = fondo_img.crop((X0, (ty + 9) * S, X1, (ty + 10) * S)) if not sotto else None
    salva_su = fondo_img.crop((X0, (ty - 2) * S, X1, ty * S)) if not sopra else None
    v3.fascia(d, x0, x1, ty)
    if salva is not None:
        fondo_img.paste(salva, (X0, (ty + 9) * S))
    if salva_su is not None:
        fondo_img.paste(salva_su, (X0, (ty - 2) * S))
        d.rectangle([X0, ty * S, X1 - 1, ty * S + 1], fill=v3.FILETTO_B2)
    if not tutta:                                          # fascia interrotta: chiudila con filetti verticali
        top, bot = ty * S - 4, (ty + 8) * S + 4
        for X in (x0 * S, x1 * S - 2):
            d.rectangle([X, top, X + 1, bot], fill=v3.FILETTO_B2)


def normalizza_crafter(orig):
    """Le caselle del fabbricatore hanno un rilievo diverso (bordo 56, smusso 173/115): portate allo schema delle
    caselle ordinarie (bordo 55, interno 139) così vengono riconosciute e disegnate come tutte le altre."""
    a = np.array(orig.convert("RGBA"))
    g = (a[..., 0] == a[..., 1]) & (a[..., 1] == a[..., 2]) & (a[..., 3] > 0)
    for da, a_ in ((56, 55), (173, 139), (115, 139)):
        m = g & (a[..., 0] == da)
        a[m, :3] = a_
    return Image.fromarray(a, "RGBA")


def ridisegna(orig, meta, nome, misura):
    if nome == "crafter.png":
        orig = normalizza_crafter(orig)
    a, opaco, grigio, dist, caselle, irregolari = analizza(orig)
    h, w = opaco.shape
    big = lambda m: np.repeat(np.repeat(m, S, 0), S, 1)
    out = big(a).copy()
    op4, g4, d4 = big(opaco), big(grigio), big(dist)
    dist4 = ndimage.distance_transform_cdt(np.pad(op4, 1), metric="chessboard")[1:-1, 1:-1]
    sfondo = v3.pietra_intarsiata(w, h)
    fondo = op4 & (g4 == 198)
    out[fondo, :3] = sfondo[fondo]
    out[fondo, 3] = 255
    cornice = op4 & (d4 <= 3) & np.isin(g4, [0, 85, 198, 255])
    yy, xx = np.mgrid[0:h * S, 0:w * S]
    alto_sx = (yy + xx) < (h * S + w * S) / 2
    v3.cornice_doppia(out, cornice, dist4, alto_sx, sfondo)
    dentro = op4 & ~cornice
    v3.ombra_interna(out, dentro & fondo, dist4)
    tema = meta.get("tema", "generico")
    v3.colora(out, dentro & (g4 == 139) & ~big(irregolari), RAME if tema == "fornace" else AMETISTA)
    v3.colora(out, dentro & np.isin(g4, [55, 85, 255]) & ~big(irregolari), OSSIDIANA)
    v3.colora(out, dentro & (g4 == 0), OSSIDIANA)
    v3.colora(out, big(irregolari), v2.SUPERFICIE)
    img = Image.fromarray(out, "RGBA")
    d = ImageDraw.Draw(img)
    maggiore = max(caselle, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]), default=None)
    for r in caselle:
        rame = tema == "fornace" and r[0] < 80 and r[1] < 70
        casella(d, *r, importante=(r == maggiore and (r[2] - r[0]) > 16), filetto=RAME if rame else FILETTO)
    ys, xs = np.nonzero(opaco)
    X0, X1, Y1 = xs.min(), xs.max() + 1, ys.max() + 1
    larghezza = X1 - X0
    fatte = set()
    for i, (x, ty) in enumerate(meta["scritte"]):
        larg = 30 if x == CENTRO else 20                    # testo minimo da tenere libero (nomi brevi)
        xt = X0 + (larghezza - larg) // 2 if x == CENTRO else x
        x0, x1, sotto, sopra = estensione(grigio, dist, xt, larg, ty, nome)
        x0, x1 = max(x0, X0 + 3), min(x1, X1 - 3)
        if "fasce" in meta:                                 # fascia di misura fissa, dentro lo spazio libero
            x0, x1 = max(x0, meta["fasce"][i][0]), min(x1, meta["fasce"][i][1])
        if (x0, x1, ty) in fatte:
            continue
        fatte.add((x0, x1, ty))
        fascia(d, x0, x1, ty, x0 == X0 + 3 and x1 == X1 - 3, sotto, sopra, img)
    if tema != "creativa":
        for (x, y) in ((X0 + 1, Y1 - 3), (X1 - 3, Y1 - 3)):
            v3.rivetto(d, x, y)
    v2.tematici(d, tema, caselle)
    return img


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    with zipfile.ZipFile(sys.argv[1]) as jar:
        misura = v3.larghezze_font(jar)
        apri = lambda p: Image.open(io.BytesIO(jar.read(p)))

        def scrivi(img, rel):
            p = os.path.join(BASE, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            img.save(p, optimize=True)
        for nome, meta in SCHERMATE.items():
            scrivi(ridisegna(apri(CONT + nome), meta, nome, misura), CONT + nome)
        for voce in jar.namelist():
            if voce.startswith(SPR + "container/creative_inventory/tab_") and voce.endswith(".png"):
                scrivi(v2.scheda(apri(voce), "_selected_" in voce), voce)
        scrivi(v2.evidenza(apri(SPR + "container/slot_highlight_back.png"), 84), SPR + "container/slot_highlight_back.png")
        scrivi(v2.evidenza(apri(SPR + "container/slot_highlight_front.png"), 30), SPR + "container/slot_highlight_front.png")
        for rel in SOVRAPPOSTE:
            colori = dict(GRIGI_SOPRA)
            if rel.startswith("container/furnace/burn"):
                colori.update({255: (240, 170, 90), 104: RAME})
            if rel.endswith("lit_progress.png"):
                colori[139] = None
            scrivi(v2.sovrapposizione(apri(SPR + rel), colori), SPR + rel)
        for rel in RICOLORATE:
            scrivi(v2.sovrapposizione(apri(SPR + rel), GRIGI_RICOLORA), SPR + rel)
        for rel in INVISIBILI:
            img = apri(SPR + rel).convert("RGBA")
            scrivi(Image.new("RGBA", img.size, (0, 0, 0, 0)), SPR + rel)
        # Mcmeta del nine-slice della casella evidenziata (dimensioni originali in pixel di interfaccia).
        for rel in ("container/slot_highlight_back.png.mcmeta", "container/slot_highlight_front.png.mcmeta"):
            if SPR + rel in jar.namelist():
                p = os.path.join(BASE, SPR + rel)
                with open(p, "wb") as f:
                    f.write(jar.read(SPR + rel))
    print("B2 completa scritta in", os.path.relpath(BASE, QUI))


if __name__ == "__main__":
    main()
