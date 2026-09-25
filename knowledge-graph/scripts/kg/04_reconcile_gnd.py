"""
04 - Abgleich mit GND (lobid) und Wikidata
------------------------------------------
Teil A - Autoren:
    Fuer jeden Autor aus autoren.csv werden Kandidaten in der GND gesucht
    (lobid-gnd, Typ DifferentiatedPerson). Jeder Kandidat wird bewertet nach
      - Namensaehnlichkeit (Nachname muss passen, Vornamen unscharf)
      - Plausibilitaet der Lebensdaten gegenueber dem Publikationszeitraum
      - wissenschaftlichem Beruf (professionOrOccupation)
      - Mitgliedschaft in der Preussischen Akademie laut Wikidata (P463 = Q329464)
        oder Affiliation mit einer Akademie laut GND
    Ergebnis: autoren_gnd.csv (bester Kandidat + Status) und
    review_authors.csv (unsichere Faelle mit den Top-3-Kandidaten).

    Manuelle Korrekturen: Datei autoren_gnd_manuell.csv mit den Spalten
    autor_key,gnd  (gnd leer lassen = bewusst kein Treffer). Diese Eintraege
    haben immer Vorrang.

    Wikidata-QIDs kommen aus den sameAs-Links von lobid; fehlende werden per
    SPARQL ueber die GND-ID (P227) nachgeschlagen.

Teil B - LLM-Entitaeten (nur wenn title_llm.jsonl existiert):
    Themen -> GND-Sachbegriffe, Orte -> GND-Geografika, Personen -> GND-Personen.
    Nur Treffer mit hoher Konfidenz werden uebernommen -> entitaeten_gnd.csv

Alle HTTP-Antworten werden in data/kg/cache/ zwischengespeichert.

Aufruf:
    python 04_reconcile_gnd.py            # Autoren + (falls vorhanden) LLM-Entitaeten
    python 04_reconcile_gnd.py --nur-autoren
"""

import argparse
import hashlib
import json
import re
import time
import unicodedata

import pandas as pd
import requests
from rapidfuzz import fuzz

from config import (AUTOREN_CSV, AUTOREN_GND_CSV, CACHE_DIR, DATA_DIR,
                    ENTITAETEN_GND_CSV, REVIEW_AUTHORS_CSV, TITLE_LLM_JSONL)

# ---- Konfiguration --------------------------------------------------------

LOBID_URL = "https://lobid.org/gnd/search"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
USER_AGENT = "BBAW-Akademieschriften-KG/0.1 (Forschungsprojekt; Python requests)"
PAUSE = 0.15  # Sekunden zwischen nicht gecachten Anfragen

MANUELL_CSV = DATA_DIR / "autoren_gnd_manuell.csv"

SCHWELLE_SICHER = 0.70     # Mindestscore fuer 'sicher'
ABSTAND_SICHER = 0.10      # Mindestabstand zum Zweitplatzierten
SCHWELLE_UNSICHER = 0.50   # darunter: 'kein_treffer'

WISSENSCHAFTLICHE_BERUFE = re.compile(
    r"(loge|login|iker|wissenschaftler|forscher|Astronom|Arzt|Mediziner|Chirurg|"
    r"Hochschullehrer|Professor|Geograph|Geograf|Philosoph|Bibliothekar|Gelehrter|"
    r"Mathematiker|Theologe|Jurist|Ingenieur|Apotheker|Naturalist|Polyhistor|"
    r"Sekretär|Schriftsteller|Übersetzer|Kartograf|Geodät|Numismatiker)", re.I)
AKADEMIE = re.compile(r"Akademie|Academie|Académie|Akademija|Academy|Society|Societät", re.I)
BERLINER_AKADEMIE = re.compile(r"(Preußische|Königliche|Königlich Preußische) Akademie der Wissenschaften", re.I)

PREUSSISCHE_AKADEMIE_WD = "Q329464"   # Wikidata: Preussische Akademie der Wissenschaften

# Titel und Namenszusaetze, die bei der Suche stoeren
ADELSPRAEDIKATE = re.compile(
    r"\b(Freiherr|Freifrau|Graf|Gräfin|Ritter|Edler|Prinz|Fürst|Comte|Marquis|Baron|"
    r"Chevalier|Sir|Lord|Abbé|von|vom|de|du|la|le|zu|van|der jüngere|der ältere|"
    r"d\. ?J\.|d\. ?Ä\.)(?=\s|$)", re.I)

session = requests.Session()
session.headers["User-Agent"] = USER_AGENT


# ---- HTTP mit Cache -------------------------------------------------------

def cached_get(url, params, headers=None):
    schluessel = hashlib.md5((url + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    pfad = CACHE_DIR / f"{schluessel}.json"
    if pfad.exists():
        return json.loads(pfad.read_text(encoding="utf-8"))
    for versuch in range(4):
        try:
            r = session.get(url, params=params, headers=headers, timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(f"HTTP {r.status_code}")
            r.raise_for_status()
            daten = r.json()
            break
        except (requests.RequestException, ValueError) as e:
            if versuch == 3:
                raise
            time.sleep(2 ** versuch * 2)
    pfad.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
    time.sleep(PAUSE)
    return daten


def lobid_suche(q, filter_, size=15):
    params = {"q": q, "filter": filter_, "format": "json", "size": size}
    return cached_get(LOBID_URL, params).get("member", [])


# ---- Hilfsfunktionen ------------------------------------------------------

def norm(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", text)).strip()


def zerlege_name(name):
    """'Leibniz, Gottfried Wilhelm Freiherr von' -> ('Leibniz', 'Gottfried Wilhelm')."""
    if "," not in name:
        return name.strip(), ""
    nach, vor = name.split(",", 1)
    vor = ADELSPRAEDIKATE.sub(" ", vor)
    return nach.strip(), re.sub(r"\s+", " ", vor).strip()


def jahr_aus(werte):
    if not werte:
        return None
    m = re.search(r"-?\d{3,4}", str(werte[0]))
    return int(m.group(0)) if m else None


def wikidata_aus(kandidat):
    for s in kandidat.get("sameAs", []) or []:
        m = re.search(r"wikidata\.org/entity/(Q\d+)", s.get("id", ""))
        if m:
            return m.group(1)
    return None


def labels(kandidat, feld):
    return [x.get("label", "") for x in kandidat.get(feld, []) or []]


# ---- Teil A: Autoren ------------------------------------------------------

def bewerte(kandidat, nachname, vorname, jahr_von, akademiemitglieder):
    namen = [kandidat.get("preferredName", "")] + (kandidat.get("variantName") or [])
    best_name = 0.0
    for n in namen:
        k_nach, k_vor = zerlege_name(n)
        if fuzz.ratio(norm(k_nach), norm(nachname)) < 85:
            continue
        if not vorname:
            sim = 0.6                           # nur Nachname bekannt
        elif not k_vor:
            sim = 0.3
        else:
            sim = fuzz.token_set_ratio(norm(k_vor), norm(vorname)) / 100
            # Initialen ('W. C. H.') gegen ausgeschriebene Vornamen
            if re.fullmatch(r"([A-Z]\.\s*)+", k_vor.strip()) or re.fullmatch(r"([A-Z]\.\s*)+", vorname):
                i1 = [w[0] for w in norm(k_vor).split()]
                i2 = [w[0] for w in norm(vorname).split()]
                if i1 and i2 and i1[0] == i2[0]:
                    sim = max(sim, 0.8)
        best_name = max(best_name, sim)
    if best_name == 0:
        return 0.0, {}

    # Lebensdaten nur gegen die ERSTE Publikation pruefen: Spaetere Jahre koennen
    # posthume Drucke oder Uebersetzungen sein (z.B. 04-phys, 1781).
    geb, tod = jahr_aus(kandidat.get("dateOfBirth")), jahr_aus(kandidat.get("dateOfDeath"))
    datum = 0.5                                   # unbekannt = neutral
    plausibel = True
    if jahr_von is not None and (geb or tod):
        datum = 1.0
        if geb is not None:
            alter = jahr_von - geb
            if not 15 <= alter <= 85:
                plausibel = False
            elif not 20 <= alter <= 70:
                datum = 0.6
        if tod is not None and tod < jahr_von - 5:
            plausibel = False

    berufe = labels(kandidat, "professionOrOccupation")
    affil = labels(kandidat, "affiliation")
    beruf = 1.0 if any(WISSENSCHAFTLICHE_BERUFE.search(b) for b in berufe) else 0.0
    if wikidata_aus(kandidat) in akademiemitglieder or any(BERLINER_AKADEMIE.search(a) for a in affil):
        akademie = 1.0
    elif any(AKADEMIE.search(a) for a in affil):
        akademie = 0.3
    else:
        akademie = 0.0

    score = 0.45 * best_name + 0.2 * datum + 0.1 * beruf + 0.25 * akademie
    if not plausibel:
        score *= 0.3
    info = {"geburt": geb, "tod": tod, "akademiemitglied": akademie == 1.0,
            "berufe": "; ".join(berufe[:4]),
            "affiliation": "; ".join(affil[:3])}
    return round(score, 3), info


def kandidaten_fuer(name, jahr_von):
    nachname, vorname = zerlege_name(name)
    typ = "type:DifferentiatedPerson"
    if jahr_von is not None:
        zeitfilter = f"{typ} AND dateOfBirth:[{jahr_von - 90} TO {jahr_von - 10}]"
    else:
        zeitfilter = typ
    ansetzung = f"{nachname}, {vorname}".strip(", ")
    phrase = f'preferredName:"{ansetzung}" OR variantName:"{ansetzung}"'
    frei = f"{nachname} {vorname}".strip()

    gesehen, kandidaten = set(), []
    for q, f in [(phrase, zeitfilter), (frei, zeitfilter), (frei, typ)]:
        for k in lobid_suche(q, f):
            if k["gndIdentifier"] not in gesehen:
                gesehen.add(k["gndIdentifier"])
                kandidaten.append(k)
        if kandidaten and f == zeitfilter and q == phrase:
            break                           # exakte Ansetzung im Zeitfenster gefunden
    return nachname, vorname, kandidaten


def gleiche_autoren_ab():
    autoren = pd.read_csv(AUTOREN_CSV)
    manuell = {}
    if MANUELL_CSV.exists():
        m = pd.read_csv(MANUELL_CSV, dtype=str).fillna("")
        manuell = dict(zip(m["autor_key"], m["gnd"]))
        print(f"Manuelle Zuordnungen: {len(manuell)}")

    # Durchgang 1: Kandidaten sammeln
    suche = {}
    for i, a in enumerate(autoren.itertuples(index=False), 1):
        if a.autor_key in manuell or not re.search(r"[A-Za-zÀ-ÿ]{3,}", a.autor):
            continue
        jahr_von = None if pd.isna(a.jahr_von) else int(a.jahr_von)
        suche[a.autor_key] = kandidaten_fuer(a.autor, jahr_von)
        if i % 100 == 0:
            print(f"  {i}/{len(autoren)} Autoren gesucht ...")

    qids = {wikidata_aus(k) for _, _, ks in suche.values() for k in ks} - {None}
    mitglieder = akademiemitglieder(qids)
    print(f"Kandidaten mit Wikidata-QID: {len(qids)}, davon Mitglied der Preuss. Akademie: {len(mitglieder)}")

    # Durchgang 2: bewerten
    zeilen, review = [], []
    for a in autoren.itertuples(index=False):
        jahr_von = None if pd.isna(a.jahr_von) else int(a.jahr_von)
        jahr_bis = None if pd.isna(a.jahr_bis) else int(a.jahr_bis)
        basis = {"autor_key": a.autor_key, "autor": a.autor, "abhandlungen": a.abhandlungen,
                 "jahr_von": jahr_von, "jahr_bis": jahr_bis}

        if a.autor_key in manuell:
            gnd = manuell[a.autor_key] or None
            zeilen.append({**basis, "gnd": gnd, "gnd_name": None, "wikidata": None,
                           "score": 1.0 if gnd else 0.0,
                           "status": "manuell" if gnd else "kein_treffer"})
            continue

        # Nur Initialen o.ae. ('J. H. B.') -> nicht abgleichbar
        if a.autor_key not in suche:
            zeilen.append({**basis, "gnd": None, "status": "nicht_abgleichbar", "score": 0.0})
            continue

        nachname, vorname, kandidaten = suche[a.autor_key]
        bewertet = []
        for k in kandidaten:
            score, info = bewerte(k, nachname, vorname, jahr_von, mitglieder)
            if score > 0:
                bewertet.append((score, k, info))
        bewertet.sort(key=lambda x: -x[0])

        if bewertet:
            s1, k1, info1 = bewertet[0]
            s2 = bewertet[1][0] if len(bewertet) > 1 else 0.0
            if s1 >= SCHWELLE_SICHER and s1 - s2 >= ABSTAND_SICHER:
                status = "sicher"
            elif s1 >= SCHWELLE_UNSICHER:
                status = "unsicher"
            else:
                status = "kein_treffer"
            zeilen.append({**basis, "gnd": k1["gndIdentifier"] if status != "kein_treffer" else None,
                           "gnd_name": k1.get("preferredName"), "wikidata": wikidata_aus(k1),
                           "score": s1, "abstand": round(s1 - s2, 3), "status": status, **info1})
            if status != "sicher":
                for rang, (s, k, info) in enumerate(bewertet[:3], 1):
                    review.append({"autor_key": a.autor_key, "autor": a.autor,
                                   "jahr_von": jahr_von, "jahr_bis": jahr_bis, "rang": rang,
                                   "score": s, "gnd": k["gndIdentifier"],
                                   "gnd_name": k.get("preferredName"), **info,
                                   "lobid": f"https://lobid.org/gnd/{k['gndIdentifier']}"})
        else:
            zeilen.append({**basis, "gnd": None, "status": "kein_treffer", "score": 0.0})

    df = pd.DataFrame(zeilen)
    df = ergaenze_wikidata(df)
    df.to_csv(AUTOREN_GND_CSV, index=False)
    pd.DataFrame(review).to_csv(REVIEW_AUTHORS_CSV, index=False)

    print("Status Autoren:", df["status"].value_counts().to_dict())
    gewichtet = df.groupby("status")["abhandlungen"].sum()
    print("Abhandlungen je Status:", gewichtet.to_dict())
    print(f"Mit Wikidata-QID: {df['wikidata'].notna().sum()}")
    print(f"Geschrieben: {AUTOREN_GND_CSV.name}, {REVIEW_AUTHORS_CSV.name}")
    return df


def wikidata_sparql(query):
    return cached_get(WIKIDATA_SPARQL, {"query": query, "format": "json"},
                      headers={"Accept": "application/sparql-results+json"})


def akademiemitglieder(qids):
    """Welche QIDs sind laut Wikidata Mitglied (P463) der Preussischen Akademie?"""
    qids, mitglieder = sorted(qids), set()
    for start in range(0, len(qids), 300):
        werte = " ".join(f"wd:{q}" for q in qids[start:start + 300])
        query = (f"SELECT ?p WHERE {{ VALUES ?p {{ {werte} }} "
                 f"?p wdt:P463 wd:{PREUSSISCHE_AKADEMIE_WD} . }}")
        try:
            daten = wikidata_sparql(query)
        except requests.RequestException as e:
            print(f"  Wikidata nicht erreichbar ({e}), Mitgliedschaft wird ignoriert")
            return set()
        mitglieder |= {b["p"]["value"].rsplit("/", 1)[-1] for b in daten["results"]["bindings"]}
    return mitglieder


def ergaenze_wikidata(df):
    """Fehlende QIDs per SPARQL ueber die GND-ID (P227) nachschlagen."""
    fehlend = df[df["gnd"].notna() & df["wikidata"].isna()]["gnd"].unique().tolist()
    gefunden = {}
    for start in range(0, len(fehlend), 200):
        block = fehlend[start:start + 200]
        werte = " ".join(f'"{g}"' for g in block)
        query = f"SELECT ?item ?gnd WHERE {{ VALUES ?gnd {{ {werte} }} ?item wdt:P227 ?gnd . }}"
        try:
            daten = wikidata_sparql(query)
        except requests.RequestException as e:
            print(f"  Wikidata nicht erreichbar ({e}), QIDs bleiben leer")
            break
        for b in daten["results"]["bindings"]:
            gefunden[b["gnd"]["value"]] = b["item"]["value"].rsplit("/", 1)[-1]
    df["wikidata"] = df["wikidata"].fillna(df["gnd"].map(gefunden))
    return df


# ---- Teil B: LLM-Entitaeten -----------------------------------------------

LLM_TYPEN = {
    "thema": "type:SubjectHeading",
    "ort": "type:PlaceOrGeographicName",
    "person": "type:DifferentiatedPerson",
}


def gleiche_llm_entitaeten_ab():
    if not TITLE_LLM_JSONL.exists():
        print(f"{TITLE_LLM_JSONL.name} fehlt -> Teil B (LLM-Entitaeten) uebersprungen")
        return
    namen = set()
    with open(TITLE_LLM_JSONL, encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            namen.update(("thema", t) for t in e.get("themen", []))
            namen.update(("ort", o["name"]) for o in e.get("orte", []))
            namen.update(("person", p["name"]) for p in e.get("personen", []))
    print(f"LLM-Entitaeten zum Abgleich: {len(namen)}")

    zeilen = []
    for typ, name in sorted(namen):
        if not name.strip():
            continue
        kandidaten = lobid_suche(f'preferredName:"{name}" OR variantName:"{name}"', LLM_TYPEN[typ], size=5)
        if not kandidaten:
            kandidaten = lobid_suche(name, LLM_TYPEN[typ], size=5)
        best, best_sim = None, 0.0
        for k in kandidaten:
            for n in [k.get("preferredName", "")] + (k.get("variantName") or []):
                sim = fuzz.ratio(norm(n), norm(name)) / 100
                if sim > best_sim:
                    best, best_sim = k, sim
        sicher = best is not None and best_sim >= 0.92 and (typ != "person" or len(kandidaten) == 1)
        zeilen.append({"typ": typ, "name": name,
                       "gnd": best["gndIdentifier"] if sicher else None,
                       "gnd_name": best.get("preferredName") if best else None,
                       "wikidata": wikidata_aus(best) if sicher else None,
                       "aehnlichkeit": round(best_sim, 3), "status": "sicher" if sicher else "offen"})
    df = pd.DataFrame(zeilen)
    df.to_csv(ENTITAETEN_GND_CSV, index=False)
    print("Status LLM-Entitaeten:", df.groupby(["typ", "status"]).size().to_dict())


# ---- Hauptprogramm --------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nur-autoren", action="store_true")
    args = ap.parse_args()
    gleiche_autoren_ab()
    if not args.nur_autoren:
        gleiche_llm_entitaeten_ab()


if __name__ == "__main__":
    main()
