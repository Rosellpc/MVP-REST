const DEFAULT_API_BASE_URL = "https://mvp-rest.onrender.com/api";

export default {
  async fetch() {
    const base = new URL(process.env.API_BASE_URL || DEFAULT_API_BASE_URL);
    if (base.protocol !== "https:") {
      return Response.json({ status: "error", detail: "API_BASE_URL must use HTTPS" }, { status: 500 });
    }

    const target = `${base.toString().replace(/\/+$/, "")}/health/`;
    try {
      const upstream = await fetch(target, { cache: "no-store" });
      return new Response(upstream.body, {
        status: upstream.status,
        headers: {
          "content-type": upstream.headers.get("content-type") || "application/json",
          "cache-control": "private, no-store",
        },
      });
    } catch {
      return Response.json({ status: "unavailable" }, { status: 502 });
    }
  },
};
