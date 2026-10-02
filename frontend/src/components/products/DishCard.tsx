import { useState } from "react";
import type { Product } from "../../types/menu";
import { useCart } from "../../features/cart/CartContext";
import { MAX_QUANTITY } from "../../features/cart/cartState";

export default function DishCard({ product }: { product: Product }) {
  const { items, addItem } = useCart();
  const [message, setMessage] = useState("");
  const quantity = items.find((item) => item.productId === product.id)?.quantity ?? 0;

  function handleAdd() {
    try {
      addItem(product);
      setMessage(`${product.name}: ${quantity + 1} en el carrito.`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "No se pudo agregar este producto.");
    }
  }

  return (
    <article className="property-card">
      <img src={product.image_url || "/images/menu/table.webp"} alt={product.name} loading="lazy" />
      <div className="property-card-content">
        <h4>{product.name}</h4>
        <p>{product.category.name || "Sin categoría"}</p>
        <strong>S/ {Number(product.sale_price).toFixed(2)}</strong>
        <button className="cart-button" type="button" onClick={handleAdd}
          disabled={quantity >= MAX_QUANTITY} aria-label={`Agregar ${product.name} al carrito`}>
          {quantity >= MAX_QUANTITY ? "Límite alcanzado" : "Agregar al carrito"}
        </button>
        <p className="cart-feedback" role="status">{message}</p>
      </div>
    </article>
  );
}

