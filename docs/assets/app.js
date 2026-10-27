'use strict';
document.querySelectorAll('[data-copy]').forEach((button) => {
  button.addEventListener('click', async () => {
    const field = document.getElementById(button.dataset.copy);
    const status = button.parentElement.querySelector('.copy-status');
    if (!field || !status) return;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(field.value);
      } else {
        field.focus();
        field.select();
        if (!document.execCommand('copy')) throw new Error('Clipboard unavailable');
      }
      status.textContent = 'Copied. Research only — do not submit.';
    } catch (_) {
      status.textContent = 'Clipboard unavailable; the full note is selectable above.';
    }
  });
});
