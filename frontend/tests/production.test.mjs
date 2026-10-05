import test from 'node:test';
import assert from 'node:assert/strict';
import { fetchTickets, updateTicket } from '../src/features/production/productionApi.ts';
import { getOrder } from '../src/features/orders/orderApi.ts';

test('tickets traverse pagination through local API proxy', async t => {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async url => {
    calls.push(url);
    return Response.json(calls.length === 1
      ? { results: [{ id: 1 }], next: 'http://backend:8000/api/v1/production/tickets/?station=BAR&page=2' }
      : { results: [{ id: 2 }], next: null });
  });
  assert.deepEqual(await fetchTickets('BAR', new AbortController().signal), [{ id: 1 }, { id: 2 }]);
  assert.equal(calls[1], '/api/v1/production/tickets/?station=BAR&page=2');
});

test('ticket cancellation submits CSRF and reason; conflicts remain visible', async t => {
  t.mock.method(globalThis, 'fetch', async (url, init) => {
    if (url.endsWith('csrf/')) return Response.json({ csrfToken: 'fresh' });
    assert.equal(init.headers['X-CSRFToken'], 'fresh');
    assert.deepEqual(JSON.parse(init.body), { reason: 'Sin insumos' });
    return Response.json({ detail: 'Actualiza la lista' }, { status: 409 });
  });
  await assert.rejects(updateTicket(1, 'cancel', 'Sin insumos'), /Actualiza la lista/);
});

test('public tracking only performs GET and preserves preparation state', async t => {
  t.mock.method(globalThis, 'fetch', async (url, init) => {
    assert.equal(url, '/api/v1/orders/demo-code/');
    assert.equal(init.method, undefined);
    return Response.json({ production_status: 'PARTIALLY_CANCELLED', payment_status: 'SIMULATED' });
  });
  assert.equal((await getOrder('demo-code', new AbortController().signal)).production_status, 'PARTIALLY_CANCELLED');
});
