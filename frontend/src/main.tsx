import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";

import CartProvider from "./features/cart/CartProvider";
import AuthProvider from "./features/auth/AuthProvider";
import "./styles/staff.css";
import router from "./router/router";
import "./index.css";
import "./styles/checkout.css";
import "./styles/catalog.css";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("No se encontró el elemento raíz de la aplicación.");
}

createRoot(rootElement).render(
  <StrictMode>
    <CartProvider>
      <AuthProvider><RouterProvider router={router} /></AuthProvider>
    </CartProvider>
  </StrictMode>,
);
