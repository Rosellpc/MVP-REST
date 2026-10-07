import ItemActions from "./ItemActions";
import { useState } from "react";
import { download, errorText, getCosting, saveCosting } from "./api";
import { units, type Ingredient } from "./types";
const blank = { name: "", purchase_unit: "kg", purchase_quantity: "1", purchase_price: "", yield_percent: "100" };
type History = { snapshot: Ingredient; reason: string; author: string; created_at: string };
export default function IngredientsPanel({ ingredients, refresh }: { ingredients: Ingredient[]; refresh: () => void }) {
  const [showEditor, setShowEditor] = useState(false);
  const [form, setForm] = useState(blank);
  const [editing, setEditing] = useState<number | null>(null);
  const [reason, setReason] = useState("");
  const [history, setHistory] = useState<History[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [source, setSource] = useState("");
  const [search, setSearch] = useState("");
  async function act(action: () => Promise<void>) { setBusy(true); setError(""); setNotice(""); try { await action(); } catch (e) { setError(errorText(e)); } finally { setBusy(false); } }
  const filtered = ingredients.filter(item => item.name.toLowerCase().includes(search.toLowerCase()));
  return <div className="costing-ingredients-section">
    <section className="costing-panel"><div className="costing-ingredients-heading"><div><span className="costing-eyebrow">REFERENCIAS DE COMPRA</span><h2>Gestiona tus insumos</h2><p>Consulta precios y rendimientos, registra productos y revisa su historial.</p></div><button disabled={busy} onClick={() => { setEditing(null); setForm(blank); setReason(""); setHistory([]); setShowEditor(true); }}>Nuevo insumo</button></div></section>
    {error && <p role="alert" className="costing-error">{error}</p>}{notice && <p role="status">{notice}</p>}
    {showEditor && <section id="ingredient-editor" className="costing-panel"><h2>{editing ? "Editar insumo" : "Nuevo insumo"}</h2><p>Precio total de compra en PEN. Rendimiento: porcentaje aprovechable tras la merma.</p>

    <form onSubmit={e => { e.preventDefault(); void act(async () => { await saveCosting(editing ? `ingredients/${editing}` : "ingredients", { ...form, reason }, editing ? "PUT" : "POST"); setEditing(null); setForm(blank); setReason(""); setHistory([]); setShowEditor(false); setNotice("Insumo guardado. Los costos de versiones anteriores se conservan."); refresh(); }); }}><fieldset disabled={busy}>
      <label>Nombre<input required maxLength={160} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></label>
      <div className="costing-fields"><label>Cantidad comprada<input required type="number" min="0.001" step="0.001" value={form.purchase_quantity} onChange={e => setForm({ ...form, purchase_quantity: e.target.value })} /></label><label>Unidad<select value={form.purchase_unit} onChange={e => setForm({ ...form, purchase_unit: e.target.value })}>{units.map(unit => <option key={unit}>{unit}</option>)}</select></label>
      <label>Precio total (S/)<input required type="number" min="0" step="0.0001" value={form.purchase_price} onChange={e => setForm({ ...form, purchase_price: e.target.value })} /></label><label>Rendimiento (%)<input required type="number" min="0.001" max="100" step="0.001" value={form.yield_percent} onChange={e => setForm({ ...form, yield_percent: e.target.value })} /></label></div>
      {editing && <label>Motivo del cambio<input required maxLength={250} value={reason} onChange={e => setReason(e.target.value)} /></label>}
      <div className="costing-actions"><button>Guardar insumo</button><button type="button" onClick={() => { setEditing(null); setForm(blank); setHistory([]); setShowEditor(false); }}>Cancelar</button></div>
    </fieldset></form>
    {editing && <div className="costing-history"><h3>Historial de referencias</h3>{!history.length && <p>Aún no hay cambios registrados.</p>}{history.map((row, i) => <p key={i}>{new Date(row.created_at).toLocaleString("es-PE")} · {row.author}<br />S/ {row.snapshot.purchase_price} / {row.snapshot.purchase_quantity} {row.snapshot.purchase_unit} · {row.snapshot.yield_percent}% aprovechable<br />{row.reason}</p>)}</div>}
  </section>}<section className="costing-panel"><h2>Insumos ({ingredients.length})</h2><label>Buscar<input type="search" value={search} onChange={e => setSearch(e.target.value)} /></label><div className="costing-table-wrap"><table className="costing-table"><caption>{filtered.length} insumos encontrados</caption><thead><tr><th scope="col">Insumo</th><th scope="col">Cantidad comprada</th><th scope="col">Unidad</th><th scope="col">Precio total (S/)</th><th scope="col">Rendimiento</th><th scope="col">Acciones</th></tr></thead><tbody>{filtered.map(item => <tr key={item.id}><th scope="row">{item.name}</th><td>{item.purchase_quantity}</td><td>{item.purchase_unit}</td><td>{item.purchase_price}</td><td>{item.yield_percent}%</td><td><ItemActions name={item.name} disabled={busy} onEdit={() => void act(async () => { const data = await getCosting(`ingredients/${item.id}`); setEditing(item.id); setForm(data.ingredient); setReason(""); setHistory(data.history); setShowEditor(true); requestAnimationFrame(() => document.getElementById("ingredient-editor")?.scrollIntoView({ block: "start" })); })} onDelete={() => { if (window.confirm(`Eliminar ${item.name} del listado? Se conservaran los costos historicos. Para volver a usarlo en una receta tendras que sustituirlo por un insumo activo.`)) void act(async () => { await saveCosting(`ingredients/${item.id}`, {}, "DELETE"); if (editing === item.id) { setShowEditor(false); setEditing(null); setForm(blank); setHistory([]); } setNotice("Insumo eliminado del listado."); refresh(); }); }} /></td></tr>)}</tbody></table></div>{!filtered.length && <p>{ingredients.length ? "No hay coincidencias con tu búsqueda." : "Aún no hay insumos. Registra el primero con Nuevo insumo."}</p>}</section>
    <details className="costing-panel"><summary>Importar / exportar insumos</summary><p>JSON con una lista «ingredients». Máximo 500 registros. Se valida todo el lote antes de guardarlo; los duplicados se rechazan.</p>
    <button onClick={() => download("insumos.json", JSON.stringify({ ingredients: ingredients.length ? ingredients.map(({ name, purchase_unit, purchase_quantity, purchase_price, yield_percent }) => ({ name, purchase_unit, purchase_quantity, purchase_price, yield_percent })) : [{ ...blank, name: "Insumo de ejemplo", purchase_price: "20" }] }, null, 2))}>{ingredients.length ? "Exportar insumos JSON" : "Descargar plantilla JSON"}</button>
    <label>Archivo JSON<input type="file" accept=".json,application/json" disabled={busy} onChange={e => { const file = e.target.files?.[0]; if (file) void act(async () => { if (file.size > 2000000) throw new Error("Máximo 2 MB."); setSource(await file.text()); }); }} /></label>
    <label>Contenido para importar<textarea rows={7} value={source} onChange={e => setSource(e.target.value)} /></label><button disabled={busy || !source.trim()} onClick={() => void act(async () => { if (source.length > 2000000) throw new Error("Máximo 2 MB."); const data = await saveCosting("import", JSON.parse(source)); setSource(""); setNotice(`${data.imported} insumos importados.`); refresh(); })}>Validar e importar</button>
  </details></div>;
}
