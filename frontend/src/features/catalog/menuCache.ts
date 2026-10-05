import type { Product } from "../../types/menu";

export function createMenuCache(fetcher: (signal: AbortSignal) => Promise<Product[]>, now = Date.now) {
  let state = { products: [] as Product[], hasData: false, refreshing: false, error: "" };
  let fetchedAt = 0;
  let inFlight: Promise<void> | null = null;
  const listeners = new Set<() => void>();
  const emit = (next: typeof state) => { state = next; listeners.forEach(listener => listener()); };
  return {
    getSnapshot: () => state,
    subscribe: (listener: () => void) => { listeners.add(listener); return () => { listeners.delete(listener); }; },
    refresh(force = false): Promise<void> {
      if (inFlight) return inFlight;
      if (!force && state.hasData && now() - fetchedAt < 60000) return Promise.resolve();
      emit({ ...state, refreshing: true, error: "" });
      inFlight = Promise.resolve().then(() => fetcher(AbortSignal.timeout(15000))).then(products => {
        fetchedAt = now();
        emit({ products, hasData: true, refreshing: false, error: "" });
      }).catch(error => {
        emit({ ...state, refreshing: false, error: error instanceof Error ? error.message : "No se pudo actualizar la carta." });
      }).finally(() => { inFlight = null; });
      return inFlight;
    },
  };
}
