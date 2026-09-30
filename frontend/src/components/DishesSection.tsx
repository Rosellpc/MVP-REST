import DishCard from "./DishCard";
import menuData from "../../../backend/catalog/data/campo_menu.json";

const DISHES = menuData.categories.flatMap((category) =>
  category.products.map((product) => ({
    ...product,
    category: category.name,
  }))
);

export default function DishesSection() {
  return (
    <section className="properties-section">
      <div className="section-title">
        <h3>Destacados</h3>
        <p>Explore la mejor opción para ti</p>
      </div>

      <div className="properties-grid">
        {DISHES.map((dish) => (
          <DishCard
            key={dish.sku}
            name={dish.name}
            category={dish.category}
            price={dish.price}
            image_url={dish.image_url}
          />
        ))}
      </div>
    </section>
  );
}