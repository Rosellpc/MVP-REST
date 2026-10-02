import { useRef, useState, type SubmitEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router";
import { useCart } from "../features/cart/CartContext";
import { CART_STORAGE_KEY } from "../features/cart/cartState";
import { createOrder, OrderApiError, type OrderPayload } from "../features/orders/orderApi";
import { readAttempt, removeAttempt, saveAttempt, type CheckoutAttempt } from "../features/orders/checkoutAttempt";
import { useOrderQuote } from "../features/orders/useOrderQuote";

export default function CheckoutPage() {
  const { items, clearCart } = useCart();
  const navigate = useNavigate();
  const [pending, setPending] = useState(readAttempt);
  const [name, setName] = useState(pending?.payload.customer_name ?? "");
  const [fulfillment, setFulfillment] = useState<OrderPayload["fulfillment"]>(pending?.payload.fulfillment ?? "DINE_IN");
  const [table, setTable] = useState(pending?.payload.table_label ?? "");
  const [accepted, setAccepted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const submittingRef = useRef(false);
  const orderItems = items.map((item) => ({ product_id: item.productId, quantity: item.quantity }));
  const { quote, loading, error: quoteError, refresh } = useOrderQuote(orderItems, items.length > 0 && !pending);

  async function submitAttempt(attempt: CheckoutAttempt) {
    if (submittingRef.current) return;
    try {
      saveAttempt(attempt);
    } catch {
      setError("El navegador no permite guardar este intento. Habilita el almacenamiento de sesión antes de confirmar.");
      return;
    }
    submittingRef.current = true;
    setSubmitting(true);
    setError("");
    try {
      // Si no se puede preservar el intento, no enviamos una compra recuperable a medias.
      setPending(attempt);
      const order = await createOrder(attempt.payload, attempt.key);
      // Conserva la clave pendiente si falla la limpieza del almacenamiento.
      sessionStorage.setItem(CART_STORAGE_KEY, "[]");
      removeAttempt();
      clearCart();
      navigate(`/orders/${order.public_code}`, { replace: true });
    } catch (err) {
      if (err instanceof OrderApiError && [400, 409].includes(err.status)) {
        removeAttempt();
        setPending(null);
        setAccepted(false);
        refresh();
        setError(err.message);
      } else {
        setError("No pudimos comprobar la confirmación. Usa Recuperar confirmación para consultar el mismo intento sin duplicarlo.");
      }
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  }

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!quote || !accepted || loading || submittingRef.current) return;
    if (!name.trim() || (fulfillment === "DINE_IN" && !table.trim())) {
      setError("Completa tu nombre y la mesa si consumirás en el local.");
      return;
    }
    const attempt: CheckoutAttempt = {
      key: crypto.randomUUID(),
      payload: { items: orderItems, customer_name: name.trim(), fulfillment,
        table_label: fulfillment === "DINE_IN" ? table.trim() : "",
        expected_total: quote.total, accept_demo: true },
    };
    void submitAttempt(attempt);
  }

  if (items.length === 0 && !pending) return <Navigate to="/cart" replace />;

  return (
      <main className="main-content cart-page">
        <p className="eyebrow">Tu pedido · Paso 2 de 2</p>
        <h1>Confirma tu pedido</h1>
        <p className="demo-notice">Demostración: el pago es simulado. No se cobrará dinero ni se enviará el pedido a cocina.</p>
        {error && <p className="checkout-error" role="alert">{error}</p>}
        {pending ? (
          <section className="cart-panel">
            <h2>{submitting ? "Confirmando tu pedido…" : "Confirmación pendiente de comprobar"}</h2>
            <p>Este intento corresponde a S/ {pending.payload.expected_total}. Conservamos su referencia para evitar duplicados.</p>
            <button className="cart-button" type="button" disabled={submitting}
              onClick={() => void submitAttempt(pending)}>
              {submitting ? "Procesando…" : "Recuperar confirmación"}
            </button>
          </section>
        ) : loading ? <p role="status">Verificando precios y disponibilidad…</p>
          : quoteError ? (
            <section className="cart-panel">
              <p role="alert">{quoteError}</p>
              <button className="cart-button" type="button" onClick={refresh}>Reintentar</button>
              <Link className="cart-back-link" to="/cart">Volver al carrito</Link>
            </section>
          ) : quote && (
            <form className="cart-layout checkout-form" onSubmit={handleSubmit}>
              <section className="cart-panel">
                <h2>Datos para la entrega</h2>
                <label>Tu nombre
                  <input required maxLength={80} autoComplete="given-name" value={name}
                    onChange={(event) => setName(event.target.value)} />
                </label>
                <label>¿Cómo disfrutarás tu pedido?
                  <select value={fulfillment} onChange={(event) => setFulfillment(event.target.value as OrderPayload["fulfillment"])}>
                    <option value="DINE_IN">Consumir en mesa</option>
                    <option value="PICKUP">Recoger para llevar</option>
                  </select>
                </label>
                {fulfillment === "DINE_IN" && <label>Número o nombre de mesa
                  <input required maxLength={20} value={table} placeholder="Ej: 12"
                    onChange={(event) => setTable(event.target.value)} />
                </label>}
                <p className="cart-muted">No solicitamos datos de tarjeta para esta demostración.</p>
                <Link className="cart-back-link" to="/cart">Modificar carrito</Link>
              </section>
              <aside className="cart-panel cart-summary">
                <h2>Tu pedido</h2>
                <ul className="checkout-lines">{quote.items.map((item) => (
                  <li key={item.product_id}><span>{item.quantity} × {item.name}</span><strong>S/ {item.line_total}</strong></li>
                ))}</ul>
                <div className="cart-total"><span>Total verificado</span><strong>S/ {quote.total}</strong></div>
                <p className="cart-muted">Soles peruanos (PEN). Impuestos incluidos.</p>
                <label className="checkout-check">
                  <input type="checkbox" required checked={accepted} onChange={(event) => setAccepted(event.target.checked)} />
                  Entiendo que este pedido y su pago son una demostración.
                </label>
                <button className="cart-button" type="submit" disabled={!accepted || submitting}>
                  Confirmar pedido de demostración
                </button>
              </aside>
            </form>
          )}
      </main>
  );
}
