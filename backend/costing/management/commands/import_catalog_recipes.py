from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from catalog.models import Product
from costing.models import Recipe, RecipeVersion


class Command(BaseCommand):
    help = "Crea fichas pendientes para productos seleccionados, sin inventar costos."

    def add_arguments(self, parser):
        parser.add_argument("--ids", required=True, help="IDs separados por comas")
        parser.add_argument("--expected-count", type=int, required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            ids = {int(value) for value in options["ids"].split(",")}
        except ValueError as exc:
            raise CommandError("IDs inválidos") from exc
        products = list(Product.objects.select_for_update().filter(pk__in=ids, published=True).select_related("category").order_by("pk"))
        if len(products) != options["expected_count"] or len(products) != len(ids):
            raise CommandError("La selección no coincide con la cantidad de productos publicados esperada.")
        linked = {row.get("source_product", {}).get("id") for row in RecipeVersion.objects.values_list("snapshot", flat=True)}
        names = {name.casefold() for name in Recipe.objects.values_list("name", flat=True)}
        created = 0
        for product in products:
            if product.pk in linked:
                continue
            if product.name.casefold() in names:
                raise CommandError(f"Ya existe una receta sin vínculo para {product.name}. Revisa antes de importar.")
            snapshot = dict(
                name=product.name, category=product.category.name, portions=1,
                portion_size="Una unidad de venta; cantidades por definir",
                preparation_minutes=None, cooking_minutes=None, temperature="",
                preparation="", presentation="", allergens=product.allergens,
                selling_price=str(product.sale_price), tax_percent="", lines=[],
                total=None, per_portion=None, net_price=None, margin=None,
                food_cost_percent=None, currency="PEN", pending_costing=True,
                source_product=dict(id=product.pk, sku=product.sku,
                                    description=product.description,
                                    declared_ingredients=product.ingredients,
                                    nutritional_information=product.nutritional_information),
            )
            recipe = Recipe.objects.create(name=product.name, current_version=1)
            RecipeVersion.objects.create(recipe=recipe, number=1, snapshot=snapshot)
            names.add(product.name.casefold())
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Creadas: {created}; ya vinculadas: {len(products) - created}."))
