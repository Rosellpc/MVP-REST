export type OrderLine = {
  product_id: number;
  name: string;
  quantity: number;
  unit_price: string;
  line_total: string;
};

export type OrderQuote = {
  items: OrderLine[];
  total: string;
  currency: "PEN";
  prices_include_taxes: boolean;
  demo: boolean;
};

export type Order = OrderQuote & {
  public_code: string;
  status: "DEMO_CONFIRMED";
  payment_status: "SIMULATED";
  fulfillment: "DINE_IN" | "PICKUP";
  created_at: string;
  production_status: "NOT_RELEASED" | "PENDING" | "IN_PROGRESS" | "READY" | "CANCELLED" | "PARTIALLY_CANCELLED";
};

export type OrderPayload = {
  items: { product_id: number; quantity: number }[];
  customer_name: string;
  fulfillment: "DINE_IN" | "PICKUP";
  table_label: string;
  expected_total: string;
  accept_demo: boolean;
};

export class OrderApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function errorMessage(data: unknown): string {
  if (typeof data === "string") return data;
  if (Array.isArray(data)) return data.map(errorMessage).join(" ");
  if (data && typeof data === "object") {
    const fields = data as Record<string, unknown>;
    if (fields.detail) return errorMessage(fields.detail);
    return Object.values(fields).map(errorMessage).join(" ");
  }
  return "No se pudo procesar el pedido.";
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const timeout = AbortSignal.timeout(10000);
  const signal = options.signal ? AbortSignal.any([options.signal, timeout]) : timeout;
  const response = await fetch(`/api/v1/${path}`, {
    ...options, signal,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new OrderApiError(
    data ? errorMessage(data) : `No se pudo procesar la solicitud (HTTP ${response.status}).`,
    response.status,
  );
  if (!data) throw new Error("La respuesta del servidor no es válida.");
  return data as T;
}

export function previewOrder(items: OrderPayload["items"], signal: AbortSignal) {
  return request<OrderQuote>("orders/preview/", {
    method: "POST", body: JSON.stringify({ items }), signal,
  });
}

export async function createOrder(payload: OrderPayload, key: string) {
  const order = await request<Order>("orders/", {
    method: "POST", headers: { "Idempotency-Key": key }, body: JSON.stringify(payload),
  });
  if (typeof order.public_code !== "string" ||
      !/^[0-9a-f-]{36}$/i.test(order.public_code) || !order.demo) {
    throw new Error("No se pudo verificar la confirmación del pedido.");
  }
  return order;
}

export function getOrder(code: string, signal: AbortSignal) {
  return request<Order>(`orders/${encodeURIComponent(code)}/`, { signal });
}
