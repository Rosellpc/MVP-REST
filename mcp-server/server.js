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

function createRestaurantServer() {
  const server = new McpServer({
    name: "restaurantos-menu",
    version: "1.0.0",
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

  return server;
}

const httpServer = createServer(async (req, res) => {
  const url = new URL(req.url || "/", "http://localhost");

  if (req.method === "OPTIONS" && url.pathname === MCP_PATH) {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, GET, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "content-type, mcp-session-id",
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

    const mcpServer = createRestaurantServer();
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