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
      const query = elements.searchInput.value.trim().toLowerCase();

      if (query.length > 0) {
        await executeSearch(query);
      }
    }
  });
}

async function executeSearch(query) {
  if (!abhandlungenCache) {
    const response = await fetch(PATH_ABHANDLUNGEN);
    abhandlungenCache = await response.json();
  }
    const results = abhandlungenCache.filter(book => {
    const searchField = (book.search || '').toLowerCase();
    const year = String(book.year || '');
    return searchField.includes(query) || year.includes(query);
  });
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