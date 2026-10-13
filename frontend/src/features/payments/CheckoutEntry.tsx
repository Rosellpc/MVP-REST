import { useEffect, useState } from "react";
import { Link } from "react-router";
import DemoCheckout from "../../pages/CheckoutPage";
import { readAttempt } from "../orders/checkoutAttempt";
import { paymentRequest, type Config } from "./api";
import CulqiCheckoutPage from "./CulqiCheckoutPage";

export default function CheckoutEntry() {
  const [config, setConfig] = useState<Config | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    paymentRequest<Config>("config/", undefined, undefined, controller.signal).then(setConfig).catch(() => {
      if (!controller.signal.aborted) setError("No se pudo consultar la configuración de pagos. Recarga para reintentar.");
    });
    return () => controller.abort();
  }, [retry]);
  if (readAttempt()) return <DemoCheckout />;
  if (!config) return <main className="main-content cart-page checkout-page">
    <p className="eyebrow">Tu pedido</p><h1>Confirma tu pedido</h1>
    <section className="cart-panel checkout-status" aria-busy={!error}>
      <h2>{error ? "No pudimos cargar el checkout" : "Preparando tu checkout…"}</h2>
      <p role={error ? "alert" : "status"}>{error ? "Tu carrito sigue guardado. Comprueba tu conexión y vuelve a intentarlo." : "Estamos consultando los medios de pago disponibles."}</p>
      {error && <button className="cart-button" onClick={() => { setError(""); setRetry(value => value + 1); }}>Reintentar</button>}
      <Link className="cart-back-link" to="/cart">Volver al carrito</Link>
    </section>
  </main>;
  if (!config.enabled) return <DemoCheckout />;
  if (!config.ready) return <main className="main-content cart-page checkout-page"><h1>Pago en configuración</h1><section className="cart-panel checkout-status"><p>El pago con Culqi aún no está disponible. Tu carrito sigue guardado; consulta al personal para continuar.</p><Link className="cart-button" to="/cart">Volver al carrito</Link></section></main>;
  return <CulqiCheckoutPage config={config} />;
}
