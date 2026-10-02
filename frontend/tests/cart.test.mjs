import test from 'node:test';
import assert from 'node:assert/strict';
import { cartReducer, cartSubtotal, parseStoredCart, priceToCents, MAX_QUANTITY } from '../src/features/cart/cartState.ts';

const product = { id: 1, name: 'Ceviche', sale_price: '25.50', image_url: '',
  description: '', category: { id: 1, name: 'Entradas' } };

test('agrega sin duplicar filas y calcula importes exactos en centavos', () => {
  const first = cartReducer([], { type: 'add', product });
  const second = cartReducer(first, { type: 'add', product });
  assert.equal(first[0].quantity, 1);
  assert.equal(second.length, 1);
  assert.equal(second[0].quantity, 2);
  assert.equal(cartSubtotal(second), 5100);
  assert.equal(priceToCents('0.10') + priceToCents('0.20'), 30);
});

test('limita cantidades y permite eliminar o vaciar', () => {
  const first = cartReducer([], { type: 'add', product });
  for (const quantity of [0, -1, 1.5, MAX_QUANTITY + 1, NaN]) {
    assert.deepEqual(cartReducer(first, { type: 'quantity', productId: 1, quantity }), first);
  }
  const max = cartReducer(first, { type: 'quantity', productId: 1, quantity: MAX_QUANTITY });
  assert.equal(cartReducer(max, { type: 'add', product })[0].quantity, MAX_QUANTITY);
  assert.deepEqual(cartReducer(first, { type: 'remove', productId: 1 }), []);
  assert.deepEqual(cartReducer(first, { type: 'clear' }), []);
});

test('recupera un carrito válido y descarta almacenamiento corrupto', () => {
  const items = cartReducer([], { type: 'add', product });
  assert.deepEqual(parseStoredCart(JSON.stringify(items)), items);
  for (const raw of [null, '{', '{}', '[null]', JSON.stringify([...items, ...items]),
    JSON.stringify([{ ...items[0], quantity: -1 }]),
    JSON.stringify([{ ...items[0], unitPrice: 'NaN' }])]) {
    assert.deepEqual(parseStoredCart(raw), []);
  }
});
