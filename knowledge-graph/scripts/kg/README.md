# Wissensgraph der Akademieschriften

Pipeline von `merged_df.csv` zu einem RDF-Graphen (`data/kg/akademieschriften.ttl` / `.trig`).

```bash
cd knowledge-graph
python3 -m venv .venv && .venv/bin/pip install -r scripts/kg/requirements.txt
cd scripts/kg
../../.venv/bin/python 01_clean.py          # Bereinigung, Jahre ergänzen, Relationen
../../.venv/bin/python 02_title_rules.py    # Regelbasierte Titelanalyse
../../.venv/bin/python 03_title_llm.py --dry-run --limit 3   # LLM-Analyse (siehe Docstring)
../../.venv/bin/python 04_reconcile_gnd.py  # Autoren -> GND / Wikidata (Netz nötig)
../../.venv/bin/python 05_build_graph.py    # RDF erzeugen
../../.venv/bin/python 06_validate.py       # SHACL + Beispielabfragen
```

| Datei | Inhalt |
|---|---|
| `namespaces.py` | alle Namespaces; hier neue Vokabulare ergänzen |
| `ontology.ttl` | Klassen/Properties `das:` und ihre Anbindung an FaBiO, schema.org, SKOS … |
| `shapes.ttl` | SHACL-Regeln |
| `queries/*.rq` | Beispielabfragen (werden von 06 ausgeführt) |
| `data/kg/review_authors.csv` | unsichere Autorenzuordnungen zur Handprüfung |
| `data/kg/autoren_gnd_manuell.csv` | manuelle Korrekturen (`autor_key,gnd`), haben Vorrang |

**Vokabulare austauschen:** nach `NAMESPACE-HOOK` suchen (`grep -rn NAMESPACE-HOOK`).
Instanzdaten verwenden nur `das:`-Begriffe, die Abbildung auf externe Vokabulare
steht in `ontology.ttl` und wird mit `MATERIALISIEREN = True` (05) in die Daten geschrieben.

**Provenienz:** Named Graphs `graph:katalog`, `graph:regeln`, `graph:llm`, `graph:gnd`
in der `.trig`-Datei.
