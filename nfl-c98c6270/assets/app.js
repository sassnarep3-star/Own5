
// Own5 Decision Console - client-side review tray (no backend, no tracking).
(function(){
  var KEY = 'own5-decisions-c98c6270';
  function load(){ try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch(e){ return {}; } }
  function save(d){ try { localStorage.setItem(KEY, JSON.stringify(d)); } catch(e){} }
  function refresh(){
    var d = load(), n = Object.keys(d).length, tray = document.getElementById('tray');
    if(!tray) return;
    tray.classList.toggle('show', n > 0);
    var list = document.getElementById('traylist');
    if(list){
      list.innerHTML = Object.keys(d).sort().map(function(k){
        return '<li><strong>'+k+'</strong> -> '+d[k].decision+
               ' <span class="fine">('+new Date(d[k].ts).toISOString().slice(0,10)+')</span>'+
               ' <button class="btn" data-clear="'+k+'">clear</button></li>';
      }).join('');
    }
    var c = document.getElementById('traycount'); if(c) c.textContent = n;
    document.querySelectorAll('[data-sugg]').forEach(function(box){
      var id = box.getAttribute('data-sugg'), cur = d[id] && d[id].decision;
      box.querySelectorAll('[data-dec]').forEach(function(b){
        b.classList.toggle('on', b.getAttribute('data-dec') === cur);
      });
    });
  }
  document.addEventListener('click', function(e){
    var b = e.target.closest('[data-dec]');
    if(b){
      var box = b.closest('[data-sugg]'), id = box.getAttribute('data-sugg');
      var d = load(); d[id] = {decision: b.getAttribute('data-dec'), ts: Date.now()};
      save(d); refresh(); return;
    }
    var c = e.target.closest('[data-clear]');
    if(c){ var d2 = load(); delete d2[c.getAttribute('data-clear')]; save(d2); refresh(); return; }
    if(e.target.id === 'trayexport'){
      var d3 = load(), lines = ['suggestion_id,decision,recorded_utc'];
      Object.keys(d3).sort().forEach(function(k){
        lines.push([k, d3[k].decision, new Date(d3[k].ts).toISOString()].join(','));
      });
      var blob = new Blob([lines.join('\n')], {type:'text/csv'});
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = 'decision-log.csv'; a.click();
      return;
    }
    if(e.target.id === 'trayclear'){ save({}); refresh(); return; }
  });
  // generic table filter
  document.querySelectorAll('input[data-filter]').forEach(function(inp){
    inp.addEventListener('input', function(){
      var q = inp.value.toLowerCase(), tbl = document.querySelector(inp.getAttribute('data-filter'));
      if(!tbl) return;
      tbl.querySelectorAll('tbody tr').forEach(function(tr){
        tr.style.display = tr.textContent.toLowerCase().indexOf(q) === -1 ? 'none' : '';
      });
    });
  });
  refresh();
})();
