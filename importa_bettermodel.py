#!/usr/bin/env python3
"""Importa nel pack i file di BetterModel che servono ai modelli indicati (es. il Goblin 3D).

BetterModel genera sul server il suo pacchetto (plugins/BetterModel/build.zip). Il pack del server lo sostituisce:
questo script ne copia in assets/bettermodel/ solo le parti usate dai modelli indicati, cioè le definizioni degli
oggetti "<modello>_<osso>.json" e tutto ciò a cui rimandano (modelli e texture). Restano fuori i modelli interni di
BetterModel per armature e giocatori, che il progetto non usa.

Uso: python3 importa_bettermodel.py <build.zip> <modello> [<modello> ...]
     poi python3 costruisci.py

I nomi interni di BetterModel (es. "c/a", "item/a") sono offuscati e dipendono dall'insieme dei modelli sul server:
ogni volta che si aggiunge o si cambia un modello va rigenerato build.zip sul server e rifatta l'importazione.
"""
import json
import pathlib
import re
import shutil
import sys
import zipfile

QUI = pathlib.Path(__file__).resolve().parent
DEST = QUI / "assets" / "bettermodel"
RIF = re.compile(r'"bettermodel:([a-z0-9_./-]+)"')


def importa(zip_path, modelli):
    z = zipfile.ZipFile(zip_path)
    nomi = set(z.namelist())
    radice = "assets/bettermodel/"
    da_fare = [n for n in nomi if n.startswith(radice + "items/")
               and any(pathlib.PurePosixPath(n).name.startswith(m + "_") for m in modelli) and n.endswith(".json")]
    for m in modelli:
        if not any(pathlib.PurePosixPath(n).name.startswith(m + "_") for n in da_fare):
            raise SystemExit(f"nessun oggetto per il modello {m} in {zip_path}")
    presi = set()
    while da_fare:
        n = da_fare.pop()
        if n in presi:
            continue
        presi.add(n)
        if not n.endswith(".json"):
            continue
        testo = z.read(n).decode("utf-8")
        json.loads(testo)  # deve essere JSON valido
        for r in RIF.findall(testo):
            candidati = [f"{radice}models/{r}.json", f"{radice}textures/{r}.png", f"{radice}textures/{r}.png.mcmeta"]
            trovati = [c for c in candidati if c in nomi]
            if not trovati:
                raise SystemExit(f"riferimento non trovato nel pacchetto: bettermodel:{r} (da {n})")
            da_fare.extend(trovati)
    if DEST.exists():
        shutil.rmtree(DEST)
    for n in sorted(presi):
        p = QUI / n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(z.read(n))
    tipi = {}
    for n in presi:
        k = n[len(radice):].split("/")[0]
        tipi[k] = tipi.get(k, 0) + 1
    print(f"importati {len(presi)} file in assets/bettermodel: "
          + ", ".join(f"{k} {v}" for k, v in sorted(tipi.items())))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    importa(sys.argv[1], sys.argv[2:])
