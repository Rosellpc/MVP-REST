import { useEffect, useState } from "react";
import { previewOrder, type OrderPayload, type OrderQuote } from "./orderApi";

export function useOrderQuote(items: OrderPayload["items"], enabled: boolean) {
  const [quote, setQuote] = useState<OrderQuote | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);
  const itemKey = JSON.stringify(items);

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    async function load() {
      setLoading(true);
      setError("");
      setQuote(null);
      try {
        const result = await previewOrder(JSON.parse(itemKey), controller.signal);
        if (!controller.signal.aborted) setQuote(result);
      } catch (err) {
        if (!controller.signal.aborted) setError(err instanceof Error ? err.message : "No se pudo verificar el carrito.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    void load();
    return () => controller.abort();
  }, [itemKey, enabled, version]);

  return { quote, loading, error, refresh: () => setVersion((value) => value + 1) };
}
