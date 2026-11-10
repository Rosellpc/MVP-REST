import { useRef, useState, type SubmitEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router";
import CheckoutSteps from "../features/payments/CheckoutSteps";
import CheckoutIcon from "../features/payments/CheckoutIcon";
import { useCart } from "../features/cart/CartContext";
import { CART_STORAGE_KEY } from "../features/cart/cartState";
import { createOrder, OrderApiError } from "../features/orders/orderApi";
import { readAttempt, removeAttempt, saveAttempt, type CheckoutAttempt } from "../features/orders/checkoutAttempt";
import { cartSignature, readCheckoutDraft, removeCheckoutDraft } from "../features/orders/checkoutDraft";
import { useOrderQuote } from "../features/orders/useOrderQuote";

export default function CheckoutPage() {
  const { items, clearCart } = useCart();
  const navigate = useNavigate();
  const [pending, setPending] = useState(readAttempt);
  const [draft] = useState(readCheckoutDraft);
  const [method, setMethod] = useState<"card" | "wallet">("card");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const submittingRef = useRef(false);
  const orderItems = items.map(item => ({ product_id: item.productId, quantity: item.quantity }));
  const draftMatchesCart = draft && cartSignature(draft.items) === cartSignature(orderItems);
  const { quote, loading, error: quoteError, refresh } = useOrderQuote(orderItems, Boolean(items.length && draftMatchesCart && !pending));
  const currentQuote = quote && cartSignature(quote.items) === cartSignature(orderItems) ? quote : null;

  async function submitAttempt(attempt: CheckoutAttempt) {
    if (submittingRef.current) return;
    try {
      saveAttempt(attempt);
    } catch {
      setError("El navegador no permite guardar este intento. Habilita el almacenamiento de sesión antes de pagar.");
      return;
    }
    submittingRef.current = true;
    setSubmitting(true);
    setError("");
    setPending(attempt);
    try {
      const order = await createOrder(attempt.payload, attempt.key);
      // Cleanup only after the backend confirms; retries reuse the saved key.
      sessionStorage.setItem(CART_STORAGE_KEY, "[]");
      removeCheckoutDraft();
      removeAttempt();
      clearCart();
      navigate(`/orders/${order.public_code}`, { replace: true });
    } catch (err) {
      if (err instanceof OrderApiError && [400, 409].includes(err.status)) {
        removeAttempt();
        setPending(null);
        refresh();
        setError(err.message);
      } else {
        setError("No pudimos comprobar el resultado. Recupera este mismo pago para consultar la confirmación sin duplicar el pedido.");
      }
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  }

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!currentQuote || !draft || !draftMatchesCart || loading || quoteError || submittingRef.current) return;
    void submitAttempt({ key: crypto.randomUUID(), payload: {
      items: orderItems, customer_name: draft.customer_name, fulfillment: draft.fulfillment,
      table_label: draft.fulfillment === "DINE_IN" ? draft.table_label : "",
      expected_total: currentQuote.total, accept_demo: true,
    } });
  }

  if (!pending && (!items.length || !draftMatchesCart)) return <Navigate to="/cart" replace />;

  const details = pending?.payload ?? draft;
  const total = pending?.payload.expected_total ?? currentQuote?.total ?? draft?.expected_total;
  const lines = currentQuote?.items ?? items.map(item => ({ product_id: item.productId, name: item.name, quantity: item.quantity }));

  return <main className="main-content cart-page checkout-page purchase-page payment-page">
    <CheckoutSteps step={1} />
    <div className="purchase-heading"><p className="eyebrow">Un último paso</p>
      <h1>Completa tu pago.</h1><p className="cart-muted">Una experiencia de prueba, sin mover dinero.</p>
    </div>
    <div className="cart-panel payment-shell">
      <aside className="payment-order" aria-labelledby="payment-summary-title">
        <span className="payment-brand"><CheckoutIcon kind="bag" /> REST-OS</span>
        <p className="eyebrow" id="payment-summary-title">Total a pagar · PEN</p>
        <p className="payment-amount">S/ {total}</p>
        <span className="payment-demo-badge">Modo de prueba</span>
        <ul className="payment-lines">{lines.map(item => <li key={item.product_id}>
          <span className="payment-line-quantity">{item.quantity}×</span><span>{item.name}</span>
        </li>)}</ul>
        {details && <div className="payment-delivery-summary"><span className="eyebrow">Entrega del pedido</span>
          <strong>{details.customer_name}</strong><span>{details.fulfillment === "DINE_IN" ? `En mesa · ${details.table_label}` : "Recoger para llevar"}</span>
        </div>}
        {!pending && <Link className="payment-edit" to="/cart">← Editar pedido o entrega</Link>}
        <p className="purchase-demo-caption">Impuestos incluidos. Sin cargos adicionales.</p>
      </aside>
      <section className="payment-form-panel" aria-labelledby="payment-title" aria-busy={submitting}>
        {error && <p className="checkout-error" role="alert">{error}</p>}
        {pending ? <div className="payment-recovery">
          <span className={`payment-status-icon ${submitting ? "is-processing" : ""}`}><CheckoutIcon kind={submitting ? "card" : "check"} /></span>
          <h2 id="payment-title">{submitting ? "Confirmando tu pago…" : "Comprueba tu pago"}</h2>
          <p role="status">{submitting ? "Estamos registrando tu pedido. Te llevaremos a su estado en cuanto esté confirmado." : "Guardamos este intento. Puedes recuperar la confirmación aunque hayas recargado la página."}</p>
          <button className="cart-button purchase-primary" type="button" disabled={submitting} onClick={() => void submitAttempt(pending)}>
            {submitting ? "Procesando…" : "Recuperar confirmación"}
          </button>
          <p className="purchase-demo-caption">No cierres esta ventana mientras se confirma.</p>
        </div> : loading || !currentQuote && !quoteError ? <div className="payment-recovery" role="status">
          <h2 id="payment-title">Preparando tu pago…</h2><p>Comprobamos una última vez el total y la disponibilidad.</p>
        </div> : quoteError ? <div className="payment-recovery">
          <h2 id="payment-title">Revisa tu pedido</h2><p role="alert">{quoteError}</p>
          <button type="button" className="cart-button purchase-primary" onClick={refresh}>Reintentar</button>
          <Link className="cart-back-link" to="/cart">Volver al carrito</Link>
        </div> : <form className="simulated-payment-form" onSubmit={handleSubmit}>
          <div className="payment-title-row"><h2 id="payment-title">Método de pago</h2><span>SIMULADO</span></div>
          <fieldset className="payment-methods"><legend className="sr-only">Selecciona un método de pago de prueba</legend>
            <label className={method === "card" ? "is-selected" : ""}>
              <input type="radio" name="payment-method" value="card" checked={method === "card"} onChange={() => setMethod("card")} />
              <CheckoutIcon kind="card" /><span>Tarjeta de prueba</span>
            </label>
            <label className={method === "wallet" ? "is-selected" : ""}>
              <input type="radio" name="payment-method" value="wallet" checked={method === "wallet"} onChange={() => setMethod("wallet")} />
              <CheckoutIcon kind="wallet" /><span>Billetera de prueba</span>
            </label>
          </fieldset>
          {method === "card" ? <div className="demo-payment-card" aria-label="Tarjeta ficticia de demostración">
            <div><span>TARJETA DE DEMOSTRACIÓN</span><CheckoutIcon kind="card" /></div>
            <p>•••• &nbsp; •••• &nbsp; •••• &nbsp; 4242</p>
            <div><strong>{details?.customer_name}</strong><span>DEMO</span></div>
          </div> : <div className="demo-wallet"><span className="demo-wallet-icon"><CheckoutIcon kind="wallet" /></span>
            <strong>Billetera de demostración</strong><p>Confirma con un clic. No necesitas vincular ninguna cuenta.</p></div>}
          <p className="payment-explanation">Este método es ficticio. No ingreses datos bancarios ni de tarjetas reales.</p>
          {currentQuote && draft && currentQuote.total !== draft.expected_total && <p className="checkout-error" role="status">El total se actualizó a S/ {currentQuote.total}. Revisa el importe antes de continuar.</p>}
          <button className="cart-button purchase-primary" type="submit" disabled={!currentQuote || loading || submitting}>
            Pagar S/ {currentQuote?.total} <CheckoutIcon kind="arrow" />
          </button>
          <p className="purchase-demo-caption">Al confirmar aceptas el pago simulado y el envío del pedido a preparación de prueba. No se cobra dinero ni se prepara un pedido real.</p>
          <Link className="cart-back-link" to="/cart">Volver al carrito</Link>
        </form>}
      </section>
    </div>
  </main>;
}
