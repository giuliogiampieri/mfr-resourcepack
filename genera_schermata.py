#!/usr/bin/env python3
"""Genera la schermata del Banco Magico (sfondo a tutta finestra e cifre del saldo) dal disegno del proprietario.

Uso: python3 genera_schermata.py   (poi python3 costruisci.py)

La schermata è una finestra tipo baule da 6 righe (176 x 222 pixel di interfaccia), disegnata a 4x (704 x 888)
per restare nitida con la scala dell'interfaccia 2-4. Il saldo è scritto con le cifre del font mfr:saldo.

Il client mette i caratteri dei font in pagine da 256 x 256 pixel (FontTexture.SIZE nel client 26.3): un
carattere più grande non entra e al suo posto compare il quadratino del carattere mancante. Per questo lo
sfondo è diviso in 4 x 4 tasselli da 176 x 224 pixel (44 x 56 di interfaccia), i caratteri da \uE020 a \uE02F
(riga r, colonna c -> \uE020 + 4r + c); il plugin li compone riga per riga (BancoMagico.titolo()).
Lo script scrive anche assets/mfr/font/banco.json (un provider per riga di tasselli, ognuno con il suo ascent).
Stampa le larghezze delle cifre da copiare in BancoMagico.java (LARGHEZZE_SALDO).
"""
import json
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 4                       # pixel di texture per pixel di interfaccia
W, H = 176, 222             # finestra tipo baule da 6 righe
QUI = os.path.dirname(os.path.abspath(__file__))
SORGENTE = os.path.join(QUI, "sorgenti", "banco-schermata.png")
FONT_TTF = "/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Bold.ttf"
CIFRE = "0123456789.:SALDOF"

ORO = (232, 168, 48)
ORO_CHIARO = (255, 224, 140)
ORO_SCURO = (122, 72, 14)
VIOLA = (46, 14, 34)
VIOLA_SCURO = (28, 8, 20)
CASELLA = (30, 12, 22)


def r(x0, y0, x1, y1):
    """Rettangolo in pixel di interfaccia -> texture (estremi inclusi in interfaccia, esclusi in texture)."""
    return [x0 * S, y0 * S, x1 * S - 1, y1 * S - 1]


def cornice(d, x0, y0, x1, y1, spessore=1, fondo=None):
    if fondo is not None:
        d.rectangle(r(x0, y0, x1, y1), fill=fondo)
    for i in range(spessore * S):
        c = ORO_CHIARO if i < S // 2 else (ORO if i < spessore * S - S // 2 else ORO_SCURO)
        d.rectangle([x0 * S + i, y0 * S + i, x1 * S - 1 - i, y1 * S - 1 - i], outline=c)


def casella(d, x, y, ricca=False):
    """Casella dell'interfaccia: oggetto in (x, y) 16x16, cornice da x-1 a x+17."""
    d.rectangle(r(x - 1, y - 1, x + 17, y + 17), fill=ORO if ricca else ORO_SCURO)
    d.rectangle(r(x - 1, y - 1, x + 17, y), fill=ORO_CHIARO if ricca else ORO)
    d.rectangle(r(x - 1, y - 1, x, y + 17), fill=ORO_CHIARO if ricca else ORO)
    d.rectangle(r(x, y, x + 16, y + 16), fill=CASELLA)
    d.rectangle(r(x, y, x + 16, y + 1), fill=(14, 5, 10))
    d.rectangle(r(x, y, x + 1, y + 16), fill=(14, 5, 10))


def sfondo():
    ref = Image.open(SORGENTE).convert("RGB")
    k = 704 / ref.width                               # stessa scala del disegno in orizzontale
    # Targa del saldo: si cancella la scritta d'esempio (il saldo vero lo scrive il plugin).
    ref = ref.copy()
    striscia = ref.crop((318, 455, 334, 527))         # tratto pulito fra monetine e scritta
    for x in range(236, 888, striscia.width):         # via anche le monetine: più spazio per il saldo
        ref.paste(striscia, (x, 455))
    # Parte alta del disegno: stemma, BANCO MAGICO, DEL FIDORO, targa del saldo (fino a y = 88 di interfaccia).
    alto_ref = int(88 * S / k)
    alto = ref.crop((0, 0, ref.width, alto_ref)).resize((W * S, 88 * S), Image.LANCZOS)

    img = Image.new("RGB", (W * S, H * S), VIOLA)
    d = ImageDraw.Draw(img)
    # Corpo: viola scuro con una trama leggera, cornice d'oro sottile ai lati e in fondo.
    for y in range(88 * S, H * S, 2):
        d.line([(0, y), (W * S, y)], fill=VIOLA_SCURO if (y // 2) % 3 == 0 else VIOLA)
    img.paste(alto, (0, 0))
    cornice(d, 0, 87, W, H, spessore=2)
    # Trave d'oro sotto la targa, che chiude le colonne del disegno.
    d.rectangle(r(0, 86, W, 88), fill=ORO)
    d.rectangle(r(0, 86, W, 87), fill=ORO_CHIARO)
    d.rectangle([0, 88 * S - S // 2, W * S - 1, 88 * S - 1], fill=ORO_SCURO)

    # Riga dei pulsanti (riga 4 della finestra): 1 5 10 20 | importo | 50 100 200 500.
    for c in range(9):
        casella(d, 8 + c * 18, 90, ricca=True)
    # Bilancia con gli allori del disegno, sotto i pulsanti.
    bil = ref.crop((205, 1088, 917, 1262))
    bh = 16 * S
    bil = bil.resize((int(bil.width * bh / bil.height), bh), Image.LANCZOS)
    img.paste(bil, ((W * S - bil.width) // 2, 109 * S))
    # Targhetta chiara dietro la scritta "Inventario" del gioco (grigia, illeggibile sul viola).
    cornice(d, 5, 126, 66, 138, spessore=1, fondo=(214, 190, 140))
    # Inventario del giocatore: 3 righe + barra rapida (finestra da 6 righe: y = 139 e 197).
    for rr in range(3):
        for c in range(9):
            casella(d, 8 + c * 18, 140 + rr * 18 - 1)
    for c in range(9):
        casella(d, 8 + c * 18, 197)
    return img


def cifre():
    cella_w, cella_h = 40, 32                         # altezza 8 di interfaccia
    font = ImageFont.truetype(FONT_TTF, 29)
    img = Image.new("RGBA", (cella_w * len(CIFRE), cella_h), (0, 0, 0, 0))
    larghezze = {}
    for i, ch in enumerate(CIFRE):
        cella = Image.new("RGBA", (cella_w, cella_h), (0, 0, 0, 0))
        maschera = Image.new("L", (cella_w, cella_h), 0)
        md = ImageDraw.Draw(maschera)
        x0, y0, x1, y1 = md.textbbox((0, 0), ch, font=font)
        cima = 6                                      # maiuscole da y=4 a y=26 circa
        md.text((1 - x0, cima - font.getbbox("S")[1]), ch, font=font, fill=255)
        ombra = maschera.filter(ImageFilter.MaxFilter(3))
        cella.paste((48, 14, 6, 255), (1, 2), ombra)
        sfum = Image.new("RGBA", (cella_w, cella_h))
        for y in range(cella_h):
            t = max(0.0, min(1.0, (y - 4) / 22))
            c = tuple(int(ORO_CHIARO[j] * (1 - t) + ORO[j] * t) for j in range(3)) + (255,)
            ImageDraw.Draw(sfum).line([(0, y), (cella_w, y)], fill=c)
        cella.paste(sfum, (0, 0), maschera)
        a = cella.getchannel("A")
        bb = a.getbbox()
        larghezze[ch] = bb[2] if bb else 0
        img.paste(cella, (i * cella_w, 0))
    return img, larghezze, cella_h


RIGHE, COLONNE = 4, 4
TASSELLO_W, TASSELLO_H = W * S // COLONNE, 224          # 176 x 224 pixel di texture, <= 256
PRIMO_TASSELLO = 0xE020
ASCENT_FINESTRA = 13                                    # con il titolo a y = 6, ascent 13 = bordo alto della finestra


def spostamenti():
    """Caratteri di spazio del font mfr:banco: \uF801.. = -1, -2, -4 ... -512; \uF821.. = +1, +2 ... +512."""
    adv = {}
    for i in range(10):
        adv[chr(0xF801 + i)] = -(1 << i)
        adv[chr(0xF821 + i)] = 1 << i
    return {"type": "space", "advances": adv}


def font_banco():
    providers = [spostamenti()]
    alto = TASSELLO_H // S                              # 56 pixel di interfaccia per riga di tasselli
    for riga in range(RIGHE):
        griglia = []
        for rr in range(RIGHE):
            if rr == riga:
                griglia.append("".join(chr(PRIMO_TASSELLO + riga * COLONNE + c) for c in range(COLONNE)))
            else:
                griglia.append("\u0000" * COLONNE)    # celle delle altre righe: saltate dal client
        providers.append({"type": "bitmap", "file": "mfr:font/banco_schermata.png", "height": alto,
                          "ascent": ASCENT_FINESTRA - riga * alto, "chars": griglia})
    return {"providers": providers}


def main():
    tex = os.path.join(QUI, "assets", "mfr", "textures", "font")
    os.makedirs(tex, exist_ok=True)
    # I font del client accettano solo immagini RGBA: in RGB il carattere non si carica.
    tela = Image.new("RGBA", (COLONNE * TASSELLO_W, RIGHE * TASSELLO_H), (0, 0, 0, 0))   # 704 x 896
    tela.paste(sfondo().convert("RGBA"), (0, 0))        # gli ultimi 8 pixel in fondo restano trasparenti
    tela.save(os.path.join(tex, "banco_schermata.png"), optimize=True)
    with open(os.path.join(QUI, "assets", "mfr", "font", "banco.json"), "w", encoding="utf-8") as f:
        json.dump(font_banco(), f, indent=2)
        f.write("\n")
    img, larghezze, cella_h = cifre()
    img.save(os.path.join(tex, "banco_saldo.png"), optimize=True)
    scala = 8 / cella_h
    anticipi = {ch: int(0.5 + w * scala) + 1 for ch, w in larghezze.items()}
    print("LARGHEZZE_SALDO:", json.dumps(anticipi, ensure_ascii=False))


if __name__ == "__main__":
    main()
