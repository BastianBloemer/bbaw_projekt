import { createConfig } from "./mirador-config.js";

function createViewer(url, canvasId) {
  const config = createConfig({
    manifestId: url,
    canvasId: canvasId || undefined,
  });

  return Mirador.viewer(config);
}

const params = new URLSearchParams(window.location.search);
const manifestParam = params.get("manifest");
const collectionParam = params.get("collection");
const canvasParam = params.get("canvas");

const DEFAULT_COLLECTION = "../../backend/data/manifest/curated/collection.json";

const resourceUrl = manifestParam || collectionParam || DEFAULT_COLLECTION;

// Ohne konkretes Manifest (kein "manifest"-Parameter) wird eine Sammlung
// (Schriftenreihe) statt einer einzelnen Abhandlung geoeffnet.
const isCollection = !manifestParam;

const viewer = createViewer(resourceUrl, canvasParam);

// Bei einer Sammlung zeigt Mirador die Baende-Liste erst in einem Dialog,
// nachdem der eingebaute "Zeige Sammlung"-Button einmal angeklickt wurde --
// ohne diesen Klick bleibt sowohl der Dialog als auch die Seitenleiste leer,
// obwohl die collection.json laengst geladen ist (dort liegen dann auch die
// eigentlichen, funktionierenden Links zu den Baenden -- ein Klick auf einen
// Eintrag oeffnet dessen Manifest). Deshalb wird der Button hier automatisch
// ausgeloest, sobald er im DOM erscheint, damit die Baende-Liste direkt und
// ohne Nutzerinteraktion sichtbar ist. Das aria-label ist -- anders als der
// sichtbare Button-Text -- unabhaengig von der Sprachauswahl (language: 'de'
// in mirador-config.js) immer "show collection".
if (isCollection) {
  const SHOW_COLLECTION_SELECTOR = '#my-mirador button[aria-label="show collection"]';

  const clickShowCollection = () => {
    const button = document.querySelector(SHOW_COLLECTION_SELECTOR);
    if (!button) {
      return false;
    }
    button.click();
    return true;
  };

  if (!clickShowCollection()) {
    const container = document.getElementById("my-mirador");
    const observer = new MutationObserver(() => {
      if (clickShowCollection()) {
        observer.disconnect();
      }
    });
    observer.observe(container, { childList: true, subtree: true });
  }
}