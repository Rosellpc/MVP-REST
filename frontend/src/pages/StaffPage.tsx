import { useEffect, useState } from "react";
import { Link } from "react-router";
import { useAuth } from "../features/auth/useAuth";
import { AuthError, checkArea } from "../features/auth/authApi";

const areas = [
  { name: "Administración", path: "/staff/admin", permission: "accounts.access_staff" },
  { name: "Cocina", path: "/kitchen", permission: "accounts.access_kitchen" },
  { name: "Barra", path: "/bar", permission: "accounts.access_bar" },
];

export function StaffHomePage() {
  const { user } = useAuth();
  return <main className="staff-content"><h1>Mis áreas de trabajo</h1><p>Selecciona un área autorizada para tu cuenta.</p>
    <div className="staff-areas">{areas.filter(a => user?.permissions.includes(a.permission)).map(a => <Link className="staff-panel" key={a.path} to={a.path}>{a.name} ↗</Link>)}</div>
    {!areas.some(a => user?.permissions.includes(a.permission)) && <p>Tu cuenta no tiene áreas asignadas. Contacta al administrador.</p>}
  </main>;
}

export function StaffAreaPage({ area, title }: { area: string; title: string }) {
  const { refresh } = useAuth();
  const [state, setState] = useState({ area: "", error: "", ready: false });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    checkArea(area, controller.signal).then(() => {
      if (!controller.signal.aborted) setState({ area, error: "", ready: true });
    }).catch(error => {
      if (controller.signal.aborted) return;
      setState({ area, error: "No pudimos autorizar el acceso a esta área.", ready: false });
      if (error instanceof AuthError && [401, 403].includes(error.status)) void refresh();
    });
    return () => controller.abort();
  }, [area, attempt, refresh]);
  return <main className="staff-content"><h1>{title}</h1>
    {state.area !== area ? <p role="status">Verificando acceso…</p> : state.error ? <div role="alert"><p>{state.error}</p><button onClick={() => setAttempt(a => a + 1)}>Reintentar</button></div> : state.ready && <section className="staff-panel"><h2>Acceso habilitado</h2><p>{area === "staff" ? "La gestión del catálogo continúa en Django Admin. Esta área está preparada para incorporar las herramientas administrativas." : "Esta área está preparada para incorporar los tickets de preparación. Todavía no recibe ni procesa pedidos."}</p></section>}
  </main>;
}
