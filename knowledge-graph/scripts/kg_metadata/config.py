"""
Gemeinsame Pfade fuer die Wissensgraph-Pipeline
------------------------------------------------
Alle Skripte (01_ ... 06_) importieren von hier, damit Ein- und Ausgabepfade
nur an einer Stelle gepflegt werden muessen.
"""

import re
import unicodedata
from pathlib import Path

# ---- Verzeichnisse --------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent            # knowledge-graph/scripts/kg
KG_ROOT = SCRIPT_DIR.parents[1]                          # knowledge-graph/
PROJECT_ROOT = KG_ROOT.parent                            # bbaw_projekt/

DATA_DIR = KG_ROOT / "data" / "kg"
CACHE_DIR = DATA_DIR / "cache"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ---- Quellen --------------------------------------------------------------

CURATED_DIR = PROJECT_ROOT / "iiif-plattform" / "backend" / "data" / "metadata" / "curated"
SOURCE_CSV = CURATED_DIR / "merged_df.csv"
SOURCE_RIS = CURATED_DIR / "merged_df.ris"

# ---- Zwischenergebnisse ---------------------------------------------------

ABHANDLUNGEN_CSV = DATA_DIR / "abhandlungen.csv"       # 01: bereinigte Abhandlungen
RELATIONEN_CSV = DATA_DIR / "relationen.csv"           # 01: Textbeziehungen als Kantenliste
REIHEN_CSV = DATA_DIR / "reihen.csv"                   # 01: Schriftenreihen
AUTOREN_CSV = DATA_DIR / "autoren.csv"                 # 01: normalisierte Autoren

TITLE_RULES_JSONL = DATA_DIR / "title_rules.jsonl"     # 02: regelbasierte Titelanalyse
TITLE_LLM_JSONL = DATA_DIR / "title_llm.jsonl"         # 03: LLM-Titelanalyse

AUTOREN_GND_CSV = DATA_DIR / "autoren_gnd.csv"         # 04: Abgleich Autoren -> GND/Wikidata
REVIEW_AUTHORS_CSV = DATA_DIR / "review_authors.csv"   # 04: unsichere Treffer zur Handpruefung
ENTITAETEN_GND_CSV = DATA_DIR / "entitaeten_gnd.csv"   # 04: Abgleich LLM-Entitaeten -> GND

# ---- Graph ----------------------------------------------------------------

ONTOLOGY_TTL = SCRIPT_DIR / "ontology.ttl"
SHAPES_TTL = SCRIPT_DIR / "shapes.ttl"
QUERIES_DIR = SCRIPT_DIR / "queries"
GRAPH_TTL = DATA_DIR / "akademieschriften.ttl"
GRAPH_TRIG = DATA_DIR / "akademieschriften.trig"       # mit Named Graphs (Provenienz)
VALIDATION_REPORT = DATA_DIR / "validation_report.txt"


# ---- Hilfsfunktionen ------------------------------------------------------

def slugify(text):
    """Erzeugt einen URI-tauglichen Schluessel, z.B. 'Euler, Leonhard' -> 'euler-leonhard'."""
    text = text.replace("ß", "ss").replace("ẞ", "SS")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
