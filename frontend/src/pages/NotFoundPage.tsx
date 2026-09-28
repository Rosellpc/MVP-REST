import { Link } from "react-router";

export default function NotFoundPage() {
  return (
    <section>
      <h1>Página no encontrada</h1>

      <p>La dirección que visitaste no existe.</p>

      <Link to="/menu">Volver al menú</Link>
    </section>
  );
}