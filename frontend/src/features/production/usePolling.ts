import { useCallback, useEffect, useRef, useState } from "react";

// Serial polling preserves the last successful response during transient failures.
export function usePolling<T>(load: (signal: AbortSignal) => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
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
      try {
        const result = await load(controller.signal);
        if (!stopped) { setData(result); setError(""); setUpdatedAt(new Date()); }
      } catch (err) {
        if (!stopped) setError(err instanceof Error ? err.message : "No se pudo actualizar.");
      } finally {
        controller = null;
        if (!stopped) {
          setLoading(false);
          const delay = queued ? 0 : 5000;
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
  }, [load]);
  return { data, error, loading, updatedAt, refresh };
}
