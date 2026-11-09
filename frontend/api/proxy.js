const DEFAULT_API_BASE_URL = "https://mvp-rest.onrender.com/api";
const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "host",
  "content-length",
]);

export default {
  async fetch(request) {
    const incoming = new URL(request.url);
    const apiPath = incoming.searchParams.get("path");

    if (!apiPath || !apiPath.startsWith("/api/") || apiPath.includes("..") || apiPath.includes("\\")) {
      return new Response("Invalid API path", { status: 400 });
    }

    const base = new URL(process.env.API_BASE_URL || DEFAULT_API_BASE_URL);
    if (!/^https:$/.test(base.protocol)) {
      return new Response("API_BASE_URL must use HTTPS", { status: 500 });
    }
    base.pathname = `${base.pathname.replace(/\/+$/, "")}/`;
    base.search = "";
    base.hash = "";

    incoming.searchParams.delete("path");
    const relativePath = apiPath.slice("/api/".length);
    const target = new URL(`${relativePath}${incoming.search}`, base);
    if (target.origin !== base.origin || !target.pathname.startsWith(base.pathname)) {
      return new Response("Invalid API path", { status: 400 });
    }

    const headers = new Headers(request.headers);
    for (const name of HOP_BY_HOP_HEADERS) headers.delete(name);

    try {
      const upstream = await fetch(target, {
        method: request.method,
        headers,
        body: ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer(),
        redirect: "follow",
        cache: "no-store",
      });

      const responseHeaders = new Headers();
      for (const name of ["content-type", "cache-control", "content-disposition", "vary", "location"]) {
        const value = upstream.headers.get(name);
        if (value) responseHeaders.set(name, value);
      }
      responseHeaders.set("cache-control", "private, no-store");
      for (const cookie of upstream.headers.getSetCookie?.() ?? []) {
        responseHeaders.append("set-cookie", cookie);
      }

      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers: responseHeaders,
      });
    } catch {
      return Response.json({ detail: "No se pudo conectar con el servicio API." }, { status: 502 });
    }
  },
};
