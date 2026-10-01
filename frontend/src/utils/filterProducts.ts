import type { Category, MenuFilters, Product } from "../types/menu";

/**
 * Filtra por nombre y categoría sin modificar la lista original.
 */
export function filterProducts(
  products: Product[],
  filters: MenuFilters,
): Product[] {
  const normalizedName = filters.name.toLocaleLowerCase("es");

  return products.filter((product) => {
    const matchesName = product.name
      .toLocaleLowerCase("es")
      .includes(normalizedName);

    const matchesCategory =
      filters.category === "" ||
      String(product.category.id) === filters.category;

    return matchesName && matchesCategory;
  });
}

/**
 * Obtiene las categorías únicas de la carta completa, ordenadas por nombre.
 */
export function getProductCategories(products: Product[]): Category[] {
  const categories = new Map<Category["id"], Category>();

  for (const product of products) {
    categories.set(product.category.id, product.category);
  }

  return Array.from(categories.values()).sort((a, b) =>
    a.name.localeCompare(b.name, "es"),
  );
}