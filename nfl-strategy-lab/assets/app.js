
function tableFilter(inp, tableId){
  var q = inp.value.toLowerCase();
  var rows = document.querySelectorAll('#'+tableId+' tbody tr');
  rows.forEach(function(r){ r.style.display = r.innerText.toLowerCase().indexOf(q) > -1 ? '' : 'none'; });
}
