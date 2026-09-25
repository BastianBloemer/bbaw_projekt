import csv

INPUT_CSV = "pipelines/iiif-plattform/backend/data/metadata/curated/merged_df.csv"
OUTPUT_RIS = "pipelines/iiif-plattform/backend/data/metadata/curated/merged_df.ris"


# Kuerzel (wie in index.html in eckigen Klammern angegeben) -> voller Titel
# der Schriftenreihe. Quelle: index.html der Plattform.
SERIES_TITLES = {
    "01-misc": "Miscellanea Berolinensia ad incrementum scientiarum, ex scriptis Societati Regiae Scientiarum exhibitis edita",
    "02-hist": "Histoire de l'Académie Royale des Sciences et des Belles-Lettres de Berlin",
    "03-nouv": "Nouveaux Mémoires de l'Académie Royale des Sciences et Belles-Lettre",
    "04-phys": "Physikalische und medicinische Abhandlungen der Königlichen Academie der Wissenschaften zu Berlin",
    "05-mem": "Mémoires de l'Académie Royale des Sciences et Belles-Lettres",
    "06-samml": "Sammlung der deutschen Abhandlungen, welche in der Königlichen Akademie der Wissenschaften zu Berlin vorgelesen worden",
    "07-abh": "Abhandlungen der Königlichen Preußischen Akademie der Wissenschaften zu Berlin",
    "08-verh": "Bericht über die zur Bekanntmachung geeigneten Verhandlungen der Königlich Preußischen Akademie der Wissenschaften zu Berlin",
    "09-mon": "Monatsberichte der Königlich Preußischen Akademie der Wissenschaften zu Berlin",
    "10-sitz": "Sitzungsberichte der Königlich Preußischen Akademie der Wissenschaften zu Berlin",
    "ak-gesch": "Monographien zur Geschichte der Akademie bis 1900",
}

# Sammelt Kuerzel, die nicht in SERIES_TITLES gefunden wurden, damit am
# Ende eine Warnung ausgegeben werden kann statt sie stillschweigend
# unaufgeloest zu lassen.
unresolved_series_codes = set()


def resolve_series_title(code):
    """Loest ein Schriftenreihen-Kuerzel zum vollen Titel auf.

    Faellt auf den urspruenglichen Wert zurueck, falls das Kuerzel nicht
    bekannt ist (z.B. Tippfehler oder neue Schriftenreihe), merkt sich
    das aber fuer eine Warnung am Ende des Laufs.
    """
    key = code.strip().lower()
    if key in SERIES_TITLES:
        return SERIES_TITLES[key]
    unresolved_series_codes.add(code)
    return code


def split_authors(raw):
    """Autoren sind durch ';' getrennt, jeder bekommt eine eigene AU-Zeile."""
    if not raw:
        return []
    return [a.strip() for a in raw.split(";") if a.strip()]


def row_to_ris(row):
    lines = ["TY  - JOUR"]

    if row.get("ID", "").strip():
        lines.append(f"ID  - {row['ID'].strip()}")

    for author in split_authors(row.get("Autor", "")):
        lines.append(f"AU  - {author}")

    if row.get("Titel", "").strip():
        lines.append(f"TI  - {row['Titel'].strip()}")

    if row.get("Schriftenreihe", "").strip():
        lines.append(f"T2  - {resolve_series_title(row['Schriftenreihe'])}")

    if row.get("Jahr", "").strip():
        lines.append(f"PY  - {row['Jahr'].strip()}")

    if row.get("Band", "").strip():
        lines.append(f"VL  - {row['Band'].strip()}")

    if row.get("Link", "").strip():
        lines.append(f"UR  - {row['Link'].strip()}")

    if row.get("Startseite", "").strip():
        lines.append(f"SP  - {row['Startseite'].strip()}")

    if row.get("Endseite", "").strip():
        lines.append(f"EP  - {row['Endseite'].strip()}")

    # Kein RIS-Standardfeld dafuer vorhanden -- als Notiz uebernehmen,
    # damit die Information nicht verloren geht.
    if row.get("Abbilder", "").strip():
        lines.append(f"N1  - Abbilder: {row['Abbilder'].strip()}")

    if row.get("Textbeziehungen", "").strip():
        lines.append(f"N1  - Textbeziehungen: {row['Textbeziehungen'].strip()}")

    lines.append("ER  - ")
    return lines


def main():
    with open(INPUT_CSV, "r", encoding="utf-8-sig", newline="") as infile:
        reader = csv.DictReader(infile)
        entries = [row_to_ris(row) for row in reader]

    with open(OUTPUT_RIS, "w", encoding="utf-8") as outfile:
        for entry in entries:
            outfile.write("\n".join(entry))
            outfile.write("\n\n")

    print(f"{len(entries)} Eintraege nach '{OUTPUT_RIS}' geschrieben.")

    if unresolved_series_codes:
        print(
            "Warnung: Diese Werte in 'Schriftenreihe' konnten keinem "
            f"bekannten Kuerzel zugeordnet werden und wurden unveraendert "
            f"uebernommen: {sorted(unresolved_series_codes)}"
        )


if __name__ == "__main__":
    main()