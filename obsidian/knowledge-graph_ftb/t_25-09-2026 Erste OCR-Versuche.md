Ich entscheide mich dazu mit den ersten OCR-Versuchen zu beginnen. Ich will es erst einmal sehr Low-Key machen und einfach ein LLM um ein OCR bitten. Für die ersten Tests entscheide ich mich dazu mit der Sammlung der deutschen Abhandlungen von 1788 bis 1803 **(samml)** zu starten. Ältere Sammlungen haben gebrochene Schriften. **samml** hat dagegen eine Antiqua-Schrift. Ich gehe einfach davon aus, dass LLMs Antiqua-Schriften besser erkennen können. Außerdem ist das Druckbild von späteren Schriften sauberer, es gibt weniger Druckfehler wie beispielsweise kleine Leerstellen bei den Buchstaben. Allerdings gibt es noch lange S, die bei den Abhandlungen **(abh)** von 1804 bis 1900 nur noch bei ß zu finden sind. Ich hoffe aber, dass das LLM gut mit dem langen S umgehen kann.

Als ich mir die erste Ausgabe von **abh** angeschaut hatte, hatte ich einen kleinen Schock bekommen. Es gibt dort viele mathematische Formeln sowie auch Tabellen und manchmal sogar kleine Abbilder. Ich weiß nicht, wie eine LLM damit umgehen kann. Ich muss das alles austesten, möchte damit aber nicht allzu viel Zeit verbringen. Ein Modell zu trainieren, sollte zumindest nicht nötig sein, da ich keine Handschriften sondern eben einen Druck mit sehr allgemeinem Schriftbild habe




Zuerst muss ich mir ein Skript schreiben, um die Abhandlungen von dem Bildserver herunterzuladen. 