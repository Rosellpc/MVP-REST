import type { MenuResponse, Product, ProductDetail } from "../../../types/menu";

export class ProductNotFoundError extends Error {
  constructor() {
    super("Este producto no existe o ya no está disponible en la carta.");
  }
}

export async function fetchProductDetail(id: string, signal: AbortSignal): Promise<ProductDetail> {
  if (!/^[1-9]\d*$/.test(id)) throw new ProductNotFoundError();
  const response = await fetch(`/api/v1/menu/${encodeURIComponent(id)}/`, { signal });
  if (response.status === 404) throw new ProductNotFoundError();
  if (!response.ok) throw new Error(`No se pudo cargar el producto (HTTP ${response.status}).`);
  return response.json();
}

/** Carga la carta completa para que los filtros incluyan todas las páginas. */
export async function fetchMenuProducts(signal: AbortSignal): Promise<Product[]> {
  const products: Product[] = [];
  let nextUrl: string | null = "/api/v1/menu/";

  while (nextUrl !== null) {
    const response = await fetch(nextUrl, { signal });

    if (!response.ok) {
      throw new Error(
        `No se pudo cargar la carta (HTTP ${response.status}).`,
      );
    }

    const data: MenuResponse = await response.json();
    products.push(...data.results);

    if (data.next) {
      const nextPage = new URL(data.next, window.location.origin);
      // Conserva el proxy de /api aunque Django devuelva una URL absoluta.
      nextUrl = nextPage.pathname + nextPage.search;
    } else {
      nextUrl = null;
    }
  }

  return products;
}
