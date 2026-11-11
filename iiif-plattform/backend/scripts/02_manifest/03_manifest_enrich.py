#!/usr/bin/env python3
"""
Reichert die korrigierten IIIF-Manifeste mit den kuratierten Metadaten an.

Für jede Abhandlung in merged_df.csv wird im Manifest ihres Bandes eine
IIIF-'Range' (Eintrag im Inhaltsverzeichnis des Viewers) angelegt – mit Titel,
Seitenangaben und Metadaten (Autor, Erscheinungsjahr, Abbildungen,
Textbeziehungen als klickbare Viewer-Links).

Eingabe:  data/metadata/curated/merged_df.csv, data/manifest/curated/**
Ausgabe:  überschreibt 'structures' in data/manifest/curated/<Reihe>/<Reihe>_<Band>.json

Idempotent: 'structures' wird bei jedem Lauf komplett neu geschrieben. Nach
einer Änderung an den Metadaten reicht es daher, dieses Skript erneut
auszuführen (Download und Korrektur der Manifeste sind nicht nötig).
"""

import html
import json
import re
from pathlib import Path
from urllib.parse import quote

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MERGED_DF_PATH = DATA_DIR / "metadata" / "curated" / "merged_df.csv"
MANIFESTS_ROOT = DATA_DIR / "manifest" / "curated"

# Pfad-Praefix, unter dem die Manifeste vom Frontend aus (frontend/html/*.html)
# erreichbar sind -- relativ, da es kein "backend/static" gibt (nur
# "backend/data"); siehe frontend/js/register-personen.js, suche.js:
# PATH_* + book["manifest"]
VIEWER_MANIFEST_PREFIX = "../../backend/data/manifest/curated"


# ---------------------------------------------------------------------------
# Metadaten laden
#
# merged_df.csv (Ergebnis von 02_metadata_curate.ipynb) enthaelt alle
# Baende/Reihen inklusive der aus Anmerkungen/Antworten neu angelegten Zeilen
# ("NEU-*"-IDs) sowie die Spalte `Textbeziehungen` (intertextuelle Bezuege als
# "Typ: ID"-Paare, getrennt mit " | ").
# ---------------------------------------------------------------------------

def load_metadata():
    df = pd.read_csv(MERGED_DF_PATH, dtype=str)
    df["pn"] = pd.to_numeric(df["Link"].str.extract(r"pn=(\d+)")[0], errors="coerce")
    print(f"{len(df)} Zeilen geladen, {df['Textbeziehungen'].notna().sum()} mit Textbeziehungen")
    return df


# Schneller Zugriff auf eine beliebige Zeile ueber ihre ID (fuer die Aufloesung
# der Textbeziehungen-Ziele, die in jedem beliebigen Band liegen koennen).
# Wird in main() gesetzt.
df_by_id = None


# ---------------------------------------------------------------------------
# Hilfsfunktionen: Manifest-/Canvas-IDs und Viewer-Links
#
# Die Manifest- und Canvas-IDs folgen im gesamten Bestand demselben Schema
# (`silo10!Bibliothek.tiff!{Schriftenreihe}!{Band}!tif`, Canvas `.../canvas/p{N}`
# mit N = Bildnummer aus `Link` bzw. `pn=`). Das wurde vorab gegen alle 245
# Manifeste geprueft (keine Abweichung) und erlaubt es, den Link zu einer
# Zielzeile zu bauen, ohne deren Manifest-Datei oeffnen zu muessen.
#
# Der Viewer-Link folgt demselben Muster wie an anderer Stelle im Frontend
# (`register-personen.js`, `suche.js`): `viewer.html?manifest=...&canvas=...`.
# ---------------------------------------------------------------------------

def manifest_base_id(schriftenreihe, band):
    return (
        f"https://digilib.bbaw.de/digilib/Manifester/IIIF/3/"
        f"silo10!Bibliothek.tiff!{schriftenreihe}!{band}!tif"
    )


def canvas_uri(schriftenreihe, band, pn):
    return f"{manifest_base_id(schriftenreihe, band)}/canvas/p{int(pn)}"


def viewer_link(schriftenreihe, band, pn, text, escape=True):
    manifest_pfad = f"{VIEWER_MANIFEST_PREFIX}/{schriftenreihe}/{schriftenreihe}_{band}.json"
    href = (
        f"viewer.html?manifest={manifest_pfad}"
        f"&canvas={quote(canvas_uri(schriftenreihe, band, pn), safe='')}"
    )
    inhalt = html.escape(text) if escape else text
    return f'<a href="{href}" target="_blank" rel="noopener">{inhalt}</a>'


# ---------------------------------------------------------------------------
# Textbeziehungen zu klickbaren Links aufloesen
#
# `Textbeziehungen` enthaelt z.B. "Fortsetzung: 094917590 | Vgl: 094928...".
# Jede Ziel-ID wird ueber `df_by_id` aufgeloest: existiert eine gueltige
# Seitenzahl (`pn`), wird ein klickbarer Link mit Titel gebaut (IIIF erlaubt
# ein eingeschraenktes HTML-Subset -- inkl. `<a>` -- in Label-/Metadata-Werten;
# Mirador rendert das, siehe `mirador-config.js` -> `theme.components.IIIFHtmlContent`).
# Ohne aufloesbare Seitenzahl (z.B. bei den NEU-Zeilen ohne Link) bleibt es
# reiner Text, damit die Information nicht verloren geht.
# ---------------------------------------------------------------------------

def beziehungen_html(wert):
    if pd.isna(wert):
        return None

    # Typ-Span steckt INNERHALB des Links (bzw. direkt im Text ohne Link),
    # nicht daneben -- damit z.B. der Hover-Effekt des Links (Farbe etc.)
    # auch den Typ mit erfasst und beides als eine zusammengehoerige Einheit
    # wirkt.
    teile = []
    for eintrag in wert.split(" | "):
        typ, ziel_id = eintrag.split(": ", 1)
        typ, ziel_id = typ.strip(), ziel_id.strip()
        typ_span = f' <span class="beziehung-typ">({html.escape(typ)})</span>'

        ziel = df_by_id.loc[ziel_id] if ziel_id in df_by_id.index else None
        if ziel is not None and pd.notna(ziel["pn"]):
            inhalt = html.escape(ziel["Titel"]) + typ_span
            wert_html = viewer_link(ziel["Schriftenreihe"], ziel["Band"], ziel["pn"], inhalt, escape=False)
        else:
            titel = ziel["Titel"] if ziel is not None else ziel_id
            wert_html = html.escape(str(titel)) + typ_span

        teile.append(f'<span class="beziehung-wert">{wert_html}</span>')

    return "<br>".join(teile)


# ---------------------------------------------------------------------------
# Ranges bauen
#
# Bildstartseite aus `Link`/`pn=`, Seitenumfang aus Startseite/Endseite,
# Fallback auf die naechste Zeile, wenn keine gueltige Seitenzahl vorliegt.
# Zusaetzlich werden `Textbeziehungen` (und `Abbilder`) als Metadata in jede
# Range geschrieben.
# ---------------------------------------------------------------------------

def extract_pn(link):
    if pd.isna(link):
        return None
    m = re.search(r"pn=(\d+)", str(link))
    return int(m.group(1)) if m else None


def baue_metadata(row):
    metadata = []

    if pd.notna(row.get("Autor")):
        metadata.append({"label": {"de": ["Autor"]}, "value": {"de": [str(row["Autor"]).strip()]}})

    # Jahr kommt aus dem RIS-Feld PY (per Werk, nicht aus dem Band abgeleitet --
    # praeziser, und bei buchweise statt jahrweise gezaehlten Reihen wie
    # 01-misc/04-phys die einzige Quelle fuer ein Jahr ueberhaupt)
    jahr = row.get("Jahr")
    if pd.notna(jahr):
        try:
            jahr_str = str(int(float(jahr)))
        except (ValueError, TypeError):
            jahr_str = None
        if jahr_str:
            metadata.append({"label": {"de": ["Erscheinungsjahr"]}, "value": {"de": [jahr_str]}})

    if pd.notna(row.get("Abbilder")):
        metadata.append({"label": {"de": ["Abbildungen"]}, "value": {"de": [str(row["Abbilder"]).strip()]}})

    beziehungen = beziehungen_html(row.get("Textbeziehungen"))
    if beziehungen:
        metadata.append({"label": {"de": ["Textbeziehungen"]}, "value": {"de": [beziehungen]}})

    return metadata


def enrich_manifest(manifest_path, df_band):
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    canvases = manifest.get("items", [])
    if not canvases:
        return 0

    df_band = df_band.copy()
    df_band["bild_start"] = df_band["Link"].apply(extract_pn)
    df_band = df_band.dropna(subset=["bild_start"]).sort_values("bild_start").reset_index(drop=True)
    if df_band.empty:
        return 0

    manifest_base = manifest.get("id", "https://example.org/manifest")
    structures = []
    anzahl_zeilen = len(df_band)

    for idx, row in df_band.iterrows():
        start_pn = int(row["bild_start"])

        try:
            sp = int(float(row["Startseite"]))
            ep = int(float(row["Endseite"]))
            end_pn = start_pn + (ep - sp)
            if end_pn > len(canvases):
                end_pn = len(canvases)
        except (ValueError, TypeError):
            sp = ep = None
            if idx + 1 < anzahl_zeilen:
                end_pn = int(df_band.loc[idx + 1, "bild_start"]) - 1
            else:
                end_pn = len(canvases)

        start_index = start_pn - 1
        end_index = max(end_pn, start_pn)
        range_canvases = [{"id": c["id"], "type": "Canvas"} for c in canvases[start_index:end_index]]
        if not range_canvases:
            continue

        # Seitenzahlen im Label, damit das Inhaltsverzeichnis im Viewer
        # (Mirador-Sidebar) sofort als solches erkennbar ist -- gedruckte
        # Buchseiten (Startseite/Endseite), nicht die Bild-/Scannummern.
        titel = str(row["Titel"])
        if sp is not None and ep is not None:
            titel += f" (S. {sp})" if sp == ep else f" (S. {sp}–{ep})"

        range_object = {
            "id": f"{manifest_base}/range/r_{row['ID']}",
            "type": "Range",
            "label": {"de": [titel]},
            "items": range_canvases,
        }

        metadata = baue_metadata(row)
        if metadata:
            range_object["metadata"] = metadata

        structures.append(range_object)

    if not structures:
        return 0

    manifest["structures"] = structures
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return len(structures)


# ---------------------------------------------------------------------------
# Alle Manifeste anreichern
#
# Iteriert ueber alle Reihen-Ordner unter data/manifest/curated/ -- neue
# Reihen/Baende laufen automatisch mit.
# ---------------------------------------------------------------------------

def main():
    global df_by_id
    df = load_metadata()
    df_by_id = df.set_index("ID", drop=False)

    gesamt_ranges = 0
    gesamt_manifeste = 0

    for sr_ordner in sorted(p for p in MANIFESTS_ROOT.iterdir() if p.is_dir()):
        print(f"=== {sr_ordner.name} ===")

        for manifest_path in sorted(sr_ordner.glob("*.json")):
            if "_mit_ranges" in manifest_path.name or manifest_path.name == "collection.json":
                continue

            band = manifest_path.stem.split("_", 1)[1]
            df_band = df[(df["Schriftenreihe"] == sr_ordner.name) & (df["Band"] == band)]

            if df_band.empty:
                print(f"  [!] Kein Eintrag fuer Band '{band}' ({manifest_path.name})")
                continue

            anzahl = enrich_manifest(manifest_path, df_band)
            gesamt_manifeste += 1
            if anzahl:
                gesamt_ranges += anzahl
                print(f"  [+] {manifest_path.name}: {anzahl} Ranges")
            else:
                print(f"  [-] {manifest_path.name}: keine gueltigen Ranges")

    print(f"\nFertig: {gesamt_ranges} Ranges in {gesamt_manifeste} Manifesten.")


if __name__ == "__main__":
    main()
