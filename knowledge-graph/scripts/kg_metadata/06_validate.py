"""
06 - Validierung und Beispielabfragen
-------------------------------------
1. Prueft akademieschriften.ttl gegen die SHACL-Shapes (shapes.ttl).
   Verletzungen (sh:Violation) sind Fehler, Warnungen (sh:Warning) sind
   bekannte Luecken der Quelldaten.
2. Gibt Kennzahlen zum Graphen aus.
3. Fuehrt alle SPARQL-Abfragen in queries/*.rq aus (Praefixe aus _prefixe.rq).

Der vollstaendige SHACL-Bericht landet in validation_report.txt.

Aufruf:
    python 06_validate.py
    python 06_validate.py --ohne-shacl     # nur Kennzahlen und Abfragen
"""

import argparse
from collections import Counter

from pyshacl import validate
from rdflib import Graph
from rdflib.namespace import RDF, SH

from config import GRAPH_TTL, QUERIES_DIR, SHAPES_TTL, VALIDATION_REPORT
from namespaces import DAS, bind_all

KENNZAHL_KLASSEN = ["Abhandlung", "Person", "Schriftenreihe", "Band", "Jahr",
                    "Gattung", "Anlass", "Disziplin", "Thema", "Ort", "Werk"]


def shacl(daten):
    shapes = Graph().parse(SHAPES_TTL, format="turtle")
    konform, bericht_graph, bericht_text = validate(
        daten, shacl_graph=shapes, inference="none", allow_warnings=True)
    VALIDATION_REPORT.write_text(bericht_text, encoding="utf-8")

    zaehler = Counter()
    for ergebnis in bericht_graph.subjects(RDF.type, SH.ValidationResult):
        schwere = bericht_graph.value(ergebnis, SH.resultSeverity).split("#")[-1]
        meldung = bericht_graph.value(ergebnis, SH.resultMessage)
        zaehler[(schwere, str(meldung))] += 1

    print(f"SHACL konform (ohne Warnungen): {konform}")
    for (schwere, meldung), n in sorted(zaehler.items()):
        print(f"  {schwere:10} {n:>6}  {meldung[:100]}")
    print(f"  Vollstaendiger Bericht: {VALIDATION_REPORT.name}")
    return not any(s == "Violation" for s, _ in zaehler)


def kennzahlen(daten):
    print(f"Tripel: {len(daten)}")
    for klasse in KENNZAHL_KLASSEN:
        n = len(set(daten.subjects(RDF.type, DAS[klasse])))
        if n:
            print(f"  das:{klasse:15} {n:>6}")


def abfragen(daten):
    prefixe = (QUERIES_DIR / "_prefixe.rq").read_text(encoding="utf-8")
    for pfad in sorted(QUERIES_DIR.glob("[0-9]*.rq")):
        text = pfad.read_text(encoding="utf-8")
        titel = text.splitlines()[0].lstrip("# ")
        print(f"\n== {pfad.name}: {titel}")
        ergebnis = list(daten.query(prefixe + text))
        if not ergebnis:
            print("   (keine Ergebnisse)")
        for zeile in ergebnis[:10]:
            werte = [daten.namespace_manager.normalizeUri(v) if hasattr(v, "startswith") and str(v).startswith("http")
                     else str(v) for v in zeile]
            print("   " + " | ".join(w[:70] for w in werte))
        if len(ergebnis) > 10:
            print(f"   ... ({len(ergebnis)} Zeilen)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ohne-shacl", action="store_true")
    args = ap.parse_args()

    daten = bind_all(Graph()).parse(GRAPH_TTL, format="turtle")
    kennzahlen(daten)
    ok = True
    if not args.ohne_shacl:
        ok = shacl(daten)
    abfragen(daten)
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
