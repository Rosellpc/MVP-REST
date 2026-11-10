import { useState, type SubmitEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router";
import { readAttempt } from "../features/orders/checkoutAttempt";
import { readPendingPayment } from "../features/payments/api";
import { useCart } from "../features/cart/CartContext";
import { formatCartAmount, MAX_QUANTITY, priceToCents } from "../features/cart/cartState";
import { cartSignature, readCheckoutDraft, saveCheckoutDraft, validDelivery } from "../features/orders/checkoutDraft";
import type { OrderPayload } from "../features/orders/orderApi";
import { useOrderQuote } from "../features/orders/useOrderQuote";
import CheckoutSteps from "../features/payments/CheckoutSteps";
import CheckoutIcon from "../features/payments/CheckoutIcon";

export default function CartPage() {
  const { items, itemCount, subtotal, setQuantity, removeItem, clearCart } = useCart();
  const navigate = useNavigate();
  const [draft] = useState(readCheckoutDraft);
  const [name, setName] = useState(draft?.customer_name ?? "");
  const [fulfillment, setFulfillment] = useState<OrderPayload["fulfillment"]>(draft?.fulfillment ?? "DINE_IN");
  const [table, setTable] = useState(draft?.table_label ?? "");
  const [error, setError] = useState("");
  const pending = Boolean(readAttempt() || readPendingPayment());
  const orderItems = items.map(item => ({ product_id: item.productId, quantity: item.quantity }));
  const { quote, loading, error: quoteError, refresh } = useOrderQuote(orderItems, items.length > 0 && !pending);
  const currentQuote = quote && cartSignature(quote.items) === cartSignature(orderItems) ? quote : null;

  function continueToPayment(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const details = { customer_name: name.trim(), fulfillment, table_label: fulfillment === "DINE_IN" ? table.trim() : "" };
    if (!validDelivery(details)) {
      setError("Completa tu nombre y la mesa si vas a consumir en el local.");
      return;
    }
    if (!currentQuote || loading || quoteError) return;
    try {
      saveCheckoutDraft({ ...details, items: orderItems, expected_total: currentQuote.total });
      navigate("/checkout");
    } catch {
      setError("No pudimos guardar tus datos. Habilita el almacenamiento de sesión para continuar.");
    }
  }

  if (pending) return <Navigate to="/checkout" replace />;

  return <main className="main-content cart-page purchase-page">
    <CheckoutSteps step={0} />
    <div className="purchase-heading"><p className="eyebrow">Un buen momento empieza aquí</p>
      <h1>Tu pedido, a tu manera.</h1><p className="cart-muted">Revisa tu selección y cuéntanos cómo te la entregamos.</p>
    </div>
    {items.length === 0 ? <section className="cart-panel cart-empty">
      <span className="purchase-empty-icon"><CheckoutIcon kind="bag" /></span>
      <h2>Tu carrito está vacío</h2><p>Tu próximo favorito te espera en la carta.</p>
      <Link className="cart-button purchase-primary" to="/menu">Explorar la carta <CheckoutIcon kind="arrow" /></Link>
    </section> : <form className="cart-panel checkout-form purchase-card" onSubmit={continueToPayment}>
      <div className="purchase-card-grid">
        <section className="purchase-order" aria-labelledby="cart-summary-title">
          <div className="purchase-section-heading"><h2 id="cart-summary-title">Resumen del pedido</h2>
            <span className="purchase-count">{itemCount} {itemCount === 1 ? "producto" : "productos"}</span></div>
          <ul className="cart-items">
            {items.map(item => {
              const line = currentQuote?.items.find(value => value.product_id === item.productId);
              return <li className="cart-item" key={item.productId}>
                <img src={item.imageUrl || "/images/menu/table.webp"} alt="" />
                <div className="cart-item-detail"><h3>{item.name}</h3>
                  <p className="cart-muted">S/ {line?.unit_price ?? item.unitPrice} / unidad</p>
                  <div className="purchase-item-actions"><div className="cart-quantity">
                    <button type="button" disabled={item.quantity <= 1} aria-label={`Quitar una unidad de ${item.name}`}
                      onClick={() => setQuantity(item.productId, item.quantity - 1)}>−</button>
                    <span aria-label={`Cantidad de ${item.name}`}>{item.quantity}</span>
                    <button type="button" disabled={item.quantity >= MAX_QUANTITY} aria-label={`Agregar una unidad de ${item.name}`}
                      onClick={() => setQuantity(item.productId, item.quantity + 1)}>+</button>
                  </div><button className="cart-text-button" type="button" aria-label={`Eliminar ${item.name} del carrito`}
                    onClick={() => removeItem(item.productId)}>Eliminar</button></div>
                </div>
                <strong>S/ {line?.line_total ?? formatCartAmount(priceToCents(item.unitPrice) * item.quantity)}</strong>
              </li>;
            })}
          </ul>
          <button className="cart-text-button purchase-clear" type="button" onClick={clearCart}>Vaciar carrito</button>
        </section>
        <section className="purchase-delivery" aria-labelledby="delivery-title">
          <p className="eyebrow">Como tú prefieras</p><h2 id="delivery-title">Datos de entrega</h2>
          <label htmlFor="delivery-name">Tu nombre
            <input id="delivery-name" required maxLength={80} autoComplete="given-name" placeholder="¿Cómo te llamas?" value={name}
              onChange={event => { setName(event.target.value); setError(""); }} />
          </label>
          <fieldset className="purchase-fulfillment"><legend>¿Cómo disfrutarás tu pedido?</legend>
            <label className={fulfillment === "DINE_IN" ? "is-selected" : ""}>
              <input type="radio" name="fulfillment" value="DINE_IN" checked={fulfillment === "DINE_IN"} onChange={() => setFulfillment("DINE_IN")} />
              <span>En mesa<small>Te lo llevamos a tu lugar</small></span>
            </label>
            <label className={fulfillment === "PICKUP" ? "is-selected" : ""}>
              <input type="radio" name="fulfillment" value="PICKUP" checked={fulfillment === "PICKUP"} onChange={() => setFulfillment("PICKUP")} />
              <span>Para recoger<small>Listo para llevar</small></span>
            </label>
          </fieldset>
          {fulfillment === "DINE_IN" ? <label htmlFor="delivery-table">Número o nombre de mesa
            <input id="delivery-table" required maxLength={20} value={table} placeholder="Por ejemplo, mesa 12"
              onChange={event => { setTable(event.target.value); setError(""); }} />
          </label> : <p className="purchase-delivery-hint">Podrás seguir el estado del pedido y recogerlo cuando esté listo.</p>}
        </section>
      </div>
      <footer className="purchase-card-footer">
        <div className="purchase-total-row"><div><span>{currentQuote ? "Total del pedido" : "Total estimado"}</span>
          <p className="cart-muted">PEN · Impuestos incluidos</p></div>
          <strong aria-live="polite">S/ {currentQuote?.total ?? formatCartAmount(subtotal)}</strong></div>
        {error && <p className="checkout-error" role="alert">{error}</p>}
        {quoteError ? <div className="checkout-error" role="alert"><p>{quoteError}</p>
          <button type="button" className="cart-text-button" onClick={refresh}>Volver a verificar</button></div>
          : <p className="purchase-verification" role="status">{loading || !currentQuote ? "Verificando precios y disponibilidad…" : "Precios y disponibilidad verificados. El pago se confirma en el siguiente paso."}</p>}
        <button className="cart-button purchase-primary" type="submit" disabled={loading || !currentQuote || Boolean(quoteError)}>
          Pagar <CheckoutIcon kind="arrow" />
        </button>
        <Link className="cart-back-link" to="/menu">Seguir comprando</Link>
        <p className="purchase-demo-caption">Experiencia de demostración. No se realizarán cobros reales.</p>
      </footer>
    </form>}
  </main>;
}
