import { Navigate, Route, Routes } from "react-router";

import CustomerLayout from "./layouts/CustomerLayout";
import MenuPage from "./pages/MenuPage";
import NotFoundPage from "./pages/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route element={<CustomerLayout />}>
        <Route
          index
          element={<Navigate to="/menu" replace />}
        />

        <Route
          path="menu"
          element={<MenuPage />}
        />

        <Route
          path="*"
          element={<NotFoundPage />}
        />
      </Route>
    </Routes>
  );
}