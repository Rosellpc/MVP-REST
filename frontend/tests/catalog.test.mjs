import test from 'node:test';
import assert from 'node:assert/strict';
import { filterProducts, getProductCategories } from '../src/utils/filterProducts.ts';

const products = [
  { id: 1, name: 'Arroz', category: { id: 2, name: 'Platos' } },
  { id: 2, name: 'Jugo', category: { id: 1, name: 'Bebidas' } },
  { id: 3, name: 'Pasta', category: { id: 2, name: 'Platos' } },
];

test('filtra solo por ID de categoría y conserva la carta original', () => {
  assert.deepEqual(filterProducts(products, { category: '2' }).map(p => p.id), [1, 3]);
  assert.deepEqual(filterProducts(products, { category: '' }), products);
  assert.deepEqual(filterProducts(products, { category: '999' }), []);
  assert.equal(products.length, 3);
});

test('las categorías provienen de toda la carta, sin duplicados', () => {
  assert.deepEqual(getProductCategories(products), [
    { id: 1, name: 'Bebidas' }, { id: 2, name: 'Platos' },
  ]);
  assert.deepEqual(getProductCategories([]), []);
});
