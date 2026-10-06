import { useCallback, useEffect, useRef, useState } from "react";

// Serial polling preserves the last successful response during transient failures.
export function usePolling<T>(load: (signal: AbortSignal) => Promise<T>, interval = 5000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const refreshRef = useRef<() => void>(() => {});
  const refresh = useCallback(() => refreshRef.current(), []);
  useEffect(() => {
    let stopped = false;
    let controller: AbortController | null = null;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let queued = false;
    async function run() {
      if (stopped || document.hidden) return;
      if (controller) { queued = true; return; }
      clearTimeout(timer);
      controller = new AbortController();
      // Defer notification so initial subscription does not synchronously render.
      await Promise.resolve();
      if (stopped) return;
      setRefreshing(true);
      try {
        const result = await load(controller.signal);
        if (!stopped) { setData(result); setError(""); setUpdatedAt(new Date()); }
      } catch (err) {
        if (!stopped) setError(err instanceof Error ? err.message : "No se pudo actualizar.");
      } finally {
        controller = null;
        if (!stopped) {
          setLoading(false);
          setRefreshing(false);
          const delay = queued ? 0 : interval;
          queued = false;
          timer = setTimeout(() => void run(), delay);
        }
      }
    }
    const visibility = () => { if (!document.hidden) void run(); else clearTimeout(timer); };
    refreshRef.current = () => { void run(); };
    document.addEventListener("visibilitychange", visibility);
    void run();
    return () => { stopped = true; controller?.abort(); clearTimeout(timer); document.removeEventListener("visibilitychange", visibility); };
  }, [load, interval]);
  const update = useCallback((change: (current: T | null) => T | null) => setData(change), []);
  return { data, error, loading, refreshing, updatedAt, refresh, update };
}
