/* Indice dei capitoli su mobile, ricerca tra i capitoli, evidenziazione del termine cercato. */
(function () {
  var toggle = document.getElementById('nav-toggle');
  var side = document.getElementById('sidebar');
  var backdrop = document.getElementById('nav-backdrop');
  var closeBtn = document.getElementById('nav-close');
  var mq = window.matchMedia('(max-width: 900px)');
  function setNav(open) {
    if (!side) return;
    side.classList.toggle('open', open);
    backdrop.hidden = !open;
    document.body.classList.toggle('nav-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    if (mq.matches) {
      if (open) { side.setAttribute('role', 'dialog'); side.setAttribute('aria-modal', 'true'); side.setAttribute('aria-label', 'Capitoli'); var cur = side.querySelector('[aria-current="page"]') || side.querySelector('a'); (cur || closeBtn).focus(); }
      else { side.removeAttribute('role'); side.removeAttribute('aria-modal'); side.removeAttribute('aria-label'); }
    }
  }
  if (toggle && side) {
    toggle.addEventListener('click', function () { setNav(!side.classList.contains('open')); });
    closeBtn.addEventListener('click', function () { setNav(false); toggle.focus(); });
    backdrop.addEventListener('click', function () { setNav(false); toggle.focus(); });
    side.addEventListener('keydown', function (e) {
      if (!side.classList.contains('open') || !mq.matches) return;
      if (e.key === 'Escape') { setNav(false); toggle.focus(); return; }
      if (e.key === 'Tab') {
        var f = side.querySelectorAll('a[href],button'); var first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
    side.addEventListener('click', function (e) { if (e.target.closest('a') && mq.matches) setNav(false); });
    (mq.addEventListener ? mq.addEventListener.bind(mq, 'change') : mq.addListener.bind(mq))(function () { setNav(false); });
  }

  // Ricerca comprimibile su mobile
  var sBtn = document.getElementById('search-toggle');
  var sBox = document.getElementById('search-box');
  if (sBtn && sBox) {
    sBtn.addEventListener('click', function () {
      var open = sBox.classList.toggle('open');
      sBtn.setAttribute('aria-expanded', String(open));
      if (open) document.getElementById('q').focus();
    });
  }

  // Torna su
  var top = document.getElementById('back-to-top');
  if (top) {
    function vis() { top.classList.toggle('show', (window.pageYOffset || document.documentElement.scrollTop) > 300); }
    window.addEventListener('scroll', vis, { passive: true }); vis();
    top.addEventListener('click', function () {
      var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' });
      var brand = document.querySelector('.brand'); if (brand) brand.focus({ preventScroll: true });
    });
  }

  // Tabelle a schede su schermi stretti: struttura visiva a blocchi, semantica di tabella ripristinata con i ruoli ARIA
  var narrowMq = window.matchMedia('(max-width: 600px)');
  function stackTables() {
    document.querySelectorAll('.tbl table').forEach(function (t) {
      var on = narrowMq.matches && t.querySelectorAll('thead th').length > 2;
      t.classList.toggle('stack', on);
      var map = [['table', 'table'], ['thead', 'rowgroup'], ['tbody', 'rowgroup'], ['tr', 'row'], ['th', 'columnheader'], ['td', 'cell']];
      map.forEach(function (m) {
        (m[0] === 'table' ? [t] : t.querySelectorAll(m[0])).forEach(function (el) {
          if (on) el.setAttribute('role', m[1]); else el.removeAttribute('role');
        });
      });
      if (on) {
        var heads = Array.prototype.map.call(t.querySelectorAll('thead th'), function (h) { return h.textContent.trim(); });
        t.querySelectorAll('tbody tr').forEach(function (tr) {
          Array.prototype.forEach.call(tr.children, function (td, i) { if (heads[i]) td.setAttribute('data-label', heads[i]); });
        });
      }
    });
  }
  stackTables();
  (narrowMq.addEventListener ? narrowMq.addEventListener.bind(narrowMq, 'change') : narrowMq.addListener.bind(narrowMq))(stackTables);

  // Tabelle scorrevoli: raggiungibili da tastiera e annunciate come regioni
  document.querySelectorAll('.tbl').forEach(function (w) {
    var t = w.querySelector('table'), hc = t ? t.querySelectorAll('thead th').length : 0;
    if (hc && hc <= 2) t.classList.add('narrow');
    function sync() {
      if (w.scrollWidth > w.clientWidth + 1) {
        var h = w.previousElementSibling, label = '';
        while (h && !/^H[1-6]$/.test(h.tagName)) h = h.previousElementSibling;
        label = h ? h.textContent : 'Contenuto';
        w.setAttribute('tabindex', '0'); w.setAttribute('role', 'region');
        var same = Array.prototype.filter.call(document.querySelectorAll('.tbl'), function (t) { var x = t.previousElementSibling; while (x && !/^H[1-6]$/.test(x.tagName)) x = x.previousElementSibling; return (x ? x.textContent : 'Contenuto') === label; });
        w.setAttribute('aria-label', 'Tabella scorrevole: ' + label + (same.length > 1 ? ' (' + (same.indexOf(w) + 1) + ' di ' + same.length + ')' : ''));
      } else { w.removeAttribute('tabindex'); w.removeAttribute('role'); w.removeAttribute('aria-label'); }
    }
    sync(); window.addEventListener('resize', sync);
  });

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
    if (!ql) { box.hidden = true; var s0 = document.getElementById('q-status'); if (s0) s0.textContent = ''; return; }
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
      var st = document.getElementById('q-status');
      if (st) st.textContent = hits.length ? hits.length + (hits.length === 1 ? ' capitolo trovato' : ' capitoli trovati') : 'Nessun capitolo trovato';
    });
  }

  if (input) {
    input.addEventListener('input', function () { render(input.value); });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { box.hidden = true; }
      if (e.key === 'ArrowDown') { var a = box.querySelector('a'); if (a && !box.hidden) { e.preventDefault(); a.focus(); } }
    });
    box.addEventListener('keydown', function (e) {
      var links = Array.prototype.slice.call(box.querySelectorAll('a')), i = links.indexOf(document.activeElement);
      if (e.key === 'ArrowDown' && i >= 0) { e.preventDefault(); (links[i + 1] || links[i]).focus(); }
      if (e.key === 'ArrowUp' && i >= 0) { e.preventDefault(); (i ? links[i - 1] : input).focus(); }
      if (e.key === 'Escape') { box.hidden = true; input.focus(); }
    });
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
