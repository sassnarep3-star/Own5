(function(){
  document.querySelectorAll('input.filter').forEach(function(box){
    var table = document.querySelector('table[data-filter="' + (box.getAttribute('data-target') || '') + '"]')
      || document.querySelector('table[data-filter]');
    if(!table) return;
    box.addEventListener('input', function(){
      var q = box.value.trim().toLowerCase();
      table.querySelectorAll('tbody tr').forEach(function(tr){
        tr.style.display = (!q || tr.textContent.toLowerCase().indexOf(q) !== -1) ? '' : 'none';
      });
    });
  });
})();
