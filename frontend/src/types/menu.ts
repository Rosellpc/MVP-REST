export type Category = {
  id: number;
  name: string;
};

// Coincide con los campos que devuelve Django.
export type Product = {
  id: number;
  name: string;
  description: string;
  image_url: string;
  sale_price: string;
  category: Category;
};

export type MenuResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Product[];
};

export type MenuFilters = {
  name: string;
  category: string; // ID de categoría; "" significa todas.
};