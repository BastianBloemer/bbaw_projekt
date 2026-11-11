#!/usr/bin/env python3
"""
Erzeugt das Abhandlungsregister für das Frontend (Suche, Register).

Liest alle Ranges ('structures') aus den angereicherten Manifesten und
schreibt sie als flache, nach Jahr/Autor/Titel sortierte Liste.

Eingabe:  data/manifest/curated/**/<Reihe>_<Band>.json
Ausgabe:  data/registers/register-abhandlungen.json
"""

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MANIFESTS_DIR = DATA_DIR / "manifest" / "curated"
OUTPUT_FILE = DATA_DIR / "registers" / "register-abhandlungen.json"


def get_canvas_id(item):
    """ID eines Canvas-Eintrags, egal ob String oder Dict."""
    if isinstance(item, dict):
        return item.get("id")
    return item


def main():
    entries = []

    for path in MANIFESTS_DIR.rglob("*.json"):
        if path.name == "collection.json":
            continue

        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)

        relative_to_manifests = path.relative_to(MANIFESTS_DIR).as_posix()
        # Relativ, da es kein "backend/static" gibt (nur "backend/data") -- muss
        # von frontend/html/*.html aus aufloesbar sein
        manifest_path = f"../../backend/data/manifest/curated/{relative_to_manifests}"

        # Kuerzel ohne Zahl/Bindestrich (z.B. "misc" statt "01-misc") -- reicht
        # als Zusatzinfo neben Autor/Jahr, ohne die Metadatenzeile zu ueberladen
        schriftenreihe = re.sub(r"^\d+-", "", path.relative_to(MANIFESTS_DIR).parts[0])

        # Band (z.B. "1745") aus dem Dateinamen "<Reihe>_<Band>.json" -- daraus,
        # falls moeglich, das Erscheinungsjahr ableiten (nicht bei buchweise statt
        # jahrweise gezaehlten Reihen wie 01-misc/04-phys, dort bleibt es leer)
        band = path.stem.split("_", 1)[1]
        jahr_match = re.match(r"(\d{4})", band)
        band_jahr = int(jahr_match.group(1)) if jahr_match else None

        for structure in manifest.get("structures", []):
            items = structure.get("items", [])

            # Start- und End-Canvas bestimmen
            start_canvas = get_canvas_id(items[0]) if items else None
            end_canvas = get_canvas_id(items[-1]) if items else None

            # Metadaten sicher auslesen ('de' bevorzugt, sonst erster verfuegbarer Wert)
            meta = {}
            for m in structure.get("metadata", []):
                label_list = m.get("label", {}).get("de") or list(m.get("label", {}).values())[0]
                value_list = m.get("value", {}).get("de") or list(m.get("value", {}).values())[0]

                if label_list and value_list:
                    meta[label_list[0]] = value_list[0]

            # Titel auslesen
            title_list = structure.get("label", {}).get("de") or list(structure.get("label", {}).values())[0]
            title = title_list[0] if title_list else ""

            author = meta.get("Autor", "")

            year = band_jahr
            if meta.get("Erscheinungsjahr", "").isdigit():
                year = int(meta["Erscheinungsjahr"])

            entries.append({
                "id": structure.get("id"),
                "title": title,
                "author": author,
                "place": meta.get("Ort", ""),
                "publisher": meta.get("Verlag", ""),
                "year": year,
                "anhang": meta.get("Abbildungen", ""),
                "textbeziehungen": meta.get("Textbeziehungen", ""),
                "schriftenreihe": schriftenreihe,
                "startCanvas": start_canvas,
                "endCanvas": end_canvas,
                "manifest": manifest_path,
                "search": f"{title} {author}".lower().strip(),
            })

    entries.sort(key=lambda x: (
        x["year"] or 9999,
        x["author"],
        x["title"],
    ))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"--> Fertig! {len(entries)} flache Abhandlungen gespeichert in '{OUTPUT_FILE}'.")


if __name__ == "__main__":
    main()
