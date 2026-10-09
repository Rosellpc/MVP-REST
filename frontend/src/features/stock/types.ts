export type StockRow = {
  product_id: number; name: string; sku: string; category: string; station: string;
  initial: number; production: number; sales: number; waste: number; adjustments: number;
  quantity: number; unit: string; status: "OUT" | "LOW" | "AVAILABLE"; updated_at: string | null;
  theoretical: number | null; counted: number | null; difference: number | null; reason: string;
};
export type Shift = { id: number; opened_at: string; closed_at: string | null; opened_by: string; closed_by: string | null; notes: string; opening_notes: string };
export type StockData = { enabled: boolean; revision: number; shift: Shift | null; rows: StockRow[]; summary: { products: number; quantity: number; production: number; sales: number; waste: number; low: number; out: number } };
export type Movement = { id: number; product_id: number; product: string; kind: string; delta: number; quantity: number; balance_after: number; actor: string; reason: string; created_at: string; shift_id: number; order_id: number | null };
export type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] };
export const kindLabel: Record<string, string> = { PRODUCTION: "Producción", SALE: "Venta demo", RETURN: "Devolución sin preparar", CANCEL_WASTE: "Cancelación preparada", WASTE: "Merma / descarte", ADJUST: "Ajuste", COUNT: "Conciliación" };
export const dateLabel = (date: string | null) => date ? new Date(date).toLocaleString("es-PE") : "Sin movimientos";
