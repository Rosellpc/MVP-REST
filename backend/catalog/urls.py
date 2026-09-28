from django.urls import path

from .views import MenuView

app_name = "catalog"

urlpatterns = [
    path("menu/", MenuView.as_view(), name="menu"),
]
