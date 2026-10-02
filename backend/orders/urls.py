from django.urls import path

from .views import CreateOrderView, OrderDetailView, PreviewOrderView

app_name = "orders"
urlpatterns = [
    path("orders/preview/", PreviewOrderView.as_view(), name="preview"),
    path("orders/", CreateOrderView.as_view(), name="create"),
    path("orders/<uuid:public_code>/", OrderDetailView.as_view(), name="detail"),
]
