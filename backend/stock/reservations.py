from django.db.models import Sum


def reserved_quantity(product_id):
    from payments.models import ReservationLine
    # Expired deadlines still hold stock until the expiration transaction commits.
    return ReservationLine.objects.filter(
        product_id=product_id, reservation__status__in=["HELD", "PROCESSING"],
    ).aggregate(total=Sum("quantity"))["total"] or 0
