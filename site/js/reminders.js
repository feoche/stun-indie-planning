// Alertes dans l'appli, 10 minutes avant chaque nouvelle affectation (hors Off).
import { dueReminder } from './model.js';
import { getFired, addFired } from './store.js';

export function checkReminders({ blocks, slug, now, fired, notify, markFired }) {
  const due = dueReminder(blocks, slug, now, fired);
  if (!due) return;
  markFired(due.key);
  notify(due.block, due.key);
}

export function startReminders({ getBlocks, getSlug, nowFn, notify, intervalMs = 15000 }) {
  const tick = () => {
    const slug = getSlug();
    if (!slug) return;
    checkReminders({
      blocks: getBlocks(), slug, now: nowFn(), fired: getFired(), notify, markFired: addFired,
    });
  };
  tick();
  const timer = setInterval(tick, intervalMs);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) tick(); });
  return { stop: () => clearInterval(timer), tick };
}
