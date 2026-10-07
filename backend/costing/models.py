from django.conf import settings
from django.db import models


class Ingredient(models.Model):
    archived = models.BooleanField(default=False)
    name = models.CharField(max_length=160, unique=True)
    purchase_unit = models.CharField(max_length=4)
    purchase_quantity = models.DecimalField(max_digits=12, decimal_places=3)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=4)
    yield_percent = models.DecimalField(max_digits=6, decimal_places=3)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [("use_costing", "Use independent recipe costing workspace")]
        ordering = ["name"]


class CostStudy(models.Model):
    name = models.CharField(max_length=160)
    snapshot = models.JSONField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]


class IngredientRevision(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, related_name="history")
    snapshot = models.JSONField()
    reason = models.CharField(max_length=250)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Recipe(models.Model):
    archived = models.BooleanField(default=False)
    name = models.CharField(max_length=160)
    current_version = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class RecipeVersion(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.PROTECT, related_name="versions")
    number = models.PositiveIntegerField()
    snapshot = models.JSONField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-number"]
        constraints = [models.UniqueConstraint(fields=["recipe", "number"], name="costing_recipe_version_unique")]


class RecipeWorkbookImport(models.Model):
    digest = models.CharField(max_length=64, unique=True)
    filename = models.CharField(max_length=250)
    report = models.JSONField(default=dict)
    source = models.JSONField(default=dict)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class InventoryCount(models.Model):
    establishment = models.CharField(max_length=160)
    department = models.CharField(max_length=100)
    inventory_date = models.DateField(null=True, blank=True)
    employee = models.CharField(max_length=160)
    currency = models.CharField(max_length=3, blank=True)
    is_example = models.BooleanField(default=False)
    source_name = models.CharField(max_length=250, blank=True)
    source_sheet = models.CharField(max_length=100, blank=True)
    source_digest = models.CharField(max_length=64, unique=True, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]


class InventoryCountLine(models.Model):
    archived = models.BooleanField(default=False)
    inventory = models.ForeignKey(InventoryCount, on_delete=models.CASCADE, related_name="lines")
    code = models.CharField(max_length=60, blank=True)
    family = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    product = models.CharField(max_length=250)
    unit = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=16, decimal_places=4)
    unit_cost = models.DecimalField(max_digits=16, decimal_places=4)
    source_row = models.PositiveIntegerField(null=True)
    source_extra = models.JSONField(default=dict)

    class Meta:
        ordering = ["pk"]


class CostingChange(models.Model):
    entity = models.CharField(max_length=40)
    object_id = models.PositiveBigIntegerField()
    action = models.CharField(max_length=20)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
