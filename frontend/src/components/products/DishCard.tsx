import { Link, useSearchParams } from "react-router";
import type { Product } from "../../types/menu";
import { rememberMenuPosition } from "../../features/catalog/menuScroll";
import { prefetchProduct } from "../../features/catalog/productDetailStore";

export default function DishCard({ product }: { product: Product }) {
  const [searchParams] = useSearchParams();
  const category = searchParams.get("category");
  const query = category ? `?category=${encodeURIComponent(category)}` : "";

  return (
    <article className="property-card">
      <Link className="product-card-link" onMouseEnter={() => prefetchProduct(product.id)} onFocus={() => prefetchProduct(product.id)} onPointerDown={() => prefetchProduct(product.id)} onClick={() => rememberMenuPosition(category ?? "")} to={`/menu/${product.id}${query}`} aria-label={`Ver detalles de ${product.name}`}>
      <img src={product.image_url || "/images/menu/table.webp"} alt={product.name} loading="lazy" />
      <div className="property-card-content">
        <h3>{product.name}</h3>
        <p>{product.category.name || "Sin categoría"}</p>
        <strong>S/ {Number(product.sale_price).toFixed(2)}</strong>
        {product.stock_quantity === 0 && <p>Agotado / no disponible en este turno</p>}
        <span className="product-card-cta">Ver producto <span aria-hidden="true">↗</span></span>
      </div>
      </Link>
    </article>
  );
}

