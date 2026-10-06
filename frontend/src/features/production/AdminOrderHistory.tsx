import { Fragment, useCallback, useState } from "react";
import { AuthError, post, request } from "../auth/authApi";
import { useAuth } from "../auth/useAuth";
import { usePolling } from "./usePolling";
import "../../styles/staff-operations.css";

type Order = {
  id: number; public_code: string; production_status: string; created_at: string;
  fulfillment: string; table_label: string; total: string; currency: string;
  items: { product_id: number; name: string; quantity: number; line_total: string }[];
  tickets: { id: number; station_code: string; status: string; created_at: string; started_at: string | null; completed_at: string | null; cancelled_at: string | null; archived_at: string | null }[];
  cancellation_request: { reason: string; requested_by: string; station: string; created_at: string; approved_at: string | null; rejected_at: string | null; rejection_reason: string } | null;
};
type Page = { count: number; next: string | null; previous: string | null; results: Order[] };
const labels: Record<string, string> = { ALL: "Todos", PENDING: "Pendientes", IN_PROGRESS: "En preparación", READY: "Listos", CANCELLED: "Cancelados" };
const date = (value: string) => new Date(value).toLocaleString("es-PE");

function OrderDetail({ order, refresh }: { order: Order; refresh: () => void }) {
  const { user } = useAuth();
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const cancellation = order.cancellation_request;
  const waiting = cancellation && !cancellation.approved_at && !cancellation.rejected_at;
  async function decide(action: "cancel" | "reject-cancellation") {
    if (busy) return;
    setBusy(true); setError("");
    try { await post(`staff/orders/${order.id}/${action}/`, { reason }); refresh(); }
    catch (err) { setError(err instanceof Error ? err.message : "No se pudo guardar la decisión."); refresh(); }
    finally { setBusy(false); }
  }
  return <div className="order-detail-grid">
    <section><h3>Productos</h3><ul>{order.items.map(item => <li key={item.product_id}>{item.quantity} × {item.name} · {order.currency} {item.line_total}</li>)}</ul><p className="ticket-code">Referencia: {order.public_code}</p><p>Pago simulado</p></section>
    <section><h3>Historial por estación</h3>{order.tickets.map(ticket => <div key={ticket.id}><strong>{ticket.station_code === "KITCHEN" ? "Cocina" : "Barra"} · {labels[ticket.status] ?? ticket.status}</strong><ul>{([
      ["Recibido", ticket.created_at], ["Iniciado", ticket.started_at], ["Listo", ticket.completed_at], ["Cancelado", ticket.cancelled_at], ["Archivado", ticket.archived_at],
    ] as const).map(([label, timestamp]) => timestamp && <li key={label}>{label}: {date(timestamp)}</li>)}</ul></div>)}</section>
    {cancellation && <section className="cancellation-review"><h3>{waiting ? "Solicitud por revisar" : cancellation.rejected_at ? "Solicitud rechazada" : "Cancelación aprobada"}</h3><p>{cancellation.reason}</p><p>{cancellation.requested_by} · {cancellation.station} · {date(cancellation.created_at)}</p>
      {cancellation.rejected_at && <p>Motivo del rechazo: {cancellation.rejection_reason}</p>}
      {waiting && user?.is_superuser && <><label>Motivo para rechazar y reanudar<input maxLength={500} value={reason} disabled={busy} onChange={event => setReason(event.target.value)} /></label><div className="review-actions"><button className="action-danger" disabled={busy} onClick={() => void decide("cancel")}>Aprobar cancelación</button><button disabled={busy || !reason.trim()} onClick={() => void decide("reject-cancellation")}>Rechazar y reanudar</button></div></>}
      {waiting && !user?.is_superuser && <p>La decisión requiere una cuenta de superusuario.</p>}
      {error && <p role="alert">{error}</p>}
    </section>}
  </div>;
}

function OrderTable({ filter, mode, page, setPage, onChange }: { filter: string; mode: string; page: number; setPage: (page: number) => void; onChange: () => void }) {
  const { refresh: refreshSession } = useAuth();
  const [expanded, setExpanded] = useState<number | null>(null);
  const load = useCallback(async (signal: AbortSignal): Promise<Page> => {
    const query = new URLSearchParams({ page: String(page) });
    if (mode === "requests") query.set("pending_cancellation", "true");
    else if (filter !== "ALL") query.set("status", filter);
    try { return await request(`staff/orders/?${query}`, { signal }); }
    catch (err) { if (err instanceof AuthError && [401, 403].includes(err.status)) void refreshSession(); throw err; }
  }, [filter, mode, page, refreshSession]);
  const { data, loading, error, updatedAt, refresh } = usePolling(load, mode === "requests" ? 5000 : 15000);
  const refreshAll = () => { if (mode === "requests" && page > 1) setPage(1); else refresh(); onChange(); };
  return <section>
    <div className="production-toolbar"><h2>{mode === "requests" ? "Órdenes por cancelar" : "Historial de pedidos"}</h2><button onClick={refreshAll}>Actualizar</button></div>
    <p role="status">{loading ? "Cargando…" : error ? "No se pudo actualizar. Los datos visibles pueden estar desactualizados." : `Actualizado: ${updatedAt?.toLocaleTimeString()}`}</p>
    {error && <p role="alert">{error}</p>}
    {data && <><div className="history-table-wrap"><table className="history-table"><caption>{data.count} pedidos encontrados</caption><thead><tr><th>Pedido</th><th>Fecha</th><th>Modalidad</th><th>Estado</th><th>Total</th><th>Detalle</th></tr></thead><tbody>
      {data.results.map(order => <Fragment key={order.id}><tr>
        <td data-label="Pedido"><strong>#{order.id}</strong></td><td data-label="Fecha">{date(order.created_at)}</td><td data-label="Modalidad">{order.fulfillment === "DINE_IN" ? `Mesa ${order.table_label}` : "Recojo"}</td>
        <td data-label="Estado"><span className={`state-badge state-${order.production_status}`}>{labels[order.production_status] ?? "Registrado"}</span>{order.cancellation_request && !order.cancellation_request.approved_at && !order.cancellation_request.rejected_at && <span className="state-badge state-CANCELLED">Cancelación por revisar</span>}</td>
        <td data-label="Total">{order.currency} {order.total}</td><td><button aria-expanded={expanded === order.id} aria-controls={`order-detail-${order.id}`} onClick={() => setExpanded(expanded === order.id ? null : order.id)}>{expanded === order.id ? "Ocultar" : "Ver detalle"}</button></td>
      </tr>{expanded === order.id && <tr className="history-detail-row"><td colSpan={6} id={`order-detail-${order.id}`}><OrderDetail order={order} refresh={refreshAll} /></td></tr>}</Fragment>)}
    </tbody></table></div>{data.results.length === 0 && <p>No hay pedidos para esta selección.</p>}
    <nav className="history-pagination" aria-label="Páginas del historial"><button disabled={!data.previous} onClick={() => setPage(page - 1)}>Anterior</button><span>Página {page}</span><button disabled={!data.next} onClick={() => setPage(page + 1)}>Siguiente</button></nav></>}
  </section>;
}

export default function AdminOrderHistory() {
  const [filter, setFilter] = useState("ALL");
  const [mode, setMode] = useState("history");
  const [page, setPage] = useState(1);
  const loadCounts = useCallback((signal: AbortSignal): Promise<Record<string, number>> => request("staff/orders/counts/", { signal }), []);
  const counts = usePolling(loadCounts);
  return <main className="staff-content staff-history"><h1>Administración · Pedidos</h1>
    <div className="admin-controls"><div className="admin-filter-row" role="group" aria-label="Filtrar historial">{Object.entries(labels).map(([value, label]) => <button key={value} aria-pressed={mode === "history" && filter === value} onClick={() => { setFilter(value); setMode("history"); setPage(1); }}>{label} <span>({counts.data?.[value] ?? "—"})</span></button>)}</div>
    <section className="admin-management-row"><button aria-pressed={mode === "requests"} onClick={() => { setMode("requests"); setPage(1); }}>Órdenes por cancelar ({counts.data?.requests ?? "—"})</button><p>Revisa el motivo. Solo un superusuario puede aprobar o rechazar.</p></section></div>
    {counts.error && <p role="alert">No se pudieron actualizar los contadores.</p>}
    <OrderTable key={`${mode}-${filter}-${page}`} filter={filter} mode={mode} page={page} setPage={setPage} onChange={counts.refresh} />
  </main>;
}
