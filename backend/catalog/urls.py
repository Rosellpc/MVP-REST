from django.urls import path

from .views import MenuProductDetailView, MenuView

app_name = "catalog"

urlpatterns = [
    path("menu/", MenuView.as_view(), name="menu"),
    path("menu/<int:pk>/", MenuProductDetailView.as_view(), name="product-detail"),
]
