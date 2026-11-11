#!/usr/bin/env python3
"""
Korrigiert die heruntergeladenen IIIF-Manifeste, damit sie im Viewer laufen.

1. Kopiert alle Manifeste aus data/manifest/raw nach data/manifest/curated und
   ergänzt dabei in allen 'id'/'target'-URLs den fehlenden Pfadteil
   'digilib/' (digilib.bbaw.de/... -> digilib.bbaw.de/digilib/...).
2. Wandelt alle 'ImageService3'-Blöcke in IIIF-Image-API-v2-Services um
   (überschreibt die Dateien in data/manifest/curated).

ACHTUNG: Überschreibt data/manifest/curated komplett mit dem Stand aus raw.
Bereits angereicherte Ranges (03_manifest_enrich.py) gehen dabei verloren –
danach also immer 03 und 04 erneut ausführen.
"""

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
INPUT_DIR = DATA_DIR / "manifest" / "raw"
OUTPUT_DIR = DATA_DIR / "manifest" / "curated"

# Muster: trifft auf digilib.bbaw.de/ nur wenn danach NICHT schon digilib/ steht
PATTERN = re.compile(r"(https?://digilib\.bbaw\.de/)(?!digilib/)")


def patch_node(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("id", "target") and isinstance(value, str):
                node[key] = PATTERN.sub(r"\1digilib/", value)
            else:
                patch_node(value)
    elif isinstance(node, list):
        for item in node:
            patch_node(item)
    return node


def copy_and_patch_urls(input_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    for input_path in sorted(input_dir.glob("**/*.json")):
        data = json.loads(input_path.read_text(encoding="utf-8"))
        patch_node(data)

        # Unterordner-Struktur im Ausgabe-Ordner beibehalten
        output_path = output_dir / input_path.relative_to(input_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def migrate_iiif3_to_v2_service(data):
    """
    Durchsucht das JSON rekursiv nach 'ImageService3' Blöcken
    und konvertiert sie in das funktionierende IIIF v2 Format.
    """
    if isinstance(data, dict):
        # Falls es sich um einen v3 Service-Block handelt
        if data.get("type") == "ImageService3" and "id" in data:
            old_id = data["id"]
            # Entferne das /3/ aus der URL
            if "/IIIF/3/" in old_id:
                new_id = old_id.replace("/IIIF/3/", "/IIIF/")

                # Struktur auf v2 Syntax umbauen
                data.clear()
                data["@id"] = new_id
                data["@type"] = "iiif:ImageService2"
                data["profile"] = "http://iiif.io/api/image/2/level2.json"
                return

        # Falls ein 'service'-Array in einem Element liegt
        if "service" in data and isinstance(data["service"], list):
            for svc in data["service"]:
                if isinstance(svc, dict) and svc.get("type") == "ImageService3":
                    migrate_iiif3_to_v2_service(svc)

        # Rekursiv weiter durch alle Schlüssel des Dicts gehen
        for value in data.values():
            if isinstance(value, (dict, list)):
                migrate_iiif3_to_v2_service(value)

    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                migrate_iiif3_to_v2_service(item)


def process_manifest_folder(folder: Path):
    """
    Liest alle .json/.jsonld Dateien im Ordner, konvertiert sie und
    ÜBERSCHREIBT die bestehenden Dateien.
    """
    if not folder.exists():
        print(f"Fehler: Der Ordner '{folder}' existiert nicht.")
        return

    success_count = 0
    for file_path in folder.rglob("*"):
        if file_path.is_file() and file_path.suffix in [".json", ".jsonld"]:
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    manifest = json.load(f)

                migrate_iiif3_to_v2_service(manifest)

                with file_path.open("w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2, ensure_ascii=False)

                print(f"Erfolgreich überschrieben: {file_path.name}")
                success_count += 1

            except Exception as e:
                print(f"Fehler bei Datei {file_path.name}: {e}")

    print(f"\nFertig! {success_count} Manifest(e) im Ordner '{folder.resolve()}' wurden direkt überschrieben.")


def main():
    copy_and_patch_urls(INPUT_DIR, OUTPUT_DIR)
    process_manifest_folder(OUTPUT_DIR)


if __name__ == "__main__":
    main()
