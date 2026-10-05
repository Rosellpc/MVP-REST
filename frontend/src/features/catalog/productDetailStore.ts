import { createDetailCache } from "./detailCache";
import { fetchProductDetail, ProductNotFoundError } from "./api/menuApi";

export const productDetailStore = createDetailCache(fetchProductDetail, error => error instanceof ProductNotFoundError);
export function prefetchProduct(id: number) { void productDetailStore.load(String(id)); }
