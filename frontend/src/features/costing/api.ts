import { request } from "../auth/authApi";

export const getCosting = (path: string, signal?: AbortSignal) => request(`costing/${path}/`, { signal });
export async function saveCosting(path: string, body: unknown, method = "POST") {
  const { csrfToken } = await request("auth/csrf/");
  const response = await fetch(`/api/v1/costing/${path}/`, {
    method, credentials: "same-origin", signal: AbortSignal.timeout(path === "recipes/workbook" ? 180000 : 10000),
    headers: body instanceof FormData ? { "X-CSRFToken": csrfToken } : { "Content-Type": "application/json", "X-CSRFToken": csrfToken }, body: body instanceof FormData ? body : JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : JSON.stringify(data));
  return data;
}
export const errorText = (error: unknown) => error instanceof Error ? error.message : "No se pudo completar la operación.";
export function download(name: string, content: string, type = "application/json") {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement("a"); link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function csvCell(value: unknown) {
  let text = String(value ?? "");
  if (/^[\s]*[=+@-]/.test(text)) text = `'${text}`;
  return `"${text.replaceAll('"', '""')}"`;
}
