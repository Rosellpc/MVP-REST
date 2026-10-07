import { useState } from "react";
import { Link, useSearchParams } from "react-router";
import CostingIcon from "./CostingIcon";
import { useAuth } from "../auth/useAuth";
import "./costing.css";

import CostingWorkspace from "./CostingWorkspace";
import { errorText as message } from "./api";

export default function CostingPage() {
  const { user, loading, signIn, signOut } = useAuth();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const allowed = user?.is_superuser || user?.permissions.includes("costing.use_costing");
  const [params, setParams] = useSearchParams();
  const sections = [["summary", "Resumen"], ["recipes", "Recetario"], ["ingredients", "Insumos"], ["inventory", "Inventario"]];
  const section = sections.find(([key]) => key === params.get("view")) ?? sections[0];
  return <div className={`costing-shell ${user && allowed ? "costing-app" : "costing-access"}`}>
    {user && allowed && <aside className="costing-sidebar costing-no-print"><Link className="costing-brand" to="/costing"><span className="costing-brand-symbol"><CostingIcon name="recipes" /></span><span><strong>REST–OS</strong><small>Cuaderno de costos</small></span></Link><span className="costing-nav-caption">GESTIÓN DE COCINA</span><nav aria-label="Secciones de costeo">{sections.map(([key, label]) => <button key={key} aria-current={section[0] === key ? "page" : undefined} onClick={() => setParams({ view: key })}><CostingIcon name={key} />{label}<span className="costing-nav-arrow">›</span></button>)}</nav><div className="costing-sidebar-tip"><span className="costing-eyebrow">CADA INGREDIENTE CUENTA</span><p>Tu recetario y tus referencias de compra, en un solo lugar.</p></div><div className="costing-profile"><span className="costing-avatar">{user.display_name.slice(0, 2).toUpperCase()}</span><div><strong>{user.display_name}</strong><small>Gestión de costos</small></div></div></aside>}
    <div className="costing-main">
    <header className="costing-header"><div className="costing-breadcrumb"><span>Cuaderno de costos</span><span aria-hidden="true">/</span><strong>{user && allowed ? section[1] : "Acceso"}</strong></div>
      <div className="costing-header-actions"><span className="costing-currency">{section[0] === "inventory" ? "Moneda por conteo" : "PEN · S/"}</span>
      {user && <button disabled={busy} onClick={async () => { setBusy(true); try { await signOut(); } catch (e) { setError(message(e)); } finally { setBusy(false); } }}>Cerrar sesión</button>}
      </div>
    </header>
    <main className="costing-content" id="costing-content">
    {error && <p role="alert" className="costing-error">{error}</p>}
    {loading ? <p role="status">Comprobando acceso…</p> : !user ? <form className="costing-panel costing-login" onSubmit={async (event) => {
      event.preventDefault(); const data = new FormData(event.currentTarget); setBusy(true); setError("");
      try { await signIn(String(data.get("username")), String(data.get("password"))); } catch (e) { setError(message(e)); } finally { setBusy(false); }
    }}><h2>Acceder al laboratorio</h2><p>Usa una cuenta administradora autorizada.</p><label>Usuario<input name="username" autoComplete="username" required /></label><label>Contraseña<input name="password" type="password" autoComplete="current-password" required /></label><button disabled={busy}>{busy ? "Ingresando…" : "Ingresar"}</button></form>
      : allowed ? <CostingWorkspace key={user.id} /> : <p role="alert">Tu cuenta no tiene permiso para gestionar costos. Solicita acceso al administrador.</p>}
    </main></div>
  </div>;
}
