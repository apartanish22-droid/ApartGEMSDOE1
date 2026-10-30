/* Public standings are neither a file receipt nor a repository score. */
const PUBLIC_FEED_MAX_AGE_MS = 24 * 60 * 60 * 1000;
const PUBLIC_FEED_FUTURE_SKEW_MS = 5 * 60 * 1000;

function formatPublicFeedStatus(data, nowMs = Date.now()) {
  const unavailable = 'Public leaderboard observation unavailable or updating. Check the official page; no file score is inferred.';
  if (!Number.isFinite(nowMs) || !data || data.status !== 'ok' || !Number.isFinite(data.top_public_dti) ||
      data.top_public_dti < 0 || data.top_public_dti > 1 || typeof data.observed_utc !== 'string') {
    return unavailable;
  }

  const observedMs = Date.parse(data.observed_utc);
  if (!Number.isFinite(observedMs)) return unavailable;
  const ageMs = nowMs - observedMs;
  if (ageMs < -PUBLIC_FEED_FUTURE_SKEW_MS) return unavailable;
  if (ageMs >= PUBLIC_FEED_MAX_AGE_MS) {
    return `Public leaderboard feed is stale (last successful observation: ${data.observed_utc}). ` +
      'The current value is unavailable; check the official page. This is not a file-level receipt.';
  }

  return `Public leaderboard observation: ${data.top_public_dti.toFixed(4)} at ${data.observed_utc}. ` +
    'Public standings only; not a score or receipt for a file in this repository.';
}

// Expose the pure formatter for a lightweight Node regression test. Browsers
// ignore CommonJS, and this script still runs without a build step.
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {formatPublicFeedStatus, PUBLIC_FEED_MAX_AGE_MS, PUBLIC_FEED_FUTURE_SKEW_MS};
}

(async () => {
  if (typeof document === 'undefined') return;
  const target = document.getElementById('public-feed');
  if (!target) return;
  try {
    const response = await fetch('data/public_feed.json', {cache: 'no-cache'});
    if (!response.ok) throw new Error('feed unavailable');
    const data = await response.json();
    target.textContent = formatPublicFeedStatus(data);
  } catch (_) {
    target.textContent = 'Public leaderboard observation unavailable or updating. Check the official page; no file score is inferred.';
  }
})();
