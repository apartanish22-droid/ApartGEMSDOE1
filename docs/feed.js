/* Timestamped public observation; never a file-level score or submission receipt. */
(async () => {
  const score = document.getElementById('public-score');
  const state = document.getElementById('public-feed-state');
  if (!score || !state) return;
  const official = 'https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/';
  function link(text) {
    const a = document.createElement('a');
    a.href = official;
    a.textContent = text;
    return a;
  }
  try {
    const response = await fetch('data/public_feed.json', {cache: 'no-store'});
    if (!response.ok) throw new Error('feed unavailable');
    const data = await response.json();
    const when = Date.parse(data.observed_utc);
    const age = Date.now() - when;
    const valid = data.status === 'ok' && typeof data.top_public_dti === 'number' &&
      data.top_public_dti >= 0 && data.top_public_dti <= 1 && Number.isFinite(when);
    if (!valid) throw new Error('no valid public observation');
    score.textContent = data.top_public_dti.toFixed(4);
    state.textContent = `${age > 36 * 60 * 60 * 1000 ? 'Stale observation' : 'Observed'} ${data.observed_utc} UTC · public only · `;
    state.append(link('check live ↗'));
  } catch (_) {
    score.textContent = 'Unavailable';
    state.textContent = 'Refresh unavailable · ';
    state.append(link('check official source ↗'));
  }
})();
