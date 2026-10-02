import type { Product } from "../../types/menu";

export type CartItem = {
  productId: number;
  name: string;
  imageUrl: string;
  unitPrice: string;
  quantity: number;
};

export const MAX_QUANTITY = 99;
export const CART_STORAGE_KEY = "restaurantos.cart.v1";

export type CartAction =
  | { type: "add"; product: Product }
  | { type: "quantity"; productId: number; quantity: number }
  | { type: "remove"; productId: number }
  | { type: "clear" };

// El subtotal es orientativo; Django calcula el importe definitivo.
export function priceToCents(price: string): number {
  if (!/^\d{1,8}\.\d{2}$/.test(price)) throw new Error("El precio no es válido.");
  const [units, cents] = price.split(".");
  return Number(units) * 100 + Number(cents);
}

export function cartSubtotal(items: CartItem[]): number {
  return items.reduce((total, item) => total + priceToCents(item.unitPrice) * item.quantity, 0);
}

export function formatCartAmount(cents: number): string {
  return (cents / 100).toLocaleString("es-PE", {
    minimumFractionDigits: 2, maximumFractionDigits: 2,
  });
}

export function cartReducer(items: CartItem[], action: CartAction): CartItem[] {
  switch (action.type) {
    case "add": {
      const existing = items.find((item) => item.productId === action.product.id);
      if (existing) {
        return items.map((item) => item.productId === action.product.id
          ? { ...item, quantity: Math.min(MAX_QUANTITY, item.quantity + 1),
              name: action.product.name, imageUrl: action.product.image_url,
              unitPrice: action.product.sale_price }
          : item);
      }
      return [...items, {
        productId: action.product.id, name: action.product.name,
        imageUrl: action.product.image_url, unitPrice: action.product.sale_price, quantity: 1,
      }];
    }
    case "quantity":
      if (!Number.isInteger(action.quantity) || action.quantity < 1 ||
          action.quantity > MAX_QUANTITY) return items;
      return items.map((item) => item.productId === action.productId
        ? { ...item, quantity: action.quantity } : item);
    case "remove":
      return items.filter((item) => item.productId !== action.productId);
    case "clear":
      return [];
  }
}

/** Descarta datos antiguos o dañados del almacenamiento del navegador. */
export function parseStoredCart(raw: string | null): CartItem[] {
  if (!raw) return [];
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    const ids = new Set<number>();
    const items: CartItem[] = [];
    for (const value of parsed) {
      if (typeof value !== "object" || value === null) return [];
      const item = value as Record<string, unknown>;
      if (typeof item.productId !== "number" || !Number.isSafeInteger(item.productId) ||
          item.productId < 1 || ids.has(item.productId) ||
          typeof item.name !== "string" || typeof item.imageUrl !== "string" ||
          typeof item.unitPrice !== "string" || typeof item.quantity !== "number" ||
          !Number.isInteger(item.quantity) || item.quantity < 1 ||
          item.quantity > MAX_QUANTITY) return [];
      priceToCents(item.unitPrice);
      ids.add(item.productId);
      items.push({ productId: item.productId, name: item.name,
        imageUrl: item.imageUrl, unitPrice: item.unitPrice, quantity: item.quantity });
    }
    return items;
  } catch {
    return [];
  }
}
