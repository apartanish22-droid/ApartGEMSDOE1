/* Static evidence rendering only. Nothing in this script can authorize a file. */
(() => {
  "use strict";
  const base = document.body.dataset.base || ".";
  const node = (tag, text, className) => {
    const el = document.createElement(tag);
    if (text !== undefined) el.textContent = text;
    if (className) el.className = className;
    return el;
  };
  const link = (href, text, className) => {
    const el = node("a", text, className);
    el.href = href;
    if (href.startsWith("https://")) { el.target = "_blank"; el.rel = "noopener noreferrer"; }
    return el;
  };
  const githubUrl = href => {
    try {
      const u = new URL(href);
      return u.protocol === "https:" && u.hostname === "github.com" ? u.href : null;
    } catch (_) { return null; }
  };
  const sourceSiteUrl = href => {
    try {
      const u = new URL(href);
      return u.protocol === "https:" && u.hostname === "buffedlizard55-lab.github.io" ? u.href : null;
    } catch (_) { return null; }
  };
  const percent = n => typeof n === "number" && Number.isFinite(n) ? `${(n * 100).toFixed(2)}%` : "Unknown";
  const set = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };
  const slug = site => site.toLowerCase();

  function renderTable(body, rows) {
    const compact = body.dataset.compact === "true";
    body.replaceChildren();
    for (const row of rows) {
      const tr = node("tr");
      const site = node("td");
      site.append(link(`${base}/sites/${slug(row.site)}.html`, row.site));
      tr.append(site);
      const file = node("td");
      const safeDownload = githubUrl(row.source_download_url);
      file.append(safeDownload ? link(safeDownload, row.filename, "file-name") : node("span", "Invalid research link", "file-name"));
      file.append(node("small", "Research only · do not resubmit"));
      tr.append(file);
      const value = node("td");
      value.append(node("strong", row.user_reported_value));
      value.append(node("small", "USER-REPORTED / UNVERIFIED"));
      tr.append(value);
      if (!compact) {
        const estimate = node("td", "Not estimable");
        estimate.append(node("small", "No validated score transfer"));
        tr.append(estimate);
      }
      const unique = node("td");
      unique.append(node("span", row.literal_focus_uniqueness_pass ? "Unknown overall" : "No", "tag gray"));
      unique.append(node("small", `${percent(row.max_near_other_focus_fraction)} near ${row.closest_focus_site || "unknown"}`));
      tr.append(unique);
      const status = node("td");
      status.append(node("span", "DO NOT SUBMIT", "tag red"));
      tr.append(status);
      body.append(tr);
    }
  }

  function renderSite(row) {
    set("site-name", row.site);
    set("site-file", row.filename);
    set("site-sha", row.sha256);
    set("site-reported", `${row.user_reported_value} · USER-REPORTED / UNVERIFIED`);
    const comparison = `${percent(row.max_near_other_focus_fraction)} within 3 pixels of ${row.closest_focus_site || "unknown"} (directional, focus-site check).`;
    set("site-unique", row.literal_focus_uniqueness_pass ? `Passed focus-site screen only; full registry unknown — ${comparison}` : `NO — ${comparison}`);
    set("site-lattice", `${percent(row.near_lattice_fraction)} of this file’s dots fall within 3 pixels of the lattice.`);
    set("site-format", row.format.basic_checks_passed ? "Basic grid, inside-footprint range and finite checks pass; this does not establish portal acceptance." : "Basic saved-byte checks failed; see the audit.");
    const source = document.getElementById("site-download");
    if (source && githubUrl(row.source_download_url)) { source.href = githubUrl(row.source_download_url); source.textContent = "Download historical file for research ↗"; }
    const site = document.getElementById("site-source");
    if (site && sourceSiteUrl(row.site_url)) site.href = sourceSiteUrl(row.site_url);
  }

  async function load() {
    try {
      const response = await fetch(`${base}/data/audit.json`, { cache: "no-cache" });
      if (!response.ok) throw new Error("audit unavailable");
      const data = await response.json();
      if (data.schema_version !== "apartgems-audit-1.0" || !Array.isArray(data.historical) || data.historical.length !== 9 || data.historical.some(r => !/^GEMSDOE[0-9]+$/.test(r.site)) || !data.preflight) throw new Error("unexpected audit schema");
      set("stat-bound", `≥ ${percent(data.preflight.min_overlap_fraction)}`);
      set("bound-detail", `≥ ${percent(data.preflight.min_overlap_fraction)}`);
      document.querySelectorAll("[data-site-table]").forEach(body => renderTable(body, data.historical));
      if (document.body.dataset.site) {
        const found = data.historical.find(row => row.site === document.body.dataset.site);
        if (!found) throw new Error("site absent from snapshot");
        renderSite(found);
      }
    } catch (error) {
      document.querySelectorAll("[data-site-table]").forEach(body => {
        body.replaceChildren();
        const row = node("tr");
        const cell = node("td", "Audit snapshot unavailable. No file is authorized; try again or open the JSON audit.");
        cell.colSpan = body.dataset.compact === "true" ? 5 : 6;
        row.append(cell); body.append(row);
      });
      set("site-file", "Audit snapshot unavailable; no file authorized.");
      set("stat-bound", "Unknown");
      set("bound-detail", "Unavailable");
    }
    try {
      const response = await fetch(`${base}/data/freshness.json`, { cache: "no-cache" });
      if (!response.ok) throw new Error("freshness unavailable");
      const data = await response.json();
      const checked = Date.parse(data.checked_utc);
      const sha = value => typeof value === "string" && /^[0-9a-f]{40}$/.test(value);
      const records = Array.isArray(data.sources) ? data.sources : [];
      const validRecords = records.length === 9 && new Set(records.map(r => r.site)).size === 9 && records.every(r =>
        /^GEMSDOE[0-9]+$/.test(r.site) && sha(r.audited_commit) && (r.current_commit === null || sha(r.current_commit)));
      const unknown = records.filter(r => r.current_commit === null).length;
      const changed = records.filter(r => r.current_commit && r.current_commit !== r.audited_commit).length;
      const validCounts = Number.isInteger(data.unknown_count) && Number.isInteger(data.changed_count) &&
        data.unknown_count === unknown && data.changed_count === changed;
      const stale = !validRecords || !validCounts || !Number.isFinite(checked) || checked > Date.now() + 5 * 60 * 1000 || (Date.now() - checked > 36 * 60 * 60 * 1000);
      const suffix = stale ? "Freshness check is stale or invalid." : data.unknown_count ? `${data.unknown_count} source check(s) unknown.` :
        data.changed_count ? `${data.changed_count} source(s) changed since the audited pins; not re-audited.` :
        "All checked GitHub source heads match their audited pins.";
      set("freshness", `GitHub source-head check: ${data.checked_utc}. ${suffix} This is not a live leaderboard feed.`);
    } catch (error) {
      set("freshness", "GitHub source freshness unavailable. The decision remains blocked; this is not a live score feed.");
    }
  }
  load();
})();
