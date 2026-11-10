import test from 'node:test';
import assert from 'node:assert/strict';
import { cartSignature, validDelivery, readCheckoutDraft, saveCheckoutDraft, removeCheckoutDraft, DRAFT_STORAGE_KEY } from '../src/features/orders/checkoutDraft.ts';

const data = new Map();
globalThis.sessionStorage = {
  getItem: key => data.get(key) ?? null,
  setItem: (key, value) => data.set(key, value),
  removeItem: key => data.delete(key),
};
const draft = { customer_name: 'Rosell', fulfillment: 'DINE_IN', table_label: '12',
  items: [{ product_id: 2, quantity: 1 }, { product_id: 1, quantity: 2 }], expected_total: '80.00' };

test('delivery requires a name and a table for dine-in, but not for pickup', () => {
  assert.equal(validDelivery(draft), true);
  assert.equal(validDelivery({ ...draft, customer_name: '  ' }), false);
  assert.equal(validDelivery({ ...draft, table_label: '  ' }), false);
  assert.equal(validDelivery({ ...draft, fulfillment: 'PICKUP', table_label: '' }), true);
});

test('cart identity ignores line order but detects changes in quantities and products', () => {
  assert.equal(cartSignature(draft.items), cartSignature([...draft.items].reverse()));
  assert.notEqual(cartSignature(draft.items), cartSignature([{ product_id: 2, quantity: 2 }]));
});

test('delivery and quote survive refresh and are removed after confirmation', () => {
  saveCheckoutDraft(draft);
  assert.deepEqual(readCheckoutDraft(), draft);
  removeCheckoutDraft();
  assert.equal(readCheckoutDraft(), null);
});

test('corrupt drafts cannot bypass the cart and delivery form', () => {
  for (const value of [null, {}, { ...draft, items: [] }, { ...draft, items: [null] },
    { ...draft, items: [draft.items[0], draft.items[0]] },
    { ...draft, items: [{ product_id: 1, quantity: 0 }] },
    { ...draft, fulfillment: 'INVALID' }, { ...draft, expected_total: 'NaN' },
    { ...draft, customer_name: 'a'.repeat(81) }]) {
    data.set(DRAFT_STORAGE_KEY, JSON.stringify(value));
    assert.equal(readCheckoutDraft(), null);
  }
  data.set(DRAFT_STORAGE_KEY, '{');
  assert.equal(readCheckoutDraft(), null);
});

test('storage failure propagates so the cart can block payment with a useful error', () => {
  const storage = globalThis.sessionStorage;
  globalThis.sessionStorage = { setItem() { throw new Error('blocked'); } };
  try { assert.throws(() => saveCheckoutDraft(draft), /blocked/); }
  finally { globalThis.sessionStorage = storage; }
});
