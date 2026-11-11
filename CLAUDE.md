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
