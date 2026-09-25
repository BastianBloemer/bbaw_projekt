"""
IIIF-OCR ueber Open WebUI
--------------------------
Liest ein IIIF-Presentation-Manifest (v2 oder v3) aus, baut daraus die
IIIF-Image-API-URLs der einzelnen Seiten und schickt jede Seite ueber die
OpenAI-kompatible Chat-Completions-API von Open WebUI an ein Vision-Modell.
Das Ergebnis wird als Textdatei gespeichert.

Installation:
    pip install requests --break-system-packages

API-Key:
    In Open WebUI unter Settings -> Account -> API Keys erzeugen und
    als Umgebungsvariable setzen:
        export OPENWEBUI_TOKEN="dein-key"
"""

import os
import time
import requests

# ---- Konfiguration -------------------------------------------------------

OPENWEBUI_URL = "http://localhost:3000"  # deine Open WebUI-Instanz, anpassen
OPENWEBUI_TOKEN = os.environ["OPENWEBUI_TOKEN"]
MODEL = "gpt-4o"  # Name des in Open WebUI konfigurierten Vision-Modells, anpassen

MANIFEST_URL = "https://beispiel-server.de/iiif/werk123/manifest.json"  # anpassen
OUTPUT_FILE = "transkription.txt"
IMAGE_SIZE = "2000,"  # IIIF-Size-Parameter, z.B. Breite 2000px, Hoehe proportional
PROMPT = """\
Du transkribierst die Textseite auf dem Bild. Gib deine Ausgabe als Markdown
zurueck und befolge dabei diese Regeln:

1. Fliesstext: Transkribiere wortgetreu, mit Zeilenumbruechen und Absaetzen
   wie im Original. Erkannte Ueberschriften als Markdown-Header (#, ##, ...)
   ausgeben.

2. Tabellen: NICHT zeichengetreu transkribieren. Gib stattdessen die
   Struktur (Zeilen, Spalten, Kopfzeile) als Markdown-Tabelle wieder. Ist
   die Tabelle dafuer zu komplex oder unklar, beschreibe Aufbau und Inhalt
   stattdessen in 1-3 Saetzen in Prosa.

3. Mathematische Formeln: Gib jede Formel in LaTeX wieder (Inline mit
   $...$, abgesetzt mit $$...$$). Ergaenze bei komplexen/mehrdeutigen
   Formeln in Klammern eine kurze Erlaeuterung, was die Formel ausdrueckt.

4. Layout-Elemente: Kennzeichne explizit, z.B.:
   [FUSSNOTE] ... / [MARGINALIE] ... / [BILDUNTERSCHRIFT] ... /
   [KOPFZEILE] ... / [SEITENZAHL] ...
   Bei mehrspaltigem Layout: erst linke, dann rechte Spalte transkribieren,
   Spaltenwechsel mit [SPALTE 2] markieren.

5. Unleserliche Stellen mit [unleserlich] kennzeichnen statt zu raten.

Gib ausschliesslich die Markdown-Ausgabe zurueck, ohne einleitende Kommentare.
"""

HEADERS = {
    "Authorization": f"Bearer {OPENWEBUI_TOKEN}",
    "Content-Type": "application/json",
}


# ---- Manifest auslesen -----------------------------------------------------

def get_image_urls(manifest_url: str) -> list[str]:
    """Extrahiert IIIF-Image-API-URLs aus einem v2- oder v3-Manifest."""
    manifest = requests.get(manifest_url, timeout=30).json()
    urls = []

    if "sequences" in manifest:  # IIIF Presentation API v2
        canvases = manifest["sequences"][0]["canvases"]
        for canvas in canvases:
            service = canvas["images"][0]["resource"]["service"]
            image_id = service["@id"]
            urls.append(f"{image_id}/full/{IMAGE_SIZE}/0/default.jpg")

    elif "items" in manifest:  # IIIF Presentation API v3
        for canvas in manifest["items"]:
            body = canvas["items"][0]["items"][0]["body"]
            image_id = body["service"][0]["id"]
            urls.append(f"{image_id}/full/{IMAGE_SIZE}/0/default.jpg")

    else:
        raise ValueError("Unbekanntes Manifest-Format")

    return urls


# ---- Eine Seite transkribieren ---------------------------------------------

def transcribe_page(image_url: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
    }
    response = requests.post(
        f"{OPENWEBUI_URL}/api/chat/completions",
        headers=HEADERS,
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


# ---- Hauptlauf ---------------------------------------------------------

def main():
    image_urls = get_image_urls(MANIFEST_URL)
    print(f"{len(image_urls)} Seiten gefunden.")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for i, url in enumerate(image_urls, start=1):
            print(f"Transkribiere Seite {i}/{len(image_urls)} ...")
            try:
                text = transcribe_page(url)
            except Exception as e:
                text = f"[FEHLER bei Seite {i}: {e}]"
            f.write(f"\n\n--- Seite {i} ---\n\n{text}")
            time.sleep(0.5)  # kleine Pause, um Rate Limits zu schonen

    print(f"Fertig. Ergebnis in {OUTPUT_FILE}")


if __name__ == "__main__":
    main()