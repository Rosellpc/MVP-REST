from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from .calculator import calculate
from .models import Ingredient, CostStudy, IngredientRevision
from .serializers import IngredientSerializer, RecipeInputSerializer, StudySerializer


class CanCost(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_perm("costing.use_costing")


class CostingView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [CanCost]


class IngredientsView(CostingView):
    def get(self, request):
        return Response(IngredientSerializer(Ingredient.objects.filter(archived=False), many=True).data)

    @transaction.atomic
    def post(self, request):
        serializer = IngredientSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        IngredientRevision.objects.create(ingredient=item, snapshot=dict(serializer.data), reason="Alta de insumo", actor=request.user)
        return Response(serializer.data, status=201)


class StudiesView(CostingView):
    def get(self, request):
        return Response(StudySerializer(CostStudy.objects.all()[:100], many=True).data)

    def post(self, request):
        serializer = RecipeInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        snapshot = calculate(serializer.validated_data)
        study = CostStudy.objects.create(name=snapshot["name"], snapshot=snapshot, created_by=request.user)
        return Response(StudySerializer(study).data, status=201)


class PreviewView(CostingView):
    def post(self, request):
        serializer = RecipeInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(calculate(serializer.validated_data))
