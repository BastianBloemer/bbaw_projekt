# 01_metadata – Metadaten beschaffen und kuratieren

Erster Teil der Pipeline. Lädt die bibliographischen Metadaten der „Digitalisierten Akademieschriften“ aus dem GBV-OPAC der BBAW-Bibliothek, bereinigt sie und erzeugt daraus die zentrale Tabelle `merged_df.csv`. Auf dieser Tabelle bauen alle weiteren Schritte auf (`02_manifest`, `03_register`).

| Nr. | Skript | Eingabe | Ausgabe |
|---|---|---|---|
| 01 | `01_metadata_download.py` | GBV-OPAC (online) | `data/metadata/raw/gbv-ris.ris`, `data/metadata/raw/gbv-vollanzeige.txt` |
| 02 | `02_metadata_curate.ipynb` | die beiden Rohdateien | `data/metadata/curated/merged_df.csv` |

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
5. Trägt fehlende Seiten von Hand nach.
6. Löst Verweise auf: Verweise in den Anmerkungen („Vgl.“, „Auszug“, „Ebenda“ …) werden anderen Zeilen zugeordnet, Antworten auf Antrittsreden ebenfalls. Fehlende Zielzeilen werden mit synthetischer `NEU-*`-ID neu angelegt.
7. Bündelt alle intertextuellen Bezüge in der Spalte `Textbeziehungen` (`Typ: ID | Typ: ID …`), jeweils in beide Richtungen.
8. Schätzt für die `NEU-*`-Zeilen einen Link (Scan-Bildnummer) über benachbarte Artikel.
9. Normalisiert die Titel, kuratiert die Reihe `ak-gesch` und exportiert das Ergebnis mit sprechenden Spaltennamen als `merged_df.csv`.


## Wann was ausführen?

- **Neue Daten aus dem OPAC holen:** 01 → 02
- **Nur an der Kuration etwas ändern:** 02

Danach in jedem Fall die Manifeste und Register aktualisieren, siehe [`02_manifest/README.md`](../02_manifest/README.md)
