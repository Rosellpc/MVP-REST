from datetime import datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo
from django.db.models import Sum, Count, Avg, F, DurationField, ExpressionWrapper, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.permissions import HasAreaPermission
from orders.models import Order, OrderItem
from production.models import ProductionTicket, CancellationRequest
from stock.models import StockControl, Shift, Balance, Movement
from costing.models import RecipeVersion, Ingredient
from catalog.models import Product

ZONE = ZoneInfo("America/Lima")


def money(value):
    return str(Decimal(value or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class Period(serializers.Serializer):
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)

    def validate(self, data):
        today = timezone.localdate(timezone=ZONE)
        end = data.get("end", today)
        start = data.get("start", end - timedelta(days=6))
        if end < start or (end - start).days > 365 or end > today:
            raise serializers.ValidationError("Elige un intervalo de hasta 366 días, sin fechas futuras.")
        return {"start": start, "end": end}


def order_metrics(orders):
    # PARTIALLY_CANCELLED is legacy and has no trustworthy partial monetary allocation.
    valid = orders.exclude(production_status__in=["CANCELLED", "PARTIALLY_CANCELLED"])
    values = valid.aggregate(amount=Sum("total"), count=Count("pk"))
    amount, count = values["amount"] or Decimal(0), values["count"]
    return valid, {"amount": money(amount), "orders": count, "average_ticket": money(amount / count) if count else None}


class DashboardView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [HasAreaPermission]
    required_permission = "accounts.access_staff"

    def get(self, request):
        period = Period(data=request.query_params)
        if not period.is_valid():
            return Response({"detail": "Fechas inválidas. Usa YYYY-MM-DD, inicio anterior al fin y un máximo de 366 días hasta hoy."}, status=400)
        start, end = period.validated_data["start"], period.validated_data["end"]
        begin = datetime.combine(start, time.min, ZONE)
        stop = datetime.combine(end + timedelta(days=1), time.min, ZONE)
        days = (end - start).days + 1
        base = Order.objects.filter(status="DEMO_CONFIRMED", payment_status="SIMULATED")
        orders = base.filter(created_at__gte=begin, created_at__lt=stop)
        valid, metrics = order_metrics(orders)
        _, previous = order_metrics(base.filter(created_at__gte=begin - timedelta(days=days), created_at__lt=begin))
        metrics["all_orders"] = orders.count()
        metrics["cancelled"] = orders.filter(production_status="CANCELLED").count()
        metrics["partial_excluded"] = orders.filter(production_status="PARTIALLY_CANCELLED").count()
        metrics["change_percent"] = money((Decimal(metrics["amount"]) - Decimal(previous["amount"])) / Decimal(previous["amount"]) * 100) if Decimal(previous["amount"]) else None
        daily = {row["day"]: row for row in valid.annotate(day=TruncDate("created_at", tzinfo=ZONE)).values("day").annotate(amount=Sum("total"), orders=Count("pk")).order_by("day")}
        trend = []
        for offset in range(days):
            day = start + timedelta(days=offset)
            value = daily.get(day, {})
            trend.append({"date": day, "amount": money(value.get("amount")), "orders": value.get("orders", 0)})
        lines = OrderItem.objects.filter(order__in=valid)
        top = list(lines.values("product_id", "name").annotate(quantity=Sum("quantity"), amount=Sum("line_total")).order_by("-quantity", "product_id", "name")[:8])
        for row in top:
            row["amount"] = money(row["amount"])
        metrics["units"] = lines.aggregate(total=Sum("quantity"))["total"] or 0
        channels = list(valid.values("fulfillment").annotate(count=Count("pk"), amount=Sum("total")).order_by("fulfillment"))
        for row in channels:
            row["amount"] = money(row["amount"])

        stations = []
        for code in ["KITCHEN", "BAR"]:
            tickets = ProductionTicket.objects.filter(station_code=code)
            counts = {row["status"]: row["count"] for row in tickets.filter(archived_at__isnull=True).values("status").annotate(count=Count("pk"))}
            completed = tickets.filter(status="READY", completed_at__gte=begin, completed_at__lt=stop).filter(completed_at__gte=F("created_at"))
            duration = completed.aggregate(average=Avg(ExpressionWrapper(F("completed_at") - F("created_at"), output_field=DurationField())), count=Count("pk"))
            stations.append({"code": code, "pending": counts.get("PENDING", 0), "preparing": counts.get("IN_PROGRESS", 0), "ready": counts.get("READY", 0),
                             "completed_sample": duration["count"], "average_minutes": round(duration["average"].total_seconds() / 60, 1) if duration["average"] is not None else None})
        stock_enabled = StockControl.objects.filter(pk=1, enabled=True).exists()
        shift = Shift.objects.filter(closed_at__isnull=True).first()
        products = Product.objects.filter(published=True, category__active=True, station__active=True, station__code__in=["KITCHEN", "BAR"])
        balances = Balance.objects.filter(product__in=products)
        stock_totals = balances.aggregate(units=Sum("quantity"), registered=Count("pk"), low=Count("pk", filter=Q(quantity__gte=1, quantity__lte=5)), out=Count("pk", filter=Q(quantity=0)))
        alerts = list(products.filter(Q(stock_balance__quantity__lte=5) | Q(stock_balance__isnull=True)).values("id", "name", "sku", "stock_balance__quantity").order_by("stock_balance__quantity", "name")[:8])
        movements = Movement.objects.filter(created_at__gte=begin, created_at__lt=stop)
        stock_totals["waste"] = movements.filter(kind__in=["WASTE", "CANCEL_WASTE"]).aggregate(total=Sum("quantity"))["total"] or 0
        stock_totals["production"] = movements.filter(kind="PRODUCTION").aggregate(total=Sum("quantity"))["total"] or 0
        snapshots = list(RecipeVersion.objects.filter(recipe__archived=False, number=F("recipe__current_version")).values_list("snapshot", flat=True))
        costed = [s for s in snapshots if s.get("per_portion") is not None and not s.get("pending_costing")]
        percentages = [Decimal(s["food_cost_percent"]) for s in costed if s.get("food_cost_percent") is not None]
        costing = {"recipes": len(snapshots), "costed": len(costed), "pending": len(snapshots) - len(costed),
                   "ingredients": Ingredient.objects.filter(archived=False).count(), "food_cost_sample": len(percentages),
                   "average_food_cost": money(sum(percentages) / len(percentages)) if percentages else None}
        return Response({"generated_at": timezone.now(), "period": {"start": start, "end": end, "timezone": "America/Lima"},
                         "demo": True, "currency": "PEN", "metrics": metrics, "previous": previous, "trend": trend,
                         "top_products": top, "channels": channels, "stations": stations,
                         "pending_cancellations": CancellationRequest.objects.filter(approved_at__isnull=True, rejected_at__isnull=True).count(),
                         "stock": {**stock_totals, "units": stock_totals["units"] or 0, "enabled": stock_enabled, "shift_id": shift.pk if shift else None,
                                   "products": products.count(), "alerts": alerts}, "costing": costing})
