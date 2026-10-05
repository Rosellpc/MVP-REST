import { useState } from "react";
import { Link, NavLink, Outlet } from "react-router";
import { useAuth } from "../features/auth/useAuth";

export default function StaffLayout() {
  const { user, signOut } = useAuth();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  return <div className="staff-shell">
    <header className="staff-header"><Link to="/staff" className="staff-brand">REST-OS · PERSONAL</Link>
      <nav aria-label="Áreas del personal"><NavLink to="/staff" end>Mis áreas</NavLink>
        {user?.permissions.includes("accounts.access_staff") && <NavLink to="/staff/admin">Administración</NavLink>}
        {user?.permissions.includes("accounts.access_kitchen") && <NavLink to="/kitchen">Cocina</NavLink>}
        {user?.permissions.includes("accounts.access_bar") && <NavLink to="/bar">Barra</NavLink>}
      </nav><span>{user?.display_name}</span>
      <button disabled={pending} onClick={async () => {
        setPending(true); setError("");
        try { await signOut(); } catch { setError("No se pudo cerrar la sesión. Inténtalo de nuevo."); }
        finally { setPending(false); }
      }}>{pending ? "Cerrando…" : "Cerrar sesión"}</button>
    </header>{error && <p role="alert">{error}</p>}<Outlet />
  </div>;
}
