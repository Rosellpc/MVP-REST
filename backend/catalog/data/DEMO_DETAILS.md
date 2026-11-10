# Información ficticia para practicar con la carta

`catalog/demo_details.py` contiene 72 ejemplos vinculados a SKU y nombre actual.
Cada campo generado declara expresamente que es de demostración. Los ingredientes,
valores nutricionales y alérgenos son ficticios, no una ficha real de las recetas
ni de las marcas comerciales. Los alérgenos se limitan a las 14 categorías de
`catalog.forms.ALLERGENS`; una lista sin categorías no certifica su ausencia.

El comando completa únicamente campos vacíos de productos publicados con categoría
y estación activas, conservando datos existentes. No modifica precios, imágenes,
existencias, recetas de costeo ni pedidos. La correspondencia por nombre evita
aplicar ejemplos de la carta actual a productos distintos del archivo de seed antiguo.

Desde `backend`, usando la base configurada en el entorno:

```bash
python manage.py fill_demo_product_details
python manage.py fill_demo_product_details --apply
```

La primera ejecución solo presenta el plan. Con `--apply`, antes de guardar se crea
un JSON en `.artifacts/catalog-backups/` con los valores anteriores y los aplicados.
La escritura y su comprobación se realizan dentro de una transacción. Repetir el
comando conserva los campos ya completados.

Para restaurar un respaldo específico:

```bash
python manage.py fill_demo_product_details --restore ../.artifacts/catalog-backups/ARCHIVO.json --apply
```

La restauración se cancela si detecta ediciones posteriores en cualquiera de los
campos que intenta restaurar. Los respaldos se conservan localmente fuera de Git.
