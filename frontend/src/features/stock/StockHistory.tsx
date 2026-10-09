import { useCallback, useState } from "react";
import { request } from "../auth/authApi";
import { usePolling } from "../production/usePolling";
import { dateLabel, kindLabel, type Movement, type Page, type Shift, type StockRow } from "./types";

export function StockHistory({ products }: { products: StockRow[] }) {
  const [product, setProduct] = useState(""); const [start, setStart] = useState(""); const [end, setEnd] = useState("");
  const query = new URLSearchParams({ ...(product ? { product } : {}), ...(start ? { start } : {}), ...(end ? { end } : {}) }).toString();
  return <section className="stock-panel"><h2>Historial de movimientos</h2><div className="stock-fields"><label>Producto<select value={product} onChange={e => setProduct(e.target.value)}><option value="">Todos, incluidos desactivados</option>{products.map(p => <option key={p.product_id} value={p.product_id}>{p.name} · {p.sku}</option>)}</select></label><label>Desde<input type="date" value={start} onChange={e => setStart(e.target.value)} /></label><label>Hasta<input type="date" value={end} min={start} onChange={e => setEnd(e.target.value)} /></label></div><Movements key={query} query={query} /></section>;
}

function Movements({ query }: { query: string }) {
  const [page, setPage] = useState(1);
  const load = useCallback((signal: AbortSignal): Promise<Page<Movement>> => request(`stock/history/?${query}&page=${page}`, { signal }), [query, page]);
  const { data, error, loading, refreshing } = usePolling(load, 15000);
  return <>{error && <p role="alert">{error}</p>}{loading ? <p>Cargando movimientos…</p> : <><div className="stock-table-wrap"><table><thead><tr><th>Fecha / responsable</th><th>Producto</th><th>Movimiento</th><th>Cantidad</th><th>Variación</th><th>Saldo</th><th>Motivo / pedido</th></tr></thead><tbody>{data?.results.map(row => <tr key={row.id}><td>{dateLabel(row.created_at)}<small>{row.actor} · Turno {row.shift_id}</small></td><td>{row.product}</td><td>{kindLabel[row.kind]}</td><td>{row.quantity}</td><td>{row.delta > 0 ? "+" : ""}{row.delta}</td><td>{row.balance_after}</td><td>{row.reason}{row.order_id && <small>Pedido #{row.order_id}</small>}</td></tr>)}</tbody></table></div>{!data?.results.length && <p>No hay movimientos para estos filtros.</p>}<div className="stock-actions"><button disabled={refreshing || !data?.previous} onClick={() => setPage(p => p - 1)}>Anterior</button><span>Página {page} · {data?.count ?? 0} movimientos</span><button disabled={refreshing || !data?.next} onClick={() => setPage(p => p + 1)}>Siguiente</button></div></>}</>;
}

export function ShiftHistory() {
  const [page, setPage] = useState(1);
  const [detail, setDetail] = useState<{ shift: Shift; rows: StockRow[] } | null>(null);
  const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  const load = useCallback((signal: AbortSignal): Promise<Page<Shift>> => request(`stock/shifts/?page=${page}`, { signal }), [page]);
  const result = usePolling(load, 30000);
  return <section className="stock-panel"><h2>Turnos y conciliaciones</h2>{(error || result.error) && <p role="alert">{error || result.error}</p>}<div className="stock-actions">{result.data?.results.map(shift => <button key={shift.id} disabled={busy} onClick={async () => { setBusy(true); setError(""); try { setDetail(await request(`stock/shifts/${shift.id}/`)); } catch (e) { setError(e instanceof Error ? e.message : "Error al cargar."); } finally { setBusy(false); } }}>Turno #{shift.id} · {dateLabel(shift.opened_at)} · {shift.closed_at ? "Cerrado" : "Abierto"}</button>)}</div><div className="stock-actions"><button disabled={result.refreshing || !result.data?.previous} onClick={() => setPage(p => p - 1)}>Anterior</button><span>Página {page}</span><button disabled={result.refreshing || !result.data?.next} onClick={() => setPage(p => p + 1)}>Siguiente</button></div>
    {detail && <><h3>Turno #{detail.shift.id}</h3><p>Apertura: {detail.shift.opened_by} · {dateLabel(detail.shift.opened_at)}<br />Cierre: {detail.shift.closed_by ?? "Pendiente"} · {detail.shift.closed_at ? dateLabel(detail.shift.closed_at) : "Abierto"}</p><p>Apertura: {detail.shift.opening_notes || "Sin observaciones"}</p><p>Cierre: {detail.shift.notes || "Sin observaciones"}</p><div className="stock-table-wrap"><table><thead><tr><th>Producto</th><th>Inicial</th><th>Ingresos</th><th>Ventas netas</th><th>Mermas</th><th>Teórico al cierre</th><th>Físico</th><th>Diferencia</th><th>Justificación</th></tr></thead><tbody>{detail.rows.map(row => <tr key={row.product_id}><th scope="row">{row.name}<small>{row.sku}</small></th><td>{row.initial}</td><td>{row.production}</td><td>{row.sales}</td><td>{row.waste}</td><td>{row.theoretical ?? "—"}</td><td>{row.counted ?? "—"}</td><td>{row.difference ?? "—"}</td><td>{row.reason || "—"}</td></tr>)}</tbody></table></div></>}
  </section>;
}
