#!/usr/bin/env python3
"""Costruisce mfr-resourcepack.zip in modo riproducibile (stesso contenuto → stessa impronta SHA-1).

Uso: python3 costruisci.py   → scrive mfr-resourcepack.zip e stampa la SHA-1 da mettere nel plugin.
"""
import hashlib
import pathlib
import zipfile

QUI = pathlib.Path(__file__).resolve().parent
USCITA = QUI / "mfr-resourcepack.zip"
FILE = [QUI / "pack.mcmeta"] + sorted(p for p in (QUI / "assets").rglob("*") if p.is_file())

with zipfile.ZipFile(USCITA, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p in FILE:
        info = zipfile.ZipInfo(p.relative_to(QUI).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, p.read_bytes())

sha1 = hashlib.sha1(USCITA.read_bytes()).hexdigest()
print(f"{USCITA.name}: {USCITA.stat().st_size} byte, sha1 {sha1}")
