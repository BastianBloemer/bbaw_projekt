# 02_manifest – IIIF-Manifeste erzeugen

Zweiter Teil der Pipeline. Lädt pro Band das IIIF-Manifest vom digilib-Server der BBAW herunter, macht es für den Viewer (Mirador) lauffähig und reichert es mit den kuratierten Metadaten aus `merged_df.csv` an.

| Nr. | Skript | Eingabe | Ausgabe |
|---|---|---|---|
| 01 | `01_manifest_download.py` | `merged_df.csv`, digilib (online) | `data/manifest/raw/<Reihe>/<Reihe>_<Band>.json` |
| 02 | `02_manifest_correct.py` | `data/manifest/raw/` | `data/manifest/curated/<Reihe>/<Reihe>_<Band>.json` |
| 03 | `03_manifest_enrich.py` | `merged_df.csv`, `data/manifest/curated/` | dieselben Manifeste, ergänzt um `structures` |
| 04 | `04_manifest_collection.py` | `data/manifest/curated/`, `merged_df.csv` | `collection.json` je Reihe und gesamt |

Alle Skripte werden aus dem Projekt-Root gestartet:

```bash
.venv/bin/python iiif-plattform/backend/scripts/02_manifest/03_manifest_enrich.py
```

## 01_manifest_download.py

Ermittelt alle Kombinationen aus Schriftenreihe und Band in `merged_df.csv` und lädt für jede das Manifest von `digilib.bbaw.de` herunter. Die Rohdaten landen unverändert in `data/manifest/raw/`.

## 02_manifest_correct.py

Behebt zwei Fehler in den Original-Manifesten, damit der Viewer die Bilder laden kann:

1. **URLs:** In allen `id`/`target`-Feldern fehlt der Pfadteil `digilib/` (`digilib.bbaw.de/…` wird zu `digilib.bbaw.de/digilib/…`).
2. **Image-Service:** `ImageService3`-Blöcke werden in IIIF-Image-API-v2-Services umgewandelt, weil nur diese zuverlässig funktionieren.

Das Skript kopiert dafür `raw/` nach `curated/`. **Achtung:** Dabei werden die Manifeste in `curated/` komplett überschrieben, und die von Schritt 03 erzeugten Inhaltsverzeichnisse gehen verloren. Nach 02 müssen also immer 03 und 04 folgen.

## 03_manifest_enrich.py

Schreibt für jede Abhandlung eine IIIF-*Range* in das Manifest ihres Bandes. Daraus entsteht das Inhaltsverzeichnis in der Seitenleiste des Viewers. Jede Range enthält:

- Titel mit gedruckten Seitenzahlen, z. B. „… (S. 12–34)“
- die zugehörigen Scan-Seiten (Canvases), berechnet aus der Bildnummer `pn=` im Link und aus Start-/Endseite
- Metadaten: Autor, Erscheinungsjahr, Abbildungen und Textbeziehungen (als klickbare Links zu den bezogenen Abhandlungen im Viewer)

Das Skript ersetzt bei jedem Lauf den Block `structures` vollständig. Es kann deshalb beliebig oft wiederholt werden.

## 04_manifest_collection.py

Erzeugt die IIIF-Collections, über die der Viewer durch den Bestand navigiert:

- je Schriftenreihe eine `collection.json` mit allen Bänden, beschriftet mit Reihentitel und Erscheinungszeitraum
- eine Gesamt-`collection.json` über alle Reihen

Die Bände der Reihe `ak-gesch` (Einzelmonographien) werden mit „Autor: Titel (Jahr)“ aus `merged_df.csv` beschriftet, die übrigen mit der Bandbezeichnung.

## Wann was ausführen?

| Situation | Schritte |
|---|---|
| **Nur Metadaten geändert** (`merged_df.csv` neu kuratiert) | **03 → 04**, danach `03_register` |
| Neue Bände / Schriftenreihen hinzugekommen | 01 → 02 → 03 → 04, danach `03_register` |
| Korrekturlogik in 02 geändert | 02 → 03 → 04, danach `03_register` |

Download (01) und Korrektur (02) sind also **nicht** nötig, wenn sich nur die Metadaten ändern. 04 ist in diesem Fall nur dann zwingend, wenn sich Titel, Autoren oder Jahre der Reihe `ak-gesch` geändert haben. Da der Lauf aber schnell ist, lohnt es sich, ihn immer mitlaufen zu lassen.

Die Register werden aus den angereicherten Manifesten gebaut. Nach jeder Änderung hier deshalb auch [`03_register`](../03_register/README.md) ausführen.
