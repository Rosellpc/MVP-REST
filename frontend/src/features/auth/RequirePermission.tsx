import { Link, Navigate, Outlet } from "react-router";
import { useAuth } from "./useAuth";

export default function RequirePermission({ permission }: { permission?: string }) {
  const { user, loading, error, refresh } = useAuth();
  if (loading) return <main className="staff-state" role="status">Comprobando sesión…</main>;
  if (error) return <main className="staff-state"><p role="alert">{error}</p><button onClick={() => void refresh()}>Reintentar</button></main>;
  if (!user) return <Navigate to="/login" replace />;
  if (permission && !user.permissions.includes(permission)) return <main className="staff-state"><h1>Acceso restringido</h1><p>Tu cuenta no tiene permiso para entrar a esta área.</p><Link to="/staff">Volver a mis áreas</Link></main>;
  return <Outlet />;
}
