from django.contrib import admin

from .models import Category, Product, Station


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "display_order",
        "active",
    )
    list_display_links = ("name",)
    list_editable = ("display_order", "active")
    list_filter = ("active",)
    search_fields = ("name",)
    ordering = ("display_order", "name")


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "active",
    )
    list_display_links = ("code",)
    list_editable = ("name", "active")
    list_filter = ("active", "code")
    search_fields = ("code", "name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "name",
        "category",
        "station",
        "sale_price",
        "published",
        "available",
    )
    list_display_links = ("sku", "name")
    list_editable = ("sale_price", "published", "available")
    list_filter = (
        "published",
        "available",
        "category",
        "station",
    )
    search_fields = ("sku", "name", "description")
    autocomplete_fields = ("category", "station")
    list_select_related = ("category", "station")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25

    fieldsets = (
        (
            "Información del producto",
            {
                "fields": (
                    "sku",
                    "name",
                    "image_url",
                    "description",
                    "category",
                ),
            },
        ),
        (
            "Ingredientes e información alimentaria",
            {
                "fields": ("ingredients", "nutritional_information", "allergens"),
            },
        ),
        (
            "Preparación y venta",
            {
                "fields": (
                    "station",
                    "sale_price",
                    "published",
                    "available",
                ),
            },
        ),
        (
            "Registro",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )
