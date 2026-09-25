document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.entry-header').forEach(header => {
    header.onclick = () => header.closest('.entry').classList.toggle('collapsed');
  });
});
