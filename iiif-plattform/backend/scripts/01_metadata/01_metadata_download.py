#!/usr/bin/env python3
"""
Lädt die Metadaten der "Digitalisierten Akademieschriften" aus dem GBV-OPAC
der BBAW-Bibliothek (https://lbsvz1.gbv.de/LNG=DU/DB=38/) herunter.

Ersetzt den bisherigen manuellen Export und erzeugt dieselben zwei Dateien
wie zuvor von Hand heruntergeladen:
  - gbv-download-<Suchbegriff>.ris   (RIS-Format für Literaturverwaltung)
  - gbv-vollanzeige.txt              (Vollanzeige-Textformat)

Vorgehen: Suche im Index [ALL] nach dem Suchbegriff ausführen, danach die
Trefferliste in Blöcken (Download-Limit des OPAC: 500 Titel) in beiden
Formaten herunterladen und zusammenführen.

Beispiel:
    python 01_metadata_download.py
    python 01_metadata_download.py --dry-run
"""

import argparse
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

BASE_URL = "https://lbsvz1.gbv.de"
DB = "38"
LNG = "DU"
IKT_ALL = "1016"  # [ALL] Alle Wörter
SRT = "YOP"  # sortiert nach Erscheinungsjahr
SEARCH_TERM = "Digitalisierte Akademieschriften"
CHUNK_SIZE = 500  # vom OPAC dokumentiertes Download-Maximum pro Anfrage

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; bbaw-metadata-downloader/1.0)"}

SID_RE = re.compile(r"SID=([a-f0-9-]+)")
HITS_RE = re.compile(r"HITS=(\d+)")
VOLLANZEIGE_HEADER_RE = re.compile(r"\A.*?Dies sind Treffer[^\n]*\n\n", re.S)


def start_session(session: requests.Session) -> str:
    r = session.get(f"{BASE_URL}/LNG={LNG}/DB={DB}/", headers=HEADERS, timeout=30)
    r.raise_for_status()
    match = SID_RE.search(r.text)
    if not match:
        raise RuntimeError("Konnte keine Session-ID von der GBV-Startseite ermitteln.")
    return match.group(1)


def run_search(session: requests.Session, sid: str, term: str) -> int:
    params = {"ACT": "SRCHA", "IKT": IKT_ALL, "TRM": term, "SRT": SRT}
    url = f"{BASE_URL}/DB={DB}/LNG={LNG}/SID={sid}/CMD"
    r = session.get(url, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    match = HITS_RE.search(r.text)
    if not match:
        raise RuntimeError("Konnte die Trefferzahl nicht aus der Ergebnisseite lesen.")
    return int(match.group(1))


def download_chunk(session: requests.Session, sid: str, hits: int, frst: int, last: int, fmt: str) -> str:
    data = {
        "FRST": str(frst),
        "LAST": str(last),
        "NORND": "1",
        "HITS": str(hits),
        "PRS": fmt,
        "CHARSET_ONCE": "UTF-8",
        "DOWNLOAD": "Y",
        "EMAIL": "",
        "download_mode": "Speichern",
    }
    if fmt == "LOAN4DWN":
        data["MAXLINE"] = "77"
    else:
        # vom OPAC-Javascript gesetzt für alle Nicht-Anzeige-Formate (u.a. RIS)
        data["XPNOFF"] = "1"

    url = f"{BASE_URL}/DB={DB}/LNG={LNG}/SID={sid}/DWN"
    r = session.post(url, data=data, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.text.replace("\r\n", "\n").replace("\r", "\n")


def download_all(session: requests.Session, sid: str, hits: int, fmt: str, chunk_size: int, sleep: float, retries: int) -> str:
    parts = []
    frst = 1
    while frst <= hits:
        last = min(frst + chunk_size - 1, hits)
        for attempt in range(1, retries + 1):
            try:
                chunk = download_chunk(session, sid, hits, frst, last, fmt)
                break
            except requests.RequestException as exc:
                if attempt == retries:
                    raise
                print(f"  Fehler ({exc}), Versuch {attempt}/{retries} ...", file=sys.stderr)
                time.sleep(sleep * attempt)
        if fmt == "LOAN4DWN":
            chunk = VOLLANZEIGE_HEADER_RE.sub("", chunk, count=1)
        parts.append(chunk)
        print(f"  {fmt}: {frst}-{last} von {hits} geladen")
        frst = last + 1
        time.sleep(sleep)
    return "".join(parts)


def backup_if_exists(path: Path) -> None:
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = path.with_name(f"{path.stem}.bak-{stamp}{path.suffix}")
        path.rename(backup)
        print(f"Bestehende Datei gesichert nach {backup}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--term", default=SEARCH_TERM, help="Suchbegriff im Index [ALL] (Standard: %(default)r)")
    parser.add_argument("--output-dir", type=Path, default=None, help="Zielverzeichnis (Standard: data/metadata/raw relativ zu diesem Skript)")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE, help="Titel pro Download-Anfrage (Standard: %(default)s)")
    parser.add_argument("--sleep", type=float, default=1.0, help="Wartezeit zwischen Anfragen in Sekunden (Standard: %(default)s)")
    parser.add_argument("--retries", type=int, default=3, help="Wiederholungsversuche pro Anfrage bei Fehlern")
    parser.add_argument("--dry-run", action="store_true", help="Nur suchen und Trefferzahl anzeigen, nichts herunterladen")
    args = parser.parse_args()

    output_dir = args.output_dir or Path(__file__).resolve().parents[2] / "data" / "metadata" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    print("Starte Session beim GBV-OPAC ...")
    sid = start_session(session)
    print(f"Suche nach {args.term!r} ...")
    hits = run_search(session, sid, args.term)
    print(f"{hits} Treffer gefunden.")

    if args.dry_run:
        return

    print("Lade RIS-Format ...")
    ris_text = download_all(session, sid, hits, "RIS", args.chunk_size, args.sleep, args.retries)
    ris_path = output_dir / f"gbv-ris.ris"
    backup_if_exists(ris_path)
    ris_path.write_text(ris_text, encoding="utf-8")
    print(f"RIS gespeichert: {ris_path} ({ris_text.count('ER  -')} Einträge)")

    print("Lade Vollanzeige-Format ...")
    voll_text = download_all(session, sid, hits, "LOAN4DWN", args.chunk_size, args.sleep, args.retries)
    voll_path = output_dir / "gbv-vollanzeige.txt"
    backup_if_exists(voll_path)
    voll_path.write_text(voll_text, encoding="utf-8")
    print(f"Vollanzeige gespeichert: {voll_path}")


if __name__ == "__main__":
    main()
