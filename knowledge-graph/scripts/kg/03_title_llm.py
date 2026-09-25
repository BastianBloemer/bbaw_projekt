"""
03 - LLM-gestuetzte Titelanalyse
--------------------------------
Schickt jeden Titel (plus Kontext: Reihe, Jahr, Autor und die Ergebnisse der
Regelanalyse aus 02) an ein LLM und laesst strukturiert extrahieren:

    titel_de        deutsche Arbeitsuebersetzung / Normalisierung des Titels
    sprache         Sprache des Titels (Korrektur der Heuristik aus 02)
    disziplin       eine Disziplin aus DISZIPLINEN
    themen          Schlagwoerter (moeglichst GND-nahe Sachbegriffe)
    personen        im Titel erwaehnte Personen (nicht der Autor) mit Rolle
    orte            erwaehnte Orte
    werke           erwaehnte Werke / Texte / Handschriften
    taxa            biologische / mineralogische Namen
    objekte         Inschriften, Muenzen, Instrumente, Himmelskoerper ...
    zeitraum        behandelter Zeitraum (Freitext, leer wenn keiner)

Der Anbieter ist austauschbar (Umgebungsvariable LLM_PROVIDER):

    openai_compat  jede OpenAI-kompatible Chat-Completions-API
                   (Open WebUI, Ollama, vLLM, LM Studio, OpenAI ...)
                   LLM_BASE_URL  z.B. http://localhost:3000/api  (Open WebUI)
                                     http://localhost:11434/v1   (Ollama)
                   LLM_API_KEY   API-Key bzw. Open-WebUI-Token
                   LLM_MODEL     Modellname
    anthropic      Claude ueber das offizielle SDK (pip install anthropic)
                   Zugangsdaten ueber ANTHROPIC_API_KEY oder `ant auth login`
                   LLM_MODEL     Standard: claude-opus-5
                   LLM_EFFORT    low | medium | high  (Standard: medium)

Ergebnisse werden zeilenweise nach title_llm.jsonl geschrieben. Bereits
analysierte IDs werden beim naechsten Lauf uebersprungen, so dass ein
abgebrochener Lauf einfach fortgesetzt werden kann.

Aufruf (bewusst ohne Standard-Volllauf):
    python 03_title_llm.py --dry-run --limit 3        # nur Prompts anzeigen
    python 03_title_llm.py --stichprobe 200           # Evaluationsstichprobe
    python 03_title_llm.py --alle                     # gesamter Bestand
"""

import argparse
import json
import os
import re
import sys
import time

import pandas as pd

from config import ABHANDLUNGEN_CSV, REIHEN_CSV, TITLE_LLM_JSONL, TITLE_RULES_JSONL

# ---- Konfiguration --------------------------------------------------------

# Arbeits-Taxonomie der Disziplinen. Sie ist bewusst grob und wird im Graphen
# als SKOS-Schema angelegt (05_build_graph.py). Offene Frage: durch eine aus
# den Texten induzierte, historische Taxonomie ersetzen?
DISZIPLINEN = [
    "Mathematik", "Astronomie", "Physik", "Chemie", "Mineralogie und Geologie",
    "Meteorologie", "Geographie", "Botanik", "Zoologie", "Anatomie und Physiologie",
    "Medizin", "Philosophie", "Klassische Philologie", "Sprachwissenschaft",
    "Germanistik und Literaturgeschichte", "Orientalistik", "Geschichte",
    "Alte Geschichte", "Archäologie und Epigraphik", "Numismatik", "Theologie",
    "Rechts- und Staatswissenschaft", "Ökonomie und Statistik",
    "Technik und Landwirtschaft", "Akademiegeschichte", "Sonstiges",
]

SYSTEM_PROMPT = """Du bist Wissenschaftshistoriker:in und erschließt die Schriften der \
Berliner Akademie der Wissenschaften (1710–1900). Du bekommst den Titel einer \
Abhandlung mit Kontext und extrahierst strukturierte Angaben für einen Wissensgraphen.

Regeln:
- Extrahiere nur, was im Titel steht oder aus ihm unmittelbar folgt. Erfinde nichts.
- Der Autor der Abhandlung gehört NICHT in "personen", auch nicht Mitautoren oder \
Kommentatoren, die bereits unter "Regelanalyse" stehen.
- Personen, Orte und Werke in der heute üblichen Ansetzungsform (GND-Stil: \
"Nachname, Vorname"; Orte mit heutigem deutschen Namen), die historische Schreibung \
kommt in "im_titel".
- "themen": 1–5 Schlagwörter auf Deutsch, möglichst als GND-Sachbegriffe \
(z.B. "Elektrizität", "Sonnenfinsternis", "Inschrift").
- Titel in Latein, Französisch oder historischem Deutsch: "titel_de" ist eine \
knappe moderne deutsche Wiedergabe.
- Leere Listen bzw. leere Zeichenketten, wenn nichts zutrifft."""

EINTRAG = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "im_titel": {"type": "string"},
    },
    "required": ["name", "im_titel"],
    "additionalProperties": False,
}

SCHEMA = {
    "type": "object",
    "properties": {
        "titel_de": {"type": "string"},
        "sprache": {"type": "string", "enum": ["de", "fr", "la", "en", "it", "andere"]},
        "disziplin": {"type": "string", "enum": DISZIPLINEN},
        "themen": {"type": "array", "items": {"type": "string"}},
        "personen": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "im_titel": {"type": "string"},
                    "rolle": {"type": "string",
                              "enum": ["gegenstand", "adressat", "urheber_eines_werks",
                                       "entdecker", "sammler", "sonstige"]},
                },
                "required": ["name", "im_titel", "rolle"],
                "additionalProperties": False,
            },
        },
        "orte": {"type": "array", "items": EINTRAG},
        "werke": {"type": "array", "items": EINTRAG},
        "taxa": {"type": "array", "items": {"type": "string"}},
        "objekte": {"type": "array", "items": {"type": "string"}},
        "zeitraum": {"type": "string"},
    },
    "required": ["titel_de", "sprache", "disziplin", "themen", "personen", "orte",
                 "werke", "taxa", "objekte", "zeitraum"],
    "additionalProperties": False,
}


# ---- Anbieter-Adapter -----------------------------------------------------
# Jeder Adapter implementiert extract(system, user) -> dict und hat .name
# (wird als Provenienz im Graphen gespeichert).

class OpenAICompatAdapter:
    """Chat-Completions-API im OpenAI-Format (Open WebUI, Ollama, vLLM ...)."""

    def __init__(self):
        import requests
        self.session = requests.Session()
        self.base_url = os.environ.get("LLM_BASE_URL", "http://localhost:3000/api").rstrip("/")
        self.model = os.environ["LLM_MODEL"]
        key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENWEBUI_TOKEN")
        if key:
            self.session.headers["Authorization"] = f"Bearer {key}"
        self.name = f"openai_compat:{self.model}"

    def extract(self, system, user):
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": "titelanalyse", "schema": SCHEMA,
                                                "strict": True}},
            "temperature": 0,
        }
        r = self.session.post(f"{self.base_url}/chat/completions", json=payload, timeout=300)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        return parse_json(text)


class AnthropicAdapter:
    """Claude ueber das offizielle Python-SDK mit Structured Outputs."""

    def __init__(self):
        import anthropic  # optional: pip install anthropic
        self.anthropic = anthropic
        self.client = anthropic.Anthropic()
        self.model = os.environ.get("LLM_MODEL", "claude-opus-5")
        self.effort = os.environ.get("LLM_EFFORT", "medium")
        self.name = f"anthropic:{self.model}"

    def extract(self, system, user):
        response = self.client.messages.create(
            model=self.model,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"effort": self.effort,
                           "format": {"type": "json_schema", "schema": SCHEMA}},
        )
        if response.stop_reason == "refusal":
            raise RuntimeError(f"Abgelehnt: {response.stop_details}")
        text = next(b.text for b in response.content if b.type == "text")
        return json.loads(text)


ADAPTER = {"openai_compat": OpenAICompatAdapter, "anthropic": AnthropicAdapter}


def parse_json(text):
    """Toleranter Parser fuer Modelle ohne echte Schema-Erzwingung."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise
        return json.loads(m.group(0))


# ---- Prompt ---------------------------------------------------------------

def baue_prompt(row, regeln, reihentitel):
    kontext = {
        "titel": row.titel,
        "reihe": reihentitel.get(row.reihe, row.reihe),
        "jahr": None if pd.isna(row.jahr) else int(float(row.jahr)),
        "autor": row.autor if isinstance(row.autor, str) else None,
        "regelanalyse": {k: regeln.get(k) for k in
                         ("sprache", "gattungen", "teil", "beteiligte", "anlass", "daten")},
    }
    return "Analysiere diese Abhandlung:\n" + json.dumps(kontext, ensure_ascii=False, indent=1)


def lade_erledigte():
    if not TITLE_LLM_JSONL.exists():
        return set()
    with open(TITLE_LLM_JSONL, encoding="utf-8") as f:
        return {json.loads(line)["id"] for line in f if line.strip()}


def validiere(ergebnis):
    fehlend = [k for k in SCHEMA["required"] if k not in ergebnis]
    if fehlend:
        raise ValueError(f"Felder fehlen: {fehlend}")
    if ergebnis["disziplin"] not in DISZIPLINEN:
        ergebnis["disziplin"] = "Sonstiges"
    return ergebnis


# ---- Hauptprogramm --------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    gruppe = ap.add_mutually_exclusive_group(required=True)
    gruppe.add_argument("--limit", type=int, help="nur die ersten N noch offenen Titel")
    gruppe.add_argument("--stichprobe", type=int, help="N zufaellige Titel, geschichtet nach Reihe")
    gruppe.add_argument("--alle", action="store_true", help="gesamten Bestand analysieren")
    ap.add_argument("--dry-run", action="store_true", help="nur Prompts ausgeben, kein API-Aufruf")
    ap.add_argument("--pause", type=float, default=0.0, help="Sekunden Pause zwischen Aufrufen")
    args = ap.parse_args()

    df = pd.read_csv(ABHANDLUNGEN_CSV, dtype=str)
    regeln = {}
    with open(TITLE_RULES_JSONL, encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            regeln[e["id"]] = e
    reihentitel = pd.read_csv(REIHEN_CSV).set_index("kuerzel")["titel"].to_dict()

    erledigt = lade_erledigte()
    offen = df[~df["id"].isin(erledigt)]
    if args.stichprobe:
        anteil = args.stichprobe / len(df)
        offen = (offen.groupby("reihe", group_keys=False)
                      .apply(lambda g: g.sample(max(1, round(len(g) * anteil)), random_state=42)))
    elif args.limit:
        offen = offen.head(args.limit)
    print(f"{len(erledigt)} bereits erledigt, {len(offen)} in diesem Lauf")

    if args.dry_run:
        for row in offen.head(5).itertuples(index=False):
            print("-" * 70)
            print(baue_prompt(row, regeln.get(row.id, {}), reihentitel))
        return

    provider = os.environ.get("LLM_PROVIDER", "openai_compat")
    adapter = ADAPTER[provider]()
    print(f"Anbieter: {adapter.name}")

    fehler = 0
    with open(TITLE_LLM_JSONL, "a", encoding="utf-8") as out:
        for i, row in enumerate(offen.itertuples(index=False), 1):
            prompt = baue_prompt(row, regeln.get(row.id, {}), reihentitel)
            try:
                ergebnis = validiere(adapter.extract(SYSTEM_PROMPT, prompt))
            except Exception as e:  # ein fehlerhafter Titel soll den Lauf nicht abbrechen
                fehler += 1
                print(f"  FEHLER bei {row.id}: {e}", file=sys.stderr)
                continue
            ergebnis = {"id": row.id, "quelle": adapter.name, **ergebnis}
            out.write(json.dumps(ergebnis, ensure_ascii=False) + "\n")
            out.flush()
            if i % 25 == 0:
                print(f"  {i}/{len(offen)} ...")
            if args.pause:
                time.sleep(args.pause)

    print(f"Fertig. Fehler: {fehler}. Ergebnisse in {TITLE_LLM_JSONL.name}")


if __name__ == "__main__":
    main()
