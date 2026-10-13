import type { OrderPayload } from "../orders/orderApi";

export type Config = { enabled: boolean; ready: boolean; public_key: string; environment: "test" };
export type Payment = { public_code: string; payment_status: string; production_status: string; total: string; amount_minor: number; reservation_expires_at: string; charging_available: boolean };
export type PendingPayment = { key: string; chargeKey: string; payload: Omit<OrderPayload, "accept_demo">; code?: string };
export const PAYMENT_STORAGE = "restaurantos.culqi-pending.v1";
export class PaymentApiError extends Error {
  status: number;
  constructor(message: string, status: number) { super(message); this.status = status; }
}

export function readPendingPayment(): PendingPayment | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(PAYMENT_STORAGE) || "null");
    if (!value || typeof value.key !== "string" || !/^[a-f0-9-]{36}$/i.test(value.key) || typeof value.chargeKey !== "string" || !/^[a-f0-9-]{36}$/i.test(value.chargeKey) || !Array.isArray(value.payload?.items)) return null;
    return value;
  } catch { return null; }
}

export function savePendingPayment(value: PendingPayment) {
  sessionStorage.setItem(PAYMENT_STORAGE, JSON.stringify(value));
}

export async function paymentRequest<T>(path: string, body?: unknown, key?: string, signal?: AbortSignal): Promise<T> {
  const timeout = AbortSignal.timeout(45000);
  const response = await fetch(`/api/v1/payments/${path}`, {
    method: body === undefined ? "GET" : "POST", cache: "no-store",
    headers: { "Content-Type": "application/json", ...(key ? { "Idempotency-Key": key } : {}) },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
  });
  const data = await response.json();
  if (!response.ok) throw new PaymentApiError(typeof data.detail === "string" ? data.detail : "Revisa los datos del pago y consulta el estado antes de reintentar.", response.status);
  return data;
}
