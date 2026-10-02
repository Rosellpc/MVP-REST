import { NavLink } from "react-router";
import { useCart } from "../../features/cart/CartContext";

export default function Header() {
  const { itemCount } = useCart();
  return (
    <header className="header">
      <h1>Rest-OS</h1>

      <nav aria-label="Navegación principal">
        <NavLink to="/menu">Menú</NavLink>
        <NavLink to="/cart">Carrito ({itemCount})</NavLink>
      </nav>
    </header>
  );
}
