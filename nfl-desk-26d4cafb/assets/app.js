
// Client-side table filtering + click-to-sort. Progressive enhancement only:
// every table is fully readable with JavaScript disabled.
(function(){
  document.querySelectorAll('input.filter').forEach(function(inp){
    var wrap = inp.closest('main') || document;
    inp.addEventListener('input', function(){
      var q = inp.value.toLowerCase();
      wrap.querySelectorAll('table').forEach(function(t){
        t.querySelectorAll('tbody tr').forEach(function(tr){
          tr.style.display = tr.textContent.toLowerCase().indexOf(q) === -1 ? 'none' : '';
        });
      });
    });
  });
  document.querySelectorAll('table').forEach(function(t){
    var ths = t.querySelectorAll('thead th');
    ths.forEach(function(th, idx){
      th.style.cursor = 'pointer';
      th.title = 'Click to sort by this column';
      th.addEventListener('click', function(){
        var tb = t.querySelector('tbody');
        var rows = Array.prototype.slice.call(tb.querySelectorAll('tr'));
        var dir = th.dataset.dir === 'asc' ? 'desc' : 'asc';
        ths.forEach(function(o){ delete o.dataset.dir; });
        th.dataset.dir = dir;
        rows.sort(function(a,b){
          var x = (a.cells[idx]||{}).textContent || '';
          var y = (b.cells[idx]||{}).textContent || '';
          var nx = parseFloat(x.replace(/[^0-9eE+\-.]/g,''));
          var ny = parseFloat(y.replace(/[^0-9eE+\-.]/g,''));
          if (!isNaN(nx) && !isNaN(ny)) { return dir==='asc' ? nx-ny : ny-nx; }
          return dir==='asc' ? x.localeCompare(y) : y.localeCompare(x);
        });
        rows.forEach(function(r){ tb.appendChild(r); });
      });
    });
  });
})();
