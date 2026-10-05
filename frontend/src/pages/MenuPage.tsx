import { useSearchParams, useLocation, useNavigationType } from "react-router";
import { useLayoutEffect, useMemo } from "react";
import { menuPosition } from "../features/catalog/menuScroll";
import Hero from "../components/ui/Hero";
import CategorySidebar from "../components/products/CategorySidebar";
import DishesSection from "../components/products/DishesSection";
import { getProductCategories } from "../utils/filterProducts.ts";
import { useMenuProducts } from "../features/catalog/hooks/useMenuProducts";

export default function MenuPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedCategory = searchParams.get("category") ?? "";

  const { products, loading, error, retry, hasData } = useMenuProducts();
  const location = useLocation();
  const navigationType = useNavigationType();
  useLayoutEffect(() => {
    if (!hasData) return;
    if (location.state?.restoreMenu || navigationType === "POP") {
      window.scrollTo({ top: menuPosition(selectedCategory), behavior: "instant" });
    } else {
      window.scrollTo({ top: 0, behavior: "instant" });
    }
  }, [hasData, location.key, location.state, navigationType, selectedCategory]);

  // Genera opciones únicas a partir de la carta completa.
  const categories = useMemo(() => getProductCategories(products), [products]);
  const selectedName = categories.find((category) => String(category.id) === selectedCategory)?.name;

  function selectCategory(category: string) {
    setSearchParams(category ? { category } : {});
  }

  return (
      <main className="main-content">
        <Hero />
        {error && hasData && <div role="status"><p>No pudimos actualizar la carta. Mostramos la última versión disponible.</p><button type="button" onClick={retry}>Reintentar actualización</button></div>}

        {loading ? (
          <p role="status">Cargando carta...</p>
        ) : error && !hasData ? (
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
          <div className="catalog-layout">
            <CategorySidebar
              categories={categories}
              products={products}
              selectedCategory={selectedCategory}
              onSelect={selectCategory}
            />

            <DishesSection
              products={products}
              filters={{ category: selectedCategory }}
              title={selectedName ?? (selectedCategory ? "Categoría no disponible" : "Nuestra carta")}
            />
          </div>
        )}
      </main>
  );
}
