const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function setup() {
  const listeners = {};
  const elements = {};
  const document = {
    activeElement: null,
    readyState: 'complete',
    addEventListener(type, callback) { listeners[type] = callback; },
    createElement() { return { value: '', select() {} }; },
    execCommand() { return false; },
    getElementById(id) { return elements[id]; },
    querySelector(selector) { return selector.startsWith('.it') ? elements.item : null; },
    querySelectorAll(selector) {
      if (selector === '.doc') return [elements.doc];
      if (selector === '.it' || selector === 'a[data-id]') return [elements.item];
      if (selector === '.grp') return [elements.group];
      if (selector === '.secbox') return [elements.section];
      return [];
    },
    documentElement: { style: { setProperty() {} } },
  };
  function element(id) {
    const own = new Set();
    return elements[id] = {
      id, hidden: false, inert: false, disabled: false, dataset: {}, textContent: '',
      classList: {
        add(name) { own.add(name); },
        remove(name) { own.delete(name); },
        contains(name) { return own.has(name); },
        toggle(name, force) { if (force) own.add(name); else own.delete(name); },
      },
      attrs: {},
      addEventListener(type, callback) { this[type] = callback; },
      setAttribute(name, value) { this.attrs[name] = value; },
      removeAttribute(name) { delete this.attrs[name]; },
      focus() { document.activeElement = this; },
      getClientRects() { return [1]; },
      querySelector(selector) {
        if (selector === '.nm') return elements.name;
        if (selector === '.cnt') return elements.count;
        if (selector === '.sc') return elements.sectionCount;
        return null;
      },
      querySelectorAll(selector) {
        if (selector === '.it:not(.hide)') return [elements.item];
        return [];
      },
      closest(selector) { return selector === '.grp' ? elements.group : null; },
    };
  }
  for (const id of ['viewer', 'ph', 'menuToggle', 'navClose', 'shade', 'currentTitle',
    'q', 'res', 'clr', 'fontDec', 'fontInc', 'backTop', 'topbar', 'nav', 'item',
    'doc', 'group', 'section', 'name', 'count', 'sectionCount']) element(id);
  document.body = element('body');
  document.body.appendChild = () => {};
  document.body.removeChild = () => {};
  elements.item.dataset = { id: '1', t: '消化内科' };
  elements.q.value = '';
  elements.item.querySelector = () => elements.name;
  elements.doc.dataset = { id: '1' };
  elements.name.textContent = '消化内科';
  elements.nav.querySelectorAll = () => [elements.navClose, elements.q, elements.item];
  const media = { matches: true, listeners: {}, addEventListener(type, callback) { this.listeners[type] = callback; } };
  const window = { matchMedia() { return media; } };
  const source = fs.readFileSync(path.join(__dirname, '..', 'tools', 'reader_app.js'), 'utf8');
  vm.runInNewContext(source, { document, window, setTimeout() {} });
  return { document, elements, listeners, media };
}

test('mobile drawer keeps focus and background interaction inside the directory', () => {
  const { document, elements, listeners } = setup();
  elements.menuToggle.click();
  assert.equal(elements.menuToggle.attrs['aria-expanded'], 'true');
  assert.equal(document.activeElement, elements.navClose);
  assert.equal(elements.topbar.inert, true);
  assert.equal(elements.viewer.inert, true);
  assert.equal(elements.backTop.inert, true);

  document.activeElement = elements.item;
  let prevented = false;
  listeners.keydown({ key: 'Tab', shiftKey: false, preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(document.activeElement, elements.navClose);

  elements.navClose.click();
  assert.equal(elements.menuToggle.attrs['aria-expanded'], 'false');
  assert.equal(elements.viewer.inert, false);
});

test('drawer closes when viewport leaves mobile layout', () => {
  const { elements, media } = setup();
  elements.menuToggle.click();
  media.matches = false;
  media.listeners.change();
  assert.equal(elements.menuToggle.attrs['aria-expanded'], 'false');
  assert.equal(elements.body.classList.contains('nav-open'), false);
});

test('copy control reports failure when the browser refuses clipboard access', () => {
  const { elements, listeners } = setup();
  const button = elements.item;
  button.dataset.copy = '规培/内科/README.md';
  listeners.click({ target: { closest() { return button; } } });
  assert.equal(button.textContent, '复制失败');
});
