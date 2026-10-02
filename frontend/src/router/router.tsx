import { createBrowserRouter, Navigate } from "react-router";
import MenuPage from "../pages/MenuPage";
import ProductDetailPage from "../pages/ProductDetailPage";
import NotFoundPage from "../pages/NotFoundPage";
import CartPage from "../pages/CartPage";
import CheckoutPage from "../pages/CheckoutPage";
import OrderConfirmationPage from "../pages/OrderConfirmationPage";

const router = createBrowserRouter([
  { path: "/", element: <Navigate to="/menu" replace /> },
  { path: "/menu", element: <MenuPage /> },
  { path: "/menu/:productId", element: <ProductDetailPage /> },
  { path: "/cart", element: <CartPage /> },
  { path: "/checkout", element: <CheckoutPage /> },
  { path: "/orders/:publicCode", element: <OrderConfirmationPage /> },
  { path: "*", element: <NotFoundPage /> },
]);

export default router;