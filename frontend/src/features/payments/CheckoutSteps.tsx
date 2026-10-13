export default function CheckoutSteps({ payment = false }: { payment?: boolean }) {
  return <nav aria-label="Progreso del pedido" className="checkout-progress">
    <ol>
      <li><span aria-hidden="true">✓</span>Carrito</li>
      <li aria-current={!payment ? "step" : undefined}><span aria-hidden="true">2</span>Datos y resumen</li>
      <li aria-current={payment ? "step" : undefined}><span aria-hidden="true">3</span>Confirmación</li>
    </ol>
  </nav>;
}
