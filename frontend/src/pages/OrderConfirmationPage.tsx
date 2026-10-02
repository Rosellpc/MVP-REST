import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import Header from "../components/layout/Header";
import { getOrder, type Order } from "../features/orders/orderApi";

export default function OrderConfirmationPage() {
  const { publicCode = "" } = useParams();
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      setLoading(true);
      setError("");
      setOrder(null);
      try {
        const data = await getOrder(publicCode, controller.signal);
        if (!controller.signal.aborted) setOrder(data);
      } catch (err) {
        if (!controller.signal.aborted) setError(err instanceof Error ? err.message : "No se pudo consultar el pedido.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    void load();
    return () => controller.abort();
  }, [publicCode, version]);

  return (
    <div className="app">
      <Header />
      <main className="main-content cart-page">
        <p className="eyebrow">Tu pedido</p>
        {loading ? <p role="status">Consultando confirmación…</p> : error ? (
          <section className="cart-panel">
            <h1>No pudimos consultar el pedido</h1>
            <p role="alert">{error}</p>
            <button className="cart-button" type="button" onClick={() => setVersion((value) => value + 1)}>Reintentar consulta</button>
            <p className="cart-muted">Reintentar aquí solo consulta el pedido; no crea uno nuevo.</p>
          </section>
        ) : order && (
          <section className="cart-panel confirmation-panel">
            <h1>Pedido de demostración registrado</h1>
            <p className="demo-notice">Pago simulado. No se ha realizado ningún cobro ni enviado una preparación a cocina.</p>
            <p>Conserva este enlace para consultar tu confirmación.</p>
            <p className="order-code">{order.public_code}</p>
            <p>{order.fulfillment === "DINE_IN" ? "Consumo en mesa" : "Recoger para llevar"}</p>
            <ul className="checkout-lines">{order.items.map((item) => (
              <li key={item.product_id}><span>{item.quantity} × {item.name}</span><strong>S/ {item.line_total}</strong></li>
            ))}</ul>
            <div className="cart-total"><span>Total · impuestos incluidos</span><strong>S/ {order.total}</strong></div>
            <Link className="cart-button" to="/menu">Volver a la carta</Link>
          </section>
        )}
      </main>
    </div>
  );
}
