import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { AuthContext } from "./AuthContext";
import { getSession, login, logout, type StaffUser } from "./authApi";

export default function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<StaffUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const generation = useRef(0);
  const refresh = useCallback(async () => {
    const current = ++generation.current;
    setLoading(true);
    setError("");
    try {
      const session = await getSession();
      if (current === generation.current) setUser(session);
    } catch {
      if (current === generation.current) setError("No pudimos comprobar tu sesión. Revisa la conexión e inténtalo de nuevo.");
    } finally {
      if (current === generation.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    const current = ++generation.current;
    getSession().then(session => {
      if (!cancelled && current === generation.current) setUser(session);
    }).catch(() => {
      if (!cancelled && current === generation.current) setError("No pudimos comprobar tu sesión. Revisa la conexión e inténtalo de nuevo.");
    }).finally(() => {
      if (!cancelled && current === generation.current) setLoading(false);
    });
    const onFocus = () => { void refresh(); };
    window.addEventListener("focus", onFocus);
    return () => { cancelled = true; window.removeEventListener("focus", onFocus); };
  }, [refresh]);

  async function signIn(username: string, password: string) {
    ++generation.current;
    const session = await login(username, password);
    ++generation.current;
    setUser(session); setError(""); setLoading(false);
  }
  async function signOut() {
    await logout();
    ++generation.current;
    setUser(null); setError(""); setLoading(false);
  }
  return <AuthContext.Provider value={{ user, loading, error, refresh, signIn, signOut }}>{children}</AuthContext.Provider>;
}
