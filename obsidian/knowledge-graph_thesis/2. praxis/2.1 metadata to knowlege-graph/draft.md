### 0 · Kuration der Metadaten

Ich hatte die Metadaten aus dem OPAC bereits für die bisherige Webanwendung für die digitalisierten Akademieschriften bereinigt. Als ich aber Claude spontan damit beauftragte mir *mal eben schnell* einen Wissensgraphen aus den Metadaten zu erstellen, hat es damit angefangen Skripte für die Vervollständigung der Metadaten zu schreiben. Ich bin mir unsicher wie es auf die Lücken in den Daten gestoßen ist.

Ich werde jedenfalls mit einer Analyse der Metadaten anfangen. Zuerst werde ich nach Lücken suchen, leere Datenfelder. Dann werde ich nach Wegen suchen die Lücken zu füllen. Diesen Schritt werden ich vollständig mit deterministischen Skripten erledigen. Da die Kuration der Metadaten für die generelle Webanwendung nützlich ist, werde ich sie in die bestehende Pipeline integrieren.

### 1 · deterministische ie aus titel

Mit einem rein regelgeleiteten Python-Skript sollen erste Informationen über die Abhandlungen aus den Titeln extrahiert werden. Die Informationstypen sind

- Sprache
- Teile wie Auszug (wobei ich hier einschreiten muss, da die Auszüge die Berichte sind), 
- Gattungen wie Nachrufe, Antrittsrende, Beobachtung usw. (Claude hat 14 Gattungen definiert, die ich überprüfen sollte)
- Mitautoren
- Datumsangaben (muss ich prüfen)
- Anlässe wie Festreden zum Geburtstag des Monarchen

### 2 · llm-getriebene ie aus Titel

- **titel_de** deutsche Arbeitsuebersetzung / Normalisierung des Titels
- **sprache** Sprache des Titels (Korrektur der Heuristik aus 02)
- **disziplin** eine Disziplin aus DISZIPLINEN
- **themen** Schlagwoerter (moeglichst GND-nahe Sachbegriffe)
- **personen** im Titel erwaehnte Personen (nicht der Autor) mit Rolle
- **orte** erwaehnte Orte
- **werke** erwaehnte Werke / Texte / Handschriften
- **taxa** biologische / mineralogische Namen
- **objekte** Inschriften, Muenzen, Instrumente, Himmelskoerper ...
- **zeitraum** behandelter Zeitraum (Freitext, leer wenn keiner)

Die Frage ist, ob man das Modell wirklich frei die Inhalte aus den Titeln extrahieren lässt (**Open Information Extraction**) oder eher Themen usw. vorgibt und dann eher matchen lässt (**Closed Information Extraction**). Außerdem schlägt Claude vor, erst einmal Stichproben zu machen und diese dann zu bewerten.

### 3 · ontology