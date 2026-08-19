# Dokumentation: Digitalisierte Akademieschriften der BBAW

Diese Datei dokumentiert vollständig, welche Dateien/Skripte im Projekt vorhanden sind, welche Funktion sie in der Pipeline haben, welche Daten sie erzeugen, und wie Suche, Register und der IIIF-Viewer im Frontend funktionieren. Gedacht als Rohmaterial zum Weiterschreiben (z. B. für die Über-Seite oder einen Abschlussbericht).

---

## 1. Überblick: Datenfluss

```
Rohdaten (extern)
  ├─ GBV-OPAC (bibliographische Metadaten)
  └─ digilib.bbaw.de (Scans als IIIF-Manifeste)
        │
        ▼
01_metadata_download.py  ──────────►  gbv-ris.ris, gbv-vollanzeige.txt
01_manifest_download.ipynb ─────────►  manifest/raw/<Reihe>/<Reihe>_<Band>.json
        │                                   │
        ▼                                   ▼
02_metadata_curate.ipynb            02_manifest_correct.ipynb
        │                                   │
        ▼                                   ▼
   merged_df.csv                   manifest/curated/<Reihe>/<Reihe>_<Band>.json
        │                                   │
        └──────────────┬────────────────────┘
                        ▼
              03_manifest_enrich.ipynb
              (schreibt Ranges + Metadata in die curated Manifeste)
                        │
                        ▼
              04_manifest_collection.ipynb
              (baut collection.json je Reihe + Gesamt-collection.json)
                        │
                        ▼
              01_register-abhandlungen.ipynb
              (liest alle curated Manifeste, erzeugt flache Liste)
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
  02_register-personen.ipynb   03_register-begriffe.ipynb
              │                   │
              ▼                   ▼
  register-personen.json    register-begriffe.json
                        │
                        ▼
         Frontend: index.html, suche.html, register.html, viewer.html, about.html
```

Die Pipeline ist in drei nummerierte Ordner unter `backend/scripts/` gegliedert: `01_metadata/`, `02_manifest/`, `03_register/`. Innerhalb jedes Ordners sind die Skripte selbst wieder nummeriert und müssen in dieser Reihenfolge laufen.

---

## 2. Rohdaten

| Datei | Herkunft | Inhalt |
|---|---|---|
| `backend/data/metadata/raw/gbv-ris.ris` | GBV-OPAC (Gemeinsamer Bibliotheksverbund), Suche „Digitalisierte Akademieschriften“ | Bibliographische Metadaten im RIS-Format (ein Eintrag pro Abhandlung: Titel, Autor:in, Jahr, Link zum Digitalisat, u. a.) |
| `backend/data/metadata/raw/gbv-vollanzeige.txt` | GBV-OPAC, gleiche Suche, Vollanzeige-Textexport | Zusätzliche Felder, die im RIS-Format fehlen — vor allem die freien **Anmerkungen** (Fortsetzungs-/Übersetzungs-/Verweishinweise, aus denen später die Textbeziehungen extrahiert werden) |
| `backend/data/manifest/raw/<Reihe>/<Reihe>_<Band>.json` | `digilib.bbaw.de` (Digitalisierungsserver der BBAW) | Ein IIIF-Presentation-Manifest pro Band: alle Scans (Canvases) dieses Bandes, ursprünglich aus einem DFG-Digitalisierungsprojekt Anfang der 2000er |

Beide Ausgangsdaten-Quellen (GBV-Metadaten, digilib-Scans) sind alles, was für dieses Projekt zur Verfügung stand. Es wurden keine weiteren Daten recherchiert oder ergänzt — nur diese beiden Quellen kuratiert, verknüpft und aufbereitet (siehe auch die Dokumentations-Sektion auf der Über-Seite).

---

## 3. Backend-Skripte im Detail

### 3.1 `backend/scripts/01_metadata/01_metadata_download.py`

Eigenständiges Python-Skript (kein Notebook), ersetzt einen früher manuellen Export. Baut eine Session beim GBV-OPAC auf, sucht im Index `[ALL]` nach „Digitalisierte Akademieschriften“, und lädt die komplette Trefferliste in Blöcken von je 500 Titeln (Download-Limit des OPAC) sowohl im RIS-Format als auch als Vollanzeige-Text herunter. Ergebnis: `gbv-ris.ris` und `gbv-vollanzeige.txt`. Sichert vorhandene Dateien automatisch mit Zeitstempel, bevor es sie überschreibt.

### 3.2 `backend/scripts/01_metadata/02_metadata_curate.ipynb`

**Das zentrale Kurations-Notebook.** Verarbeitet die beiden Rohdaten-Dateien zu einer einzigen, sauberen Tabelle `merged_df.csv`. 26 Zellen, in dieser Reihenfolge:

**RIS-Verarbeitung**
- RIS-Datei parsen (Zeilen im `KEY  - Wert`-Format zu einer Zeile pro Eintrag zusammenfassen)
- Unnötige RIS-Felder verwerfen, Datensätze mit `ak-gesch` im Link (Fehlklassifikationen) entfernen
- `PY` (Erscheinungsjahr) bereinigen: Ausreißer außerhalb 1700–1900 verwerfen (v. a. „2001“ = fälschlich erfasstes Digitalisierungsjahr)
- Autorennamen normalisieren (nicht komplett großgeschriebene Wörter)

**Vollanzeige-Verarbeitung**
- Text in einzelne Datensätze splitten, anhand fester Feldbezeichner (`Aufsatz / Teil:`, `Anmerkung:` usw.) in Spalten zerlegen
- Bibliographischen Zusammenhang und Anmerkungen zusammenführen und bereinigen
- Seitenangaben aus Freitext in `SP`/`EP` (Start-/Endseite) extrahieren, inkl. römischer Ziffern
- Aus der Anmerkung werden **Abbilder** (Tafeln/Abbildungen-Hinweise), **Übersetzung/Original**-Hinweise und **Antwort**-Hinweise (Antworten auf Antrittsreden) als eigene Spalten herausgezogen
- Weitere Textreinigung (Anführungszeichen, offensichtlich irrelevante Anmerkungen wie „Druckfehler“ o. ä.)

**Zusammenführung**
- RIS und Vollanzeige über den Digitalisat-Link gemerged (Outer Join), Duplikate entfernt
- Schriftenreihe und Band aus dem Link extrahiert
- Für ca. 30 Zeilen mit fehlerhaften Quelldaten Seitenzahlen von Hand nachgetragen

**Intertextuelle Beziehungen** (das aufwendigste Teilstück)
- Anmerkung wird vor weiterer Bearbeitung als `Anmerkung_original_backup` gesichert
- Anmerkungen wie „Auszug: 1837. MB S. 105–107“ werden geparst: Abkürzung (MB, SB, Abh., Mém. …) auf Schriftenreihe/Band abgebildet, Zielzeile über Seitenüberlappung + gleicher Autor:in-Nachname gesucht. Mehrfache Teilverweise in einer Anmerkung (mehrere Seitenbereiche) werden einzeln aufgelöst; unauflösbare Bereiche werden als neue Zeilen (`NEU-<Quell-ID>-<n>`) angelegt, mit Titel/Autor der Quellzeile
- Fortsetzungs-Duplikate (zwei/drei Zeilen mit identischem Titel/Autor, die tatsächlich verschiedene Teile sind) bekommen korrigierte Start-/Endseiten
- Aus der `Antwort`-Spalte werden neue Zeilen für Antworten auf Antrittsreden angelegt, sofern nicht schon vorhanden (Abgleich über Schriftenreihe/Band/Seiten-Overlap/Nachname)
- **Textbeziehungen**: eigenständige, in sich abgeschlossene Neuberechnung aller Beziehungstypen (Vgl/Verweis, Auszug, Fortsetzung, Nachtrag, Antwort, Übersetzung) direkt aus dem Anmerkungs-Backup, zusammengeführt zu `"Typ: ID | Typ: ID"`-Paaren, auf **beiden** beteiligten Zeilen bidirektional eingetragen. Aktuelle Typ-Bezeichnungen (aus Sicht der jeweiligen Zeile):

  | Vorwärts | Rückwärts | Bedeutung der Zielzeile |
  |---|---|---|
  | Verweis | Verweis | Verweis im gleichen Band/derselben Reihe (fasst auch die früheren „Vgl.“-Fälle zusammen — die Beziehung ist inhaltlich zu uneinheitlich für eine gerichtete Bezeichnung) |
  | Übersetzung | Original | Zielzeile ist die Übersetzung bzw. das Original |
  | Auszug | Volltext | Zielzeile ist der Auszug bzw. die vollständige Fassung |
  | Fortsetzung | Hauptteil | Zielzeile ist die Fortsetzung bzw. der Hauptteil |
  | Nachtrag | Hauptteil | Zielzeile ist der Nachtrag bzw. der Haupttext |
  | Antwort | Antrittsrede | Zielzeile ist die Antwort bzw. die beantwortete Antrittsrede |

  **Wichtige Einschränkung:** Diese Beziehungen wurden ausschließlich aus den GBV-Anmerkungen extrahiert. Ob dort ursprünglich alle bestehenden Beziehungen erfasst waren, ist unbekannt — die Textbeziehungen können daher unvollständig sein.
- Für alle neu angelegten Zeilen (`NEU-*`) wird ein geschätzter Digitalisat-Link hergeleitet: Nächstgelegene existierende Zeile im selben Band gesucht, deren Versatz zwischen gedruckter Seitenzahl und Scan-Bildnummer übernommen

**Abschluss**
- Titel normalisiert (Anführungszeichen am Rand entfernt, erster Buchstabe großgeschrieben — wirkt sich automatisch auch auf die Textbeziehungen-Anzeige aus, da diese den Titel der Zielzeile verwendet)
- Sortierung nach Reihe/Band/Startseite
- Spalten in sprechende Namen umbenannt und als `merged_df.csv` exportiert

**Ergebnis-Spalten von `merged_df.csv`:** `Startseite, Endseite, Abbilder, ID, Titel, Autor, Jahr, Link, Schriftenreihe, Band, Textbeziehungen` — aktuell 8434 Zeilen, davon 984 mit mindestens einer Textbeziehung.

### 3.3 `backend/scripts/02_manifest/01_manifest_download.ipynb`

Frühes, einmalig gelaufenes Skript: lädt für jede eindeutige Schriftenreihe/Band-Kombination (damals aus einer inzwischen abgelösten `df_all.csv`) das zugehörige IIIF-Manifest von `digilib.bbaw.de` herunter und legt es unter `manifest/raw/<Reihe>/<Reihe>_<Band>.json` ab. Bootstrap-Schritt, nicht Teil des regulären Re-Runs.

### 3.4 `backend/scripts/02_manifest/02_manifest_correct.ipynb`

Kopiert alle Manifeste von `manifest/raw/` nach `manifest/curated/` und korrigiert dabei zwei strukturelle Probleme der Rohdaten:
1. Fehlende `digilib/`-Pfadsegmente in URLs werden ergänzt
2. IIIF-Image-Service-Blöcke im (nicht unterstützten) v3-Format werden ins funktionierende v2-Format konvertiert (`@id`/`@type`/`profile` statt `id`/`type`)

### 3.5 `backend/scripts/02_manifest/03_manifest_enrich.ipynb`

Reichert jedes curated Manifest mit **Ranges** (Inhaltsverzeichnis-Einträgen) an, basierend auf `merged_df.csv`:
- Lädt `merged_df.csv`, extrahiert die Scan-Bildnummer (`pn=`) aus dem Link
- Für jede Zeile eines Bandes wird eine Range gebaut: Start-Bildnummer aus dem Link, Seitenumfang aus Start-/Endseite (Fallback: bis zur nächsten Zeile, falls Seitenzahlen fehlen)
- Jede Range bekommt `metadata`: Autor, Erscheinungsjahr (aus der Spalte `Jahr`, die pro Werk aus dem RIS-Feld `PY` stammt — präziser als aus dem Banddateinamen abgeleitet, und bei buchweise statt jahrweise gezählten Reihen wie 01-misc/04-phys die einzige Jahresquelle überhaupt), Abbildungen, und **Textbeziehungen als HTML**: jede Ziel-ID wird über den Titel + Link aufgelöst; ist eine gültige Seitenzahl bekannt, entsteht ein klickbarer `viewer.html?manifest=...&canvas=...`-Link (IIIF erlaubt ein eingeschränktes HTML-Subset inkl. `<a>` in Metadata-Werten), sonst bleibt es Text. Typ und Titel stehen in separaten `<span class="beziehung-typ">`/`<span class="beziehung-wert">`, damit sie im Frontend unabhängig gestylt werden können; der Typ steht in Klammern hinter dem Titel, innerhalb des Links (damit z. B. Hover-Effekte beide erfassen)
- Iteriert automatisch über alle Reihen-Ordner unter `manifest/curated/`

Aktuell: 8410 Ranges über 245 Manifeste.

### 3.6 `backend/scripts/02_manifest/04_manifest_collection.ipynb`

Baut die IIIF-Collection-Hierarchie:
- Pro Schriftenreihe eine `collection.json` im jeweiligen Ordner, mit einem Eintrag pro Band. Bandbezeichnung als Label, dabei werden zwei zusammengezogene Jahreszahlen ohne Trennzeichen (z. B. „18041811“, aus der Quelle übernommen) für die Anzeige mit Bindestrich versehen („1804-1811“)
- Eine Gesamt-`collection.json` in `manifest/curated/`, mit den zehn Reihen als Einträgen, Label inkl. Erscheinungszeitraum (fest hinterlegt, da nicht jede Reihe jahrweise gezählt ist)

### 3.7 `backend/scripts/03_register/01_register-abhandlungen.ipynb`

Liest **alle** curated Manifeste, extrahiert aus jeder Range Titel, Autor, Ort, Verlag, Jahr, Abbildungen, Textbeziehungen sowie Start-/End-Canvas, und schreibt eine flache Liste `register-abhandlungen.json`. Zusätzlich:
- `schriftenreihe`: Kürzel ohne Zahl/Bindestrich (z. B. „abh“ statt „07-abh“), abgeleitet aus dem Ordnernamen
- `year`: bevorzugt aus der Range-Metadata „Erscheinungsjahr“ (präzise, pro Werk), sonst Fallback auf die ersten vier Ziffern des Banddateinamens
- `search`: kleingeschriebene Kombination aus Titel + Autor, als Suchgrundlage für `suche.js`
- `manifest`, `startCanvas`, `endCanvas`: für den Sprung in den Viewer

Sortiert nach Jahr, Autor, Titel. Aktuell 8410 Einträge.

### 3.8 `backend/scripts/03_register/02_register-personen.ipynb`

Gruppiert `register-abhandlungen.json` nach Autor:in (Stammbuchstabe unicode-normalisiert, z. B. É → E), zweistufig verschachtelt (Buchstabe → Person → Werkliste). Jedes Abhandlungs-Objekt wird 1:1 übernommen (inkl. `anhang`, `textbeziehungen`, `schriftenreihe`). Aktuell 1047 Personen in 25 Buchstabengruppen.

### 3.9 `backend/scripts/03_register/03_register-begriffe.ipynb`

Extrahiert Begriffe aus den Abhandlungstiteln mittels spaCy (`de_core_news_sm` für die eigentliche Verarbeitung; `fr_core_news_sm`/Latein-Stopwörter zusätzlich für die Stopwort-Liste):
- Personennamen (aus den Autor:innen-Angaben sowie über spaCy-NER erkannte Personennamen) werden ausgeschlossen
- Übrige Wörter werden **lemmatisiert** (`token.lemma_`), damit unterschiedliche Wortformen (z. B. „Versuche“/„Versuchen“) nicht als separate Begriffe auftauchen
- Ergebnis: verschachteltes Register Buchstabe → Begriff → Liste der Abhandlungen (Objekte wieder 1:1 aus `register-abhandlungen.json` übernommen)

Begriffe insgesamt: rund 13.700 (nach Einführung der Lemmatisierung reduziert von zuvor ca. 15.700 ohne).

---

## 4. Struktur der erzeugten Manifeste (IIIF Presentation API 3.0)

Jedes Manifest (`manifest/curated/<Reihe>/<Reihe>_<Band>.json`) enthält:

```json
{
  "@context": "...",
  "type": "Manifest",
  "id": "https://digilib.bbaw.de/.../silo10!Bibliothek.tiff!<Reihe>!<Band>!tif",
  "items": [ /* eine Canvas pro Scan-Seite, in Bildreihenfolge */ ],
  "structures": [ /* eine Range pro Abhandlung, aus 03_manifest_enrich.ipynb */ ]
}
```

Eine **Canvas** referenziert das eigentliche Bild über den digilib-Bildservice (IIIF Image API v2). Eine **Range** (Inhaltsverzeichnis-Eintrag) sieht so aus:

```json
{
  "id": ".../range/r_<ID>",
  "type": "Range",
  "label": { "de": ["<Titel>"] },
  "items": [ /* Canvas-Referenzen dieser Abhandlung */ ],
  "metadata": [
    { "label": {"de": ["Autor"]}, "value": {"de": ["..."]} },
    { "label": {"de": ["Erscheinungsjahr"]}, "value": {"de": ["..."]} },
    { "label": {"de": ["Abbildungen"]}, "value": {"de": ["..."]} },
    { "label": {"de": ["Textbeziehungen"]}, "value": {"de": ["<HTML mit Links>"]} }
  ]
}
```

**Wichtig:** Mirador (der eingesetzte IIIF-Viewer) zeigt diese Range-Metadata standardmäßig **nicht** an — das Info-Panel ist deaktiviert (`panels.info: false` in `mirador-config.js`) und würde ohnehin nur Manifest-, nicht Range-Metadata anzeigen. Die Metadata existiert also in den Manifesten, wird aber ausschließlich von den Registern/der Suche ausgelesen (`01_register-abhandlungen.ipynb` liest `structure.metadata`).

Die **Collection-Hierarchie**: eine Gesamt-`collection.json` (10 Schriftenreihen als Einträge) → je eine `collection.json` pro Reihe (alle Bände dieser Reihe als Einträge).

---

## 5. Frontend: Suche & Register

### Gemeinsame Basis

Beide Seiten zeigen Treffer im identischen Format (`work`-Block), erzeugt in `frontend/js/suche.js` bzw. `frontend/js/register-personen.js`/`register-begriffe.js`:

```
<Titel>  [Download-Icon]
Autor:in | Jahr | Anhang | Reihenkürzel
<Textbeziehungen, falls vorhanden>
```

- **Titel**: fett, verlinkt (`<a class="work-title">`), öffnet `viewer.html?manifest=...&canvas=...` in neuem Tab (direkt auf die passende Seite gesprungen)
- **Download-Icon** (`work-download`, SVG aus `zip-download.js`): lädt beim Klick alle Seiten der Abhandlung als ZIP herunter. Zeigt währenddessen Fortschritt (`3/12`), danach ✓ oder ⚠, mit eigenem gestyltem Popup als Tooltip-Ersatz (`work-download-popup`, verzögertes Einblenden über `transition-delay`, abgerundete Ecken)
- **Metadatenzeile** (`work-meta`, klein/grau): Autor:in (nur bei Suche/Begriffe — im Personen-Register bereits durch den übergeordneten Karten-Header abgedeckt), Jahr, Anhang (z. B. „mit 1 Tafel“), Reihenkürzel — alle mit „|“ getrennt
- **Textbeziehungen** (`work-beziehungen`, kursiv): das fertige HTML aus der Manifest-Metadata, direkt übernommen. Beziehungstyp steht fett, klein, in Klammern, innerhalb des Links

### `frontend/js/zip-download.js`

Baut das ZIP-Archiv **im Browser** ohne externe Bibliothek: eigene CRC32-Implementierung + manuell zusammengesetzte ZIP-Struktur (lokale Dateiheader, zentrales Verzeichnis, End-of-Central-Directory), Methode „store“ (keine Kompression, da JPEGs ohnehin kaum komprimieren). Lädt das Manifest der Abhandlung, ermittelt die Canvases zwischen `startCanvas` und `endCanvas`, holt zu jeder das Vollauflösungsbild über den IIIF-Image-Service und packt alles zusammen.

### Suche (`suche.html`, `suche.js`)

Ein Eingabefeld. Bei Enter wird `register-abhandlungen.json` (einmalig gecacht) nach dem Suchbegriff gefiltert — Treffer, wenn Titel, Autor **oder** Jahr den Begriff enthalten (Feld `search` in den Daten). Ergebnisliste im oben beschriebenen Format.

### Register (`register.html`, `register-main.js`, `register-personen.js`, `register-begriffe.js`)

Zwei Modi, umschaltbar über `#register-switch` (Autor:innen / Begriffe), jeweils aus `register-personen.json`/`register-begriffe.json` geladen. Darunter eine Buchstabenleiste (`#alphabet-nav`) zum Springen. Jede Person/jeder Begriff ist eine aufklappbare Karte (`.entry`/`.entry-header`/`.contents`, standardmäßig eingeklappt), die beim Aufklappen die zugehörigen Abhandlungen im Suche-Format zeigt.

---

## 6. Frontend: IIIF-Viewer

### `viewer.html`, `mirador-app.js`, `mirador-config.js`

Reine Mirador-Instanz (`#my-mirador`), öffnet sich immer in einem neuen Tab, ohne eigene Seiten-Navigation. Zwei URL-Parameter steuern, was geladen wird:
- `?manifest=<Pfad>&canvas=<ID>` — eine einzelne Abhandlung, optional mit Sprung zur passenden Canvas
- `?collection=<Pfad>` — eine Sammlung (z. B. von einer Startseiten-Kachel aus); ohne Parameter wird die Gesamt-`collection.json` geladen

**Ansicht je nach Kontext** (gesteuert über `isCollection = !manifestParam` in `mirador-app.js`):
- Einzelne Abhandlung: Seitenleiste mit Inhaltsverzeichnis (Canvas-Index) offen
- Sammlung: Seitenleiste geschlossen, da der Index dort nur eine nicht anklickbare Liste zeigen würde — Navigation läuft über Miradors eigene „Zeige Sammlungen“-Funktion

**Design-Anpassungen in `mirador-config.js`** (`theme` in der Mirador-Konfiguration, MUI-basiert):
- Primärfarbe Rot (`#d70035`), Sekundärfarbe Blaugrau (`#3E4955`), passend zum übrigen Frontend
- Links in Manifest-/Range-Metadata (`IIIFHtmlContent`) rot, unterstrichen
- Rahmen unter jedem Inhaltsverzeichnis-Eintrag (`MuiTreeItem`), keine Rundung
- Gelbe Standard-Hervorhebung des gerade sichtbaren Eintrags im Index deaktiviert (transparent gesetzt)

**`viewer.css`**: setzt `ul { display: block }` innerhalb von `#my-mirador` zurück, weil `base.css` global `ul { display: flex; flex-wrap: wrap }` für die eigene Navigation setzt — das würde sonst auch Miradors intern als `<ul>` gebauten Inhaltsverzeichnis-Baum betreffen und die Einträge je nach Seitenleistenbreite mehrspaltig statt einspaltig anordnen.

**Was der Viewer NICHT zeigt**: Anhangsinformationen und Textbeziehungen — das Info-Panel ist deaktiviert und würde ohnehin nur Manifest-, nicht Range-Metadata anzeigen (siehe Abschnitt 4). Diese Informationen sind ausschließlich über Suche und Register zugänglich.

---

## 7. Datenverzeichnisse im Überblick

```
backend/
├── data/
│   ├── metadata/
│   │   ├── raw/          gbv-ris.ris, gbv-vollanzeige.txt
│   │   └── curated/      merged_df.csv
│   ├── manifest/
│   │   ├── raw/          <Reihe>/<Reihe>_<Band>.json (unbearbeitet von digilib)
│   │   └── curated/      <Reihe>/<Reihe>_<Band>.json (korrigiert + Ranges) + collection.json je Ebene
│   └── registers/
│       ├── register-abhandlungen.json
│       ├── register-personen.json
│       └── register-begriffe.json
└── scripts/
    ├── 01_metadata/   01_metadata_download.py, 02_metadata_curate.ipynb
    ├── 02_manifest/   01_manifest_download.ipynb, 02_manifest_correct.ipynb,
    │                  03_manifest_enrich.ipynb, 04_manifest_collection.ipynb
    └── 03_register/   01_register-abhandlungen.ipynb, 02_register-personen.ipynb,
                       03_register-begriffe.ipynb

frontend/
├── html/   index.html, suche.html, register.html, viewer.html, about.html
├── js/     suche.js, register-main.js, register-personen.js, register-begriffe.js,
│           zip-download.js, mirador-app.js, mirador-config.js, mirador-dependencies.js,
│           about.js, back-to-top.js
├── css/    base.css, index.css, suche.css, register.css, viewer.css, about.css
└── imgs/   Logos, Kachelbilder je Schriftenreihe
```
