#!/usr/bin/env python3
"""Anteprime affiancate attuale | variante A | variante B del prototipo GUI v3 (campionamento "nearest").

Uso: python3 prototipi/anteprima_gui_v3.py <jar del client 26.3> <cartella di uscita> [varianti, es. B,B2]
Oggetti, posizioni e caselle identici nelle tre colonne; etichette con il font del gioco nel grigio 0x404040.
MOCKUP: posizioni dal codice del client 26.3; schede della creativa approssimate; baule da 3 righe.
"""
import importlib.util
import os
import sys
import zipfile

from PIL import Image, ImageDraw, ImageFont

QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("anteprima_v2", os.path.join(QUI, "prototipi", "anteprima_gui_v2.py"))
a2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a2)
CONT, SPR = a2.CONT, a2.SPR


def sfondo_finestra(f, nome, w, h):
    tex = f(CONT + nome)
    k = tex.width // 256
    return tex.crop((0, 0, w * k, h * k)).resize((w * 4, h * 4), Image.NEAREST)


def etichette(tela, glifi, voci, w, h):
    t = Image.new("RGBA", (w, h))
    for testo, x, y in voci:
        a2.scrivi_testo(t, glifi, testo, x, y)
    tela.alpha_composite(t.resize((w * 4, h * 4), Image.NEAREST))


def oggetti(tela, jar, voci, dy=0):
    for (x, y), n in voci.items():
        a2.blit(tela, a2.oggetto(jar, n), x, y + dy, 16, 16)


def fornace(f, jar, glifi, titolo="Fornace"):
    tela = Image.new("RGBA", (176 * 4, 166 * 4))
    tela.alpha_composite(sfondo_finestra(f, "furnace.png", 176, 166))
    lit = f(SPR + "container/furnace/lit_progress.png")
    a2.blit(tela, lit.crop((0, lit.height * 5 // 14, lit.width, lit.height)), 56, 41, 14, 9)
    arrow = f(SPR + "container/furnace/burn_progress.png")
    a2.blit(tela, arrow.crop((0, 0, arrow.width * 15 // 24, arrow.height)), 79, 34, 15, 16)
    a2.blit(tela, f(SPR + "container/slot_highlight_back.png"), 58, 80, 24, 24)
    oggetti(tela, jar, {(56, 17): "raw_iron", (56, 53): "coal", (116, 35): "iron_ingot", (8, 142): "bread",
                        (26, 142): "stick", (44, 142): "iron_sword", (8, 84): "arrow", (62, 84): "apple"})
    a2.blit(tela, f(SPR + "container/slot_highlight_front.png"), 58, 80, 24, 24)
    etichette(tela, glifi, [(titolo, (176 - a2.larghezza(glifi, titolo)) // 2, 6), ("Inventario", 8, 72)], 176, 166)
    return tela


def tramoggia(f, jar, glifi):
    tela = Image.new("RGBA", (176 * 4, 133 * 4))
    tela.alpha_composite(sfondo_finestra(f, "hopper.png", 176, 133))
    oggetti(tela, jar, {(44, 20): "iron_ingot", (62, 20): "gold_nugget", (8, 109): "bread", (26, 109): "coal"})
    etichette(tela, glifi, [("Tramoggia", 8, 6), ("Inventario", 8, 39)], 176, 133)
    return tela


def baule(f, jar, glifi):
    """Baule da 3 righe: pezzo alto della texture (3*18+17 = 71 px) + pezzo basso (96 px da y = 126)."""
    tex = f(CONT + "generic_54.png")
    k = tex.width // 256
    tela = Image.new("RGBA", (176 * 4, 167 * 4))
    tela.alpha_composite(tex.crop((0, 0, 176 * k, 71 * k)).resize((704, 284), Image.NEAREST), (0, 0))
    tela.alpha_composite(tex.crop((0, 126 * k, 176 * k, 222 * k)).resize((704, 384), Image.NEAREST), (0, 284))
    oggetti(tela, jar, {(8, 18): "apple", (26, 18): "bread", (8, 36): "iron_ingot", (8, 143): "stick"})
    etichette(tela, glifi, [("Baule", 8, 6), ("Inventario", 8, 73)], 176, 167)
    return tela


def banco(f, jar, glifi):
    tela = Image.new("RGBA", (176 * 4, 166 * 4))
    tela.alpha_composite(sfondo_finestra(f, "crafting_table.png", 176, 166))
    oggetti(tela, jar, {(30, 17): "stick", (48, 17): "stick", (30, 35): "iron_ingot", (124, 35): "iron_pickaxe",
                        (8, 142): "bread"})
    etichette(tela, glifi, [("Fabbricazione", 29, 6), ("Inventario", 8, 72)], 176, 166)
    return tela


def creativa(f, jar, glifi):
    return a2.creativa(f, jar, glifi)


def colonne(immagini, titoli, scala):
    imgs = [a2.schermo(i, scala) for i in immagini]
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    W = sum(i.width for i in imgs) + 40 * (len(imgs) + 1)
    H = max(i.height for i in imgs) + 70
    tela = Image.new("RGBA", (W, H), (34, 44, 38, 255))
    d = ImageDraw.Draw(tela)
    for y in range(0, H, 6):
        d.line([(0, y), (W, y)], fill=(30 + y % 18, 40 + y % 12, 34, 255))
    x = 40
    for img, t in zip(imgs, titoli):
        tela.alpha_composite(img, (x, 55))
        d.text((x, 16), t, font=font, fill=(240, 212, 154) if t != titoli[0] else (235, 235, 235))
        x += img.width + 40
    return tela.convert("RGB")


def main():
    jar = zipfile.ZipFile(sys.argv[1])
    uscita = sys.argv[2]
    os.makedirs(uscita, exist_ok=True)
    glifi = a2.font_gioco(jar)
    varianti = sys.argv[3].split(",") if len(sys.argv) > 3 else ["A", "B"]
    fonti = [a2.Fonti(jar, QUI)] + [a2.Fonti(jar, os.path.join(QUI, "prototipi", f"gui-v3-{v}")) for v in varianti]
    nomi = {"A": "A  Cartiglio", "B": "B  Architrave", "B2": "B2  Fascia sottile"}
    for nome, fn in (("fornace", fornace), ("tramoggia", tramoggia), ("baule", baule), ("banco", banco),
                     ("creativa", creativa)):
        for scala in (2, 3):
            img = colonne([fn(f, jar, glifi) for f in fonti], [f"ATTUALE - scala {scala}"] + [nomi[v] for v in varianti],
                          scala)
            img.save(os.path.join(uscita, f"{nome}_scala{scala}.png"))
    lungo = "Fornace della Gilda dei Fabbri"
    img = colonne([fornace(f, jar, glifi, lungo) for f in fonti[1:]], [nomi[v] + " - nome lungo" for v in varianti], 2)
    img.save(os.path.join(uscita, "nome_lungo_scala2.png"))
    print("anteprime in", uscita)


if __name__ == "__main__":
    main()
