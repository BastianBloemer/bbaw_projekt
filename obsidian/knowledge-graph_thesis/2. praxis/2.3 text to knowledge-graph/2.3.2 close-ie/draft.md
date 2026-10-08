### 0 · Schema festlegen oder übernehmen

- **Hayouni et al.**: mehrere _bestehende_ Ontologien zu einem Netz verbinden, also der Fall „Ontologie übernehmen“, nur realistisch mit mehreren
- **Demers**: eine bestehende Ontologie (DoCO) direkt übernehmen
- **ExtracTable**: Nutzer:innen definieren das Schema selbst
- **What's In Your Field**: ein fachübergreifendes Schema wissenschaftlicher Konzepte
- **SciKGExtract**: ein tief verschachteltes Fachschema (65 Properties, 155 Messwert-Knoten)

### 1 · Modell an das Schema anpassen (Trainings- bzw. Beispieldaten)

Ein festes Schema braucht Beispiele dafür, was z. B. eine „Person“ oder ein „Messwert“ im Sinne des Schemas ist.

- **Santoso et al.**: synthetische NER-Trainingsdaten per LLM, wenn kaum annotierte Daten vorhanden sind
- **What's In Your Field**: kommt mit nur 20 annotierten Abstracts aus
- **Galka & Vogeler**: Annotationen werden zwischen Übersetzungen übertragen (FR → DE). Auch so entstehen Annotationen, ohne alles neu von Hand zu machen.

### 2 · Dokumente aufbereiten und Kontext modellieren

- **ExtracTable**: Dokumentvorverarbeitung und Aufbau des Korpus
- **GCN-PCR**: Das Dokument wird als Graph aus Entitäten, Erwähnungen und Sätzen modelliert, einschließlich **Koreferenz**
- **SciKGExtract**: Fehler beim Zerlegen der Prozesse zeigen, wie viel davon abhängt

### 3 · Entitäten erkennen (NER)

- **Galka & Vogeler**: LLM-NER in historischen Ego-Dokumenten; komplexe Personenreferenzen und verschachtelte Entitäten
- **Santoso et al.**: NER bei wenig Ressourcen
- **GCN-PCR**: Erwähnungen als Kandidaten für die Argumente von Ereignissen

### 4 · Relationen, Ereignisse, Slots füllen

Hier liegt die eigentliche Tripel-Extraktion, in unterschiedlicher Komplexität:

- **Galka & Vogeler**: Beziehungen zwischen Personen, also klassische binäre Relationen (Pilot)
- **Demers / What's In Your Field / ExtracTable**: Textinhalte werden Klassen bzw. Schema-Feldern zugeordnet
- **GCN-PCR**: **Ereignisse** mit mehreren Argumenten, also n-stellige Relationen
- **SciKGExtract**: **verschachteltes Slot-Filling**, ein Prozess mit Schritten, Parametern und Messwerten

### 5 · Normalisierung und Entity Linking

- **DeepEL**: Entity Linking auf eine Wissensbasis, LLM-gestützt in jedem Teilschritt
- **SciKGExtract**: Normalisierung über PubChem, die nachweislich jedes Modell verbessert
- **ExtracTable**: nennt Entity Linking ausdrücklich als offene Baustelle

### 6 · Validierung

- **SciKGExtract**: agentische Prüfung und Nachbesserung (F1 steigt von 0,59 auf 0,81)
- **DeepEL**: Selbstvalidierung über den globalen Kontext
- **ExtracTable**: Human-in-the-Loop
- **Hayouni et al.**: Validierung durch Fachleute mit Inter-Annotator-Agreement
- **Demers**: Abgleich mit veröffentlichten Reviews als Ground Truth

### 7 · Integration und Nutzung

- **ExtracTable**: Integration in den ORKG
- **What's In Your Field**: Abfragen über 30.000 Papers, Trends, Visualisierung
- **SciKGExtract / GCN-PCR**: Integration in KG-basierte Systeme

## Übersicht als Matrix

● = Schwerpunkt · ○ = wird mitbehandelt

|Text|0|1|2|3|4|5|6|7|
|---|---|---|---|---|---|---|---|---|
|Hayouni et al.|●||||||●||
|Demers (LIS)|●||||●||○||
|ExtracTable|●||●||○|○|●|●|
|What's In Your Field|●|●|||●|||●|
|SciKGExtract|●||○||●|●|●|○|
|Santoso et al.||●||●|||||
|Galka & Vogeler||●||●|○||||
|GCN-PCR|||●|○|●|||○|
|DeepEL||||||●|●||

## Vergleich mit der offenen Pipeline

||Offene IE|Geschlossene IE|
|---|---|---|
|Schema|entsteht am **Ende** (Schema-Induktion)|steht am **Anfang**|
|Hauptproblem|Tripel bündeln und vereinheitlichen|Text korrekt dem Schema zuordnen|
|Vereinheitlichung|Clustering von Relationsphrasen|Entity Linking, Normalisierung auf Normdaten|
|Evaluation|schwierig, kein Goldstandard|gegen annotierte Daten möglich|
|Zusätzlicher Aufwand|–|Beispiel- und Trainingsdaten|

## Was die Ordnung zeigt

- **Kein Text behandelt, wie man ein Schema von Grund auf entwirft.** Hier werden Schemata übernommen, kombiniert oder selbst gesetzt. Für das klassische Ontology Engineering (Kompetenzfragen, Wiederverwendung von CIDOC-CRM o. Ä.) bräuchtest du eigene Literatur.
- **Schritt 4 reicht von einfach bis komplex.** Binäre Tripel (Galka) sind etwas anderes als Ereignisse (GCN-PCR) oder verschachtelte Prozesse (SciKGExtract). Für n-stellige Strukturen brauchst du in RDF Zwischenknoten. Das ist auch für die Modellierung der Provenienz wichtig.
- **Galka & Vogeler ist für dich der Schlüsseltext.** Er ist der einzige mit historischen, deutsch- und französischsprachigen Editionstexten. Dazu kommt ein Punkt zur Provenienz: Bei NER als **TEI-Annotation** ist die Anbindung an den Text automatisch gegeben, weil die Annotation _im_ Text steht. Das ist die Inline-Variante zu dem, was wir vorhin für die Stand-off-Variante besprochen haben.
- **Validierung ist hier deutlich besser ausgebaut als bei der offenen IE.** Das liegt daran, dass ein festes Schema einen Goldstandard überhaupt erst möglich macht.