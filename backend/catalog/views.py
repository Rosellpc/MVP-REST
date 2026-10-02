from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle

from .models import Product
from .serializers import MenuProductDetailSerializer, MenuProductSerializer, MenuQuerySerializer


class MenuPagination(PageNumberPagination):
    page_size = 100


class MenuThrottle(AnonRateThrottle):
    scope = "public_menu"
    rate = "120/min"


def public_products():
    return Product.objects.filter(
        published=True, available=True, category__active=True, station__active=True,
    ).select_related("category")


class MenuView(ListAPIView):
    """Public, read-only menu of products currently eligible for sale."""

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = MenuProductSerializer
    pagination_class = MenuPagination
    throttle_classes = [MenuThrottle]
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        query = MenuQuerySerializer(data=self.request.query_params.dict())
        query.is_valid(raise_exception=True)

        products = public_products().order_by("category__display_order", "category__name", "name", "pk")
        category_id = query.validated_data.get("category")
        if category_id is not None:
            products = products.filter(category_id=category_id)
        return products


class MenuProductDetailView(RetrieveAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = MenuProductDetailSerializer
    throttle_classes = [MenuThrottle]
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        return public_products()
