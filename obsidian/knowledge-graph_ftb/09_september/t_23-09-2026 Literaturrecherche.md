
ÜBRIGENS: Ich baue eine **Volltext-Datenbank**. Ich möchte den Textkorpus in neue Ordnungen bringen und beispielsweise die Werke nach Ähnlichkeit gruppieren. Das Problem wird hier vor allem sein, die Metadaten zu finden oder zu konstruieren.

https://tedunderwood.com/2015/06/04/seven-ways-humanists-are-using-computers-to-understand-text/#bib
Ein zentrales Konzept ist das Konzept der **Modellierung**. Es gibt verschiedene Typen von Modellen, z.B. statistische Modelle. Statistische Modelle sind meistens Gleichungen, die die Wahrscheinlichkeit einer Assoziation zwischen Varianbeln beschreiben. Die Antwort-Variable ist die Variable, die man verstehen will. Die Prediktor-Variablen sind die Dinge von denen man glaubt, dass sie das Verstehen oder Vorhersagen helfen.
- Man könnte nun Aspekte von Texten auswählen, messen und dann für die Bedeutung davon argumentieren
- Ein anderer Weg wäre, ein Konzept zu identifizieren, das man verstehen will, und dieses Konzept dann zu modellieren. 

Ted Underwood spricht vor allem von statistischen Modellen. Ein Wissensgraph ist aber kein statistisches Modell. Ein Wissensgraph ist vielmehr ein strukturelles Modell.

Gibt es eine Spannung zwischen Modellierung zum Erklären und Modellierung zum Vorhersagen? https://www.stat.berkeley.edu/~aldous/157/Papers/shmueli.pdf


Ich lese in https://tedunderwood.com/2011/02/06/why-search-was-the-killer-app-in-text-mining-and-what-we-might-learn-from-it/#comments, dass Suchalgorithmen komplex sind, dass sie diese Komplexität verstecken, dass sie verschiedene statistische Gewichte verschiedenen Terms zuordnen, dass sie auf verschiedenen Annahmen über die Beziehung zwischen Wörtern und Dokumenten basieren.

Könnte die Analyse von Konkordance mit z.B. antconc nützlich für mich sein? Ich hätte dann eine Liste mit Worten, die einzeigt, wie häufig diese Worte vorkommen, und ebenso, in welchem Kontext zu vorkommen.

Ich muss mir laut https://tedunderwood.com/2015/06/04/seven-ways-humanists-are-using-computers-to-understand-text/#bib zwei Fragen stellen. Erstens, wie repräsentiere ich die Texte? Zweitens, was mache ich mit diesen Repräsentationen? Also, wie können Texte repräsentiert werden?:
- Z.B. durch Bag of Words (Zahlen der Wörter) -> Themen können auf dem Level von Wortentscheidungen registriert werden
- Zählen von Two-Word-Phrases
- Qualitative Informationen, die nicht gezählt werden können, können als Categoriale Variabel repräsentiert werden
- siehe auch https://www.nltk.org/

**OK! VIELLEICHT KÖNNTE MEINE EIGENTLICHE AUFGABE ES SEIN, ENTITÄTEN IN DEN DOKUMENTEN ZU ERKENNEN UND MIT DEM WIKIDATA-WISSENSGRAPH ZU VERLINKEN**

Mit der DHQ muss ich besonders umgehen. Dort kann ich nämlich eine Volltextsuche in allen Artikeln machen. Ich behandel die DHQ deshalb erstmal als ein Werk

