import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router";
import "../../styles/order-farewell.css";

export default function OrderFarewell() {
  const navigate = useNavigate();
  const [stage, setStage] = useState<"delivery" | "thanks">("delivery");
  const [paused, setPaused] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    heading.current?.focus();
  }, [stage]);

  useEffect(() => {
    if (paused) return;
    const timer = window.setTimeout(() => {
      if (stage === "delivery") setStage("thanks");
      else navigate("/menu", { replace: true });
    }, stage === "delivery" ? 8000 : 5000);
    return () => window.clearTimeout(timer);
  }, [stage, paused, navigate]);

  return <main className="order-farewell">
    <section className="order-farewell__panel" aria-labelledby="farewell-title">
      <span className="order-farewell__check" aria-hidden="true">✓</span>
      <p className="eyebrow">{stage === "delivery" ? "Tu pedido está listo" : "Hasta pronto"}</p>
      <h1 id="farewell-title" ref={heading} tabIndex={-1}>
        {stage === "delivery" ? "¡Muchas gracias por tu preferencia!" : "¡Gracias por visitarnos!"}
      </h1>
      <p className="order-farewell__message">
        {stage === "delivery"
          ? "Enseguida, una persona de atención al cliente estará contigo para entregarte tu orden."
          : "Esperamos que disfrutes tu pedido. Vuelve pronto, será un gusto atenderte nuevamente."}
      </p>
      <p className="cart-muted">Demostración: este aviso no representa una entrega real.</p>
      <p className="order-farewell__hint" role="status">
        {paused ? "La continuación automática está pausada." : stage === "delivery" ? "En unos segundos mostraremos nuestra despedida." : "Volveremos automáticamente al menú para el siguiente cliente."}
      </p>
      <div className="order-farewell__actions">
        <button className="cart-button" onClick={() => stage === "delivery" ? setStage("thanks") : navigate("/menu", { replace: true })}>
          {stage === "delivery" ? "Continuar" : "Volver al menú"}
        </button>
        <button className="cart-text-button" onClick={() => setPaused(value => !value)}>
          {paused ? "Reanudar continuación automática" : "Necesito más tiempo"}
        </button>
      </div>
    </section>
  </main>;
}
