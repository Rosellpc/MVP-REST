import { useEffect, useSyncExternalStore } from "react";
import { fetchMenuProducts } from "../api/menuApi";
import { createMenuCache } from "../menuCache";
import { useAvailability } from "./useAvailability";
import { useMemo } from "react";

const cache = createMenuCache(fetchMenuProducts);

export function useMenuProducts() {
  const state = useSyncExternalStore(cache.subscribe, cache.getSnapshot);
  const availability = useAvailability();
  const products = useMemo(() => state.products.map(product => ({ ...product, stock_quantity: availability.data ? (product.id in availability.data ? availability.data[product.id] : 0) : product.stock_quantity })), [state.products, availability.data]);
  useEffect(() => {
    void cache.refresh();
    const onFocus = () => { if (!document.hidden) void cache.refresh(); };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onFocus);
    return () => {
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onFocus);
    };
  }, []);
  return { ...state, products, loading: !state.hasData && !state.error, retry: () => { void cache.refresh(true); availability.refresh(); } };
}
