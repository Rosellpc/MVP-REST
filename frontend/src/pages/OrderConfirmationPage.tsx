import OrderProgress from "../features/orders/OrderProgress";
import OrderFarewell from "../features/orders/OrderFarewell";
import { useCallback } from "react";
import { usePolling } from "../features/production/usePolling";
import { Link, useParams } from "react-router";
import { getOrder } from "../features/orders/orderApi";

export default function OrderConfirmationPage() {
  const { publicCode = "" } = useParams();
  return <OrderTracking key={publicCode} publicCode={publicCode} />;
}

function OrderTracking({ publicCode }: { publicCode: string }) {
  const load = useCallback((signal: AbortSignal) => getOrder(publicCode, signal), [publicCode]);
  const { data: order, error, loading, refresh } = usePolling(load);

  if (order?.production_status === "READY") return <OrderFarewell />;


  return (
      <main className="main-content cart-page">
        <p className="eyebrow">Tu pedido</p>
        {loading ? <p role="status">Consultando confirmación…</p> : error && !order ? (
          <section className="cart-panel">
            <h1>No pudimos consultar el pedido</h1>
            <p role="alert">{error}</p>
            <button className="cart-button" type="button" onClick={refresh}>Reintentar consulta</button>
            <p className="cart-muted">Reintentar aquí solo consulta el pedido; no crea uno nuevo.</p>
          </section>
        ) : order && (
          <section className="cart-panel confirmation-panel">
            <h1>Pedido de demostración registrado</h1>
            <p className="demo-notice">Pago y preparación de demostración. No se realizan cobros ni preparaciones reales.</p>
            <OrderProgress status={order.production_status} />
            {error && <p role="alert">{error} Se muestra la última información recibida.</p>}
            <p>Conserva este enlace para consultar tu pedido.</p>
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
  );
}
