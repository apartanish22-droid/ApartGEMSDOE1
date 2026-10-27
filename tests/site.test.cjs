const assert = require('node:assert/strict');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');
const root = path.resolve(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'docs/assets/app.js'), 'utf8');
const card = JSON.parse(fs.readFileSync(path.join(root, 'evidence/run-card.json'), 'utf8'));
const focus = JSON.parse(fs.readFileSync(path.join(root, 'evidence/focus-audit.json'), 'utf8'));

function render(page = 'executive-summary.html') {
  const html = fs.readFileSync(path.join(root, 'docs', page), 'utf8');
  const dom = new JSDOM(html, { url: `https://example.test/${page}`, runScripts: 'outside-only' });
  // Static, evidence-bound approval must not depend on a live/malformed feed.
  dom.window.fetch = () => { throw new Error('No live data feed is authorized'); };
  dom.window.eval(script);
  return dom;
}
const settle = () => new Promise(resolve => setTimeout(resolve, 0));

test('overview has nine reference-only rows and an explicitly negative research download', () => {
  const dom = render(); const doc = dom.window.document;
  assert.equal(doc.querySelectorAll('.portfolio-table tbody tr').length, 9);
  assert.match(doc.querySelector('.decision-panel').textContent, /DO NOT SUBMIT/);
  assert.equal(doc.querySelector('a[download][href$=".tif"]').getAttribute('href'),
    `downloads/${card.submission_name}.tif`);
  assert.equal(doc.getElementById('submission-note').value, card.submission_note);
  assert(doc.getElementById('submission-note').readOnly);
  assert.equal(doc.querySelector('form'), null);
  assert.equal(doc.querySelector('[data-submit]'), null);
  assert.match(doc.body.textContent, /Parallel H2 promotion rejected/);
  dom.window.close();
});

test('all nine canonical detail pages identify exact historical files without score receipts or approval', () => {
  for (const row of focus.rows) {
    const dom = render(`sites/${row.site}.html`); const doc = dom.window.document;
    assert.equal(doc.querySelector('h1').textContent, row.site);
    assert(doc.body.textContent.includes(row.inspected_filename));
    assert.match(doc.body.textContent, /No exact-file submission-page receipt/);
    assert.match(doc.body.textContent, /DO NOT SUBMIT/);
    assert.match(doc.body.textContent, /not estimable/i);
    assert(!doc.body.textContent.includes(row.historical_user_reported_value));
    assert.match(doc.body.textContent, /gems-segment-pooled-v1/);
    dom.window.close();
  }
});

test('secure clipboard copies the exact note, not HTML, and labels research-only status', async () => {
  const dom = render(); const win = dom.window; let copied;
  Object.defineProperty(win, 'isSecureContext', { value: true });
  Object.defineProperty(win.navigator, 'clipboard', { value: { writeText: async value => { copied = value; } } });
  win.document.querySelector('[data-copy]').click(); await settle();
  assert.equal(copied, card.submission_note);
  assert.match(win.document.querySelector('.copy-status').textContent, /Copied\. Research only/);
  assert(copied.length <= 140);
  dom.window.close();
});

test('unavailable clipboard never reports a false success or authorizes upload', async () => {
  const dom = render(); const win = dom.window;
  Object.defineProperty(win, 'isSecureContext', { value: true });
  Object.defineProperty(win.navigator, 'clipboard', { value: { writeText: async () => { throw new Error('denied'); } } });
  win.document.querySelector('[data-copy]').click(); await settle();
  assert.match(win.document.querySelector('.copy-status').textContent, /Clipboard unavailable/);
  assert.match(win.document.querySelector('.decision-panel').textContent, /DO NOT SUBMIT/);
  dom.window.close();
});

test('fallback copy is plain text, fails honestly, and tolerates a missing target', async () => {
  const dom = render(); const doc = dom.window.document;
  let calls = 0;
  doc.execCommand = name => { assert.equal(name, 'copy'); calls++; return false; };
  doc.getElementById('submission-note').value = '<img src=x onerror=alert(1)>';
  doc.querySelector('[data-copy]').click(); await settle();
  assert.equal(calls, 1);
  assert.equal(doc.querySelectorAll('img').length, 0);
  assert.match(doc.querySelector('.copy-status').textContent, /Clipboard unavailable/);
  doc.querySelector('[data-copy]').dataset.copy = 'missing-target';
  doc.querySelector('[data-copy]').click(); await settle();
  assert.equal(calls, 1);
  dom.window.close();
});
