import { useState } from "react";
import { pen, type Dashboard } from "./types";

export default function SalesChart({ rows }: { rows: Dashboard["trend"] }) {
  const [selected, setSelected] = useState<number | null>(null);
  const index = selected === null ? rows.length - 1 : Math.min(selected, rows.length - 1);
  const row = rows[index];
  const max = Math.max(1, ...rows.map(item => Number(item.amount)));
  const x = (i: number) => rows.length === 1 ? 320 : 30 + i / (rows.length - 1) * 580;
  const y = (amount: string) => 185 - Number(amount) / max * 150;
  const points = rows.map((item, i) => `${x(i)},${y(item.amount)}`).join(" ");
  return <section className="dashboard-panel dashboard-trend"><div className="dashboard-section-title"><div><span className="dashboard-eyebrow">EVOLUCIÓN DIARIA</span><h2>Pedidos en cifras</h2></div><span>PEN · demostración</span></div>
    <p aria-live="polite">{row?.date} · <strong>{pen(row?.amount ?? "0")}</strong> · {row?.orders ?? 0} pedidos</p>
    <svg viewBox="0 0 640 220" role="img" aria-label="Importe diario de pedidos no cancelados. Consulta los valores en la tabla inferior." onPointerMove={e => { const rect = e.currentTarget.getBoundingClientRect(); const position = (e.clientX - rect.left) / rect.width * 640; setSelected(Math.max(0, Math.min(rows.length - 1, Math.round((position - 30) / 580 * (rows.length - 1))))); }}>
      {[35, 85, 135, 185].map(value => <line key={value} x1="30" x2="610" y1={value} y2={value} stroke="#ffffff15" />)}
      <text x="30" y="22" fill="#bcc6c0" fontSize="11">{pen(String(max))}</text>
      <polygon points={`30,185 ${points} 610,185`} fill="#87bba112" />
      <polyline points={points} fill="none" stroke="#a8d7bf" strokeWidth="3" strokeLinejoin="round" />
      {row && <circle cx={x(index)} cy={y(row.amount)} r="5" fill="#d1f2df" />}
      <text x="30" y="211" fill="#bcc6c0" fontSize="11">{rows[0]?.date}</text><text x="610" y="211" textAnchor="end" fill="#bcc6c0" fontSize="11">{rows.at(-1)?.date}</text>
    </svg><label className="dashboard-chart-select">Explorar día<select value={index} onChange={e => setSelected(Number(e.target.value))}>{rows.map((r, i) => <option key={r.date} value={i}>{r.date}</option>)}</select></label>
    <details><summary>Ver datos de la gráfica</summary><div className="dashboard-table-wrap"><table><thead><tr><th>Fecha</th><th>Pedidos</th><th>Importe demo</th></tr></thead><tbody>{rows.map(item => <tr key={item.date}><td>{item.date}</td><td>{item.orders}</td><td>{pen(item.amount)}</td></tr>)}</tbody></table></div></details>
  </section>;
}
