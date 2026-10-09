import { useRef, useState, type FormEvent, type ReactNode } from "react";
import { post } from "../auth/authApi";
import type { StockData, StockRow } from "./types";

function ActionForm({ title, action, payload, children, onDone, onClose }: { title: string; action: string; payload: () => object; children: ReactNode; onDone: () => void; onClose: () => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const attempt = useRef({ content: "", key: "" });
  const sending = useRef(false);
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (sending.current) return;
    const body = payload();
    const content = JSON.stringify(body);
    if (attempt.current.content !== content) attempt.current = { content, key: crypto.randomUUID() };
    sending.current = true; setBusy(true); setError("");
    try { await post(`stock/${action}/`, { ...body, key: attempt.current.key }); onDone(); }
    catch (e) { setError(e instanceof Error ? e.message : "No se pudo guardar."); }
    finally { sending.current = false; setBusy(false); }
  }
  return <section className="stock-panel stock-editor" aria-label={title}><h2>{title}</h2><form onSubmit={submit}><fieldset disabled={busy}>{children}</fieldset>{error && <p role="alert" className="stock-error">{error}</p>}<div className="stock-actions"><button disabled={busy}>{busy ? "Guardando…" : "Confirmar"}</button><button type="button" disabled={busy} onClick={onClose}>Volver sin guardar</button></div></form></section>;
}

export function ShiftForm({ data, mode, onDone, onClose }: { data: StockData; mode: "open" | "close"; onDone: () => void; onClose: () => void }) {
  const [rows, setRows] = useState(data.rows.map(row => ({ product_id: row.product_id, keep: row.quantity ? "" : "0", production: "0", counted: "", reason: "" })));
  const [notes, setNotes] = useState("");
  function change(index: number, field: string, value: string) { setRows(current => current.map((row, i) => i === index ? { ...row, [field]: value } : row)); }
  return <ActionForm title={mode === "open" ? "Apertura y revisión de sobrantes" : "Conteo físico y cierre de turno"} action={mode} onDone={onDone} onClose={onClose} payload={() => ({ revision: data.revision, notes, ...(mode === "close" ? { shift_id: data.shift?.id } : {}), items: rows.map(row => mode === "open" ? { product_id: row.product_id, keep: Number(row.keep), production: Number(row.production), reason: row.reason } : { product_id: row.product_id, counted: Number(row.counted), reason: row.reason }) })}>
    <p>{mode === "open" ? "Confirma las unidades que siguen aptas para servir. Los sobrantes descartados generarán una merma. Registra la producción nueva por separado. Al confirmar se activa el control de venta de todos estos productos." : "Cuenta las unidades reales sin incluir pedidos ya descontados. Justifica cada diferencia. Si hay ventas o movimientos durante el conteo, será necesario volver a cargarlo. El cierre es definitivo y pausa la venta hasta el siguiente turno."}</p>
    <div className="stock-table-wrap"><table><thead><tr><th>Producto</th><th>{mode === "open" ? "Saldo anterior" : "Teórico"}</th><th>{mode === "open" ? "Sobrante apto" : "Conteo físico"}</th>{mode === "open" && <th>Producción nueva</th>}<th>Justificación</th></tr></thead><tbody>{data.rows.map((item, index) => <tr key={item.product_id}><th scope="row">{item.name}<small>{item.sku}</small></th><td>{item.quantity}</td><td><input aria-label={`${mode === "open" ? "Apto" : "Conteo"} ${item.name}`} type="number" min="0" max={mode === "open" ? item.quantity : 1000000} step="1" required value={mode === "open" ? rows[index].keep : rows[index].counted} onChange={e => change(index, mode === "open" ? "keep" : "counted", e.target.value)} /></td>{mode === "open" && <td><input aria-label={`Producción ${item.name}`} required type="number" min="0" max="1000000" step="1" value={rows[index].production} onChange={e => change(index, "production", e.target.value)} /></td>}<td><input aria-label={`Motivo ${item.name}`} maxLength={500} required={Number(mode === "open" ? rows[index].keep : rows[index].counted) !== item.quantity} value={rows[index].reason} onChange={e => change(index, "reason", e.target.value)} placeholder="Caducidad, diferencia, conservación…" /></td></tr>)}</tbody></table></div>
    <label>Observaciones del responsable<textarea maxLength={2000} value={notes} onChange={e => setNotes(e.target.value)} /></label>
    <label className="stock-check"><input type="checkbox" required />{mode === "open" ? "He revisado la aptitud de los sobrantes y las cantidades ingresadas." : "He verificado el conteo físico y las diferencias."}</label>
  </ActionForm>;
}

export function MovementForm({ row, shiftId, onDone, onClose }: { row: StockRow; shiftId: number; onDone: () => void; onClose: () => void }) {
  const [kind, setKind] = useState("PRODUCTION");
  const [quantity, setQuantity] = useState("");
  const [reason, setReason] = useState("");
  return <ActionForm title={`Registrar movimiento · ${row.name}`} action="movements" onDone={onDone} onClose={onClose} payload={() => ({ shift_id: shiftId, product_id: row.product_id, kind, quantity: Number(quantity), reason })}>
    <p>{row.sku} · Saldo al abrir el formulario: {row.quantity} unidades. El servidor valida el saldo vigente al guardar.</p><div className="stock-fields"><label>Movimiento<select value={kind} onChange={e => setKind(e.target.value)}><option value="PRODUCTION">Ingreso de producción</option><option value="WASTE">Merma / caducidad / descarte</option><option value="ADJUST">Ajuste justificado</option></select></label><label>Cantidad{kind === "ADJUST" ? " (+ ingreso / − salida)" : ""}<input required type="number" step="1" min={kind === "ADJUST" ? -1000000 : 1} max={1000000} value={quantity} onChange={e => setQuantity(e.target.value)} /></label></div><label>Motivo y referencia<textarea required maxLength={500} value={reason} onChange={e => setReason(e.target.value)} placeholder="Indica la causa y, si corresponde, el número de pedido." /></label>
    {kind === "ADJUST" && <p>Para devoluciones físicas, confirma antes que el producto siga apto. Una cancelación aprobada ya genera su propio movimiento; evita devolverla dos veces.</p>}
  </ActionForm>;
}
