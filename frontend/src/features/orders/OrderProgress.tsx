import type { Order } from "./orderApi";
import "../../styles/order-progress.css";

export default function OrderProgress({ status }: { status: Order["production_status"] }) {
  const interrupted = status === "CANCELLED" || status === "PARTIALLY_CANCELLED";
  const step = status === "READY" ? 2 : status === "IN_PROGRESS" ? 1 : status === "PENDING" ? 0 : -1;
  const labels = ["Recibido", "En preparación", "Listo"];
  return <section className="order-tracker" aria-label="Seguimiento del pedido">
    <h2>Estado de tu pedido</h2>
    <ol className="order-tracker__steps">
      {labels.map((label, index) => <li key={label} className={index <= step ? "is-complete" : ""} aria-current={index === step ? "step" : undefined}>
        <span className="order-tracker__dot" aria-hidden="true">{index < step ? "✓" : index + 1}</span>
        <span>{label}</span>
      </li>)}
    </ol>
    <p role="status">{interrupted ? (status === "CANCELLED" ? "Pedido cancelado. Consulta al personal." : "Pedido parcialmente cancelado. Consulta al personal para conocer el detalle.") : step < 0 ? "Pendiente de envío a las estaciones." : step === 2 ? "Todas las estaciones han terminado tu pedido de demostración." : "Actualizamos el estado automáticamente mientras esta página está visible."}</p>
  </section>;
}
