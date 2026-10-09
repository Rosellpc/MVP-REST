from rest_framework import serializers


class OperationInput(serializers.Serializer):
    key = serializers.UUIDField()


class OpenItem(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    keep = serializers.IntegerField(min_value=0, max_value=1000000)
    production = serializers.IntegerField(min_value=0, max_value=1000000, default=0)
    reason = serializers.CharField(max_length=500, allow_blank=True, default="")


class OpenInput(OperationInput):
    revision = serializers.IntegerField(min_value=0)
    notes = serializers.CharField(max_length=2000, allow_blank=True, default="")
    items = OpenItem(many=True, allow_empty=False)


class MovementInput(OperationInput):
    shift_id = serializers.IntegerField(min_value=1)
    product_id = serializers.IntegerField(min_value=1)
    kind = serializers.ChoiceField(choices=["PRODUCTION", "WASTE", "ADJUST"])
    quantity = serializers.IntegerField(min_value=-1000000, max_value=1000000)
    reason = serializers.CharField(max_length=500, allow_blank=False)

    def validate(self, data):
        if not data["quantity"] or (data["kind"] != "ADJUST" and data["quantity"] < 0):
            raise serializers.ValidationError({"detail": "La cantidad debe ser positiva; solo los ajustes admiten negativos."})
        return data


class CloseItem(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    counted = serializers.IntegerField(min_value=0, max_value=1000000)
    reason = serializers.CharField(max_length=500, allow_blank=True, default="")


class CloseInput(OpenInput):
    shift_id = serializers.IntegerField(min_value=1)
    items = CloseItem(many=True, allow_empty=False)


class HistoryQuery(serializers.Serializer):
    product = serializers.IntegerField(min_value=1, required=False)
    shift = serializers.IntegerField(min_value=1, required=False)
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)
