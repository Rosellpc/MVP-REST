import { useState } from "react";
import { download, errorText, saveCosting } from "./api";
import type { Ingredient, Version } from "./types";

export default function RecipeImport({ ingredients, recipes, refresh }: { ingredients: Ingredient[]; recipes: Version[]; refresh: () => void }) {
  const [source, setSource] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const template = { recipes: [{ name: "Mi receta", category: "Fondos", portions: 4, portion_size: "250 g", preparation_minutes: 15, cooking_minutes: 20, temperature: "Caliente", preparation: "Describe los pasos", presentation: "Describe el montaje", allergens: "Pendiente de revisar", selling_price: "0.00", tax_percent: "0.00", lines: [{ ingredient_name: ingredients[0]?.name ?? "Nombre exacto del insumo registrado", quantity: "1", unit: ingredients[0]?.purchase_unit ?? "kg", basis: "usable" }] }] };
  return <details className="costing-panel costing-history costing-no-print"><summary>Importar / exportar recetario JSON</summary><p>Hasta 100 recetas por archivo. Usa los nombres de insumos ya registrados. Se valida todo el lote antes de guardar; no se sobrescriben recetas existentes.</p><div className="costing-actions"><button onClick={() => download("plantilla-recetario.json", JSON.stringify(template, null, 2))}>Descargar plantilla JSON</button><button disabled={!recipes.length} onClick={() => download("recetario.json", JSON.stringify({ recipes: recipes.map(({ snapshot }) => ({ ...snapshot, lines: snapshot.lines.map(line => ({ ingredient_name: line.name, quantity: line.quantity, unit: line.unit, basis: line.basis })) })) }, null, 2))}>Exportar recetario JSON</button></div>
    <p>Al importar se calculan los costos con los precios actuales. Los totales incluidos en archivos se ignoran.</p>
    {error && <p role="alert" className="costing-error">{error}</p>}{notice && <p role="status">{notice}</p>}
    <label>Archivo JSON<input type="file" accept=".json,application/json" disabled={busy} onChange={async e => { const file = e.target.files?.[0]; if (!file) return; setError(""); setNotice(""); try { if (file.size > 2000000) throw new Error("Máximo 2 MB."); setSource(await file.text()); } catch (err) { setError(errorText(err)); } }} /></label><label>Contenido JSON<textarea disabled={busy} rows={9} value={source} onChange={e => setSource(e.target.value)} /></label>
    <button disabled={busy || !source.trim()} onClick={async () => { setBusy(true); setError(""); setNotice(""); try { if (source.length > 2000000) throw new Error("Máximo 2 MB."); const data = await saveCosting("recipes/import", JSON.parse(source)); setNotice(`${data.imported} recetas importadas como versión 1.`); setSource(""); refresh(); } catch (err) { setError(errorText(err)); } finally { setBusy(false); } }}>{busy ? "Importando…" : "Validar e importar recetas"}</button>
  </details>;
}
