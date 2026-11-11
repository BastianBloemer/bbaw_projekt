#!/usr/bin/env python3
"""
Erzeugt das Begriffsregister (Schlagwörter aus den Titeln) für das Frontend.

Zerlegt jeden Abhandlungstitel mit spaCy, lemmatisiert die Wörter und
filtert Stoppwörter (de/fr/la) sowie Personennamen heraus. Die Begriffe
werden nach Anfangsbuchstaben gruppiert.

Benötigt die spaCy-Modelle de_core_news_sm und fr_core_news_sm
(stehen in requirements.txt).

Eingabe:  data/registers/register-abhandlungen.json
Ausgabe:  data/registers/register-begriffe.json
"""

import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import spacy

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
INPUT_FILE = DATA_DIR / "registers" / "register-abhandlungen.json"
OUTPUT_FILE = DATA_DIR / "registers" / "register-begriffe.json"

KNOWN_NAME_VARIANTS = set()


def extract_names_from_json(entries: list[dict]) -> set[str]:
    names = set()
    for entry in entries:
        author_str = entry.get("author", "")
        if author_str:
            raw_names = re.findall(r"\b[a-zA-ZäöüßÄÖÜàâæçéèêëîïôœùûüÿÀÂÆÇÉÈÊËÎÏÔŒÙÛÜŸ]+\b", author_str)
            for name in raw_names:
                names.add(name.lower())
    return names


def extract_keywords(text: str, nlp_de, stop_words: set[str], author_names: set[str]) -> set[str]:
    doc = nlp_de(text)
    spacy_names = {
        word.lower()
        for ent in doc.ents
        if ent.label_ in ("PER", "PERSON")
        for word in re.findall(r"\b\w+\b", ent.text)
    }

    all_names_to_ignore = author_names | spacy_names | KNOWN_NAME_VARIANTS

    # Lemmatisierung: unterschiedliche Wortformen (z.B. "Versuche"/"Versuchen"/
    # "Versuchs") werden ueber token.lemma_ auf ihre Grundform ("Versuch")
    # zusammengefuehrt, damit sie im Register nicht als separate Begriffe
    # auftauchen.
    keywords = set()
    for token in doc:
        if not token.is_alpha:
            continue
        word_lower = token.text.lower()
        lemma = token.lemma_
        if (word_lower not in stop_words
                and word_lower not in all_names_to_ignore
                and len(lemma) >= 3):
            keywords.add(lemma.capitalize())

    return keywords


def get_base_letter(char: str) -> str:
    normalized = unicodedata.normalize("NFD", char)
    base_char = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return base_char.upper()


def main():
    # 1. DATEI LADEN
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"--> {len(data)} Einträge geladen.")
    except FileNotFoundError:
        print(f"Fehler: Datei unter '{INPUT_FILE}' wurde nicht gefunden.")
        sys.exit(1)

    # 2. SPACY & FILTER VORBEREITEN
    nlp_de = spacy.load("de_core_news_sm")
    nlp_fr = spacy.load("fr_core_news_sm")
    nlp_la = spacy.blank("la")

    stop_words = (
        nlp_de.Defaults.stop_words
        | nlp_fr.Defaults.stop_words
        | nlp_la.Defaults.stop_words
    )
    author_names = extract_names_from_json(data)

    # 3. REGISTER ERSTELLEN
    nested_index = defaultdict(lambda: defaultdict(list))

    for entry in data:
        keywords = extract_keywords(entry.get("title", ""), nlp_de, stop_words, author_names)

        for term in keywords:
            first_letter = get_base_letter(term[0])
            # Das Abhandlungs-Objekt (entry) wird 1:1 übernommen
            # (enthaelt bereits "anhang" und "textbeziehungen" aus register-abhandlungen)
            nested_index[first_letter][term].append(entry)

    # Alphabetische Sortierung
    sorted_grouped_index = {}
    for letter in sorted(nested_index.keys()):
        sorted_grouped_index[letter] = dict(sorted(nested_index[letter].items()))

    # 4. OUTPUT SPEICHERN
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_grouped_index, f, ensure_ascii=False, indent=2)

    print(f"--> Nach Buchstaben sortiertes Begriff-Register gespeichert unter: '{OUTPUT_FILE}'")


if __name__ == "__main__":
    main()
