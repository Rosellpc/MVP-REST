import { useEffect, useState } from "react";
import DemoCheckout from "../../pages/CheckoutPage";
import { readAttempt } from "../orders/checkoutAttempt";
import { paymentRequest, type Config } from "./api";
import CulqiCheckoutPage from "./CulqiCheckoutPage";

export default function CheckoutEntry() {
  const [config, setConfig] = useState<Config | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    paymentRequest<Config>("config/", undefined, undefined, controller.signal).then(setConfig).catch(() => {
      if (!controller.signal.aborted) setError("No se pudo consultar la configuración de pagos. Recarga para reintentar.");
    });
    return () => controller.abort();
  }, []);
  if (readAttempt()) return <DemoCheckout />;
  if (!config) return <main className="main-content cart-page"><p role="status">{error || "Consultando medios de pago…"}</p></main>;
  if (!config.enabled) return <DemoCheckout />;
  if (!config.ready) return <main className="main-content cart-page"><h1>Pago en configuración</h1><p>La integración de Culqi todavía no está disponible. Consulta al personal.</p></main>;
  return <CulqiCheckoutPage config={config} />;
}
