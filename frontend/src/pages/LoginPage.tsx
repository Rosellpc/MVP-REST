import { useState } from "react";
import { Link, Navigate } from "react-router";
import { useAuth } from "../features/auth/useAuth";

export default function LoginPage() {
  const { user, loading, error: sessionError, refresh, signIn } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  if (loading) return <main className="staff-state" role="status">Comprobando sesión…</main>;
  if (user) return <Navigate to="/staff" replace />;
  return <main className="staff-login"><section className="staff-panel">
    <Link to="/menu" className="staff-brand">REST-OS</Link>
    <h1>Acceso del personal</h1><p>Ingresa con la cuenta asignada por administración.</p>
    {sessionError && <div role="alert"><p>{sessionError}</p><button onClick={() => void refresh()}>Comprobar de nuevo</button></div>}
    <form onSubmit={async (event) => {
      event.preventDefault(); if (pending) return;
      setPending(true); setError("");
      try { await signIn(username, password); }
      catch (err) { setError(err instanceof Error ? err.message : "No se pudo iniciar sesión."); }
      finally { setPending(false); setPassword(""); }
    }}>
      <label>Usuario<input autoComplete="username" required maxLength={150} value={username} onChange={e => setUsername(e.target.value)} /></label>
      <label>Contraseña<input type="password" autoComplete="current-password" required maxLength={1024} value={password} onChange={e => setPassword(e.target.value)} /></label>
      {error && <p role="alert">{error}</p>}
      <button disabled={pending}>{pending ? "Ingresando…" : "Iniciar sesión"}</button>
    </form><Link to="/menu">Volver al menú</Link>
  </section></main>;
}
