import { request, post } from "../auth/authApi.ts";

export type Ticket = {
  id: number; public_code: string; fulfillment: string; table_label: string;
  station_code: "KITCHEN" | "BAR"; status: "PENDING" | "IN_PROGRESS" | "READY" | "CANCELLED";
  demo: boolean; created_at: string;
  items: { id: number; name: string; quantity: number }[];
};

export async function fetchTickets(station: string, signal: AbortSignal): Promise<Ticket[]> {
  const tickets: Ticket[] = [];
  let path: string | null = `production/tickets/?station=${station}`;
  while (path) {
    const data = await request(path, { signal });
    tickets.push(...data.results);
    path = data.next ? `production/tickets/${new URL(data.next, "http://localhost").search}` : null;
  }
  return tickets;
}

export function updateTicket(id: number, action: "start" | "complete" | "cancel" | "finalize", reason = "") {
  return post(`production/tickets/${id}/${action}/`, { reason });
}
