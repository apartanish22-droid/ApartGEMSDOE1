/* GitHub-only freshness check. It does not monitor or scrape DrivenData. */
(() => {
  "use strict";
  const rows = Array.from(document.querySelectorAll("[data-review-repo]"));
  const button = document.getElementById("refresh-sources");
  const summary = document.getElementById("feed-summary");
  if (!rows.length || !button || !summary) return;

  async function refresh() {
    button.disabled = true;
    summary.textContent = "Checking public GitHub repository heads…";
    const results = await Promise.all(rows.map(async row => {
      const status = row.querySelector(".feed-state");
      const repo = row.dataset.reviewRepo;
      const expected = row.dataset.reviewHead;
      status.textContent = "Checking…";
      try {
        const response = await fetch(`https://api.github.com/repos/buffedlizard55-lab/${encodeURIComponent(repo)}/commits/main`, {
          headers: { Accept: "application/vnd.github+json" }, cache: "no-store"
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (!data || typeof data.sha !== "string" || !/^[a-f0-9]{40}$/.test(data.sha)) throw new Error("Invalid response");
        const changed = data.sha !== expected;
        status.textContent = changed ? "Head changed since review" : "Head unchanged since review";
        return changed ? "changed" : "unchanged";
      } catch (_) {
        status.textContent = "Freshness unavailable";
        return "unknown";
      }
    }));
    const count = item => results.filter(x => x === item).length;
    const checkedAt = new Date().toISOString().replace("T", " ").slice(0, 19) + " UTC";
    summary.textContent = `Checked ${checkedAt}: ${count("changed")} changed, ${count("unchanged")} unchanged, ${count("unknown")} unavailable. A head check does not re-audit files or verify scores.`;
    button.disabled = false;
  }
  button.addEventListener("click", refresh);
  refresh();
})();
