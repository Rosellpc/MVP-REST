import test from 'node:test';
import assert from 'node:assert/strict';
import { createMenuCache } from '../src/features/catalog/menuCache.ts';

test('reuses fresh menu and deduplicates concurrent requests', async () => {
  let calls = 0;
  let time = 100;
  const cache = createMenuCache(async () => { calls++; return [{ id: calls }]; }, () => time);
  await Promise.all([cache.refresh(), cache.refresh()]);
  assert.equal(calls, 1);
  await cache.refresh();
  assert.equal(calls, 1);
  time += 60001;
  const refresh = cache.refresh();
  assert.deepEqual(cache.getSnapshot().products, [{ id: 1 }]);
  assert.equal(cache.getSnapshot().hasData, true);
  await refresh;
  assert.equal(calls, 2);
});

test('background failure preserves last menu and explicit retry recovers', async () => {
  let fail = false;
  const cache = createMenuCache(async () => { if (fail) throw new Error('offline'); return [{ id: 1 }]; });
  await cache.refresh();
  fail = true;
  await cache.refresh(true);
  assert.equal(cache.getSnapshot().error, 'offline');
  assert.equal(cache.getSnapshot().hasData, true);
  assert.equal(cache.getSnapshot().products.length, 1);
  fail = false;
  await cache.refresh(true);
  assert.equal(cache.getSnapshot().error, '');
});

test('empty catalog is a valid cached response', async () => {
  let calls = 0;
  const cache = createMenuCache(async () => { calls++; return []; });
  await cache.refresh();
  await cache.refresh();
  assert.equal(calls, 1);
  assert.equal(cache.getSnapshot().hasData, true);
});
