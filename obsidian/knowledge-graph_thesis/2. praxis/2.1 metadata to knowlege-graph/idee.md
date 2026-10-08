# Woher kommen die Metadaten?

Die Metadaten zu den digitalisierten Akademieschriften, die ich zu einem ersten Wissensgraphen verarbeiten will, kommen ursprünglich aus dem OPAC der BBAW. Wer oder im Rahmen welchen Projektes die Metadaten erzeugt wurden weiß ich bisher noch nicht. Ich selbst hatte die Metadaten im Rahmen meines Praktikums heruntergeladen und kuratiert.

# Welche Informationen stecken in den Metadaten?

Da die Metadaten hauptsächlich strukturierten Informationen bestehen, müssen Klassen wie Dokument, Person, Titel oder Jahr nicht extrahiert werden. Sie können *einfach* übernommen werden. Ich muss mir aber überlegen, in welche Ontologie ich die Informationen hineingebe. Soll es beispielsweise heißen "*Person hat geschrieben Dokument*" oder "*Dokument wurde geschrieben von Person*" oder beides? Ich muss mir also überlegen, in welche Klassen- und Beziehungstypen ich die Informationen hineingebe.

Die Metadaten enthalten mit *wissenschaftliche Klasse* und *Anhang* zwei Kategorien, von denen ich glaube, dass die Einträge unvollständig sind. Ich muss mir überlegen, wie ich damit umgehe, ob ich beispielsweise die Klassenzuordnung der Dokumente erst vornehme, wenn ich ein OCR von den Inhaltsangaben der Bände habe. Ich muss mich auch Fragen, wie ich damit umgehe, dass sich die wissenschaftlichen Klassen im Laufe der 200 Jahre ausdifferenzieren.

Die Titel sind in sich unstrukturiert und aus ihnen können deshalb Informationen extrahiert werden. Hier muss ich mich Fragen, wie ich herausbekomme, welche Informationstypen sich extrahieren lassen. Ich muss mich Fragen, ob ich die Typen durch eine Analyse der Titel erschließe und sie dann aus den Titeln emergieren, oder ob ich eine bestehende Ontologie als Muster nehme. Ich muss mich außerdem Fragen, wie ich deterministische und statistische Methoden miteinander kombiniere.

# Woher kommt die Ontologie und brauche ich überhaupt eine?

In einer Ontologie werden die Regeln definiert, welche Klassen- und Beziehungen es gibt sowie welche Klassen miteinander in welchen Beziehung stehen dürfen. Ich muss mir die Frage stelle, ob ich eine bestehende Ontologie nachnutzt und wenn ja, auch welcher Ebene. Mit einer bestehenden Ontologie könnte ich die beispielsweise auch die Informationsextraktion aus den Titel steuern und vorgeben, was überhaupt gefunden werden darf. Ich fände das nicht den richtigen weg, wenn ich die Titel manuell analysieren würde. Aber da ich mit einem LLM arbeite, könnte mir eine bestehende Ontologie Kontrolle geben. 

Andersherum könnte ich auch erst im nachhinein eine Ontologie erzeugen. Dann würde man erst *offen* und *frei* die Informationen aus den Metadaten übernehmen und extrahieren, in Klassen einteilen und in Beziehungen setzen lassen. In einem zweiten Schritt würde man dann prüfen, welche Ontologie aus den Daten emergiert. Die emergierende Ontologie könnte man dann evaluieren und gegebenenfalls die Daten nachkuratieren.

# Wie wird der Wissensgraph evaluiert?

Wenn ich eine vorher konstruierte Ontologie in den Wissensgraphen mit seinen konkreten Entitäten einbinde, kann ich seine Validität prüfen. Wenn der Graph nicht valide ist, gibt es meistens Fehler in den Daten. Grundsätzlich ist es aber auch möglich, dass die Ontologie nicht zu den Informationen passt, die sich aus den Metadaten übernehmen und extrahieren lassen. 

Ich muss hauptsächlich eine gute Evaluierungsmethode für die von einer LLM aus den Titeln extrahierten Informationen finden. Hier reicht aber die Prüfung der Validität nicht aus, da die Validität nur eine Übereinstimmung mit den Regeln der Ontologie spiegelt. Ich muss aber prüfen, ob die Informationen, die die LLM in den Titeln gefunden hat, auch wirklich in den Titeln enthalten waren und die LLM nicht halluziniert hat. Hierfür müsste ich vielleicht Stichproben nehmen oder nochmal eine andere LLM das gegenchecken lassen. Außerdem sollte ich die Herkunft meiner Informationen in den Wissensgraphen mit aufnehmen und die Beziehung *erzeugt von*  sowie die Klassen *LLM* und *Deterministisches Skript* verwenden.

Am Ende sollte ich auch ein prototypisches Interface zur Evaluation bauen. Ich habe bei der Entwicklung der bisherigen Webanwendung für die digitalisierten Akademieschriften gelernt, dass ein Interface noch einmal eine neue Perspektive auf die Datenbank ermöglicht und auch Lücken und Fehler zeigen kann. Ich sollte darauf achten, ein solches Interface nicht zu spät zu entwickeln.

# Was bringt der Wissensgraph 1.0?

Der auf den Metadaten allein beruhende Wissensgraph sollte auf der Ebene des Interfaces übersichtliche und dadurch nützliche Filter ermöglichen. Durch die im Wissensgraph abgelegten Beziehungen können Dokumente nicht nur über auf Entitäten beruhende Registereinträge wie Personen, wissenschaftliche Klassen, Jahre und Begriffe gesucht werden, sondern die Entitäten selbst können über ihre Eigenschaften bestimmt werden. Eine Suche wäre beispielsweise *Dokumente von Autoren die in mehr als einer wissenschaftlichen Klasse publiziert haben*. Ich erwarte, dass der Wissensgraph 1.0 genügend dünn ist, dass keine komplexe Abfragesprache nötig ist und wirklich ein Filterinterface gestaltet werden kann.

Den Wissensgraphen 1.0 als Zwischenschritt wirklich zu entwickeln kann außerdem einen Vergleich zu dem Wissensgraphen ermöglichen, der dann aeine LLM-getriebenen Informationsextraktion einer schmutzigen OCR und CV zu seiner Grundlage hat. Vielleicht ist es sogar sinnvoll, den Wissensgraphen 1.0 in zwei Schritten zu entwickeln und einen ersten Graphen allein auf die Grundlage deterministischer Informationsextraktion zu stellen.

