import { renderPersonenRegister } from './register-personen.js';
import { renderBegriffeRegister } from './register-begriffe.js';

// Zuordnung von Mode zu Render-Funktion
const registers = {
  personen: renderPersonenRegister,
  begriffe: renderBegriffeRegister
};

document.addEventListener('DOMContentLoaded', () => {
  const switchContainer = document.getElementById('register-switch');
  const buttons = switchContainer.querySelectorAll('.mode');

  switchContainer.addEventListener('click', (e) => {
    // Nur reagieren, wenn ein .mode Button geklickt wurde
    const btn = e.target.closest('.mode');
    if (!btn || btn.classList.contains('active')) return;

    // Aktive Klasse umschalten
    buttons.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // Passendes Register ausführen
    const mode = btn.dataset.mode;
    registers[mode]();
  });

  // Start-Register initial rendern (Personen)
  renderPersonenRegister();
});