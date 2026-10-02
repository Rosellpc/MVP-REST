import { useState } from "react";
import Header from "../components/layout/Header";
import Hero from "../components/ui/Hero";
import SearchBox from "../components/ui/SearchBox";
import DishesSection from "../components/products/DishesSection";
import { getProductCategories } from "../utils/filterProducts.ts";
import { useMenuProducts } from "../features/catalog/hooks/useMenuProducts";
import type { MenuFilters } from "../types/menu";

export default function MenuPage() {
  const [filters, setFilters] = useState<MenuFilters>({
    name: "",
    category: "",
  });

  const { products, loading, error, retry } = useMenuProducts();

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
              onClick={retry}
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
