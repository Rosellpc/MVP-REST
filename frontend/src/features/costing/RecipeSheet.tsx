import { costMoney } from "./types";
import { download } from "./api";
import type { Version } from "./types";
export default function RecipeSheet({ version }: { version: Version }) {
  const r = version.snapshot;
  return <article className="costing-panel costing-sheet"><h2>{r.name} · v{version.number}</h2><p>{r.category || "Sin categoría"} · {r.portions} porciones · {r.portion_size || "Tamaño no definido"}</p><p>Guardada por {version.author} · {new Date(version.created_at).toLocaleString("es-PE")}</p>
    {r.pending_costing && <p className="costing-note">Pendiente de costeo. Completa insumos, cantidades, rendimiento e impuesto al editar esta ficha. El precio final corresponde al menú al momento de la importación; los costos y márgenes aún no están calculados.</p>}
    {r.source_product && <details><summary>Referencia del menú · {r.source_product.sku}</summary><p>{r.source_product.description}</p><p className="costing-prose">Ingredientes declarados, sin cantidades: {r.source_product.declared_ingredients || "No especificados"}</p></details>}
    {r.import_source && <details className="costing-error"><summary>Importada de Excel · revisar supuestos</summary><p>{r.import_source.file} / {r.import_source.sheet} · Costo original: {r.import_source.original_total}</p><ul>{r.import_source.notes.map(note => <li key={note}>{note}</li>)}</ul><p>Tiempo de cocción original: {r.import_source.original_cooking_time || "No indicado"}</p></details>}
    <div className="costing-actions costing-no-print"><button onClick={() => window.print()}>Imprimir / guardar PDF</button><button onClick={() => download(`${r.name}-v${version.number}.json`, JSON.stringify(version, null, 2))}>Exportar ficha JSON</button></div>
    <div className="costing-result costing-fields"><p>Costo total<strong>{costMoney(r.total)}</strong></p><p>Por porción<strong>{costMoney(r.per_portion)}</strong></p></div>
    <p>Precio final: S/ {r.selling_price} · Impuesto incluido: {r.tax_percent === "" ? "Por definir" : `${r.tax_percent}%`} · Venta neta: {costMoney(r.net_price)}</p><p>Margen teórico por porción: {costMoney(r.margin)} · Food cost: {r.food_cost_percent === null ? (r.pending_costing ? "Pendiente de costeo" : "Sin precio de venta") : `${r.food_cost_percent}%`}</p>
    <ul>{r.lines.map((line, i) => <li key={i}>{line.name} · {line.quantity} {line.unit} ({line.basis === "usable" ? "aprovechable" : "bruta"}) · S/ {line.cost}</li>)}</ul>
    <p>Preparación: {r.preparation_minutes === null ? "No especificada" : `${r.preparation_minutes} min`} · Cocción: {r.cooking_minutes === null ? "No especificada" : `${r.cooking_minutes} min`} · Servicio: {r.temperature || "No definido"}</p>
    <h3>Preparación</h3><p className="costing-prose">{r.preparation || "Pendiente de completar"}</p><h3>Presentación</h3><p className="costing-prose">{r.presentation || "Pendiente de completar"}</p><h3>Alérgenos declarados</h3><p>{r.allergens || "Pendientes de revisar"}</p><p>Costos teóricos históricos en PEN. No incluyen mano de obra ni gastos operativos.</p>
  </article>;
}
