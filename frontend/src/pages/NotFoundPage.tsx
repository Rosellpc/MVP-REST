import { Link } from "react-router";
import "../styles/not-found.css";

export default function NotFoundPage() {
  return (
    <main className="not-found" aria-labelledby="not-found-title">
      <section className="not-found__panel">
        <Link
          className="not-found__brand"
          to="/"
          aria-label="Rest-OS — ir al inicio"
        >
          REST-OS
        </Link>

        <p className="not-found__code" aria-hidden="true">
          404
        </p>

        <p className="not-found__eyebrow">Página no encontrada</p>

        <p className="not-found__description">
          El enlace puede haber cambiado o la dirección no existe.
          Vuelve al menú y encuentra tu próximo favorito.
        </p>

        <div className="not-found__actions">
          <Link className="not-found__button" to="/menu">
            Explorar el menú
            <span aria-hidden="true">↗</span>
          </Link>

          <Link className="not-found__secondary" to="/cart">
            Ver mi carrito
          </Link>
        </div>
      </section>
    </main>
  );
}