export type Ingredient = { id: number; name: string; purchase_unit: string; purchase_quantity: string; purchase_price: string; yield_percent: string };
export type Line = { ingredient_id: number; quantity: string; unit: string; basis: string; name?: string; cost?: string };
export type FormRecipe = {
  name: string; portions: number; category: string; portion_size: string;
  preparation_minutes: number | null; cooking_minutes: number | null; temperature: string;
  preparation: string; presentation: string; allergens: string; selling_price: string; tax_percent: string; lines: Line[];
};
export type Snapshot = FormRecipe & { total: string; per_portion: string; net_price: string; margin: string; food_cost_percent: string | null; import_source?: { file: string; sheet: string; original_total: string; notes: string[]; original_cooking_time?: string } };
export type Version = { id: number; recipe_id: number; number: number; snapshot: Snapshot; created_at: string; author: string };
export const units = ["g", "kg", "ml", "l", "unit"];
