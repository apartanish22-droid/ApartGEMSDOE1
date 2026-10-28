/* The scheduled feed is a public standings observation, never a file receipt. */
(async () => {
  const target = document.getElementById('public-feed');
  if (!target) return;
  try {
    const response = await fetch('data/public_feed.json', {cache: 'no-cache'});
    if (!response.ok) throw new Error('feed unavailable');
    const data = await response.json();
    if (data.status !== 'ok' || !Number.isFinite(data.top_public_dti) || !data.observed_utc) {
      throw new Error('feed stale or malformed');
    }
    target.textContent = `Public leaderboard observation: ${data.top_public_dti.toFixed(4)} at ${data.observed_utc}. This is not a file-level submission receipt and may be stale.`;
  } catch (_) {
    target.textContent = 'Public leaderboard observation unavailable or updating. Check the official page; no file score is inferred.';
  }
})();
