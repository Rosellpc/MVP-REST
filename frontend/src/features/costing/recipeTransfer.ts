import type { Version } from "./types";

// Drafts remain in the full backup; only valid formulations enter recalculation imports.
export function recipeTransferBatches(versions: Version[]) {
  const ready = versions.filter(({ snapshot: s }) => !s.pending_costing && s.per_portion !== null && s.lines.length > 0 && s.tax_percent !== "");
  const recipes = ready.map(({ snapshot: s }) => ({
    name: s.name, category: s.category, portions: s.portions, portion_size: s.portion_size,
    preparation_minutes: s.preparation_minutes, cooking_minutes: s.cooking_minutes,
    temperature: s.temperature, preparation: s.preparation, presentation: s.presentation,
    allergens: s.allergens, selling_price: s.selling_price, tax_percent: s.tax_percent,
    lines: s.lines.map(line => ({ ingredient_name: line.name, quantity: line.quantity, unit: line.unit, basis: line.basis })),
  }));
  const batches = [];
  for (let index = 0; index < recipes.length; index += 100) batches.push({ recipes: recipes.slice(index, index + 100) });
  return { batches, pending: versions.length - ready.length };
}
