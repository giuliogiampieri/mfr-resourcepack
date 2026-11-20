#!/usr/bin/env python3
"""Anteprima prima/dopo del prototipo GUI v2, come la vede il giocatore (campionamento "nearest" come Minecraft).

Uso: python3 prototipi/anteprima_gui_v2.py <jar del client 26.3> <cartella di uscita>
"Prima" = texture attuali del pacchetto (assets/), "dopo" = prototipi/gui-v2/. Sprite non presenti nel pacchetto:
quelli originali del gioco. Etichette con il font del gioco (ascii.png) nel grigio 0x404040 dei contenitori.
È un MOCKUP: posizioni ricavate dal codice del client 26.3, schede della creativa approssimate.
"""
import io
import os
import sys
import zipfile

from PIL import Image, ImageDraw, ImageFont

QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONT = "assets/minecraft/textures/gui/container/"
SPR = "assets/minecraft/textures/gui/sprites/"
GRIGIO = (64, 64, 64, 255)


class Fonti:
    def __init__(self, jar, cartella):
        self.jar, self.cartella = jar, cartella

    def __call__(self, rel):
        p = os.path.join(self.cartella, rel)
        if os.path.exists(p):
            return Image.open(p).convert("RGBA")
        return Image.open(io.BytesIO(self.jar.read(rel))).convert("RGBA")


def font_gioco(jar):
    img = Image.open(io.BytesIO(jar.read("assets/minecraft/textures/font/ascii.png"))).convert("RGBA")
    glifi = {}
    for code in range(32, 127):
        cella = img.crop(((code % 16) * 8, (code // 16) * 8, (code % 16) * 8 + 8, (code // 16) * 8 + 8))
        bb = cella.getchannel("A").getbbox()
        glifi[chr(code)] = (cella, 4 if chr(code) == " " else (bb[2] if bb else 0) + 1)
    return glifi


def scrivi_testo(tela, glifi, testo, x, y):
    for ch in testo:
        cella, avanzamento = glifi.get(ch, glifi["?"])
        colorata = Image.new("RGBA", cella.size, GRIGIO)
        tela.alpha_composite(Image.composite(colorata, Image.new("RGBA", cella.size), cella.getchannel("A")), (x, y))
        x += avanzamento


def larghezza(glifi, testo):
    return sum(glifi.get(ch, glifi["?"])[1] for ch in testo) - 1


def oggetto(jar, nome):
    return Image.open(io.BytesIO(jar.read(f"assets/minecraft/textures/item/{nome}.png"))).convert("RGBA").crop((0, 0, 16, 16))


def blit(tela, img, x, y, w, h, scala_tex=None):
    """Disegna img (anche ad alta risoluzione) in un rettangolo w x h di pixel di interfaccia, a 4 sotto-pixel."""
    tela.alpha_composite(img.resize((w * 4, h * 4), Image.NEAREST), (x * 4, y * 4))


def fornace(f, jar, glifi):
    tela = Image.new("RGBA", (176 * 4, 166 * 4))
    tex = f(CONT + "furnace.png")
    tela.alpha_composite(tex.crop((0, 0, tex.width * 176 // 256, tex.height * 166 // 256)).resize((704, 664), Image.NEAREST))
    lit = f(SPR + "container/furnace/lit_progress.png")
    k = 9                                                        # fiamma consumata in parte (14 -> 9 righe)
    blit(tela, lit.crop((0, lit.height * (14 - k) // 14, lit.width, lit.height)), 56, 36 + 14 - k, 14, k)
    arrow = f(SPR + "container/furnace/burn_progress.png")
    blit(tela, arrow.crop((0, 0, arrow.width * 15 // 24, arrow.height)), 79, 34, 15, 16)
    items = {(56, 17): "raw_iron", (56, 53): "coal", (116, 35): "iron_ingot", (8, 142): "bread", (26, 142): "stick",
             (44, 142): "iron_sword", (8, 84): "arrow"}
    evid = (62, 84)
    blit(tela, f(SPR + "container/slot_highlight_back.png"), evid[0] - 4, evid[1] - 4, 24, 24)
    for (x, y), n in items.items():
        blit(tela, oggetto(jar, n), x, y, 16, 16)
    blit(tela, oggetto(jar, "apple"), *evid, 16, 16)
    blit(tela, f(SPR + "container/slot_highlight_front.png"), evid[0] - 4, evid[1] - 4, 24, 24)
    testo = Image.new("RGBA", (176, 166))
    scrivi_testo(testo, glifi, "Fornace", (176 - larghezza(glifi, "Fornace")) // 2, 6)
    scrivi_testo(testo, glifi, "Inventario", 8, 72)
    tela.alpha_composite(testo.resize((704, 664), Image.NEAREST))
    return tela


def tramoggia(f, jar, glifi):
    tela = Image.new("RGBA", (176 * 4, 133 * 4))
    tex = f(CONT + "hopper.png")
    tela.alpha_composite(tex.crop((0, 0, tex.width * 176 // 256, tex.height * 133 // 256)).resize((704, 532), Image.NEAREST))
    for (x, y), n in {(44, 20): "iron_ingot", (62, 20): "gold_nugget", (8, 109): "bread", (26, 109): "coal"}.items():
        blit(tela, oggetto(jar, n), x, y, 16, 16)
    testo = Image.new("RGBA", (176, 133))
    scrivi_testo(testo, glifi, "Tramoggia", 8, 6)
    scrivi_testo(testo, glifi, "Inventario", 8, 39)
    tela.alpha_composite(testo.resize((704, 532), Image.NEAREST))
    return tela


def creativa(f, jar, glifi):
    W, H, M = 195, 136, 30                                       # pannello e margine per le schede
    tela = Image.new("RGBA", (W * 4, (H + 2 * M) * 4))
    icone_su = ["brick", "cyan_dye", "wheat_seeds", "oak_sign", "redstone"]
    icone_giu = ["diamond_pickaxe", "iron_sword", "golden_apple", "iron_ingot"]
    def tab(col, alto, sel, icona, destra=False):
        x = (W - 27) if destra else 27 * col
        y = M - 28 if alto else M + H - 4
        nome = f"tab_{'top' if alto else 'bottom'}_{'selected' if sel else 'unselected'}_{min(col, 6) + 1}.png"
        blit(tela, f(SPR + "container/creative_inventory/" + nome), x, y, 26, 32)
        if icona:
            blit(tela, oggetto(jar, icona), x + 5, y + (9 if alto else 7), 16, 16)
    for i, ic in enumerate(icone_su):
        tab(i, True, False, ic)
    tab(6, True, False, "compass_00", destra=True)
    for i, ic in enumerate(icone_giu):
        tab(i, False, False, ic)
    tex = f(CONT + "creative_inventory/tab_inventory.png")
    tela.alpha_composite(tex.crop((0, 0, tex.width * W // 256, tex.height * H // 256)).resize((W * 4, H * 4), Image.NEAREST), (0, M * 4))
    tab(6, False, True, None, destra=True)
    for (x, y), n in {(9, 112): "bread", (27, 112): "iron_pickaxe", (45, 112): "apple"}.items():
        blit(tela, oggetto(jar, n), x, y + M, 16, 16)
    return tela


def schermo(img, scala):
    """Come appare a scala d'interfaccia 'scala': 1 pixel di interfaccia = 'scala' pixel, campionamento nearest."""
    return img.resize((img.width * scala // 4, img.height * scala // 4), Image.NEAREST)


def main():
    jar = zipfile.ZipFile(sys.argv[1])
    uscita = sys.argv[2]
    os.makedirs(uscita, exist_ok=True)
    glifi = font_gioco(jar)
    prima = Fonti(jar, QUI)
    dopo = Fonti(jar, os.path.join(QUI, "prototipi", "gui-v2"))
    etichetta = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    for nome, fn in (("fornace", fornace), ("tramoggia", tramoggia), ("creativa", creativa)):
        for scala in (2, 3):
            a, b = schermo(fn(prima, jar, glifi), scala), schermo(fn(dopo, jar, glifi), scala)
            tela = Image.new("RGBA", (a.width + b.width + 90, max(a.height, b.height) + 70), (34, 44, 38, 255))
            for i in range(0, tela.height, 6):                    # sfondo "mondo" scuro e sfocato
                ImageDraw.Draw(tela).line([(0, i), (tela.width, i)], fill=(30 + i % 18, 40 + i % 12, 34, 255))
            tela.alpha_composite(a, (30, 55))
            tela.alpha_composite(b, (a.width + 60, 55))
            d = ImageDraw.Draw(tela)
            d.text((30, 14), f"PRIMA (attuale) - scala {scala}", font=etichetta, fill=(240, 240, 240))
            d.text((a.width + 60, 14), f"DOPO (prototipo v2) - scala {scala}", font=etichetta, fill=(240, 212, 154))
            p = os.path.join(uscita, f"{nome}_scala{scala}.png")
            tela.convert("RGB").save(p)
            print(p)


if __name__ == "__main__":
    main()
