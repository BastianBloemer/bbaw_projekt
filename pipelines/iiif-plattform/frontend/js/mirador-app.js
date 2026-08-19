import { createConfig } from "./mirador-config.js";

function createViewer(url, canvasId, isCollection) {
    const config = createConfig({
        manifestId: url,
        canvasId: canvasId || undefined,
        isCollection
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
// geoeffnet, nicht eine einzelne Abhandlung -- dafuer bleibt der Index
// (Seitenleiste) aus, siehe mirador-config.js.
const isCollection = !manifestParam;

const viewer = createViewer(resourceUrl, canvasParam, isCollection);