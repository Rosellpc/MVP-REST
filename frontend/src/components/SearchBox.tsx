import { useState, type SubmitEvent } from "react";

type SearchBoxProps = {
  onSearch: (filters: { name: string; category: string}) => void;
};

export default function SearchBox({onSearch}: SearchBoxProps) {
  // Estado local para controlar lo que se escribe en cada campo.
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    // Evita que el navegador recargue la página al enviar el formulario.
    event.preventDefault();

    // Envía los valores al componente padre
    // trim() quita espacios accidentales al principio y al final.
    onSearch({
      name: name.trim(),
      category: category.trim(),
    });
  }

  function handleclear() {
    setName("");
    setCategory("");

    // Quita los filtros aplicados en el componente padre.
    onSearch({ name: "", category: ""});
  }

  return (
    <>
      <form className="search-box" onSubmit={handleSubmit}>
        <label>
          Buscar platillo
          <input
            type="text"
            placeholder="Ej: Ceviche, Hamburguesa..."
            value={name}
            // Actualiza el estado local conforme se escribe.
            onChange={(event) => setName(event.target.value)}
          />
        </label>

        <label>
          Categoría
          <input 
            type="text" 
            placeholder="Entradas, Fondos, Postres" 
            value={category} 
            // Cuarda el texto de categoría para enviarlo al pulsar Buscar.
            onChange={(event) => setCategory(event.target.value)}
          />
        </label>


        <button type="submit">Buscar</button>
        <button type="button" onClick={handleclear}>X</button>
      </form>

      <p className="search-box box-state" aria-live="polite">
        Búsqueda: <strong>{name || "Sin búsqueda"}</strong>
      </p>
    </>
  );
}