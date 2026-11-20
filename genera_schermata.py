#!/usr/bin/env python3
"""Genera le schermate del Banco Magico (banco tipo baule, "Importo a scelta" sull'incudine, cifre del saldo) dal disegno del proprietario.

Uso: python3 genera_schermata.py   (poi python3 costruisci.py)

La schermata è una finestra tipo baule da 5 righe (176 x 204 pixel di interfaccia) con l'arco del disegno che
sporge di 33 pixel sopra la finestra; tutto è disegnato a 4x (704 x 948) per restare nitido con la scala 2-4. Il saldo è scritto con le cifre del font mfr:saldo.

Il client mette i caratteri dei font in pagine da 256 x 256 pixel (FontTexture.SIZE nel client 26.3): un
carattere più grande non entra e al suo posto compare il quadratino del carattere mancante. Per questo lo
sfondo è diviso in 4 x 4 tasselli da 176 x 240 pixel (44 x 60 di interfaccia), i caratteri da \uE020 a \uE02F
(riga r, colonna c -> \uE020 + 4r + c); il plugin li compone riga per riga (BancoMagico.titolo()).
Lo script scrive anche assets/mfr/font/banco.json (un provider per riga di tasselli, ognuno con il suo ascent).
Stampa le larghezze delle cifre da copiare in BancoMagico.java (LARGHEZZE_SALDO).
"""
import json
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 4                       # pixel di texture per pixel di interfaccia
W, H = 176, 204             # finestra tipo baule da 5 righe
SOPRA = 33                  # l'arco del disegno sporge sopra la finestra (lì gli angoli sono trasparenti)
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
    """Sfondo alto SOPRA + H pixel di interfaccia: l'arco sopra la finestra, poi la finestra da 5 righe.
    Sopra la finestra il nero intorno all'arco diventa trasparente (si vede il mondo sfocato); dentro la finestra
    tutto è coperto, perché dietro c'è la finestra grigia del baule."""
    ref = Image.open(SORGENTE).convert("RGB")
    k = 704 / ref.width                               # stessa scala del disegno in orizzontale
    # Targa del saldo: si cancella la scritta d'esempio (il saldo vero lo scrive il plugin).
    ref = ref.copy()
    striscia = ref.crop((318, 455, 334, 527))         # tratto pulito fra monetine e scritta
    for x in range(236, 888, striscia.width):         # via anche le monetine: più spazio per il saldo
        ref.paste(striscia, (x, 455))
    # Parte alta del disegno: arco, stemma, BANCO MAGICO, DEL FIDORO, targa del saldo (88 pixel di interfaccia).
    alto_ref = int(88 * S / k)
    alto = ref.crop((0, 0, ref.width, alto_ref)).resize((W * S, 88 * S), Image.LANCZOS)
    alto = trasparente_fuori(alto.convert("RGBA"))
    fine_stemma = 88 - SOPRA                          # y della finestra dove finisce la parte alta (55)

    img = Image.new("RGBA", (W * S, (SOPRA + H) * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    o = lambda x0, y0, x1, y1: r(x0, y0 + SOPRA, x1, y1 + SOPRA)   # coordinate della finestra -> immagine
    # Corpo della finestra (tutta, anche dietro lo stemma): viola scuro con una trama leggera.
    d.rectangle([0, SOPRA * S, W * S - 1, (SOPRA + H) * S - 1], fill=VIOLA + (255,))
    for y in range(SOPRA * S, (SOPRA + H) * S, 2):
        d.line([(0, y), (W * S, y)], fill=(VIOLA_SCURO if (y // 2) % 3 == 0 else VIOLA) + (255,))
    img.alpha_composite(alto, (0, 0))
    d = ImageDraw.Draw(img)
    cornice_o(d, 0, fine_stemma - 1, W, H, spessore=2)
    # Trave d'oro sotto la targa, che chiude le colonne del disegno.
    d.rectangle(o(0, fine_stemma - 2, W, fine_stemma), fill=ORO)
    d.rectangle(o(0, fine_stemma - 2, W, fine_stemma - 1), fill=ORO_CHIARO)
    d.rectangle([0, (SOPRA + fine_stemma) * S - S // 2, W * S - 1, (SOPRA + fine_stemma) * S - 1], fill=ORO_SCURO)
    # Bilancia con gli allori del disegno, fra la trave e i pulsanti.
    bil = ref.crop((205, 1088, 917, 1262))
    bh = 16 * S
    bil = bil.resize((int(bil.width * bh / bil.height), bh), Image.LANCZOS)
    img.paste(bil, ((W * S - bil.width) // 2, (SOPRA + 64) * S))
    # Riga dei pulsanti (riga 4 della finestra, caselle 36-44): 1 5 10 20 | importo | 50 100 200 500.
    for c in range(9):
        casella(d, 8 + c * 18, SOPRA + 90, ricca=True)
    # Targhetta chiara dietro la scritta "Inventario" del gioco (grigia, illeggibile sul viola): y = H - 94.
    cornice_o(d, 5, H - 96, 66, H - 84, spessore=1, fondo=(214, 190, 140))
    # Inventario del giocatore: 3 righe + barra rapida (finestra da 5 righe: y = 121 e 179).
    for rr in range(3):
        for c in range(9):
            casella(d, 8 + c * 18, SOPRA + 121 + rr * 18)
    for c in range(9):
        casella(d, 8 + c * 18, SOPRA + 179)
    return img


def cornice_o(d, x0, y0, x1, y1, **k):
    cornice(d, x0, y0 + SOPRA, x1, y1 + SOPRA, **k)


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
TASSELLO_W, TASSELLO_H = W * S // COLONNE, 240          # 176 x 240 pixel di texture, <= 256
PRIMO_TASSELLO = 0xE020
ASCENT_FINESTRA = 13 + SOPRA                            # titolo a y = 6: ascent 13 = bordo alto, + SOPRA per l'arco
SALDO_ASCENT = -59 + 33                                 # cifre del saldo nella targa (alla y della finestra 39..47)


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


def trasparente_fuori(img, soglia=40, colore=(0, 0, 0, 0)):
    """Il nero intorno al disegno (angoli sopra l'arco) diventa trasparente, o del colore dato: si parte dal bordo
    alto e dai lati dell'immagine e si allarga a tutti i pixel quasi neri collegati. Il nero dentro il disegno resta."""
    w, h = img.size
    px = img.load()
    scuro = lambda x, y: px[x, y][3] > 0 and sum(px[x, y][:3]) < soglia
    coda = [(x, 0) for x in range(w)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    visti = set()
    while coda:
        x, y = coda.pop()
        if (x, y) in visti or not (0 <= x < w and 0 <= y < h) or not scuro(x, y):
            continue
        visti.add((x, y))
        px[x, y] = colore
        coda += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return img


def font_finestra():
    providers = [spostamenti()]
    providers[0]["advances"][" "] = 3
    alto = STEMMA_ALTO // S                             # 44 pixel di interfaccia per riga
    for riga in range(STEMMA_RIGHE):
        griglia = []
        for rr in range(STEMMA_RIGHE):
            if rr == riga:
                griglia.append("".join(chr(PRIMO_STEMMA + riga * COLONNE + c) for c in range(COLONNE)))
            else:
                griglia.append("\u0000" * COLONNE)
        providers.append({"type": "bitmap", "file": "mfr:font/banco_stemma.png", "height": alto,
                          "ascent": ASCENT_RIGA - riga * alto, "chars": griglia})
    providers.append({"type": "bitmap", "file": "mfr:font/banco_saldo.png", "height": 8,
                      "ascent": SALDO_FINESTRA_ASCENT, "chars": [CIFRE]})
    return {"providers": providers}


# --- "Importo a scelta": schermata dell'incudine (176 x 166) con lo sfondo disegnato ---
# Il campo di testo dell'incudine è disegnato PRIMA del titolo: lo sfondo ha un buco trasparente sopra il campo
# (x 60-168, y 21-35), dove si vedono il campo dell'incudine e la cifra scritta. Il saldo va nella targa in alto
# (font mfr:incudine). La casella 0 (segnaposto "Cancella") e quella del risultato hanno la cornice.
INC_W, INC_H, INC_SOPRA = 176, 166, 0                   # niente stemma sopra la finestra (richiesta del 20/11)
INC_TASSELLO_H = 168                                    # 4 righe da 42 pixel di interfaccia: tutte con parti opache
PRIMO_INCUDINE = 0xE040
INC_SALDO_ASCENT = 7                                    # cifre alte 8 a y = 6..14, al centro della targa
BUCO = (60, 21, 168, 35)                                # dentro lo sprite del campo (59, 20, 110 x 16)


def disegno_alto():
    """Parte alta del disegno (88 pixel di interfaccia) senza la scritta d'esempio, nero esterno trasparente."""
    ref = Image.open(SORGENTE).convert("RGB").copy()
    striscia = ref.crop((318, 455, 334, 527))
    for x in range(236, 888, striscia.width):
        ref.paste(striscia, (x, 455))
    alto_ref = int(88 * S * ref.width / (W * S))
    alto = ref.crop((0, 0, ref.width, alto_ref)).resize((W * S, 88 * S), Image.LANCZOS)
    return ref, trasparente_fuori(alto.convert("RGBA"))


def scritta(img, testo, cx, y, alto=8):
    """Scritta dorata con ombra scura, maiuscole alte {alto} pixel di interfaccia, centrata in cx (interfaccia)."""
    font = ImageFont.truetype(FONT_TTF, int(alto * S * 1.36))
    maschera = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(maschera)
    x0, y0, x1, y1 = md.textbbox((0, 0), testo, font=font)
    cima = font.getbbox("I")[1]
    md.text((cx * S - (x1 - x0) / 2 - x0, y * S - cima), testo, font=font, fill=255)
    ombra = maschera.filter(ImageFilter.MaxFilter(3))
    img.paste((48, 14, 6, 255), (S // 2, S // 2), ombra)
    sfum = Image.new("RGBA", img.size)
    sd = ImageDraw.Draw(sfum)
    for yy in range(y * S, (y + alto) * S + 1):
        t = max(0.0, min(1.0, (yy - y * S) / (alto * S)))
        sd.line([(0, yy), (img.width, yy)], fill=tuple(int(ORO_CHIARO[j] * (1 - t) + ORO[j] * t) for j in range(3)) + (255,))
    img.paste(sfum, (0, 0), maschera)


def incudine():
    ref, alto = disegno_alto()
    img = Image.new("RGBA", (INC_W * S, (INC_SOPRA + INC_H) * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    O = INC_SOPRA
    # Corpo della finestra.
    d.rectangle([0, O * S, INC_W * S - 1, (O + INC_H) * S - 1], fill=VIOLA + (255,))
    for y in range(O * S, (O + INC_H) * S, 2):
        d.line([(0, y), (INC_W * S, y)], fill=(VIOLA_SCURO if (y // 2) % 3 == 0 else VIOLA) + (255,))
    cornice(d, 0, O, INC_W, O + INC_H, spessore=2)
    # Targa del saldo in alto nella finestra (il saldo lo scrive il plugin).
    targa = alto.crop((29 * S, 66 * S, 147 * S, 88 * S))
    targa = targa.resize((round(targa.width * 18 / 22), 18 * S), Image.LANCZOS)
    img.alpha_composite(targa, ((INC_W * S - targa.width) // 2, (O + 1) * S))
    # Campo dell'importo: scritta a sinistra, cornice d'oro, buco trasparente sul campo dell'incudine.
    scritta(img, "IMPORTO", 31, O + 25, alto=6)
    d = ImageDraw.Draw(img)
    cornice(d, BUCO[0] - 2, O + BUCO[1] - 2, BUCO[2] + 2, O + BUCO[3] + 2, spessore=1, fondo=(10, 3, 8))
    d.rectangle(r(BUCO[0], O + BUCO[1], BUCO[2], O + BUCO[3]), fill=(0, 0, 0, 0))
    # Riga delle caselle: moneta (casella 0), RITIRA -> risultato (casella 2). La casella 1 resta senza cornice.
    casella(d, 27, O + 47)
    scritta(img, "RITIRA", 100, O + 50, alto=7)
    d = ImageDraw.Draw(img)
    d.polygon([(123 * S, (O + 51) * S), (129 * S, (O + 55) * S), (123 * S, (O + 59) * S)], fill=ORO)
    cornice(d, 131, O + 44, 153, O + 66, spessore=1)
    casella(d, 134, O + 47, ricca=True)
    # Targhetta per la scritta "Inventario" (y = 72) e inventario del giocatore (y = 84 e 142).
    cornice(d, 5, O + 70, 66, O + 82, spessore=1, fondo=(214, 190, 140))
    for rr in range(3):
        for c in range(9):
            casella(d, 8 + c * 18, O + 84 + rr * 18)
    for c in range(9):
        casella(d, 8 + c * 18, O + 142)
    return img


def font_incudine():
    providers = [spostamenti()]
    providers[0]["advances"][" "] = 3
    alto = INC_TASSELLO_H // S                          # 64
    for riga in range(RIGHE):
        griglia = []
        for rr in range(RIGHE):
            if rr == riga:
                griglia.append("".join(chr(PRIMO_INCUDINE + riga * COLONNE + c) for c in range(COLONNE)))
            else:
                griglia.append("\u0000" * COLONNE)
        providers.append({"type": "bitmap", "file": "mfr:font/banco_incudine.png", "height": alto,
                          "ascent": 13 + INC_SOPRA - riga * alto, "chars": griglia})
    providers.append({"type": "bitmap", "file": "mfr:font/banco_saldo.png", "height": 8,
                      "ascent": INC_SALDO_ASCENT, "chars": [CIFRE]})
    return {"providers": providers}


def main():
    tex = os.path.join(QUI, "assets", "mfr", "textures", "font")
    os.makedirs(tex, exist_ok=True)
    # I font del client accettano solo immagini RGBA: in RGB il carattere non si carica.
    tela = Image.new("RGBA", (COLONNE * TASSELLO_W, RIGHE * TASSELLO_H), (0, 0, 0, 0))   # 704 x 960
    tela.paste(sfondo(), (0, 0))                        # in fondo restano 12 pixel trasparenti
    tela.save(os.path.join(tex, "banco_schermata.png"), optimize=True)
    with open(os.path.join(QUI, "assets", "mfr", "font", "banco.json"), "w", encoding="utf-8") as f:
        json.dump(font_banco(), f, indent=2)
        f.write("\n")
    tela = Image.new("RGBA", (COLONNE * TASSELLO_W, RIGHE * INC_TASSELLO_H), (0, 0, 0, 0))   # 704 x 1024
    tela.paste(incudine(), (0, 0))
    tela.save(os.path.join(tex, "banco_incudine.png"), optimize=True)
    with open(os.path.join(QUI, "assets", "mfr", "font", "incudine.json"), "w", encoding="utf-8") as f:
        json.dump(font_incudine(), f, indent=2)
        f.write("\n")
    with open(os.path.join(QUI, "assets", "mfr", "font", "saldo.json"), "w", encoding="utf-8") as f:
        json.dump({"providers": [{"type": "space", "advances": {" ": 3}},
                                 {"type": "bitmap", "file": "mfr:font/banco_saldo.png", "height": 8,
                                  "ascent": SALDO_ASCENT, "chars": [CIFRE]}]}, f, indent=2)
        f.write("\n")
    img, larghezze, cella_h = cifre()
    img.save(os.path.join(tex, "banco_saldo.png"), optimize=True)
    scala = 8 / cella_h
    anticipi = {ch: int(0.5 + w * scala) + 1 for ch, w in larghezze.items()}
    print("LARGHEZZE_SALDO:", json.dumps(anticipi, ensure_ascii=False))


if __name__ == "__main__":
    main()
