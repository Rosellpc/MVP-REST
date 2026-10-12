import { useCallback, useState } from "react";
import { request } from "../auth/authApi";
import { usePolling } from "./usePolling";

type Notice = { id: number; order_number: number; reason: string };

export default function CancellationNotices({ station }: { station: "KITCHEN" | "BAR" }) {
  const [since] = useState(() => new Date(Date.now() - 5 * 60000).toISOString());
  const [dismissed, setDismissed] = useState<number[]>([]);
  const load = useCallback(async (signal: AbortSignal): Promise<Notice[]> => {
    const query = new URLSearchParams({ station, approved_since: since });
    const rows: Notice[] = [];
    let path: string | null = `production/cancellation-notices/?${query}`;
    while (path) {
      const page = await request(path, { signal });
      rows.push(...page.results);
      path = page.next ? `production/cancellation-notices/${new URL(page.next, "http://localhost").search}` : null;
    }
    return rows;
  }, [station, since]);
  const { data, error } = usePolling(load, 10000);
  const notices = data?.filter(row => !dismissed.includes(row.id)) ?? [];
  return <section aria-label="Cancelaciones aprobadas">{error && <p role="status">No se pudieron actualizar los avisos de cancelación.</p>}{notices.map(notice => <div className="ticket-card" role="status" key={notice.id}><p><strong>Pedido #{notice.order_number}: cancelación aprobada por el administrador.</strong></p><p>{notice.reason}</p><button onClick={() => setDismissed(current => [...current, notice.id])}>Entendido</button></div>)}</section>;
}
