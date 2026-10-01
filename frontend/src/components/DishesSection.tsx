import DishCard from "./DishCard";
import menuData from "../../../backend/catalog/data/campo_menu.json";

type DishesSectionProps = {
  nameFilter: string;
  categoryFilter: string;
};

// Convierte las categorías del JSON en una sola lista de productos.
// También agrega a cada producto el nombre de la categoría donde aparece.
const DISHES = menuData.categories.flatMap((category) =>
  category.products.map((product) => ({
    ...product,
    category: category.name,
  }))
);

export default function DishesSection({
  nameFilter,
  categoryFilter,
}: DishesSectionProps) {
  // Convierte los términos a minúsculas para que la búsqueda no distinga
  // entre mayúsculas y minúsculas.
  const normalizedName = nameFilter.toLocaleLowerCase();
  const normalizedCategory = categoryFilter.toLocaleLowerCase();

  // Conserva los productos cuyo nombre Y categoría contienen los términos.
  // Si un filtro está vacío, includes("") coincide y no limita resultados.
  const filteredDishes = DISHES.filter(
    (dish) =>
      dish.name.toLocaleLowerCase().includes(normalizedName) &&
      dish.category.toLocaleLowerCase().includes(normalizedCategory)
  );

  return (
    <section className="properties-section">
      <div className="section-title">
        <h3>Destacados</h3>
        <p>Explora nuestras opciones</p>
      </div>

      {/* Muestra un mensaje cuando ninguno coincide con los filtros. */}
      {filteredDishes.length === 0 ? (
        <p role="status">No se encontraron productos con esos filtros.</p>
      ) : (
        <div className="properties-grid">
          {/* Renderiza una tarjeta por cada producto filtrado. */}
          {filteredDishes.map((dish) => (
            <DishCard
              key={dish.sku}
              name={dish.name}
              category={dish.category}
              price={dish.price}
              image_url={dish.image_url}
            />
          ))}
        </div>
      )}
    </section>
  );
}