import { createServer } from "node:http";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";

const API_BASE_URL = (
  process.env.API_BASE_URL || "https://mvp-rest.onrender.com"
).replace(/\/+$/, "");

const PORT = Number(process.env.PORT || 8787);
const MCP_PATH = "/mcp";
const MCP_METHODS = new Set(["POST", "GET", "DELETE"]);
const MCP_RESOURCE_URL = (process.env.MCP_RESOURCE_URL || "https://restos-mcp.onrender.com/mcp").replace(/\/+$/, "");
const AUTH_ISSUER = (process.env.MCP_AUTH_ISSUER || API_BASE_URL).replace(/\/+$/, "");
const RESOURCE_METADATA_URL = `${new URL(MCP_RESOURCE_URL).origin}/.well-known/oauth-protected-resource`;

function authRequired(scope) {
  return {
    isError: true,
    content: [{ type: "text", text: "Conecta tu cuenta de personal de RestaurantOS para consultar estos datos privados." }],
    _meta: {
      "mcp/www_authenticate": [`Bearer resource_metadata="${RESOURCE_METADATA_URL}", scope="${scope}", error="invalid_token", error_description="Connect your RestaurantOS staff account"`],
    },
  };
}

async function getPrivateReport(path, args, authorization, scope) {
  if (!authorization || !/^Bearer [^\s]+$/i.test(authorization) || authorization.length > 4103) {
    return authRequired(scope);
  }
  const url = new URL(path, API_BASE_URL);
  for (const [key, value] of Object.entries(args)) {
    if (value !== undefined) url.searchParams.set(key, value);
  }
  try {
    // Only the two fixed report routes below receive a user's token.
    const response = await fetch(url, {
      headers: { Accept: "application/json", Authorization: authorization },
      redirect: "error",
      signal: AbortSignal.timeout(20000),
      cache: "no-store",
    });
    if (response.status === 401) return authRequired(scope);
    if (!response.ok) {
      const text = response.status === 403
        ? "Tu cuenta o conexión no tiene permiso para este reporte. Revisa el acceso de personal y vuelve a conectar la cuenta."
        : response.status === 400
          ? "Revisa las fechas: usa YYYY-MM-DD, hasta 366 días y sin fechas futuras."
          : "El reporte no está disponible temporalmente. Intenta de nuevo.";
      return { isError: true, content: [{ type: "text", text }] };
    }
    return result(await response.json());
  } catch {
    return { isError: true, content: [{ type: "text", text: "No se pudo consultar el reporte. Intenta de nuevo." }] };
  }
}

class PublicApiError extends Error {
  constructor(status) {
    super("Public API request failed");
    this.status = status;
  }
}

async function getPublicJson(path) {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "GET",
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(12000),
    });
  } catch {
    throw new PublicApiError(503);
  }

  if (!response.ok) {
    throw new PublicApiError(response.status);
  }

  try {
    return await response.json();
  } catch {
    throw new PublicApiError(502);
  }
}

function apiErrorResult(error, notFoundMessage) {
  let message;

  if (error instanceof PublicApiError && error.status === 404) {
    message = notFoundMessage;
  } else if (error instanceof PublicApiError && error.status === 503) {
    message = "La API del menú no está disponible temporalmente.";
  } else {
    // No incluir la respuesta ni detalles internos del backend.
    message = "No se pudo completar la consulta del menú.";
  }

  return {
    isError: true,
    content: [{ type: "text", text: message }],
  };
}

function result(data) {
  return {
    content: [{ type: "text", text: JSON.stringify(data) }],
    structuredContent: data,
  };
}

const categorySchema = z
  .object({
    id: z.number().int(),
    name: z.string(),
  })
  .nullable();

const productSummarySchema = z.object({
  id: z.number().int(),
  name: z.string(),
  description: z.string(),
  image_url: z.string(),
  category: categorySchema,
  sale_price: z.string(),
  stock_quantity: z.number().int().nullable(),
});

const productDetailSchema = productSummarySchema.extend({
  ingredients: z.unknown().optional(),
  nutritional_information: z.unknown().optional(),
  allergens: z.unknown().optional(),
});

const listOutputSchema = {
  count: z.number().int(),
  products: z.array(productSummarySchema),
};

const detailOutputSchema = {
  product: productDetailSchema,
};

const availabilityOutputSchema = {
  id: z.number().int(),
  found: z.boolean(),
  stock_quantity: z.number().int().nullable(),
  available: z.boolean().nullable(),
};

function summarizeProduct(item) {
  const category =
    item.category && typeof item.category === "object"
      ? {
          id: Number(item.category.id),
          name: String(item.category.name ?? ""),
        }
      : null;

  return {
    id: Number(item.id),
    name: String(item.name ?? ""),
    description: String(item.description ?? ""),
    image_url: String(item.image_url ?? ""),
    category,
    sale_price: String(item.sale_price ?? ""),
    stock_quantity: Number.isInteger(item.stock_quantity)
      ? item.stock_quantity
      : null,
  };
}

function createRestaurantServer(authorization) {
  const server = new McpServer({
    name: "restaurantos-menu",
    version: "1.1.0",
  });

  const readOnlyAnnotations = {
    readOnlyHint: true,
    destructiveHint: false,
    openWorldHint: false,
  };

  server.registerTool(
    "listar_productos",
    {
      title: "Listar productos del menú",
      description:
        "Lista los productos públicos del menú. Puede filtrar por texto en nombre, descripción o categoría, y por ID de categoría.",
      inputSchema: {
        q: z.string().trim().max(80).optional(),
        categoriaId: z.number().int().positive().optional(),
      },
      outputSchema: listOutputSchema,
      annotations: readOnlyAnnotations,
      _meta: { securitySchemes: [{ type: "noauth" }] },
    },
    async ({ q, categoriaId }) => {
      try {
        const params = new URLSearchParams();

        if (categoriaId !== undefined) {
          // Django recibe el filtro con el nombre "category".
          params.set("category", String(categoriaId));
        }

        const queryString = params.size ? `?${params.toString()}` : "";
        const data = await getPublicJson(`/api/v1/menu/${queryString}`);
        const apiProducts = Array.isArray(data.results) ? data.results : [];

        const searchText = q?.trim().toLocaleLowerCase("es") || "";

        const products = apiProducts
          .filter((item) => {
            if (!searchText) return true;

            const searchableText = [
              item.name,
              item.description,
              item.category?.name,
            ]
              .filter(Boolean)
              .join(" ")
              .toLocaleLowerCase("es");

            return searchableText.includes(searchText);
          })
          .slice(0, 50)
          .map(summarizeProduct);

        return result({
          count: products.length,
          products,
        });
      } catch (error) {
        return apiErrorResult(
          error,
          "No se pudo encontrar la lista pública de productos."
        );
      }
    }
  );

  server.registerTool(
    "obtener_producto",
    {
      title: "Obtener un producto",
      description:
        "Obtiene los datos públicos de un producto del menú usando su ID.",
      inputSchema: {
        id: z.number().int().positive(),
      },
      outputSchema: detailOutputSchema,
      annotations: readOnlyAnnotations,
      _meta: { securitySchemes: [{ type: "noauth" }] },
    },
    async ({ id }) => {
      try {
        const item = await getPublicJson(`/api/v1/menu/${id}/`);

        const product = {
          ...summarizeProduct(item),
          ...(Object.hasOwn(item, "ingredients")
            ? { ingredients: item.ingredients }
            : {}),
          ...(Object.hasOwn(item, "nutritional_information")
            ? { nutritional_information: item.nutritional_information }
            : {}),
          ...(Object.hasOwn(item, "allergens")
            ? { allergens: item.allergens }
            : {}),
        };

        return result({ product });
      } catch (error) {
        return apiErrorResult(
          error,
          `No existe un producto público con el ID ${id}.`
        );
      }
    }
  );

  server.registerTool(
    "consultar_disponibilidad",
    {
      title: "Consultar disponibilidad",
      description:
        "Consulta la cantidad disponible de un producto publicado en el menú.",
      inputSchema: {
        id: z.number().int().positive(),
      },
      outputSchema: availabilityOutputSchema,
      annotations: readOnlyAnnotations,
      _meta: { securitySchemes: [{ type: "noauth" }] },
    },
    async ({ id }) => {
      try {
        // El endpoint devuelve un objeto como {"1": 12, "2": 0}.
        const stock = await getPublicJson("/api/v1/menu/stock/");
        const key = String(id);

        if (!Object.hasOwn(stock, key)) {
          return {
            isError: true,
            content: [
              {
                type: "text",
                text: `El producto ${id} no está en el menú público.`,
              },
            ],
          };
        }

        const quantity = Number.isInteger(stock[key]) ? stock[key] : null;

        return result({
          id,
          found: true,
          stock_quantity: quantity,
          available:
            quantity === null ? null : quantity > 0,
        });
      } catch (error) {
        return apiErrorResult(
          error,
          "No se pudo consultar la disponibilidad del menú."
        );
      }
    }
  );

  const dateSchema = z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Usa YYYY-MM-DD").optional();
  const periodInput = { start: dateSchema, end: dateSchema };
  for (const tool of [
    {
      name: "consultar_dashboard",
      title: "Consultar dashboard privado",
      description: "Lee los indicadores del dashboard de RestaurantOS: ventas simuladas, comparación del período anterior, tendencia diaria, productos más vendidos, canales, cocina, barra, stock, alertas y costeo. Requiere una cuenta de personal autorizada. start y end son fechas inclusivas YYYY-MM-DD; por defecto consulta los últimos 7 días en America/Lima. Máximo 366 días. Los indicadores operativos actuales no representan un historial del período. No modifica datos.",
      path: "/api/v1/mcp/dashboard/",
      scope: "dashboard:read",
    },
    {
      name: "resumen_ventas",
      title: "Resumen privado de ventas",
      description: "Consulta totales agregados de pedidos de demostración con pago simulado: importe, pedidos válidos, cancelaciones, unidades y ticket promedio. No representa cobros reales. Requiere cuenta de personal. start y end son fechas inclusivas YYYY-MM-DD; por defecto últimos 7 días en America/Lima, máximo 366 días. No devuelve datos de clientes ni modifica datos.",
      path: "/api/v1/mcp/sales/summary/",
      scope: "sales:read",
    },
  ]) {
    server.registerTool(tool.name, {
      title: tool.title,
      description: tool.description,
      inputSchema: periodInput,
      annotations: readOnlyAnnotations,
      _meta: { securitySchemes: [{ type: "oauth2", scopes: [tool.scope] }] },
    }, (args) => getPrivateReport(tool.path, args, authorization, tool.scope));
  }

  return server;
}

const httpServer = createServer(async (req, res) => {
  const url = new URL(req.url || "/", "http://localhost");

  if (req.method === "GET" && ["/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/mcp"].includes(url.pathname)) {
    res.writeHead(200, { "content-type": "application/json", "Access-Control-Allow-Origin": "*" });
    res.end(JSON.stringify({
      resource: MCP_RESOURCE_URL,
      authorization_servers: [AUTH_ISSUER],
      scopes_supported: ["dashboard:read", "sales:read"],
      bearer_methods_supported: ["header"],
    }));
    return;
  }

  if (req.method === "OPTIONS" && url.pathname === MCP_PATH) {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, GET, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "content-type, authorization, mcp-session-id, mcp-protocol-version",
      "Access-Control-Expose-Headers": "Mcp-Session-Id",
    });
    res.end();
    return;
  }

  // Comprobación simple del servidor MCP; no consulta la base de datos.
  if (req.method === "GET" && url.pathname === "/") {
    res.writeHead(200, { "content-type": "text/plain; charset=utf-8" });
    res.end("RestaurantOS MCP server is running");
    return;
  }

  if (url.pathname === MCP_PATH && MCP_METHODS.has(req.method)) {
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Expose-Headers", "Mcp-Session-Id");

    res.setHeader("Cache-Control", "private, no-store");
    const mcpServer = createRestaurantServer(req.headers.authorization);
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
      enableJsonResponse: true,
    });

    res.on("close", () => {
      void transport.close();
      void mcpServer.close();
    });

    try {
      await mcpServer.connect(transport);
      await transport.handleRequest(req, res);
    } catch {
      // Mantener el detalle técnico fuera de la respuesta HTTP.
      if (!res.headersSent) {
        res.writeHead(500, {
          "content-type": "text/plain; charset=utf-8",
        });
        res.end("Internal server error");
      }
    }

    return;
  }

  res.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
  res.end("Not Found");
});

httpServer.listen(PORT, () => {
  console.log(`RestaurantOS MCP escuchando en http://localhost:${PORT}/mcp`);
});
