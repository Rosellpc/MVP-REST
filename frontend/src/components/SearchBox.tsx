import { useState, type SubmitEvent } from "react";
import type { Category, MenuFilters } from "../types/menu";

type SearchBoxProps = {
  categories: Category[];
  appliedFilters: MenuFilters;
  onSearch: (filters: MenuFilters) => void;
};

export default function SearchBox({
  categories,
  appliedFilters,
  onSearch,
}: SearchBoxProps) {
  // Valores que el usuario está editando.
  const [name, setName] = useState(appliedFilters.name);
  const [category, setCategory] = useState(appliedFilters.category);

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    // Solo al enviar se actualizan los filtros de la lista.
    onSearch({
      name: name.trim(),
      category,
    });
  }

  function handleClear() {
    setName("");
    setCategory("");
    onSearch({ name: "", category: "" });
  }

  const appliedCategory = categories.find(
    (item) => String(item.id) === appliedFilters.category,
  );

  return (
    <>
      <form className="search-box" onSubmit={handleSubmit}>
        <label>
          Buscar platillo
          <input
            type="search"
            placeholder="Ej: Ceviche, Hamburguesa..."
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </label>

        <label>
          Categoría
          <select
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          >
            <option value="">Todas las categorías</option>

            {categories.map((item) => (
              <option key={item.id} value={String(item.id)}>
                {item.name}
              </option>
            ))}
          </select>
        </label>

        <button type="submit">Buscar</button>
        <button type="button" onClick={handleClear}>
          Limpiar
        </button>
      </form>

      <p aria-live="polite">
        Búsqueda aplicada:{" "}
        <strong>{appliedFilters.name || "Todos los productos"}</strong>
        {" · "}
        Categoría:{" "}
        <strong>{appliedCategory?.name || "Todas"}</strong>
      </p>
    </>
  );
}