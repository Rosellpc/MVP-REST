import { useEffect, useSyncExternalStore } from "react";
import { fetchMenuProducts } from "../api/menuApi";
import { createMenuCache } from "../menuCache";

const cache = createMenuCache(fetchMenuProducts);

export function useMenuProducts() {
  const state = useSyncExternalStore(cache.subscribe, cache.getSnapshot);
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
  return { ...state, loading: !state.hasData && !state.error, retry: () => { void cache.refresh(true); } };
}
