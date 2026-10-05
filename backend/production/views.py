from rest_framework.authentication import SessionAuthentication
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from orders.models import Order
from .models import ProductionTicket, CancellationRequest
from .permissions import CanReadTickets, CanReleaseOrders, allowed_stations
from .serializers import TicketSerializer, StaffOrderSerializer, CancelSerializer, CancellationSerializer, DirectCancelSerializer
from .services import release_order_to_production, transition_ticket, finalize_ticket, request_cancellation, approve_cancellation


class Pagination(PageNumberPagination):
    page_size = 50


class StaffOrderList(ListAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [CanReleaseOrders]
    serializer_class = StaffOrderSerializer
    pagination_class = Pagination
    queryset = Order.objects.filter(status="DEMO_CONFIRMED", payment_status="SIMULATED").select_related("cancellation_request__requested_by", "cancellation_request__ticket").prefetch_related("items", "tickets__items", "tickets__order__cancellation_request").order_by("-created_at", "-pk")


class ReleaseOrderView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [CanReleaseOrders]

    def post(self, request, pk):
        tickets, created = release_order_to_production(pk, request.user)
        return Response(TicketSerializer(tickets, many=True).data, status=201 if created else 200)


class TicketQueryset:
    authentication_classes = [SessionAuthentication]
    permission_classes = [CanReadTickets]
    serializer_class = TicketSerializer

    def get_queryset(self):
        queryset = ProductionTicket.objects.filter(station_code__in=allowed_stations(self.request.user)).select_related("order__cancellation_request").prefetch_related("items")
        station = self.request.query_params.get("station")
        status = self.request.query_params.get("status")
        if station:
            if station not in ("KITCHEN", "BAR"):
                raise ValidationError({"station": "Estación inválida."})
            queryset = queryset.filter(station_code=station)
        if status:
            if status not in ProductionTicket.Status.values:
                raise ValidationError({"status": "Estado inválido."})
            queryset = queryset.filter(status=status)
        return queryset


class TicketList(TicketQueryset, ListAPIView):
    pagination_class = Pagination

    def get_queryset(self):
        return super().get_queryset().filter(Q(archived_at__isnull=True) | Q(status="CANCELLED"))


class TicketDetail(TicketQueryset, RetrieveAPIView):
    pass


class TicketAction(TicketQueryset, RetrieveAPIView):
    http_method_names = ["post", "options"]
    target_status = ""

    def post(self, request, pk):
        ticket = self.get_object()
        if self.target_status == "FINALIZED":
            return Response(TicketSerializer(finalize_ticket(ticket.pk, request.user)).data)
        reason = ""
        if self.target_status == "CANCELLED":
            serializer = CancelSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            reason = serializer.validated_data["reason"]
            cancellation = request_cancellation(ticket.pk, request.user, reason)
            return Response(CancellationSerializer(cancellation).data)
        ticket = transition_ticket(ticket.pk, request.user, self.target_status, reason)
        return Response(TicketSerializer(ticket).data)


class ApproveCancellationView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [CanReleaseOrders]

    def post(self, request, pk):
        serializer = DirectCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(CancellationSerializer(approve_cancellation(pk, request.user, serializer.validated_data.get("reason", ""))).data)


class CancellationNotices(ListAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [CanReadTickets]
    serializer_class = CancellationSerializer
    pagination_class = Pagination

    def get_queryset(self):
        stations = allowed_stations(self.request.user)
        station = self.request.query_params.get("station")
        if station:
            stations = [station] if station in stations else []
        return CancellationRequest.objects.filter(approved_at__isnull=False, order__tickets__station_code__in=stations).select_related("order", "ticket", "requested_by").distinct().order_by("-approved_at", "-pk")
