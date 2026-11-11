"""
02 - Regelbasierte Titelanalyse
-------------------------------
Zieht mit deterministischen Regeln (reguläre Ausdrücke, Wortlisten)
Informationen aus den Titeln der Abhandlungen. Das Ergebnis ist
vollstaendig reproduzierbar und bildet die Grundlage, auf der die
LLM-Analyse (03) aufsetzt.

Extrahiert pro Abhandlung:
    sprache        de / fr / la (Heuristik, Fallback langdetect)
    haupttitel     Titel ohne Teil-Suffix nach ' : '
    teil           Suffix nach ' : ' (z.B. 'Auszug', 'Second mémoire'),
                   dazu teil_typ und teil_nummer
    gattungen      Liste von Gattungs-Schluesseln (siehe GATTUNGEN)
    beteiligte     weitere Personen aus dem Titel, mit Rolle
                   ('Mit K. RUNGE', 'Mit Bemerkungen von A. WEBER')
    daten          vollstaendige Datumsangaben (ISO), z.B. 'am 25. Januar 1883'
    jahre          im Titel genannte Jahreszahlen
    anlass         Anlass einer Festrede (siehe ANLAESSE)
    klammern       Inhalte eckiger Klammern mit Typ (titel / verweis / anmerkung)

Aufruf:
    python 02_title_rules.py
"""

import json
import re
from collections import Counter

import pandas as pd
from langdetect import DetectorFactory, LangDetectException, detect

from config import ABHANDLUNGEN_CSV, TITLE_RULES_JSONL

DetectorFactory.seed = 0

# ---- Wortlisten -----------------------------------------------------------
# Die Schluessel werden in 05_build_graph.py zu SKOS-Konzepten (das:Gattung_*).
# Die deutschen Bezeichnungen stehen in GATTUNG_LABELS.

GATTUNGEN = {
    "nachruf":       r"\b(Éloge|Eloge|Gedächtni(ss|ß|s)rede|Lobrede|Nachruf|Denkrede|Leben des|Vie de)\b",
    "antrittsrede":  r"\b(Antrittsrede|Discours de réception)\b",
    "antwort":       r"^(Antwort|Réponse|Erwiederung|Erwiderung)\b|\bAntwort auf\b",
    "festrede":      r"\b(Festrede|Discours prononcé|Rede\b|Discours\b|Oratio)",
    "bericht":       r"\b(Bericht|Rapport|Jahresbericht|Gutachten)",
    "beobachtung":   r"\b(Beobachtung|Observation|Observatio|Wahrnehmung)",
    "brief":         r"\b(Brief|Schreiben (an|des|von)|Epistola|Lettre)",
    "untersuchung":  r"\b(Untersuchung|Recherches?|Examen|Disquisitio|Inquisitio|Prüfung)",
    "versuch":       r"\b(Versuch|Expérience|Experiment|Essai|Specimen)",
    "bemerkung":     r"\b(Bemerkung|Anmerkung|Remarque|Réflexion|Annotatio|Considération|Betrachtung)",
    "beschreibung":  r"\b(Beschreibung|Description|Descriptio)",
    "mitteilung":    r"\b(Mittheilung|Mitteilung|Notiz|Nachricht)",
    "beitrag":       r"\b(Beitr(ä|ae)ge?|Contribution)",
    "memoire":       r"\b(Mémoire|Memoire|Abhandlung|Dissertation|Dissertatio)\b",
}

GATTUNG_LABELS = {
    "nachruf": "Nachruf / Gedächtnisrede", "antrittsrede": "Antrittsrede",
    "antwort": "Antwort auf Antrittsrede", "festrede": "Festrede / Rede",
    "bericht": "Bericht / Gutachten", "beobachtung": "Beobachtung",
    "brief": "Brief", "untersuchung": "Untersuchung", "versuch": "Versuch / Experiment",
    "bemerkung": "Bemerkung", "beschreibung": "Beschreibung", "mitteilung": "Mitteilung",
    "beitrag": "Beitrag", "memoire": "Mémoire / Abhandlung",
}

ANLAESSE = {
    "jahrestag_friedrich_ii": r"Jahres ?tag(es)? Friedrichs II|Friedrichs des Grossen Geburtstag",
    "leibniztag":             r"Leibniz(ischen|schen)? Jahrestag|Leibniz-Sitzung|Leibnizischen",
    "geburtstag_monarch":     r"Geburtsfest(es)? Sr\.? Majestät|Geburtstag(es)? (Kaiser|König)",
}

ANLASS_LABELS = {
    "jahrestag_friedrich_ii": "Jahrestag Friedrichs II.",
    "leibniztag": "Leibniztag",
    "geburtstag_monarch": "Geburtstag des Monarchen",
}

TEIL_TYPEN = {
    "auszug":      r"^(Auszug|Extrait)",
    "fortsetzung": r"(Fortsetzung|Suite|Continuation|Continuatio)",
    "nachtrag":    r"(Nachtrag|Zusätze?|Zusatz|Addition|Supplément|Supplementum|Anhang)",
    "schluss":     r"^(Fin|Schluss|Schluß|Beschluss)",
    "abschnitt":   r"(Abschnitt|Abtheilung|Abteilung|Theil|Teil|Partie|Section|Mémoire|Dissertation|Abhandlung|Vorlesung|Band|Buch|[IVXL]+\.?$)",
}

ORDINALE = {
    "erste": 1, "erster": 1, "ersten": 1, "premier": 1, "première": 1, "primus": 1,
    "zweite": 2, "zweiter": 2, "zweiten": 2, "second": 2, "seconde": 2, "deuxième": 2,
    "dritte": 3, "dritter": 3, "dritten": 3, "troisième": 3,
    "vierte": 4, "vierter": 4, "vierten": 4, "quatrième": 4,
    "fünfte": 5, "fünfter": 5, "fünften": 5, "cinquième": 5,
    "sechste": 6, "sechster": 6, "sixième": 6,
    "siebente": 7, "siebenter": 7, "siebente": 7, "siebte": 7, "septième": 7,
    "achte": 8, "achter": 8, "huitième": 8,
    "neunte": 9, "neunter": 9, "neuvième": 9,
    "zehnte": 10, "zehnter": 10, "dixième": 10,
    "elfte": 11, "elfter": 11, "onzième": 11,
    "zwölfte": 12, "zwölfter": 12, "douzième": 12,
    "treizième": 13, "quatorzième": 14, "quinzième": 15,
}

ROEMISCH = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}

MONATE = {
    "januar": 1, "janvier": 1, "februar": 2, "février": 2, "märz": 3, "mars": 3,
    "april": 4, "avril": 4, "mai": 5, "juni": 6, "juin": 6, "juli": 7, "juillet": 7,
    "august": 8, "août": 8, "september": 9, "septembre": 9, "october": 10,
    "oktober": 10, "octobre": 10, "november": 11, "novembre": 11,
    "december": 12, "dezember": 12, "décembre": 12,
}

# Signalwoerter fuer die Sprachheuristik (Kleinschreibung, ganze Woerter)
SPRACH_MARKER = {
    "de": {"über", "ueber", "und", "der", "die", "das", "des", "von", "den", "dem",
           "einige", "einer", "eine", "zur", "zum", "nebst", "bei", "aus", "mit"},
    "fr": {"sur", "le", "la", "les", "des", "du", "et", "de", "une", "un", "à",
           "pour", "dans", "mémoire", "qui", "par", "l", "d", "quelques"},
    "la": {"de", "et", "in", "ad", "ex", "cum", "quae", "qui", "quod", "super",
           "circa", "observatio", "historia", "anno", "novum", "nova"},
}
LATEIN_ENDUNGEN = re.compile(r"\b\w+(orum|arum|ibus|ionis|ium|atis)\b", re.I)

# Beteiligte Personen: 'Mit K. RUNGE', 'Mit Bemerkungen von A. WEBER und W. VON SIEMENS'
NAME = r"(?:[A-ZÄÖÜ][a-zäöü]{0,2}\.\s*)+(?:(?:VON|VOM|DE|VAN)\s+)?[A-ZÄÖÜ][A-ZÄÖÜ\-]+"
BETEILIGTE_MUSTER = [
    ("kommentator",  r"[Mm]it (?:einer |einigen )?(?:Bemerkung(?:en)?|Anmerkung(?:en)?|Zusätzen) von"),
    ("vorwort",      r"[Mm]it einem Vorworte? von"),
    ("brief",        r"[Mm]it einem Schreiben von"),
    ("mitwirkung",   r"[Uu]nter Mitwirkung von"),
    ("mitautor",     r"\bMit"),
]


# ---- Regeln ---------------------------------------------------------------

def roemisch_zu_int(s):
    s = s.upper().rstrip(".")
    if not s or any(c not in ROEMISCH for c in s):
        return None
    total = 0
    for i, c in enumerate(s):
        v = ROEMISCH[c]
        total += -v if i + 1 < len(s) and ROEMISCH[s[i + 1]] > v else v
    return total


def erkenne_sprache(titel, reihe):
    woerter = re.findall(r"[a-zäöüéèêàâçîôûœ]+", titel.lower())
    score = Counter()
    for w in woerter:
        for lang, marker in SPRACH_MARKER.items():
            if w in marker:
                score[lang] += 1
    score["la"] += len(LATEIN_ENDUNGEN.findall(titel))
    if re.search(r"[éèêàçûÉ]|\bl'|\bd'", titel):
        score["fr"] += 2
    if re.search(r"[äöüß]|Ue|Ae|Oe", titel):
        score["de"] += 2
    if score:
        (best, n), *rest = score.most_common(2) + [(None, 0)]
        if n >= 2 and n > rest[0][1]:
            return best, "heuristik"
    # langdetect kennt kein Latein und verwechselt lateinische Titel mit
    # it/en/nl. Deshalb nur de/fr uebernehmen, sonst Latein-Signale pruefen.
    try:
        lang = detect(titel)
        if lang in {"de", "fr"}:
            return lang, "langdetect"
    except LangDetectException:
        pass
    if score["la"] >= 1 and reihe in {"01-misc", "02-hist", "03-nouv", "05-mem"}:
        return "la", "heuristik"
    # Letzter Ausweg: Hauptsprache der Reihe
    reihen_sprache = {"01-misc": "la", "02-hist": "fr", "03-nouv": "fr", "05-mem": "fr"}
    return reihen_sprache.get(reihe, "de"), "reihe"


def zerlege_teil(titel):
    if " : " not in titel:
        return titel, None, None, None
    haupt, teil = titel.split(" : ", 1)
    teil = teil.strip()
    typ = None
    for key, pattern in TEIL_TYPEN.items():
        if re.search(pattern, teil, re.I):
            typ = key
            break
    nummer = None
    for w in re.findall(r"[\wäöüéè]+", teil.lower()):
        if w in ORDINALE:
            nummer = ORDINALE[w]
            break
    if nummer is None:
        m = re.search(r"\b([IVXL]+)\b\.?", teil)
        if m:
            nummer = roemisch_zu_int(m.group(1))
    if nummer is None:
        m = re.search(r"\b(\d{1,2})\b", teil)
        if m:
            nummer = int(m.group(1))
    return haupt.strip(), teil, typ, nummer


def finde_gattungen(titel):
    return [key for key, pattern in GATTUNGEN.items() if re.search(pattern, titel)]


def finde_beteiligte(titel):
    gefunden = []
    belegt = set()
    for rolle, einleitung in BETEILIGTE_MUSTER:
        for m in re.finditer(einleitung + r"\s+(" + NAME + r"(?:(?:,\s*|\s+und\s+)" + NAME + r")*)", titel):
            if m.start() in belegt:
                continue
            belegt.add(m.start())
            for name in re.split(r",\s*|\s+und\s+", m.group(1)):
                name = name.strip()
                if name and {"name": name, "rolle": rolle} not in gefunden:
                    gefunden.append({"name": name, "rolle": rolle})
    return gefunden


def finde_daten(titel):
    daten = []
    for m in re.finditer(r"\b(\d{1,2})\.\s*([A-Za-zäöüéû]+)\s+(1[5-9]\d\d)\b", titel):
        monat = MONATE.get(m.group(2).lower())
        if monat:
            daten.append(f"{m.group(3)}-{monat:02d}-{int(m.group(1)):02d}")
    return daten


def finde_anlass(titel):
    for key, pattern in ANLAESSE.items():
        if re.search(pattern, titel, re.I):
            return key
    return None


def finde_klammern(titel):
    ergebnis = []
    for m in re.finditer(r"\[([^\]]+)\]", titel):
        inhalt = m.group(1).strip()
        if m.start() == 0:
            typ = "titel"          # '[Voltaire als Naturforscher.] Festrede ...'
        elif re.search(r"\b(S\.|MB|Bd\.|Misc\.|pag\.|p\.)\s*\d|\b1[6-9]\d\d\b.*S\.", inhalt):
            typ = "verweis"        # '[MB 1853, S. 717-732]'
        elif re.match(r"(d\.\s*i\.|d\.h\.|se\.|sc\.)", inhalt):
            typ = "aufloesung"     # '[d. i. Christian Maximilian Spener]'
        else:
            typ = "anmerkung"
        ergebnis.append({"inhalt": inhalt, "typ": typ})
    return ergebnis


def analysiere(row):
    titel = row.titel
    haupt, teil, teil_typ, teil_nummer = zerlege_teil(titel)
    sprache, sprache_quelle = erkenne_sprache(haupt, row.reihe)
    jahre = sorted({int(j) for j in re.findall(r"\b(1[5-9]\d\d)\b", titel)})
    return {
        "id": row.id,
        "sprache": sprache,
        "sprache_quelle": sprache_quelle,
        "haupttitel": haupt,
        "teil": teil,
        "teil_typ": teil_typ,
        "teil_nummer": teil_nummer,
        "gattungen": finde_gattungen(titel),
        "beteiligte": finde_beteiligte(titel),
        "daten": finde_daten(titel),
        "jahre": jahre,
        "anlass": finde_anlass(titel),
        "klammern": finde_klammern(titel),
    }


# ---- Hauptprogramm --------------------------------------------------------

def main():
    df = pd.read_csv(ABHANDLUNGEN_CSV, dtype=str)
    ergebnisse = [analysiere(row) for row in df.itertuples(index=False)]

    with open(TITLE_RULES_JSONL, "w", encoding="utf-8") as f:
        for e in ergebnisse:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    # ---- Bericht ----
    res = pd.DataFrame(ergebnisse)
    print(f"Analysiert: {len(res)} Titel -> {TITLE_RULES_JSONL.name}")
    print("Sprache:", res["sprache"].value_counts().to_dict(),
          "| Quelle:", res["sprache_quelle"].value_counts().to_dict())
    print("Gattungen:", Counter(g for gs in res["gattungen"] for g in gs).most_common())
    print(f"Ohne Gattung: {(res['gattungen'].str.len() == 0).sum()}")
    print("Teil-Typen:", res["teil_typ"].value_counts(dropna=False).to_dict())
    print("Beteiligte:", Counter(b["rolle"] for bs in res["beteiligte"] for b in bs))
    print("Anlässe:", res["anlass"].value_counts().to_dict())
    print(f"Titel mit Datum: {(res['daten'].str.len() > 0).sum()}, "
          f"mit Jahreszahl: {(res['jahre'].str.len() > 0).sum()}")
    print("Klammern:", Counter(k["typ"] for ks in res["klammern"] for k in ks))


if __name__ == "__main__":
    main()
