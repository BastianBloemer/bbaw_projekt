# Claude-Notizen zu diesem Ordner

Ergänzt `readme.md` (die Notizen des Nutzers) um die technischen Details, damit eine spätere Session hier nahtlos weitermachen kann.

## Herkunft der Daten

Quelle: `knowledge/zotero/zotero.sqlite` (Zotero-Datenbank), Stand 06.08.2026. Da die Datei während laufendem Zotero gesperrt sein kann, wird für Auswertungen immer eine Kopie verwendet, nie die Live-Datei direkt gelesen/beschrieben.

`export_zotero.py` (in diesem Ordner) extrahiert alle Top-Level-Literatureinträge (also ohne Notizen, Attachments und PDF-Annotationen) aus **beiden** Bibliotheken — persönliche Bibliothek und Gruppen-Bibliothek "dh_unibe" — inkl. Titel, Autor:innen, Jahr, Zeitschrift/Verlag, DOI, URL, Abstract, Tags und Sammlungen. Ergebnis: 2608 Einträge, siehe `insgesamt.json`.

Zum erneuten Ausführen: Pfade in `DB` und `OUT` am Kopfende des Skripts anpassen (aktuell zeigen sie auf einen Scratchpad-Pfad einer alten Session), dann `python3 export_zotero.py`.

## Relevanz-Klassifikation (relevant.json / nicht_relevant.json)

Vorgehen (auf Wunsch des Nutzers explizit **nicht** anhand von Tags/Sammlungen, sondern inhaltlich):
1. Aus Zeitgründen bei 2608 Einträgen zunächst nur **Titel** verwendet, keine Abstracts (das wäre der nächste Verfeinerungsschritt, siehe unten).
2. Liste in 4 Blöcke à ~652 Einträge gesplittet, 4 parallele Agents haben je einen Block bewertet (binär: relevant/nicht relevant).
3. Kriterium pro Agent-Prompt: Relevanz für die Masterarbeit "Semantische Erschließung mit Wissensgraphen" — Themenfelder waren Wissensgraphen, Semantic Web, Ontologien, RDF/OWL, Linked (Open) Data, SPARQL, Named Entity Recognition/Linking, Informationsextraktion, kontrollierte Vokabulare/Thesauri, Metadatenmodellierung, CIDOC-CRM, Wissensrepräsentation, semantische Erschließung von Bibliotheks-/Archivbeständen, Text Mining, Entity Resolution, automatische Verschlagwortung, DH-Datenmodellierung mit Semantikbezug.
4. Bewusst **inklusiv** eingestellt (Grenzfälle eher "relevant"), ausgeschlossen wurden nur klar fachfremde Titel (z.B. reine Archäologie-Grabungsberichte, reine Kunstgeschichte/Theologie ohne Digital-/Semantikbezug).
5. Was "Relevanz" genau bedeutet, wurde nicht weiter definiert (Notiz des Nutzers in `readme.md` — wichtige Einschränkung für die Interpretation der Ergebnisse).

Ergebnis: 555 relevant, 2053 nicht relevant.

## Offene Punkte / Stand 06.08.2026

- 555 relevante Einträge sind dem Nutzer für die Masterarbeit zu viele — weitere Eingrenzung nötig, aber noch nicht entschieden wie.
- **Wichtig:** Nutzer möchte **nicht** nach Publikationstyp filtern (z.B. Blogposts raus) — Blogposts gelten für ihn als zitierfähige Quellen für diese Arbeit.
- Nächster naheliegender Verfeinerungsschritt: jetzt, bei nur noch 555 statt 2608 Einträgen, wäre eine inhaltliche Bewertung inkl. Abstracts (wo vorhanden) machbar — z.B. mit einer 3-Stufen-Skala (hoch/mittel/niedrig) statt binär.
- Alternative/ergänzende Hebel, die besprochen, aber noch nicht umgesetzt wurden: thematisches Clustering mit Obergrenze pro Cluster, Aktualitäts-Filter (z.B. letzte 10–15 Jahre).
- Nutzer-Ideen aus `readme.md`: bei wachsender Zotero-Bibliothek künftig nur neu hinzugekommene Titel bewerten lassen, oder eine eigene Zotero-Sammlung "Semantische Erschließung mit Wissensgraphen" für die als relevant markierten Titel anlegen.
