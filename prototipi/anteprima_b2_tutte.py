#!/usr/bin/env python3
"""Foglio di controllo della B2 completa: ogni schermata con le scritte italiane dove le mette il gioco (titoli
centrati dove il pacchetto ridefinisce la lingua). Uso: python3 anteprima_b2_tutte.py <jar> <cartella uscita>"""
import io, os, sys, zipfile, json
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import anteprima_gui_v2 as a2  # noqa: E402  (stessa cartella)
import genera_gui_b2 as b2      # noqa: E402

QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B2 = os.path.join(QUI, "prototipi", "gui-v3-B2")
it = json.load(open(os.path.join(B2, "assets/minecraft/lang/it_it.json"), encoding="utf-8"))
NOMI = {  # testi italiani (lingua del gioco 26.3); quelli centrati dal pacchetto hanno lo spazio iniziale
    "generic_54.png": ["Baule", "Inventario"], "shulker_box.png": ["Scatola di shulker", "Inventario"],
    "dispenser.png": ["Distributore", "Inventario"], "crafter.png": ["Fabbricatore", "Inventario"],
    "hopper.png": ["Tramoggia", "Inventario"], "furnace.png": ["Fornace", "Inventario"],
    "blast_furnace.png": ["Forno fusorio", "Inventario"], "smoker.png": ["Affumicatore", "Inventario"],
    "crafting_table.png": ["Fabbricazione", "Inventario"], "inventory.png": ["Fabbricazione"],
    "brewing_stand.png": ["Alambicco", "Inventario"], "enchanting_table.png": ["Incanta", "Inventario"],
    "anvil.png": ["Ripara e denomina", "Inventario"], "grindstone.png": ["Ripara e disincanta", "Inventario"],
    "smithing.png": ["Migliora un oggetto", "Inventario"], "stonecutter.png": ["Tagliapietre", "Inventario"],
    "loom.png": ["Telaio", "Inventario"], "cartography_table.png": ["Cartografia", "Inventario"],
    "horse.png": ["Cavallo", "Inventario"], "nautilus.png": ["Nautilo", "Inventario"],
    "villager.png": ["Scambi", "Corazzaio", "Inventario"], "beacon.png": [],
    "creative_inventory/tab_items.png": ["Blocchi da costruzione"], "creative_inventory/tab_item_search.png": ["Cerca..."],
}
CENTRATI = {v.lstrip("\uf821\uf822\uf823\uf824\uf825\uf826\uf827\uf828\uf829\uf82a") for v in it.values()}


def main():
    jar = zipfile.ZipFile(sys.argv[1]); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    glifi = a2.font_gioco(jar)
    pannelli = []
    for nome, meta in b2.SCHERMATE.items():
        if nome == "creative_inventory/tab_inventory.png":
            continue
        tex = Image.open(os.path.join(B2, b2.CONT, nome)).convert("RGBA")
        k = tex.width // Image.open(io.BytesIO(jar.read(b2.CONT + nome))).width
        bb = tex.getchannel("A").getbbox()
        w, h = (bb[2] + k - 1) // k, (bb[3] + k - 1) // k
        tela = tex.crop((0, 0, w * k, h * k)).resize((w * 2, h * 2), Image.NEAREST)
        testo = Image.new("RGBA", (w, h))
        for (x, y), s in zip(meta["scritte"], NOMI[nome]):
            centrato = s in CENTRATI and nome not in ("crafting_table.png", "inventory.png")
            if x == b2.CENTRO or (centrato and w <= 176):
                xx = ((176 if w <= 176 else w) - a2.larghezza(glifi, s)) // 2 if x == b2.CENTRO or centrato else x
                if nome == "villager.png" and x == b2.CENTRO:
                    xx = 49 + w // 2 - a2.larghezza(glifi, s) // 2
            else:
                xx = x
            a2.scrivi_testo(testo, glifi, s, xx, y)
        tela.alpha_composite(testo.resize((w * 2, h * 2), Image.NEAREST))
        pannelli.append((nome.split("/")[-1][:-4], tela))
    col = 3; pad = 16
    righe = [pannelli[i:i + col] for i in range(0, len(pannelli), col)]
    W = col * (max(p.width for _, p in pannelli) + pad) + pad
    H = sum(max(p.height for _, p in r) + 30 for r in righe) + pad
    foglio = Image.new("RGBA", (W, H), (30, 36, 34, 255)); d = ImageDraw.Draw(foglio)
    y = pad
    for r in righe:
        x = pad
        for n, p in r:
            d.text((x, y), n, fill=(230, 220, 190)); foglio.alpha_composite(p, (x, y + 14)); x += p.width + pad
        y += max(p.height for _, p in r) + 30
    foglio.save(os.path.join(out, "b2_tutte_scala2.png"))
    print(os.path.join(out, "b2_tutte_scala2.png"), foglio.size)


main()
