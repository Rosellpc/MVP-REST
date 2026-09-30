import { Route, Routes } from "react-router";
import MenuPage from "./pages/MenuPage";
import NotFoundPage from "./pages/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MenuPage />} />
      <Route path="*" element={<NotFoundPage />} />
      
    </Routes>
  )
}

