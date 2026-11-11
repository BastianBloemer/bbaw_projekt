#!/usr/bin/env python3
"""
Erzeugt das Personenregister für das Frontend.

Gruppiert die Abhandlungen nach Autor:in und diese nach Anfangsbuchstaben
(Akzente werden ignoriert, z.B. É -> E).

Eingabe:  data/registers/register-abhandlungen.json
Ausgabe:  data/registers/register-personen.json
"""

import json
import unicodedata
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
REGISTER = DATA_DIR / "registers" / "register-abhandlungen.json"
OUTPUT = DATA_DIR / "registers" / "register-personen.json"


def make_key(name: str) -> str:
    return name.lower().replace(";", "|").strip()


def display_name(name: str) -> str:
    return name


def get_base_letter(char: str) -> str:
    normalized = unicodedata.normalize("NFD", char)
    base_char = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return base_char.upper()


def main():
    # 1. ABHANDLUNGEN LADEN
    with open(REGISTER, encoding="utf8") as f:
        books = json.load(f)

    # Zweistufiger defaultdict: Buchstabe -> Personenschlüssel -> Personen-Objekt
    persons = defaultdict(lambda: defaultdict(lambda: {
        "anzeige": "",
        "werke": [],
    }))

    # 2. PERSONEN-INDEX ERSTELLEN
    for book in books:
        author = book.get("author", "").strip()
        if not author:
            continue

        key = make_key(author)
        display = display_name(author)

        # Stammbuchstabe ermitteln (z.B. É -> E)
        first_letter = get_base_letter(display[0])

        person_entry = persons[first_letter][key]
        person_entry["anzeige"] = display

        # Das Abhandlungs-Objekt (book) wird 1:1 als Werk übernommen
        # (enthaelt bereits "anhang" und "textbeziehungen" aus register-abhandlungen)
        person_entry["werke"].append(book)

    # 3. ALPHABETISCH SORTIEREN
    sorted_persons = {}
    for letter in sorted(persons.keys()):
        sorted_letter_group = {}
        for key in sorted(persons[letter].keys()):
            person_data = persons[letter][key]
            # Werke der Person alphabetisch nach Titel sortieren
            person_data["werke"].sort(key=lambda w: w.get("title", ""))
            sorted_letter_group[key] = person_data
        sorted_persons[letter] = sorted_letter_group

    # 4. OUTPUT SPEICHERN
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf8") as f:
        json.dump(sorted_persons, f, ensure_ascii=False, indent=2)

    total_persons = sum(len(group) for group in sorted_persons.values())
    print(f"{total_persons} Personen in {len(sorted_persons)} Buchstaben-Gruppen geschrieben.")


if __name__ == "__main__":
    main()
