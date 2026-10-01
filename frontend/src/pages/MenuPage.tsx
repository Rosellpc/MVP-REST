import { useState } from "react";
import Header from "../components/Header";
import Hero from "../components/Hero";
import SearchBox from "../components/SearchBox";
import DishesSection from "../components/DishesSection";

export default function MenuPage() {
  // El componente padre guarda los filtros que se usarán para buscar.
  // Ambos empiezan vacíos, por lo que inicialmente no se restringen resultados.
  const [filters, setFilters] = useState({
    name: "",
    category: "",
  });

  return (
    <div className="app">
      <Header />
      <main className="main-content">
        <Hero />

        {/* SearchBox envía los valores al estado de MenuPage. */}
        <SearchBox onSearch={setFilters} />

        {/* DishesSection recibe los filtros y decide qué productos mostrar. */}
        <DishesSection
          nameFilter={filters.name}
          categoryFilter={filters.category}
        />
      </main>
    </div>
  );
}