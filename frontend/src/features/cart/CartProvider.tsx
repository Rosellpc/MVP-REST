import { useEffect, useReducer, type ReactNode } from "react";
import { CartContext } from "./CartContext";
import { readAttempt } from "../orders/checkoutAttempt";
import { CART_STORAGE_KEY, cartReducer, cartSubtotal, parseStoredCart, priceToCents } from "./cartState";

export default function CartProvider({ children }: { children: ReactNode }) {
  const [items, dispatch] = useReducer(cartReducer, undefined, () => {
    try {
      return parseStoredCart(sessionStorage.getItem(CART_STORAGE_KEY));
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      sessionStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
    } catch {
      // Si el navegador bloquea el almacenamiento, el carrito funciona en memoria.
    }
  }, [items]);

  return (
    <CartContext.Provider value={{
      items,
      itemCount: items.reduce((count, item) => count + item.quantity, 0),
      subtotal: cartSubtotal(items),
      addItem: (product) => {
        if (readAttempt()) throw new Error("Primero recupera la confirmación pendiente desde el checkout.");
        priceToCents(product.sale_price);
        dispatch({ type: "add", product });
      },
      setQuantity: (productId, quantity) => dispatch({ type: "quantity", productId, quantity }),
      removeItem: (productId) => dispatch({ type: "remove", productId }),
      clearCart: () => dispatch({ type: "clear" }),
    }}>
      {children}
    </CartContext.Provider>
  );
}
