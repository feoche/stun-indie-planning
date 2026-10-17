import test from 'node:test';
import assert from 'node:assert/strict';
import { createPlanningSource } from '../../site/js/data.js';

function harness(responses) {
  const calls = [];
  const updates = [];
  const statuses = [];
  const fetchFn = async (url, opts) => {
    calls.push({ url, opts });
    const r = responses.shift();
    if (r instanceof Error) throw r;
    return { ok: true, json: async () => r };
  };
  const source = createPlanningSource({
    url: './data/planning.json', fetchFn,
    onUpdate: (p) => updates.push(p), onStatus: (s) => statuses.push(s),
  });
  return { source, calls, updates, statuses };
}

test('poll bypasses the HTTP cache', async () => {
  const h = harness([{ version: 'a' }]);
  await h.source.pollNow();
  assert.equal(h.calls[0].opts.cache, 'no-store');
});

test('onUpdate fires only when the version changes', async () => {
  const h = harness([{ version: 'a' }, { version: 'a' }, { version: 'b' }]);
  await h.source.pollNow();
  await h.source.pollNow();
  assert.equal(h.updates.length, 1);
  await h.source.pollNow();
  assert.deepEqual(h.updates.map((p) => p.version), ['a', 'b']);
});

test('network failure goes offline without throwing, then recovers', async () => {
  const h = harness([{ version: 'a' }, new Error('network'), { version: 'a' }]);
  await h.source.pollNow();
  await h.source.pollNow();
  assert.equal(h.statuses.at(-1), 'offline');
  assert.equal(h.updates.length, 1);
  await h.source.pollNow();
  assert.equal(h.statuses.at(-1), 'online');
  assert.equal(h.updates.length, 1);
});
