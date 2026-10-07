import { useState } from "react";
import { errorText, saveCosting } from "./api";
import { units, type FormRecipe, type Ingredient, type Snapshot, type Version } from "./types";

const blank: FormRecipe = { name: "", portions: 1, category: "", portion_size: "", preparation_minutes: 0, cooking_minutes: 0, temperature: "", preparation: "", presentation: "", allergens: "", selling_price: "0", tax_percent: "0", lines: [] };
export default function RecipeEditor({ ingredients, initial, onSaved, onClose }: { ingredients: Ingredient[]; initial?: Version; onSaved: () => void; onClose: () => void }) {
  const [form, setForm] = useState<FormRecipe>(initial?.snapshot ?? blank);
  const [preview, setPreview] = useState<Snapshot | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  function update(patch: Partial<FormRecipe>) { setForm(current => ({ ...current, ...patch })); setPreview(null); }
  async function submit(save: boolean) {
    setBusy(true); setError("");
    try {
      const data = await saveCosting(save ? initial ? `recipes/${initial.recipe_id}` : "recipes" : "recipes/preview", { ...form, expected_version: initial?.number });
      if (save) onSaved(); else setPreview(data);
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  return <section className="costing-panel"><h2>{initial ? `Nueva versión de ${initial.snapshot.name}` : "Nueva receta"}</h2><p>Al guardar se conservan la ficha, los precios y el rendimiento utilizados. Una edición crea otra versión.</p>
    {error && <p role="alert" className="costing-error">{error}</p>}
    <form onSubmit={e => { e.preventDefault(); void submit(false); }}><fieldset disabled={busy}>
      <div className="costing-fields"><label>Nombre<input required maxLength={160} value={form.name} onChange={e => update({ name: e.target.value })} /></label><label>Categoría<input maxLength={100} value={form.category} onChange={e => update({ category: e.target.value })} /></label>
      <label>Porciones<input type="number" min="1" max="100000" required value={form.portions} onChange={e => update({ portions: Number(e.target.value) })} /></label><label>Tamaño de porción<input maxLength={100} placeholder="Ej.: 250 g" value={form.portion_size} onChange={e => update({ portion_size: e.target.value })} /></label>
      <label>Preparación (min)<input type="number" min="0" max="100000" required value={form.preparation_minutes ?? ""} onChange={e => update({ preparation_minutes: Number(e.target.value) })} /></label><label>Cocción (min)<input type="number" min="0" max="100000" required value={form.cooking_minutes ?? ""} onChange={e => update({ cooking_minutes: Number(e.target.value) })} /></label></div>
      <label>Temperatura de servicio<input maxLength={100} value={form.temperature} onChange={e => update({ temperature: e.target.value })} /></label>
      <h3>Composición</h3><p>Bruta: antes de limpiar. Aprovechable: cantidad neta; el cálculo incorpora la merma.</p>
      {!ingredients.length && <p>Registra un insumo antes de formular la receta.</p>}
      {form.lines.map((line, i) => <div className="costing-line" key={i}><div className="costing-fields"><label>Insumo {i + 1}<select required value={line.ingredient_id || ""} onChange={e => update({ lines: form.lines.map((row, index) => index === i ? { ...row, ingredient_id: Number(e.target.value), unit: ingredients.find(item => item.id === Number(e.target.value))?.purchase_unit ?? "g" } : row) })}><option value="">Seleccionar</option>{ingredients.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label>Cantidad<input required type="number" min="0.001" step="0.001" value={line.quantity} onChange={e => update({ lines: form.lines.map((row, index) => index === i ? { ...row, quantity: e.target.value } : row) })} /></label>
        <label>Unidad<select value={line.unit} onChange={e => update({ lines: form.lines.map((row, index) => index === i ? { ...row, unit: e.target.value } : row) })}>{units.map(unit => <option key={unit}>{unit}</option>)}</select></label>
        <label>Base<select value={line.basis} onChange={e => update({ lines: form.lines.map((row, index) => index === i ? { ...row, basis: e.target.value } : row) })}><option value="usable">Aprovechable</option><option value="gross">Bruta</option></select></label></div><button type="button" onClick={() => update({ lines: form.lines.filter((_, index) => index !== i) })}>Quitar insumo {i + 1}</button></div>)}
      <button type="button" disabled={!ingredients.length || form.lines.length >= 200} onClick={() => update({ lines: [...form.lines, { ingredient_id: 0, quantity: "", unit: "g", basis: "usable" }] })}>Añadir insumo</button>
      <h3>Ficha técnica</h3>
      <label>Preparación<textarea maxLength={20000} rows={5} value={form.preparation} onChange={e => update({ preparation: e.target.value })} /></label>
      <label>Presentación<textarea maxLength={10000} rows={3} value={form.presentation} onChange={e => update({ presentation: e.target.value })} /></label>
      <label>Alérgenos declarados<textarea maxLength={2000} rows={2} placeholder="Sin completar significa pendiente de revisar, no ausencia de alérgenos." value={form.allergens} onChange={e => update({ allergens: e.target.value })} /></label>
      <h3>Simulación de venta</h3><p>Precio por porción con impuesto incluido. El margen solo descuenta insumos; no representa utilidad neta.</p>
      <div className="costing-fields"><label>Precio final (S/)<input type="number" required min="0" step="0.01" value={form.selling_price} onChange={e => update({ selling_price: e.target.value })} /></label><label>Impuesto incluido (%)<input type="number" required min="0" max="100" step="0.01" value={form.tax_percent} onChange={e => update({ tax_percent: e.target.value })} /></label></div>
      <div className="costing-actions"><button disabled={!form.lines.length} type="submit">{busy ? "Procesando…" : "Calcular / simular"}</button><button type="button" onClick={onClose}>Cerrar editor</button></div>
      {preview && <div className="costing-result" aria-live="polite"><p>Total: S/ {preview.total} · Por porción: S/ {preview.per_portion}</p><p>Venta neta: S/ {preview.net_price} · Margen teórico: S/ {preview.margin} · Food cost: {preview.food_cost_percent === null ? "Sin precio de venta" : `${preview.food_cost_percent}%`}</p><button type="button" onClick={() => void submit(true)}>Guardar {initial ? "nueva versión" : "receta"}</button></div>}
    </fieldset></form>
  </section>;
}
