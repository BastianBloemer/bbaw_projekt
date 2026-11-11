# 01_metadata – Metadaten beschaffen und kuratieren

Erster Teil der Pipeline. Lädt die bibliographischen Metadaten der „Digitalisierten Akademieschriften“ aus dem GBV-OPAC der BBAW-Bibliothek, bereinigt sie und erzeugt daraus die zentrale Tabelle `merged_df.csv`. Auf dieser Tabelle bauen alle weiteren Schritte auf (`02_manifest`).

| Nr. | Skript | Eingabe | Ausgabe |
|---|---|---|---|
| 01 | `01_metadata_download.py` | GBV-OPAC (online) | `data/metadata/raw/gbv-ris.ris`, `data/metadata/raw/gbv-vollanzeige.txt` |
| 02 | `02_metadata_curate.ipynb` | die beiden Rohdateien | `data/metadata/curated/merged_df.csv` |
| 03 | `03_metadata_analyse.ipynb` (optional) | `merged_df.csv`, Vollanzeige | – (schreibt nichts) |

## 01_metadata_download.py

Sucht im OPAC nach „Digitalisierte Akademieschriften“ und lädt alle Treffer in Blöcken von 500 Titeln herunter, und zwar in zwei Formaten:

- **RIS**: strukturierte Felder (Titel, Autor, Jahr, Link …)
- **Vollanzeige**: Textformat mit Anmerkungen, bibliographischem Zusammenhang, Umfang usw., die im RIS fehlen

Bestehende Dateien werden vor dem Überschreiben mit Zeitstempel gesichert (`*.bak-JJJJMMTT-hhmmss.*`).

```bash
.venv/bin/python iiif-plattform/backend/scripts/01_metadata/01_metadata_download.py --dry-run   # nur Trefferzahl
.venv/bin/python iiif-plattform/backend/scripts/01_metadata/01_metadata_download.py
```

## 02_metadata_curate.ipynb

Bewusst ein Notebook, weil hier kuratiert und analysiert wird: Zwischenergebnisse werden angesehen, Sonderfälle von Hand geprüft und nachgetragen. Das Notebook mit dem Kernel aus `.venv` öffnen und von oben nach unten ausführen.

Was es tut:

1. Liest RIS und Vollanzeige ein und wandelt beide in DataFrames um.
2. Bereinigt sie: überflüssige Felder entfernen, unplausible Jahre (außerhalb 1700–1900) verwerfen, Großschreibung der Autornamen normalisieren.
3. Extrahiert aus Umfang und Anmerkungen Seitenzahlen (Start-/Endseite), Fortsetzungen, Tafeln, Übersetzungen und Antworten.
4. Führt RIS und Vollanzeige über den Link zusammen und leitet Schriftenreihe und Band aus der URL ab.
5. Trägt fehlende oder falsche Seiten von Hand nach und korrigiert die Seiten von Fortsetzungs-Duplikaten.
6. **Korrigiert verdoppelte erste Ziffern** aus dem Katalog (z. B. „S. 1104“ statt „S. 104“, ca. 100 meist einseitige Einträge). Erkennbar sind sie daran, dass der Abstand zwischen Bildnummer und Seite nicht zu den Nachbarartikeln passt. In Bänden, in denen jede Abhandlung mit S. 1 beginnt, wird außerdem ein fehlender Bindestrich korrigiert („S. 1114“ → S. 1–114).
7. **Schätzt fehlende Seitenzahlen** (bei ca. 100 Zeilen fehlen sie schon im Katalog) aus der Bildnummer im Link und dem Versatz des benachbarten Artikels. Nachbarn mit unpassendem Versatz werden dabei übergangen. Ist die geschätzte Länge größer als 150 Seiten, bleibt die Endseite leer. Beginnen beide Nachbarn mit S. 1 (eigene Seitenzählung je Abhandlung), wird die Startseite 1 und die Endseite bleibt leer. Beginnt nur der folgende Artikel mit S. 1, liegt der Eintrag im Vorspann mit eigener, meist römischer Zählung (z. B. Gedächtnisreden). Dann wird nicht geschätzt, und die Seiten werden nach Prüfung im Viewer als Einzelkorrektur nachgetragen.

   Die neue Spalte `Seiten_Quelle` hält die Herkunft der Seiten fest: `csv` (Katalog), `manuell` (von Hand nachgetragen), `korrigiert` (verdoppelte Ziffer), `geschaetzt` (aus der Bildnummer), `verweis` (`NEU-*`-Zeilen).
8. Löst Verweise auf: Verweise in den Anmerkungen („Vgl.“, „Auszug“, „Ebenda“ …) werden anderen Zeilen zugeordnet, Antworten auf Antrittsreden ebenfalls. Fehlende Zielzeilen werden mit synthetischer `NEU-*`-ID neu angelegt. Dabei gilt:
   - „Mém.“ und „Hist.“ werden je nach Jahr der passenden Reihe zugeordnet: `02-hist` bis 1769, `03-nouv` 1770–1786, `05-mem` ab 1786 einschließlich der Doppeljahrgänge wie `17881789`.
   - Eine Zeile mit exakt gleicher Fundstelle (Reihe, Band, Seiten) gilt als Ziel, sodass keine Kopien bestehender Zeilen entstehen.
   - Verweise auf die eigenen Seiten (Selbstverweise) werden verworfen.
   - Pro Fundstelle entsteht nur ein Neueintrag, auch wenn mehrere Quellzeilen sie nennen. Alle Quellzeilen verweisen dann auf diesen Eintrag.
9. Bündelt alle intertextuellen Bezüge in der Spalte `Textbeziehungen` (`Typ: ID | Typ: ID …`), jeweils in beide Richtungen.
10. Schätzt für die `NEU-*`-Zeilen einen Link (Scan-Bildnummer) über benachbarte Artikel.
11. Normalisiert die Titel, kuratiert die Reihe `ak-gesch` und benennt die Spalten sprechend um.
12. **Zweite Kuration** (Abschnitt am Ende des Notebooks):
    - **Jahre ergänzen:** Fehlende Werte in `Jahr` werden aus dem häufigsten Jahr desselben Bandes ergänzt, sonst aus der Jahreszahl in der Bandbezeichnung, sofern sie in den Zeitraum der Reihe passt. Die neue Spalte `Jahr_Quelle` hält die Herkunft fest (`csv`, `band_modus`, `band_nummer`).
    - **Autoren normalisieren:** `Autor` wird überschrieben. Grundlage sind eine Korrekturliste (`AUTOR_KORREKTUREN`), die Auflösung reiner Nachnamen zum vollen Namen, wenn das eindeutig möglich ist, und die Vereinheitlichung von Schreibvarianten. „Ohne Angabe Des Verfassers“ bleibt stehen.

    Kontrollzellen zeigen u. a. alle Autoränderungen und nicht eindeutig auflösbare Namen.
13. Speichert das Ergebnis als `merged_df.csv`.

## 03_metadata_analyse.ipynb

Optionale Qualitätsprüfung von `merged_df.csv`, ohne Schreibzugriff. Das Notebook erstellt Prüflisten mit klickbaren digilib-Links:

- Neueinträge (`NEU-*`) ohne eigenen Katalog-Link, jeweils mit Quellzeile und dem Katalogtext, aus dem sie erschlossen wurden, sowie mehrfach erschlossene Neueinträge
- doppelte Titel, eingeteilt in Kategorien mit Empfehlung zum Umgang

Nach Änderungen an der Kuration erneut ausführen, um den Effekt zu prüfen.

## Wann was ausführen?

- **Neue Daten aus dem OPAC holen:** 01 → 02
- **Nur an der Kuration etwas ändern:** 02

Danach in jedem Fall die Manifeste und Register aktualisieren, siehe [`02_manifest/README.md`](../02_manifest/README.md)
