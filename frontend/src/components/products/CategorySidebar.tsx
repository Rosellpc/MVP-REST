import type { Category, Product } from "../../types/menu";

type CategorySidebarProps = {
  categories: Category[];
  products: Product[];
  selectedCategory: string;
  onSelect: (category: string) => void;
};

export default function CategorySidebar({ categories, products, selectedCategory, onSelect }: CategorySidebarProps) {
  const counts = new Map<number, number>();
  for (const product of products) {
    counts.set(product.category.id, (counts.get(product.category.id) ?? 0) + 1);
  }

  return (
    <aside className="category-sidebar" aria-labelledby="category-heading">
      <h2 id="category-heading">Categorías</h2>
      <ul className="category-options">
        <li>
          <button type="button" aria-pressed={selectedCategory === ""} onClick={() => onSelect("")}>
            <span>Toda la carta</span><span className="category-count">{products.length}</span>
          </button>
        </li>
        {categories.map((category) => (
          <li key={category.id}>
            <button type="button" aria-pressed={selectedCategory === String(category.id)}
              onClick={() => onSelect(String(category.id))}>
              <span>{category.name}</span><span className="category-count">{counts.get(category.id) ?? 0}</span>
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
