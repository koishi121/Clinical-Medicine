function ready() {
  var viewer = document.getElementById('viewer');
  var placeholder = document.getElementById('ph');
  var menuToggle = document.getElementById('menuToggle');
  var navClose = document.getElementById('navClose');
  var shade = document.getElementById('shade');
  var currentTitle = document.getElementById('currentTitle');
  var docs = {};
  document.querySelectorAll('.doc').forEach(function (doc) { docs[doc.dataset.id] = doc; });

  function closeMenu(returnFocus) {
    if (!document.body.classList.contains('nav-open')) return;
    document.body.classList.remove('nav-open');
    menuToggle.setAttribute('aria-expanded', 'false');
    if (returnFocus) menuToggle.focus();
  }
  menuToggle.addEventListener('click', function () {
    document.body.classList.add('nav-open');
    menuToggle.setAttribute('aria-expanded', 'true');
    navClose.focus();
  });
  navClose.addEventListener('click', function () { closeMenu(true); });
  shade.addEventListener('click', function () { closeMenu(true); });
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') closeMenu(true);
  });

  function show(id) {
    document.querySelectorAll('.it').forEach(function (item) {
      item.classList.remove('active');
      item.removeAttribute('aria-current');
    });
    var item = document.querySelector('.it[data-id="' + id + '"]');
    if (item) {
      item.classList.add('active');
      item.setAttribute('aria-current', 'page');
      currentTitle.textContent = item.querySelector('.nm').textContent;
      var group = item.closest('.grp');
      if (group) group.open = true;
    }
    document.querySelectorAll('.doc').forEach(function (doc) { doc.hidden = true; });
    var doc = docs[id];
    placeholder.hidden = !!doc;
    if (doc) doc.hidden = false;
    viewer.scrollTop = 0;
    closeMenu(false);
  }
  document.querySelectorAll('a[data-id]').forEach(function (link) {
    link.addEventListener('click', function (event) {
      event.preventDefault();
      show(link.dataset.id);
      viewer.focus();
    });
  });

  document.addEventListener('click', function (event) {
    var button = event.target.closest('[data-copy]');
    if (!button) return;
    var field = document.createElement('textarea');
    field.value = button.dataset.copy;
    document.body.appendChild(field);
    field.select();
    try { document.execCommand('copy'); button.textContent = '已复制'; }
    catch (error) { button.textContent = '复制失败'; }
    document.body.removeChild(field);
    setTimeout(function () { button.textContent = '复制路径'; }, 1600);
  });

  var input = document.getElementById('q');
  var result = document.getElementById('res');
  var items = Array.prototype.slice.call(document.querySelectorAll('.it'));
  function search() {
    var query = input.value.trim().toLowerCase();
    var shown = 0;
    items.forEach(function (item) {
      var match = !query || (item.dataset.t || '').toLowerCase().indexOf(query) >= 0;
      item.classList.toggle('hide', !match);
      if (match) shown++;
    });
    document.querySelectorAll('.grp').forEach(function (group) {
      var visible = group.querySelectorAll('.it:not(.hide)').length;
      group.classList.toggle('hide', visible === 0);
      var count = group.querySelector('.cnt');
      if (count) count.textContent = visible;
      if (query && visible) group.open = true;
    });
    document.querySelectorAll('.secbox').forEach(function (section) {
      var visible = section.querySelectorAll('.it:not(.hide)').length;
      section.classList.toggle('hide', visible === 0 && !!query);
      var count = section.querySelector('.sc');
      if (count) count.textContent = visible;
    });
    result.textContent = query ? ('匹配 ' + shown + ' / ' + items.length + ' 项') : ('共 ' + items.length + ' 项');
  }
  input.addEventListener('input', search);
  document.getElementById('clr').addEventListener('click', function () {
    input.value = '';
    search();
    input.focus();
  });

  var fontSize = 16;
  var fontDec = document.getElementById('fontDec');
  var fontInc = document.getElementById('fontInc');
  function setFont(delta) {
    fontSize = Math.max(15, Math.min(20, fontSize + delta));
    document.documentElement.style.setProperty('--reader-size', fontSize + 'px');
    fontDec.disabled = fontSize === 15;
    fontInc.disabled = fontSize === 20;
  }
  fontDec.addEventListener('click', function () { setFont(-1); });
  fontInc.addEventListener('click', function () { setFont(1); });
  document.getElementById('backTop').addEventListener('click', function () { viewer.scrollTop = 0; });

  search();
  setFont(0);
  var first = document.querySelector('.it[aria-current="page"]') || document.querySelector('.it');
  if (first) show(first.dataset.id);
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
else ready();
