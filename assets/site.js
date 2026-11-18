/* Indice dei capitoli su mobile, ricerca tra i capitoli, evidenziazione del termine cercato. */
(function () {
  var toggle = document.getElementById('nav-toggle');
  var nav = document.getElementById('nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });
  }

  var input = document.getElementById('q');
  var box = document.getElementById('results');
  var index = null;

  function load() {
    if (index) return Promise.resolve(index);
    return fetch('assets/search-index.json').then(function (r) { return r.json(); })
      .then(function (d) { index = d; return d; }).catch(function () { index = []; return index; });
  }

  function snippet(text, q) {
    var i = text.toLowerCase().indexOf(q);
    if (i < 0) return '';
    var a = Math.max(0, i - 50), b = Math.min(text.length, i + q.length + 80);
    return (a ? '… ' : '') + text.slice(a, b) + (b < text.length ? ' …' : '');
  }

  function render(q) {
    var ql = q.trim().toLowerCase();
    box.textContent = '';
    if (!ql) { box.hidden = true; return; }
    load().then(function (d) {
      var hits = d.filter(function (c) { return (c.title + ' ' + c.text).toLowerCase().indexOf(ql) >= 0; });
      if (!hits.length) {
        var p = document.createElement('p');
        p.textContent = 'Nessun capitolo contiene questa parola.';
        box.appendChild(p);
      }
      hits.forEach(function (c) {
        var a = document.createElement('a');
        a.href = c.slug + '.html?q=' + encodeURIComponent(q.trim());
        var s = document.createElement('strong');
        s.textContent = (c.num ? c.num + '. ' : '') + c.title;
        var m = document.createElement('small');
        m.textContent = snippet(c.text, ql);
        a.appendChild(s); a.appendChild(m); box.appendChild(a);
      });
      box.hidden = false;
    });
  }

  if (input) {
    input.addEventListener('input', function () { render(input.value); });
    input.addEventListener('keydown', function (e) { if (e.key === 'Escape') { box.hidden = true; } });
    document.addEventListener('click', function (e) { if (!box.contains(e.target) && e.target !== input) box.hidden = true; });
  }

  var q = new URLSearchParams(location.search).get('q');
  var prose = document.querySelector('.prose');
  if (q && prose) {
    var ql = q.toLowerCase(), first = null;
    var walker = document.createTreeWalker(prose, NodeFilter.SHOW_TEXT);
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function (n) {
      var i = n.nodeValue.toLowerCase().indexOf(ql);
      if (i < 0) return;
      var r = document.createRange();
      r.setStart(n, i); r.setEnd(n, i + q.length);
      var mk = document.createElement('mark');
      r.surroundContents(mk);
      if (!first) first = mk;
    });
    if (first) first.scrollIntoView({ block: 'center' });
    if (input) input.value = q;
  }
})();
