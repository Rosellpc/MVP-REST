from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import BasePermission
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from catalog.models import Product
from .models import Shift, Balance, Movement
from .services import operate, control_lock
from .serializers import OpenInput, MovementInput, CloseInput, HistoryQuery


class CanStock(BasePermission):
    def has_permission(self, request, view):
        code = "view_stock" if request.method in ("GET", "HEAD", "OPTIONS") else "manage_stock"
        return request.user.is_authenticated and request.user.is_active and request.user.has_perm(f"stock.{code}")


class StockView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [CanStock]


def shift_payload(shift):
    if not shift:
        return None
    return {"id": shift.pk, "opened_at": shift.opened_at, "closed_at": shift.closed_at,
            "opened_by": shift.opened_by.username, "closed_by": shift.closed_by.username if shift.closed_by else None, "notes": shift.notes, "opening_notes": shift.opening_notes}


def rows_payload(shift, products):
    balances = {b.product_id: b for b in Balance.objects.all()}
    items = {item.product_id: item for item in shift.items.all()} if shift else {}
    totals = {}
    if shift:
        from django.db.models import Sum, Max
        for row in shift.movements.values("product_id", "kind").annotate(quantity=Sum("quantity"), delta=Sum("delta"), last=Max("created_at")):
            totals.setdefault(row["product_id"], {})[row["kind"]] = row
    rows = []
    for product in products:
        item = items.get(product.pk)
        balance = balances.get(product.pk)
        stats = totals.get(product.pk, {})
        q = lambda key: stats.get(key, {}).get("quantity", 0)
        adjustments = sum(stats.get(key, {}).get("delta", 0) for key in ["ADJUST", "COUNT"])
        quantity = item.counted if item and shift.closed_at else balance.quantity if balance else 0
        rows.append(dict(product_id=product.pk, name=item.name if item else product.name,
                         sku=item.sku if item else product.sku, category=product.category.name, station=product.station.code,
                         initial=item.initial if item else quantity, production=q("PRODUCTION"),
                         sales=q("SALE") - q("RETURN") - q("CANCEL_WASTE"),
                         waste=q("WASTE") + q("CANCEL_WASTE"), adjustments=adjustments,
                         quantity=quantity, unit="unidad de venta", low_threshold=5,
                         status="OUT" if quantity == 0 else "LOW" if quantity <= 5 else "AVAILABLE",
                         updated_at=max((s["last"] for s in stats.values()), default=None),
                         theoretical=item.theoretical if item else None, counted=item.counted if item else None,
                         difference=item.difference if item else None, reason=item.reason if item else ""))
    return rows


class DashboardView(StockView):
    @transaction.atomic
    def get(self, request):
        control = control_lock()
        shift = Shift.objects.select_related("opened_by", "closed_by").order_by("-id").first()
        if shift and not shift.closed_at:
            products = Product.objects.filter(shiftitem__shift=shift)
        else:
            products = Product.objects.filter(Q(published=True, station__code__in=["KITCHEN", "BAR"]) | Q(stock_balance__quantity__gt=0))
        rows = rows_payload(shift, products.select_related("category", "station").order_by("name"))
        summary = {key: sum(row[key] for row in rows) for key in ["quantity", "production", "sales", "waste"]}
        summary.update(products=len(rows), out=sum(r["status"] == "OUT" for r in rows), low=sum(r["status"] == "LOW" for r in rows))
        return Response(dict(enabled=control.enabled, revision=control.revision, shift=shift_payload(shift), rows=rows, summary=summary))


class ActionView(StockView):
    action = ""
    def post(self, request):
        serializer = {"open": OpenInput, "movement": MovementInput, "close": CloseInput}[self.action](data=request.data)
        if not serializer.is_valid():
            raise ValidationError({"detail": "Revisa los campos: " + str(serializer.errors)})
        return Response(operate(self.action, serializer.validated_data, request.user))


class StockPagination(PageNumberPagination):
    page_size = 50


class HistoryView(StockView):
    def get(self, request):
        query = HistoryQuery(data=request.query_params)
        query.is_valid(raise_exception=True)
        rows = Movement.objects.select_related("actor", "product", "order_item")
        for key, lookup in [("product", "product_id"), ("shift", "shift_id"), ("start", "created_at__date__gte"), ("end", "created_at__date__lte")]:
            if key in query.validated_data:
                rows = rows.filter(**{lookup: query.validated_data[key]})
        page = StockPagination()
        result = page.paginate_queryset(rows, request)
        return page.get_paginated_response([dict(id=row.pk, product_id=row.product_id, product=row.product.name, kind=row.kind,
            delta=row.delta, quantity=row.quantity, balance_after=row.balance_after, reason=row.reason,
            actor=row.actor.username if row.actor else "Sistema · checkout", created_at=row.created_at,
            shift_id=row.shift_id, order_id=row.order_item.order_id if row.order_item else None) for row in result])


class ShiftsView(StockView):
    def get(self, request):
        page = StockPagination()
        rows = page.paginate_queryset(Shift.objects.select_related("opened_by", "closed_by").order_by("-id"), request)
        return page.get_paginated_response([shift_payload(row) for row in rows])


class ShiftDetailView(StockView):
    @transaction.atomic
    def get(self, request, pk):
        control_lock()
        shift = get_object_or_404(Shift.objects.select_related("opened_by", "closed_by"), pk=pk)
        products = Product.objects.filter(shiftitem__shift=shift).select_related("category", "station").order_by("name")
        return Response(dict(shift=shift_payload(shift), rows=rows_payload(shift, products)))
