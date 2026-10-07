from django.urls import path
from .views import IngredientsView, StudiesView, PreviewView
from .recipe_views import IngredientDetailView, ImportIngredientsView, RecipePreviewView, RecipesView, RecipeDetailView, SummaryView
from .import_views import InventoryView, RecipeImportView, RecipeWorkbookView
from .item_actions import InventoryLineView

urlpatterns = [
    path("costing/inventory/<int:pk>/lines/<int:line_id>/", InventoryLineView.as_view()),
    path("costing/recipes/workbook/", RecipeWorkbookView.as_view()),
    path("costing/inventory/", InventoryView.as_view()),
    path("costing/recipes/import/", RecipeImportView.as_view()),
    path("costing/ingredients/<int:pk>/", IngredientDetailView.as_view()),
    path("costing/import/", ImportIngredientsView.as_view()),
    path("costing/recipes/preview/", RecipePreviewView.as_view()),
    path("costing/recipes/", RecipesView.as_view()),
    path("costing/recipes/<int:pk>/", RecipeDetailView.as_view()),
    path("costing/summary/", SummaryView.as_view()),
    path("costing/ingredients/", IngredientsView.as_view()),
    path("costing/studies/", StudiesView.as_view()),
    path("costing/preview/", PreviewView.as_view()),
]
