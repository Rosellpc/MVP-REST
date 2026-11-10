import type { OrderPayload } from "./orderApi";

export type DeliveryDetails = Pick<OrderPayload, "customer_name" | "fulfillment" | "table_label">;
export type CheckoutDraft = DeliveryDetails & Pick<OrderPayload, "items" | "expected_total">;
export const DRAFT_STORAGE_KEY = "restaurantos.checkout-draft.v1";

export function validDelivery(details: DeliveryDetails): boolean {
  return Boolean(details.customer_name.trim() && details.customer_name.trim().length <= 80
    && ["DINE_IN", "PICKUP"].includes(details.fulfillment)
    && (details.fulfillment === "PICKUP" || (details.table_label.trim() && details.table_label.trim().length <= 20)));
}

export function cartSignature(items: OrderPayload["items"]): string {
  return JSON.stringify(items.map(item => ({ product_id: item.product_id, quantity: item.quantity }))
    .sort((a, b) => a.product_id - b.product_id));
}

export function readCheckoutDraft(): CheckoutDraft | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(DRAFT_STORAGE_KEY) || "null");
    if (!value || typeof value.customer_name !== "string" || typeof value.table_label !== "string"
      || !validDelivery(value) || typeof value.expected_total !== "string"
      || !/^\d{1,12}\.\d{2}$/.test(value.expected_total) || !Array.isArray(value.items)
      || value.items.length === 0 || value.items.length > 100
      || value.items.some((item: OrderPayload["items"][number]) => !item
        || !Number.isInteger(item.product_id) || item.product_id < 1
        || !Number.isInteger(item.quantity) || item.quantity < 1 || item.quantity > 99)
      || new Set(value.items.map((item: OrderPayload["items"][number]) => item.product_id)).size !== value.items.length) return null;
    return value;
  } catch {
    return null;
  }
}

export function saveCheckoutDraft(draft: CheckoutDraft) {
  sessionStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(draft));
}

export function removeCheckoutDraft() {
  sessionStorage.removeItem(DRAFT_STORAGE_KEY);
}
