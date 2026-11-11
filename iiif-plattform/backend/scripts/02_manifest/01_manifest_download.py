#!/usr/bin/env python3
"""
Lädt für jede Kombination aus Schriftenreihe und Band (aus merged_df.csv) das
IIIF-Manifest vom digilib-Server der BBAW herunter.

Eingabe:  data/metadata/curated/merged_df.csv
Ausgabe:  data/manifest/raw/<Schriftenreihe>/<Schriftenreihe>_<Band>.json
"""

import json
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MERGED_DF_PATH = DATA_DIR / "metadata" / "curated" / "merged_df.csv"
OUTPUT_ROOT = DATA_DIR / "manifest" / "raw"

BASE_URL = "https://digilib.bbaw.de/digilib/Manifester/IIIF/3/silo10!Bibliothek.tiff!{schriftenreihe}!{band}!tif"


def main():
    df = pd.read_csv(MERGED_DF_PATH, dtype=str)
    unique_combinations = df[["Schriftenreihe", "Band"]].dropna().drop_duplicates()

    for _, row in unique_combinations.iterrows():
        schriftenreihe = row["Schriftenreihe"]
        band = row["Band"]

        output_dir = OUTPUT_ROOT / schriftenreihe
        output_dir.mkdir(parents=True, exist_ok=True)

        url = BASE_URL.format(schriftenreihe=schriftenreihe, band=band)

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            manifest_data = response.json()

            filepath = output_dir / f"{schriftenreihe}_{band}.json"
            with filepath.open("w", encoding="utf-8") as f:
                json.dump(manifest_data, f, ensure_ascii=False, indent=2)

            print(f"✅ Gespeichert: {filepath}")

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP-Fehler bei {url}: {e}")
        except requests.exceptions.ConnectionError:
            print(f"❌ Verbindungsfehler bei {url}")
        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout bei {url}")
        except json.JSONDecodeError:
            print(f"⚠️ Kein gültiges JSON bei {url}")


if __name__ == "__main__":
    main()
