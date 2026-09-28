import { Link, Outlet } from "react-router";

export default function CustomerLayout() {
  return (
    <>
      <a href="#contenido-principal">
        Ir al contenido principal
      </a>

      <header>
        <Link to="/menu">RestaurantOS</Link>

        <nav aria-label="Navegación principal">
          <ul>
            <li>
              <Link to="/menu">Menú</Link>
            </li>
          </ul>
        </nav>
      </header>

      <main id="contenido-principal">
        <Outlet />
      </main>

      <footer>
        <p>RestaurantOS · Carta digital</p>
      </footer>
    </>
  );
}