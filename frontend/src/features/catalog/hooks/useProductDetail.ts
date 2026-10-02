import { useEffect, useState } from "react";
import type { ProductDetail } from "../../../types/menu";
import { fetchProductDetail, ProductNotFoundError } from "../api/menuApi";

export function useProductDetail(id: string) {
  const [state, setState] = useState<{
    id: string; product: ProductDetail | null; loading: boolean; error: string; notFound: boolean;
  }>({ id, product: null, loading: true, error: "", notFound: false });
  const [version, setVersion] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      setState({ id, product: null, loading: true, error: "", notFound: false });
      try {
        const product = await fetchProductDetail(id, controller.signal);
        if (!controller.signal.aborted) setState({ id, product, loading: false, error: "", notFound: false });
      } catch (err) {
        if (!controller.signal.aborted) setState({ id, product: null, loading: false,
          error: err instanceof Error ? err.message : "No se pudo cargar el producto.",
          notFound: err instanceof ProductNotFoundError });
      }
    }
    void load();
    return () => controller.abort();
  }, [id, version]);

  // Evita mostrar el producto anterior al navegar entre dos fichas.
  return {
    product: state.id === id ? state.product : null,
    loading: state.id !== id || state.loading,
    error: state.id === id ? state.error : "",
    notFound: state.id === id && state.notFound,
    retry: () => setVersion((value) => value + 1),
  };
}
