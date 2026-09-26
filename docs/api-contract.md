# Contrato inicial — API v1 de demostración

## GET /api/v1/health/

Público. 200: `{"status":"ok"}`. Solo disponibilidad del proceso.

## GET /api/v1/menu/

Público, solo lectura. 200:

```json
{
  "demo": true,
  "currency": "PEN",
  "products": [
    {
      "id": "demo-lomo",
      "name": "Lomo saltado",
      "category": "Platos",
      "description": "Descripción de ejemplo",
      "price": "36.00"
    }
  ]
}
```

Excluye productos no publicados o no disponibles. Los importes son texto decimal.
No existe paginación en esta lista fija de cuatro productos; se definirá para el
catálogo persistente. Los IDs demo no son IDs de tablas ni sirven para comprar.

503 con `{"detail":"El catálogo todavía no está habilitado."}` cuando se desactiva
la demostración. Los métodos de escritura no están habilitados.

El resto de endpoints del README sigue siendo una propuesta sin implementación.
