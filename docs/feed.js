/* The scheduled feed is a public standings observation, never a file receipt. */
(async () => {
  const target = document.getElementById('public-feed');
  if (!target) return;
  try {
    const response = await fetch('data/public_feed.json', {cache: 'no-cache'});
    if (!response.ok) throw new Error('feed unavailable');
    const data = await response.json();
    const observedMs = Date.parse(data.observed_utc);
    const ageMs = Date.now() - observedMs;
    const configuredAge = Number(data.max_age_seconds);
    const maxAgeMs = Math.min(
      Number.isFinite(configuredAge) && configuredAge > 0 ? configuredAge : 24 * 60 * 60,
      24 * 60 * 60,
    ) * 1000;
    if (data.status !== 'ok' || !Number.isFinite(data.top_public_dti) ||
        data.top_public_dti < 0 || data.top_public_dti > 1 ||
        !Number.isFinite(observedMs) || ageMs < -5 * 60 * 1000 || ageMs > maxAgeMs) {
      throw new Error('feed stale or malformed');
    }
    target.textContent = `Public leaderboard observation: ${data.top_public_dti.toFixed(4)} at ${data.observed_utc}. This is not a file-level submission receipt.`;
  } catch (_) {
    target.textContent = 'Public leaderboard observation unavailable or stale. Check the official page; no file score is inferred.';
  }
})();
