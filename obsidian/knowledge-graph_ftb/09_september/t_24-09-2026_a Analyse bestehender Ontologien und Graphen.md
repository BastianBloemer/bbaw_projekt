# Thesaurus != Taxonomie?

Ich bin darauf gekommen, dass es neben den Ontologien der DNB oder von Wikidata wahrscheinlich noch spezialisierte Ontologien zu einzelnen wissenschaftlichen Fächern und Feldern geben wird. Ein Beispiel ist ChEBI, eine Datenbank von chemischen Entitäten. Ich habe gerade allerdings Probleme, mir die Ontologie herunterladen und zu analysieren. Mein Firefox stürzt dann immer ab. In einem Chat mit Claude erfahre ich aber, dass ChEBI wirklich nur eine Ontologie oder ein Datenbank-Modell für chemische Entitäten ist. Entitäten wie beispielsweise ein einzelnes Wassermolekül unter meinem Mikroskop sind natürlich nicht Teil des Modells. Dies ist letztendlich auch bei der DNB und bei Wikidata der Fall. Aber die DNB und Wikidata sind eben nicht nur Datenbank-Modelle sondern mit Inhalt gefüllt Datenbanken.

Bei der DNB gibt es Entiäten wie Personen und Orte. Ich habe am 22-09-2026 geschrieben, dass die GND *Gold* als ein Sachbegriff enthält. *Gold* und *Edelmetalle* sind im Unterschied zu ChEBI keine eigenen Klassen. Der Grund dafür ist, dass die GND eher ein SKOS-artiger Thesaurus ist mit der Funktion Begriffssysteme zu modellieren. ChEBI ist dagegen eine Taxonomie, bei der fachliche Begriffe selbst als Klassen und nicht als Instanzen modelliert sind.

Im Gegensatz zu Claude steht auf https://www.w3.org/2004/02/skos/intro aber eine Beschreibung von SKOS als ein Standard für die Entwicklung sowohl von Theausri als auch von Taxonomien.

> SKOS is an area of work developing specifications and standards to support the use of knowledge organization systems (KOS) such as thesauri, classification schemes, subject heading systems and taxonomies within the framework of the Semantic Web.

Claude reagiert darauf aber so, dass SKOS Teil der Bibliothekswelt ist und in dieser Welt der Begriff Taxonomie anders verwendet wird als in der Welt der Ontologien. Das führt mich nun zu der wichtigen Frage, ob ich einen Thesaurus oder eine Taxonomie als Datenbank für die *digitalen Akademieschriften* gebrauchen soll.

# historische oder zeitgenössische oder keine Ontologie?

Ich frage mich, ob ich auf bestehende zeitgenössische Ontologien wie die von ChEBI zurückgreife oder ob ich eine LLM nutze und auf der Basis der digitalisierten Akademieschriften eine historische Ontologie erzeugen lasse. Diese induzierte Ontologie könnte man dann mit den zeitgenössischen Ontologien in einen Zusammenhang bringen.






