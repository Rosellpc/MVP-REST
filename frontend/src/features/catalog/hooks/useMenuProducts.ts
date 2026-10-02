import { useEffect, useState } from "react";
import type { Product } from "../../../types/menu";
import { fetchMenuProducts } from "../api/menuApi";

/** Gestiona el ciclo de carga de la carta, sus errores y los reintentos. */
export function useMenuProducts() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadProducts() {
      setLoading(true);
      setError("");

      try {
        const data = await fetchMenuProducts(controller.signal);

        if (!controller.signal.aborted) {
          setProducts(data);
        }
      } catch (err) {
        if (controller.signal.aborted) return;

        setError(
          err instanceof Error
            ? err.message
            : "Ocurrió un error al cargar la carta.",
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadProducts();

    // Una solicitud anterior no debe actualizar el estado tras cancelarse.
    return () => controller.abort();
  }, [reloadKey]);

  function retry() {
    setReloadKey((value) => value + 1);
  }

  return { products, loading, error, retry };
}
