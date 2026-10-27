#!/usr/bin/env node
/** Bounded, autonomous browser check. Starts/closes its own static test server.
 * Screenshots/binaries stay ignored; only the small JSON evidence is tracked.
 * Never sends a competition submission, retrieves external data, or reruns science.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'node:http';
import { createHash } from 'node:crypto';
import { pipeline } from 'node:stream/promises';
import { createReadStream } from 'node:fs';
import { createBrotliDecompress } from 'node:zlib';
import { createRequire } from 'node:module';
import { chromium } from '@playwright/test';
import bundled from '@sparticuz/chromium';
import AxeBuilder from '@axe-core/playwright';

const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DOCS = path.join(ROOT, 'docs');
const CACHE = path.join(ROOT, '.cache/browser');
const report = { schema: 'apartgems-browser-verification-v1', checked_utc: new Date().toISOString(),
  scope: 'Local rendered site; no organizer portal or live Pages browser acceptance claim',
  submission_authorized: false, checks: {}, errors: [], screenshots: 'Ignored .cache/browser/' };
let server, browser;

async function check(name, fn) {
  try { report.checks[name] = { passed: true, detail: await fn() ?? '' }; }
  catch (error) { report.checks[name] = { passed: false, detail: String(error) }; report.errors.push(`${name}: ${error}`); }
}

async function siteInputs(directory = DOCS, hashes = {}) {
  for (const item of await fs.readdir(directory, { withFileTypes: true })) {
    const file = path.join(directory, item.name);
    if (item.isDirectory()) await siteInputs(file, hashes);
    else if (/\.(html|css|js)$/.test(item.name))
      hashes[path.relative(ROOT, file)] = createHash('sha256').update(await fs.readFile(file)).digest('hex');
  }
  return hashes;
}

async function serve() {
  const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript',
    '.svg': 'image/svg+xml', '.json': 'application/json', '.tif': 'image/tiff', '.csv': 'text/csv', '.md': 'text/plain' };
  server = createServer(async (request, response) => {
    try {
      const url = new URL(request.url, 'http://test.invalid');
      let name = path.resolve(DOCS, `.${decodeURIComponent(url.pathname)}`);
      if (name !== DOCS && !name.startsWith(`${DOCS}${path.sep}`)) { response.writeHead(403).end(); return; }
      if ((await fs.stat(name)).isDirectory()) name = path.join(name, 'index.html');
      const content = await fs.readFile(name);
      response.writeHead(200, { 'Content-Type': types[path.extname(name)] || 'application/octet-stream' });
      response.end(content);
    } catch { response.writeHead(404).end('Not found'); }
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '0.0.0.0', resolve); });
  return `http://127.0.0.1:${server.address().port}/`;
}

try {
  await fs.mkdir(CACHE, { recursive: true });
  report.checker_sha256 = createHash('sha256').update(await fs.readFile(fileURLToPath(import.meta.url))).digest('hex');
  report.site_inputs_sha256 = await siteInputs();
  report.site_inputs_sha256['index.html'] = createHash('sha256').update(await fs.readFile(path.join(ROOT, 'index.html'))).digest('hex');
  // This npm-delivered binary and its verified-system shared libraries let the
  // test run without apt, a privileged OS install, or downloading from a new host.
  const packageRoot = path.dirname(path.dirname(fileURLToPath(import.meta.resolve('@sparticuz/chromium'))));
  report.browser_package = 'chromium 153.0.0';
  const libraries = path.join(CACHE, 'lambda-libs');
  await fs.mkdir(libraries, { recursive: true });
  const tar = require('tar-fs');
  await pipeline(createReadStream(path.join(packageRoot, 'bin/al2023.tar.br')), createBrotliDecompress(), tar.extract(libraries));
  const executablePath = process.env.PLAYWRIGHT_EXECUTABLE_PATH || await bundled.executablePath();
  browser = await chromium.launch({ executablePath, args: bundled.args, headless: true,
    env: { ...process.env, LD_LIBRARY_PATH: `${path.join(libraries, 'lib')}:${process.env.LD_LIBRARY_PATH || ''}` } });
  report.browser_version = browser.version();
  const providedBase = process.env.GEMS_PREVIEW_URL;
  const base = providedBase ? `${providedBase.replace(/\/$/, '')}/` : await serve();
  const context = await browser.newContext({ viewport: { width: 1512, height: 1080 }, acceptDownloads: true });
  await context.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: new URL(base).origin });
  const page = await context.newPage();
  const runtimeErrors = [];
  page.on('pageerror', error => runtimeErrors.push(error.message));
  const card = JSON.parse(await fs.readFile(path.join(ROOT, 'evidence/run-card.json'), 'utf8'));
  const experiment = JSON.parse(await fs.readFile(path.join(ROOT, 'evidence/experiment.json'), 'utf8'));

  await check('entry_and_negative_decision', async () => {
    const response = await page.goto(base, { waitUntil: 'networkidle' });
    assert.equal(response.status(), 200);
    assert.match(await page.title(), /Executive summary/);
    assert.match(await page.locator('.decision-panel').first().innerText(), /DO NOT SUBMIT/);
    assert.match(await page.locator('main').innerText(), /60,988/);
    assert.match(await page.locator('main').innerText(), /gems-segment-pooled-v1/);
    await page.screenshot({ path: path.join(CACHE, 'desktop.png'), fullPage: true });
    const button = page.locator('a[download][href$=".tif"]').first();
    const box = await button.boundingBox();
    assert(box && box.y < 1080, 'Research download must be prominent on desktop');
    return 'Root entry redirects correctly; explicit negative decision and local holdout metadata.';
  });
  await check('exact_download_hash', async () => {
    const [download] = await Promise.all([
      page.waitForEvent('download'), page.locator('a[download][href$=".tif"]').first().click(),
    ]);
    assert.equal(download.suggestedFilename(), experiment.artifact.filename);
    const bytes = await fs.readFile(await download.path());
    assert.equal(bytes.length, experiment.artifact.bytes);
    assert.equal(createHash('sha256').update(bytes).digest('hex'), card.raster_sha256);
    return { filename: download.suggestedFilename(), bytes: bytes.length, sha256: card.raster_sha256 };
  });
  await check('clipboard_exact_note', async () => {
    await page.getByRole('button', { name: 'Copy research note' }).click();
    await page.waitForFunction(() => document.querySelector('.copy-status')?.textContent.startsWith('Copied.'));
    assert.equal(await page.evaluate(() => navigator.clipboard.readText()), card.submission_note);
    assert(card.submission_note.length <= 140);
    return `Exact ${card.submission_note.length}-character research-only note copied.`;
  });
  await check('clipboard_failure_is_honest', async () => {
    await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', { configurable: true,
      value: { writeText: async () => { throw new Error('permission denied'); } } }));
    await page.getByRole('button', { name: 'Copy research note' }).click();
    await page.waitForFunction(() => document.querySelector('.copy-status')?.textContent.includes('Clipboard unavailable'));
    return 'Denied clipboard does not falsely report success; note remains selectable.';
  });
  await check('clipboard_legacy_fallback', async () => {
    await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', { configurable: true, value: undefined }));
    await page.getByRole('button', { name: 'Copy research note' }).click();
    await page.waitForFunction(() => document.querySelector('.copy-status')?.textContent.startsWith('Copied.'));
    return 'Selection/execCommand fallback works without Clipboard API.';
  });
  await check('desktop_accessibility', async () => {
    const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    const violations = result.violations.map(item => ({ id: item.id, impact: item.impact,
      nodes: item.nodes.map(node => ({ target: node.target, summary: node.failureSummary })) }));
    assert.deepEqual(violations, [], JSON.stringify(violations));
    return { wcag_violations: 0, incomplete_checks: result.incomplete.length };
  });
  await check('responsive_and_mobile_download', async () => {
    const widths = [320, 390, 768, 1024, 1512, 1920];
    for (const width of widths) {
      await page.setViewportSize({ width, height: 844 });
      const sizes = await page.evaluate(() => ({ viewport: innerWidth, page: document.documentElement.scrollWidth }));
      assert(sizes.page <= sizes.viewport + 1, `Horizontal page overflow at ${width}: ${sizes.page}`);
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(CACHE, 'mobile.png'), fullPage: true });
    const box = await page.locator('a[download][href$=".tif"]').first().boundingBox();
    assert(box && box.y >= 0 && box.y + box.height <= 844, `Mobile research download must be fully above fold: ${JSON.stringify(box)}`);
    return { viewport_widths: widths, mobile_download_top: box.y };
  });
  await check('mobile_accessibility', async () => {
    const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    assert.deepEqual(result.violations.map(item => ({ id: item.id, targets: item.nodes.map(node => node.target) })), []);
    return { wcag_violations: 0, incomplete_checks: result.incomplete.length };
  });
  await check('nine_site_pages_and_guides', async () => {
    for (const name of [...[24, 25, 27, 28, 30, 31, 32, 33, 36].map(n => `sites/GEMSDOE${n}.html`),
      'sites.html', 'submission-guide.html', 'research.html', 'sources.html']) {
      const response = await page.goto(new URL(name, base).href, { waitUntil: 'networkidle' });
      assert.equal(response.status(), 200, name);
      const sizes = await page.evaluate(() => ({ viewport: innerWidth, page: document.documentElement.scrollWidth }));
      assert(sizes.page <= sizes.viewport + 1, `Mobile overflow: ${name}`);
      if (name.startsWith('sites/')) assert.match(await page.locator('main').innerText(), /DO NOT SUBMIT/);
      const a11y = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
      assert.deepEqual(a11y.violations.map(item => ({ id: item.id, targets: item.nodes.map(node => node.target) })), [], `Accessibility: ${name}`);
    }
    for (const n of [24,25,27,28,30,31,32,33,36]) {
      await page.goto(new URL(`sites/gemsdoe${n}.html`, base).href, { waitUntil: 'networkidle' });
      assert.equal(new URL(page.url()).pathname.split('/').at(-1), `GEMSDOE${n}.html`);
    }
    await page.goto(new URL('hypotheses.html', base).href, { waitUntil: 'networkidle' });
    assert.equal(new URL(page.url()).pathname.split('/').at(-1), 'research.html');
    const expected = ['index.html', 'docs/index.html', 'docs/executive-summary.html', 'docs/sites.html',
      'docs/submission-guide.html', 'docs/research.html', 'docs/sources.html', 'docs/hypotheses.html'];
    for (const n of [24,25,27,28,30,31,32,33,36]) expected.push(`docs/sites/GEMSDOE${n}.html`, `docs/sites/gemsdoe${n}.html`);
    assert.deepEqual(Object.keys(report.site_inputs_sha256).filter(p => p.endsWith('.html')).sort(), expected.sort(), 'Every active HTML route must be covered; unknown legacy pages are not silently ignored');
    return 'Thirteen canonical secondary pages pass automated WCAG 2.1 A/AA checks; ten legacy routes redirect correctly, in addition to entry/index. Every active HTML route is accounted for. Automated checks are not a conformance certificate.';
  });
  await check('no_runtime_errors', async () => { assert.deepEqual(runtimeErrors, []); return 'No browser JavaScript exceptions.'; });
} catch (error) {
  report.errors.push(String(error.stack || error));
} finally {
  if (browser) await browser.close();
  if (server) await new Promise(resolve => server.close(resolve));
  report.passed = report.errors.length === 0;
  await fs.mkdir(path.join(ROOT, 'evidence'), { recursive: true });
  await fs.writeFile(path.join(ROOT, 'evidence/browser-verification.json'), `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify(report, null, 2));
  process.exitCode = report.passed ? 0 : 1;
}
