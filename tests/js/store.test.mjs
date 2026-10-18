import test from 'node:test';
import assert from 'node:assert/strict';
import { getSeen, setSeen } from '../../site/js/store.js';

test('seen state is kept per person', () => {
  setSeen('robin', { version: 'a', blocks: [1] });
  setSeen('jeff', { version: 'b', blocks: [2] });
  assert.equal(getSeen('robin').version, 'a');
  assert.equal(getSeen('jeff').version, 'b');
  assert.equal(getSeen('chris'), null);
});
