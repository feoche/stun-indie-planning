import test from 'node:test';
import assert from 'node:assert/strict';
import {
  parseBlocks, findPerson, parisDate, formatTime, blocksOfDay, homeState,
  blockKey, dueReminder, changedBlocks, REMINDER_LEAD_MS,
} from '../../site/js/model.js';

const days = [{ date: '2026-10-23' }, { date: '2026-10-24' }, { date: '2026-10-25' }];
const raw = (start, end, role) => ({ start, end, role });
const person = {
  name: 'Robin',
  slug: 'robin',
  blocks: [
    raw('2026-10-24T09:00:00+02:00', '2026-10-24T10:00:00+02:00', 'Run'),
    raw('2026-10-24T10:00:00+02:00', '2026-10-24T12:00:00+02:00', 'Backup'),
    raw('2026-10-24T12:00:00+02:00', '2026-10-24T12:30:00+02:00', 'Stand'),
    raw('2026-10-24T12:30:00+02:00', '2026-10-24T13:00:00+02:00', 'Off'),
    raw('2026-10-25T09:00:00+01:00', '2026-10-25T10:00:00+01:00', 'Run'),
  ],
};
const blocks = parseBlocks(person);
const at = (iso) => new Date(iso);

test('REMINDER_LEAD_MS is 10 minutes', () => assert.equal(REMINDER_LEAD_MS, 600000));

test('findPerson returns null for unknown slug', () => {
  assert.equal(findPerson({ people: [person] }, 'robin'), person);
  assert.equal(findPerson({ people: [person] }, 'nobody'), null);
});

test('before the festival', () => {
  const s = homeState(blocks, days, at('2026-10-22T12:00:00Z'));
  assert.equal(s.kind, 'before');
  assert.equal(s.next, blocks[0]);
});

test('not-started: before first block of the day', () => {
  const s = homeState(blocks, days, at('2026-10-24T06:59:00Z')); // 08:59 Paris
  assert.equal(s.kind, 'not-started');
  assert.equal(s.current, null);
  assert.equal(s.next, blocks[0]);
});

test('active has current and next', () => {
  const s = homeState(blocks, days, at('2026-10-24T08:30:00Z')); // 10:30 Paris
  assert.equal(s.kind, 'active');
  assert.equal(s.current, blocks[1]);
  assert.equal(s.next, blocks[2]);
});

test('block ending exactly now is no longer current', () => {
  const s = homeState(blocks, days, at('2026-10-24T08:00:00Z')); // 10:00 Paris
  assert.equal(s.current, blocks[1]);
});

test('off-day: person has no blocks that day', () => {
  const s = homeState(blocks, days, at('2026-10-23T10:00:00Z'));
  assert.equal(s.kind, 'off-day');
});

test('done-today after the last block', () => {
  const s = homeState(blocks, days, at('2026-10-25T09:00:00Z')); // 10:00 Paris, block ended
  assert.equal(s.kind, 'done-today');
  assert.equal(s.current, null);
});

test('after the festival', () => {
  assert.equal(homeState(blocks, days, at('2026-10-26T10:00:00Z')).kind, 'after');
});

test('DST: Sunday offset is +01:00', () => {
  const s = homeState(blocks, days, at('2026-10-25T08:00:00Z'));
  assert.equal(s.kind, 'active');
  assert.equal(s.current, blocks[4]);
  assert.equal(formatTime(at('2026-10-25T08:00:00Z')), '9h00');
  assert.equal(formatTime(at('2026-10-23T07:00:00Z')), '9h00');
  assert.equal(formatTime(at('2026-10-24T08:30:00Z')), '10h30');
});

test('parisDate uses Paris, not the device zone', () => {
  assert.equal(parisDate(at('2026-10-23T22:30:00Z')), '2026-10-24');
  assert.equal(parisDate(at('2026-10-24T12:00:00Z')), '2026-10-24');
});

test('blocksOfDay filters by Paris date', () => {
  assert.equal(blocksOfDay(blocks, '2026-10-24').length, 4);
  assert.equal(blocksOfDay(blocks, '2026-10-23').length, 0);
});

test('dueReminder window: [start-10min, start)', () => {
  const fired = new Set();
  const due = dueReminder(blocks, 'robin', at('2026-10-24T07:50:00Z'), fired); // 09:50 Paris
  assert.equal(due.block, blocks[1]);
  assert.equal(due.key, blockKey('robin', blocks[1]));
  assert.equal(dueReminder(blocks, 'robin', at('2026-10-24T07:49:59Z'), fired), null);
  assert.equal(dueReminder(blocks, 'robin', at('2026-10-24T08:00:00Z'), fired), null);
  assert.equal(dueReminder(blocks, 'robin', at('2026-10-24T07:50:00Z'), new Set([due.key])), null);
});

test('dueReminder ignores Off', () => {
  assert.equal(dueReminder(blocks, 'robin', at('2026-10-24T10:25:00Z'), new Set()), null); // 12:25 -> Off at 12:30
});

test('dueReminder includes every role but Off', () => {
  const due = dueReminder(blocks, 'robin', at('2026-10-24T09:55:00Z'), new Set()); // 11:55 -> Stand at 12:00
  assert.equal(due.block.role, 'Stand');
});

test('changedBlocks marks moved or new blocks only', () => {
  const next = structuredClone(person.blocks);
  next[1] = raw('2026-10-24T10:00:00+02:00', '2026-10-24T11:30:00+02:00', 'Backup');
  const changed = changedBlocks(person.blocks, next);
  assert.deepEqual([...changed], [at('2026-10-24T10:00:00+02:00').toISOString()]);
  assert.equal(changedBlocks(person.blocks, person.blocks).size, 0);
});

import { clockOffset } from '../../site/js/model.js';

test('clockOffset: ?now= is honoured on localhost only', () => {
  const real = Date.parse('2026-10-24T10:00:00Z');
  const q = '?now=2026-10-24T14:10:00%2B02:00';
  assert.equal(clockOffset(q, 'localhost', real), Date.parse('2026-10-24T12:10:00Z') - real);
  assert.equal(clockOffset(q, '127.0.0.1', real), Date.parse('2026-10-24T12:10:00Z') - real);
  assert.equal(clockOffset(q, 'feoche.github.io', real), 0);
  assert.equal(clockOffset('?now=garbage', 'localhost', real), 0);
  assert.equal(clockOffset('', 'localhost', real), 0);
});

import { removedBlocks, isAlertActive, defaultDay, platformOf } from '../../site/js/model.js';

test('removedBlocks reports blocks that disappeared', () => {
  const next = person.blocks.slice(1);
  assert.equal(removedBlocks(person.blocks, next).size, 1);
  assert.equal(removedBlocks(person.blocks, person.blocks).size, 0);
});

test('isAlertActive stops once the block has started', () => {
  assert.equal(isAlertActive(blocks[1], at('2026-10-24T07:55:00Z')), true);
  assert.equal(isAlertActive(blocks[1], at('2026-10-24T08:00:00Z')), false);
});

test('defaultDay follows the Paris date, first day outside the festival', () => {
  assert.equal(defaultDay(days, at('2026-10-24T08:00:00Z')), '2026-10-24');
  assert.equal(defaultDay(days, at('2026-10-24T22:30:00Z')), '2026-10-25');
  assert.equal(defaultDay(days, at('2026-10-01T08:00:00Z')), '2026-10-23');
});

test('platformOf', () => {
  assert.equal(platformOf('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)'), 'ios');
  assert.equal(platformOf('Mozilla/5.0 (Linux; Android 14; Pixel 8)'), 'android');
  assert.equal(platformOf('Mozilla/5.0 (Windows NT 10.0)'), 'other');
});

import { slotsOfDay, roleAtTime, whoIsWhere } from '../../site/js/model.js';

const team = {
  days,
  roles: { Run: {}, Backup: {}, Off: {} },
  people: [
    { name: 'Robin', slug: 'robin', blocks: [
      raw('2026-10-24T09:00:00+02:00', '2026-10-24T10:00:00+02:00', 'Run'),
      raw('2026-10-24T10:00:00+02:00', '2026-10-24T10:30:00+02:00', 'Off'),
    ] },
    { name: 'Jeff', slug: 'jeff', blocks: [
      raw('2026-10-24T11:00:00+02:00', '2026-10-24T12:00:00+02:00', 'Backup'),
    ] },
  ],
};

test('slotsOfDay lists 30-min starts from the earliest start to the latest end (exclusive)', () => {
  const slots = slotsOfDay(team, '2026-10-24');
  assert.equal(slots.length, 6); // 9h00 .. 11h30
  assert.equal(formatTime(slots[0]), '9h00');
  assert.equal(formatTime(slots.at(-1)), '11h30');
  assert.deepEqual(slotsOfDay(team, '2026-10-23'), []);
});

test('roleAtTime is half-open and empty outside blocks', () => {
  const b = parseBlocks(team.people[0]);
  assert.equal(roleAtTime(b, at('2026-10-24T07:00:00Z')), 'Run'); // 09:00 Paris
  assert.equal(roleAtTime(b, at('2026-10-24T08:00:00Z')), 'Off'); // 10:00 Paris
  assert.equal(roleAtTime(b, at('2026-10-24T08:30:00Z')), ''); // 10:30 Paris
});

test('whoIsWhere groups names by role at a given instant', () => {
  assert.deepEqual(whoIsWhere(team, at('2026-10-24T07:30:00Z')), { Run: ['Robin'] });
  assert.deepEqual(whoIsWhere(team, at('2026-10-24T09:15:00Z')), { Backup: ['Jeff'] });
  assert.deepEqual(whoIsWhere(team, at('2026-10-22T09:15:00Z')), {});
});

import { slotProgress } from '../../site/js/model.js';

test('slotProgress is the fraction of the 30-min slot elapsed, clamped to [0, 1]', () => {
  const slot = at('2026-10-24T12:00:00Z');
  assert.equal(slotProgress(slot, at('2026-10-24T12:00:00Z')), 0);
  assert.equal(slotProgress(slot, at('2026-10-24T12:10:00Z')), 1 / 3);
  assert.equal(slotProgress(slot, at('2026-10-24T12:15:00Z')), 0.5);
  assert.equal(slotProgress(slot, at('2026-10-24T12:45:00Z')), 1);
  assert.equal(slotProgress(slot, at('2026-10-24T11:50:00Z')), 0);
});

import { roleLabel } from '../../site/js/model.js';

test('roleLabel: easter egg suffix only for Florent', () => {
  const info = { label: 'Run' };
  assert.equal(roleLabel(info, 'florent'), 'Run Chapeau');
  assert.equal(roleLabel(info, 'robin'), 'Run');
  assert.equal(roleLabel(info, null), 'Run');
});
