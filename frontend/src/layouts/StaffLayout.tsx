import { useState } from "react";
import { Link, NavLink, Outlet } from "react-router";
import { useAuth } from "../features/auth/useAuth";

export default function StaffLayout() {
  const { user, signOut } = useAuth();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  return <div className="staff-shell">
    <header className="staff-header">
      <Link to="/staff" className="staff-brand" aria-label="Rest-OS, áreas del personal">
        <span>REST-OS</span><span className="staff-brand__caption">Espacio del personal</span>
      </Link>
      <nav aria-label="Áreas del personal"><NavLink to="/staff" end>Áreas</NavLink>
        {user?.permissions.includes("accounts.access_staff") && <NavLink to="/staff/admin">Admin</NavLink>}
        {user?.permissions.includes("accounts.access_kitchen") && <NavLink to="/kitchen">Cocina</NavLink>}
        {user?.permissions.includes("accounts.access_bar") && <NavLink to="/bar">Barra</NavLink>}
      </nav>
      <div className="staff-account">
        <span className="staff-account__avatar" aria-hidden="true">{user?.display_name.trim().slice(0, 1).toLocaleUpperCase() || "P"}</span>
        <div className="staff-account__identity"><span className="staff-account__label">Sesión del personal</span><span className="staff-account__name">{user?.display_name}</span></div>
      <button className="staff-logout" disabled={pending} onClick={async () => {
        setPending(true); setError("");
        try { await signOut(); } catch { setError("No se pudo cerrar la sesión. Inténtalo de nuevo."); }
        finally { setPending(false); }
      }}><svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M9 5H5v14h4M14 8l4 4-4 4M9 12h9" /></svg>{pending ? "Cerrando…" : "Cerrar sesión"}</button>
      </div>
    </header>{error && <p className="staff-header-error" role="alert">{error}</p>}<Outlet />
  </div>;
}
