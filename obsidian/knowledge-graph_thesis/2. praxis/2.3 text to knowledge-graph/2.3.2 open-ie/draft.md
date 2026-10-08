### 0 · Grundlagen: Was ist Open IE?

- **Vo & Bagheri (2016)**: die klassischen Generationen, also regelbasierte Relationsphrasen und Clause-basierte Extraktion
- **Kamp et al. (2023)**: neuerer Überblick, Abgrenzung zur Relationsextraktion, Anwendungen in KGs

### 1 · Analyseeinheit und Kontext festlegen

Was wird eigentlich extrahiert, und aus welchem Textausschnitt?

- **Chausson & Ross**: Die Einheit ist der _Claim_, nicht das Tripel. Das zeigt, dass diese Wahl eine eigene Entscheidung ist.
- **MOIE-KG**: Die Einheit ist das _lange Dokument_. Relationen reichen über mehrere Absätze, deshalb braucht es ein dokumentweites Gedächtnis.

### 2 · Offene Extraktion

- **Vo & Bagheri / Kamp**: Relationsphrasen und ihre Argumente, die klassischen Verfahren
- **Organising Knowledge from Text**: Subjekt-Prädikat-Objekt-Tripel per LLM-Prompting, mit Vergleich von Zero-, One- und Few-Shot sowie Negativbeispielen
- **ELLMO**: Terme und Typen
- **Chausson & Ross**: Claims

### 3 · Bündeln und Kanonisieren

Das Kernproblem der offenen IE: „gründete“, „rief ins Leben“ und „war Gründer von“ sollen _eine_ Relation werden.

- **Chausson & Ross**: Claims werden zu einem Katalog zusammengeführt („catalogue“)
- **ELLMO**: Clustering und Vektordatenbanken grenzen die Kandidaten ein
- _Lücke:_ Kein Text behandelt **Entity Linking auf Normdaten** wie GND oder Wikidata. Hier passt DeepEL aus deiner ersten Auswahl als Baustein.

### 4 · Schema-Induktion: von offen zu strukturiert

- **ELLMO**: Typen und Beziehungen zwischen Typen, also Ontology Learning
- **Oarga et al.**: Ontologie und KG zero-shot, end-to-end
- **MOIE-KG**: Ontologie als _dynamische_ Zwischenrepräsentation; neue Typen werden kontrolliert in das Schema übernommen („controlled type projection“). Das ist die Brücke zur geschlossenen IE.

### 5 · Graph bauen, verifizieren, evaluieren

- **MOIE-KG**: eigene Agenten für „verification and repair“
- **Oarga et al.**: Evaluation, indem eine _bestehende_ Ontologie nachgebaut wird
- **Chausson & Ross**: Precision/Recall gegen manuelle Annotation, Fehleranalyse
- **Organising Knowledge**: Zusammenführen mit einem bestehenden Domänen-KG

### 6 · Nutzung und Anreicherung

- **Organising Knowledge**: TransE-Embeddings und Relationsvorhersage. Ausgewertet wird, welche Prädikat-Kategorien dazu am meisten beitragen.
- **Chausson & Ross**: Netzwerkanalyse (Echokammern, Polarisierung)

## Übersicht als Matrix

● = Schwerpunkt · ○ = wird mitbehandelt

|Text|0|1|2|3|4|5|6|
|---|---|---|---|---|---|---|---|
|Vo & Bagheri|●||●|||||
|Kamp et al.|●||●||||○|
|Organising Knowledge|||●|||○|●|
|Chausson & Ross||●|●|●||●|○|
|ELLMO|||●|●|●|||
|Oarga et al.|||○||●|●||
|MOIE-KG||●|○|○|●|●||

## Was die Ordnung zeigt

- **Schritt 2 ist gut belegt, Schritt 3 kaum.** Genau dort liegt die bekannte Schwäche offener IE: Die Tripel bleiben bruchstückhaft und uneinheitlich. Die Literatur dazu heißt meist _OIE canonicalization_. Danach könntest du gezielt suchen.
- **Schritt 4 ist der Übergang zur geschlossenen IE.** Die Pipeline endet faktisch bei einem Schema. Damit schließt sich der Kreis zu deiner Frage von vorhin: Offene IE kann der Weg _zur_ Ontologie sein, die man für geschlossene IE braucht.
- **Provenienz fehlt durchgehend.** Keiner dieser Texte sagt, wie ein Tripel an seine Textstelle gebunden bleibt. Dafür sind Vogeler, Alassi und ATAG zuständig, als Querschnittsthema für alle Schritte.