import type { ProductDetail } from "../../types/menu";

export function createDetailCache(fetcher: (id: string, signal: AbortSignal) => Promise<ProductDetail>, isNotFound: (error: unknown) => boolean, now = Date.now) {
  type State = { product: ProductDetail | null; loading: boolean; error: string; notFound: boolean };
  const entries = new Map<string, { state: State; at: number; pending: Promise<void> | null }>();
  const listeners = new Set<() => void>();
  function entry(id: string) {
    let value = entries.get(id);
    if (!value) {
      value = { state: { product: null, loading: true, error: "", notFound: false }, at: 0, pending: null };
      entries.set(id, value);
    }
    return value;
  }
  return {
    subscribe(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener); }; },
    snapshot(id: string) { return entry(id).state; },
    load(id: string, force = false): Promise<void> {
      const value = entry(id);
      if (value.pending) return value.pending;
      if (!force && value.state.product && now() - value.at < 60000) return Promise.resolve();
      value.pending = Promise.resolve().then(() => fetcher(id, AbortSignal.timeout(10000))).then(product => {
        value.at = now();
        value.state = { product, loading: false, error: "", notFound: false };
      }).catch(error => {
        const notFound = isNotFound(error);
        value.state = { product: notFound ? null : value.state.product, loading: false, notFound,
          error: error instanceof Error ? error.message : "No se pudo cargar el producto." };
      }).finally(() => {
        value.pending = null;
        listeners.forEach(listener => listener());
      });
      return value.pending;
    },
  };
}
