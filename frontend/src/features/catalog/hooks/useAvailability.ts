import { usePolling } from "../../production/usePolling";

async function load(signal: AbortSignal): Promise<Record<string, number | null>> {
  const response = await fetch("/api/v1/menu/stock/", { signal: AbortSignal.any([signal, AbortSignal.timeout(10000)]), cache: "no-store" });
  if (!response.ok) throw new Error("No se pudo actualizar la disponibilidad.");
  return response.json();
}

// Only quantities are refreshed; photos, descriptions and cached navigation stay intact.
export function useAvailability() { return usePolling(load, 15000); }
