import { useEffect, useState } from "react";
import Header from "../components/layout/Header";
import Hero from "../components/ui/Hero";
import SearchBox from "../components/ui/SearchBox";
import DishesSection from "../components/products/DishesSection";
import { getProductCategories } from "../utils/filterProducts.ts";
import type {
  MenuFilters,
  MenuResponse,
  Product,
} from "../types/menu";

export default function MenuPage() {
  const [filters, setFilters] = useState<MenuFilters>({
    name: "",
    category: "",
  });

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
        const allProducts: Product[] = [];
        let nextUrl: string | null = "/api/v1/menu/";

        // La API entrega hasta 20 productos por página.
        // Seguimos "next" hasta completar la carta.
        while (nextUrl !== null) {
          const response = await fetch(nextUrl, {
            signal: controller.signal,
          });

          if (!response.ok) {
            throw new Error(
              `No se pudo cargar la carta (HTTP ${response.status}).`,
            );
          }

          const data: MenuResponse = await response.json();
          allProducts.push(...data.results);

          if (data.next) {
            const nextPage = new URL(data.next, window.location.origin);

            // Conservamos una URL relativa para pasar por el proxy de Vite.
            nextUrl = nextPage.pathname + nextPage.search;
          } else {
            nextUrl = null;
          }
        }

        if (!controller.signal.aborted) {
          setProducts(allProducts);
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

    // Cancela las solicitudes si el componente se desmonta.
    return () => controller.abort();
  }, [reloadKey]);

  // Genera opciones únicas a partir de la carta completa.
  const categories = getProductCategories(products);

  return (
    <div className="app">
      <Header />

      <main className="main-content">
        <Hero />

        {loading ? (
          <p role="status">Cargando carta...</p>
        ) : error ? (
          <div>
            <p role="alert">{error}</p>
            <button
              type="button"
              onClick={() => setReloadKey((value) => value + 1)}
            >
              Reintentar
            </button>
          </div>
        ) : products.length === 0 ? (
          <p role="status">
            No hay productos disponibles en este momento.
          </p>
        ) : (
          <>
            <SearchBox
              categories={categories}
              appliedFilters={filters}
              onSearch={setFilters}
            />

            <DishesSection
              products={products}
              filters={filters}
            />
          </>
        )}
      </main>
    </div>
  );
}
