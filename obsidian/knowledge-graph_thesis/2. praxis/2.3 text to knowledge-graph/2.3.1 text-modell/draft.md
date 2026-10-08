## Die drei Phasen

**1. Vorher: den Text adressierbar machen**

- Den Text in Segmente mit **stabilen IDs** zerlegen (Absatz, Satz, notfalls Zeichenbereich).
- Hier gehören Vogeler, Alassi und ATAG hin. Sie liefern das Textmodell, auf das man später verweisen kann (Segment-IDs, ENC-Links, Stand-off-Annotation).
- Ohne diesen Schritt hat ein Tripel kein stabiles Ziel, auf das es zeigen könnte.

**2. Während: den Beleg zusammen mit dem Tripel ausgeben**

- Das LLM liefert zu jedem Tripel die **Segment-ID und ein wörtliches Zitat**:
    
    ```json
    {"s": "Leibniz", "p": "gründete", "o": "Societät der Wissenschaften",
     "segment": "abh-1745-03-p12", "evidence": "die Societät der Wissenschaften ins Leben gerufen"}
    ```
    
- Dann **automatisch prüfen**: Steht das Zitat wirklich in diesem Segment? Ein einfacher String-Abgleich reicht und entlarvt viele Halluzinationen. Tripel ohne gültigen Beleg werden verworfen oder markiert.
- MOIE-KG macht etwas Ähnliches mit „evidence-based feedback“.

**3. Nachher: die Belege durch die Pipeline tragen**

- Beim Bündeln und Kanonisieren werden die Belege **gesammelt, nicht ersetzt**. Ein kanonisches Tripel hat dann _n_ Belegstellen.
- Beim Entity Linking bleibt die ursprüngliche Textform erhalten („Societät“ → `gnd:…`).

## Wie man das in RDF modelliert (kurz)

Ein Tripel kann in RDF nicht ohne Weiteres auf sich selbst verweisen. Gängige Lösungen:

- **Named Graphs (TriG):** jedes Tripel oder jede Tripelgruppe in einen eigenen Graphen legen und _über_ den Graphen Aussagen machen. Das passt zu den `.trig`-Dateien, die es im Projekt schon gab.
- **RDF-star:** `<< :Leibniz :gruendete :Akademie >> :belegtDurch :segment_p12 .`
- **W3C Web Annotation** (`oa:TextQuoteSelector`, `oa:TextPositionSelector`): Standard für Stand-off-Verweise auf Textstellen. Das passt gut zum Editionskontext.

Zusätzlich lohnt es sich, zwei Ebenen zu unterscheiden:

- **Beleg-Provenienz:** _Welche Textstelle_ stützt das Tripel?
- **Prozess-Provenienz:** _Wie_ ist es entstanden (Modell, Prompt-Version, Datum, manuell geprüft ja/nein)? Dafür eignet sich **PROV-O**.