# 03_register – Register für das Frontend erzeugen

Dritter Teil der Pipeline. Baut aus den angereicherten Manifesten die JSON-Register, mit denen das Frontend Suche, Personen- und Begriffsregister darstellt.

| Nr. | Skript | Eingabe | Ausgabe |
|---|---|---|---|
| 01 | `01_register-abhandlungen.py` | `data/manifest/curated/**` | `data/registers/register-abhandlungen.json` |
| 02 | `02_register-personen.py` | `register-abhandlungen.json` | `data/registers/register-personen.json` |
| 03 | `03_register-begriffe.py` | `register-abhandlungen.json` | `data/registers/register-begriffe.json` |

Alle Skripte werden aus dem Projekt-Root gestartet:

```bash
.venv/bin/python iiif-plattform/backend/scripts/03_register/01_register-abhandlungen.py
.venv/bin/python iiif-plattform/backend/scripts/03_register/02_register-personen.py
.venv/bin/python iiif-plattform/backend/scripts/03_register/03_register-begriffe.py
```

## 01_register-abhandlungen.py

Liest die Ranges (`structures`) aller Manifeste aus und schreibt sie als flache Liste, sortiert nach Jahr, Autor und Titel. Jeder Eintrag enthält:

- Titel, Autor, Jahr und Schriftenreihe
- Abbildungen und Textbeziehungen
- Start- und End-Canvas sowie den Pfad zum Manifest, damit der Viewer direkt an die richtige Stelle springt
- ein Suchfeld aus Titel und Autor in Kleinbuchstaben

Dieses Register ist die Grundlage für die beiden folgenden.

## 02_register-personen.py

Gruppiert die Abhandlungen nach Autor:in und die Autor:innen nach Anfangsbuchstaben. Akzente werden dabei ignoriert (É wird unter E einsortiert). Die Werke einer Person sind nach Titel sortiert.

## 03_register-begriffe.py

Gewinnt Schlagwörter aus den Titeln:

1. Jeder Titel wird mit spaCy zerlegt und **lemmatisiert**, sodass z. B. „Versuche“ und „Versuchs“ zu „Versuch“ werden.
2. Herausgefiltert werden Stoppwörter (Deutsch, Französisch, Latein), Personennamen (aus den Autorfeldern und aus der spaCy-Namenserkennung) und Wörter mit weniger als drei Buchstaben.
3. Die Begriffe werden nach Anfangsbuchstaben gruppiert, jeder mit seinen Abhandlungen.

Benötigt die spaCy-Modelle `de_core_news_sm` und `fr_core_news_sm`. Sie stehen in der `requirements.txt` im Projekt-Root.

## Wann was ausführen?

Immer **01 → 02 → 03**, nachdem sich die Manifeste geändert haben (also nach jedem Lauf von [`02_manifest`](../02_manifest/README.md)). 02 und 03 hängen nur von 01 ab und können in beliebiger Reihenfolge laufen.
