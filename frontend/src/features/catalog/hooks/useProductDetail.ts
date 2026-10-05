import { useEffect, useSyncExternalStore } from "react";
import { productDetailStore } from "../productDetailStore";

export function useProductDetail(id: string) {
  const state = useSyncExternalStore(productDetailStore.subscribe, () => productDetailStore.snapshot(id));
  useEffect(() => {
    void productDetailStore.load(id);
    const focus = () => { if (!document.hidden) void productDetailStore.load(id); };
    window.addEventListener("focus", focus);
    return () => window.removeEventListener("focus", focus);
  }, [id]);
  return { ...state, retry: () => { void productDetailStore.load(id, true); } };
}
