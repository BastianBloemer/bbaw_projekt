// Download einzelner Abhandlungen als ZIP mit den Einzelseiten (Volltaufloesung
// ueber den IIIF Image API Service jeder Canvas). Baut das ZIP-Archiv direkt
// im Browser zusammen (Methode "store", keine Kompression -- JPEGs
// komprimieren ohnehin kaum, dafuer ohne externe Bibliothek/CDN, analog dazu,
// dass auch Mirador komplett lokal vorliegt).

// Klassisches Download-Icon (Material "file_download"), inline als SVG --
// keine externe Icon-Bibliothek noetig, faerbt sich per currentColor mit.
export const DOWNLOAD_ICON = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>';

const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) {
      c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    }
    table[n] = c >>> 0;
  }
  return table;
})();

function crc32(bytes) {
  let crc = 0xFFFFFFFF;
  for (let i = 0; i < bytes.length; i++) {
    crc = CRC_TABLE[(crc ^ bytes[i]) & 0xFF] ^ (crc >>> 8);
  }
  return (crc ^ 0xFFFFFFFF) >>> 0;
}

function dosDateTime() {
  const now = new Date();
  const time = (now.getHours() << 11) | (now.getMinutes() << 5) | (now.getSeconds() >> 1);
  const date = ((now.getFullYear() - 1980) << 9) | ((now.getMonth() + 1) << 5) | now.getDate();
  return { time, date };
}

function buildZip(files) {
  const { time, date } = dosDateTime();
  const localParts = [];
  const centralParts = [];
  let offset = 0;

  for (const file of files) {
    const nameBytes = new TextEncoder().encode(file.name);
    const crc = crc32(file.data);
    const size = file.data.length;

    const localHeader = new DataView(new ArrayBuffer(30));
    localHeader.setUint32(0, 0x04034b50, true);
    localHeader.setUint16(4, 20, true);
    localHeader.setUint16(6, 0, true);
    localHeader.setUint16(8, 0, true);
    localHeader.setUint16(10, time, true);
    localHeader.setUint16(12, date, true);
    localHeader.setUint32(14, crc, true);
    localHeader.setUint32(18, size, true);
    localHeader.setUint32(22, size, true);
    localHeader.setUint16(26, nameBytes.length, true);
    localHeader.setUint16(28, 0, true);

    localParts.push(new Uint8Array(localHeader.buffer), nameBytes, file.data);

    const centralHeader = new DataView(new ArrayBuffer(46));
    centralHeader.setUint32(0, 0x02014b50, true);
    centralHeader.setUint16(4, 20, true);
    centralHeader.setUint16(6, 20, true);
    centralHeader.setUint16(8, 0, true);
    centralHeader.setUint16(10, 0, true);
    centralHeader.setUint16(12, time, true);
    centralHeader.setUint16(14, date, true);
    centralHeader.setUint32(16, crc, true);
    centralHeader.setUint32(20, size, true);
    centralHeader.setUint32(24, size, true);
    centralHeader.setUint16(28, nameBytes.length, true);
    centralHeader.setUint16(30, 0, true);
    centralHeader.setUint16(32, 0, true);
    centralHeader.setUint16(34, 0, true);
    centralHeader.setUint16(36, 0, true);
    centralHeader.setUint32(38, 0, true);
    centralHeader.setUint32(42, offset, true);

    centralParts.push(new Uint8Array(centralHeader.buffer), nameBytes);

    offset += 30 + nameBytes.length + size;
  }

  const centralStart = offset;
  const centralSize = centralParts.reduce((sum, part) => sum + part.length, 0);

  const eocd = new DataView(new ArrayBuffer(22));
  eocd.setUint32(0, 0x06054b50, true);
  eocd.setUint16(4, 0, true);
  eocd.setUint16(6, 0, true);
  eocd.setUint16(8, files.length, true);
  eocd.setUint16(10, files.length, true);
  eocd.setUint32(12, centralSize, true);
  eocd.setUint32(16, centralStart, true);
  eocd.setUint16(20, 0, true);

  return new Blob([...localParts, ...centralParts, new Uint8Array(eocd.buffer)], { type: 'application/zip' });
}

function sanitizeFilename(name) {
  return (name || 'abhandlung').replace(/[\\/:*?"<>|]/g, '_').trim().slice(0, 120);
}

function imageUrlFromCanvas(canvas) {
  const annotation = canvas.items?.[0]?.items?.[0];
  const service = annotation?.body?.service?.[0];
  const serviceId = service?.['@id'] || service?.id;
  if (serviceId) {
    return `${serviceId}/full/full/0/default.jpg`;
  }
  return annotation?.body?.id || null;
}

// Laedt das Manifest, ermittelt die Canvases zwischen startCanvas und
// endCanvas (inklusive) und packt deren Bilder als ZIP zusammen.
export async function downloadAbhandlungAsZip(book, onProgress) {
  const manifestRes = await fetch(book.manifest);
  if (!manifestRes.ok) {
    throw new Error(`Manifest konnte nicht geladen werden (${manifestRes.status})`);
  }
  const manifest = await manifestRes.json();
  const canvases = manifest.items || [];

  const startIdx = canvases.findIndex(c => c.id === book.startCanvas);
  if (startIdx === -1) {
    throw new Error('Startseite nicht im Manifest gefunden.');
  }
  const endIdx = canvases.findIndex(c => c.id === book.endCanvas);
  const from = Math.min(startIdx, endIdx === -1 ? startIdx : endIdx);
  const to = Math.max(startIdx, endIdx === -1 ? startIdx : endIdx);
  const relevantCanvases = canvases.slice(from, to + 1);

  const files = [];
  for (let i = 0; i < relevantCanvases.length; i++) {
    const imageUrl = imageUrlFromCanvas(relevantCanvases[i]);
    if (!imageUrl) continue;

    const res = await fetch(imageUrl);
    if (!res.ok) continue;
    const data = new Uint8Array(await res.arrayBuffer());
    const pageNumber = String(i + 1).padStart(3, '0');
    files.push({ name: `${pageNumber}.jpg`, data });

    if (onProgress) onProgress(i + 1, relevantCanvases.length);
  }

  if (files.length === 0) {
    throw new Error('Keine Seiten gefunden.');
  }

  const zipBlob = buildZip(files);
  const url = URL.createObjectURL(zipBlob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${sanitizeFilename(book.title)}.zip`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// Von den Register-/Suche-Views genutzter Hilfsablauf: Button-Status waehrend
// des Downloads pflegen (Fortschritt/Fehler), danach zuruecksetzen.
export function startAbhandlungDownload(button, book) {
  if (button.disabled) return;
  const originalContent = button.innerHTML;
  button.disabled = true;

  downloadAbhandlungAsZip(book, (done, total) => {
    button.textContent = `${done}/${total}`;
  })
    .then(() => {
      button.textContent = '✓';
    })
    .catch(err => {
      console.error(err);
      button.textContent = '⚠';
    })
    .finally(() => {
      setTimeout(() => {
        button.innerHTML = originalContent;
        button.disabled = false;
      }, 2000);
    });
}
