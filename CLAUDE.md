# Projektregeln

## Python-Umgebung
- Es gibt genau **eine** virtuelle Umgebung: `.venv` im Projekt-Root (`bbaw_projekt/.venv`).
- **Niemals** eine neue `.venv` (oder ein anderes venv) anlegen – auch nicht in Unterordnern wie `knowledge-graph/` oder `iiif-plattform/`.
- Python immer über `.venv/bin/python` bzw. `.venv/bin/pip` aufrufen.
- Neue Pakete in die Root-`.venv` installieren und in `requirements.txt` (Root) nachtragen.

## Python-Skript (`.py`) oder Notebook (`.ipynb`)?
- **Standard ist `.py`.** Alles, was als Pipeline-Schritt wiederholt und ohne Eingriff durchläuft (Download, Umwandlung, Anreicherung, Export, Register), wird ein Python-Skript mit `main()` und `if __name__ == "__main__":`.
- **`.ipynb` nur für explorative Arbeit:** Datenkuration und -analyse, bei der Zwischenergebnisse angeschaut, Sonderfälle geprüft und Werte von Hand nachgetragen werden (z. B. `iiif-plattform/backend/scripts/01_metadata/02_metadata_curate.ipynb`).
- Im Zweifel `.py` wählen oder nachfragen.
- Pfade in Skripten relativ zur Skriptdatei bilden (`Path(__file__).resolve().parents[...]`), nicht relativ zum Arbeitsverzeichnis.

## Arbeitsbereich
- Aktuell wird **nur in `knowledge-graph/`** gearbeitet. `iiif-plattform/` ist abgeschlossen: dort nur lesen, nichts schreiben oder ändern.
- Metadaten kommen über `knowledge-graph/01_metadata_import.py` als `knowledge-graph/data/metadata.csv` (Kopie von `iiif-plattform/backend/data/metadata/curated/merged_df.csv`).

## Datenänderungen nur im Skript
- **Alle Änderungen an Daten passieren ausschließlich im Code** der Pipeline-Skripte/Notebooks (z. B. `02_metadata_curate.ipynb`). Das Skript ist zugleich die Dokumentation der Arbeit: Jede Korrektur muss dort nachvollziehbar und reproduzierbar stehen.
- Erzeugte Dateien (z. B. `merged_df.csv`, Manifeste, Register) **nie direkt bearbeiten** – weder von Hand noch per einmaligem Befehl. Sie entstehen nur durch Ausführen der Skripte.
- Einzelkorrekturen (z. B. falsche Seitenzahlen eines Eintrags) als Codezeile in die passende Zelle schreiben, mit Kommentar: was war falsch, woher stammt der richtige Wert.
- Tests gegen Kopien im Temp-Verzeichnis sind erlaubt; die echten Ausgabedateien schreibt der Nutzer durch Ausführen des Skripts.

## Abschluss jeder Antwort: was neu laden / ausführen
- Wenn Skripte oder Notebooks geändert wurden, endet die Antwort **immer** mit einer Liste:
  1. **Neu laden** (in VS Code geöffnete Dateien, die geändert wurden – sonst überschreibt die offene Version die Änderung)
  2. **Ausführen, in dieser Reihenfolge** – alle Skripte/Notebooks der Pipeline, die ab der Änderung neu laufen müssen, damit sie im Viewer ankommen (z. B. `02_metadata_curate.ipynb` → `02_manifest/03` → `04` → `03_register/01` → `02` → `03`), mit Befehlen aus dem Projekt-Root.

## Claude-Konfiguration
- Allgemeine Projektregeln gehören in diese `CLAUDE.md`.
- Skills gehören nach `.claude/skills/<skill-name>/SKILL.md`. Skills **nicht selbst schreiben**, sondern
  1. den vollständigen Inhalt der `SKILL.md` im Chat anzeigen und
  2. den Terminal-Befehl angeben, mit dem der Nutzer die Datei selbst anlegt, z. B.:
     ```bash
     mkdir -p ~/Dokumente/bbaw_projekt/.claude/skills/<skill-name>
     cat > ~/Dokumente/bbaw_projekt/.claude/skills/<skill-name>/SKILL.md <<'EOF'
     …Inhalt…
     EOF
     ```
