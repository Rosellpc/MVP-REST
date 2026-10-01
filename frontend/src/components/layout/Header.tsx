import { NavLink } from "react-router";

export default function Header() {
  return (
    <header className="header">
      <h1>Rest-OS</h1>

      <nav aria-label="Navegación principal">
        <NavLink to="/menu">Menú</NavLink>
      </nav>
    </header>
  );
}