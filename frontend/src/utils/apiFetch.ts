/** Sends API calls through Vite's local proxy in development and a fixed
 * same-origin Vercel Function in production. */
export function apiFetch(input: string | URL, init?: RequestInit): Promise<Response> {
  const source = new URL(input.toString(), window.location.origin);

  if (!source.pathname.startsWith("/api/")) {
    return fetch(input, init);
  }

  if (import.meta.env.DEV) {
    // Django may return absolute pagination URLs; route those through Vite too.
    return fetch(new URL(`${source.pathname}${source.search}${source.hash}`, window.location.origin), init);
  }

  const proxy = new URL("/api/proxy", window.location.origin);
  proxy.searchParams.set("path", source.pathname);
  source.searchParams.forEach((value, key) => proxy.searchParams.append(key, value));
  return fetch(proxy, init);
}
