import Header from "../components/layout/Header";
import { Link, Navigate } from "react-router";
import { readAttempt } from "../features/orders/checkoutAttempt";
import { useCart } from "../features/cart/CartContext";
import { formatCartAmount, MAX_QUANTITY, priceToCents } from "../features/cart/cartState";

export default function CartPage() {
  const { items, itemCount, subtotal, setQuantity, removeItem, clearCart } = useCart();

  if (readAttempt()) return <Navigate to="/checkout" replace />;

  return (
    <div className="app">
      <Header />
      <main className="main-content cart-page">
        <p className="eyebrow">Tu pedido · Paso 1 de 2</p>
        <h1>Tu carrito</h1>
        <p className="cart-muted">Revisa tus productos antes de continuar.</p>
        {items.length === 0 ? (
          <section className="cart-panel cart-empty">
            <h2>Tu carrito está vacío</h2>
            <p>Explora la carta y agrega algo para disfrutar.</p>
            <Link className="cart-button" to="/menu">Explorar la carta</Link>
          </section>
        ) : (
          <div className="cart-layout">
            <section className="cart-panel" aria-label="Productos del carrito">
              <ul className="cart-items">
                {items.map((item) => (
                  <li className="cart-item" key={item.productId}>
                    <img src={item.imageUrl || "/images/menu/table.webp"} alt="" />
                    <div className="cart-item-detail">
                      <h2>{item.name}</h2>
                      <p className="cart-muted">S/ {item.unitPrice} por unidad</p>
                      <div className="cart-quantity">
                        <button type="button" disabled={item.quantity <= 1}
                          aria-label={`Quitar una unidad de ${item.name}`}
                          onClick={() => setQuantity(item.productId, item.quantity - 1)}>−</button>
                        <span aria-label={`Cantidad de ${item.name}`}>{item.quantity}</span>
                        <button type="button" disabled={item.quantity >= MAX_QUANTITY}
                          aria-label={`Agregar una unidad de ${item.name}`}
                          onClick={() => setQuantity(item.productId, item.quantity + 1)}>+</button>
                      </div>
                      <button className="cart-text-button" type="button"
                        aria-label={`Eliminar ${item.name} del carrito`}
                        onClick={() => removeItem(item.productId)}>Eliminar</button>
                    </div>
                    <strong>S/ {formatCartAmount(priceToCents(item.unitPrice) * item.quantity)}</strong>
                  </li>
                ))}
              </ul>
              <button className="cart-text-button" type="button" onClick={clearCart}>Vaciar carrito</button>
            </section>
            <aside className="cart-panel cart-summary" aria-label="Resumen del pedido">
              <h2>Resumen</h2>
              <p>{itemCount} {itemCount === 1 ? "producto" : "productos"}</p>
              <div className="cart-total" aria-live="polite">
                <span>Subtotal estimado</span><strong>S/ {formatCartAmount(subtotal)}</strong>
              </div>
              <p className="cart-muted">El precio y la disponibilidad se verifican al confirmar.</p>
              <Link className="cart-button" to="/checkout">Continuar al checkout</Link>
              <Link className="cart-back-link" to="/menu">Seguir eligiendo</Link>
            </aside>
          </div>
        )}
      </main>
    </div>
  );
}
