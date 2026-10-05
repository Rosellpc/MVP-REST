import { useCallback, useState } from "react";
import { useAuth } from "../auth/useAuth";
import { AuthError } from "../auth/authApi";
import { fetchTickets, updateTicket, type Ticket } from "./productionApi";
import { usePolling } from "./usePolling";
import "../../styles/production.css";

const columns = { PENDING: "Pendientes", IN_PROGRESS: "En preparación", READY: "Listos", CANCELLED: "Cancelados" };

function TicketCard({ ticket, refresh, now }: { ticket: Ticket; refresh: () => void; now: number }) {
  const { user, refresh: refreshSession } = useAuth();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [reason, setReason] = useState("");
  const canAdvance = user?.permissions.includes(`production.advance_${ticket.station_code.toLowerCase()}_ticket`);
  const canCancel = user?.permissions.includes("production.cancel_ticket");
  const active = ticket.status === "PENDING" || ticket.status === "IN_PROGRESS";
  async function act(action: "start" | "complete" | "cancel" | "finalize") {
    if (pending) return;
    setPending(true); setError("");
    try { await updateTicket(ticket.id, action, reason); refresh(); }
    catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo actualizar el ticket.");
      if (err instanceof AuthError && [401, 403].includes(err.status)) void refreshSession();
      refresh();
    } finally { setPending(false); }
  }
  return <article className="ticket-card">
    <span className="eyebrow">Demostración · Ticket #{ticket.id}</span>
    <h3>{ticket.fulfillment === "DINE_IN" ? `Mesa ${ticket.table_label}` : "Para recoger"}</h3>
    <p className="ticket-code" title={ticket.public_code}>Pedido {ticket.public_code}</p>
    <p><time dateTime={ticket.created_at}>{new Date(ticket.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time> · {Math.max(0, Math.floor((now - Date.parse(ticket.created_at)) / 60000))} min desde recepción</p>
    <ul>{ticket.items.map(item => <li key={item.id}><strong>{item.quantity} ×</strong> {item.name}</li>)}</ul>
    {error && <p role="alert">{error}</p>}
    {ticket.status === "READY" && canAdvance && <button disabled={pending} onClick={() => void act("finalize")}>{pending ? "Finalizando…" : "Finalizado"}</button>}
    {active && canAdvance && <button disabled={pending} onClick={() => void act(ticket.status === "PENDING" ? "start" : "complete")}>{pending ? "Guardando…" : ticket.status === "PENDING" ? "Iniciar preparación" : "Marcar listo"}</button>}
    {active && canCancel && <details><summary>Cancelar ticket</summary><label>Motivo<input maxLength={500} value={reason} onChange={event => setReason(event.target.value)} disabled={pending} /></label><button disabled={pending || !reason.trim()} onClick={() => void act("cancel")}>Confirmar cancelación</button></details>}
  </article>;
}

export default function ProductionBoard({ station }: { station: "KITCHEN" | "BAR" }) {
  const { refresh: refreshSession } = useAuth();
  const load = useCallback(async (signal: AbortSignal) => {
    try { return await fetchTickets(station, signal); }
    catch (err) {
      if (err instanceof AuthError && [401, 403].includes(err.status)) void refreshSession();
      throw err;
    }
  }, [station, refreshSession]);
  const { data, error, loading, updatedAt, refresh } = usePolling(load);
  return <main className="production-board">
    <h1>{station === "KITCHEN" ? "Cocina" : "Barra"}</h1>
    <p className="demo-notice">Producción de demostración. No representa preparaciones reales.</p>
    <div className="production-toolbar"><p role="status">{loading ? "Cargando tickets…" : `Última actualización: ${updatedAt?.toLocaleTimeString() ?? "sin datos"}`}</p><button onClick={refresh}>Actualizar</button></div>
    {error && <p role="alert">{error} Los datos visibles pueden estar desactualizados.</p>}
    {!loading && data?.length === 0 && <p>No hay tickets para esta estación.</p>}
    <div className="production-columns">{Object.entries(columns).map(([status, label]) => {
      const tickets = data?.filter(ticket => ticket.status === status) ?? [];
      return <section key={status}><h2>{label} <span>({tickets.length})</span></h2>{tickets.map(ticket => <TicketCard key={ticket.id} ticket={ticket} refresh={refresh} now={updatedAt?.getTime() ?? 0} />)}</section>;
    })}</div>
  </main>;
}
