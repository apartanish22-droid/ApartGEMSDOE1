const assert = require('node:assert/strict');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');
const root = path.resolve(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'docs/assets/app.js'), 'utf8');
const audit = JSON.parse(fs.readFileSync(path.join(root, 'docs/data/audit.json'), 'utf8'));
const freshness = JSON.parse(fs.readFileSync(path.join(root, 'docs/data/freshness.json'), 'utf8'));

async function render(page, data = audit, opts = {}) {
  const html = fs.readFileSync(path.join(root, 'docs', page), 'utf8');
  const dom = new JSDOM(html, {url: `https://example.test/${page}`, runScripts: 'outside-only'});
  dom.window.fetch = async url => {
    if (opts.fail) throw new Error('offline');
    const value = String(url).endsWith('audit.json') ? data : (opts.freshness ?? freshness);
    return {ok: true, json: async () => value};
  };
  dom.window.eval(script);
  await new Promise(resolve => setTimeout(resolve, 20));
  return dom;
}

test('overview renders nine research-only rows and never unlocks a TIFF', async () => {
  const dom = await render('index.html');
  const doc = dom.window.document;
  assert.equal(doc.querySelectorAll('[data-site-table] tr').length, 9);
  assert.match(doc.querySelector('h1').textContent, /clear decision/i);
  assert.match(doc.querySelector('.decision').textContent, /No submission file is approved/);
  assert.match(doc.querySelector('.button.disabled').textContent, /TIFF unavailable/);
  assert.match(doc.getElementById('stat-bound').textContent, /82\.34%/);
  assert.equal(doc.querySelectorAll('.tag.red').length, 9);
  assert.match(doc.getElementById('freshness').textContent, /not a live leaderboard feed/i);
  dom.window.close();
});

test('each detailed site identifies its own historical file but stays blocked', async () => {
  for (const record of audit.historical) {
    const dom = await render(`sites/${record.site.toLowerCase()}.html`);
    const doc = dom.window.document;
    assert.equal(doc.getElementById('site-file').textContent, record.filename);
    assert.match(doc.getElementById('site-reported').textContent, /UNVERIFIED/);
    assert.match(doc.getElementById('site-unique').textContent, /^NO/);
    assert.match(doc.body.textContent, /DO NOT SUBMIT/);
    assert.equal(doc.getElementById('site-download').hostname, 'github.com');
    dom.window.close();
  }
});

test('offline or malformed data fail closed instead of displaying stale approval', async () => {
  const dom = await render('index.html', audit, {fail: true});
  const doc = dom.window.document;
  assert.match(doc.querySelector('[data-site-table]').textContent, /unavailable/i);
  assert.match(doc.querySelector('.decision').textContent, /No submission file is approved/);
  assert.match(doc.getElementById('freshness').textContent, /unavailable/i);
  dom.window.close();
  const malformed = structuredClone(audit); malformed.historical = [];
  const missing = await render('index.html', malformed);
  assert.match(missing.window.document.querySelector('[data-site-table]').textContent, /unavailable/i);
  missing.window.close();
});

test('untrusted JSON cannot inject markup or unsafe download URLs', async () => {
  const input = structuredClone(audit);
  input.historical[0].filename = '<img src=x onerror=alert(1)>';
  input.historical[0].source_download_url = 'javascript:alert(1)';
  const dom = await render('index.html', input);
  const body = dom.window.document.querySelector('[data-site-table]');
  assert.equal(body.querySelectorAll('img').length, 0);
  assert.match(body.textContent, /Invalid research link/);
  assert.equal(body.querySelectorAll('a[href^="javascript:"]').length, 0);
  dom.window.close();
});


test('invalid or inconsistent freshness snapshots are never called current', async () => {
  for (const bad of [
    {...freshness, checked_utc: '2099-01-01T00:00:00Z'},
    {...freshness, changed_count: 0},
    {...freshness, sources: []},
  ]) {
    const dom = await render('index.html', audit, {freshness: bad});
    assert.match(dom.window.document.getElementById('freshness').textContent, /stale or invalid/i);
    dom.window.close();
  }
});
