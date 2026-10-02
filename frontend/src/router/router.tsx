import { createBrowserRouter, Navigate } from "react-router";

import MainLayout from "../layouts/MainLayout";

import MenuPage from "../pages/MenuPage";
import ProductDetailPage from "../pages/ProductDetailPage";
import NotFoundPage from "../pages/NotFoundPage";
import CartPage from "../pages/CartPage";
import CheckoutPage from "../pages/CheckoutPage";
import OrderConfirmationPage from "../pages/OrderConfirmationPage";

const router = createBrowserRouter([
    {
        element: <MainLayout />,
        children: [
            { path: "/", element: <Navigate to="/menu" replace /> },
            { path: "/menu", element: <MenuPage /> },
        ],
    },
    { path: "*", element: <NotFoundPage /> },
    { path: "/cart", element: <CartPage /> },
    { path: "/checkout", element: <CheckoutPage /> },
    { path: "/orders/:publicCode", element: <OrderConfirmationPage /> },
    { path: "/menu/:productId", element: <ProductDetailPage /> },



]);

export default router;