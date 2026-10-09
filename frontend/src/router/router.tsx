import { createBrowserRouter, Navigate } from "react-router";

import MainLayout from "../layouts/MainLayout";
import StaffLayout from "../layouts/StaffLayout";
import RequirePermission from "../features/auth/RequirePermission";
import LoginPage from "../pages/LoginPage";
import CostingPage from "../features/costing/CostingPage";
import StockPage from "../features/stock/StockPage";
import ProductionBoard from "../features/production/ProductionBoard";
import { StaffHomePage } from "../pages/StaffPage";
import ReleaseOrders from "../features/production/AdminOrderHistory";

import MenuPage from "../pages/MenuPage";
import ProductDetailPage from "../pages/ProductDetailPage";
import NotFoundPage from "../pages/NotFoundPage";
import CartPage from "../pages/CartPage";
import CheckoutPage from "../pages/CheckoutPage";
import OrderConfirmationPage from "../pages/OrderConfirmationPage";

const router = createBrowserRouter([
    { path: "/costing", element: <CostingPage /> },
    {
        element: <MainLayout />,
        children: [
            { path: "/", element: <Navigate to="/menu" replace /> },
            { path: "/menu", element: <MenuPage /> },
            { path: "/cart", element: <CartPage /> },
            { path: "/checkout", element: <CheckoutPage /> },
            { path: "/orders/:publicCode", element: <OrderConfirmationPage /> },
            { path: "/menu/:productId", element: <ProductDetailPage /> },
        ],
    },
    { path: "*", element: <NotFoundPage /> },
    { path: "/login", element: <LoginPage /> },
    { element: <RequirePermission />, children: [
        { element: <StaffLayout />, children: [
            { path: "/staff", element: <StaffHomePage /> },
            { element: <RequirePermission permission="stock.view_stock" />, children: [
                { path: "/stock", element: <StockPage /> },
            ] },
            { element: <RequirePermission permission="accounts.access_staff" />, children: [
                { path: "/staff/admin", element: <ReleaseOrders /> },
            ] },
            { element: <RequirePermission permission="accounts.access_kitchen" />, children: [
                { path: "/kitchen", element: <ProductionBoard key="kitchen" station="KITCHEN" /> },
            ] },
            { element: <RequirePermission permission="accounts.access_bar" />, children: [
                { path: "/bar", element: <ProductionBoard key="bar" station="BAR" /> },
            ] },
        ] },
    ] },



]);

export default router;
