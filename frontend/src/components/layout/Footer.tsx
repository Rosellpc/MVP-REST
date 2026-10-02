import { Link } from "react-router";
import "../../styles/footer.css";

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="site-footer__container">
        <div className="site-footer__grid">
          <div className="site-footer__identity">
            <Link
              className="site-footer__brand"
              to="/"
              aria-label="Rest-OS — ir al inicio"
            >
              REST-OS
            </Link>

            <p className="site-footer__tagline">
              Tu pedido, a tu ritmo.
            </p>

            <p className="site-footer__description">
              Explora la carta, elige tus favoritos y organiza tu
              pedido desde una sola experiencia de autoservicio.
            </p>
          </div>

          <nav
            className="site-footer__section"
            aria-labelledby="footer-navigation-title"
          >
            <h2 id="footer-navigation-title">Explora</h2>

            <ul className="site-footer__links">
              <li>
                <Link to="/menu">Nuestra carta</Link>
              </li>
              <li>
                <Link to="/cart">Mi carrito</Link>
              </li>
            </ul>
          </nav>

          <div className="site-footer__section">
            <h2>A tu manera</h2>

            <ul className="site-footer__services">
              <li>Para consumir en mesa</li>
              <li>Para recoger</li>
            </ul>

            <p className="site-footer__currency">
              Precios en soles (PEN), con impuestos incluidos.
            </p>
          </div>
        </div>

        <div className="site-footer__notice">
          <span className="site-footer__badge">Demostración</span>

          <p>
            Los pedidos y el pago forman parte de una demostración.
            No se realizan cobros ni se envían pedidos a preparación.
          </p>
        </div>

        <div className="site-footer__bottom">
          <p>© {new Date().getFullYear()} RestaurantOS</p>
          <p>Autoservicio para restaurantes.</p>
        </div>
      </div>
    </footer>
  );
}