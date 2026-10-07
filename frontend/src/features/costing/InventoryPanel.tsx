import ItemActions from "./ItemActions";
import { useEffect, useState } from "react";
import { csvCell, download, errorText, getCosting, saveCosting } from "./api";

type Line = { id?: number; code: string; family: string; location: string; product: string; unit: string; quantity: string; unit_cost: string; inventory_value?: string };
type CountForm = { establishment: string; department: string; inventory_date: string; employee: string; currency: string; is_example: boolean; notes: string; lines: Line[] };
type Count = CountForm & { id: number; total: string; source_name: string; source_sheet: string };
const blankLine = (): Line => ({ code: "", family: "", location: "", product: "", unit: "", quantity: "0", unit_cost: "0" });
const blank = (): CountForm => ({ establishment: "", department: "", inventory_date: "", employee: "", currency: "PEN", is_example: false, notes: "", lines: [blankLine()] });
const columns = [["code", "Código"], ["family", "Familia"], ["location", "Ubicación"], ["product", "Producto"], ["unit", "Unidad / presentación"], ["quantity", "Cantidad"], ["unit_cost", "Coste unidad"]] as const;

export default function InventoryPanel() {
  const [editLine, setEditLine] = useState<Line | null>(null);
  const [counts, setCounts] = useState<Count[]>([]);
  const [selected, setSelected] = useState<Count | null>(null);
  const [form, setForm] = useState<CountForm>(blank);
  const [editing, setEditing] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [sheet, setSheet] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reload, setReload] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    getCosting("inventory", controller.signal).then(rows => { if (!controller.signal.aborted) setCounts(rows); }).catch(e => { if (!controller.signal.aborted) setError(errorText(e)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [reload]);
  async function store(body: unknown) {
    setBusy(true); setError(""); setNotice("");
    try {
      const data = await saveCosting("inventory", body);
      setSelected(data.inventory); setEditing(false); setForm(blank()); setReload(v => v + 1);
      setNotice(data.created ? `Inventario guardado: ${data.inventory.lines.length} productos.` : "Este archivo ya estaba importado. Se abrió el registro existente.");
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  async function changeLine(line: Line, method: string) {
    if (!selected || !line.id) return;
    setBusy(true); setError("");
    try {
      const updated = await saveCosting(`inventory/${selected.id}/lines/${line.id}`, line, method);
      setSelected(updated); setCounts(current => current.map(count => count.id === updated.id ? updated : count)); setEditLine(null); setNotice("Inventario actualizado; cambio registrado.");
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  function exportCount(count: Count) {
    const rows = [["Establecimiento", count.establishment], ["Departamento", count.department], ["Fecha", count.inventory_date], ["Empleado", count.employee], ["Moneda", count.currency || "No indicada"], ["Tipo", count.is_example ? "Ejemplo" : "Conteo de referencia"], [], [...columns.map(([, label]) => label), "Valor inventario"], ...count.lines.map(line => [...columns.map(([key]) => line[key]), line.inventory_value]), ["TOTAL", count.total]];
    download(`inventario-${count.id}.csv`, "\ufeff" + rows.map(row => row.map(csvCell).join(";")).join("\r\n"), "text/csv;charset=utf-8");
  }
  return <>
    <section className="costing-panel"><h2>Inventario por conteo</h2><p>Registra los campos de la hoja Excel y conserva cada conteo. Los valores no se suman entre conteos ni modifican automáticamente las existencias o los costos de recetas.</p>
      {error && <p role="alert" className="costing-error">{error} <button onClick={() => { setError(""); setReload(v => v + 1); }}>Recargar</button></p>}{notice && <p role="status">{notice}</p>}
      <div className="costing-actions"><button disabled={busy} onClick={() => { setEditing(true); setSelected(null); }}>Nuevo conteo manual</button></div>
      <form onSubmit={e => { e.preventDefault(); if (!file) return; if (file.size > 5000000) { setError("El archivo supera 5 MB."); return; } const data = new FormData(); data.append("file", file); if (sheet.trim()) data.append("sheet", sheet.trim()); void store(data); }}><fieldset disabled={busy}><div className="costing-fields"><label>Importar Excel de inventario<input required type="file" accept=".xlsx" onChange={e => setFile(e.target.files?.[0] ?? null)} /></label><label>Nombre de hoja (opcional)<input maxLength={100} placeholder="Automático si solo hay una hoja con datos" value={sheet} onChange={e => setSheet(e.target.value)} /></label></div><button disabled={!file}>{busy ? "Guardando…" : "Importar plantilla Excel"}</button></fieldset></form>
      <p>Las hojas llamadas «Ejemplo» se identifican como datos de ejemplo. Si el Excel no especifica moneda, se conserva como «No indicada».</p>
    </section>
    {editing && <section className="costing-panel costing-history"><h2>Nuevo conteo</h2><form onSubmit={e => { e.preventDefault(); void store(form); }}><fieldset disabled={busy}>
      <div className="costing-fields">{[["establishment", "Establecimiento"], ["department", "Departamento"], ["employee", "Nombre del empleado"]].map(([key, label]) => <label key={key}>{label}<input required maxLength={key === "department" ? 100 : 160} value={form[key as "establishment"]} onChange={e => setForm({ ...form, [key]: e.target.value })} /></label>)}
      <label>Fecha del inventario<input required type="date" value={form.inventory_date} onChange={e => setForm({ ...form, inventory_date: e.target.value })} /></label><label>Moneda<select value={form.currency} onChange={e => setForm({ ...form, currency: e.target.value })}>{["PEN", "USD", "EUR", "COP"].map(value => <option key={value}>{value}</option>)}</select></label><label>Tipo<select value={String(form.is_example)} onChange={e => setForm({ ...form, is_example: e.target.value === "true" })}><option value="false">Conteo de referencia</option><option value="true">Ejemplo / demostración</option></select></label></div>
      {form.lines.map((line, index) => <div className="costing-line" key={index}><h3>Producto {index + 1}</h3><div className="costing-fields">{columns.map(([key, label]) => <label key={key}>{label}<input required={["product", "unit", "quantity", "unit_cost"].includes(key)} type={key === "quantity" || key === "unit_cost" ? "number" : "text"} min="0" step="0.0001" maxLength={key === "product" ? 250 : key === "code" ? 60 : 100} value={line[key]} onChange={e => setForm({ ...form, lines: form.lines.map((row, i) => i === index ? { ...row, [key]: e.target.value } : row) })} /></label>)}</div><button type="button" disabled={form.lines.length === 1} onClick={() => setForm({ ...form, lines: form.lines.filter((_, i) => i !== index) })}>Quitar producto {index + 1}</button></div>)}
      <label>Observaciones<textarea rows={3} maxLength={5000} value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} /></label><p>El servidor calcula Valor inventario = Cantidad × Coste unidad y el total al guardar.</p>
      <div className="costing-actions"><button type="button" disabled={form.lines.length >= 1000} onClick={() => setForm({ ...form, lines: [...form.lines, blankLine()] })}>Añadir producto</button><button>Guardar conteo</button><button type="button" onClick={() => setEditing(false)}>Cerrar</button></div>
    </fieldset></form></section>}
    <section className="costing-panel costing-history"><h2>Conteos guardados</h2>{loading && <p role="status">Cargando inventarios…</p>}{!loading && !counts.length && <p>Aún no hay inventarios registrados.</p>}<div className="costing-recipe-list">{counts.map(count => <button key={count.id} disabled={busy} onClick={() => { setSelected(count); setEditing(false); setEditLine(null); }}><strong>{count.establishment} · {count.department}</strong><span>{count.inventory_date || "Fecha no indicada"} · {count.lines.length} productos · {count.is_example ? "EJEMPLO" : "Conteo de referencia"}</span></button>)}</div></section>
    {selected && <section className="costing-panel costing-history"><h2>{selected.establishment} · {selected.is_example ? "Inventario de ejemplo" : "Conteo de referencia"}</h2><p>Departamento: {selected.department} · Fecha: {selected.inventory_date || "No indicada"} · Empleado: {selected.employee}</p><p>Moneda: {selected.currency || "No indicada en el archivo"} · {selected.source_name} {selected.source_sheet && ` / ${selected.source_sheet}`}</p><p>{selected.notes}</p><button onClick={() => exportCount(selected)}>Exportar inventario CSV</button>{editLine && <form id="inventory-line-editor" className="costing-line" onSubmit={e => { e.preventDefault(); void changeLine(editLine, "PUT"); }}><h3>Editar {editLine.product}</h3><fieldset disabled={busy}><div className="costing-fields">{columns.map(([key, label]) => <label key={key}>{label}<input required={["product", "unit", "quantity", "unit_cost"].includes(key)} type={key === "quantity" || key === "unit_cost" ? "number" : "text"} min="0" step="0.0001" maxLength={key === "product" ? 250 : key === "code" ? 60 : 100} value={editLine[key]} onChange={e => setEditLine({ ...editLine, [key]: e.target.value })} /></label>)}</div><div className="costing-actions"><button>Guardar cambios</button><button type="button" onClick={() => setEditLine(null)}>Cancelar</button></div></fieldset></form>}<div className="costing-table-wrap"><table className="costing-table"><caption>Detalle del inventario ({selected.lines.length} filas)</caption><thead><tr>{columns.map(([key, label]) => <th key={key} scope="col">{label}</th>)}<th scope="col">Valor inventario</th><th scope="col">Acciones</th></tr></thead><tbody>{selected.lines.map((line, i) => <tr key={i}>{columns.map(([key]) => <td key={key}>{line[key]}</td>)}<td>{line.inventory_value}</td><td><ItemActions name={line.product} disabled={busy} onEdit={() => { setEditLine({ ...line }); requestAnimationFrame(() => document.getElementById("inventory-line-editor")?.scrollIntoView({ block: "center" })); }} onDelete={() => { if (window.confirm(`Eliminar ${line.product} de este inventario? El total se recalculara y se conservara el registro del cambio.`)) void changeLine(line, "DELETE"); }} /></td></tr>)}</tbody><tfoot><tr><th colSpan={7} scope="row">Total</th><td>{selected.total}</td><td /></tr></tfoot></table></div></section>}
  </>;
}
