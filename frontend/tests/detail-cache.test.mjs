import test from 'node:test';
import assert from 'node:assert/strict';
import { createDetailCache } from '../src/features/catalog/detailCache.ts';

test('prefetch and navigation share a request and cache products separately', async () => {
  let calls = 0;
  const cache = createDetailCache(async id => { calls++; return { id }; }, () => false);
  await Promise.all([cache.load('1'), cache.load('1')]);
  await cache.load('1');
  assert.equal(calls, 1);
  assert.equal(cache.snapshot('2').product, null);
  await cache.load('2');
  assert.equal(cache.snapshot('1').product.id, '1');
  assert.equal(cache.snapshot('2').product.id, '2');
});

test('stale details survive network failure but are removed on 404', async () => {
  let time = 100;
  let failure = '';
  const cache = createDetailCache(async id => {
    if (failure) throw new Error(failure);
    return { id };
  }, error => error.message === '404', () => time);
  await cache.load('1');
  time += 60001;
  failure = 'offline';
  await cache.load('1');
  assert.equal(cache.snapshot('1').product.id, '1');
  assert.equal(cache.snapshot('1').error, 'offline');
  failure = '404';
  await cache.load('1', true);
  assert.equal(cache.snapshot('1').product, null);
  assert.equal(cache.snapshot('1').notFound, true);
});
