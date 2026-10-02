import { useSearchParams } from "react-router";
import Hero from "../components/ui/Hero";
import CategorySidebar from "../components/products/CategorySidebar";
import DishesSection from "../components/products/DishesSection";
import { getProductCategories } from "../utils/filterProducts.ts";
import { useMenuProducts } from "../features/catalog/hooks/useMenuProducts";

export default function MenuPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedCategory = searchParams.get("category") ?? "";

  const { products, loading, error, retry } = useMenuProducts();

  // Genera opciones únicas a partir de la carta completa.
  const categories = getProductCategories(products);
  const selectedName = categories.find((category) => String(category.id) === selectedCategory)?.name;

  function selectCategory(category: string) {
    setSearchParams(category ? { category } : {});
  }

  return (
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
