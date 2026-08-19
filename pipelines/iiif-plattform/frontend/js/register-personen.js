import { startAbhandlungDownload, DOWNLOAD_ICON } from './zip-download.js';

const PATH_PERSONEN = '../../backend/data/registers/register-personen.json';
let personenData = null;
let currentLetter = null;

export async function renderPersonenRegister() {
  const alphabetNav = document.getElementById('alphabet-nav');
  const container = document.getElementById('entries-container');

  if (!personenData) {
    const res = await fetch(PATH_PERSONEN);
    personenData = await res.json();
  }

  const letters = Object.keys(personenData).sort();
  if (!currentLetter) currentLetter = letters[0];

  renderAlphabet(alphabetNav, container, letters);
  renderEntries(container);
}

function renderAlphabet(navEl, containerEl, letters) {
  navEl.innerHTML = '';
  letters.forEach(letter => {
    const btn = document.createElement('div');
    btn.className = `letter ${letter === currentLetter ? 'active' : ''}`;
    btn.textContent = letter;
    btn.onclick = () => {
      currentLetter = letter;
      navEl.querySelector('.active')?.classList.remove('active');
      btn.classList.add('active');
      renderEntries(containerEl);
    };
    navEl.appendChild(btn);
  });
}

function renderEntries(containerEl) {
  containerEl.innerHTML = '';

  Object.values(personenData[currentLetter] || {}).forEach(person => {
    const card = document.createElement('div');
    card.className = 'entry collapsed';

    const header = document.createElement('div');
    header.className = 'entry-header';
    header.innerHTML = `<span>${person.anzeige}</span><span id="abhandlungen">${person.werke.length} Abhandlung/en</span>`;
    header.onclick = () => card.classList.toggle('collapsed');

    const content = document.createElement('div');
    content.className = 'contents';

    person.werke.forEach(book => {
      const work = document.createElement('div');
      work.className = 'work';

      const year = book.year ? ` ${book.year}` : '';
      const anhang = book.anhang ? ` | ${book.anhang}` : '';
      const schriftenreihe = book.schriftenreihe ? ` | ${book.schriftenreihe}` : '';
      const link = `viewer.html?manifest=${book.manifest}${book.startCanvas ? `&canvas=${encodeURIComponent(book.startCanvas)}` : ''}`;
      const beziehungen = book.textbeziehungen ? `<div class="work-beziehungen">${book.textbeziehungen}</div>` : '';

      work.innerHTML = `
        <a class="work-title" href="${link}" target="_blank" rel="noopener">${book.title}</a>
        <button type="button" class="work-download" aria-label="Abhandlung herunterladen">${DOWNLOAD_ICON}<span class="work-download-popup">Abhandlung herunterladen</span></button>
        <div class="work-meta">${year}${anhang}${schriftenreihe}</div>
        ${beziehungen}
      `;

      work.querySelector('.work-download').onclick = () => startAbhandlungDownload(work.querySelector('.work-download'), book);

      content.appendChild(work);
    });

    card.append(header, content);
    containerEl.appendChild(card);
  });
}