export default function SearchBox() {
  return (
    <section className="search-box">
      <label>
        Buscar Platillo
        <input type="text" placeholder="Ej: Ceviche, Hamburguesa..." />
      </label>
      <label>
        Categoría
        <input type="text" placeholder="Entradas, Fondos, Postres" />
      </label>
      <label>
        Personas
        <input type="number" placeholder="1" />
      </label>
      <button>Buscar</button>
    </section>
  );
}