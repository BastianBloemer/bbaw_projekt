"""
01 - Bereinigung der Metadaten
------------------------------
Liest merged_df.csv (und fuer die Reihentitel merged_df.ris) und schreibt
vier bereinigte Tabellen nach knowledge-graph/data/kg/:

    abhandlungen.csv  eine Zeile pro Abhandlung (Jahr ergaenzt, Abbilder zerlegt,
                      Autor normalisiert)
    relationen.csv    Textbeziehungen als Kantenliste (quelle, typ, ziel)
    reihen.csv        Schriftenreihen mit vollem Titel und Zeitraum
    autoren.csv       normalisierte Autoren mit Anzahl der Abhandlungen

Aufruf:
    python 01_clean.py
"""

import re
from collections import Counter

import pandas as pd

from config import (ABHANDLUNGEN_CSV, AUTOREN_CSV, RELATIONEN_CSV, REIHEN_CSV,
                    SOURCE_CSV, SOURCE_RIS, slugify)

# ---- Konfiguration --------------------------------------------------------

ANONYM = "Ohne Angabe Des Verfassers"

# Manuelle Korrekturen fuer Autorennamen, die nicht dem Schema
# "Nachname, Vorname" folgen. Schluessel = Wert in der CSV.
AUTOR_KORREKTUREN = {
    "Friedrich Ii König von Preussen": "Friedrich II., Preußen, König",
    "Friedrich": "Friedrich II., Preußen, König",
    "Wilhelm Adolf Prinz von Braunschweig": "Wilhelm Adolf, Braunschweig-Wolfenbüttel, Prinz",
}

# Zahlwoerter, die in der Spalte "Abbilder" vorkommen
ZAHLWOERTER = {"einer": 1, "eine": 1, "einem": 1, "zwei": 2, "drei": 3, "vier": 4}


# ---- Hilfsfunktionen ------------------------------------------------------

def read_ris_series_titles(path):
    """Liest aus der RIS-Datei den Reihentitel (T2) pro ID."""
    titles = {}
    current_id, current_t2 = None, None
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            if line.startswith("ID  - "):
                current_id = line[6:].strip()
            elif line.startswith("T2  - "):
                current_t2 = line[6:].strip()
            elif line.startswith("ER  -"):
                if current_id and current_t2:
                    titles[current_id] = current_t2
                current_id, current_t2 = None, None
    return titles


def ergaenze_jahre(df):
    """
    Fehlende Jahre werden in dieser Reihenfolge ergaenzt:
      1. haeufigstes bekanntes Jahr innerhalb desselben Bandes (Reihe + Band)
      2. Jahreszahl am Anfang der Bandbezeichnung (z.B. '1882-1', '1856'),
         aber nur, wenn sie im bekannten Zeitraum der Reihe liegt
    Die Spalte 'jahr_quelle' dokumentiert, woher das Jahr stammt.
    """
    df["jahr"] = pd.to_numeric(df["Jahr"], errors="coerce").astype("Int64")
    df["jahr_quelle"] = df["jahr"].notna().map({True: "csv", False: None})

    band_modus = (df.dropna(subset=["jahr"])
                    .groupby(["Schriftenreihe", "Band"])["jahr"]
                    .agg(lambda s: s.mode().iloc[0]))
    reihen_zeitraum = df.dropna(subset=["jahr"]).groupby("Schriftenreihe")["jahr"].agg(["min", "max"])

    for idx in df.index[df["jahr"].isna()]:
        reihe, band = df.at[idx, "Schriftenreihe"], df.at[idx, "Band"]
        if (reihe, band) in band_modus.index:
            df.at[idx, "jahr"] = band_modus[(reihe, band)]
            df.at[idx, "jahr_quelle"] = "band_modus"
            continue
        m = re.match(r"^(1[6-9]\d\d)", str(band))
        if m and reihe in reihen_zeitraum.index:
            jahr = int(m.group(1))
            lo, hi = reihen_zeitraum.loc[reihe, "min"], reihen_zeitraum.loc[reihe, "max"]
            if lo <= jahr <= hi:
                df.at[idx, "jahr"] = jahr
                df.at[idx, "jahr_quelle"] = "band_nummer"
    return df


def zerlege_abbilder(text):
    """'mit 2 Tafeln und 1 Tabelle' -> (2, 1, False). Figuren nur als Flag."""
    if not isinstance(text, str):
        return 0, 0, False
    t = text.lower()

    def zaehle(pattern):
        n = 0
        for m in re.finditer(r"(\d+|" + "|".join(ZAHLWOERTER) + r")\s+(?:doppel)?" + pattern, t):
            z = m.group(1)
            n += int(z) if z.isdigit() else ZAHLWOERTER[z]
        return n

    tafeln = zaehle(r"tafel")
    tabellen = zaehle(r"tabelle")
    # "mit Tafel O, Fig. 1-14" -> mindestens eine Tafel
    if tafeln == 0 and "tafel" in t:
        tafeln = 1
    if tabellen == 0 and "tabelle" in t:
        tabellen = 1
    figuren = bool(re.search(r"\bfig", t))
    return tafeln, tabellen, figuren


def normalisiere_autoren(df):
    """Setzt die Spalten 'autor' (normalisierter Name) und 'autor_key' (Slug)."""
    roh = df["Autor"].fillna(ANONYM).str.strip()
    voll = sorted({a for a in roh if "," in a})
    nachname_zu_voll = {}
    for name in voll:
        nachname_zu_voll.setdefault(name.split(",")[0].strip(), set()).add(name)

    def normalisiere(name):
        if name == ANONYM:
            return None
        if name in AUTOR_KORREKTUREN:
            return AUTOR_KORREKTUREN[name]
        if "," not in name:
            # Nur Nachname (z.B. 'Böckh'): eindeutig aufloesbar?
            kandidaten = nachname_zu_voll.get(name, set())
            if len(kandidaten) == 1:
                return next(iter(kandidaten))
        return name

    df["autor"] = roh.map(normalisiere)
    df["autor_key"] = df["autor"].map(lambda a: slugify(a) if isinstance(a, str) else None)
    # Schreibvarianten mit gleichem Slug (z.B. 'Du Bois-Reymond' / 'du Bois-Reymond')
    # werden zusammengefuehrt; es gilt die haeufigste Schreibweise.
    kanonisch = df.dropna(subset=["autor_key"]).groupby("autor_key")["autor"].agg(
        lambda s: s.value_counts().index[0])
    df["autor"] = df["autor_key"].map(kanonisch)
    return df


def zerlege_relationen(df):
    """
    'Antwort: NEU-ANTWORT-1 | Verweis: 094924716' -> Kanten.
    Semantik laut Stichprobe: Die Bezeichnung benennt die ROLLE DES ZIELS,
    d.h. 'Fortsetzung: X' bedeutet 'X ist die Fortsetzung dieser Abhandlung'.
    """
    kanten = []
    for quelle, feld in df[["ID", "Textbeziehungen"]].dropna().itertuples(index=False):
        for teil in feld.split("|"):
            if ":" not in teil:
                continue
            typ, ziel = (s.strip() for s in teil.split(":", 1))
            kanten.append({"quelle": quelle, "typ": typ, "ziel": ziel})
    rel = pd.DataFrame(kanten).drop_duplicates()
    bekannte = set(df["ID"])
    rel["ziel_vorhanden"] = rel["ziel"].isin(bekannte)
    return rel


# ---- Hauptprogramm --------------------------------------------------------

def main():
    df = pd.read_csv(SOURCE_CSV, dtype=str, encoding="utf-8-sig")
    print(f"Gelesen: {len(df)} Abhandlungen aus {SOURCE_CSV.name}")

    df = ergaenze_jahre(df)
    df = normalisiere_autoren(df)

    abb = df["Abbilder"].map(zerlege_abbilder)
    df["tafeln"] = abb.map(lambda x: x[0])
    df["tabellen"] = abb.map(lambda x: x[1])
    df["figuren"] = abb.map(lambda x: x[2])

    df["band_key"] = df["Schriftenreihe"] + "/" + df["Band"]
    df["ist_ppn"] = df["ID"].str.match(r"^\d{8}[\dX]$")

    # Reihentitel aus RIS
    ris = read_ris_series_titles(SOURCE_RIS)
    df["reihentitel"] = df["ID"].map(ris)

    abhandlungen = df.rename(columns={
        "ID": "id", "Titel": "titel", "Link": "link", "Schriftenreihe": "reihe",
        "Band": "band", "Startseite": "startseite", "Endseite": "endseite",
        "Abbilder": "abbilder", "Autor": "autor_original",
    })[["id", "ist_ppn", "titel", "autor", "autor_key", "autor_original",
        "jahr", "jahr_quelle", "reihe", "band", "band_key", "startseite", "endseite",
        "abbilder", "tafeln", "tabellen", "figuren", "link"]]
    abhandlungen.to_csv(ABHANDLUNGEN_CSV, index=False)

    rel = zerlege_relationen(df)
    rel.to_csv(RELATIONEN_CSV, index=False)

    reihen = (df.groupby("Schriftenreihe")
                .agg(titel=("reihentitel", lambda s: Counter(s.dropna()).most_common(1)[0][0]
                            if s.notna().any() else None),
                     jahr_von=("jahr", "min"), jahr_bis=("jahr", "max"),
                     baende=("Band", "nunique"), abhandlungen=("ID", "size"))
                .reset_index().rename(columns={"Schriftenreihe": "kuerzel"}))
    reihen.to_csv(REIHEN_CSV, index=False)

    autoren = (abhandlungen.dropna(subset=["autor"])
                 .groupby(["autor_key", "autor"])
                 .agg(abhandlungen=("id", "size"), jahr_von=("jahr", "min"),
                      jahr_bis=("jahr", "max"),
                      reihen=("reihe", lambda s: ";".join(sorted(set(s)))))
                 .reset_index().sort_values("abhandlungen", ascending=False))
    autoren.to_csv(AUTOREN_CSV, index=False)

    # ---- Bericht ----
    print(f"Jahr fehlt noch bei {abhandlungen['jahr'].isna().sum()} Abhandlungen")
    print("Jahr-Quelle:", abhandlungen["jahr_quelle"].value_counts(dropna=False).to_dict())
    print(f"Autoren: {len(autoren)}, anonym: {abhandlungen['autor'].isna().sum()}, "
          f"nur Nachname: {(~abhandlungen['autor'].fillna(',').str.contains(',')).sum()}")
    print(f"Relationen: {len(rel)} Kanten, Typen: {rel['typ'].value_counts().to_dict()}")
    print(f"Reihen ohne Titel: {reihen['titel'].isna().sum()}")
    print(f"Geschrieben: {ABHANDLUNGEN_CSV.name}, {RELATIONEN_CSV.name}, "
          f"{REIHEN_CSV.name}, {AUTOREN_CSV.name}")


if __name__ == "__main__":
    main()
