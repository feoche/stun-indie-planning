import test from 'node:test';
import assert from 'node:assert/strict';
import { checkReminders } from '../../site/js/reminders.js';
import { parseBlocks } from '../../site/js/model.js';

const blocks = parseBlocks({
  blocks: [
    { start: '2026-10-24T09:00:00+02:00', end: '2026-10-24T10:00:00+02:00', role: 'Run' },
    { start: '2026-10-24T10:00:00+02:00', end: '2026-10-24T11:00:00+02:00', role: 'Backup' },
    { start: '2026-10-24T11:00:00+02:00', end: '2026-10-24T12:00:00+02:00', role: 'Off' },
  ],
});

function run(nowIso, fired = new Set()) {
  const notified = [];
  const call = () => checkReminders({
    blocks, slug: 'robin', now: new Date(nowIso), fired,
    notify: (block) => notified.push(block), markFired: (key) => fired.add(key),
  });
  return { notified, call };
}

test('notifies once for a block starting in 10 minutes', () => {
  const { notified, call } = run('2026-10-24T07:50:00Z'); // 09:50 Paris -> Backup at 10:00
  call();
  call();
  assert.equal(notified.length, 1);
  assert.equal(notified[0].role, 'Backup');
});

test('does not notify for Off', () => {
  const { notified, call } = run('2026-10-24T08:50:00Z'); // 10:50 Paris -> Off at 11:00
  call();
  assert.equal(notified.length, 0);
});

test('does not notify outside the 10-minute window', () => {
  const { notified, call } = run('2026-10-24T07:45:00Z'); // 09:45 Paris
  call();
  assert.equal(notified.length, 0);
});
