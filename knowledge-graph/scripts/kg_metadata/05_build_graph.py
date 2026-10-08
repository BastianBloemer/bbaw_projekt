"""
05 - Aufbau des Wissensgraphen (RDF)
------------------------------------
Fuehrt die Ergebnisse von 01-04 zu einem RDF-Graphen zusammen.

Provenienz ueber Named Graphs:
    graph:ontologie  Inhalt von ontology.ttl
    graph:katalog    Fakten aus merged_df.csv (Titel, Autor, Band, Jahr, Relationen ...)
    graph:regeln     Ergebnisse der Regelanalyse der Titel (02)
    graph:llm        Ergebnisse der LLM-Analyse der Titel (03), falls vorhanden
    graph:gnd        Verknuepfungen mit GND/Wikidata (04), falls vorhanden

Ausgabe:
    akademieschriften.trig   alle Named Graphs (mit Provenienz)
    akademieschriften.ttl    Vereinigung aller Graphen (einfacher zu laden)

Alle Stellen, an denen ein externes Vokabular direkt verwendet wird, sind mit
NAMESPACE-HOOK markiert. Die Zuordnung der das:-Klassen/Properties zu externen
Vokabularen steht in ontology.ttl. Mit MATERIALISIEREN = True werden die dort
deklarierten Oberklassen/-properties zusaetzlich in die Daten geschrieben, so
dass z.B. auch eine Abfrage nach fabio:JournalArticle ohne Reasoner funktioniert.

Aufruf:
    python 05_build_graph.py
"""

import json
import re
from datetime import datetime, timezone

import pandas as pd
from rdflib import Dataset, Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, TIME, XSD

from config import (ABHANDLUNGEN_CSV, AUTOREN_CSV, AUTOREN_GND_CSV, ENTITAETEN_GND_CSV,
                    GRAPH_TRIG, GRAPH_TTL, ONTOLOGY_TTL, RELATIONEN_CSV, REIHEN_CSV,
                    TITLE_LLM_JSONL, TITLE_RULES_JSONL, slugify)
from namespaces import (DAS, FABIO, GND, GRAPH, ISO639, K10PLUS, PRISM, PROV, RES, SCHEMA,
                        WD, bind_all)

# ---- Konfiguration --------------------------------------------------------

MATERIALISIEREN = True   # Oberklassen/-properties aus ontology.ttl in die Daten schreiben

# Spalte "Textbeziehungen" -> Property (Lesart: Bezeichnung = Rolle des Ziels)
RELATION_PROPERTY = {
    "Verweis": DAS.verweistAuf,
    "Fortsetzung": DAS.hatFortsetzung,
    "Hauptteil": DAS.hatHauptteil,
    "Nachtrag": DAS.hatNachtrag,
    "Auszug": DAS.hatAuszug,
    "Volltext": DAS.hatVolltext,
    "Übersetzung": DAS.hatUebersetzung,
    "Original": DAS.hatOriginal,
    "Antwort": DAS.hatAntwort,
    "Antrittsrede": DAS.hatAntrittsrede,
}

BETEILIGTE_PROPERTY = {
    "mitautor": DAS.mitautor,
    "kommentator": DAS.kommentator,
    "vorwort": DAS.vorwort,
    "brief": DAS.briefschreiber,
    "mitwirkung": DAS.mitwirkung,
}

# Bezeichnungen der Gattungen / Anlaesse (Schluessel aus 02_title_rules.py)
GATTUNG_LABELS = {
    "nachruf": "Nachruf / Gedächtnisrede", "antrittsrede": "Antrittsrede",
    "antwort": "Antwort auf Antrittsrede", "festrede": "Festrede / Rede",
    "bericht": "Bericht / Gutachten", "beobachtung": "Beobachtung",
    "brief": "Brief", "untersuchung": "Untersuchung", "versuch": "Versuch / Experiment",
    "bemerkung": "Bemerkung", "beschreibung": "Beschreibung", "mitteilung": "Mitteilung",
    "beitrag": "Beitrag", "memoire": "Mémoire / Abhandlung",
}
ANLASS_LABELS = {
    "jahrestag_friedrich_ii": "Jahrestag Friedrichs II.",
    "leibniztag": "Leibniztag",
    "geburtstag_monarch": "Geburtstag des Monarchen",
}


# ---- URIs -----------------------------------------------------------------

def u_abhandlung(id_):   return RES[f"abhandlung/{id_}"]
def u_person(key):       return RES[f"person/{key}"]
def u_reihe(kuerzel):    return RES[f"reihe/{kuerzel}"]
def u_band(band_key):    return RES[f"band/{slugify(band_key)}"]
def u_jahr(jahr):        return RES[f"jahr/{int(jahr)}"]
def u_gattung(key):      return RES[f"gattung/{key}"]
def u_anlass(key):       return RES[f"anlass/{key}"]
def u_disziplin(name):   return RES[f"disziplin/{slugify(name)}"]
def u_thema(name):       return RES[f"thema/{slugify(name)}"]
def u_ort(name):         return RES[f"ort/{slugify(name)}"]
def u_werk(name):        return RES[f"werk/{slugify(name)}"]

SCHEMES = {
    "gattung": RES["schema/gattungen"],
    "anlass": RES["schema/anlaesse"],
    "disziplin": RES["schema/disziplinen"],
    "thema": RES["schema/themen"],
}


def gyear(jahr):
    return Literal(f"{int(jahr):04d}", datatype=XSD.gYear)


def leer(wert):
    return wert is None or (isinstance(wert, float) and pd.isna(wert)) or wert == ""


# ---- Bausteine ------------------------------------------------------------

def konzept(g, uri, klasse, label, scheme):
    """Legt ein SKOS-Konzept an (Gattung, Disziplin, Thema, Anlass)."""
    g.add((uri, RDF.type, klasse))
    g.add((uri, SKOS.prefLabel, Literal(label, lang="de")))       # NAMESPACE-HOOK: skos
    g.add((uri, SKOS.inScheme, scheme))                            # NAMESPACE-HOOK: skos
    g.add((uri, RDFS.label, Literal(label, lang="de")))


def jahr_knoten(g, jahr):
    uri = u_jahr(jahr)
    g.add((uri, RDF.type, DAS.Jahr))
    g.add((uri, RDFS.label, Literal(str(int(jahr)))))
    g.add((uri, TIME.year, gyear(jahr)))                           # NAMESPACE-HOOK: time
    g.add((uri, TIME.unitType, TIME.unitYear))                     # NAMESPACE-HOOK: time
    return uri


def person_knoten(g, key, name):
    uri = u_person(key)
    g.add((uri, RDF.type, DAS.Person))
    g.add((uri, SCHEMA.name, Literal(name)))                       # NAMESPACE-HOOK: schema
    g.add((uri, RDFS.label, Literal(name)))
    return uri


class Personenindex:
    """Ordnet Namen aus Titeln ('K. RUNGE', 'Humboldt, Alexander von') vorhandenen Autoren zu."""

    def __init__(self, autoren):
        self.keys = set(autoren["autor_key"])
        self.nach_nachname = {}
        # sortiert nach Produktivitaet: bei Schreibvarianten gewinnt die haeufigste
        for key, name in zip(autoren["autor_key"], autoren["autor"]):
            nach, _, vor = name.partition(",")
            self.nach_nachname.setdefault(slugify(nach), []).append((key, vor.strip()))

    @staticmethod
    def initialen(vornamen):
        return [w[0].upper() for w in re.findall(r"[A-Za-zÀ-ÿ]+", vornamen)
                if w.lower() not in {"von", "vom", "van", "de", "du"}]

    def finde(self, name):
        if slugify(name) in self.keys:
            return slugify(name)
        if "," in name:
            nach, _, vor = name.partition(",")
        else:  # 'K. A. MARTIUS' / 'W. VON SIEMENS'
            teile = name.split()
            nach = teile[-1]
            vor = " ".join(t for t in teile[:-1] if t.upper() not in {"VON", "VOM"})
        kandidaten = self.nach_nachname.get(slugify(nach), [])
        gesucht = self.initialen(vor)
        passend = [(k, v) for k, v in kandidaten
                   if self.initialen(v)[:len(gesucht)] == gesucht]
        if len(passend) == 1:
            return passend[0][0]
        # Mehrere Schreibvarianten derselben Person ('Kirchhoff, Gustav' /
        # 'Kirchhoff, Gustav Robert'): gleicher erster Vorname -> haeufigste Variante
        if passend and len({v.split()[0] if v else "" for _, v in passend}) == 1:
            return passend[0][0]
        return None


# ---- Graph: Katalog -------------------------------------------------------

def baue_katalog(g, abh, reihen, relationen, autoren):
    for r in reihen.itertuples(index=False):
        uri = u_reihe(r.kuerzel)
        g.add((uri, RDF.type, DAS.Schriftenreihe))
        g.add((uri, DCTERMS.title, Literal(r.titel)))              # NAMESPACE-HOOK: dcterms
        g.add((uri, RDFS.label, Literal(r.titel)))
        g.add((uri, DAS.kuerzel, Literal(r.kuerzel)))
        if not leer(r.jahr_von):
            g.add((uri, SCHEMA.startDate, gyear(r.jahr_von)))      # NAMESPACE-HOOK: schema
            g.add((uri, SCHEMA.endDate, gyear(r.jahr_bis)))        # NAMESPACE-HOOK: schema

    for a in autoren.itertuples(index=False):
        person_knoten(g, a.autor_key, a.autor)

    # Baende mit haeufigstem Erscheinungsjahr
    band_jahr = abh.dropna(subset=["jahr"]).groupby("band_key")["jahr"].agg(lambda s: s.mode().iloc[0])
    for (band_key, reihe, band), _ in abh.groupby(["band_key", "reihe", "band"]):
        uri = u_band(band_key)
        g.add((uri, RDF.type, DAS.Band))
        g.add((uri, RDFS.label, Literal(f"{reihe} {band}")))
        g.add((uri, DAS.bandnummer, Literal(band)))
        g.add((uri, DAS.inReihe, u_reihe(reihe)))
        if band_key in band_jahr.index:
            g.add((uri, DAS.erschienenIm, jahr_knoten(g, band_jahr[band_key])))

    for a in abh.itertuples(index=False):
        uri = u_abhandlung(a.id)
        g.add((uri, RDF.type, DAS.Abhandlung))
        g.add((uri, DCTERMS.title, Literal(a.titel)))              # NAMESPACE-HOOK: dcterms
        g.add((uri, RDFS.label, Literal(a.titel)))
        g.add((uri, DCTERMS.identifier, Literal(a.id)))            # NAMESPACE-HOOK: dcterms
        g.add((uri, DAS.inBand, u_band(a.band_key)))
        if not leer(a.autor_key):
            g.add((uri, DAS.autor, u_person(a.autor_key)))
        if not leer(a.jahr):
            g.add((uri, DAS.erschienenIm, jahr_knoten(g, a.jahr)))
            g.add((uri, FABIO.hasPublicationYear, gyear(a.jahr)))      # NAMESPACE-HOOK: fabio
            g.add((uri, DAS.jahrQuelle, Literal(a.jahr_quelle)))
        if not leer(a.startseite):
            g.add((uri, PRISM.startingPage, Literal(a.startseite)))  # NAMESPACE-HOOK: prism
        if not leer(a.endseite):
            g.add((uri, PRISM.endingPage, Literal(a.endseite)))      # NAMESPACE-HOOK: prism
        if int(a.tafeln):
            g.add((uri, DAS.anzahlTafeln, Literal(int(a.tafeln))))
        if int(a.tabellen):
            g.add((uri, DAS.anzahlTabellen, Literal(int(a.tabellen))))
        if a.figuren == "True":
            g.add((uri, DAS.hatFiguren, Literal(True)))
        if not leer(a.link):
            g.add((uri, DAS.digitalisat, URIRef(a.link)))
        if a.ist_ppn == "True":
            g.add((uri, DAS.ppn, Literal(a.id)))
            g.add((uri, RDFS.seeAlso, K10PLUS[a.id]))              # NAMESPACE-HOOK: k10plus

    for r in relationen.itertuples(index=False):
        prop = RELATION_PROPERTY.get(r.typ)
        if prop is not None and r.ziel_vorhanden == "True":
            g.add((u_abhandlung(r.quelle), prop, u_abhandlung(r.ziel)))


# ---- Graph: Regeln --------------------------------------------------------

def baue_regeln(g, regeln, personen):
    for key, label in GATTUNG_LABELS.items():
        konzept(g, u_gattung(key), DAS.Gattung, label, SCHEMES["gattung"])
    for key, label in ANLASS_LABELS.items():
        uri = u_anlass(key)
        g.add((uri, RDF.type, DAS.Anlass))
        g.add((uri, SCHEMA.name, Literal(label, lang="de")))       # NAMESPACE-HOOK: schema
        g.add((uri, RDFS.label, Literal(label, lang="de")))
    g.add((SCHEMES["gattung"], RDF.type, SKOS.ConceptScheme))     # NAMESPACE-HOOK: skos
    g.add((SCHEMES["gattung"], RDFS.label, Literal("Gattungen", lang="de")))

    neue_personen = 0
    for e in regeln:
        uri = u_abhandlung(e["id"])
        g.add((uri, DCTERMS.language, ISO639[e["sprache"]]))       # NAMESPACE-HOOK: dcterms + iso639
        if e["haupttitel"] and e["teil"]:
            g.add((uri, DAS.haupttitel, Literal(e["haupttitel"])))
            g.add((uri, DAS.teil, Literal(e["teil"])))
            if e["teil_typ"]:
                g.add((uri, DAS.teilTyp, Literal(e["teil_typ"])))
            if e["teil_nummer"]:
                g.add((uri, DAS.teilNummer, Literal(int(e["teil_nummer"]))))
        for gattung in e["gattungen"]:
            g.add((uri, DAS.gattung, u_gattung(gattung)))
        if e["anlass"]:
            g.add((uri, DAS.anlass, u_anlass(e["anlass"])))
        for datum in e["daten"]:
            g.add((uri, DAS.erwaehntesDatum, Literal(datum, datatype=XSD.date)))
        for jahr in e["jahre"]:
            g.add((uri, DAS.erwaehntesJahr, gyear(jahr)))
        for k in e["klammern"]:
            g.add((uri, DAS.klammerzusatz, Literal(k["inhalt"])))
        for b in e["beteiligte"]:
            key = personen.finde(b["name"])
            if key is None:
                key = slugify(b["name"])
                person_knoten(g, key, b["name"].title())
                neue_personen += 1
            g.add((uri, BETEILIGTE_PROPERTY[b["rolle"]], u_person(key)))
    return neue_personen


# ---- Graph: LLM -----------------------------------------------------------

def baue_llm(g, llm, personen, entitaeten_gnd):
    g.add((SCHEMES["disziplin"], RDF.type, SKOS.ConceptScheme))   # NAMESPACE-HOOK: skos
    g.add((SCHEMES["thema"], RDF.type, SKOS.ConceptScheme))       # NAMESPACE-HOOK: skos

    def gnd_link(uri, typ, name, als_konzept=False):
        treffer = entitaeten_gnd.get((typ, name))
        if not treffer:
            return
        gnd, qid = treffer
        # NAMESPACE-HOOK: skos:exactMatch fuer Konzepte, owl:sameAs fuer Dinge
        g.add((uri, SKOS.exactMatch if als_konzept else OWL.sameAs, GND[gnd]))
        if qid:
            g.add((uri, SKOS.exactMatch if als_konzept else OWL.sameAs, WD[qid]))

    for e in llm:
        uri = u_abhandlung(e["id"])
        if e.get("titel_de"):
            g.add((uri, DAS.titelDeutsch, Literal(e["titel_de"], lang="de")))
        if e.get("disziplin"):
            d = u_disziplin(e["disziplin"])
            konzept(g, d, DAS.Disziplin, e["disziplin"], SCHEMES["disziplin"])
            g.add((uri, DAS.disziplin, d))
        for t in e.get("themen", []):
            t_uri = u_thema(t)
            konzept(g, t_uri, DAS.Thema, t, SCHEMES["thema"])
            gnd_link(t_uri, "thema", t, als_konzept=True)
            g.add((uri, DAS.thema, t_uri))
        for o in e.get("orte", []):
            o_uri = u_ort(o["name"])
            g.add((o_uri, RDF.type, DAS.Ort))
            g.add((o_uri, SCHEMA.name, Literal(o["name"])))           # NAMESPACE-HOOK: schema
            g.add((o_uri, RDFS.label, Literal(o["name"])))
            gnd_link(o_uri, "ort", o["name"])
            g.add((uri, DAS.erwaehnt, o_uri))
        for w in e.get("werke", []):
            w_uri = u_werk(w["name"])
            g.add((w_uri, RDF.type, DAS.Werk))
            g.add((w_uri, SCHEMA.name, Literal(w["name"])))           # NAMESPACE-HOOK: schema
            g.add((w_uri, RDFS.label, Literal(w["name"])))
            g.add((uri, DAS.erwaehnt, w_uri))
        for p in e.get("personen", []):
            key = personen.finde(p["name"]) or slugify(p["name"])
            p_uri = person_knoten(g, key, p["name"])
            gnd_link(p_uri, "person", p["name"])
            g.add((uri, DAS.handeltVon if p["rolle"] == "gegenstand" else DAS.erwaehnt, p_uri))
        for t in e.get("taxa", []):
            g.add((uri, DAS.taxon, Literal(t)))
        for o in e.get("objekte", []):
            g.add((uri, DAS.objekt, Literal(o)))
        if e.get("zeitraum"):
            g.add((uri, DAS.behandelterZeitraum, Literal(e["zeitraum"])))


# ---- Graph: GND -----------------------------------------------------------

def baue_gnd(g, autoren_gnd):
    for a in autoren_gnd.itertuples(index=False):
        uri = u_person(a.autor_key)
        g.add((uri, DAS.abgleichStatus, Literal(a.status)))
        g.add((uri, DAS.abgleichScore, Literal(float(a.score))))
        if a.status not in {"sicher", "manuell"} or leer(a.gnd):
            continue
        g.add((uri, OWL.sameAs, GND[str(a.gnd)]))                     # NAMESPACE-HOOK: owl + gnd
        if not leer(a.wikidata):
            g.add((uri, OWL.sameAs, WD[a.wikidata]))                   # NAMESPACE-HOOK: owl + wikidata
        if not leer(getattr(a, "geburt", None)):
            g.add((uri, SCHEMA.birthDate, gyear(a.geburt)))            # NAMESPACE-HOOK: schema
        if not leer(getattr(a, "tod", None)):
            g.add((uri, SCHEMA.deathDate, gyear(a.tod)))               # NAMESPACE-HOOK: schema


# ---- Materialisierung -----------------------------------------------------

def materialisiere(ds, ontologie):
    """Schreibt Oberklassen/-properties (transitiv) aus der Ontologie in jeden Graphen."""
    def huelle(praedikat):
        direkt = {}
        for s, o in ontologie.subject_objects(praedikat):
            direkt.setdefault(s, set()).add(o)
        ergebnis = {}
        for start in direkt:
            gesehen, stapel = set(), [start]
            while stapel:
                for o in direkt.get(stapel.pop(), ()):
                    if o not in gesehen:
                        gesehen.add(o)
                        stapel.append(o)
            ergebnis[start] = gesehen
        return ergebnis

    oberklassen = huelle(RDFS.subClassOf)
    oberprops = huelle(RDFS.subPropertyOf)
    for g in ds.graphs():
        if g.identifier == GRAPH.ontologie:
            continue
        neu = []
        for s, p, o in g:
            if p == RDF.type and o in oberklassen:
                neu += [(s, RDF.type, k) for k in oberklassen[o]]
            if p in oberprops:
                neu += [(s, q, o) for q in oberprops[p]]
        for t in neu:
            g.add(t)


# ---- Hauptprogramm --------------------------------------------------------

def lade_jsonl(pfad):
    with open(pfad, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    abh = pd.read_csv(ABHANDLUNGEN_CSV, dtype=str)
    reihen = pd.read_csv(REIHEN_CSV)
    relationen = pd.read_csv(RELATIONEN_CSV, dtype=str)
    autoren = pd.read_csv(AUTOREN_CSV)
    personen = Personenindex(autoren)

    ds = bind_all(Dataset())
    jetzt = Literal(datetime.now(timezone.utc).isoformat(timespec="seconds"), datatype=XSD.dateTime)
    meta = ds.graph(GRAPH.meta)

    def neuer_graph(name, quelle):
        g = ds.graph(GRAPH[name])
        # NAMESPACE-HOOK: prov (Provenienz der Named Graphs)
        meta.add((GRAPH[name], RDF.type, PROV.Entity))
        meta.add((GRAPH[name], PROV.generatedAtTime, jetzt))
        meta.add((GRAPH[name], PROV.wasDerivedFrom, Literal(quelle)))
        return g

    ontologie = neuer_graph("ontologie", "ontology.ttl")
    ontologie.parse(ONTOLOGY_TTL, format="turtle")

    baue_katalog(neuer_graph("katalog", "merged_df.csv / merged_df.ris"), abh, reihen, relationen, autoren)
    print("Katalog: fertig")

    regeln = lade_jsonl(TITLE_RULES_JSONL)
    neu = baue_regeln(neuer_graph("regeln", "02_title_rules.py"), regeln, personen)
    print(f"Regeln: fertig ({neu} Beteiligte ohne Entsprechung unter den Autoren)")

    if TITLE_LLM_JSONL.exists():
        llm = lade_jsonl(TITLE_LLM_JSONL)
        entitaeten = {}
        if ENTITAETEN_GND_CSV.exists():
            e = pd.read_csv(ENTITAETEN_GND_CSV, dtype=str)
            e = e[e["status"] == "sicher"]
            entitaeten = {(t, n): (gnd, None if pd.isna(q) else q)
                          for t, n, gnd, q in zip(e["typ"], e["name"], e["gnd"], e["wikidata"])}
        quellen = sorted({x.get("quelle", "?") for x in llm})
        baue_llm(neuer_graph("llm", "03_title_llm.py: " + ", ".join(quellen)), llm, personen, entitaeten)
        print(f"LLM: fertig ({len(llm)} Titel)")
    else:
        print(f"LLM: {TITLE_LLM_JSONL.name} fehlt, übersprungen")

    if AUTOREN_GND_CSV.exists():
        baue_gnd(neuer_graph("gnd", "04_reconcile_gnd.py (lobid-gnd, Wikidata)"),
                 pd.read_csv(AUTOREN_GND_CSV, dtype={"gnd": str}))
        print("GND: fertig")
    else:
        print(f"GND: {AUTOREN_GND_CSV.name} fehlt, übersprungen")

    if MATERIALISIEREN:
        materialisiere(ds, ontologie)
        print("Oberklassen/-properties materialisiert")

    ds.serialize(GRAPH_TRIG, format="trig")
    union = bind_all(Graph())
    for s, p, o, _ in ds.quads((None, None, None, None)):
        union.add((s, p, o))
    union.serialize(GRAPH_TTL, format="turtle")

    print("Tripel je Graph:")
    for g in ds.graphs():
        if len(g):
            print(f"  {g.identifier.n3(ds.namespace_manager):22} {len(g):>8}")
    print(f"Gesamt (Vereinigung): {len(union)} -> {GRAPH_TTL.name}, {GRAPH_TRIG.name}")


if __name__ == "__main__":
    main()
