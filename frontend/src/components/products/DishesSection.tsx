import DishCard from "./DishCard";
import { filterProducts } from "../../utils/filterProducts.js";
import type { MenuFilters, Product } from "../../types/menu";

type DishesSectionProps = {
  products: Product[];
  filters: MenuFilters;
  title: string;
};

export default function DishesSection({
  products,
  filters,
  title,
}: DishesSectionProps) {
  const filteredProducts = filterProducts(products, filters);

  return (
    <section className="properties-section">
      <div className="section-title">
        <h2>{title}</h2>
        <p role="status">
          {filteredProducts.length} {filteredProducts.length === 1 ? "producto" : "productos"}
        </p>
      </div>

      {filteredProducts.length === 0 ? (
        <p>No hay productos disponibles en esta categoría. Selecciona otra categoría de la barra lateral.</p>
      ) : (
        <div className="properties-grid">
          {filteredProducts.map((product) => (
            <DishCard
              key={product.id}
              product={product}
            />
          ))}
        </div>
      )}
    </section>
  );
}
