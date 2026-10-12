export type Dashboard = {
  generated_at: string; period: { start: string; end: string; timezone: string }; demo: boolean; currency: string;
  metrics: { amount: string; orders: number; all_orders: number; cancelled: number; partial_excluded: number; average_ticket: string | null; units: number; change_percent: string | null };
  previous: { amount: string; orders: number; average_ticket: string | null };
  trend: { date: string; amount: string; orders: number }[];
  top_products: { product_id: number; name: string; quantity: number; amount: string }[];
  channels: { fulfillment: string; count: number; amount: string }[];
  stations: { code: string; pending: number; preparing: number; ready: number; completed_sample: number; average_minutes: number | null }[];
  pending_cancellations: number;
  stock: { enabled: boolean; shift_id: number | null; units: number; products: number; registered: number; low: number; out: number; waste: number; production: number; alerts: { id: number; name: string; sku: string; stock_balance__quantity: number | null }[] };
  costing: { recipes: number; costed: number; pending: number; ingredients: number; average_food_cost: string | null; food_cost_sample: number };
};
export const pen = (value: string | null) => value === null ? "Sin datos" : new Intl.NumberFormat("es-PE", { style: "currency", currency: "PEN" }).format(Number(value));
