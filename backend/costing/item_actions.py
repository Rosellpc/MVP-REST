from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from .views import CostingView
from .models import InventoryCount, InventoryCountLine, CostingChange
from .inventory import CountLineSerializer, count_payload


class InventoryLineView(CostingView):
    @transaction.atomic
    def put(self, request, pk, line_id):
        count = get_object_or_404(InventoryCount.objects.select_for_update(), pk=pk)
        line = get_object_or_404(InventoryCountLine, pk=line_id, inventory=count, archived=False)
        before = dict(CountLineSerializer(line).data)
        # Source metadata is preserved; only the seven editable columns may change.
        fields = ("code", "family", "location", "product", "unit", "quantity", "unit_cost")
        serializer = CountLineSerializer(line, data={key: request.data[key] for key in fields if key in request.data})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        CostingChange.objects.create(entity="inventory_line", object_id=line.pk, action="edit", before=before, after=dict(serializer.data), actor=request.user)
        return Response(count_payload(count))

    @transaction.atomic
    def delete(self, request, pk, line_id):
        count = get_object_or_404(InventoryCount.objects.select_for_update(), pk=pk)
        line = get_object_or_404(InventoryCountLine, pk=line_id, inventory=count, archived=False)
        CostingChange.objects.create(entity="inventory_line", object_id=line.pk, action="delete", before=dict(CountLineSerializer(line).data), actor=request.user)
        line.archived = True
        line.save(update_fields=["archived"])
        return Response(count_payload(count))
