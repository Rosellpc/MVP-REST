from uuid import uuid4
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from catalog.models import Category, Product, Station
from orders.models import Order, OrderItem
from .models import ProductionTicket, TicketEvent
from .services import release_order_to_production, transition_ticket


@override_settings(PRODUCTION_DEMO_ENABLED=True)
class ProductionTests(TestCase):
    def test_finalize_archives_once_and_preserves_public_ready(self):
        self.release()
        for station in ("KITCHEN", "BAR"):
            ticket = self.ticket(station)
            self.action(ticket, "start")
            self.action(ticket, "complete")
        ticket = self.ticket("KITCHEN")
        self.client.force_authenticate(self.kitchen)
        events = TicketEvent.objects.count()
        self.assertEqual(self.action(ticket, "finalize").status_code, 200)
        self.assertEqual(self.action(ticket, "finalize").status_code, 200)
        self.assertEqual(TicketEvent.objects.count(), events + 1)
        self.assertEqual(self.client.get("/api/v1/production/tickets/").data["count"], 0)
        ticket.refresh_from_db()
        self.assertIsNotNone(ticket.archived_at)
        self.assertEqual(ticket.status, "READY")
        self.order.refresh_from_db()
        self.assertEqual(self.order.production_status, "READY")
        self.client.force_authenticate(self.bar)
        self.assertEqual(self.client.get("/api/v1/production/tickets/").data["count"], 1)
        self.assertEqual(self.action(ticket, "finalize").status_code, 404)
        self.assertEqual(self.action(self.ticket("BAR"), "finalize").status_code, 200)

    def test_finalize_rejects_unready_ticket(self):
        self.release()
        ticket = self.ticket("KITCHEN")
        self.assertEqual(self.action(ticket, "finalize").status_code, 409)
        ticket.refresh_from_db()
        self.assertIsNone(ticket.archived_at)

    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", verbosity=0)
        for role in ("ADMIN", "KITCHEN", "BAR"):
            user = get_user_model().objects.create_user(role.lower(), password="test-password")
            user.groups.add(Group.objects.get(name=role))
            setattr(cls, role.lower(), user)
        category = Category.objects.create(name="Test")
        for code in ("KITCHEN", "BAR", "DELIVERY"):
            station = Station.objects.create(code=code, name=code)
            Product.objects.create(sku=code, name=code, station=station, category=category, sale_price=10)

    def setUp(self):
        self.order = Order.objects.create(idempotency_key=uuid4(), request_hash="test", customer_name="Private", fulfillment="DINE_IN", table_label="2", total=20)
        for code in ("KITCHEN", "BAR"):
            OrderItem.objects.create(order=self.order, product=Product.objects.get(sku=code), name=f"Snapshot {code}", station_code=code, unit_price=10, quantity=1, line_total=10)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def release(self):
        return self.client.post(f"/api/v1/staff/orders/{self.order.pk}/release/")

    def ticket(self, station):
        return ProductionTicket.objects.get(order=self.order, station_code=station)

    def action(self, ticket, action, data=None):
        return self.client.post(f"/api/v1/production/tickets/{ticket.pk}/{action}/", data or {}, format="json")

    def test_release_idempotency_and_snapshots(self):
        Product.objects.update(name="Changed", station=Station.objects.get(code="DELIVERY"))
        self.assertEqual(self.release().status_code, 201)
        self.assertEqual(self.release().status_code, 200)
        self.assertEqual(ProductionTicket.objects.count(), 2)
        self.assertEqual(TicketEvent.objects.count(), 2)
        self.assertEqual(self.ticket("KITCHEN").items.get().name, "Snapshot KITCHEN")
        self.order.refresh_from_db()
        self.assertEqual(self.order.released_by, self.admin)
        self.assertEqual(self.order.payment_status, "SIMULATED")

    @override_settings(PRODUCTION_DEMO_ENABLED=False)
    def test_disabled_by_default(self):
        self.assertEqual(self.release().status_code, 403)
        self.assertFalse(ProductionTicket.objects.exists())

    def test_delivery_rejects_entire_order(self):
        self.order.items.filter(station_code="BAR").update(station_code="DELIVERY")
        self.assertEqual(self.release().status_code, 409)
        self.assertFalse(ProductionTicket.objects.exists())
        self.order.refresh_from_db()
        self.assertIsNone(self.order.released_at)

    def test_real_or_empty_orders_not_released(self):
        self.order.payment_status = "PAID"
        self.order.save()
        self.assertEqual(self.release().status_code, 409)
        self.order.payment_status = "SIMULATED"
        self.order.save()
        self.order.items.all().delete()
        self.assertEqual(self.release().status_code, 409)

    def test_release_transaction_rolls_back(self):
        with patch("production.services.TicketEvent.objects.create", side_effect=RuntimeError("fail")):
            with self.assertRaises(RuntimeError):
                release_order_to_production(self.order.pk, self.admin)
        self.assertFalse(ProductionTicket.objects.exists())
        self.order.refresh_from_db()
        self.assertIsNone(self.order.released_at)

    def test_station_scope_and_direct_id_access(self):
        self.release()
        for actor, own, other in ((self.kitchen, "KITCHEN", "BAR"), (self.bar, "BAR", "KITCHEN")):
            self.client.force_authenticate(actor)
            data = self.client.get("/api/v1/production/tickets/").data
            self.assertEqual(data["count"], 1)
            self.assertEqual(data["results"][0]["station_code"], own)
            self.assertNotIn("customer_name", data["results"][0])
            self.assertEqual(self.client.get(f"/api/v1/production/tickets/?station={other}").data["count"], 0)
            self.assertEqual(self.client.get(f"/api/v1/production/tickets/{self.ticket(other).pk}/").status_code, 404)
            self.assertEqual(self.action(self.ticket(other), "start").status_code, 404)
            self.assertEqual(self.release().status_code, 403)
            self.assertEqual(self.client.get("/api/v1/staff/orders/").status_code, 403)

    def test_transitions_aggregate_and_retry(self):
        self.release()
        kitchen, bar = self.ticket("KITCHEN"), self.ticket("BAR")
        self.assertEqual(self.action(kitchen, "complete").status_code, 409)
        for ticket in (kitchen, bar):
            self.assertEqual(self.action(ticket, "start").status_code, 200)
            self.assertEqual(self.action(ticket, "start").status_code, 200)
            self.assertEqual(self.action(ticket, "complete").status_code, 200)
            self.order.refresh_from_db()
            self.assertEqual(self.order.production_status, "IN_PROGRESS" if ticket == kitchen else "READY")
        self.assertEqual(TicketEvent.objects.count(), 6)
        self.assertEqual(self.action(kitchen, "start").status_code, 409)

    def test_cancellation_permissions_reason_and_partial_status(self):
        self.release()
        ticket = self.ticket("KITCHEN")
        self.client.force_authenticate(self.kitchen)
        self.assertEqual(self.action(ticket, "cancel", {"reason": "test"}).status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.action(ticket, "cancel", {"reason": "  "}).status_code, 400)
        self.assertEqual(self.action(ticket, "cancel", {"reason": "Sin insumos"}).status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.production_status, "PARTIALLY_CANCELLED")
        event = ticket.events.last()
        self.assertEqual(event.actor, self.admin)
        self.assertEqual(event.reason, "Sin insumos")
        self.assertEqual(self.action(ticket, "start").status_code, 409)
        self.action(self.ticket("BAR"), "cancel", {"reason": "Cancelación total"})
        self.order.refresh_from_db()
        self.assertEqual(self.order.production_status, "CANCELLED")

    def test_ready_ticket_cannot_be_cancelled(self):
        self.release()
        ticket = self.ticket("KITCHEN")
        self.action(ticket, "start")
        self.action(ticket, "complete")
        self.assertEqual(self.action(ticket, "cancel", {"reason": "test"}).status_code, 409)

    def test_unauthenticated_access_denied(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.release().status_code, 403)
        self.assertEqual(self.client.get("/api/v1/production/tickets/").status_code, 403)

    def test_csrf_required_for_session_mutations(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_login(self.admin)
        self.assertEqual(self.release().status_code, 403)
        token = self.client.get("/api/v1/auth/csrf/").data["csrfToken"]
        response = self.client.post(f"/api/v1/staff/orders/{self.order.pk}/release/", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.action(self.ticket("KITCHEN"), "start").status_code, 403)

    def test_service_enforces_station_permission(self):
        self.release()
        from rest_framework.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied):
            transition_ticket(self.ticket("BAR").pk, self.kitchen, "IN_PROGRESS")

    def test_public_tracking_only_exposes_aggregate_production_status(self):
        public = APIClient()
        url = f"/api/v1/orders/{self.order.public_code}/"
        self.assertEqual(public.get(url).data["production_status"], "NOT_RELEASED")
        self.release()
        self.assertEqual(public.get(url).data["production_status"], "PENDING")
        for station in ("KITCHEN", "BAR"):
            ticket = self.ticket(station)
            self.action(ticket, "start")
            self.action(ticket, "complete")
            data = public.get(url).data
            self.assertEqual(data["production_status"], "IN_PROGRESS" if station == "KITCHEN" else "READY")
            for field in ("released_by", "customer_name", "table_label", "events", "tickets"):
                self.assertNotIn(field, data)
            self.assertEqual(data["payment_status"], "SIMULATED")
