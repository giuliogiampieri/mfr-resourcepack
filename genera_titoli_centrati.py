#!/usr/bin/env python3
"""Titoli dei contenitori centrati con il pacchetto (il client li mette a sinistra, a x = 8 o simili).

Uso: python3 genera_titoli_centrati.py <jar del client 26.3> <it_it.json del gioco> <cartella di destinazione>

Il pacchetto non può spostare il testo, ma può ridefinire i nomi nel file di lingua: davanti a ogni nome mette
caratteri di spazio larghi quanto serve (aggiunti al font minecraft:default, \\uF821.. = +1, +2, +4 ... pixel),
così il testo cade al centro della finestra, come fa il gioco da sé per la fornace: x = (176 - larghezza) / 2.
Scrive assets/minecraft/lang/it_it.json, en_us.json (solo le voci ridefinite: le altre restano quelle del gioco) e
assets/minecraft/font/default.json (solo gli spazi: il gioco unisce i font dei pacchetti a quelli originali).

Esclusi di proposito: schermate già centrate dal gioco (fornaci, distributore, crafter, alambicco, villico),
banco da lavoro (la stessa voce "container.crafting" è usata anche nell'inventario del personaggio a x = 97),
incudine (titolo accanto al martello), forgia (titolo a y = 15), tavolo da incantesimi e telaio (a destra del
titolo ci sono pulsanti e motivi: un titolo centrato ci finirebbe sopra). Limiti: i contenitori con un nome personalizzato
e i giocatori con altre lingue vedono il titolo a sinistra; dove il gioco usa il nome predefinito dentro un
messaggio (per esempio "Baule è chiuso a chiave") compare lo spazio iniziale.
"""
import io
import json
import os
import sys
import zipfile

from PIL import Image

LARGHEZZA_FINESTRA = 176
# voce -> x a cui il gioco scrive il titolo (codice del client 26.3)
TITOLI = {
    "container.chest": 8, "container.chestDouble": 8, "container.enderchest": 8, "container.barrel": 8,
    "container.hopper": 8, "container.shulkerBox": 8, "container.grindstone_title": 8,
    "container.cartography_table": 8, "container.stonecutter": 8,
    "container.inventory": 8,           # "Inventario": x = 8 (villico: 107, area larga uguale)
}
# Titolo dell'inventario (e del banco da lavoro, stessa voce): il gioco lo scrive a (97, 6), sopra la fascia del
# pacchetto (y 7,5..16,5). Il pacchetto lo disegna con una copia delle lettere 2 pixel più in basso (font
# minecraft:default, \uE000 + codice ASCII, ascent 5 invece di 7) e lo centra nella fascia x 76..171 con spazi positivi
# o negativi (\uF801.. = -1, -2, -4, -8). Richiesta del proprietario del 23/11.
SPOSTATI = {"container.crafting": (97, 76, 171, 2)}     # voce -> (x del gioco, inizio fascia, fine fascia, giù di)


def avanzamenti(jar):
    img = Image.open(io.BytesIO(jar.read("assets/minecraft/textures/font/ascii.png"))).convert("RGBA")
    w = {}
    for c in range(32, 127):
        cella = img.crop(((c % 16) * 8, (c // 16) * 8, (c % 16) * 8 + 8, (c // 16) * 8 + 8))
        bb = cella.getchannel("A").getbbox()
        w[chr(c)] = 4 if chr(c) == " " else (bb[2] if bb else 0) + 1
    return w


def spazio(px):
    """px pixel di spazio con i caratteri \\uF821.. (potenze di due)."""
    s = ""
    for i in range(9, -1, -1):
        if px >= 1 << i:
            s += chr(0xF821 + i)
            px -= 1 << i
    return s


def spazio_firmato(px):
    """Come spazio(), anche negativo (\uF801.. = -1, -2, -4, -8)."""
    if px >= 0:
        return spazio(px)
    s, px = "", -px
    for i in range(3, -1, -1):
        while px >= 1 << i:
            s += chr(0xF801 + i)
            px -= 1 << i
    return s


def main():
    jar = zipfile.ZipFile(sys.argv[1])
    it = json.load(open(sys.argv[2], encoding="utf-8"))
    en = json.loads(jar.read("assets/minecraft/lang/en_us.json"))
    dest = sys.argv[3]
    w = avanzamenti(jar)
    for nome, lingua in (("it_it", it), ("en_us", en)):
        voci = {}
        for chiave, x0 in TITOLI.items():
            testo = lingua[chiave]
            if any(ch not in w for ch in testo):
                raise SystemExit(f"{nome} {chiave}: carattere fuori da ascii.png, larghezza non calcolabile")
            larghezza = sum(w[ch] for ch in testo)          # come Font.width del gioco
            px = (LARGHEZZA_FINESTRA - larghezza) // 2 - x0
            voci[chiave] = spazio(px) + testo if px > 0 else testo
            print(f"{nome} {chiave}: '{testo}' largo {larghezza}, spostato di {max(px, 0)}")
        for chiave, (x_gioco, a, b, giu) in SPOSTATI.items():
            testo = lingua[chiave]
            larghezza = sum(w[ch] for ch in testo)
            px = round((a + b) / 2 - (larghezza - 1) / 2) - x_gioco
            voci[chiave] = spazio_firmato(px) + "".join(chr(0xE000 + ord(ch)) for ch in testo)
            print(f"{nome} {chiave}: '{testo}' largo {larghezza}, spostato di {px} e {giu} in giù")
        os.makedirs(os.path.join(dest, "assets", "minecraft", "lang"), exist_ok=True)
        with open(os.path.join(dest, "assets", "minecraft", "lang", nome + ".json"), "w", encoding="utf-8") as f:
            json.dump(voci, f, ensure_ascii=True, indent=2)
            f.write("\n")
    os.makedirs(os.path.join(dest, "assets", "minecraft", "font"), exist_ok=True)
    with open(os.path.join(dest, "assets", "minecraft", "font", "default.json"), "w", encoding="utf-8") as f:
        spazi = {chr(0xF821 + i): 1 << i for i in range(10)}
        spazi.update({chr(0xF801 + i): -(1 << i) for i in range(4)})
        giu = {"type": "bitmap", "file": "minecraft:font/ascii.png", "ascent": 7 - 2,
               "chars": ["".join(chr(0xE000 + r * 16 + c) for c in range(16)) for r in range(16)]}
        json.dump({"providers": [{"type": "space", "advances": spazi}, giu]}, f, ensure_ascii=True, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
