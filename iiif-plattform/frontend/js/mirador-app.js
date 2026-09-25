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
const resourceUrl = manifestParam || collectionParam || DEFAULT_COLLECTION;
const isCollection = !manifestParam;
const viewer = createViewer(resourceUrl, canvasParam);


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