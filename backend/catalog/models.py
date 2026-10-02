from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(
        "nombre",
        max_length=100,
        unique=True,
    )
    display_order = models.PositiveIntegerField(
        "orden de visualización",
        default=0,
    )
    active = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class Station(models.Model):
    class Code(models.TextChoices):
        KITCHEN = "KITCHEN", "Cocina"
        BAR = "BAR", "Barra"
        DELIVERY = "DELIVERY", "Entrega"

    code = models.CharField(
        "código",
        max_length=20,
        choices=Code.choices,
        unique=True,
    )
    name = models.CharField("nombre", max_length=100)
    active = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "estación de preparación"
        verbose_name_plural = "estaciones de preparación"
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    code__in=["KITCHEN", "BAR", "DELIVERY"]
                ),
                name="catalog_station_valid_code",
            ),
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    sku = models.CharField(
        "SKU",
        max_length=50,
        unique=True,
        help_text="Código único del producto. Ejemplo: PROD-001.",
    )
    name = models.CharField("nombre", max_length=150)
    description = models.TextField("descripción", blank=True)
    ingredients = models.TextField(
        "ingredientes", blank=True, default="",
        help_text="Ingredientes declarados por el restaurante. Puedes escribir uno por línea.",
    )
    nutritional_information = models.TextField(
        "información nutricional", blank=True, default="",
        help_text="Indica la porción de referencia, cantidades y unidades. No introduzcas valores estimados sin verificar.",
    )
    allergens = models.TextField(
        "alérgenos", blank=True, default="",
        help_text="Información verificada de alérgenos y posibles trazas. Vacío significa información no disponible, no ausencia de alérgenos.",
    )
    image_url = models.URLField(
        "URL de la imagen",
        max_length=2045,
        blank=True,
        default=""    ,
        help_text="Enlace directo a una imagen externa."
    )
    category = models.ForeignKey(
        Category,
        verbose_name="categoría",
        related_name="products",
        on_delete=models.PROTECT,
    )
    station = models.ForeignKey(
        Station,
        verbose_name="estación de preparación",
        related_name="products",
        on_delete=models.PROTECT,
    )
    sale_price = models.DecimalField(
        "precio de venta",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    published = models.BooleanField(
        "publicado",
        default=False,
        help_text="Habilita su publicación en el menú.",
    )
    available = models.BooleanField(
        "disponible",
        default=True,
        help_text="Indica si actualmente puede pedirse.",
    )
    created_at = models.DateTimeField(
        "fecha de creación",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "última actualización",
        auto_now=True,
    )

    class Meta:
        verbose_name = "producto"
        verbose_name_plural = "productos"
        ordering = ["name"]
        constraints = [
        models.CheckConstraint(
                condition=models.Q(sale_price__gte=0),
                name="catalog_product_price_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.sku} - {self.name}"
