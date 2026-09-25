Um die Inkonsistenzen in den Seiteninformationen zu beheben, bin ich nochmal einen Schritt zurück gegangen und habe die json-Dokumente in Dataframes verwandeln, die die Daten in Form von flachen Tabellen speichern, wodurch man sie mit Python besonders leicht bearbeiten kann. 

Am Anfang habe ich versucht mit einem [Dataframe](https://pandas.pydata.org/docs/) zu arbeiten, das die Daten zu allen Schriftenreihen enthielt. Da es mir schwer viel, bei einer solchen Menge die Fehler und Muster in den Daten zu überschauen und zu verstehen, habe ich mich dazu entschieden, für jede der 10 Schriftenreihen ein einzelnes Dataframe zu erstellen. An diesen Dataframes habe ich dann mit Python herumexperimentiert, versucht die Seiteninformationen in den Einträgen zu finden, zu korrigieren und an die richtige Stelle zu bringen. Ich brauchte ein bisschen, um mich an die Arbeit mit den Dataframes zu gewöhnen, zu verstehen wo die Informationen in den Tabellen stehen und zu sehen, dass bei manchen Einträgen auch schon in den ris-Dokumenten die Seiteninformationen einfach fehlten. Ich hätte besser ganz zu Beginn meiner Arbeit die ris-Dokumente einmal analysiert, anstatt direkt mit ihnen zu arbeiten.




