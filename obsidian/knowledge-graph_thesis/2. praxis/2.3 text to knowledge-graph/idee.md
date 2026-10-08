
**Eine Fachontologie für alle Fächer gibt es nicht, aber eine fachübergreifende Ebene schon**

Statt Inhalte (Elemente, Krankheiten, Planeten) zu modellieren, modellierst du die **Wissenspraktiken**, die in fast allen Fächern vorkommen:

- **Aussage/Behauptung** (was wird behauptet, von wem, mit welcher Sicherheit)
- **Beobachtung** und **Experiment/Versuch** (Gegenstand, Verfahren, Instrument, Ergebnis)
- **Messung** (Größe, Wert, Einheit, Bedingungen)
- **Hypothese, Theorie, Erklärung** und die Argumentation dafür oder dagegen
- **Methode, Instrument, Material/Substanz**
- **Bezugnahmen**: widerlegt, stützt, übernimmt, kritisiert

Dafür gibt es Vorbilder, an denen du dich orientieren kannst: CIDOC CRMsci und CRMinf (Beobachtung, Inferenz, Argumentation), die SPAR-Ontologien (z. B. CiTO für Zitationsfunktionen), Nanopublikationen und ORKG als Modell für strukturierte Wissenschaftsbeiträge.

**Darüber ein Fachmodul pro Disziplin, bottom-up entwickelt**

Die fachspezifischen Klassen (z. B. Mineral, Symptom, Himmelskörper, Rechtsinstitut) würde ich nicht vorab festlegen. Sie entstehen pro Fach aus einer Pilotextraktion, am besten mit **Schema-Induktion**: Das LLM extrahiert zunächst relativ frei typisierte Aussagen, du clusterst die vorkommenden Typen und Relationen, und Fachleute bereinigen das Ergebnis. Danach friert du das Schema pro Fach ein und extrahierst gezielt.

**Aussagen nicht als Fakten speichern**

Bei historischen Quellen ist das der wichtigste Punkt. „Phlogiston wird beim Verbrennen frei“ ist keine Tatsache, sondern eine Behauptung von Autor X im Jahr Y. Modelliere deshalb attribuierte Aussagen („X behauptet, dass …“) mit Fundstelle, Originalwortlaut und historischem Begriff. Moderne Zuordnungen kommen als separate, kennzeichenbare Ebene dazu. Sonst baust du einen Wissensgraphen, der historische Theorien stillschweigend in heutiges Wissen übersetzt oder widersprüchlich wird.

**Strukturierte Extraktion und Passagenebene kombinieren**

Eine vollständige Strukturierung wird nicht gelingen und ist auch nicht nötig. Ein tragfähiger Mix:

1. Strukturierte Aussagen und Experimente dort, wo das Schema gut greift
2. Eine typisierte Zusammenfassung pro Abschnitt (z. B. „beschreibt Versuch zu …, Ergebnis …“) als Fallback
3. Einen Embedding-Index über die Passagen für semantische Suche
4. Verlinkung der Aussagen auf die Originalstelle, sodass Nutzende immer zur Quelle kommen

So geht nichts verloren, was das Schema nicht erfasst, und du kannst das Schema schrittweise nachziehen.