import DishCard from "./DishCard";
import { filterProducts } from "../../utils/filterProducts.js";
import type { MenuFilters, Product } from "../../types/menu";

type DishesSectionProps = {
  products: Product[];
  filters: MenuFilters;
};

export default function DishesSection({
  products,
  filters,
}: DishesSectionProps) {
  const filteredProducts = filterProducts(products, filters);

  return (
    <section className="properties-section">
      <div className="section-title">
        <h3>Nuestra carta</h3>
        <p role="status">
          {filteredProducts.length} productos encontrados
        </p>
      </div>

      {filteredProducts.length === 0 ? (
        <p>No se encontraron productos con esos filtros.</p>
      ) : (
        <div className="properties-grid">
          {filteredProducts.map((product) => (
            <DishCard
              key={product.id}
              name={product.name}
              category={product.category.name}
              price={product.sale_price}
              image_url={product.image_url}
            />
          ))}
        </div>
      )}
    </section>
  );
}
