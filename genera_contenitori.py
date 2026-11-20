#!/usr/bin/env python3
"""Inventario e contenitori del gioco nei colori del Banco Magico (viola scuro e oro), con targhette chiare dietro
le scritte.

Uso: python3 genera_contenitori.py <jar del client Minecraft 26.3>   (poi python3 costruisci.py)

Oltre ai contenitori: schede della modalità creativa ricolorate e pulsante del libro delle ricette invisibile.

Le texture originali stanno nel jar del client (non nel repository): lo script le legge da lì e le RIDISEGNA a 4x
(come il banco: il gioco accetta texture dei contenitori a risoluzione maggiore) in
assets/minecraft/textures/gui/container/: cornice d'oro sfumata larga 2 pixel di interfaccia, sfondo viola a
righine, caselle scure con bordo d'oro, frecce e disegni in oro scuro, targhette come quella del banco. Le scritte dei contenitori ("Inventario", "Baule", "Fornace"...) il gioco le disegna sempre in
grigio scuro (0x404040) e il pacchetto non le può cambiare: sul viola scuro non si leggerebbero, quindi dietro
ogni scritta c'è una targhetta chiara larga quanto la finestra (anche i nomi lunghi dei bauli rinominati ci stanno).
Lo script controlla che le targhette coprano solo lo sfondo, mai caselle o disegni.
"""
import io
import os
import sys
import zipfile

from PIL import Image, ImageDraw

QUI = os.path.dirname(os.path.abspath(__file__))
USCITA = os.path.join(QUI, "assets", "minecraft", "textures", "gui", "container")
DENTRO = "assets/minecraft/textures/gui/container/"

GRIGI = {
    198: (46, 14, 34),      # sfondo della finestra -> viola del banco
    139: (84, 34, 66),      # interno delle caselle e frecce -> viola medio (le frecce restano visibili)
    255: (232, 168, 48),    # luce del rilievo e bordo chiaro delle caselle -> oro
    85: (122, 72, 14),      # ombra del rilievo -> oro scuro
    55: (20, 6, 14),        # bordo scuro delle caselle
    0: (14, 5, 10),         # contorno
}
TARGHETTA = (214, 190, 140)
ORO_SCURO = (122, 72, 14)

# Targhette (x0, y0, x1, y1), estremi esclusi in fondo, in pixel della texture: dove il gioco scrive titolo ed
# etichetta "Inventario" di ogni schermata. Il baule (generic_54) è disegnato in due pezzi: l'etichetta è a y 128
# della texture. Beacon: scritte chiare, nessuna targhetta. Creativa e scelta della modalità: non toccate.
TARGHETTE = {
    "generic_54.png": [(7, 4, 169, 15), (7, 126, 169, 137)],
    "shulker_box.png": [(7, 4, 169, 15), (7, 71, 169, 81)],
    "dispenser.png": [(7, 4, 169, 15), (7, 70, 169, 81)],
    "crafter.png": [(7, 4, 169, 15), (7, 70, 169, 81)],
    "hopper.png": [(7, 4, 169, 15), (7, 37, 169, 48)],
    "furnace.png": [(7, 4, 169, 15), (7, 70, 169, 81)],
    "blast_furnace.png": [(7, 4, 169, 15), (7, 70, 169, 81)],
    "smoker.png": [(7, 4, 169, 15), (7, 70, 169, 81)],
    "crafting_table.png": [(27, 4, 169, 15), (7, 70, 169, 81)],
    "inventory.png": [(95, 6, 170, 17)],
    "brewing_stand.png": [(7, 4, 169, 15), (7, 70, 77, 81)],
    "enchanting_table.png": [(10, 3, 169, 13), (7, 70, 58, 81)],
    "anvil.png": [(58, 4, 170, 15), (7, 70, 169, 81)],
    "grindstone.png": [(7, 4, 169, 15), (7, 71, 169, 81)],
    "smithing.png": [(42, 13, 169, 24), (7, 70, 169, 81)],
    "stonecutter.png": [(7, 3, 169, 14), (7, 70, 169, 81)],
    "loom.png": [(5, 3, 140, 12), (7, 70, 137, 81)],
    "cartography_table.png": [(7, 3, 169, 13), (7, 70, 169, 81)],
    "horse.png": [(7, 4, 169, 15), (7, 71, 169, 81)],
    "nautilus.png": [(7, 4, 169, 15), (7, 71, 169, 81)],
    "villager.png": [(4, 4, 272, 15), (105, 70, 272, 81)],
    "beacon.png": [],
    # Inventario della modalità creativa (staff): titolo della scheda a (8, 6), casella di ricerca da x = 80.
    "creative_inventory/tab_inventory.png": [],
    "creative_inventory/tab_items.png": [(7, 4, 190, 16)],
    "creative_inventory/tab_item_search.png": [(7, 4, 79, 16)],
}

# Altre immagini dell'interfaccia (cartella sprites) ricolorate senza targhette: schede e barra della creativa.
SPRITE_DIR = "assets/minecraft/textures/gui/sprites/"
SPRITE_PREFISSI = ("container/creative_inventory/",)
# Pulsante del libro delle ricette (fornaci, banco da lavoro, inventario): reso invisibile su richiesta del
# proprietario. Il gioco lo tiene comunque nello stesso posto: cliccando lì il libro si apre ancora.
INVISIBILI = ("recipe_book/button.png", "recipe_book/button_highlighted.png")


def ricolora(img):
    img = img.convert("RGBA")
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a and r == g == b and r in GRIGI:
                px[x, y] = GRIGI[r] + (a,)
    return img


S = 4
VIOLA, VIOLA_SCURO = (46, 14, 34), (28, 8, 20)
ORO_CHIARO, ORO_M = (255, 224, 140), (232, 168, 48)
CASELLA, OMBRA = (30, 12, 22), (14, 5, 10)


def ridisegna(orig, rettangoli):
    """Texture del gioco (1x) -> versione 4x nello stile del banco, con le targhette."""
    import numpy as np
    from scipy import ndimage
    a = np.array(orig.convert("RGBA"))
    h, w = a.shape[:2]
    opaco = a[..., 3] > 0
    grigio = np.where((a[..., 0] == a[..., 1]) & (a[..., 1] == a[..., 2]) & opaco, a[..., 0].astype(int), -1)
    dist1 = ndimage.distance_transform_cdt(np.pad(opaco, 1), metric="chessboard")[1:-1, 1:-1]
    # Caselle: zone del grigio 139 che toccano il bordo scuro (55); le rettangolari hanno anche l'ombra interna.
    # Le altre zone 139 (frecce, fiamme, bolle) sono disegni e diventano oro scuro.
    interno = np.zeros((h, w), bool)
    primo = np.zeros((h, w), bool)                     # prima riga e prima colonna dell'interno (ombra)
    etichette, n = ndimage.label(grigio == 139)
    for i, sl in enumerate(ndimage.find_objects(etichette), start=1):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        pieno = (etichette[sl] == i).all()
        bordo = y0 > 0 and x0 > 0 and (grigio[y0 - 1, x0:x1] == 55).all() and (grigio[y0:y1, x0 - 1] == 55).all()
        if pieno and bordo and (y1 - y0) >= 8 and (x1 - x0) >= 8:
            interno[sl] = True
            primo[y0, x0:x1] = True
            primo[y0:y1, x0] = True
        elif (ndimage.binary_dilation(etichette == i) & (grigio == 55)).any():
            interno[etichette == i] = True              # casella di forma irregolare (bottiglie dell'alambicco)
    big = lambda m: np.repeat(np.repeat(m, S, 0), S, 1)
    out = big(a).copy()
    g4, d1_4, int4, primo4 = big(grigio), big(dist1), big(interno), big(primo)
    op4 = big(opaco)
    dist4 = ndimage.distance_transform_cdt(np.pad(op4, 1), metric="chessboard")[1:-1, 1:-1]
    yy = np.arange(h * S)[:, None] * np.ones((1, w * S), int)
    righine = np.where(((yy // 2) % 3 == 0)[..., None], np.array(VIOLA_SCURO), np.array(VIOLA))
    cornice = op4 & (d1_4 <= 3) & np.isin(g4, [0, 85, 198, 255])
    dentro = op4 & ~cornice

    def colora(maschera, colore):
        out[maschera, :3] = colore if not isinstance(colore, np.ndarray) else colore[maschera]
        out[maschera, 3] = 255

    colora(dentro & (g4 == 198), righine)
    colora(cornice & (dist4 > 8), righine)             # terzo pixel del rilievo del gioco: già corpo
    colora(cornice & (dist4 <= 8) & (dist4 >= 7), ORO_SCURO)
    colora(cornice & (dist4 <= 6) & (dist4 >= 3), ORO_M)
    colora(cornice & (dist4 <= 2), ORO_CHIARO)
    colora(dentro & (g4 == 55), ORO_M)                 # bordo alto e sinistro delle caselle
    colora(dentro & np.isin(g4, [255, 85]), ORO_SCURO)  # bordo basso e destro delle caselle
    colora(dentro & (g4 == 0), OMBRA)
    colora(int4, CASELLA)
    colora(int4 & primo4, OMBRA)
    colora(dentro & (g4 == 139) & ~int4, ORO_SCURO)    # frecce e disegni
    img = Image.fromarray(out, "RGBA")
    d = ImageDraw.Draw(img)
    for (x0, y0, x1, y1) in rettangoli:
        d.rectangle([x0 * S, y0 * S, x1 * S - 1, y1 * S - 1], fill=TARGHETTA)
        for i in range(S):
            c = ORO_CHIARO if i < S // 2 else ORO_SCURO
            d.rectangle([x0 * S + i, y0 * S + i, x1 * S - 1 - i, y1 * S - 1 - i], outline=c)
    return img


def targhetta(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=TARGHETTA)
    d.rectangle([x0, y0, x1 - 1, y1 - 1], outline=ORO_SCURO)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    problemi = []
    with zipfile.ZipFile(sys.argv[1]) as jar:
        for nome, rettangoli in TARGHETTE.items():
            orig = Image.open(io.BytesIO(jar.read(DENTRO + nome))).convert("RGBA")
            for (x0, y0, x1, y1) in rettangoli:
                estranei = sum(1 for y in range(y0, y1) for x in range(x0, x1) if orig.getpixel((x, y))[:3] != (198, 198, 198))
                if estranei:
                    problemi.append(f"{nome} {x0, y0, x1, y1}: {estranei} pixel non di sfondo")
            scrivi(ridisegna(orig, [inventario_corto(r) for r in rettangoli]), os.path.join(USCITA, nome))
        for voce in sorted(jar.namelist()):
            rel = voce[len(SPRITE_DIR):] if voce.startswith(SPRITE_DIR) else None
            if rel is None or not voce.endswith(".png"):
                continue
            uscita = os.path.join(QUI, voce)
            if rel.startswith(SPRITE_PREFISSI):
                scrivi(ricolora(Image.open(io.BytesIO(jar.read(voce)))), uscita)
            elif rel in INVISIBILI:
                dim = Image.open(io.BytesIO(jar.read(voce))).size
                scrivi(Image.new("RGBA", dim, (0, 0, 0, 0)), uscita)
    if problemi:
        print("TARGHETTE SU CASELLE O DISEGNI:\n  " + "\n  ".join(problemi))
        sys.exit(1)


def inventario_corto(rett):
    """Targhetta di "Inventario" lunga come quella del banco (61 pixel); i titoli restano larghi quanto la finestra."""
    x0, y0, x1, y1 = rett
    return (x0, y0, min(x1, x0 + 61), y1) if y0 >= 35 else rett


def scrivi(img, percorso):
    os.makedirs(os.path.dirname(percorso), exist_ok=True)
    img.save(percorso, optimize=True)
    print("scritto", os.path.relpath(percorso, QUI))


if __name__ == "__main__":
    main()
