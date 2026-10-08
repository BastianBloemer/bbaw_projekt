"""
Zentrale Namespace-Definitionen
-------------------------------
Alle Vokabulare, die der Wissensgraph verwendet, werden HIER definiert.
Wer ein Vokabular austauschen oder ein neues ergaenzen will (z.B. CIDOC-CRM,
BIBFRAME, RiC-O, GND-Ontologie ...), aendert zuerst diese Datei und sucht dann
in 05_build_graph.py und ontology.ttl nach der Markierung

    NAMESPACE-HOOK

An jeder so markierten Stelle wird eine Klasse oder Property eines externen
Vokabulars verwendet.
"""

from rdflib import Namespace
from rdflib.namespace import DCTERMS, FOAF, OWL, RDF, RDFS, SKOS, TIME, XSD

# ==========================================================================
# NAMESPACE-HOOK: eigener Namespace des Projekts
# Die Basis-URI ist ein Platzhalter. Fuer eine Veroeffentlichung sollte eine
# stabile URI gewaehlt werden (z.B. ueber w3id.org oder eine BBAW-Domain).
# ==========================================================================
BASE = "https://akademieschriften.bbaw.de/kg/"

DAS = Namespace(BASE + "ontology#")        # Klassen und Properties des Projekts
RES = Namespace(BASE + "resource/")        # Instanzen (Abhandlungen, Personen, ...)
GRAPH = Namespace(BASE + "graph/")         # Named Graphs fuer Provenienz

# ==========================================================================
# NAMESPACE-HOOK: bibliographische Vokabulare (SPAR-Ontologien, PRISM, FRBR)
# Alternativen: BIBO (http://purl.org/ontology/bibo/), BIBFRAME
# (http://id.loc.gov/ontologies/bibframe/), RDA (http://rdaregistry.info/)
# ==========================================================================
FABIO = Namespace("http://purl.org/spar/fabio/")
CITO = Namespace("http://purl.org/spar/cito/")
FRBR = Namespace("http://purl.org/vocab/frbr/core#")
PRISM = Namespace("http://prismstandard.org/namespaces/basic/2.0/")

# ==========================================================================
# NAMESPACE-HOOK: allgemeine Vokabulare (schema.org)
# Alternativen fuer Personen/Orte/Ereignisse: CIDOC-CRM
# (http://www.cidoc-crm.org/cidoc-crm/), GND-Ontologie (siehe unten)
# ==========================================================================
SCHEMA = Namespace("https://schema.org/")

# ==========================================================================
# NAMESPACE-HOOK: Normdaten (Verknuepfungsziele)
# ==========================================================================
GND = Namespace("https://d-nb.info/gnd/")                       # GND-Entitaeten
GNDO = Namespace("https://d-nb.info/standards/elementset/gnd#")  # GND-Ontologie
WD = Namespace("http://www.wikidata.org/entity/")                # Wikidata-Items
WDT = Namespace("http://www.wikidata.org/prop/direct/")          # Wikidata-Properties
K10PLUS = Namespace("https://opac.k10plus.de/DB=2.1/PPNSET?PPN=")  # Katalogsatz (PPN)

# ==========================================================================
# NAMESPACE-HOOK: Sprachcodes (Library of Congress, ISO 639-1)
# Alternativen: Lexvo (http://lexvo.org/id/iso639-3/), Wikidata-Sprach-Items
# ==========================================================================
ISO639 = Namespace("http://id.loc.gov/vocabulary/iso639-1/")

# ==========================================================================
# NAMESPACE-HOOK: Provenienz (PROV-O)
# ==========================================================================
PROV = Namespace("http://www.w3.org/ns/prov#")

# Aus rdflib uebernommen: DCTERMS, FOAF, OWL, RDF, RDFS, SKOS, TIME, XSD

PREFIXES = {
    "das": DAS,
    "res": RES,
    "graph": GRAPH,
    "fabio": FABIO,
    "cito": CITO,
    "frbr": FRBR,
    "prism": PRISM,
    "schema": SCHEMA,
    "gnd": GND,
    "gndo": GNDO,
    "wd": WD,
    "wdt": WDT,
    "k10plus": K10PLUS,
    "iso639": ISO639,
    "prov": PROV,
    "dcterms": DCTERMS,
    "foaf": FOAF,
    "owl": OWL,
    "rdf": RDF,
    "rdfs": RDFS,
    "skos": SKOS,
    "time": TIME,
    "xsd": XSD,
}


def bind_all(graph):
    """Bindet alle Praefixe an einen rdflib-Graphen (bzw. Dataset)."""
    for prefix, ns in PREFIXES.items():
        graph.bind(prefix, ns, override=True)
    return graph
