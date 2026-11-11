#!/usr/bin/env python3
"""
Erzeugt die IIIF-Collections, über die der Viewer durch den Bestand navigiert.

- Pro Schriftenreihe eine Sub-Collection:
  data/manifest/curated/<Reihe>/collection.json (Label: Reihentitel + Zeitraum)
- Eine Gesamt-Collection über alle Reihen:
  data/manifest/curated/collection.json

Für die Reihe 'ak-gesch' (Einzelmonographien) werden die Labels der Bände aus
merged_df.csv gebildet ('Autor: Titel (Jahr)') statt aus dem Dateinamen.
"""

import json
import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MANIFESTS_DIR = DATA_DIR / "manifest" / "curated"
MERGED_DF_PATH = DATA_DIR / "metadata" / "curated" / "merged_df.csv"
# Relativ, da es kein "backend/static" gibt (nur "backend/data") -- muss von
# frontend/html/*.html aus aufloesbar sein, siehe mirador-app.js DEFAULT_COLLECTION
BASE_URL = "../../backend/data/manifest/curated"
OUTPUT_FILE = MANIFESTS_DIR / "collection.json"
EXCLUDE_FILENAMES = "collection.json"
# Reihe mit Einzelmonographien statt jahr-/bandweiser Zaehlung: die
# Bandbezeichnung im Dateinamen (z.B. "bart-1") taugt nicht als Label,
# daher wird es aus dem CSV (Spalten "Titel", "Autor", "Jahr") gezogen.
AK_GESCH_FOLDER = "ak-gesch"
SERIES_TITLES = {
    "01-misc": "Miscellanea Berolinensia ad incrementum scientiarum, ex scriptis Societati Regiae Scientiarum exhibitis edita",
    "02-hist": "Histoire de l'Académie Royale des Sciences et des Belles-Lettres de Berlin",
    "03-nouv": "Nouveaux Mémoires de l'Académie Royale des Sciences et Belles-Lettre",
    "04-phys": "Physikalische und medicinische Abhandlungen der Königlichen Academie der Wissenschaften zu Berlin",
    "05-mem":  "Mémoires de l'Académie Royale des Sciences et Belles-Lettres",
    "06-samml": "Sammlung der deutschen Abhandlungen, welche in der Königlichen Akademie der Wissenschaften zu Berlin vorgelesen worden",
    "07-abh": "Abhandlungen der Königlichen Preußischen Akademie der Wissenschaften zu Berlin",
    "08-verh": "Bericht über die zur Bekanntmachung geeigneten Verhandlungen der Königlich Preußischen Akademie der Wissenschaften zu Berlin",
    "09-mon": "Monatsberichte der Königlich Preußischen Akademie der Wissenschaften zu Berlin",
    "10-sitz": "Sitzungsberichte der Königlich Preußischen Akademie der Wissenschaften zu Berlin",
    "ak-gesch": "Monographien zur Geschichte der Akademie bis 1900",
}
# Erscheinungszeitraum je Reihe (von, bis) -- fuer die Anzeige auf
# Schriftenreihen-Ebene im Viewer. Fest hinterlegt statt aus den
# Banddateinamen abgeleitet, weil nicht jede Reihe jahrweise gezaehlte
# Baende hat (01-misc/04-phys sind fortlaufend nummeriert, keine Jahre).
SERIES_YEARS = {
    "01-misc": (1710, 1744),
    "02-hist": (1745, 1769),
    "03-nouv": (1770, 1786),
    "04-phys": (1781, 1786),
    "05-mem":  (1786, 1804),
    "06-samml": (1788, 1803),
    "07-abh":  (1804, 1900),
    "08-verh": (1836, 1855),
    "09-mon":  (1856, 1881),
    "10-sitz": (1882, 1900),
    "ak-gesch": (1711, 1950),
}


def load_ak_gesch_meta(merged_df_path: Path) -> dict[str, dict]:
    """Metadaten der Reihe 'ak-gesch' aus 'merged_df.csv' laden, zugeordnet
    ueber die Bandbezeichnung (Spalte 'Band'). Titel, Autor und Jahr
    ersetzen bzw. ergaenzen die nichtssagende Bandbezeichnung ('bart-1'
    o.ae.) als Manifest-Label."""
    if not merged_df_path.exists():
        print(f"  ! merged_df.csv nicht gefunden ({merged_df_path.resolve()}) -- "
              f"{AK_GESCH_FOLDER}-Labels bleiben Bandbezeichnungen")
        return {}
    df = pd.read_csv(merged_df_path, dtype=str)
    df = df[df["Schriftenreihe"] == AK_GESCH_FOLDER]
    meta: dict[str, dict] = {}
    for _, row in df.iterrows():
        if pd.isna(row["Band"]) or pd.isna(row["Titel"]):
            continue
        meta[str(row["Band"]).strip()] = {
            "titel": str(row["Titel"]).strip(),
            "autor": str(row["Autor"]).strip() if pd.notna(row["Autor"]) else "",
            "jahr": str(row["Jahr"]).strip() if pd.notna(row["Jahr"]) else "",
        }
    return meta


def build_ak_gesch_label(meta: dict) -> str:
    """Label fuer einen 'ak-gesch'-Band: 'Autor: Titel (Jahr)'. Autor und
    Jahr werden nur ergaenzt, wenn im CSV vorhanden."""
    label = meta["titel"]
    if meta.get("autor"):
        label = f"{meta['autor']}: {label}"
    if meta.get("jahr"):
        label = f"{label} ({meta['jahr']})"
    return label


def find_manifests(root: Path):
    all_json_files = root.rglob("*.json")
    manifests = [
        p
        for p in all_json_files
        if p.name not in EXCLUDE_FILENAMES and p.parent != root
    ]
    return sorted(manifests)


def group_by_series(manifests, root: Path):
    groups: dict[str, list[Path]] = {}
    for m in manifests:
        relative = m.relative_to(root)
        series_folder = relative.parts[0]
        groups.setdefault(series_folder, []).append(m)
    # Innerhalb jeder Serie alphabetisch/numerisch nach Dateiname sortieren
    for series_folder in groups:
        groups[series_folder].sort(key=lambda p: p.name)
    return groups


def format_band_label(band: str) -> str:
    """Baende, die zwei zusammengezogene Jahreszahlen ohne Trennzeichen
    tragen (z.B. '18041811', aus der Quelle uebernommen), werden fuer die
    Anzeige mit einem Bindestrich versehen ('1804-1811'). Normale Baende
    (ein Jahr oder fortlaufende Nummerierung wie bei 01-misc/04-phys)
    bleiben unveraendert."""
    m = re.fullmatch(r"(\d{4})(\d{4})", band)
    return f"{m.group(1)}-{m.group(2)}" if m else band


def build_manifest_item(manifest_path: Path, root: Path, base_url: str, meta_by_band=None):
    """Erzeugt den Collection-Eintrag für einen einzelnen Band.
    Label = nur die Bandbezeichnung nach dem ersten Unterstrich
    (z.B. '1745' statt '02-hist_1745'). Ausnahme: Ist ein Metadaten-Lookup
    uebergeben (Reihe 'ak-gesch'), wird das Label aus Autor, Titel und
    Jahr des CSV zusammengesetzt."""
    relative_path = manifest_path.relative_to(root)
    manifest_url = f"{base_url}/{relative_path.as_posix()}"
    band = manifest_path.stem.split("_", 1)[1]

    if meta_by_band and band in meta_by_band:
        label = build_ak_gesch_label(meta_by_band[band])
    else:
        label = format_band_label(band)

    return {
        "id": manifest_url,
        "type": "Manifest",
        "label": {"de": [label]},
    }


def build_series_collection(series_folder: str, manifest_paths, root: Path, base_url: str, meta_by_band=None):
    """Erzeugt die Sub-Collection für eine Schriftenreihe und speichert
    sie als collection.json im jeweiligen Ordner. Das Label enthält den
    Erscheinungszeitraum der Reihe (von-bis)."""
    series_dir = root / series_folder
    series_output_file = series_dir / "collection.json"
    series_url = f"{base_url}/{series_folder}/collection.json"
    series_title = SERIES_TITLES.get(series_folder, series_folder)

    if series_folder in SERIES_YEARS:
        von, bis = SERIES_YEARS[series_folder]
        series_label = f"{series_title} ({von}–{bis})"
    else:
        series_label = series_title

    series_collection = {
        "@context": "http://iiif.io/api/presentation/3/context.json",
        "id": series_url,
        "type": "Collection",
        "label": {"de": [series_label]},
        "items": [
            build_manifest_item(m, root, base_url, meta_by_band) for m in manifest_paths
        ],
    }

    series_output_file.write_text(
        json.dumps(series_collection, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  -> Sub-Collection gespeichert unter: {series_output_file.resolve()}")

    return {
        "id": series_url,
        "type": "Collection",
        "label": {"de": [series_label]},
    }


def main():
    if not MANIFESTS_DIR.exists():
        print(f"Verzeichnis nicht gefunden: {MANIFESTS_DIR.resolve()}")
        print("Bitte MANIFESTS_DIR im Skript anpassen.")
        return

    manifests = find_manifests(MANIFESTS_DIR)
    print(f"{len(manifests)} Manifest(e) gefunden unter {MANIFESTS_DIR}/")

    if not manifests:
        print("Keine Manifest-Dateien gefunden - Collection wird trotzdem")
        print("mit leerer items-Liste erzeugt.")

    groups = group_by_series(manifests, MANIFESTS_DIR)
    print(f"{len(groups)} Schriftenreihe(n) erkannt: {', '.join(sorted(groups))}")

    ak_gesch_meta = load_ak_gesch_meta(MERGED_DF_PATH)
    if ak_gesch_meta:
        print(f"{len(ak_gesch_meta)} {AK_GESCH_FOLDER}-Titel aus dem CSV geladen")

    top_level_items = []
    for series_folder in sorted(groups):
        print(f"Verarbeite Schriftenreihe: {series_folder}")
        meta_by_band = ak_gesch_meta if series_folder == AK_GESCH_FOLDER else None
        top_level_items.append(
            build_series_collection(series_folder, groups[series_folder], MANIFESTS_DIR, BASE_URL, meta_by_band)
        )

    collection = {
        "@context": "http://iiif.io/api/presentation/3/context.json",
        "id": f"{BASE_URL}/collection.json",
        "type": "Collection",
        "label": {"de": ["Digitalisierte Akademieschriften der BBAW"]},
        "items": top_level_items,
    }

    OUTPUT_FILE.write_text(
        json.dumps(collection, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Gesamt-Collection gespeichert unter: {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()
