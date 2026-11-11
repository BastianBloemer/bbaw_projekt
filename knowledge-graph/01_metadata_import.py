#!/usr/bin/env python3
"""
01 - Metadaten aus der IIIF-Plattform übernehmen
------------------------------------------------
Kopiert die kuratierte Tabelle der IIIF-Plattform unverändert in den
Knowledge-Graph und benennt sie um:

    iiif-plattform/backend/data/metadata/curated/merged_df.csv
        -> knowledge-graph/data/metadata.csv

Die IIIF-Plattform bleibt die Quelle; Änderungen an den Metadaten passieren
dort (02_metadata_curate.ipynb). Nach jeder neuen Kuration dieses Skript
erneut ausführen.

Aufruf (aus dem Projekt-Root):
    .venv/bin/python knowledge-graph/01_metadata_import.py
"""

import shutil
from pathlib import Path

KG_DIR = Path(__file__).resolve().parent
QUELLE = KG_DIR.parent / "iiif-plattform" / "backend" / "data" / "metadata" / "curated" / "merged_df.csv"
ZIEL = KG_DIR / "data" / "metadata.csv"


def main():
    if not QUELLE.exists():
        raise SystemExit(f"Quelle nicht gefunden: {QUELLE}")
    ZIEL.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(QUELLE, ZIEL)
    zeilen = sum(1 for _ in ZIEL.open(encoding="utf-8-sig")) - 1
    print(f"{zeilen} Zeilen kopiert: {QUELLE.name} -> {ZIEL}")


if __name__ == "__main__":
    main()
