from django.urls import path

from .views import MenuProductDetailView, MenuView, MenuStockView

app_name = "catalog"

urlpatterns = [
    path("menu/", MenuView.as_view(), name="menu"),
    path("menu/stock/", MenuStockView.as_view(), name="menu-stock"),
    path("menu/<int:pk>/", MenuProductDetailView.as_view(), name="product-detail"),
]
