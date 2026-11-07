import https from "node:https";

const API_ORIGIN = new URL("https://mvp-rest.onrender.com");
const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);

export const config = {
  api: { bodyParser: false },
};

export default function handler(request, response) {
  const incomingUrl = new URL(request.url || "/", "https://vercel.invalid");
  const routePath = request.query?.path;
  const routeSegments = Array.isArray(routePath)
    ? routePath
    : typeof routePath === "string"
      ? [routePath]
      : [];
  const apiPath = routeSegments.length > 0
    ? `/api/${routeSegments.join("/")}${incomingUrl.pathname.endsWith("/") ? "/" : ""}`
    : incomingUrl.pathname.startsWith("/api/")
      ? incomingUrl.pathname
      : `/api${incomingUrl.pathname.startsWith("/") ? "" : "/"}${incomingUrl.pathname}`;
  const upstreamUrl = new URL(
    `${apiPath}${incomingUrl.search}`,
    API_ORIGIN,
  );
  const requestHeaders = { ...request.headers, host: API_ORIGIN.host };

  for (const header of HOP_BY_HOP_HEADERS) {
    delete requestHeaders[header];
  }

  const upstreamRequest = https.request(
    upstreamUrl,
    {
      method: request.method || "GET",
      headers: requestHeaders,
    },
    (upstreamResponse) => {
      const responseHeaders = { ...upstreamResponse.headers };

      for (const header of HOP_BY_HOP_HEADERS) {
        delete responseHeaders[header];
      }

      response.writeHead(upstreamResponse.statusCode || 502, responseHeaders);
      upstreamResponse.pipe(response);
    },
  );

  upstreamRequest.on("error", () => {
    if (!response.headersSent) {
      response.statusCode = 502;
      response.end("API upstream unavailable");
      return;
    }

    response.destroy();
  });

  request.pipe(upstreamRequest);
}
