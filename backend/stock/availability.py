from django.db.models import IntegerField, OuterRef, Subquery, Value, Exists, Case, When
from django.db.models.functions import Coalesce
from .models import StockControl, Shift, Balance


def with_stock_availability(products):
    """One SQL query for menu and quote; checkout still locks and checks on release."""
    balances = Balance.objects.filter(
        product_id=OuterRef("pk"), product__shiftitem__shift__closed_at__isnull=True,
        product__shiftitem__isnull=False,
    ).values("quantity")[:1]
    return products.alias(
        _stock_enabled=Exists(StockControl.objects.filter(pk=1, enabled=True)),
        _stock_open=Exists(Shift.objects.filter(closed_at__isnull=True)),
    ).annotate(stock_quantity=Case(
        When(_stock_enabled=False, then=Value(None, output_field=IntegerField())),
        When(_stock_open=False, then=Value(0)),
        default=Coalesce(Subquery(balances), Value(0), output_field=IntegerField()),
        output_field=IntegerField(),
    ))
