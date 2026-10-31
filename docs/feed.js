/* A dated public standings observation is never a file-level submission receipt. */
(async () => {
  const target = document.getElementById('public-feed');
  if (!target) return;
  const maxAgeMs = 24 * 60 * 60 * 1000;
  const validScore = value => typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1;
  const freshEnough = stamp => {
    const observed = Date.parse(stamp);
    const age = Date.now() - observed;
    return Number.isFinite(observed) && age >= -5 * 60 * 1000 && age <= maxAgeMs;
  };
  try {
    const response = await fetch('data/public_feed.json', {cache: 'no-cache'});
    if (!response.ok) throw new Error('feed unavailable');
    const data = await response.json();
    const configuredAge = Number(data.max_age_seconds);
    const scheduledAgeMs = Math.min(
      Number.isFinite(configuredAge) && configuredAge > 0 ? configuredAge : maxAgeMs / 1000,
      maxAgeMs / 1000,
    ) * 1000;
    const scheduledObserved = Date.parse(data.observed_utc);
    const scheduledAge = Date.now() - scheduledObserved;
    const scheduledValid = data.status === 'ok' && validScore(data.top_public_dti) &&
      Number.isFinite(scheduledObserved) && scheduledAge >= -5 * 60 * 1000 &&
      scheduledAge <= scheduledAgeMs;
    if (scheduledValid) {
      target.textContent = `Public leaderboard observation: ${data.top_public_dti.toFixed(4)} at ${data.observed_utc}. This is not a file-level submission receipt.`;
      return;
    }

    const direct = data.direct_page_observation;
    if (direct && direct.status === 'observed' && validScore(direct.top_public_dti) &&
        freshEnough(direct.observed_utc)) {
      const rank = Number.isInteger(direct.top_rank) ? `rank ${direct.top_rank}, ` : '';
      const participant = typeof direct.top_participant === 'string' ? direct.top_participant : 'participant not recorded';
      target.textContent = `Direct official leaderboard page read: ${direct.top_public_dti.toFixed(4)} (${rank}${participant}) on ${direct.observed_utc}. Scheduled feed refresh is unavailable. Team-level public standing; not a file-level submission receipt.`;
      return;
    }
    throw new Error('feed stale or malformed');
  } catch (_) {
    target.textContent = 'Public leaderboard observation unavailable or stale. Check the official page; no file score is inferred.';
  }
})();
