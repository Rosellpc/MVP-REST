export default function CheckoutSteps({ step = 1 }: { step?: 0 | 1 | 2 }) {
  return <nav aria-label="Progreso del pedido" className="checkout-progress">
    <ol>{["Carrito y entrega", "Pago", "Estado del pedido"].map((label, index) =>
      <li key={label} aria-current={step === index ? "step" : undefined}>
        <span aria-hidden="true">{index < step ? "✓" : index + 1}</span>{label}
      </li>)}</ol>
  </nav>;
}
