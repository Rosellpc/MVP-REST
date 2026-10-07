import { useEffect, useState } from "react";
import { download, errorText, getCosting, saveCosting } from "./api";
type Report = { ingredients_created: number; ingredients_reused: number; recipes_created: number; pending: { type: string; name: string; reason: string }[]; warnings: string[] };
type Batch = { id: number; filename: string; report: Report };
export default function RecipeWorkbookPanel({ refresh }: { refresh: () => void }) {
  const [batches, setBatches] = useState<Batch[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);
  useEffect(() => { const controller = new AbortController(); getCosting("recipes/workbook", controller.signal).then(setBatches).catch(e => { if (!controller.signal.aborted) setError(errorText(e)); }); return () => controller.abort(); }, [reload]);
  return <details className="costing-panel costing-history costing-no-print"><summary>Excel de costeo e informes de importación ({batches.length})</summary><p>Admite la plantilla costos-recetas.xlsx con «Lista de Ingredientes» y hojas «Receta». Crea referencias nuevas y conserva el origen. Los insumos conflictivos y las recetas incompletas quedan en el informe; no se sobrescriben registros existentes.</p><p>Se recalculan merma e impuesto incluido. Las cantidades se interpretan como aprovechables y deben revisarse antes de uso operativo.</p>
    {error && <p role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}
    <form onSubmit={async e => { e.preventDefault(); if (!file) return; setBusy(true); setError(""); try { if (file.size > 10000000) throw new Error("Máximo 10 MB."); const body = new FormData(); body.append("file", file); const data = await saveCosting("recipes/workbook", body); setNotice(data.created ? `Importadas ${data.report.recipes_created} recetas; ${data.report.pending.length} pendientes.` : "El archivo ya estaba importado; no se duplicaron registros."); setReload(v => v + 1); refresh(); } catch (err) { setError(errorText(err)); } finally { setBusy(false); } }}><label>Excel del recetario<input type="file" required accept=".xlsx" disabled={busy} onChange={e => setFile(e.target.files?.[0] ?? null)} /></label><button disabled={busy || !file}>{busy ? "Importando…" : "Importar Excel"}</button></form>
    {batches.map(batch => <section key={batch.id}><h3>{batch.filename}</h3><p>{batch.report.ingredients_created} insumos nuevos · {batch.report.recipes_created} recetas · {batch.report.pending.length} pendientes</p><ul>{batch.report.pending.map((row, i) => <li key={i}>{row.name}: {row.reason}</li>)}</ul><button onClick={() => download(`informe-recetario-${batch.id}.json`, JSON.stringify(batch, null, 2))}>Descargar informe</button></section>)}
  </details>;
}
