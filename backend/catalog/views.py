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
    from django.db.models import IntegerField, OuterRef, Subquery, Value, Exists, Case, When
    from django.db.models.functions import Coalesce
    from stock.models import StockControl, Shift, Balance
    products = Product.objects.filter(
        published=True, available=True, category__active=True, station__active=True,
    ).select_related("category")
    balances = Balance.objects.filter(product_id=OuterRef("pk"), product__shiftitem__shift__closed_at__isnull=True,
                                      product__shiftitem__isnull=False).values("quantity")[:1]
    return products.alias(_stock_enabled=Exists(StockControl.objects.filter(pk=1, enabled=True)),
                          _stock_open=Exists(Shift.objects.filter(closed_at__isnull=True))).annotate(
        stock_quantity=Case(When(_stock_enabled=False, then=Value(None, output_field=IntegerField())),
                            When(_stock_open=False, then=Value(0)), default=Coalesce(Subquery(balances), Value(0), output_field=IntegerField()), output_field=IntegerField()))


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


from rest_framework.views import APIView
from rest_framework.response import Response


class MenuStockView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [MenuThrottle]

    def get(self, request):
        return Response(dict(public_products().values_list("pk", "stock_quantity")))
