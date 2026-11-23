#!/usr/bin/env python3
"""Barre a fiala sopra la hotbar (#191 nel repository del server): vita, fame e sete nello stile della fiala del mana.

Decisioni del proprietario (22/11/2026): barre disegnate da noi; vita con contorno dorato, un cuoricino accanto e
tacche per contare i cuori; fame e sete con contorno argentato. Il 23/11 il proprietario ha lasciato a Claude il primo
disegno di vita e fame ("poi al massimo le aggiustiamo"). Icona della fame (coscia) e della sete (goccia): proposta.

Ogni barra è larga 82 pixel e alta 9, come la fila dei cuori: icona 9x9, un pixel vuoto, fiala di 72x7 (interno di
70 pixel, 7 per cuore: le tacche cadono ogni 2 punti di vita). Il server le disegnerà come caratteri di un font nella
barra delle azioni: sfondo (fiala vuota con icona e tacche), poi uno spazio negativo e il liquido del livello giusto.

Uso: python3 genera_barre_hud.py
  → assets/mfr/textures/font/hud/<barra>_vuota.png    (82x9: icona, vetro vuoto, tacche)
  → assets/mfr/textures/font/hud/<barra>_liquido.png  (82x189: 21 righe da 9, livelli 0..20 dall'alto)
  → assets/mfr/font/hud.json                          (font mfr:hud: barre e spazi)
  → assets/minecraft/textures/gui/sprites/hud/heart/*.png, food_*.png (trasparenti)
"""
import pathlib
from PIL import Image

QUI = pathlib.Path(__file__).resolve().parent
CARTELLA = QUI / "assets/mfr/textures/font/hud"
L, A = 82, 9
FX0, FX1, FY0, FY1 = 10, 81, 1, 7          # fiala: colonne 10..81, righe 1..7 (contorno compreso)
INTERNO = FX1 - FX0 - 1                    # 70 pixel di liquido
LIVELLI = 21                               # 0..20

ORO = dict(alto=(255, 226, 130), basso=(150, 98, 30), lato=(222, 172, 70))
ARGENTO = dict(alto=(240, 242, 250), basso=(118, 124, 140), lato=(190, 195, 210))
BARRE = {
    "vita": dict(cornice=ORO, inizio=(170, 18, 30), fine=(235, 60, 60), tacche=True, icona="cuore"),
    "fame": dict(cornice=ARGENTO, inizio=(170, 92, 30), fine=(226, 150, 60), tacche=False, icona="coscia"),
    "sete": dict(cornice=ARGENTO, inizio=(30, 120, 200), fine=(90, 200, 235), tacche=False, icona="goccia"),
}
VUOTO = (22, 26, 44)
RIFLESSO_VUOTO = (60, 66, 92)

# Icone 9x9 (originali, nello stile dei simboli del HUD): . trasparente, lettere = colori qui sotto.
ICONE = {
    "cuore": [
        ".KK...KK.",
        "KrrK.KrrK",
        "KrwrKrrrK",
        "KrrrrrrrK",
        "KrrrrrrdK",
        ".KrrrrdK.",
        "..KrrdK..",
        "...KdK...",
        "....K....",
    ],
    "coscia": [
        "......KK.",
        ".....KwwK",
        "....KwwK.",
        "..KKKwK..",
        ".KoooK...",
        "KoyoooK..",
        "KooooodK.",
        ".KoooddK.",
        "..KKKKK..",
    ],
    "goccia": [
        "....K....",
        "...KbK...",
        "...KbK...",
        "..KbbbK..",
        ".KbwbbbK.",
        ".KwbbbbK.",
        ".KbbbbdK.",
        "..KbddK..",
        "...KKK...",
    ],
}
COLORI = {"K": (34, 16, 20), "r": (220, 40, 48), "d": (140, 18, 28), "w": (255, 235, 225), "o": (200, 120, 50),
          "y": (240, 190, 110), "b": (60, 160, 230)}
COLORI_ICONA = {"goccia": {"d": (30, 90, 170)}, "coscia": {"d": (130, 70, 25), "w": (245, 235, 215)}}


def misto(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def scuro(c, f):
    return tuple(int(v * f) for v in c)


def chiaro(c, f):
    return tuple(int(v + (255 - v) * f) for v in c)


def nella_fiala(x, y):
    """Estremi arrotondati: i quattro angoli della fiala restano trasparenti."""
    return FX0 <= x <= FX1 and FY0 <= y <= FY1 and not (x in (FX0, FX1) and y in (FY0, FY1))


def bordo(x, y):
    return x in (FX0, FX1) or y in (FY0, FY1)


def tacca(x):
    """Ogni 2 punti di vita (7 pixel di liquido) una tacca, esclusi gli estremi."""
    i = x - FX0 - 1
    return 0 < i < INTERNO and i % 7 == 6


def icona(im, nome):
    colori = dict(COLORI, **COLORI_ICONA.get(nome, {}))
    for y, riga in enumerate(ICONE[nome]):
        for x, ch in enumerate(riga):
            if ch != ".":
                im.putpixel((x, y), colori[ch] + (255,))


def vuota(b):
    im = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    icona(im, b["icona"])
    c = b["cornice"]
    for x in range(L):
        for y in range(A):
            if not nella_fiala(x, y):
                continue
            if y == FY0:
                p = c["alto"] + (235,)
            elif y == FY1:
                p = c["basso"] + (235,)
            elif x in (FX0, FX1):
                p = c["lato"] + (235,)
            elif b["tacche"] and tacca(x):
                p = misto(c["lato"], VUOTO, 0.45) + (220,)
            elif y == FY0 + 1:
                p = RIFLESSO_VUOTO + (205,)
            else:
                p = VUOTO + (205,)
            im.putpixel((x, y), p)
    return im


def liquido(b, livello):
    """Livello 0..20: riempie round(70 * livello / 20) pixel dell'interno; il resto è trasparente."""
    im = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    pieni = round(INTERNO * livello / 20)
    for i in range(pieni):
        x = FX0 + 1 + i
        base = misto(b["inizio"], b["fine"], i / (INTERNO - 1))
        for y in range(FY0 + 1, FY1):
            if y == FY0 + 1:
                p = chiaro(base, 0.38)                         # riflesso del vetro sul liquido
            elif y == FY1 - 1:
                p = scuro(base, 0.8)
            else:
                p = base
            if b["tacche"] and tacca(x):
                p = misto(p, b["cornice"]["basso"], 0.55)       # tacca visibile anche sul liquido
            im.putpixel((x, y), p + (255,))
    # Il gioco misura la larghezza di un carattere bitmap fino all'ultima colonna non trasparente: un pixel quasi
    # invisibile (alfa 1) nell'ultima colonna tiene ogni livello largo 82, anche il livello 0.
    im.putpixel((L - 1, A // 2), (0, 0, 0, 1))
    for x in range(FX0 + 3, min(FX0 + 1 + pieni, FX0 + 12)):    # lampo di luce vicino all'estremo sinistro
        r, g, bl, a = im.getpixel((x, FY0 + 1))
        t = max(0.0, 1 - abs(x - (FX0 + 7)) / 5)
        im.putpixel((x, FY0 + 1), chiaro((r, g, bl), 0.35 * t) + (a,))
    return im


def foglio(b):
    im = Image.new("RGBA", (L, A * LIVELLI), (0, 0, 0, 0))
    for livello in range(LIVELLI):
        im.paste(liquido(b, livello), (0, A * livello))
    return im


# Font mfr:hud: spazi (+1..+128, -1..-128) e barre. Altezza dalla riga della barra delle azioni (in alto a y = -72 dal
# fondo dello schermo): un carattere con ascent a ha il bordo alto a -72 + 7 - a. Fila dei cuori (-39): a = -26;
# fila sopra (-49), quella della sete: a = -16.
PRIMO = {"vita": 0xE100, "fame": 0xE120, "sete": 0xE140}
ASCENT = {"vita": -26, "fame": -26, "sete": -16}


def font():
    spazi = {chr(0xF821 + i): 1 << i for i in range(8)}
    spazi.update({chr(0xF801 + i): -(1 << i) for i in range(8)})
    prov = [{"type": "space", "advances": spazi}]
    for nome in BARRE:
        prov.append({"type": "bitmap", "file": f"mfr:font/hud/{nome}_vuota.png", "height": A,
                     "ascent": ASCENT[nome], "chars": [chr(PRIMO[nome])]})
        prov.append({"type": "bitmap", "file": f"mfr:font/hud/{nome}_liquido.png", "height": A,
                     "ascent": ASCENT[nome], "chars": [chr(PRIMO[nome] + 1 + i) for i in range(LIVELLI)]})
    return {"providers": prov}


# Cuori e cosce del gioco trasparenti: al loro posto le barre (#191). Restano i cuori della cavalcatura (vehicle_*).
CUORI = ([f"{t}{v}{b}" for t in ("", "poisoned_", "withered_", "absorbing_", "frozen_")
          for v in ("full", "half", "hardcore_full", "hardcore_half") for b in ("", "_blinking")]
         + ["container", "container_blinking", "container_hardcore", "container_hardcore_blinking"])
COSCE = [f"food_{v}{f}" for v in ("empty", "half", "full") for f in ("", "_hunger")]


if __name__ == "__main__":
    import json
    (QUI / "assets/mfr/font").mkdir(parents=True, exist_ok=True)
    with open(QUI / "assets/mfr/font/hud.json", "w", encoding="utf-8") as f:
        json.dump(font(), f, ensure_ascii=True, indent=2)
        f.write("\n")
    sprite = QUI / "assets/minecraft/textures/gui/sprites/hud"
    (sprite / "heart").mkdir(parents=True, exist_ok=True)
    vuoto = Image.new("RGBA", (9, 9), (0, 0, 0, 0))
    for n in CUORI:
        vuoto.save(sprite / "heart" / f"{n}.png", optimize=True)
    for n in COSCE:
        vuoto.save(sprite / f"{n}.png", optimize=True)
    print(f"font mfr:hud, {len(CUORI)} cuori e {len(COSCE)} cosce trasparenti")
    CARTELLA.mkdir(parents=True, exist_ok=True)
    for nome, b in BARRE.items():
        for suffisso, img in (("vuota", vuota(b)), ("liquido", foglio(b))):
            p = CARTELLA / f"{nome}_{suffisso}.png"
            img.save(p, optimize=True)
            print(f"{p.relative_to(QUI)}: {img.width}x{img.height}")
