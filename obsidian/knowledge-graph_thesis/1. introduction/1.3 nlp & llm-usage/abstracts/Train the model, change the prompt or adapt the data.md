**Autor:**  Rodrigues
**Datum:** 2025-07-11

**Zusammenfassung**

KI-Generiert

Wie lassen sich große Sprachmodelle (LLMs) an reale, oft unstrukturierte Anwendungsdaten anpassen, ohne sie aufwendig neu zu trainieren? Dieser Beitrag fasst den Vortrag von Prof. Dr. Roman Klinger (Universität Bamberg) zusammen, den er am 22. Mai 2025 an der Universität zu Köln gehalten hat. Ich stelle die drei Strategien vor, die er unterscheidet: das Modell fein justieren (train the model), die Eingabeanweisung anpassen (change the prompt) und den Input in eine geeignetere Form bringen (adapt the data).

Anhand von zwei Projekten zeige ich, wie die beiden letzten Strategien funktionieren. MOPO (Multi-Objective Prompt Optimization) optimiert Prompts per evolutionärem Verfahren und Pareto-Auswahl gleichzeitig für mehrere Kontexte, etwa Nachrichtenüberschriften und Social Media. So entstehen emotionale Texte, die in beiden Domänen funktionieren. Das zweite Projekt (Wührl und Klinger) formuliert umgangssprachliche Social-Media-Aussagen mit Direct Preference Optimization so um, dass ein Fact-Checking-Modell sie besser prüfen kann, und zwar ohne manuell annotierte Trainingsdaten.

Ich vergleiche beide Ansätze und skizziere offene Fragen für die weitere Forschung. Mein Fazit: Gezielt gestaltete Eingaben statt mehr Rechenleistung verbessern die Ergebnisse oft deutlich, bei geringerem Aufwand und höherer Interpretierbarkeit.