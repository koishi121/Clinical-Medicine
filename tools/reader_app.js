function ready() {
  var viewer = document.getElementById('viewer');
  var placeholder = document.getElementById('ph');
  var menuToggle = document.getElementById('menuToggle');
  var navClose = document.getElementById('navClose');
  var shade = document.getElementById('shade');
  var nav = document.getElementById('nav');
  var background = [document.getElementById('topbar'), viewer, document.getElementById('backTop')];
  var currentTitle = document.getElementById('currentTitle');
  var docs = {};
  document.querySelectorAll('.doc').forEach(function (doc) { docs[doc.dataset.id] = doc; });

  function setBackgroundInert(value) {
    background.forEach(function (node) {
      node.inert = value;
      if (value) node.setAttribute('aria-hidden', 'true');
      else node.removeAttribute('aria-hidden');
    });
  }
  function closeMenu(returnFocus) {
    if (!document.body.classList.contains('nav-open')) return;
    document.body.classList.remove('nav-open');
    menuToggle.setAttribute('aria-expanded', 'false');
    setBackgroundInert(false);
    if (returnFocus) menuToggle.focus();
  }
  menuToggle.addEventListener('click', function () {
    document.body.classList.add('nav-open');
    menuToggle.setAttribute('aria-expanded', 'true');
    navClose.focus();
    setBackgroundInert(true);
  });
  navClose.addEventListener('click', function () { closeMenu(true); });
  shade.addEventListener('click', function () { closeMenu(true); });
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') closeMenu(true);
    if (event.key !== 'Tab' || !document.body.classList.contains('nav-open')) return;
    var focusable = Array.prototype.slice.call(
      nav.querySelectorAll('button:not([disabled]), input:not([disabled]), summary, a[href]')
    ).filter(function (item) { return item.getClientRects().length > 0; });
    if (!focusable.length) return;
    var first = focusable[0], last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault(); last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault(); first.focus();
    } else if (focusable.indexOf(document.activeElement) < 0) {
      event.preventDefault(); first.focus();
    }
  });
  var mobileView = window.matchMedia('(max-width: 860px)');
  function handleViewportChange() {
    if (!mobileView.matches && document.body.classList.contains('nav-open')) {
      closeMenu(false);
      viewer.focus();
    }
  }
  if (mobileView.addEventListener) mobileView.addEventListener('change', handleViewportChange);
  else mobileView.addListener(handleViewportChange);

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

  function fallbackCopy(text) {
    var field = document.createElement('textarea');
    field.value = text;
    document.body.appendChild(field);
    field.select();
    var copied = false;
    try { copied = document.execCommand('copy'); }
    catch (error) { copied = false; }
    document.body.removeChild(field);
    return copied;
  }
  function reportCopy(button, copied) {
    button.textContent = copied ? '已复制' : '复制失败';
    setTimeout(function () { button.textContent = '复制路径'; }, 1600);
  }
  document.addEventListener('click', function (event) {
    var button = event.target.closest('[data-copy]');
    if (!button) return;
    var text = button.dataset.copy;
    if (typeof navigator !== 'undefined' && navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        function () { reportCopy(button, true); },
        function () { reportCopy(button, fallbackCopy(text)); }
      );
    } else {
      reportCopy(button, fallbackCopy(text));
    }
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
