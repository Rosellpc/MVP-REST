import { useState } from "react";
import { Link } from "react-router";
import { request } from "../auth/authApi";
import { useAuth } from "../auth/useAuth";
import { usePolling } from "../production/usePolling";
import { ShiftForm, MovementForm } from "./StockForms";
import { StockHistory, ShiftHistory } from "./StockHistory";
import { dateLabel, type StockData, type StockRow } from "./types";
import "./stock.css";

const loadStock = (signal: AbortSignal): Promise<StockData> => request("stock/", { signal });
const statusLabel = { OUT: "Agotado", LOW: "Stock bajo", AVAILABLE: "Disponible" };
export default function StockPage() {
  const { user } = useAuth();
  const { data, error, loading, refreshing, updatedAt, refresh } = usePolling(loadStock, 10000);
  const [tab, setTab] = useState("stock"); const [search, setSearch] = useState(""); const [status, setStatus] = useState(""); const [station, setStation] = useState(""); const [sort, setSort] = useState("name");
  const [form, setForm] = useState<{ mode: "open" | "close"; data: StockData } | { mode: "movement"; row: StockRow; shiftId: number } | null>(null);
  const [feedback, setFeedback] = useState("");
  const canManage = user?.permissions.includes("stock.manage_stock");
  const active = data?.shift && !data.shift.closed_at;
  const rows = (data?.rows ?? []).filter(row => `${row.name} ${row.sku}`.toLocaleLowerCase().includes(search.toLocaleLowerCase()) && (!status || status === row.status) && (!station || station === row.station)).sort((a, b) => sort === "quantity" ? a.quantity - b.quantity : sort === "sales" ? b.sales - a.sales : a.name.localeCompare(b.name, "es"));
  function done() { setForm(null); setFeedback("Operación registrada correctamente en el historial."); refresh(); }
  return <main className="stock-page"><header className="stock-heading"><div><span className="stock-eyebrow">PRODUCCIÓN · EXISTENCIAS</span><h1>Stock</h1><p>Del inicio del turno al último servicio.</p></div><div className="stock-actions"><Link to="/costing?view=recipes">Ver recetario ↗</Link><button onClick={refresh} disabled={refreshing}>{refreshing ? "Actualizando…" : "Actualizar"}</button></div></header>
    {error && <p className="stock-error" role="alert">{error} Los datos visibles pueden estar desactualizados.</p>}{feedback && <p role="status">{feedback}</p>}
    {loading ? <p role="status">Cargando stock…</p> : data && <><section className="stock-panel stock-shift"><div><strong>{active ? `Turno #${data.shift!.id} abierto` : "Sin turno abierto"}</strong><p>{data.enabled ? active ? "El checkout descuenta las unidades al confirmar el pedido de demostración." : "Venta pausada hasta la apertura del siguiente turno." : "Control aún no activado. Registra las cantidades reales en la primera apertura."}</p><small>Última actualización: {updatedAt?.toLocaleTimeString("es-PE")} · Stock bajo: 1 a 5 unidades.</small></div>{canManage && <button disabled={!!form || refreshing} onClick={() => { setFeedback(""); setForm({ mode: active ? "close" : "open", data }); }}>{active ? "Realizar cierre" : "Abrir turno"}</button>}</section>
    <div className="stock-metrics">{[["Productos", data.summary.products], ["Unidades disponibles", data.summary.quantity], ["Producción", data.summary.production], ["Ventas netas demo", data.summary.sales], ["Agotados", data.summary.out], ["Stock bajo", data.summary.low], ["Mermas", data.summary.waste]].map(([label, value]) => <section className="stock-panel" key={label}><span>{label}</span><strong>{value}</strong></section>)}</div><p className="stock-caption">Cantidades en unidades de venta; no representan insumos ni costos. {active ? "Movimientos del turno actual." : "Movimientos del último turno, si existe."}</p>
    {form ? form.mode === "movement" ? <MovementForm key={`${form.shiftId}-${form.row.product_id}`} row={form.row} shiftId={form.shiftId} onDone={done} onClose={() => setForm(null)} /> : <ShiftForm key={form.mode} mode={form.mode} data={form.data} onDone={done} onClose={() => setForm(null)} /> : <><nav className="stock-actions" aria-label="Vistas de stock">{[["stock", "Existencias"], ["history", "Movimientos"], ["shifts", "Cierres de turno"]].map(([key, label]) => <button key={key} aria-current={tab === key ? "page" : undefined} onClick={() => setTab(key)}>{label}</button>)}</nav>
    {tab === "stock" && <section className="stock-panel"><div className="stock-fields"><label>Buscar producto o SKU<input type="search" value={search} onChange={e => setSearch(e.target.value)} /></label><label>Estado<select value={status} onChange={e => setStatus(e.target.value)}><option value="">Todos</option>{Object.entries(statusLabel).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label><label>Área<select value={station} onChange={e => setStation(e.target.value)}><option value="">Todas</option><option value="KITCHEN">Cocina</option><option value="BAR">Barra</option></select></label><label>Ordenar<select value={sort} onChange={e => setSort(e.target.value)}><option value="name">Nombre</option><option value="quantity">Menor stock</option><option value="sales">Más vendidos</option></select></label></div><div className="stock-table-wrap"><table><thead><tr><th>Producto</th><th>Inicial</th><th>Ingresos</th><th>Ventas netas</th><th>Mermas</th><th>Ajustes</th><th>Actual</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{rows.map(row => <tr key={row.product_id}><th scope="row">{row.name}<small>{row.sku} · {row.category}</small><small>{dateLabel(row.updated_at)}</small></th><td>{row.initial}</td><td>{row.production}</td><td>{row.sales}</td><td>{row.waste}</td><td>{row.adjustments > 0 ? "+" : ""}{row.adjustments}</td><td><strong>{row.quantity}</strong><small>{row.unit}</small></td><td><span className={`stock-badge stock-badge-${row.status.toLowerCase()}`}>{statusLabel[row.status]}</span></td><td>{canManage && active ? <button onClick={() => { setFeedback(""); setForm({ mode: "movement", row, shiftId: data.shift!.id }); }}>Registrar</button> : "—"}</td></tr>)}</tbody></table></div><p>{rows.length} productos · Inicial + ingresos − ventas netas − mermas + ajustes = saldo actual.</p></section>}
    {tab === "history" && <StockHistory products={data.rows} />}{tab === "shifts" && <ShiftHistory />}</>}
    </>}
  </main>;
}
