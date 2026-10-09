import { useEffect, useSyncExternalStore } from "react";
import { productDetailStore } from "../productDetailStore";
import { useAvailability } from "./useAvailability";

export function useProductDetail(id: string) {
  const state = useSyncExternalStore(productDetailStore.subscribe, () => productDetailStore.snapshot(id));
  const availability = useAvailability();
  useEffect(() => {
    void productDetailStore.load(id);
    const focus = () => { if (!document.hidden) void productDetailStore.load(id); };
    window.addEventListener("focus", focus);
    return () => window.removeEventListener("focus", focus);
  }, [id]);
  const product = state.product && availability.data ? { ...state.product, stock_quantity: id in availability.data ? availability.data[id] : 0 } : state.product;
  return { ...state, product, retry: () => { void productDetailStore.load(id, true); availability.refresh(); } };
}
