import { useCallback, useEffect, useRef, useState, type SubmitEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router";
import { useCart } from "../cart/CartContext";
import { CART_STORAGE_KEY } from "../cart/cartState";
import type { OrderQuote } from "../orders/orderApi";
import { authenticate, openCheckout, setup3DS } from "./culqi";
import { PAYMENT_STORAGE, PaymentApiError, paymentRequest, readPendingPayment, savePendingPayment, type Config, type Payment, type PendingPayment } from "./api";

export default function CulqiCheckoutPage({ config }: { config: Config }) {
  const { items, clearCart } = useCart();
  const navigate = useNavigate();
  const [pending, setPending] = useState(readPendingPayment);
  const [payment, setPayment] = useState<Payment | null>(null);
  const [quote, setQuote] = useState<OrderQuote | null>(null);
  const [name, setName] = useState("");
  const [fulfillment, setFulfillment] = useState<"DINE_IN" | "PICKUP">("DINE_IN");
  const [table, setTable] = useState("");
  const [accepted, setAccepted] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const guard = useRef(false);
  const checkoutRef = useRef<{ close: () => void } | null>(null);
  const authenticationController = useRef<AbortController | null>(null);
  const [resume3DS, setResume3DS] = useState<{ source_id: string; email: string; device_id: string } | null>(null);
  const cartKey = JSON.stringify(items.map(item => ({ product_id: item.productId, quantity: item.quantity })));

  useEffect(() => {
    if (pending) return;
    const controller = new AbortController();
    paymentRequest<OrderQuote>("preview/", { items: JSON.parse(cartKey) }, undefined, controller.signal)
      .then(setQuote).catch(err => { if (!controller.signal.aborted) setError(err.message); });
    return () => controller.abort();
  }, [cartKey, pending]);
  useEffect(() => () => { checkoutRef.current?.close(); authenticationController.current?.abort(); }, []);

  const receive = useCallback((result: Payment) => {
    setPayment(result);
    if (result.payment_status === "PAID" && result.production_status !== "NOT_RELEASED") {
      sessionStorage.setItem(CART_STORAGE_KEY, "[]");
      sessionStorage.removeItem(PAYMENT_STORAGE);
      clearCart();
      navigate(`/orders/${result.public_code}`, { replace: true });
    }
  }, [clearCart, navigate]);

  useEffect(() => {
    if (!pending?.code) return;
    const controller = new AbortController();
    const load = () => paymentRequest<Payment>(`${pending.code}/`, undefined, undefined, controller.signal).then(receive).catch(err => {
      if (!controller.signal.aborted) setError(err.message);
    });
    void load();
    const timer = window.setInterval(() => { if (!document.hidden) void load(); }, 10000);
    return () => { controller.abort(); clearInterval(timer); };
  }, [pending?.code, receive]);

  async function run(action: () => Promise<void>) {
    if (guard.current) return;
    guard.current = true; setBusy(true); setError("");
    try { await action(); } catch (err) { setError(err instanceof Error ? err.message : "No se pudo completar el pago. Consulta su estado."); }
    finally { guard.current = false; setBusy(false); }
  }

  async function prepare(attempt: PendingPayment) {
    savePendingPayment(attempt); setPending(attempt);
    let result: Payment;
    try { result = await paymentRequest<Payment>("prepare/", attempt.payload, attempt.key); }
    catch (err) {
      if (err instanceof PaymentApiError && [400, 409].includes(err.status)) {
        sessionStorage.removeItem(PAYMENT_STORAGE); setPending(null); setQuote(null);
      }
      throw err;
    }
    const next = { ...attempt, code: result.public_code };
    savePendingPayment(next); setPending(next); receive(result);
  }

  function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!quote || !accepted) return;
    void run(() => prepare({ key: crypto.randomUUID(), chargeKey: crypto.randomUUID(),
      payload: { customer_name: name.trim(), fulfillment, table_label: fulfillment === "DINE_IN" ? table.trim() : "",
        expected_total: quote.total, items: JSON.parse(cartKey) } }));
  }

  async function authenticateAndSend(attempt: PendingPayment, data: { source_id: string; email: string; device_id: string }) {
    authenticationController.current?.abort();
    const controller = new AbortController();
    authenticationController.current = controller;
    const authentication_3DS = await authenticate(data.source_id, controller.signal);
    receive(await paymentRequest<Payment>(`${attempt.code}/charge/`, { ...data, authentication_3DS }, attempt.chargeKey));
  }

  async function pay() {
    if (!pending?.code || !payment) return;
    const attempt = pending;
    checkoutRef.current?.close();
    checkoutRef.current = await openCheckout(config.public_key, payment.amount_minor, token => {
      void run(async () => {
        const device_id = await setup3DS(config.public_key, payment.amount_minor, token.email);
        const data = { source_id: token.id, email: token.email, device_id };
        setResume3DS(data);
        const result = await paymentRequest<Payment>(`${attempt.code}/charge/`, data, attempt.chargeKey);
        receive(result);
        if (result.payment_status === "REQUIRES_ACTION") await authenticateAndSend(attempt, data);
      });
    }, setError);
  }

  if (items.length === 0 && !pending) return <Navigate to="/cart" replace />;
  const terminal = payment && ["FAILED", "EXPIRED"].includes(payment.payment_status);
  return <main className="main-content cart-page">
    <p className="eyebrow">Checkout · Culqi</p><h1>Completa tu pedido</h1>
    <p className="demo-notice">Entorno de integración: utiliza medios de pago de prueba. No se cobrará dinero real. El pago aprobado enviará tickets de prueba a Cocina y Barra.</p>
    {error && <p className="checkout-error" role="alert">{error}</p>}
    {pending ? <section className="cart-panel">
      <h2>{terminal ? "Intento finalizado sin pago" : "Tu pago de prueba"}</h2>
      <p>Total: S/ {pending.payload.expected_total}</p>
      <p role="status">{busy ? "Procesando… No cierres esta página." : payment?.payment_status === "PENDING" ? "Productos reservados. Continúa con el pago." : payment?.payment_status === "REQUIRES_ACTION" ? "Completa la autenticación de tu tarjeta." : terminal ? "Puedes regresar al carrito para iniciar otro intento." : "Estamos verificando el resultado. Conservamos tu referencia para evitar duplicados."}</p>
      {payment?.payment_status === "PENDING" && <><p>Reserva hasta {new Date(payment.reservation_expires_at).toLocaleTimeString("es-PE")}</p><button className="cart-button" disabled={busy} onClick={() => void run(pay)}>Pagar con tarjeta de prueba</button></>}
      {payment?.payment_status === "REQUIRES_ACTION" && resume3DS && <button className="cart-button" disabled={busy} onClick={() => void run(() => authenticateAndSend(pending, resume3DS))}>Continuar autenticación</button>}
      {!terminal && <button className="cart-button" disabled={busy} onClick={() => void run(async () => {
        if (!pending.code) await prepare(pending);
        else receive(await paymentRequest<Payment>(`${pending.code}/reconcile/`, {}));
      })}>Consultar / recuperar intento</button>}
      {payment?.payment_status === "REQUIRES_ACTION" && !resume3DS && <p>La sesión de autenticación se interrumpió. Puedes cancelar este intento antes de iniciar uno nuevo.</p>}
      {payment && ["PENDING", "REQUIRES_ACTION"].includes(payment.payment_status) && <button className="cart-text-button" disabled={busy} onClick={() => void run(async () => {
        checkoutRef.current?.close(); authenticationController.current?.abort();
        receive(await paymentRequest<Payment>(`${pending.code}/abandon/`, {}));
      })}>Cancelar este intento sin cobro</button>}
      {pending.code && <p className="order-code">{pending.code}</p>}
      {terminal && <button className="cart-button" onClick={() => { sessionStorage.removeItem(PAYMENT_STORAGE); setPending(null); setPayment(null); navigate("/cart"); }}>Volver al carrito</button>}
    </section> : quote ? <form className="cart-layout checkout-form" onSubmit={submit}>
      <section className="cart-panel"><h2>Datos para la entrega</h2>
        <label>Tu nombre<input required maxLength={80} autoComplete="given-name" value={name} onChange={e => setName(e.target.value)} /></label>
        <label>Modalidad<select value={fulfillment} onChange={e => setFulfillment(e.target.value as "DINE_IN" | "PICKUP")}><option value="DINE_IN">Consumir en mesa</option><option value="PICKUP">Recoger para llevar</option></select></label>
        {fulfillment === "DINE_IN" && <label>Mesa<input required maxLength={20} value={table} onChange={e => setTable(e.target.value)} /></label>}
        <Link className="cart-back-link" to="/cart">Modificar carrito</Link>
      </section>
      <aside className="cart-panel"><h2>Tu pedido</h2><ul className="checkout-lines">{quote.items.map(item => <li key={item.product_id}><span>{item.quantity} × {item.name}</span><strong>S/ {Number(item.line_total).toFixed(2)}</strong></li>)}</ul>
        <div className="cart-total"><span>Total · impuestos incluidos</span><strong>S/ {quote.total}</strong></div>
        <label className="checkout-check"><input type="checkbox" required checked={accepted} onChange={e => setAccepted(e.target.checked)} />Entiendo que es un pago de prueba.</label>
        <button className="cart-button" disabled={busy || !accepted}>Reservar y continuar al pago</button>
      </aside>
    </form> : <p role="status">{error ? "Vuelve al carrito para revisar los productos." : "Verificando precios y disponibilidad…"} <Link to="/cart">Volver al carrito</Link></p>}
  </main>;
}
