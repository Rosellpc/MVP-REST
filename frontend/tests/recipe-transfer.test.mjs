import test from 'node:test';
import assert from 'node:assert/strict';
import { recipeTransferBatches } from '../src/features/costing/recipeTransfer.ts';

test('drafts are excluded from import files, complete recipes use batches of at most 100', () => {
  const recipe = { snapshot: { name: 'Recipe', per_portion: '1.00', tax_percent: '0', lines: [{ name: 'Ingredient', quantity: '1', unit: 'kg', basis: 'gross' }], source_product: { id: 99 } } };
  const draft = { snapshot: { ...recipe.snapshot, pending_costing: true, per_portion: null, lines: [] } };
  const { batches, pending } = recipeTransferBatches([...Array.from({ length: 101 }, () => recipe), draft]);
  assert.equal(pending, 1);
  assert.deepEqual(batches.map(batch => batch.recipes.length), [100, 1]);
  assert.equal(batches[0].recipes[0].lines[0].ingredient_name, 'Ingredient');
  assert.equal('source_product' in batches[0].recipes[0], false);
});
