import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router";
import Header from "../components/layout/Header";
import { useProductDetail } from "../features/catalog/hooks/useProductDetail";
import { useCart } from "../features/cart/CartContext";
import { MAX_QUANTITY } from "../features/cart/cartState";

export default function ProductDetailPage() {
  const { productId = "" } = useParams();
  const [searchParams] = useSearchParams();
  const category = searchParams.get("category");
  const menuUrl = category ? `/menu?category=${encodeURIComponent(category)}` : "/menu";
  const { product, loading, error, notFound, retry } = useProductDetail(productId);
  const { items, addItem } = useCart();
  const [feedback, setFeedback] = useState({ productId: "", message: "" });
  const quantity = items.find((item) => item.productId === product?.id)?.quantity ?? 0;

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0 });
  }, [productId]);

  function handleAdd() {
    if (!product || quantity >= MAX_QUANTITY) return;
    try {
      addItem(product);
      setFeedback({ productId, message: `${product.name} añadido. ${quantity + 1} en tu carrito.` });
    } catch (err) {
      setFeedback({ productId, message: err instanceof Error ? err.message : "No se pudo agregar el producto." });
    }
  }

  return (
    <div className="app">
      <Header />
      <main className="main-content product-detail-page">
        <Link className="catalog-back" to={menuUrl}>← Volver a la carta</Link>
        {loading ? <p role="status">Cargando producto…</p> : error ? (
          <section className="cart-panel">
            <h1>{notFound ? "Producto no disponible" : "No pudimos cargar el producto"}</h1>
            <p role="alert">{error}</p>
            {!notFound && <button className="cart-button" type="button" onClick={retry}>Reintentar</button>}
          </section>
        ) : product && (
          <>
            <section className="product-overview" aria-labelledby="product-name">
              <img className="product-detail-image" src={product.image_url || "/images/menu/table.webp"}
                alt={product.name} onError={(event) => {
                  if (!event.currentTarget.src.endsWith("/images/menu/table.webp")) event.currentTarget.src = "/images/menu/table.webp";
                }} />
              <div className="cart-panel product-purchase">
                <p className="eyebrow">{product.category.name}</p>
                <h1 id="product-name">{product.name}</h1>
                <p className="product-description">{product.description.trim() || "La descripción de este producto aún no está disponible."}</p>
                <p className="product-detail-price">S/ {Number(product.sale_price).toFixed(2)}</p>
                <p className="cart-muted">Precio en soles. Impuestos incluidos.</p>
                <button className="cart-button" type="button" disabled={quantity >= MAX_QUANTITY} onClick={handleAdd}>
                  {quantity >= MAX_QUANTITY ? "Límite alcanzado" : "Añadir al carrito"}
                </button>
                <p role="status" className="product-feedback">{feedback.productId === productId ? feedback.message : ""}</p>
                <Link className="cart-back-link" to="/cart">Ver carrito{quantity > 0 ? ` · ${quantity} de este producto` : ""}</Link>
              </div>
            </section>
            <div className="product-information">
              <section className="cart-panel" aria-labelledby="ingredients-title">
                <h2 id="ingredients-title">Ingredientes</h2>
                <p>{product.ingredients.trim() || "Información de ingredientes no disponible."}</p>
              </section>
              <section className="cart-panel" aria-labelledby="nutrition-title">
                <h2 id="nutrition-title">Información nutricional</h2>
                <p>{product.nutritional_information.trim() || "Información nutricional no disponible."}</p>
              </section>
              <section className="cart-panel" aria-labelledby="allergens-title">
                <h2 id="allergens-title">Alérgenos</h2>
                <p>{product.allergens.trim() || "Información de alérgenos no disponible. Consulta al personal antes de pedir si tienes alguna alergia."}</p>
              </section>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
