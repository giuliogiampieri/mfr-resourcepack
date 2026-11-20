#!/usr/bin/env python3
"""Inventario e contenitori del gioco nei colori del Banco Magico (viola scuro e oro), con targhette chiare dietro
le scritte.

Uso: python3 genera_contenitori.py <jar del client Minecraft 26.3>   (poi python3 costruisci.py)

Le texture originali stanno nel jar del client (non nel repository): lo script le legge da lì e scrive le versioni
ricolorate in assets/minecraft/textures/gui/container/. Le texture del gioco usano solo 6 grigi, che diventano i
colori del banco. Le scritte dei contenitori ("Inventario", "Baule", "Fornace"...) il gioco le disegna sempre in
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
}


def ricolora(img):
    img = img.convert("RGBA")
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a and r == g == b and r in GRIGI:
                px[x, y] = GRIGI[r] + (a,)
    return img


def targhetta(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=TARGHETTA)
    d.rectangle([x0, y0, x1 - 1, y1 - 1], outline=ORO_SCURO)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    os.makedirs(USCITA, exist_ok=True)
    problemi = []
    with zipfile.ZipFile(sys.argv[1]) as jar:
        for nome, rettangoli in TARGHETTE.items():
            orig = Image.open(io.BytesIO(jar.read(DENTRO + nome))).convert("RGBA")
            for (x0, y0, x1, y1) in rettangoli:
                estranei = sum(1 for y in range(y0, y1) for x in range(x0, x1) if orig.getpixel((x, y))[:3] != (198, 198, 198))
                if estranei:
                    problemi.append(f"{nome} {x0, y0, x1, y1}: {estranei} pixel non di sfondo")
            img = ricolora(orig)
            d = ImageDraw.Draw(img)
            for rett in rettangoli:
                targhetta(d, *rett)
            img.save(os.path.join(USCITA, nome), optimize=True)
            print("scritto", nome)
    if problemi:
        print("TARGHETTE SU CASELLE O DISEGNI:\n  " + "\n  ".join(problemi))
        sys.exit(1)


if __name__ == "__main__":
    main()
