import { useCallback, useState } from "react";
import { request, post, AuthError } from "../auth/authApi";
import { useAuth } from "../auth/useAuth";
import { usePolling } from "./usePolling";

type StaffOrder = { id: number; public_code: string; production_status: string; table_label: string; fulfillment: string };

function ReleaseCard({ order, refresh }: { order: StaffOrder; refresh: () => void }) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  return <article className="ticket-card"><h2>Pedido #{order.id}</h2><p className="ticket-code">{order.public_code}</p><p>{order.fulfillment === "DINE_IN" ? `Mesa ${order.table_label}` : "Para recoger"}</p>
    {error && <p role="alert">{error}</p>}
    <button disabled={pending} onClick={async () => {
      if (pending) return;
      setPending(true); setError("");
      try { await post(`staff/orders/${order.id}/release/`); refresh(); }
      catch (err) { setError(err instanceof Error ? err.message : "No se pudo liberar el pedido."); refresh(); }
      finally { setPending(false); }
    }}>{pending ? "Liberando…" : "Liberar a preparación de prueba"}</button>
  </article>;
}

export default function ReleaseOrders() {
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
      return orders.filter(order => order.production_status === "NOT_RELEASED");
    } catch (err) {
      if (err instanceof AuthError && [401, 403].includes(err.status)) void refreshSession();
      throw err;
    }
  }, [refreshSession]);
  const { data, error, loading, refresh } = usePolling(load);
  return <main className="staff-content"><h1>Administración · Pedidos</h1><p className="demo-notice">Demostración: la liberación envía tickets de prueba a Cocina y Barra. No se realizan preparaciones reales.</p>
    {loading && <p role="status">Cargando pedidos…</p>}{error && <p role="alert">{error}</p>}<button onClick={refresh}>Actualizar</button>
    {data?.length === 0 && <p>No hay pedidos pendientes de aceptación.</p>}
    {user?.permissions.includes("production.release_order") && data?.map(order => <ReleaseCard key={order.id} order={order} refresh={refresh} />)}
  </main>;
}
