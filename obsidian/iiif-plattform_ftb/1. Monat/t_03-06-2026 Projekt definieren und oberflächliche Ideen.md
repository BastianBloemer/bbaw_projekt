Bei einem ersten Meeting mit Herrn Schnöpf und Frau Seidig haben wir die Aufgabe für mein Praktikum definiert. Diese Aufgabe wird sein, die [digitale Sammlung der Akademieschriften]((https://bibliothek.bbaw.de/digitalisierte-sammlungen/akademieschriften) weiterzuentwickeln. Das Projekt lässt sich in zwei Teile zergliedern:

- Weiterentwicklung der Präsentations-Ebene mit Orientierung an dem Corporate Design der BBAW ((siehe [EDOC](https://edoc.bbaw.de/home))
- Erstellung einer Transkription zu den Dokumenten mit dem Ziel, eine Volltext-Suche zu ermöglichen

Im Gespräch mit Herrn Schnöpf haben wir festgelegt, dass wir [IIIF-Manifeste](https://iiif.io/) erstellen wollen. Später können wir dann einen Viewer in die Präsentations-Ebene einbauen, der diese Manifeste liest, die Bilder der Akademieschriften in einer Bilderdatenbank findet und anzeigt sowie Funktionen wie Zoomen usw. ermöglicht. In den IIIF-Manifesten wollen wir neben dem Link zur Bilddatenbank auch die bibliographischen Metadaten zu den verschiedenen Abhandlungen und Sitzungsberichten in den Akademieschriften hineinschreiben. Meine erste Aufgabe wird es daher sein, diese Daten zu sammeln und zu strukturieren.

Als Orientierung für das Webdesign habe ich mir die Digitale Sammlung der [Stabi](https://digital.staatsbibliothek-berlin.de/,) sowie anderer Wissenschaftsakademien angeschaut. Dabei hat sich für mich folgende Architektur für das Frontend ergeben:

- Startseite 
	- Schnellsuche
	- Kachel-Ansicht zu den Bänden oder zu den Klassen (vgl. [Philosophisch-Historisch](https://digi.hadw-bw.de/view/sbhadwphkl))
- Ergebnisliste
	- Listenansicht und Ergebniskacheln
	- Filter-Sidebar mit Facettensuche (z.B. [Historische Systematik des Alten Realkataloges](https://ark.staatsbibliothek-berlin.de/))
- IIIF Viewer
	- Inhaltsverzeichnis
	- Metadatenpanel
	- Seitennavigation
	- Zoom-Steuerung

- Downloadoptionen?
- Personendatenbank? (vgl. [Personendatenbank](https://archiv.saw-leipzig.de/personen))