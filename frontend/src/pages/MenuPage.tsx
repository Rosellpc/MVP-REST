import "../styles/menu.css";

export default function MenuPage() {
  return (
    <div className="menu-page">
      <header className="menu-hero">
        <p className="menu-eyebrow">
          RESTAURANTOS · CARTA DIGITAL
        </p>

        <h1>Nuestra carta</h1>

        <p className="menu-intro">
          Explora nuestros platos y bebidas.
          Encuentra algo que quieras disfrutar.
        </p>

        <a
          className="menu-button"
          href="#productos-titulo"
        >
          Explorar productos
          <span aria-hidden="true">↗</span>
        </a>
      </header>

      <div className="menu-layout">
        <section
          className="menu-glass menu-categories-panel"
          aria-labelledby="categorias-titulo"
        >
          <div className="menu-section-heading">
            <span className="menu-section-number" aria-hidden="true">
              01
            </span>

            <h2 id="categorias-titulo">
              Categorías
            </h2>
          </div>

          {/* Aquí incorporaremos el selector de categorías. */}
        </section>

        <section
          className="menu-glass menu-products-panel"
          aria-labelledby="productos-titulo"
        >
          <div className="menu-section-heading">
            <span className="menu-section-number" aria-hidden="true">
              02
            </span>

            <h2 id="productos-titulo">
              Productos
            </h2>
          </div>

          {/* Aquí mostraremos los productos del backend. */}

          {/* Aquí incorporaremos los controles de paginación. */}
        </section>
      </div>
    </div>
  );
}