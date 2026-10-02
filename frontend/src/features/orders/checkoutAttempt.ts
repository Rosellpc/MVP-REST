import type { OrderPayload } from "./orderApi";

export type CheckoutAttempt = { key: string; payload: OrderPayload };
export const ATTEMPT_STORAGE_KEY = "restaurantos.checkout-attempt.v1";

export function readAttempt(): CheckoutAttempt | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(ATTEMPT_STORAGE_KEY) || "null");
    if (!value || typeof value.key !== "string" || !/^[0-9a-f-]{36}$/i.test(value.key) ||
        !value.payload || typeof value.payload.customer_name !== "string" ||
        typeof value.payload.expected_total !== "string" ||
        typeof value.payload.table_label !== "string" ||
        !["DINE_IN", "PICKUP"].includes(value.payload.fulfillment) ||
        value.payload.accept_demo !== true || !Array.isArray(value.payload.items) ||
        value.payload.items.length === 0) return null;
    return value;
  } catch {
    return null;
  }
}

export function saveAttempt(attempt: CheckoutAttempt) {
  // Se guarda antes del POST: un reintento tras recargar mantiene la misma clave.
  sessionStorage.setItem(ATTEMPT_STORAGE_KEY, JSON.stringify(attempt));
}

export function removeAttempt() {
  sessionStorage.removeItem(ATTEMPT_STORAGE_KEY);
}
