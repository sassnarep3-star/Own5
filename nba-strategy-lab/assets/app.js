document.querySelectorAll('.table-filter').forEach((input) => {
  const card = input.closest('.table-card');
  const rows = [...card.querySelectorAll('tbody tr')];
  const count = card.querySelector('.row-count');
  const total = rows.length;
  input.addEventListener('input', () => {
    const query = input.value.trim().toLocaleLowerCase();
    let visible = 0;
    rows.forEach((row) => {
      const show = row.textContent.toLocaleLowerCase().includes(query);
      row.classList.toggle('filtered-out', !show);
      if (show) visible += 1;
    });
    count.textContent = `${visible} / ${total} rows`;
  });
});
