import { startAbhandlungDownload, DOWNLOAD_ICON } from './zip-download.js';

const PATH_ABHANDLUNGEN = '../../backend/data/registers/register-abhandlungen.json';

let abhandlungenCache = null;
let elements = {};

function init() {
  elements = {
    searchInput: document.getElementById('search-input'),
    resultsContainer: document.getElementById('results-container')
  };

  elements.searchInput.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const query = elements.searchInput.value.trim();

      if (query.length > 0) {
        await executeSearch(query);
      }
    }
  });
}

// Entfernt diakritische Zeichen (È -> E, ü -> u, ...), damit die Suche nicht
// zwischen Akzent-Varianten unterscheidet.
function normalize(text) {
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

function levenshtein(a, b) {
  const m = a.length;
  const n = b.length;
  if (m === 0) return n;
  if (n === 0) return m;

  let prev = Array.from({ length: n + 1 }, (_, j) => j);
  for (let i = 1; i <= m; i++) {
    const curr = [i];
    for (let j = 1; j <= n; j++) {
      curr[j] = a[i - 1] === b[j - 1]
        ? prev[j - 1]
        : 1 + Math.min(prev[j - 1], prev[j], curr[j - 1]);
    }
    prev = curr;
  }
  return prev[n];
}

// Erlaubte Tippfehler-Distanz je Wortlaenge -- kurze Woerter bleiben exakt,
// sonst waeren Fehltreffer bei 3-4-Buchstaben-Woertern zu wahrscheinlich.
function fuzzyThreshold(wordLength) {
  if (wordLength <= 3) return 0;
  if (wordLength <= 5) return 1;
  return 2;
}

function wordMatches(queryWord, targetText) {
  if (targetText.includes(queryWord)) return true;

  const threshold = fuzzyThreshold(queryWord.length);
  if (threshold === 0) return false;

  return targetText.split(/\s+/).some(targetWord =>
    Math.abs(targetWord.length - queryWord.length) <= threshold &&
    levenshtein(queryWord, targetWord) <= threshold
  );
}

// Ablauf der Suche:
// 1. Titel/Autor jeder Abhandlung stehen bereits vorberechnet im Feld
//    "search" (register-abhandlungen.json); beim ersten Aufruf wird daraus
//    ein Cache gebaut, der pro Eintrag den akzent- und gross-/kleinschreibung-
//    freien Text ("normalizedSearch") sowie das Jahr als String enthaelt.
// 2. Die Sucheingabe wird genauso normalisiert (normalize()) und in
//    einzelne Woerter zerlegt.
// 3. Ein Eintrag ist ein Treffer, wenn entweder das Jahr die Eingabe
//    enthaelt ODER jedes Suchwort im normalisierten Suchtext vorkommt
//    (Reihenfolge der Woerter spielt keine Rolle).
// 4. "Vorkommen" ist dabei etwas fuzzy: ein Suchwort passt, wenn es als
//    Teilstring auftaucht (deckt Praefixe/Wortfragmente ab) oder wenn es zu
//    einem Wort im Suchtext nur um wenige Tippfehler abweicht
//    (Levenshtein-Distanz, siehe fuzzyThreshold() -- kurze Woerter bleiben
//    exakt, laengere erlauben 1-2 Fehler).
async function executeSearch(query) {
  if (!abhandlungenCache) {
    const response = await fetch(PATH_ABHANDLUNGEN);
    const books = await response.json();
    abhandlungenCache = books.map(book => ({
      book,
      normalizedSearch: normalize(book.search || ''),
      year: String(book.year || '')
    }));
  }

  const normalizedQuery = normalize(query);
  const queryWords = normalizedQuery.split(/\s+/).filter(Boolean);

  const results = abhandlungenCache
    .filter(({ normalizedSearch, year }) =>
      year.includes(normalizedQuery) ||
      queryWords.every(word => wordMatches(word, normalizedSearch))
    )
    .map(({ book }) => book);

  renderResults(results, query);
}

function renderResults(results, query) {
  elements.resultsContainer.innerHTML = '';

  if (results.length === 0) {
    elements.resultsContainer.innerHTML = `<div id="empty-state">Keine Ergebnisse für "${query}" gefunden.</div>`;
    return;
  }

  const hits = document.createElement('div');
  hits.id = 'hits';
  hits.textContent = `${results.length} Treffer`;
  elements.resultsContainer.appendChild(hits);

  const hitbox = document.createElement('div');
  hitbox.id = 'entry-card';

  const content = document.createElement('div');
  content.className = 'contents';

  results.forEach(book => {
    const work = document.createElement('div');
    work.className = 'work';

    const author = book.author ? ` ${book.author}` : '';
    const year = book.year ? ` | ${book.year}` : '';
    const anhang = book.anhang ? ` | ${book.anhang}` : '';
    const schriftenreihe = book.schriftenreihe ? ` | ${book.schriftenreihe}` : '';

    // Hier wird der Link zum Viewer zusammengesetzt
    const manifestUrl = book.manifest;
    const canvasId = book.startCanvas;
    let viewerLink = `viewer.html?manifest=${manifestUrl}`;
    if (canvasId) {
      viewerLink += `&canvas=${encodeURIComponent(canvasId)}`;
    }
    const beziehungen = book.textbeziehungen ? `<div class="work-beziehungen">${book.textbeziehungen}</div>` : '';

    work.innerHTML = `
      <a class="work-title" href="${viewerLink}" target="_blank" rel="noopener">${book.title}</a>
      <button type="button" class="work-download" aria-label="Abhandlung herunterladen">${DOWNLOAD_ICON}<span class="work-download-popup">Abhandlung herunterladen</span></button>
      <div class="work-meta">${author}${year}${anhang}${schriftenreihe}</div>
      ${beziehungen}
    `;

    work.querySelector('.work-download').onclick = () => startAbhandlungDownload(work.querySelector('.work-download'), book);

    content.appendChild(work);
  });

  hits.appendChild(content);
  elements.resultsContainer.appendChild(hits);
}

document.addEventListener('DOMContentLoaded', init);