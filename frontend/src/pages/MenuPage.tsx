export default function MenuPage() {
  return (
    <>
      <header>
        <h1>Nuestra carta</h1>
        <p>Explora nuestros platos y bebidas.</p>
      </header>

      <section aria-labelledby="categorias-titulo">
        <h2 id="categorias-titulo">Categorías</h2>

        {/* Aquí incorporaremos el selector de categorías. */}
      </section>

      <section aria-labelledby="productos-titulo">
        <h2 id="productos-titulo">Productos</h2>

        {/* Aquí mostraremos los productos del backend. */}

        {/* Aquí incorporaremos los controles de paginación. */}
      </section>
    </>
  );
}