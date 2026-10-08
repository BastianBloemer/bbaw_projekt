Claude hat nun eine erste kleine Pipeline aus sechs Python-Skripten gebaut, um den KG 1.0 zu erzeugen.
# Reinigung/Kuration der bibliographischen Metadaten
Die Metadaten scheinen noch nicht ganz sauber zu sein. Auch nach der Reinigung scheint es noch Jahreszahlen zu fehlen und Claude schreibt auch von 21 anonymen Abhandlungen, also fehlenden Autor:innen. Diese Reinigungen sollten aber nicht in der KG 1.0 Pipeline gemacht werden, sondern noch in der iiif-plattform-Pipeline. Dort liegen die Metadaten und dort sollten sie auch gereinigt werden. Ich werde das Skript daher verschieben und die Reinigung dort vornehmen und eventuell auch Dinge ergänzen, die Claude nicht ergänzen konnte.
# Deterministische Extraktion von Informationen aus Titeln
Mit einem rein regelgeleiteten Python-Skript sollen erste Informationen über die Abhandlungen aus den Titeln extrahiert werden. Die Informationstypen sind 
- Sprache
- Teile wie Auszug (wobei ich hier einschreiten muss, da die Auszüge die Berichte sind), 
- Gattungen wie Nachrufe, Antrittsrende, Beobachtung usw. (Claude hat 14 Gattungen definiert, die ich überprüfen sollte)
- Mitautoren
- Datumsangaben (muss ich prüfen)
- Anlässe wie Festreden zum Geburtstag des Monarchen
# LLM-getriebene Extraktion von Informationen aus Titeln
Das LLM-Skript muss ich am Ende mit der OpenAI-API der BBAW koppeln. Das Modell soll  folgendes extrahieren
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

Der von Claude geschriebene Prompt geht wie folgt:

>Du bist Wissenschaftshistoriker:in und erschließt die Schriften der \ Berliner Akademie der Wissenschaften (1710–1900). Du bekommst den Titel einer \ Abhandlung mit Kontext und extrahierst strukturierte Angaben für einen Wissensgraphen.
	 Regeln:
		 - Extrahiere nur, was im Titel steht oder aus ihm unmittelbar folgt. Erfinde nichts.
		- Der Autor der Abhandlung gehört NICHT in "personen", auch nicht Mitautoren oder \ Kommentatoren, die bereits unter "Regelanalyse" stehen.
		- Personen, Orte und Werke in der heute üblichen Ansetzungsform (GND-Stil: \ "Nachname, Vorname"; Orte mit heutigem deutschen Namen), die historische Schreibung \ kommt in "im_titel".
		- "themen": 1–5 Schlagwörter auf Deutsch, möglichst als GND-Sachbegriffe \ (z.B. "Elektrizität", "Sonnenfinsternis", "Inschrift").
		- Titel in Latein, Französisch oder historischem Deutsch: "titel_de" ist eine \ knappe moderne deutsche Wiedergabe.
		- Leere Listen bzw. leere Zeichenketten, wenn nichts zutrifft

Der Prompt ist sehr sehr knapp und ich weiß nicht, ob das gut oder schlecht ist. 

# Verlinkung von Informationen mit GND/Wikidata
Das **NEL** mit der GND soll tatsächlich auch deterministisch stattfinden. Dabei werden über eine API mögliche Kandidaten aus der GND herausgesucht. Bei Personen werden diese Kandidaten beispielsweise hauptsächlich über mögliche Berufe gefiltert und ein Ähnlichkeitswert vergeben. Wenn es mehrere Personen gibt, die einen bestimmten Ähnlichkeitswert übersteigen, dann wird ein Eintrag in einer Review-Tabelle angelegt, die dann noch von Menschen angeschaut werden muss und eben diejenigen Namen enthält, bei denen die deterministische Zuordnung zu keinem klaren Ergebnis gekommen ist.

Das Matching von Personen mit ihrem GND (oder auch Wikidata)-Eintrag ermöglicht später eine Art Personenkatalog anzulegen und Informationen über die Mitglieder der Akademie zu präsentieren. Aber bietet das wirklich einen Mehrwert, wenn die Suche der Person in Wikipedia o.ä. nur einen Klick entfernt ist?

# Konstruktion & Evaluation des Graphen

Das Konstruktions-Skript verstehe ich nicht unmittelbar und ich muss es noch einmal eingehender studieren. Das Evaluations-Skript prüft den konstruierten Graphen mit  SHACL-Schemen. SHACL-Shapes sind ein Regelset, dem KGs entsprechen können/müssen. Sturkturmerkmale oder Zeilen, an denen der KG der SHACL-Grammatik wiederspricht, werden als Fehler oder als Lücken angezeigt. Es erinnert mich ungefähr an das, was in der Oxygen-Software passiert, wenn man dort in ein Dokument ein Schema einbindet. In Oxygen wird dann die Validität geprüft. Außerdem prüft Oxygen noch die Wohlgeformtheit eines Dokumentes, aber nicht auf der Grundlage eines eingebundenen Schemas sondern weil Dokumententypen selbst an sich eine bestimmte Syntax haben. Ein Dokument ist also Wohlgeformt, wenn es die grundlegenden Syntaxregeln der Sprache erfüllt, in der es geschrieben ist. Ein Dokument ist Valide, wenn es auch den zusätzlich eingebundenen Schemata entspricht, die inhaltliche Regeln geben.

