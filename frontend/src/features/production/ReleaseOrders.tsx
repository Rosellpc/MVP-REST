import { useCallback, useState } from "react";
import { request, post, AuthError } from "../auth/authApi";
import { useAuth } from "../auth/useAuth";
import { usePolling } from "./usePolling";

type StaffOrder = {
  cancellation_request: { reason: string; requested_by: string; station: string; created_at: string; approved_at: string | null } | null;
  id: number; public_code: string; production_status: string; table_label: string; fulfillment: string;
  created_at: string; released_at: string | null; total: string; currency: string;
  items: { product_id: number; name: string; quantity: number; line_total: string }[];
  tickets: { id: number; station_code: string; status: string; started_at: string | null; completed_at: string | null; cancelled_at: string | null; archived_at: string | null }[];
};

const statusLabels: Record<string, string> = { PENDING: "Pendientes", IN_PROGRESS: "En preparación", READY: "Listos", CANCELLED: "Cancelados" };
const dateLabel = (value: string) => new Date(value).toLocaleString("es-PE");

function ReleaseCard({ order, refresh, direct = false }: { order: StaffOrder; refresh: () => void; direct?: boolean }) {
  const { user } = useAuth();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [reason, setReason] = useState("");
  const waiting = Boolean(order.cancellation_request && !order.cancellation_request.approved_at);
  const canDirect = direct && !order.cancellation_request && ["PENDING", "IN_PROGRESS"].includes(order.production_status);
  return <article className="ticket-card"><h2>Pedido #{order.id}</h2><p className="ticket-code">{order.public_code}</p><p>{order.fulfillment === "DINE_IN" ? `Mesa ${order.table_label}` : "Para recoger"}</p>
    <p><strong>{statusLabels[order.production_status] ?? "Registrado"}</strong> · {dateLabel(order.created_at)}</p>
    <p>Total: {order.currency} {order.total} · Pago simulado</p>
    <details><summary>Ver detalle e historial</summary>
      <ul>{order.items.map(item => <li key={item.product_id}>{item.quantity} × {item.name} — {order.currency} {item.line_total}</li>)}</ul>
      <p>Registrado: {dateLabel(order.created_at)}</p>
      {order.released_at && <p>Enviado a preparación: {dateLabel(order.released_at)}</p>}
      {order.tickets.map(ticket => <section key={ticket.id} aria-label={`Ticket ${ticket.id}`}>
        <h3>{ticket.station_code === "KITCHEN" ? "Cocina" : "Barra"} · #{ticket.id}</h3>
        <p>{ticket.status === "CANCELLED" ? "Cancelado por el administrador" : ticket.archived_at ? "Finalizado y archivado" : statusLabels[ticket.status]}</p>
        <ul>{([
          ["Preparación iniciada", ticket.started_at], ["Listo", ticket.completed_at],
          ["Cancelado", ticket.cancelled_at], ["Finalizado", ticket.archived_at],
        ] as const).filter(([, date]) => date).map(([label, date]) => <li key={label}>{label}: {dateLabel(date!)}</li>)}</ul>
      </section>)}
    </details>
    {error && <p role="alert">{error}</p>}
    {order.cancellation_request && <section className="order-progress"><h3>{order.cancellation_request.approved_at ? "Cancelación aprobada" : "Solicitud de cancelación"}</h3><p>{order.cancellation_request.reason}</p><p>Solicitada por {order.cancellation_request.requested_by} · {order.cancellation_request.station} · {dateLabel(order.cancellation_request.created_at)}</p></section>}
    {canDirect && user?.is_superuser && <label className="direct-cancel-reason">Motivo de cancelación<input value={reason} maxLength={500} onChange={event => setReason(event.target.value)} disabled={pending} /></label>}
    {(waiting || canDirect) && user?.is_superuser && <button disabled={pending || (canDirect && !reason.trim())} onClick={async () => {
      if (pending) return;
      setPending(true); setError("");
      try { await post(`staff/orders/${order.id}/cancel/`, canDirect ? { reason } : {}); refresh(); }
      catch (err) { setError(err instanceof Error ? err.message : "No se pudo cancelar el pedido."); refresh(); }
      finally { setPending(false); }
    }}>{pending ? "Cancelando…" : waiting ? "Cancelar pedido y aprobar solicitud" : "Confirmar cancelación de la orden"}</button>}
    {order.cancellation_request && !order.cancellation_request.approved_at && !user?.is_superuser && <p>Solo un superusuario puede aprobar esta cancelación.</p>}
  </article>;
}

export default function ReleaseOrders() {
  const [filter, setFilter] = useState("ALL");
  const [mode, setMode] = useState<"history" | "requests">("history");
  const { user, refresh: refreshSession } = useAuth();
  const load = useCallback(async (signal: AbortSignal): Promise<StaffOrder[]> => {
    const orders: StaffOrder[] = [];
    let path: string | null = "staff/orders/";
    try {
      while (path) {
        const page = await request(path, { signal });
        orders.push(...page.results);
        path = page.next ? `staff/orders/${new URL(page.next, window.location.origin).search}` : null;
      }
      return orders.sort((a, b) => Number(Boolean(b.cancellation_request && !b.cancellation_request.approved_at)) - Number(Boolean(a.cancellation_request && !a.cancellation_request.approved_at)));
    } catch (err) {
      if (err instanceof AuthError && [401, 403].includes(err.status)) void refreshSession();
      throw err;
    }
  }, [refreshSession]);
  const { data, error, loading, refresh } = usePolling(load);
  const requests = data?.filter(order => order.cancellation_request && !order.cancellation_request.approved_at) ?? [];
  const visible = mode === "requests" ? requests : data?.filter(order => filter === "ALL" || order.production_status === filter) ?? [];
  return <main className="staff-content"><h1>Administración · Pedidos</h1><p className="demo-notice">Los pedidos se envían automáticamente a preparación de demostración. Solo un superusuario puede aprobar las solicitudes de cancelación.</p>
    {loading && <p role="status">Cargando pedidos…</p>}{error && <p role="alert">{error}</p>}<button onClick={refresh}>Actualizar</button>
    <div className="admin-controls">
      <div className="admin-filter-row" role="group" aria-label="Filtros por estado">
        {Object.entries({ ALL: "Todos", ...statusLabels }).map(([value, label]) => <button key={value} aria-pressed={mode === "history" && filter === value} onClick={() => { setFilter(value); setMode("history"); }}>{label}</button>)}
      </div>
      <section className="admin-management-row" aria-label="Gestión de cancelaciones">
        <button aria-pressed={mode === "requests"} onClick={() => setMode("requests")}>Órdenes por cancelar <span>({requests.length})</span></button>
        <p>Revisa el motivo antes de aprobar. La cancelación afecta al pedido completo.</p>
      </section>
    </div>
    <h2>{mode === "requests" ? "Órdenes por cancelar" : "Historial de pedidos"}</h2>
    {!loading && visible.length === 0 && <p>No hay pedidos para esta selección.</p>}
    {user?.permissions.includes("production.release_order") && visible.map(order => <ReleaseCard key={`${mode}-${order.id}`} order={order} refresh={refresh}  />)}
  </main>;
}
