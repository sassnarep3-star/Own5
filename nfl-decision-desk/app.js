'use strict';
const input = document.querySelector('#filter');
const rows = [...document.querySelectorAll('tbody tr')];
input.addEventListener('input', () => {
  const query = input.value.toLowerCase();
  let visible = 0;
  rows.forEach(row => { row.hidden = !row.textContent.toLowerCase().includes(query); if (!row.hidden) visible++; });
  document.querySelector('#count').textContent = `${visible} of ${rows.length} rows`;
});
document.querySelectorAll('nav a').forEach(a => {
  if (a.getAttribute('href') === (location.pathname.split('/').pop() || 'index.html')) a.setAttribute('aria-current', 'page');
});
