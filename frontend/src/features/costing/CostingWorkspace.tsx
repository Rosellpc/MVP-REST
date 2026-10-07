import ItemActions from "./ItemActions";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import { csvCell, download, errorText, getCosting, saveCosting } from "./api";
import type { Ingredient, Version } from "./types";
import RecipeEditor from "./RecipeEditor";
import RecipeSheet from "./RecipeSheet";
import IngredientsPanel from "./IngredientsPanel";
import InventoryPanel from "./InventoryPanel";
import RecipeImport from "./RecipeImport";
import CostingOverview from "./CostingOverview";
import CostingIcon from "./CostingIcon";
import RecipeWorkbookPanel from "./RecipeWorkbookPanel";

type Summary = { ingredients: number; recipes: number; versions: number; priced_recipes: number; average_food_cost: string | null };
type LegacyStudy = { id: number; name: string; created_at: string; snapshot: { total: string; per_portion: string } };
export default function CostingWorkspace() {
  const [params, setParams] = useSearchParams();
  const tab = params.get("view") || "summary";
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [recipes, setRecipes] = useState<Version[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [legacy, setLegacy] = useState<LegacyStudy[]>([]);
  const [reload, setReload] = useState(0);
  const [error, setError] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [editor, setEditor] = useState<Version | "new" | null>(null);
  const [versions, setVersions] = useState<Version[]>([]);
  const [selected, setSelected] = useState<Version | null>(null);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [opening, setOpening] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    Promise.all(["ingredients", "recipes", "summary", "studies"].map(path => getCosting(path, controller.signal)))
      .then(([items, rows, metrics, old]) => { if (!controller.signal.aborted) { setIngredients(items); setRecipes(rows); setSummary(metrics); setLegacy(old); setLoaded(true); setError(""); } })
      .catch(e => { if (!controller.signal.aborted) setError(errorText(e)); });
    return () => controller.abort();
  }, [reload]);
  const refresh = () => setReload(value => value + 1);
  const filtered = recipes.filter(row => row.snapshot.name.toLowerCase().includes(search.toLowerCase()) && (!category || row.snapshot.category === category));
  async function open(recipe: Version) {
    setOpening(true); setError("");
    try { const rows = await getCosting(`recipes/${recipe.recipe_id}`); setVersions(rows); setSelected(rows[0]); setEditor(null); } catch (e) { setError(errorText(e)); } finally { setOpening(false); }
  }
  return <>
    <div className="costing-page-intro costing-no-print"><span className="costing-eyebrow">{tab === "summary" ? "CONTROL DE COSTOS" : tab === "recipes" ? "ARCHIVO DE COCINA" : tab === "ingredients" ? "REFERENCIAS DE COMPRA" : "CONTROL DE INVENTARIO"}</span><h1>{tab === "summary" ? "Tu cocina, en cifras." : tab === "recipes" ? "Recetario" : tab === "ingredients" ? "Insumos" : "Inventario"}</h1></div>
    <p className="costing-note costing-no-print">{tab === "inventory" ? "Conteos independientes. La moneda y las presentaciones se conservan según cada registro." : "PEN · Costos teóricos de insumos. Los cambios de precios se aplican al calcular nuevas versiones; las fichas guardadas conservan su costo histórico."}</p>
    {error && <p className="costing-error" role="alert">{error} <button onClick={refresh}>Reintentar carga</button></p>}
    {!loaded ? <p role="status">{error ? "No se pudieron cargar los datos." : "Cargando laboratorio…"}</p> : <>
      {tab === "summary" && <><div className="costing-metrics">{[["Insumos", summary?.ingredients], ["Recetas", summary?.recipes], ["Versiones guardadas", summary?.versions], ["Food cost promedio", summary?.average_food_cost ? `${summary.average_food_cost}%` : "Sin datos"]].map(([label, value]) => <section key={label} className="costing-panel"><div className="costing-metric-label"><h2>{label}</h2><CostingIcon name={label === "Insumos" ? "ingredients" : "recipes"} /></div><strong>{value}</strong><small>Referencias del laboratorio</small></section>)}</div><p>Promedio simple de {summary?.priced_recipes} recetas con precio de venta, basado en su última versión guardada. No está ponderado por ventas.</p><CostingOverview recipes={recipes} onOpen={row => { setParams({ view: "recipes" }); void open(row); }} onIngredients={() => setParams({ view: "ingredients" })} />
      <section className="costing-panel costing-history"><h2>Cálculos de la primera etapa</h2><p>Se conservan los últimos 100 estudios independientes anteriores al recetario.</p>{legacy.map(study => <details key={study.id}><summary>{study.name} · S/ {study.snapshot.per_portion} por porción</summary><p>Total: S/ {study.snapshot.total} · {new Date(study.created_at).toLocaleString("es-PE")}</p><button onClick={() => download(`estudio-${study.id}.json`, JSON.stringify(study, null, 2))}>Descargar estudio completo</button></details>)}</section></>}
      {tab === "ingredients" && <IngredientsPanel ingredients={ingredients} refresh={refresh} />}
      {tab === "inventory" && <InventoryPanel />}
      {tab === "recipes" && <><div className="costing-actions costing-no-print"><button onClick={() => { setEditor("new"); setSelected(null); }}>Nueva receta</button><button disabled={!filtered.length} onClick={() => download("recetario.csv", "\ufeff" + [["Receta", "Categoría", "Versión", "Costo total PEN", "Costo por porción PEN", "Precio final PEN", "Margen teórico PEN"], ...filtered.map(row => [row.snapshot.name, row.snapshot.category, row.number, row.snapshot.total, row.snapshot.per_portion, row.snapshot.selling_price, row.snapshot.margin])].map(row => row.map(csvCell).join(";")).join("\r\n"), "text/csv;charset=utf-8")}>Exportar listado CSV (Excel)</button></div>
        {editor ? <RecipeEditor key={editor === "new" ? "new" : editor.id} ingredients={ingredients} initial={editor === "new" ? undefined : editor} onClose={() => setEditor(null)} onSaved={() => { setEditor(null); setSelected(null); refresh(); }} /> : <>
          {!selected && <><div className="costing-fields costing-no-print"><label>Buscar receta<input type="search" value={search} onChange={e => setSearch(e.target.value)} /></label><label>Categoría<select value={category} onChange={e => setCategory(e.target.value)}><option value="">Todas</option>{[...new Set(recipes.map(row => row.snapshot.category).filter(Boolean))].sort().map(value => <option key={value}>{value}</option>)}</select></label></div>
          <div className="costing-recipe-table costing-no-print"><div className="costing-recipe-table-head"><span>Plato / versión</span><span>Categoría</span><span>Costo / porción</span><span>Precio final</span><span>Food cost</span><span>Acciones</span></div>{filtered.map(row => <div className="costing-recipe-row" key={row.id}><button className="costing-recipe-name" disabled={opening} onClick={() => void open(row)}><strong>{row.snapshot.name}</strong><small>v{row.number} · {row.snapshot.portions} porciones</small></button><span className="costing-row-category">{row.snapshot.category || "Sin categoría"}</span><span><small className="costing-mobile-label">Costo / porción</small>S/ {row.snapshot.per_portion}</span><span><small className="costing-mobile-label">Precio final</small>S/ {row.snapshot.selling_price}</span><span><small className="costing-mobile-label">Food cost</small><span className="costing-food-tag">{row.snapshot.food_cost_percent === null ? "Sin precio" : `${row.snapshot.food_cost_percent}%`}</span></span><ItemActions name={row.snapshot.name} disabled={opening} onEdit={() => { setEditor(row); setSelected(null); }} onDelete={async () => { if (!window.confirm(`Eliminar ${row.snapshot.name} del recetario? Sus versiones historicas se conservaran.`)) return; setOpening(true); setError(""); try { await saveCosting(`recipes/${row.recipe_id}`, {}, "DELETE"); setRecipes(current => current.filter(item => item.recipe_id !== row.recipe_id)); setSelected(null); refresh(); } catch (e) { setError(errorText(e)); } finally { setOpening(false); } }} /></div>)}<div className="costing-list-count">{filtered.length} recetas</div></div>{!filtered.length && <p>No hay recetas para mostrar. Crea tu primera ficha técnica.</p>}
          </>}
          {selected && <><div className="costing-actions costing-no-print"><button onClick={() => setSelected(null)}>Volver al recetario</button><label>Versión histórica<select value={selected.id} onChange={e => setSelected(versions.find(row => row.id === Number(e.target.value)) ?? null)}>{versions.map(row => <option key={row.id} value={row.id}>v{row.number} · {new Date(row.created_at).toLocaleString("es-PE")}</option>)}</select></label><button onClick={() => setEditor(versions[0])}>Editar última versión / recalcular</button></div><RecipeSheet version={selected} /></>}
          {tab === "recipes" && <RecipeImport ingredients={ingredients} recipes={recipes} refresh={refresh} />}
      {tab === "recipes" && <RecipeWorkbookPanel refresh={refresh} />}
    </>}
      </>}
    </>}
  </>;
}
